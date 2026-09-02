import asyncio
from typing import List, Tuple
from app.domain.schemas import ChatMessage, ExecutionPlan
from app.services.agent_service import agent_service
from app.config import settings
from openai import AsyncOpenAI

class SequentialOrchestratorEvaluator:
    """
    Evaluation Suite for Planner Orchestrator & Multi-Agent Sequential Hand-offs.
    """

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY.strip(),
            timeout=15.0
        )

    async def eval_plan_generation(self) -> List[Tuple[str, str, bool, str]]:
        results = []

        # Case 1: Multi-step Forex + Transfer
        prompt1 = [ChatMessage(role="user", content="Check live conversion for 500 USD to EUR and prepare transfer to Sarah")]
        plan1: ExecutionPlan = await agent_service._generate_execution_plan(prompt1, self.client)
        domains1 = [s.domain for s in plan1.plan]
        pass1 = ("WEALTH" in domains1) and ("TRANSACTION" in domains1)
        results.append(("Orchestrator", "DAG Plan: Forex + Transfer Chained", pass1, f"Steps: {domains1} (is_multistep={plan1.is_multistep})"))

        # Case 2: Multi-step Security Freeze + Transaction History
        prompt2 = [ChatMessage(role="user", content="Freeze my lost debit card and check my recent transactions")]
        plan2: ExecutionPlan = await agent_service._generate_execution_plan(prompt2, self.client)
        domains2 = [s.domain for s in plan2.plan]
        pass2 = ("SECURITY" in domains2) and ("TRANSACTION" in domains2)
        results.append(("Orchestrator", "DAG Plan: Freeze Card + History Chained", pass2, f"Steps: {domains2} (is_multistep={plan2.is_multistep})"))

        # Case 3: Single-Intent Fast Path (Balance)
        prompt3 = [ChatMessage(role="user", content="What is my account balance?")]
        plan3: ExecutionPlan = await agent_service._generate_execution_plan(prompt3, self.client)
        domains3 = [s.domain for s in plan3.plan]
        pass3 = (len(plan3.plan) == 1) and (domains3[0] == "TRANSACTION")
        results.append(("Orchestrator", "DAG Plan: Single-Intent Fast Path (Balance)", pass3, f"Steps: {domains3} (is_multistep={plan3.is_multistep})"))

        # Case 4: Single-Intent Fast Path (Support FAQ)
        prompt4 = [ChatMessage(role="user", content="What are the wire transfer fees?")]
        plan4: ExecutionPlan = await agent_service._generate_execution_plan(prompt4, self.client)
        domains4 = [s.domain for s in plan4.plan]
        pass4 = (len(plan4.plan) == 1) and (domains4[0] == "SUPPORT")
        results.append(("Orchestrator", "DAG Plan: Single-Intent Fast Path (FAQ)", pass4, f"Steps: {domains4} (is_multistep={plan4.is_multistep})"))

        return results


sequential_evaluator = SequentialOrchestratorEvaluator()
