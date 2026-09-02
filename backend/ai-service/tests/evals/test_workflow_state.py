import time
from typing import List, Tuple
from app.services.workflow_state_service import workflow_state_service
from app.domain.schemas import WorkflowState

class WorkflowStateEvaluator:
    """
    Evaluation Suite for Long-Running Multi-Turn Workflow State Engine in Redis (7-Day TTL).
    """

    async def eval_workflow_lifecycle(self) -> List[Tuple[str, str, bool, str]]:
        results = []
        ts = int(time.time() * 1000)
        user_alpha = f"user_wf_alpha_{ts}"
        user_beta = f"user_wf_beta_{ts}"

        # 1. Connect Redis if needed
        if not workflow_state_service.rdb:
            await workflow_state_service.connect()

        # 2. Initialize Loan Application Workflow for User Alpha (Step 1)
        wf_alpha = await workflow_state_service.advance_workflow(
            user_id=user_alpha,
            workflow_type="LOAN_APPLICATION",
            step=1,
            new_data={"loan_type": "PERSONAL", "requested_amount": 35000, "term_months": 36},
            next_status="IN_PROGRESS"
        )
        pass_init = wf_alpha is not None and wf_alpha.current_step == 1
        results.append(("Workflow State", "Initialize Long-Running Loan Workflow (Step 1)", pass_init, f"Workflow ID: {wf_alpha.workflow_id if wf_alpha else 'None'}"))

        # 3. Simulate Next-Day Resume (Fetch from Redis)
        resumed_wf = await workflow_state_service.get_active_workflow(user_alpha)
        pass_resume = (
            resumed_wf is not None and
            resumed_wf.workflow_type == "LOAN_APPLICATION" and
            resumed_wf.collected_data.get("requested_amount") == 35000
        )
        results.append(("Workflow State", "Asynchronous Workflow Resume from Redis", pass_resume, f"Resumed Step: {resumed_wf.current_step if resumed_wf else 'None'}"))

        # 4. Advance to Step 2 with Income Verification Data
        wf_step2 = await workflow_state_service.advance_workflow(
            user_id=user_alpha,
            workflow_type="LOAN_APPLICATION",
            step=2,
            new_data={"monthly_income": 7500, "employment_status": "EMPLOYED"},
            next_status="WAITING_FOR_USER_INPUT"
        )
        pass_step2 = (
            wf_step2 is not None and
            wf_step2.current_step == 2 and
            wf_step2.collected_data.get("monthly_income") == 7500 and
            wf_step2.collected_data.get("requested_amount") == 35000  # Prior data preserved!
        )
        results.append(("Workflow State", "Accumulate Multi-Turn Form Fields (Step 2)", pass_step2, f"Total Keys: {len(wf_step2.collected_data) if wf_step2 else 0}"))

        # 5. Multi-Tenant Workflow Isolation (User Beta must NOT see User Alpha's workflow)
        beta_wf = await workflow_state_service.get_active_workflow(user_beta)
        pass_iso = beta_wf is None
        results.append(("Workflow State", "Multi-Tenant State Isolation (Zero Leakage)", pass_iso, "Beta Active: None (Isolated)"))

        # 6. Complete Workflow & Clean Teardown
        completed = await workflow_state_service.complete_workflow(user_alpha, "LOAN_APPLICATION")
        alpha_after_complete = await workflow_state_service.get_active_workflow(user_alpha)
        pass_teardown = completed and (alpha_after_complete is None)
        results.append(("Workflow State", "Workflow Completion & Redis Queue Teardown", pass_teardown, "Draft Key Removed Successfully"))

        return results


workflow_evaluator = WorkflowStateEvaluator()
