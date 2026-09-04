import logging
import json
from typing import List, Dict, Any, Optional, Callable, Awaitable, Tuple
from openai import AsyncOpenAI
from app.domain.schemas import ChatMessage, ChatResponse
from app.services.model_fallback import model_fallback
from app.services.pii_redactor import redact_text, redact_data

from app.logger import app_logger as logger



def _format_context_for_log(context: List[Dict[str, Any]]) -> str:
    """Helper to format conversation context for clear inspection in logs."""
    formatted_turns = []
    for idx, msg in enumerate(context, 1):
        role = msg.get("role", "unknown").upper()
        content = msg.get("content")
        tool_calls = msg.get("tool_calls")
        tool_name = msg.get("name")
        
        turn_str = f"  [{idx}] Role: {role}"
        if tool_name:
            turn_str += f" (Tool: {tool_name})"
        if content:
            # Truncate very long content in multi-turn context display for readability
            preview = content if len(str(content)) <= 300 else f"{str(content)[:300]}... [truncated {len(str(content))} chars]"
            turn_str += f"\n      Content: {preview}"
        if tool_calls:
            calls_preview = [f"{tc.get('function', {}).get('name')}({tc.get('function', {}).get('arguments')})" for tc in tool_calls]
            turn_str += f"\n      Tool Calls: {', '.join(calls_preview)}"
        formatted_turns.append(turn_str)
    return "\n".join(formatted_turns)


class ReActLoopHarness:
    """
    Native ReAct (Reasoning + Acting) Loop Harness for Banking Copilot.
    ===================================================================

    What is the ReAct Pattern?
    --------------------------
    ReAct stands for "Reasoning + Acting". Instead of answering in one shot,
    the AI follows an iterative cycle:
    
         ┌────────────────────────────────────────────────────────┐
         │ 1. Thought:    The LLM reasons about what tool to call │
         │       │                                                │
         │       ▼                                                │
         │ 2. Action:     Calls an MCP banking tool (e.g. check) │
         │       │                                                │
         │       ▼                                                │
         │ 3. Observation: Receives real data back from banking   │
         │       │                                                │
         │       ▼                                                │
         │ 4. Thought:    Synthesizes the final helpful answer   │
         └────────────────────────────────────────────────────────┘

    Key Features:
    - Context Logging: Full trace of messages, tool arguments, and results.
    - Loop Guard: Prevents runaway tool execution via max_iterations (default 5).
    - Dynamic Feedback: Feeds tool observations back into context turns.
    - Action Cards: Extracts UI events (e.g. TRANSFER_DRAFT) for frontend rendering.
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
        api_key_override: Optional[str] = None,
        scratchpad_context: Optional[List[str]] = None,
        step_objective: Optional[str] = None,
        domain: Optional[str] = "AGENT",
        user_id: Optional[str] = "system"
    ) -> ChatResponse:
        """
        Runs the ReAct reasoning loop with full execution logging and optional inter-agent scratchpad injection.
        """
        if not openai_client or not tools:
            raise ValueError("OpenAI client and tools are required for ReAct loop execution.")

        # Initialize conversation context with PII sanitization
        conversation_context: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        if scratchpad_context:
            scratchpad_text = "\n".join([f"• {entry}" for entry in scratchpad_context])
            conversation_context.append({
                "role": "system",
                "content": f"📋 [INTER-AGENT SCRATCHPAD (PREVIOUS AGENT OBSERVATIONS)]:\n{scratchpad_text}\nUse the exact figures, currencies, and account numbers from previous steps."
            })

        if step_objective:
            conversation_context.append({
                "role": "system",
                "content": f"🎯 [CURRENT STEP OBJECTIVE]: {step_objective}"
            })

        for m in user_messages:
            sanitized_content = redact_text(m.content) if m.content else ""
            conversation_context.append({"role": m.role, "content": sanitized_content})

        tools_used_history: List[str] = []
        last_action_type: Optional[str] = None
        last_action_data: Optional[Dict[str, Any]] = None
        observations_summary: List[str] = []

        logger.info(
            f"\n"
            f"╔═══════════════════════════════════════════════════════════════════════╗\n"
            f"║ 🤖 [ReAct Loop] Starting Reasoning Session (Max Steps: {self.max_iterations})         ║\n"
            f"╚═══════════════════════════════════════════════════════════════════════╝"
        )

        for iteration in range(1, self.max_iterations + 1):
            logger.info(
                f"\n--- [ReAct Step {iteration}/{self.max_iterations}] Preparing LLM Completion ---\n"
                f"📥 [Context Sent to Model ({len(conversation_context)} turns)]:\n"
                f"{_format_context_for_log(conversation_context)}\n"
                f"🛠️ [Available Tools ({len(tools)})]: {[t.get('function', {}).get('name') for t in tools]}"
            )

            choice, successful_model, err_msg = await model_fallback.execute_completion(
                openai_client=openai_client,
                messages=conversation_context,
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
                model_override=model_override,
                api_key_override=api_key_override,
                domain=domain,
                user_id=user_id
            )


            # Handle quota limit / fatal failure across all models
            if err_msg and not choice:
                logger.error(f"❌ [ReAct Step {iteration}] Model pool failed: {err_msg}")
                return ChatResponse(
                    reply=err_msg,
                    action_type=last_action_type,
                    action_data=last_action_data,
                    tools_used=tools_used_history
                )

            if not choice:
                logger.warning(f"⚠️ [ReAct Step {iteration}] Empty choice returned from model.")
                break

            # ----------------------------------------------------------------
            # SCENARIO A: LLM decided to call one or more tools (ACTION)
            # ----------------------------------------------------------------
            if choice.tool_calls and len(choice.tool_calls) > 0:
                logger.info(
                    f"\n🤖 [Model Response (Iteration {iteration})] (Model: {successful_model}):\n"
                    f"   • Thought / Content: {choice.content or '(None - Direct Tool Call)'}\n"
                    f"   • Tool Calls Count: {len(choice.tool_calls)}"
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
                        logger.warning(f"⚠️ [ReAct Step {iteration}] Failed to parse tool arguments: {json_err}")
                        t_args = {}

                    logger.info(
                        f"\n⚡ [Tool Execution Invoked (Iteration {iteration})]:\n"
                        f"   • Tool Name: {t_name}\n"
                        f"   • Arguments: {json.dumps(t_args, indent=2)}"
                    )
                    tools_used_history.append(t_name)

                    # Execute tool via MCP
                    obs_text, act_type, act_data = await tool_executor(t_name, t_args, auth_token)
                    observations_summary.append(obs_text)

                    logger.info(
                        f"\n📋 [Tool Response / Observation (Iteration {iteration})]:\n"
                        f"   • Tool: {t_name}\n"
                        f"   • Observation Result: {obs_text}\n"
                        f"   • Action Type: {act_type or '(None)'}\n"
                        f"   • Action Data: {json.dumps(act_data) if act_data else '(None)'}"
                    )

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
            logger.info(
                f"\n🏁 [ReAct Final Answer (Iteration {iteration})] (Model: {successful_model}):\n"
                f"   • Reply: {final_content}\n"
                f"   • Total Tools Used: {tools_used_history}\n"
                f"   • Action Emitted: {last_action_type or '(None)'}"
            )

            return ChatResponse(
                reply=final_content,
                action_type=last_action_type,
                action_data=last_action_data,
                tools_used=tools_used_history
            )

        # Iteration limit reached: Synthesize gathered observations
        logger.warning(f"⚠️ [ReAct Harness] Reached max iterations ({self.max_iterations}). Synthesizing collected observations.")
        fallback_reply = "\n\n".join(observations_summary) if observations_summary else "I have completed processing your request."
        
        return ChatResponse(
            reply=fallback_reply,
            action_type=last_action_type,
            action_data=last_action_data,
            tools_used=tools_used_history
        )

react_harness = ReActLoopHarness(max_iterations=5)
