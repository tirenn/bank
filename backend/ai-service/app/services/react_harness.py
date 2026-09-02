import logging
import json
from typing import List, Dict, Any, Optional, Callable, Awaitable, Tuple
from openai import AsyncOpenAI
from app.domain.schemas import ChatMessage, ChatResponse
from app.services.model_fallback import model_fallback
from app.services.pii_redactor import redact_text, redact_data

logger = logging.getLogger("ai_service.react_harness")

class ReActLoopHarness:
    """
    Native ReAct (Reasoning + Acting) Loop Harness.
    Executes a multi-turn Thought -> Action (Tool Call) -> Observation (Tool Output) -> Thought cycle
    without third-party graph framework dependencies.

    Key Features:
    - Iteration Guard: Prevents infinite loops via max_iterations (default 5).
    - Message History Accumulator: Feeds tool outputs (Observations) back to LLM context for multi-step reasoning.
    - Multi-Tool Chaining: Allows LLM to perform sequential operations (e.g. Check Balance -> Draft Transfer -> Calculate Fee).
    - Resilient Fallback: Uses multi-model fallback executor on every step.
    - Structured Action & UI Event Aggregation: Preserves action_type & action_data for frontend widgets.
    """

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations

    async def execute_loop(
        self,
        system_prompt: str,
        user_messages: List[ChatMessage],
        tools: List[Dict[str, Any]],
        tool_executor: Callable[[str, Dict[str, Any], Optional[str]], Awaitable[Tuple[str, Optional[str], Optional[Dict[str, Any]]]]],
        auth_token: Optional[str] = None,
        openai_client: Optional[AsyncOpenAI] = None,
        model_override: Optional[str] = None,
        api_key_override: Optional[str] = None
    ) -> ChatResponse:
        """
        Runs the ReAct reasoning loop.
        """
        if not openai_client or not tools:
            raise ValueError("OpenAI client and tools are required for ReAct loop execution.")

        # Initialize conversation context with PII sanitization
        conversation_context: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        for m in user_messages:
            sanitized_content = redact_text(m.content) if m.content else ""
            conversation_context.append({"role": m.role, "content": sanitized_content})

        tools_used_history: List[str] = []
        last_action_type: Optional[str] = None
        last_action_data: Optional[Dict[str, Any]] = None
        observations_summary: List[str] = []

        logger.info(f"[ReAct Harness] Starting reasoning loop (Max Iterations: {self.max_iterations})")

        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"[ReAct Harness] Iteration step [{iteration}/{self.max_iterations}]")

            choice, successful_model, err_msg = await model_fallback.execute_completion(
                openai_client=openai_client,
                messages=conversation_context,
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
                model_override=model_override,
                api_key_override=api_key_override
            )


            # Handle quota limit / fatal failure across all models
            if err_msg and not choice:
                logger.error(f"[ReAct Harness] Model pool failed on iteration {iteration}: {err_msg}")
                return ChatResponse(
                    reply=err_msg,
                    action_type=last_action_type,
                    action_data=last_action_data,
                    tools_used=tools_used_history
                )

            if not choice:
                break

            # ----------------------------------------------------------------
            # SCENARIO A: LLM decided to call one or more tools (ACTION)
            # ----------------------------------------------------------------
            if choice.tool_calls and len(choice.tool_calls) > 0:
                logger.info(
                    f"[ReAct Harness] Thought: Calling {len(choice.tool_calls)} tool(s) via model {successful_model}"
                )

                # Append assistant message with tool calls to context
                assistant_tool_call_entry: Dict[str, Any] = {
                    "role": "assistant",
                    "content": choice.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id or f"call_{i}",
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for i, tc in enumerate(choice.tool_calls)
                    ]
                }
                conversation_context.append(assistant_tool_call_entry)

                # Execute all tools requested by the LLM in this iteration step
                for tc in choice.tool_calls:
                    t_name = tc.function.name
                    try:
                        t_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except Exception as json_err:
                        logger.warning(f"[ReAct Harness] Failed to parse tool arguments: {json_err}")
                        t_args = {}

                    logger.info(f"[ReAct Harness] Executing Action: {t_name}({t_args})")
                    tools_used_history.append(t_name)

                    # Execute tool via MCP
                    obs_text, act_type, act_data = await tool_executor(t_name, t_args, auth_token)
                    observations_summary.append(obs_text)

                    if act_type:
                        last_action_type = act_type
                        last_action_data = act_data

                    # Append Observation (tool response) back into context for next ReAct iteration
                    conversation_context.append({
                        "role": "tool",
                        "tool_call_id": tc.id or f"call_{t_name}",
                        "name": t_name,
                        "content": str(obs_text)
                    })

                # Loop continues to next iteration so LLM can observe tool results!
                continue

            # ----------------------------------------------------------------
            # SCENARIO B: LLM provided Final Thought / Answer (NO MORE TOOLS)
            # ----------------------------------------------------------------
            final_content = (choice.content or "").strip()
            logger.info(f"[ReAct Harness] Final Answer reached on iteration {iteration}.")

            return ChatResponse(
                reply=final_content,
                action_type=last_action_type,
                action_data=last_action_data,
                tools_used=tools_used_history
            )

        # Iteration limit reached: Synthesize gathered observations
        logger.warning(f"[ReAct Harness] Reached max iterations ({self.max_iterations}). Synthesizing collected observations.")
        fallback_reply = "\n\n".join(observations_summary) if observations_summary else "I have completed processing your request."
        
        return ChatResponse(
            reply=fallback_reply,
            action_type=last_action_type,
            action_data=last_action_data,
            tools_used=tools_used_history
        )

react_harness = ReActLoopHarness(max_iterations=5)
