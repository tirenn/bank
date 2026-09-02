import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI
from app.config import settings

import httpx
import time

logger = logging.getLogger("ai_service.model_fallback")

_cached_db_models: List[str] = []
_last_fetch_time: float = 0.0

async def fetch_models_from_db() -> List[str]:
    """
    Fetches the active AI model list dynamically from the PostgreSQL database via Core Banking API.
    Caches result for 60 seconds to optimize performance.
    """
    global _cached_db_models, _last_fetch_time
    now = time.time()
    if _cached_db_models and (now - _last_fetch_time < 60.0):
        return _cached_db_models

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"{settings.CORE_BANKING_URL}/api/v1/ai/models")
            if res.status_code == 200:
                data = res.json()
                models = data.get("models", [])
                if models and isinstance(models, list):
                    _cached_db_models = [m for m in models if isinstance(m, str) and m.strip()]
                    _last_fetch_time = now
                    logger.info(f"Loaded {len(_cached_db_models)} AI models dynamically from PostgreSQL database")
                    return _cached_db_models
    except Exception as e:
        logger.debug(f"Could not fetch models from core DB API: {e}")

    return _cached_db_models or []


class ModelExecutionPlan:
    """
    Centralized execution plan for AI model routing.
    - is_paid_dedicated=True: Single paid model, NO fallback to free models on error.
    - is_paid_dedicated=False: Free tier pool, with automatic cascading fallback on limit/429.
    """
    def __init__(self, models: List[str], is_paid_dedicated: bool, error: Optional[str] = None):
        self.models = models
        self.is_paid_dedicated = is_paid_dedicated
        self.error = error


def resolve_model_execution_plan(
    api_key: Optional[str] = None,
    model_override: Optional[str] = None,
    active_db_models: Optional[List[str]] = None
) -> ModelExecutionPlan:
    """
    CENTRALIZED AI MODEL SELECTION LOGIC:
    1. If api_key is present AND model_override is empty -> Validation Error.
    2. If api_key is present AND model_override is present -> Dedicated Paid Mode (Single Model, No Fallback).
    3. If api_key is empty/nil -> Free Tier Mode (Active DB Pool with Multi-Tier Fallback Cascade).
    """
    has_key = bool(api_key and api_key.strip() and api_key.strip() != "YOUR_OPENROUTER_API_KEY_HERE")
    has_model = bool(model_override and str(model_override).strip())

    # Case 1: Custom API Key is provided, but Model Name is empty -> Validation Error
    if has_key and not has_model:
        return ModelExecutionPlan(
            models=[],
            is_paid_dedicated=True,
            error="Model name is required when an OpenRouter API Key is provided. Please select or enter a paid model."
        )

    # Case 2: Custom API Key is provided WITH Model Name -> Dedicated Paid Mode (Strictly 1 Model, No Fallback)
    if has_key and has_model:
        clean_model = str(model_override).strip()
        logger.info(f"🎯 [DEDICATED PAID MODE] Active model locked to: '{clean_model}' (Fallback Disabled)")
        return ModelExecutionPlan(
            models=[clean_model],
            is_paid_dedicated=True,
            error=None
        )

    # Case 3: Free Tier Mode (No Custom Key) -> Sequential Multi-Model Cascading Fallback Queue
    pool = active_db_models or _cached_db_models or []
    models_queue: List[str] = []

    if has_model and str(model_override).strip() in pool:
        models_queue.append(str(model_override).strip())

    for m in pool:
        if m and m not in models_queue:
            models_queue.append(m)

    logger.info(f"🔄 [FREE TIER CASCADE MODE] Active model queue: {models_queue} (Fallback Enabled)")
    return ModelExecutionPlan(
        models=models_queue,
        is_paid_dedicated=False,
        error=None
    )


def resolve_model_sequence(model_override: Optional[Any] = None) -> List[str]:
    plan = resolve_model_execution_plan(api_key=None, model_override=model_override, active_db_models=_cached_db_models)
    return plan.models


# ============================================================================
# 1. DEDICATED FUNCTION: CHAT AI & TOOL CALLING FALLBACK
# ============================================================================

async def execute_chat_with_fallback(
    openai_client: AsyncOpenAI,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
    temperature: float = 0.1,
    model_override: Optional[str] = None,
    api_key_override: Optional[str] = None
) -> Tuple[Optional[Any], Optional[str], Optional[str]]:
    """
    Executes conversational AI completions & tool calling for SubAgents.
    - If Paid Mode: Executes strictly against the single paid model without fallback.
    - If Free Mode: Sequentially iterates through the free model pool on failure (429, timeout, quota).
    Returns: (choice_message, successful_model_name, error_message)
    """
    # 1. Ensure active database model pool is loaded
    await fetch_models_from_db()

    # 2. Resolve Centralized Execution Plan
    plan = resolve_model_execution_plan(
        api_key=api_key_override,
        model_override=model_override,
        active_db_models=_cached_db_models
    )

    if plan.error:
        logger.warning(f"[CHAT VALIDATION ERROR] {plan.error}")
        return None, None, f"⚠️ Validation Error: {plan.error}"

    # 3. Dedicated Paid Mode (Single Model, No Fallback)
    if plan.is_paid_dedicated:
        paid_model = plan.models[0]
        logger.info(f"[CHAT DEDICATED PAID] Executing single-shot completion with '{paid_model}'")
        try:
            payload: Dict[str, Any] = {
                "model": paid_model,
                "messages": messages,
                "temperature": temperature,
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice or "auto"

            response = await openai_client.chat.completions.create(**payload)
            if response and response.choices and len(response.choices) > 0:
                choice = response.choices[0].message
                logger.info(f"[CHAT DEDICATED PAID] Succeeded with model: '{paid_model}'")
                return choice, paid_model, None
            else:
                return None, None, f"⚠️ Error: Model '{paid_model}' returned empty choices from OpenRouter."
        except Exception as exc:
            err_msg = str(exc)
            logger.error(f"[CHAT DEDICATED PAID ERROR] Paid model '{paid_model}' failed: {err_msg}")
            return None, None, f"⚠️ OpenRouter Error ({paid_model}): {err_msg}"

    # 4. Free Tier Mode (Cascading Multi-Model Fallback Queue)
    model_queue = plan.models
    failure_log: List[str] = []

    for idx, current_model in enumerate(model_queue):
        try:
            logger.info(
                f"[CHAT FREE FALLBACK] Trying model tier [{idx + 1}/{len(model_queue)}]: {current_model}"
            )
            payload: Dict[str, Any] = {
                "model": current_model,
                "messages": messages,
                "temperature": temperature,
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice or "auto"

            response = await openai_client.chat.completions.create(**payload)
            if response and response.choices and len(response.choices) > 0:
                choice = response.choices[0].message
                logger.info(f"[CHAT FREE FALLBACK] Succeeded with model: {current_model}")
                return choice, current_model, None
            else:
                failure_log.append(f"[{current_model}] returned empty choices")
        except Exception as exc:
            err_msg = str(exc)
            logger.warning(
                f"[CHAT FREE FALLBACK] Model '{current_model}' failed: {err_msg}. Cascading to next model tier..."
            )
            failure_log.append(f"[{current_model}]: {err_msg}")

    logger.error(
        f"[CHAT FREE FALLBACK] All {len(model_queue)} models exhausted: {'; '.join(failure_log)}"
    )
    exhausted_message = (
        "⚠️ Error: All free LLM model quotas have been exhausted across all providers. "
        "Please try again in a few moments or provide a custom OpenRouter API key and model name in admin settings."
    )
    return None, None, exhausted_message


from app.services.prompt_loader import load_prompt

# ============================================================================
# 2. DEDICATED FUNCTION: RAG DYNAMIC CHUNKING FALLBACK
# ============================================================================

async def execute_rag_chunking_with_fallback(
    openai_client: Optional[AsyncOpenAI],
    topic: str,
    text: str,
    model_override: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Executes LLM-driven dynamic semantic document splitting for RAG ingestion.
    Uses sequential model fallback to ensure robust chunking.
    Returns: List of chunk dictionaries [{"content": "...", "strategy": "llm_dynamic", "model": "..."}]
    """
    if not text or not text.strip():
        return []

    if not openai_client:
        logger.info("[RAG CHUNKING] OpenRouter client not configured. Skipping LLM chunking.")
        return []

    system_prompt = load_prompt("rag_chunking_system.md") or "You are a precise JSON document chunker. Output only JSON."
    user_prompt_template = load_prompt("rag_chunking_user.md")

    if user_prompt_template:
        prompt = user_prompt_template.replace("{topic}", topic).replace("{text}", text[:6000])
    else:
        prompt = f"Divide banking document (Topic: '{topic}') into semantic chunks as JSON array:\n\n{text[:6000]}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    choice, successful_model, err = await execute_chat_with_fallback(
        openai_client=openai_client,
        messages=messages,
        temperature=0.0,
        model_override=model_override
    )


    if choice and choice.content:
        try:
            raw_json = choice.content.strip()
            if raw_json.startswith("```"):
                lines = raw_json.split("\n")
                raw_json = "\n".join([l for l in lines if not l.startswith("```")])
            chunks_list = json.loads(raw_json)
            if isinstance(chunks_list, list) and len(chunks_list) > 0:
                logger.info(
                    f"[RAG CHUNKING] Succeeded using {successful_model}: "
                    f"Generated {len(chunks_list)} semantic chunks for topic '{topic}'"
                )
                return [
                    {
                        "content": str(c).strip(),
                        "strategy": "llm_dynamic",
                        "model": successful_model
                    }
                    for c in chunks_list if str(c).strip()
                ]
        except Exception as parse_err:
            logger.warning(
                f"[RAG CHUNKING] Failed to parse JSON response: {parse_err}. "
                f"Raw: {choice.content[:200]}"
            )

    return []

# ============================================================================
# COMPATIBILITY WRAPPER CLASS
# ============================================================================

class ModelFallbackMechanism:
    fetch_models_from_db = staticmethod(fetch_models_from_db)
    resolve_model_execution_plan = staticmethod(resolve_model_execution_plan)
    resolve_model_sequence = staticmethod(resolve_model_sequence)
    execute_completion = staticmethod(execute_chat_with_fallback)
    execute_dynamic_chunking = staticmethod(execute_rag_chunking_with_fallback)
    ModelExecutionPlan = ModelExecutionPlan


model_fallback = ModelFallbackMechanism



