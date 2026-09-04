"""
Planner Service & Supervisor Orchestrator for Tirenn Banking Microservice.
=========================================================================
Single Responsibility Principle (SRP):
This service is solely responsible for decomposing complex customer requests
into an optimal Directed Acyclic Graph (DAG) Execution Plan.

Visual Workflow:
----------------
  Customer Inquiry: "Convert 500 USD to EUR then transfer to Sarah"
                              │
                              ▼
                 [ Supervisor Planner LLM ]
                              │
                              ▼
                    Generated DAG Plan:
          ┌────────────────────────────────────────┐
          │ Step 1: WEALTH (Forex Conversion)      │
          │ Step 2: TRANSACTION (Transfer to Sarah)│
          └────────────────────────────────────────┘
"""

import json
import re
from typing import List, Optional
from openai import AsyncOpenAI

from app.domain.schemas import ChatMessage, PlanStep, ExecutionPlan
from app.services.prompt_loader import load_prompt
from app.services.model_fallback import model_fallback
from app.logger import app_logger as logger


class PlannerService:
    """
    Supervisor Planner Orchestrator.
    Analyzes customer intent and generates a single-step or multi-step DAG ExecutionPlan.
    """

    VALID_DOMAINS = ["TRANSACTION", "IDENTITY", "SECURITY", "WEALTH", "SUPPORT"]

    async def generate_execution_plan(
        self,
        messages: List[ChatMessage],
        openai_client: Optional[AsyncOpenAI],
        model_override: Optional[str] = None,
        api_key_override: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Decomposes customer prompt into an ExecutionPlan DAG.

        Args:
            messages: List of recent chat messages from the customer.
            openai_client: Configured AsyncOpenAI client instance.
            model_override: Optional specific model name requested by caller.
            api_key_override: Optional paid OpenRouter API key.

        Returns:
            ExecutionPlan with is_multistep flag and ordered list of PlanSteps.
        """
        latest_user_text = messages[-1].content if messages else ""
        
        # Default fallback: single-step transaction intent
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

                # Strategy 1: Attempt structured JSON DAG plan parsing
                plan = self._parse_json_plan(content, latest_user_text, successful_model)
                if plan:
                    return plan

                # Strategy 2: Fallback keyword matching for single domain classification
                plan = self._parse_keyword_domain(content, latest_user_text, successful_model)
                if plan:
                    return plan

        except Exception as e:
            logger.warning(f"[Planner Orchestrator Fallback]: {e}")

        return default_single_plan

    def _parse_json_plan(
        self,
        raw_content: str,
        fallback_objective: str,
        model_name: Optional[str] = None
    ) -> Optional[ExecutionPlan]:
        """
        Extracts and validates JSON plan structure from LLM response.
        """
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if not json_match:
            return None

        try:
            parsed = json.loads(json_match.group(0))
            steps_data = parsed.get("plan", [])
            valid_steps: List[PlanStep] = []

            for s in steps_data:
                dom = str(s.get("domain", "")).strip().upper()
                if dom in self.VALID_DOMAINS:
                    valid_steps.append(PlanStep(
                        step=s.get("step", len(valid_steps) + 1),
                        domain=dom,
                        objective=str(s.get("objective", fallback_objective))
                    ))

            if valid_steps:
                is_multistep = parsed.get("is_multistep", len(valid_steps) > 1)
                steps_repr = "\n".join([f"   [{s.step}] Domain: {s.domain} | Objective: {s.objective}" for s in valid_steps])
                logger.info(
                    f"🗺️ [Planner Orchestrator DAG] Generated Plan (Multi-step: {is_multistep}, Steps: {len(valid_steps)}) via {model_name}:\n"
                    f"{steps_repr}"
                )
                return ExecutionPlan(
                    is_multistep=is_multistep,
                    plan=valid_steps,
                    rationale=parsed.get("rationale")
                )
        except Exception as parse_err:
            logger.debug(f"[Plan JSON Parse Exception]: {parse_err}")

        return None

    def _parse_keyword_domain(
        self,
        raw_content: str,
        fallback_objective: str,
        model_name: Optional[str] = None
    ) -> Optional[ExecutionPlan]:
        """
        Extracts domain keyword when LLM responds with plain text instead of JSON.
        """
        content_upper = raw_content.upper()
        for valid_domain in self.VALID_DOMAINS:
            if valid_domain in content_upper:
                logger.info(f"🧠 [LLM Supervisor Router] Direct single-step classified to: '{valid_domain}' (via {model_name})")
                return ExecutionPlan(
                    is_multistep=False,
                    plan=[PlanStep(step=1, domain=valid_domain, objective=fallback_objective)]
                )
        return None


# Singleton instance
planner_service = PlannerService()
