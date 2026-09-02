import asyncio
import time
import httpx
from typing import List, Dict, Any

from tests.evals.test_tool_calling import tool_evaluator
from tests.evals.test_security_privacy import security_evaluator
from tests.evals.test_rag_quality import rag_evaluator
from app.config import settings


async def get_test_auth_token() -> str:
    """
    Authenticate against bank-core to obtain JWT token for testing.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{settings.CORE_BANKING_URL}/api/v1/auth/login",
                json={"email": "john.doe@bank.com", "password": "password123"}
            )
            if res.status_code == 200:
                return res.json().get("token", "")
    except Exception as e:
        print(f"Warning: Could not login to bank-core ({e}). Testing in unauthenticated mode.")
    return ""


async def run_all_evals():
    start_time = time.time()

    print("\n" + "=" * 78)
    print(" 🏦  TIRENN BANKING AI EVALUATION HARNESS")
    print("=" * 78)

    print(" Initializing 3-Layer Hybrid AI Evaluation Matrix...\n")

    auth_token = await get_test_auth_token()

    all_results: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # 1. LAYER 1: Tool Registration & Deterministic Calculators
    # -------------------------------------------------------------
    print(" [1/3] Running Layer 1: MCP Tool Registration & Execution Evals...")
    reg_results = await tool_evaluator.eval_tool_registration()
    for r in reg_results:
        all_results.append({
            "layer": "Layer 1: Tools",
            "name": f"MCP Schema: {r['domain']}",
            "passed": r["passed"],
            "details": f"{r['total_found']}/{r['total_expected']} tools registered"
        })

    tool_results = await tool_evaluator.eval_deterministic_tools()
    for r in tool_results:
        all_results.append({
            "layer": "Layer 1: Tools",
            "name": r["test_name"],
            "passed": r["passed"],
            "details": r["output_snippet"]
        })

    # -------------------------------------------------------------
    # 2. LAYER 2: Security, Privacy & Multi-Tenant Evals
    # -------------------------------------------------------------
    print(" [2/3] Running Layer 2: Security, PII Redaction & Multi-Tenant Evals...")
    pii_results = security_evaluator.eval_pii_redaction()
    for r in pii_results:
        all_results.append({
            "layer": "Layer 2: Security",
            "name": r["test_name"],
            "passed": r["passed"],
            "details": r["sanitized_output"][:60]
        })

    if auth_token:
        tenant_results = await security_evaluator.eval_multi_tenant_isolation(auth_token)
        for r in tenant_results:
            all_results.append({
                "layer": "Layer 2: Security",
                "name": r["test_name"],
                "passed": r["passed"],
                "details": r["response"][:60]
            })

    # -------------------------------------------------------------
    # 3. LAYER 3: ChromaDB Vector RAG Quality & Semantic Relevance
    # -------------------------------------------------------------
    print(" [3/3] Running Layer 3: ChromaDB FAQ Vector RAG Quality Evals...")
    rag_results = await rag_evaluator.eval_faq_retrieval()
    for r in rag_results:
        all_results.append({
            "layer": "Layer 3: RAG",
            "name": f"FAQ: {r['query'][:35]}...",
            "passed": r["passed"],
            "details": f"Dist: {r['distance']} | Relevance: {r['relevance_score']}"
        })

    elapsed_ms = (time.time() - start_time) * 1000.0

    # -------------------------------------------------------------
    # Render Scorecard Table
    # -------------------------------------------------------------
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r["passed"])
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100.0) if total_tests > 0 else 0.0

    print("\n" + "=" * 78)
    print(f" {'LAYER':<18} | {'TEST CASE / TARGET':<32} | {'STATUS':<8} | {'DETAILS'}")
    print("-" * 78)
    for r in all_results:
        status_str = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f" {r['layer']:<18} | {r['name']:<32} | {status_str:<8} | {r['details']}")
    print("=" * 78)

    print(f"\n📊 EVALUATION SCORECARD SUMMARY:")
    print(f"   • Total Evaluated Cases : {total_tests}")
    print(f"   • Passed Cases          : {passed_tests} ✅")
    print(f"   • Failed Cases          : {failed_tests} ❌")
    print(f"   • Pass Rate             : {pass_rate:.1f}%")
    print(f"   • Execution Latency     : {elapsed_ms:.2f} ms\n")

    if failed_tests > 0:
        print(" ⚠️  Some evaluation cases failed. Review details above.\n")
        exit(1)
    else:
        print(" 🎉 ALL AI EVALUATION SUITES PASSED BENCHMARK CRITERIA!\n")
        exit(0)


if __name__ == "__main__":
    asyncio.run(run_all_evals())
