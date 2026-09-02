import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI
from app.config import settings
from app.domain.schemas import ChatMessage, ChatResponse
from app.repositories.mcp_repository import mcp_repository
from app.repositories.faq_repository import faq_repository

from app.services.model_fallback import model_fallback
from app.services.react_harness import react_harness
from app.services.prompt_loader import load_prompt
from app.services.rag_cache_service import rag_cache_service

from app.logger import app_logger as logger



class BaseSubAgent:
    def __init__(self, name: str, domain: str, prompt_file: str):
        self.name = name
        self.domain = domain
        self.prompt_file = prompt_file
        self.system_prompt = load_prompt(prompt_file)
        self._cached_tools: Optional[List[Dict[str, Any]]] = None

    async def get_tools(self) -> List[Dict[str, Any]]:
        if self._cached_tools is None:
            self._cached_tools = await mcp_repository.list_tools(self.domain)
        return self._cached_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], auth_token: Optional[str] = None) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        return await mcp_repository.call_tool(self.domain, tool_name, arguments, auth_token)

    async def run(
        self,
        messages: List[ChatMessage],
        auth_token: Optional[str] = None,
        openai_client: Optional[AsyncOpenAI] = None,
        model: Optional[str] = None,
        api_key_override: Optional[str] = None
    ) -> ChatResponse:
        tools = await self.get_tools()

        if not openai_client:
            return ChatResponse(
                reply="⚠️ AI Service is offline or OpenRouter API key is not configured. Please configure an API key in settings or verify server environment variables.",
                action_type=None,
                action_data=None,
                tools_used=[]
            )

        prompt_content = load_prompt(self.prompt_file) or self.system_prompt
        try:
            # Full Model-Driven: Execute multi-turn ReAct Loop Harness
            return await react_harness.execute_loop(
                system_prompt=prompt_content,
                user_messages=messages,
                tools=tools,
                tool_executor=self.execute_tool,
                auth_token=auth_token,
                openai_client=openai_client,
                model_override=model,
                api_key_override=api_key_override
            )

        except Exception as e:
            logger.error(f"[ReAct Harness Error in {self.name}]: {e}", exc_info=True)
            return ChatResponse(
                reply=f"⚠️ An error occurred while processing your request via {self.name}: {str(e)}",
                action_type=None,
                action_data=None,
                tools_used=[]
            )


class TransactionSubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="TransactionSubAgent",
            domain="transaction",
            prompt_file="transaction_agent.md"
        )


class IdentitySubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="IdentitySubAgent",
            domain="identity",
            prompt_file="identity_agent.md"
        )


class SecuritySubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="SecuritySubAgent",
            domain="security",
            prompt_file="security_agent.md"
        )


class WealthSubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="WealthSubAgent",
            domain="wealth",
            prompt_file="wealth_agent.md"
        )


class SupportFaqSubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="SupportFaqSubAgent",
            domain="support",
            prompt_file="support_faq_agent.md"
        )

    async def get_tools(self) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "function": {
                "name": "search_bank_faq",
                "description": "Search banking policy, limits, fees, and FAQ in ChromaDB vector store.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            }
        }]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], auth_token: Optional[str] = None) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        query = arguments.get("query", "")
        res_text = faq_repository.search(query, n_results=3)
        return res_text, None, None

    async def run(
        self,
        messages: List[ChatMessage],
        auth_token: Optional[str] = None,
        openai_client: Optional[AsyncOpenAI] = None,
        model: Optional[str] = None
    ) -> ChatResponse:
        last_msg = messages[-1].content if messages else ""

        # 1. Query Redis RAG Answer Cache for fast sub-millisecond retrieval
        cached = await rag_cache_service.get_cached_answer(last_msg)
        if cached and cached.get("reply"):
            logger.info(f"⚡ Returning Redis cached RAG answer for query: '{last_msg}'")
            return ChatResponse(
                reply=cached["reply"],
                action_type=cached.get("action_type"),
                action_data=cached.get("action_data"),
                tools_used=cached.get("tools_used") or ["search_bank_faq (redis_semantic_cached)"]
            )

        # 2. Execute standard multi-turn ReAct loop with LLM & ChromaDB
        response = await super().run(messages, auth_token, openai_client, model)

        # 3. Store valid answer in Redis RAG cache on success
        if response and response.reply and not response.reply.startswith("⚠️"):
            tools = response.tools_used or ["search_bank_faq"]
            await rag_cache_service.set_cached_answer(
                query=last_msg,
                reply=response.reply,
                action_type=response.action_type,
                action_data=response.action_data,
                tools_used=tools
            )

        return response


class AgentService:
    """
    Supervisor Multi-Agent Orchestrator.
    - LLM-driven intent classification (NO hardcoded keywords).
    - Routes to specialized domain SubAgents (Transaction, Identity, Security, Wealth, SupportFaq).
    - Integrated with Redis Semantic & Exact Cache.
    """

    def __init__(self):
        self.tx_agent = TransactionSubAgent()
        self.id_agent = IdentitySubAgent()
        self.sec_agent = SecuritySubAgent()
        self.wlt_agent = WealthSubAgent()
        self.faq_agent = SupportFaqSubAgent()

    async def _classify_intent_llm(
        self,
        messages: List[ChatMessage],
        openai_client: Optional[AsyncOpenAI],
        model_override: Optional[str] = None,
        api_key_override: Optional[str] = None
    ) -> str:
        """
        Model-driven intent routing: Uses LLM to decide which SubAgent domain should handle the request.
        """
        if not openai_client or not messages:
            return "TRANSACTION"

        router_system_prompt = load_prompt("supervisor_router.md") or (
            "You are Tirenn Bank's Supervisor Orchestrator. Classify the user inquiry into exactly ONE domain:\n"
            "- TRANSACTION: For checking balances, wire transfers, transactions, statements, opening accounts.\n"
            "- IDENTITY: For viewing profile, updating address, and KYC documents.\n"
            "- SECURITY: For card locking/freezing, unfreezing, and daily transfer limits.\n"
            "- WEALTH: For currency conversion (forex), loan calculations, and beneficiaries.\n"
            "- SUPPORT: For bank policies, fee rules, APY rates, and FAQ search.\n\n"
            "Return ONLY the single uppercase domain word: TRANSACTION, IDENTITY, SECURITY, WEALTH, or SUPPORT."
        )


        try:
            latest_user_text = messages[-1].content if messages else ""
            context = [
                {"role": "system", "content": router_system_prompt},
                {"role": "user", "content": f"Classify this user request into ONE domain:\n\"{latest_user_text}\""}
            ]

            choice, successful_model, err = await model_fallback.execute_completion(
                openai_client=openai_client,
                messages=context,
                temperature=0.0,
                model_override=model_override,
                api_key_override=api_key_override
            )

            if choice and choice.content:
                domain_raw = choice.content.strip().upper()
                tokens = [t.strip(",.:;!?()[]{}'\"") for t in domain_raw.split()]
                for valid_domain in ["WEALTH", "SECURITY", "IDENTITY", "SUPPORT", "TRANSACTION"]:
                    if valid_domain in tokens:
                        logger.info(f"🧠 [LLM Supervisor Router] Classified user message to SubAgent: '{valid_domain}' (via {successful_model})")
                        return valid_domain
                for valid_domain in ["WEALTH", "SECURITY", "IDENTITY", "SUPPORT", "TRANSACTION"]:
                    if valid_domain in domain_raw:
                        logger.info(f"🧠 [LLM Supervisor Router] Classified user message to SubAgent: '{valid_domain}' (via {successful_model})")
                        return valid_domain

        except Exception as e:
            logger.warning(f"[LLM Supervisor Router] Routing fallback: {e}")

        return "TRANSACTION"



    async def process_chat(
        self,
        messages: List[ChatMessage],
        auth_token: str,
        api_key_override: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> ChatResponse:
        last_msg = messages[-1].content if messages else ""

        # 1. Global Fast-Path: Check Redis Exact & Semantic Cache (0-4 ms)
        cached = await rag_cache_service.get_cached_answer(last_msg)
        if cached and cached.get("reply"):
            logger.info(f"⚡ [Redis Cache HIT] Returning cached answer for query: '{last_msg}'")
            return ChatResponse(
                reply=cached["reply"],
                action_type=cached.get("action_type"),
                action_data=cached.get("action_data"),
                tools_used=cached.get("tools_used") or ["search_bank_faq (redis_semantic_cached)"]
            )

        # 2. Centralized Model Execution Plan & Strict Validation
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
                tools_used=[]
            )

        api_key = api_key_override or settings.OPENROUTER_API_KEY
        model_name = plan.models[0] if plan.models else None

        if not api_key or not api_key.strip() or api_key == "YOUR_OPENROUTER_API_KEY_HERE":
            return ChatResponse(
                reply="⚠️ AI Service is offline or OpenRouter API key is not configured. Please configure an API key in admin settings or verify server environment variables.",
                action_type=None,
                action_data=None,
                tools_used=[]
            )

        openai_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key.strip(),
            timeout=15.0,
            default_headers={
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "Antigravity Bank AI Assistant",
            }
        )

        # 3. LLM Supervisor decides which SubAgent handles the inquiry
        domain = await self._classify_intent_llm(messages, openai_client, model_name, api_key_override)

        # 4. Delegate to the chosen SubAgent
        if domain == "IDENTITY":
            return await self.id_agent.run(messages, auth_token, openai_client, model_name, api_key_override)
        elif domain == "SECURITY":
            return await self.sec_agent.run(messages, auth_token, openai_client, model_name, api_key_override)
        elif domain == "WEALTH":
            return await self.wlt_agent.run(messages, auth_token, openai_client, model_name, api_key_override)
        elif domain == "SUPPORT":
            return await self.faq_agent.run(messages, auth_token, openai_client, model_name, api_key_override)
        else:
            return await self.tx_agent.run(messages, auth_token, openai_client, model_name, api_key_override)



agent_service = AgentService()


