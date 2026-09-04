"""
Domain Interfaces & Protocols for Tirenn AI Banking Microservice.
================================================================
This module defines the abstract contracts (Interfaces) using Python's typing.Protocol.

SOLID Principles Applied:
- Interface Segregation Principle (ISP): Clients depend only on small, focused interfaces.
- Dependency Inversion Principle (DIP): High-level business logic depends on abstractions,
  not concrete low-level implementations.
"""

from typing import Protocol, List, Dict, Any, Optional, Tuple, runtime_checkable
from openai import AsyncOpenAI
from app.domain.schemas import ChatMessage, ChatResponse, ExecutionPlan


@runtime_checkable
class IToolExecutor(Protocol):
    """
    Protocol for executing a named tool with arguments.
    Any class or function that implements this signature can be passed as a tool executor.
    """
    async def __call__(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        auth_token: Optional[str] = None
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        Executes a banking tool.
        Returns:
            Tuple containing:
            1. output_text: Human-readable or JSON result for the LLM.
            2. action_type: Optional UI widget type (e.g. 'TRANSFER_DRAFT').
            3. action_data: Optional structured data for the frontend widget.
        """
        ...


@runtime_checkable
class ISubAgent(Protocol):
    """
    Contract for all Specialized Domain Sub-Agents in Tirenn Bank.
    Liskov Substitution Principle (LSP): Every sub-agent (Transaction, Wealth, etc.)
    can be used interchangeably wherever an ISubAgent is expected.
    """
    name: str
    domain: str

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Returns the list of MCP tool definitions available to this sub-agent."""
        ...

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        auth_token: Optional[str] = None
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """Executes a tool call requested by this sub-agent."""
        ...

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
        Executes the sub-agent reasoning loop for a specific customer request or chained step.
        """
        ...


@runtime_checkable
class IPlanGenerator(Protocol):
    """
    Contract for the Supervisor Planner Orchestrator.
    Single Responsibility Principle (SRP): Isolates the responsibility of analyzing
    customer intent and generating a Directed Acyclic Graph (DAG) execution plan.
    """
    async def generate_execution_plan(
        self,
        messages: List[ChatMessage],
        openai_client: Optional[AsyncOpenAI],
        model_override: Optional[str] = None,
        api_key_override: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Decomposes a customer inquiry into a single-step or multi-step ExecutionPlan.
        """
        ...


@runtime_checkable
class IGuardrail(Protocol):
    """
    Contract for prompt inspection and adversarial jailbreak guardrails.
    """
    def inspect_prompt(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Inspects text for prompt injection or adversarial attacks.
        Returns: (is_threat: bool, threat_category: Optional[str], refusal_message: Optional[str])
        """
        ...
