import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI
from app.config import settings
from app.domain.schemas import ChatMessage, ChatResponse, PlanStep, ExecutionPlan, ScratchpadEntry
from app.repositories.mcp_repository import mcp_repository
from app.repositories.faq_repository import faq_repository

from app.services.model_fallback import model_fallback
from app.services.react_harness import react_harness
from app.services.prompt_loader import load_prompt
from app.services.rag_cache_service import rag_cache_service
from app.services.workflow_state_service import workflow_state_service
from app.services.cost_tracker_service import cost_tracker_service
from app.services.prompt_injection_guardrail import prompt_injection_guardrail

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
        api_key_override: Optional[str] = None,
        scratchpad_context: Optional[List[str]] = None,
        step_objective: Optional[str] = None,
        user_id: Optional[str] = "system"
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
            # Full Model-Driven: Execute multi-turn ReAct Loop Harness with optional scratchpad
            return await react_harness.execute_loop(
                system_prompt=prompt_content,
                user_messages=messages,
                tools=tools,
                tool_executor=self.execute_tool,
                auth_token=auth_token,
                openai_client=openai_client,
                model_override=model,
                api_key_override=api_key_override,
                scratchpad_context=scratchpad_context,
                step_objective=step_objective,
                domain=self.domain.upper(),
                user_id=user_id
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
        if self._cached_tools is None:
            self._cached_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_bank_faq",
                        "description": "Semantic search across Tirenn Bank vector FAQ knowledge base for policies, wire fees, rules, APY interest, and help articles.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language query to search in vector knowledge base"
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "Number of top matching FAQ entries to retrieve (default: 3)",
                                    "default": 3
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            ]
        return self._cached_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], auth_token: Optional[str] = None) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        if tool_name == "search_bank_faq":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 3)
            results = await faq_repository.search(query=query, n_results=top_k)
            if not results:
                return "No matching FAQ articles found in knowledge base.", None, None

            formatted = "\n\n".join([
                f"### [FAQ Match {i+1}] {item.get('metadata', {}).get('question', 'Q&A')}\n"
                f"Category: {item.get('metadata', {}).get('category', 'general')}\n"
                f"{item.get('document', '')}"
                for i, item in enumerate(results)
            ])
            return formatted, None, None

        return f"Unknown FAQ tool: {tool_name}", None, None


class AgentService:
    def __init__(self):
        self.tx_agent = TransactionSubAgent()
        self.id_agent = IdentitySubAgent()
        self.sec_agent = SecuritySubAgent()
        self.wlt_agent = WealthSubAgent()
        self.faq_agent = SupportFaqSubAgent()

    def _get_subagent_by_domain(self, domain: str) -> BaseSubAgent:
        d = domain.upper()
        if d == "IDENTITY":
            return self.id_agent
        elif d == "SECURITY":
            return self.sec_agent
        elif d == "WEALTH":
            return self.wlt_agent
        elif d == "SUPPORT":
            return self.faq_agent
        else:
            return self.tx_agent

    async def _generate_execution_plan(
        self,
        messages: List[ChatMessage],
        openai_client: Optional[AsyncOpenAI],
        model_override: Optional[str] = None,
        api_key_override: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Planner Orchestrator: Decomposes the user's prompt into an ExecutionPlan DAG.
        """
        latest_user_text = messages[-1].content if messages else ""
        default_single_plan = ExecutionPlan(
            is_multistep=False,
            plan=[PlanStep(step=1, domain="TRANSACTION", objective=latest_user_text)]
        )

        if not openai_client or not messages:
            return default_single_plan

        router_system_prompt = load_prompt("supervisor_router.md") or (
            "You are Tirenn Bank's Supervisor Orchestrator. Classify into TRANSACTION, IDENTITY, SECURITY, WEALTH, or SUPPORT."
        )

        try:
            context = [
                {"role": "system", "content": router_system_prompt},
                {"role": "user", "content": f"Analyze and create an execution plan for this customer inquiry:\n\"{latest_user_text}\""}
            ]

            choice, successful_model, err = await model_fallback.execute_completion(
                openai_client=openai_client,
                messages=context,
                temperature=0.0,
                model_override=model_override,
                api_key_override=api_key_override
            )

            if choice and choice.content:
                content = choice.content.strip()

                # 1. Try parsing structured JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group(0))
                        steps_data = parsed.get("plan", [])
                        valid_steps: List[PlanStep] = []
                        for s in steps_data:
                            dom = str(s.get("domain", "")).strip().upper()
                            if dom in ["TRANSACTION", "IDENTITY", "SECURITY", "WEALTH", "SUPPORT"]:
                                valid_steps.append(PlanStep(
                                    step=s.get("step", len(valid_steps) + 1),
                                    domain=dom,
                                    objective=str(s.get("objective", latest_user_text))
                                ))

                        if valid_steps:
                            is_multistep = parsed.get("is_multistep", len(valid_steps) > 1)
                            logger.info(
                                f"🗺️ [Planner Orchestrator DAG] Generated Plan (Multi-step: {is_multistep}, Steps: {len(valid_steps)}) via {successful_model}:\n" +
                                "\n".join([f"   [{s.step}] Domain: {s.domain} | Objective: {s.objective}" for s in valid_steps])
                            )
                            return ExecutionPlan(
                                is_multistep=is_multistep,
                                plan=valid_steps,
                                rationale=parsed.get("rationale")
                            )
                    except Exception as parse_err:
                        logger.debug(f"[Plan JSON Parse Exception]: {parse_err}")

                # 2. Fallback: Parse single domain keyword
                content_upper = content.upper()
                for valid_domain in ["WEALTH", "SECURITY", "IDENTITY", "SUPPORT", "TRANSACTION"]:
                    if valid_domain in content_upper:
                        logger.info(f"🧠 [LLM Supervisor Router] Direct single-step classified to: '{valid_domain}' (via {successful_model})")
                        return ExecutionPlan(
                            is_multistep=False,
                            plan=[PlanStep(step=1, domain=valid_domain, objective=latest_user_text)]
                        )

        except Exception as e:
            logger.warning(f"[Planner Orchestrator Fallback]: {e}")

        return default_single_plan

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
        Executes sequential sub-agent hand-offs, maintaining a shared scratchpad across steps.
        """
        scratchpad_logs: List[str] = []
        all_tools_used: List[str] = []
        last_action_type: Optional[str] = None
        last_action_data: Optional[Dict[str, Any]] = None
        accumulated_replies: List[str] = []

        total_steps = min(len(plan.plan), 4) # Guardrail cap

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

        # Final response formatting
        if len(accumulated_replies) == 1:
            final_reply = accumulated_replies[0]
        else:
            # Combine sequential agent outputs cleanly
            final_reply = "\n\n---\n\n".join(accumulated_replies)

        return ChatResponse(
            reply=final_reply,
            action_type=last_action_type,
            action_data=last_action_data,
            tools_used=list(dict.fromkeys(all_tools_used)) # Remove duplicate tool names
        )


    async def process_chat(
        self,
        messages: List[ChatMessage],
        auth_token: str,
        api_key_override: Optional[str] = None,
        model_override: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ChatResponse:
        last_msg = messages[-1].content if messages else ""

        # 0. Edge Security Guardrail: Prompt Injection & Jailbreak Defense (< 0.5 ms)
        is_attack, attack_category, refusal = prompt_injection_guardrail.inspect_prompt(last_msg)
        if is_attack:
            logger.warning(
                f"🚨 [PROMPT INJECTION BLOCKED] Category: {attack_category} | User: {user_id or 'anonymous'} | Prompt: '{last_msg[:80]}...'"
            )
            return ChatResponse(
                reply=refusal,
                action_type=None,
                action_data=None,
                tools_used=[f"prompt_injection_guardrail ({attack_category.lower()})"],
                active_workflow=None
            )

        # 1. Global Fast-Path: Check Redis Exact & Semantic Cache (0-4 ms)
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

        # 2. Check for Active Long-Running Workflow in Redis (7-Day TTL)
        active_wf = await workflow_state_service.get_active_workflow(user_id) if user_id else None

        if active_wf and user_id:
            # Check for explicit cancellation request
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

        # 3. Centralized Model Execution Plan & Strict Validation
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

        api_key = api_key_override or settings.OPENROUTER_API_KEY
        model_name = plan.models[0] if plan.models else None

        if not api_key or not api_key.strip() or api_key == "YOUR_OPENROUTER_API_KEY_HERE":
            return ChatResponse(
                reply="⚠️ AI Service is offline or OpenRouter API key is not configured. Please configure an API key in admin settings or verify server environment variables.",
                action_type=None,
                action_data=None,
                tools_used=[],
                active_workflow=active_wf
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

        # Prepare messages with workflow state injection if active
        enriched_messages = list(messages)
        if active_wf:
            wf_context_str = (
                f"[ACTIVE LONG-RUNNING WORKFLOW STATE (FROM REDIS)]:\n"
                f"• Type: {active_wf.workflow_type}\n"
                f"• Progress: Step {active_wf.current_step} of {active_wf.total_steps} ({active_wf.status})\n"
                f"• Previously Collected Application Data: {json.dumps(active_wf.collected_data)}\n"
                f"Resume this application seamlessly. Validate the next required field from the customer."
            )
            enriched_messages.insert(0, ChatMessage(role="system", content=wf_context_str))

        # 4. Planner Orchestrator: Generate single or multi-step execution plan
        exec_plan = await self._generate_execution_plan(enriched_messages, openai_client, model_name, api_key_override)

        # 5. Fast-Path: Single Sub-Agent Direct Execution
        if not exec_plan.is_multistep or len(exec_plan.plan) <= 1:
            target_domain = exec_plan.plan[0].domain if exec_plan.plan else "TRANSACTION"
            subagent = self._get_subagent_by_domain(target_domain)
            response = await subagent.run(
                messages=enriched_messages,
                auth_token=auth_token,
                openai_client=openai_client,
                model=model_name,
                api_key_override=api_key_override,
                user_id=user_id or "system"
            )
        else:
            # 6. Multi-Step Chained Sequential Execution
            response = await self._execute_chained_plan(
                plan=exec_plan,
                messages=enriched_messages,
                auth_token=auth_token,
                openai_client=openai_client,
                model_name=model_name,
                api_key_override=api_key_override,
                user_id=user_id or "system"
            )


        # Attach active workflow state to response
        response.active_workflow = active_wf
        return response



agent_service = AgentService()
