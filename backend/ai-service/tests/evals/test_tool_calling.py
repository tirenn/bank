from typing import Dict, Any, List
from app.repositories.mcp_repository import mcp_repository



class ToolCallingEvaluator:
    """
    Evaluates MCP Tool Registration and Argument Validation across all 4 Domains.
    """

    async def eval_tool_registration(self) -> Dict[str, Any]:
        """
        Verify that all expected banking tools are registered in MCP domains.
        """
        domains = {
            "transaction": ["get_balance", "get_transactions", "draft_transfer", "get_transaction_details", "get_all_accounts", "open_new_account", "request_account_statement"],
            "security": ["lock_unlock_card", "set_spending_limit"],
            "identity": ["get_user_profile", "update_user_address", "submit_kyc_verification"],
            "wealth": ["calculate_forex_conversion", "calculate_loan_mortgage", "manage_beneficiaries"],
        }
        
        results = []
        for domain, expected_tools in domains.items():
            tools = await mcp_repository.list_tools(domain)
            registered_names = [t["function"]["name"] for t in tools]
            
            missing = [t for t in expected_tools if t not in registered_names]
            passed = len(missing) == 0
            
            results.append({
                "suite": "Tool Registration",
                "domain": domain,
                "passed": passed,
                "total_expected": len(expected_tools),
                "total_found": len(registered_names),
                "missing": missing,
            })
            
        return results

    async def eval_deterministic_tools(self) -> List[Dict[str, Any]]:
        """
        Evaluates pure calculator tools with known deterministic inputs.
        """
        eval_cases = [
            {
                "name": "Forex Conversion (USD to EUR)",
                "domain": "wealth",
                "tool": "calculate_forex_conversion",
                "args": {"from_currency": "USD", "to_currency": "EUR", "amount": 1000},
                "expected_contains": ["Forex Conversion:", "Rate:", "EUR"],
            },
            {
                "name": "Loan Mortgage Calculation (30-yr fixed)",
                "domain": "wealth",
                "tool": "calculate_loan_mortgage",
                "args": {"principal": 300000, "annual_rate_pct": 6.5, "term_months": 360, "loan_type": "MORTGAGE"},
                "expected_contains": ["Loan Simulation", "Principal:", "Monthly Payment:"],
            },
            {
                "name": "Forex Inverted (EUR to USD)",
                "domain": "wealth",
                "tool": "calculate_forex_conversion",
                "args": {"from_currency": "EUR", "to_currency": "USD", "amount": 500},
                "expected_contains": ["Forex Conversion:", "USD"],
            }
        ]
        
        results = []
        for case in eval_cases:
            obs_text, act_type, act_data = await mcp_repository.call_tool(
                domain=case["domain"],
                name=case["tool"],
                arguments=case["args"]
            )
            
            passed = all(k in obs_text for k in case["expected_contains"])
            results.append({
                "suite": "Tool Execution",
                "test_name": case["name"],
                "passed": passed,
                "output_snippet": obs_text[:80] if obs_text else "EMPTY",
                "details": f"Expected substrings: {case['expected_contains']}"
            })
            
        return results

tool_evaluator = ToolCallingEvaluator()

