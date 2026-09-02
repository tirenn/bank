from typing import Dict, Any, List
from app.services.pii_redactor import redact_text, redact_data
from app.repositories.mcp_repository import mcp_repository


class SecurityPrivacyEvaluator:
    """
    Evaluates PII Masking, Credential Redaction, and Multi-Tenant Isolation.
    """

    def eval_pii_redaction(self) -> List[Dict[str, Any]]:
        """
        Evaluates regex PII masking and redaction filters.
        """
        eval_cases = [
            {
                "name": "16-digit Card Masking (Standard Spaces)",
                "input": "My Visa card is 4532 8920 1823 9042",
                "expected_contains": "•••• •••• •••• 9042",
                "forbidden_contains": "4532 8920 1823 9042",
            },
            {
                "name": "16-digit Card Masking (Dashed)",
                "input": "Debit card: 5412-7721-9012-4431",
                "expected_contains": "•••• •••• •••• 4431",
                "forbidden_contains": "5412-7721-9012-4431",
            },
            {
                "name": "CVV / Security Code Redaction",
                "input": "Card details: cvv 832 and security code: 492",
                "expected_contains": "CVV: [CVV_REDACTED]",
                "forbidden_contains": "832",
            },
            {
                "name": "Password & API Key Redaction",
                "input": 'Payload: {"password": "supersecretpassword123"}',
                "expected_contains": "[REDACTED]",
                "forbidden_contains": "supersecretpassword123",
            },
            {
                "name": "Bearer JWT Token Redaction",
                "input": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDN4500_B7uEAkJa1-QgKycqxljbGpqTII2Za27Cg",
                "expected_contains": "Bearer [AUTH_TOKEN_REDACTED]",
                "forbidden_contains": "eyJhbGci",
            }
        ]

        results = []
        for case in eval_cases:
            output = redact_text(case["input"])
            passed = (case["expected_contains"] in output) and (case["forbidden_contains"] not in output)
            
            results.append({
                "suite": "PII & Redaction",
                "test_name": case["name"],
                "passed": passed,
                "sanitized_output": output,
                "expected": f"Contains '{case['expected_contains']}', excludes raw secrets."
            })

        return results

    async def eval_multi_tenant_isolation(self, auth_token: str) -> List[Dict[str, Any]]:
        """
        Evaluates that tools reject unowned accounts and block cross-user snooping.
        """
        eval_cases = [
            {
                "name": "Cross-Account Balance Denial",
                "domain": "transaction",
                "tool": "get_balance",
                "args": {"account_number": "ACC-99999999"},
                "expected_rejection": ["Access Denied", "does not belong to your profile", "No bank accounts"],
            },
            {
                "name": "Unauthorized Transaction ID Lookup",
                "domain": "transaction",
                "tool": "get_transaction_details",
                "args": {"identifier": "TRF-99999999-000000"},
                "expected_rejection": ["Transaction not found", "not authorized", "access denied"],
            }
        ]

        results = []
        for case in eval_cases:
            obs_text, act_type, act_data = await mcp_repository.call_tool(
                domain=case["domain"],
                name=case["tool"],
                arguments=case["args"],
                auth_token=auth_token
            )

            # Access should be rejected or not found (zero data leaked)
            passed = any(rejection_kw.lower() in obs_text.lower() for rejection_kw in case["expected_rejection"])
            results.append({
                "suite": "Multi-Tenant Security",
                "test_name": case["name"],
                "passed": passed,
                "response": obs_text[:90] if obs_text else "EMPTY",
                "expected": f"Must reject with Access Denied / Not Found."
            })

        return results

security_evaluator = SecurityPrivacyEvaluator()
