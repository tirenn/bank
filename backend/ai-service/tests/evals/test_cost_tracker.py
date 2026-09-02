import time
from typing import List, Tuple
from app.services.cost_tracker_service import cost_tracker_service

class CostTrackerEvaluator:
    """
    Evaluation Suite for AI Token & Cost Tracking Engine with OpenRouter dynamic rates and Redis telemetry.
    """

    async def eval_cost_tracking(self) -> List[Tuple[str, str, bool, str]]:
        results = []

        # 1. Connect Redis if needed
        if not cost_tracker_service.rdb:
            await cost_tracker_service.connect()

        # 2. Fetch Pricing Catalog Test
        pricing = await cost_tracker_service.fetch_and_cache_pricing()
        pass_pricing = isinstance(pricing, dict)
        results.append(("Cost Tracker", "Fetch & Cache OpenRouter Model Rates", pass_pricing, f"Cached Models: {len(pricing)} entries"))

        # 3. Free Model Zero-Cost Rule Test
        free_cost = await cost_tracker_service.record_usage(
            model="google/gemini-2.0-flash-exp:free",
            domain="TRANSACTION",
            prompt_tokens=500,
            completion_tokens=150,
            user_id="eval_test_user"
        )
        pass_free = (free_cost == 0.0)
        results.append(("Cost Tracker", "Deterministic Free Tier Surcharge ($0.00)", pass_free, f"Calculated Cost: ${free_cost:.6f}"))

        # 4. Commercial Model Dynamic Pricing Calculation Test
        paid_cost = await cost_tracker_service.record_usage(
            model="openai/gpt-4o",
            domain="WEALTH",
            prompt_tokens=1000,
            completion_tokens=200,
            user_id="eval_test_user"
        )
        pass_paid = (paid_cost > 0.0)
        results.append(("Cost Tracker", "Dynamic Paid Model Pricing ($/1M tokens)", pass_paid, f"Calculated Cost: ${paid_cost:.6f} USD"))

        # 5. Redis Atomic Aggregates Verification
        summary_data = await cost_tracker_service.get_cost_summary()
        summary = summary_data.get("summary", {})
        pass_summary = (
            summary.get("total_tokens", 0) >= 1850 and
            summary.get("total_requests", 0) >= 2 and
            "WEALTH" in summary_data.get("by_domain", {})
        )
        results.append(("Cost Tracker", "Redis Real-Time Atomic Telemetry Sync", pass_summary, f"Total Tokens: {summary.get('total_tokens')}, Requests: {summary.get('total_requests')}"))

        # 6. Audit Stream Cap Verification
        recent = summary_data.get("recent_stream", [])
        pass_stream = len(recent) >= 2 and recent[0].get("user_id") == "eval_test_user"
        results.append(("Cost Tracker", "Audit Stream Ingestion & Capping", pass_stream, f"Stream Entries: {len(recent)} (Latest: {recent[0].get('domain') if recent else 'None'})"))

        return results


cost_evaluator = CostTrackerEvaluator()
