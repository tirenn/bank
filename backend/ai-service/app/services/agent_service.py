"""
Agent Service & Banking AI Coordinator for Tirenn Banking Microservice.
=======================================================================
Clean Architecture & SOLID Coordinator Facade:
This service serves as the central entrypoint for customer chat interactions,
coordinating:
1. Edge Security Guardrail (Prompt injection & jailbreak prevention)
2. Fast-Path Caching (Redis exact & semantic cache)
3. 7-Day Long-Running Multi-Turn Workflows (Redis workflow state)
4. Planner Orchestrator (DAG generation via PlannerService)
5. Multi-Agent Swarm Dispatcher (SubAgentRegistry)
6. Inter-Agent Sequential Scratchpad (Data sharing between chained steps)

SOLID Principles Applied:
- Single Responsibility: Delegates planning to PlannerService and domain execution to SubAgents.
- Open/Closed: Uses SubAgentRegistry for agent lookup without modifying coordinator code.
- Dependency Inversion: Accepts dependencies in constructor for testability.
"""

from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from app.domain.schemas import ChatMessage, ChatResponse, PlanStep, ExecutionPlan
from app.domain.interfaces import IPlanGenerator
from app.services.model_fallback import model_fallback
from app.services.rag_cache_service import rag_cache_service
from app.services.workflow_state_service import workflow_state_service
from app.services.cost_tracker_service import cost_tracker_service
from app.services.prompt_injection_guardrail import prompt_injection_guardrail
from app.services.planner_service import PlannerService, planner_service
from app.services.subagents import (
    BaseSubAgent,
    SubAgentRegistry,
    subagent_registry,
    TransactionSubAgent,
    IdentitySubAgent,
    SecuritySubAgent,
    WealthSubAgent,
    SupportFaqSubAgent
)
from app.logger import app_logger as logger


class AgentService:
    """
    High-level Coordinator for Banking AI operations.
    Coordinates security inspection, cache lookups, workflow engine,
    intent planning, and sequential sub-agent hand-offs.
    """

    def __init__(
        self,
        registry: Optional[SubAgentRegistry] = None,
        planner: Optional[IPlanGenerator] = None
    ):
        self.registry = registry or subagent_registry
        self.planner = planner or planner_service

        # Backward compatibility references for legacy access
        self.tx_agent = self.registry.get("TRANSACTION")
        self.id_agent = self.registry.get("IDENTITY")
        self.sec_agent = self.registry.get("SECURITY")
        self.wlt_agent = self.registry.get("WEALTH")
        self.faq_agent = self.registry.get("SUPPORT")

    def _get_subagent_by_domain(self, domain: str) -> BaseSubAgent:
        """
        Retrieves the sub-agent for the specified domain via the registry.
        (Maintained for backward compatibility with internal methods).
        """
        agent = self.registry.get(domain)
        return agent or self.tx_agent

    async def _generate_execution_plan(
        self,
        messages: List[ChatMessage],
        openai_client: Optional[AsyncOpenAI],
        model_override: Optional[str] = None,
        api_key_override: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Generates a DAG execution plan.
        Delegates directly to the dedicated PlannerService (SRP).
        """
        return await self.planner.generate_execution_plan(
            messages=messages,
            openai_client=openai_client,
            model_override=model_override,
            api_key_override=api_key_override
        )

    async def _execute_chained_plan(
        self,
        plan: ExecutionPlan,
        messages: List[ChatMessage],
        auth_token: str,
        openai_client: AsyncOpenAI,
        model_name: Optional[str] = None,
        api_key_override: Optional[str] = None,
        user_id: Optional[str] = "system"
    ) -> ChatResponse:
        """
        Executes sequential sub-agent hand-offs, passing observations between agents
        via an in-memory execution scratchpad.

        Data Flow:
        ----------
        Step 1 (e.g. Wealth): Converts 500 USD -> 431.25 EUR
                    │
                    ▼
            [ Scratchpad Entry ]
                    │
                    ▼
        Step 2 (e.g. Transaction): Injects 431.25 EUR into transfer draft to recipient
        """
        scratchpad_logs: List[str] = []
        all_tools_used: List[str] = []
        last_action_type: Optional[str] = None
        last_action_data: Optional[Dict[str, Any]] = None
        accumulated_replies: List[str] = []

        total_steps = min(len(plan.plan), 4)  # Safety guardrail to avoid runaway loops

        logger.info(
            f"\n"
            f"╔═══════════════════════════════════════════════════════════════════════════════════╗\n"
            f"║ ⛓️ [Sequential Multi-Agent Execution] Dispatching {total_steps} Chained Steps                    ║\n"
            f"╚═══════════════════════════════════════════════════════════════════════════════════╝"
        )

        for idx in range(total_steps):
            step = plan.plan[idx]
            subagent = self._get_subagent_by_domain(step.domain)

            logger.info(
                f"\n▶️ [Executing Step {step.step}/{total_steps}] SubAgent: '{subagent.name}' ({step.domain})\n"
                f"   Objective: \"{step.objective}\""
            )

            step_response = await subagent.run(
                messages=messages,
                auth_token=auth_token,
                openai_client=openai_client,
                model=model_name,
                api_key_override=api_key_override,
                scratchpad_context=scratchpad_logs if scratchpad_logs else None,
                step_objective=step.objective,
                user_id=user_id
            )

            # Record step observation into scratchpad for next agents in the chain
            step_summary = f"Step {step.step} ({step.domain}): {step_response.reply}"
            scratchpad_logs.append(step_summary)
            accumulated_replies.append(step_response.reply)

            if step_response.tools_used:
                all_tools_used.extend(step_response.tools_used)

            # Preserve frontend action cards (e.g. TRANSFER_DRAFT, CARD_FROZEN)
            if step_response.action_type:
                last_action_type = step_response.action_type
                last_action_data = step_response.action_data

        # Final consolidated response formatting
        if len(accumulated_replies) == 1:
            final_reply = accumulated_replies[0]
        else:
            final_reply = "\n\n---\n\n".join(accumulated_replies)

        return ChatResponse(
            reply=final_reply,
            action_type=last_action_type,
            action_data=last_action_data,
            tools_used=list(dict.fromkeys(all_tools_used))
        )

    async def process_chat(
        self,
        messages: List[ChatMessage],
        auth_token: str,
        api_key_override: Optional[str] = None,
        model_override: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Main entrypoint for customer conversational interactions.

        Step-by-step pipeline:
        0. Edge Security Inspection: Blocks prompt injections & jailbreaks (< 0.5 ms).
        1. Redis Fast-Path Cache: Returns instant semantic answer if query was previously answered (0-4 ms).
        2. Long-Running Workflow Engine: Checks for active 7-day multi-turn application drafts in Redis.
        3. Model Execution Resolution: Resolves dedicated paid model vs. free-tier fallback pool.
        4. Intent Planning: Decomposes inquiry into single-step or multi-step execution plan.
        5. Execution: Dispatches either fast-path single sub-agent or chained multi-agent loop.
        6. Workflow Accumulation & Auto-Cache: Updates 7-day workflow state and caches semantic FAQ answers.
        """
        last_msg = messages[-1].content if messages else ""

        # -------------------------------------------------------------
        # Step 0: Edge Security Guardrail (Prompt Injection Defense)
        # -------------------------------------------------------------
        is_attack, attack_category, refusal = prompt_injection_guardrail.inspect_prompt(last_msg)
        if is_attack:
            logger.warning(
                f"🚨 [PROMPT INJECTION BLOCKED] Category: {attack_category} | "
                f"User: {user_id or 'anonymous'} | Prompt: '{last_msg[:80]}...'"
            )
            return ChatResponse(
                reply=refusal,
                action_type=None,
                action_data=None,
                tools_used=[f"prompt_injection_guardrail ({attack_category.lower()})"],
                active_workflow=None
            )

        # -------------------------------------------------------------
        # Step 1: Global Fast-Path (Redis Exact & Semantic Cache)
        # -------------------------------------------------------------
        cached = await rag_cache_service.get_cached_answer(last_msg)
        if cached and cached.get("reply"):
            logger.info(f"⚡ [Redis Cache HIT] Returning cached answer for query: '{last_msg}'")
            return ChatResponse(
                reply=cached["reply"],
                action_type=cached.get("action_type"),
                action_data=cached.get("action_data"),
                tools_used=cached.get("tools_used") or ["search_bank_faq (redis_semantic_cached)"],
                active_workflow=None
            )

        # -------------------------------------------------------------
        # Step 2: Long-Running Multi-Turn Workflow State (7-Day TTL)
        # -------------------------------------------------------------
        active_wf = await workflow_state_service.get_active_workflow(user_id) if user_id else None

        if active_wf and user_id:
            cancel_keywords = ["cancel application", "batal pengajuan", "cancel workflow", "reset form", "batal kpr"]
            if any(kw in last_msg.lower() for kw in cancel_keywords):
                await workflow_state_service.cancel_workflow(user_id)
                return ChatResponse(
                    reply=f"🚫 Your active **{active_wf.workflow_type}** application has been cancelled and cleared. Let me know how else I can help!",
                    action_type=None,
                    action_data=None,
                    tools_used=[],
                    active_workflow=None
                )

        # -------------------------------------------------------------
        # Step 3: Model Execution Plan Resolution
        # -------------------------------------------------------------
        db_models = await model_fallback.fetch_models_from_db()
        plan = model_fallback.resolve_model_execution_plan(
            api_key=api_key_override,
            model_override=model_override,
            active_db_models=db_models
        )

        if plan.error:
            logger.warning(f"[CHAT VALIDATION ERROR] {plan.error}")
            return ChatResponse(
                reply=f"⚠️ Validation Error: {plan.error}",
                action_type=None,
                action_data=None,
                tools_used=[],
                active_workflow=active_wf
            )

        # Initialize AsyncOpenAI client configured for OpenRouter
        api_key_to_use = api_key_override or "dummy_key_for_free_models"
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key_to_use,
            timeout=30.0
        )

        # -------------------------------------------------------------
        # Step 4: Planner Orchestrator DAG Generation
        # -------------------------------------------------------------
        exec_plan = await self._generate_execution_plan(
            messages=messages,
            openai_client=client,
            model_override=model_override,
            api_key_override=api_key_override
        )

        # -------------------------------------------------------------
        # Step 5: Execution (Fast Path vs Chained DAG)
        # -------------------------------------------------------------
        if not exec_plan.is_multistep and len(exec_plan.plan) <= 1:
            # Single-Intent Fast Path
            target_domain = exec_plan.plan[0].domain if exec_plan.plan else "TRANSACTION"
            subagent = self._get_subagent_by_domain(target_domain)
            logger.info(f"⚡ [Fast Path Execution] Routing directly to '{subagent.name}' ({target_domain})")
            chat_res = await subagent.run(
                messages=messages,
                auth_token=auth_token,
                openai_client=client,
                model=model_override,
                api_key_override=api_key_override,
                user_id=user_id or "system"
            )
        else:
            # Multi-Step Chained DAG Execution
            chat_res = await self._execute_chained_plan(
                plan=exec_plan,
                messages=messages,
                auth_token=auth_token,
                openai_client=client,
                model_name=model_override,
                api_key_override=api_key_override,
                user_id=user_id or "system"
            )

        # -------------------------------------------------------------
        # Step 6: Workflow State Accumulation & Semantic Caching
        # -------------------------------------------------------------
        if user_id:
            chat_res.active_workflow = await workflow_state_service.get_active_workflow(user_id)

        # Auto-cache FAQ answers in Redis if the inquiry was purely informational
        if chat_res.tools_used and any("search_bank_faq" in t for t in chat_res.tools_used) and not chat_res.action_type:
            await rag_cache_service.cache_answer(
                query=last_msg,
                reply=chat_res.reply,
                tools_used=chat_res.tools_used,
                action_type=chat_res.action_type,
                action_data=chat_res.action_data
            )

        return chat_res


# Global singleton instance for the application
agent_service = AgentService()

# Re-export classes for backward compatibility
__all__ = [
    "AgentService",
    "agent_service",
    "BaseSubAgent",
    "TransactionSubAgent",
    "IdentitySubAgent",
    "SecuritySubAgent",
    "WealthSubAgent",
    "SupportFaqSubAgent",
]
