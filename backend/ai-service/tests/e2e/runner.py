import time
import sys
from typing import List, Tuple
from tests.e2e.test_banking_lifecycle import banking_e2e_tester

def run_banking_e2e_matrix():
    start_time = time.time()

    print("\n" + "=" * 86)
    print(" 🏦  TIRENN CORE BANKING END-TO-END (E2E) INTEGRATION & LEDGER HARNESS")
    print("=" * 86)
    print(" Initializing 6 Core Banking Test Suites (Excluding Chat & RAG)...\n")

    all_results: List[Tuple[str, str, bool, str]] = []

    # Run Suite 1
    print(" [1/6] Running Suite 1: Customer Onboarding, Identity & KYC...")
    all_results.extend(banking_e2e_tester.test_customer_registration_and_login())

    # Run Suite 2
    print(" [2/6] Running Suite 2: Accounts, Deposits, P2P Transfers & ACID Ledger...")
    all_results.extend(banking_e2e_tester.test_banking_ledger_and_transfers())

    # Run Suite 3
    print(" [3/6] Running Suite 3: Overdraft Protection & Boundary Security...")
    all_results.extend(banking_e2e_tester.test_overdraft_and_fraud_protection())

    # Run Suite 4
    print(" [4/6] Running Suite 4: Debit Card Security, Freezing & Spending Limits...")
    all_results.extend(banking_e2e_tester.test_card_security_and_limits())

    # Run Suite 5
    print(" [5/6] Running Suite 5: Trusted Beneficiaries & Financial Calculators...")
    all_results.extend(banking_e2e_tester.test_beneficiaries_and_calculators())

    # Run Suite 6
    print(" [6/6] Running Suite 6: Admin RBAC & AI Model Fallback Immutability...")
    all_results.extend(banking_e2e_tester.test_admin_rbac_and_immutability())

    elapsed_ms = (time.time() - start_time) * 1000

    # Print Scorecard Table
    print("\n" + "=" * 86)
    print(f" {'SUITE / DOMAIN':<18} | {'TEST CASE / TARGET':<42} | {'STATUS':<8} | {'DETAILS'}")
    print("-" * 86)

    passed_count = 0
    failed_count = 0

    for suite, test_name, passed, details in all_results:
        status_str = "✅ PASS" if passed else "❌ FAIL"
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        
        detail_preview = details[:20] if len(details) > 20 else details
        print(f" {suite:<18} | {test_name:<42} | {status_str:<8} | {detail_preview}")

    print("=" * 86)

    total_tests = len(all_results)
    pass_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0.0

    print(f"\n📊 E2E SCORECARD SUMMARY:")
    print(f"   • Total Evaluated Cases : {total_tests}")
    print(f"   • Passed Cases          : {passed_count} ✅")
    print(f"   • Failed Cases          : {failed_count} ❌")
    print(f"   • Pass Rate             : {pass_rate:.1f}%")
    print(f"   • Execution Latency     : {elapsed_ms:.2f} ms\n")

    if failed_count == 0:
        print(" 🎉 ALL CORE BANKING E2E TEST SUITES PASSED SYSTEM CRITERIA!\n")
        sys.exit(0)
    else:
        print(f" ⚠️ CRITICAL: {failed_count} test case(s) failed in Core Banking E2E Matrix.\n")
        sys.exit(1)


if __name__ == "__main__":
    run_banking_e2e_matrix()
