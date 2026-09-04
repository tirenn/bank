"""
Base Sub-Agent Implementation for Tirenn Banking Microservice.
=============================================================
This class provides the foundational behavior for all domain-specific AI agents
(Transaction, Identity, Security, Wealth, and Support FAQ).

SOLID Principles Applied:
- Liskov Substitution Principle (LSP): Subclasses inherit this contract and can
  be substituted anywhere without breaking caller expectations.
- Dependency Inversion Principle (DIP): Depends on the ISubAgent protocol and
  MCP repository port rather than hardcoded global implementations.
"""

from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI

from app.domain.schemas import ChatMessage, ChatResponse
from app.repositories.mcp_repository import mcp_repository
from app.services.prompt_loader import load_prompt
from app.services.react_harness import react_harness
from app.logger import app_logger as logger


class BaseSubAgent:
    """
    Base class for all domain sub-agents.
    Handles system prompt loading, MCP tool retrieval, and execution of the ReAct reasoning loop.

    Attributes:
        name (str): Human-readable name of the sub-agent (e.g., 'TransactionSubAgent').
        domain (str): Domain identifier matching MCP tools (e.g., 'transaction').
        prompt_file (str): Markdown file name containing the system instructions.
    """

    def __init__(self, name: str, domain: str, prompt_file: str):
        self.name = name
        self.domain = domain
        self.prompt_file = prompt_file
        self.system_prompt = load_prompt(prompt_file)
        self._cached_tools: Optional[List[Dict[str, Any]]] = None

    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Retrieves the list of tools available to this sub-agent.
        Tools are cached in-memory after the first fetch to minimize overhead.
        """
        if self._cached_tools is None:
            self._cached_tools = await mcp_repository.list_tools(self.domain)
        return self._cached_tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        auth_token: Optional[str] = None
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        Dispatches tool execution to the private Model Context Protocol (MCP) server.
        Forwards the customer's authenticated JWT to preserve backend authorization boundaries.
        """
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
        """
        Runs the sub-agent's reasoning loop for a customer request or chained DAG step.

        Args:
            messages: Conversation history leading up to the current turn.
            auth_token: Customer's signed JWT token.
            openai_client: AsyncOpenAI client configured for OpenRouter.
            model: Optional model override (e.g. from admin panel).
            api_key_override: Optional paid API key override.
            scratchpad_context: Observations from previous agents in a multi-step chain.
            step_objective: The specific goal for this sub-agent in a multi-agent plan.
            user_id: Customer ID used for telemetry and rate-limiting.

        Returns:
            ChatResponse containing the reply text, tools used, and optional action cards.
        """
        tools = await self.get_tools()

        if not openai_client:
            return ChatResponse(
                reply=(
                    "⚠️ AI Service is offline or OpenRouter API key is not configured. "
                    "Please configure an API key in settings or verify server environment variables."
                ),
                action_type=None,
                action_data=None,
                tools_used=[]
            )

        # Ensure latest prompt content is loaded (hot-reloaded if prompt file changed)
        prompt_content = load_prompt(self.prompt_file) or self.system_prompt

        try:
            # Delegate to the ReAct reasoning loop harness
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
