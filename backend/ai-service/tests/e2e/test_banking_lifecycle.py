import time
import httpx
from typing import Dict, Any, Tuple, Optional, List
from app.config import settings

BASE_URL = settings.CORE_BANKING_URL

class BankingE2ETester:
    """
    Comprehensive End-to-End Test Suite for Tirenn Core Banking API:
    - Authentication, KYC & Profiles
    - Multi-Account Creation & Management
    - Deposit & Ledger ACID Integrity
    - P2P Transfers & Cross-Account Balance Sync
    - Overdraft Protection & Negative Edge Cases
    - Card Security, Freezing & Spending Limits
    - Beneficiary Management & Financial Calculators
    - Admin RBAC & Free AI Model Immutability
    """

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(base_url=self.base_url, timeout=10.0)

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    # --------------------------------------------------------------------------
    # SUITE 1: AUTHENTICATION, KYC & PROFILES
    # --------------------------------------------------------------------------
    def test_customer_registration_and_login(self) -> List[Tuple[str, str, bool, str]]:
        results = []
        ts = int(time.time() * 1000)
        
        # User Alpha
        alpha_email = f"e2e.alpha.{ts}@bank.com"
        alpha_payload = {
            "email": alpha_email,
            "password": "Password123!",
            "full_name": "Alpha Tester",
            "phone_number": "+1555123456",
            "initial_balance": 50.0
        }
        res_reg = self.client.post("/api/v1/auth/register", json=alpha_payload)
        pass_reg = res_reg.status_code in (200, 201) and "token" in res_reg.json()
        results.append(("Suite 1: Auth", f"Register Customer Alpha ({alpha_email})", pass_reg, f"Status {res_reg.status_code}"))

        # User Beta
        beta_email = f"e2e.beta.{ts}@bank.com"
        beta_payload = {
            "email": beta_email,
            "password": "Password123!",
            "full_name": "Beta Recipient",
            "phone_number": "+1555654321",
            "initial_balance": 0.0
        }
        res_reg_beta = self.client.post("/api/v1/auth/register", json=beta_payload)
        pass_reg_beta = res_reg_beta.status_code in (200, 201) and "token" in res_reg_beta.json()
        results.append(("Suite 1: Auth", f"Register Customer Beta ({beta_email})", pass_reg_beta, f"Status {res_reg_beta.status_code}"))

        # Login Alpha
        res_login = self.client.post("/api/v1/auth/login", json={"email": alpha_email, "password": "Password123!"})
        pass_login = res_login.status_code == 200 and "token" in res_login.json()
        alpha_token = res_login.json().get("token") if pass_login else ""
        results.append(("Suite 1: Auth", "Login Customer Alpha & Issue JWT", pass_login, f"Token received (length: {len(alpha_token)})"))

        # Profile & KYC Details
        res_profile = self.client.get("/api/v1/auth/me", headers=self._get_headers(alpha_token))
        pass_prof = res_profile.status_code == 200 and res_profile.json().get("email") == alpha_email
        results.append(("Suite 1: Auth", "Retrieve Profile & Verify Identity", pass_prof, f"Email: {res_profile.json().get('email')}"))

        # Address Update
        res_addr = self.client.put("/api/v1/users/address", headers=self._get_headers(alpha_token), json={
            "street": "742 Evergreen Terrace",
            "city": "Springfield",
            "state": "OR",
            "postal_code": "97477",
            "country": "USA"
        })
        pass_addr = res_addr.status_code == 200
        results.append(("Suite 1: Auth", "Update Residential Address", pass_addr, f"Status: {res_addr.status_code}"))

        return results

    # --------------------------------------------------------------------------
    # SUITE 2: ACCOUNTS, DEPOSITS, TRANSFERS & LEDGER INTEGRITY
    # --------------------------------------------------------------------------
    def test_banking_ledger_and_transfers(self) -> List[Tuple[str, str, bool, str]]:
        results = []
        ts = int(time.time() * 1000)

        # Setup 2 dedicated test accounts
        user_a_email = f"ledger.a.{ts}@bank.com"
        user_b_email = f"ledger.b.{ts}@bank.com"

        res_a = self.client.post("/api/v1/auth/register", json={
            "email": user_a_email,
            "password": "Password123!",
            "full_name": "Ledger Alice",
            "initial_balance": 100.0
        })
        token_a = res_a.json().get("token")

        res_b = self.client.post("/api/v1/auth/register", json={
            "email": user_b_email,
            "password": "Password123!",
            "full_name": "Ledger Bob",
            "initial_balance": 50.0
        })
        token_b = res_b.json().get("token")

        # 1. Fetch Alice and Bob default accounts
        acc_a_data = self.client.get("/api/v1/accounts/my", headers=self._get_headers(token_a)).json().get("account", {})
        acc_b_data = self.client.get("/api/v1/accounts/my", headers=self._get_headers(token_b)).json().get("account", {})
        
        acc_a_num = acc_a_data.get("account_number")
        acc_b_num = acc_b_data.get("account_number")
        results.append(("Suite 2: Ledger", "Account Provisioning on Sign-Up", bool(acc_a_num and acc_b_num), f"Alice: {acc_a_num} | Bob: {acc_b_num}"))

        # 2. Deposit $500 (50,000 cents) to Alice
        dep_res = self.client.post("/api/v1/transfers/deposit", headers=self._get_headers(token_a), json={
            "amount_cents": 50000,
            "description": "Payroll Direct Deposit"
        })
        pass_dep = dep_res.status_code == 200
        results.append(("Suite 2: Ledger", "Deposit Funds ($500.00)", pass_dep, f"Status: {dep_res.status_code}"))

        # 3. Create Secondary Savings Account for Alice
        new_acc_res = self.client.post("/api/v1/accounts", headers=self._get_headers(token_a), json={
            "account_name": "Emergency Fund",
            "account_type": "SAVINGS",
            "initial_deposit_dollars": 0.0
        })
        pass_new_acc = new_acc_res.status_code in (200, 201)
        results.append(("Suite 2: Ledger", "Open Secondary Savings Account", pass_new_acc, f"Status: {new_acc_res.status_code}"))

        # 4. Multi-Account Listing
        list_accs = self.client.get("/api/v1/accounts", headers=self._get_headers(token_a))
        accounts_list = list_accs.json().get("accounts", [])
        pass_multi = list_accs.status_code == 200 and len(accounts_list) >= 2
        results.append(("Suite 2: Ledger", "List Multi-Account Hierarchy", pass_multi, f"Total Accounts: {len(accounts_list)}"))

        # 5. Account Lookup before Transfer
        lookup_res = self.client.get(f"/api/v1/accounts/lookup/{acc_b_num}", headers=self._get_headers(token_a))
        pass_lookup = lookup_res.status_code == 200 and lookup_res.json().get("account_number") == acc_b_num
        results.append(("Suite 2: Ledger", "Recipient Account Lookup", pass_lookup, f"Recipient: {lookup_res.json().get('account_name')}"))

        # 6a. OTP Gate Verification: Rejection of Invalid OTP
        invalid_otp_res = self.client.post("/api/v1/transfers", headers=self._get_headers(token_a), json={
            "to_account_number": acc_b_num,
            "amount_cents": 20000,
            "description": "Dinner Split",
            "category": "Food & Dining",
            "otp": "000000"
        })
        pass_otp_gate = invalid_otp_res.status_code == 400
        results.append(("Suite 2: Ledger", "OTP Gate: Reject Invalid OTP", pass_otp_gate, f"Rejected with Status {invalid_otp_res.status_code}"))

        # 6b. P2P Transfer: Alice sends $200 (20,000 cents) to Bob with valid OTP
        xfer_res = self.client.post("/api/v1/transfers", headers=self._get_headers(token_a), json={
            "to_account_number": acc_b_num,
            "amount_cents": 20000,
            "description": "Dinner Split",
            "category": "Food & Dining",
            "otp": "888888"
        })
        pass_xfer = xfer_res.status_code == 200
        results.append(("Suite 2: Ledger", "Execute P2P Transfer with Valid OTP", pass_xfer, f"Status: {xfer_res.status_code}"))

        # 7. ACID Balance Verification
        alice_bal_cents = self.client.get("/api/v1/accounts/my", headers=self._get_headers(token_a)).json().get("account", {}).get("balance_cents", 0)
        bob_bal_cents = self.client.get("/api/v1/accounts/my", headers=self._get_headers(token_b)).json().get("account", {}).get("balance_cents", 0)
        pass_acid = (alice_bal_cents == 130000) and (bob_bal_cents == 120000)
        results.append(("Suite 2: Ledger", "ACID Balance Consistency Sync", pass_acid, f"Alice: ${alice_bal_cents/100:.2f} (exp 1300) | Bob: ${bob_bal_cents/100:.2f} (exp 1200)"))


        # 8. Transaction Stream Verification
        txs_res = self.client.get("/api/v1/transactions", headers=self._get_headers(token_a))
        txs = txs_res.json().get("transactions") or []
        pass_stream = len(txs) >= 2
        results.append(("Suite 2: Ledger", "Transaction History Stream", pass_stream, f"Recorded Transactions: {len(txs)}"))

        # 9. Spending Breakdown Summary
        summary_res = self.client.get("/api/v1/transactions/summary", headers=self._get_headers(token_a))
        pass_summary = summary_res.status_code == 200
        results.append(("Suite 2: Ledger", "Categorized Spending Summary", pass_summary, f"Status: {summary_res.status_code}"))

        return results

    # --------------------------------------------------------------------------
    # SUITE 3: NEGATIVE TESTS & OVERDRAFT PROTECTION
    # --------------------------------------------------------------------------
    def test_overdraft_and_fraud_protection(self) -> List[Tuple[str, str, bool, str]]:
        results = []
        ts = int(time.time() * 1000)
        user_email = f"fraud.test.{ts}@bank.com"

        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": user_email,
            "password": "Password123!",
            "full_name": "Test Fraud",
            "initial_balance": 100.0
        })
        token = reg_res.json().get("token")

        # 1. Overdraft Transfer ($50,000 with only $100 balance)
        overdraft_res = self.client.post("/api/v1/transfers", headers=self._get_headers(token), json={
            "to_account_number": "ACC-99999999",
            "amount_cents": 5000000,
            "description": "Illegal Overdraft"
        })
        pass_overdraft = overdraft_res.status_code in (400, 422)
        results.append(("Suite 3: Security", "Overdraft Denial (Balance Protection)", pass_overdraft, f"Rejected with HTTP {overdraft_res.status_code}"))

        # 2. Transfer to Non-Existent Account
        invalid_acc_res = self.client.post("/api/v1/transfers", headers=self._get_headers(token), json={
            "to_account_number": "ACC-00000000-NONEXISTENT",
            "amount_cents": 1000,
            "description": "Invalid Destination"
        })
        pass_invalid = invalid_acc_res.status_code in (400, 404)
        results.append(("Suite 3: Security", "Invalid Account Rejection", pass_invalid, f"Rejected with HTTP {invalid_acc_res.status_code}"))

        # 3. Negative / Zero Transfer Amount
        zero_xfer = self.client.post("/api/v1/transfers", headers=self._get_headers(token), json={
            "to_account_number": "ACC-12345678",
            "amount_cents": -5000,
            "description": "Negative amount exploit"
        })
        pass_zero = zero_xfer.status_code in (400, 422)
        results.append(("Suite 3: Security", "Negative Transfer Amount Denial", pass_zero, f"Rejected with HTTP {zero_xfer.status_code}"))

        # 4. Unauthorized Access (Missing JWT)
        no_auth = self.client.get("/api/v1/accounts/my")
        pass_no_auth = no_auth.status_code == 401
        results.append(("Suite 3: Security", "Unauthenticated Request Interception", pass_no_auth, f"Rejected with HTTP {no_auth.status_code}"))

        return results

    # --------------------------------------------------------------------------
    # SUITE 4: DEBIT CARD LIFECYCLE & LIMITS
    # --------------------------------------------------------------------------
    def test_card_security_and_limits(self) -> List[Tuple[str, str, bool, str]]:
        results = []
        ts = int(time.time() * 1000)
        user_email = f"card.test.{ts}@bank.com"

        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": user_email,
            "password": "Password123!",
            "full_name": "Card Tester",
            "initial_balance": 100.0
        })
        token = reg_res.json().get("token")
        acc_num = self.client.get("/api/v1/accounts/my", headers=self._get_headers(token)).json().get("account", {}).get("account_number")

        # 1. Update Daily Limit to $7,500 (750,000 cents)
        limit_res = self.client.put("/api/v1/accounts/limits", headers=self._get_headers(token), json={
            "account_number": acc_num,
            "daily_transfer_limit_cents": 750000
        })
        pass_limit = limit_res.status_code == 200
        results.append(("Suite 4: Cards", "Update Daily Transfer Limits ($7,500)", pass_limit, f"Status: {limit_res.status_code}"))

        # 2. Freeze Debit Card
        freeze_res = self.client.put("/api/v1/accounts/status", headers=self._get_headers(token), json={
            "account_number": acc_num,
            "frozen": True,
            "reason": "Lost or stolen debit card"
        })
        pass_freeze = freeze_res.status_code == 200
        results.append(("Suite 4: Cards", "Freeze Lost/Stolen Debit Card", pass_freeze, f"Status: {freeze_res.status_code}"))

        # 3. Verify Frozen Status
        my_acc = self.client.get("/api/v1/accounts/my", headers=self._get_headers(token)).json().get("account", {})
        pass_status_check = my_acc.get("is_frozen") is True or my_acc.get("status") == "FROZEN"
        results.append(("Suite 4: Cards", "Verify Card State is FROZEN", pass_status_check, f"is_frozen: {my_acc.get('is_frozen')}"))

        # 4. Unfreeze Debit Card
        unfreeze_res = self.client.put("/api/v1/accounts/status", headers=self._get_headers(token), json={
            "account_number": acc_num,
            "frozen": False,
            "reason": "Customer found debit card"
        })
        pass_unfreeze = unfreeze_res.status_code == 200
        results.append(("Suite 4: Cards", "Unfreeze & Restore Debit Card", pass_unfreeze, f"Status: {unfreeze_res.status_code}"))

        return results

    # --------------------------------------------------------------------------
    # SUITE 5: BENEFICIARIES & FINANCIAL CALCULATORS
    # --------------------------------------------------------------------------
    def test_beneficiaries_and_calculators(self) -> List[Tuple[str, str, bool, str]]:
        results = []
        ts = int(time.time() * 1000)
        user_email = f"ben.test.{ts}@bank.com"

        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": user_email,
            "password": "Password123!",
            "full_name": "Ben Tester",
            "initial_balance": 100.0
        })
        token = reg_res.json().get("token")

        # 1. Add Beneficiary
        add_ben = self.client.post("/api/v1/beneficiaries", headers=self._get_headers(token), json={
            "name": "Sarah Connor",
            "account_number": "ACC-99887766",
            "bank_name": "Tirenn Bank",
            "nickname": "Sarah"
        })
        pass_add_ben = add_ben.status_code in (200, 201)
        results.append(("Suite 5: Wealth", "Add Trusted Beneficiary Contact", pass_add_ben, f"Status: {add_ben.status_code}"))

        # 2. List Beneficiaries
        list_ben = self.client.get("/api/v1/beneficiaries", headers=self._get_headers(token))
        bens = list_ben.json().get("beneficiaries") or []
        pass_list_ben = list_ben.status_code == 200 and len(bens) >= 1
        results.append(("Suite 5: Wealth", "Retrieve Beneficiary Directory", pass_list_ben, f"Count: {len(bens)}"))

        # 3. Public Forex Conversion
        forex_res = self.client.post("/api/v1/forex/convert", json={
            "amount": 1000.0,
            "from": "USD",
            "to": "EUR"
        })
        pass_forex = forex_res.status_code == 200 and forex_res.json().get("converted_amount", 0) > 0
        results.append(("Suite 5: Wealth", "Forex Engine Conversion (USD->EUR)", pass_forex, f"Converted: {forex_res.json().get('converted_amount')} EUR"))

        # 4. Public Loan Calculation
        loan_res = self.client.post("/api/v1/loans/calculate", json={
            "principal": 30000.0,
            "annual_rate_pct": 6.5,
            "term_months": 36,
            "loan_type": "PERSONAL"
        })
        pass_loan = loan_res.status_code == 200 and loan_res.json().get("monthly_payment", 0) > 0
        results.append(("Suite 5: Wealth", "Loan Amortization Calculation", pass_loan, f"Monthly: ${loan_res.json().get('monthly_payment')}"))


        return results

    # --------------------------------------------------------------------------
    # SUITE 6: ADMIN RBAC & AI MODEL IMMUTABILITY
    # --------------------------------------------------------------------------
    def test_admin_rbac_and_immutability(self) -> List[Tuple[str, str, bool, str]]:
        results = []

        # 1. Login as Admin
        admin_login = self.client.post("/api/v1/auth/login", json={
            "email": "admin@bank.com",
            "password": "password123"
        })
        pass_adm_login = admin_login.status_code == 200
        admin_token = admin_login.json().get("token") if pass_adm_login else ""
        results.append(("Suite 6: Admin", "Admin Credentials Authentication", pass_adm_login, f"Status: {admin_login.status_code}"))

        # 2. Access Admin AI Models (Read-Only Telemetry)
        models_res = self.client.get("/api/v1/admin/ai/models", headers=self._get_headers(admin_token))
        pass_models = models_res.status_code == 200 and models_res.json().get("count", 0) > 0
        results.append(("Suite 6: Admin", "Admin AI Model Telemetry Access", pass_models, f"Models Active: {models_res.json().get('count')}"))

        # 3. Verify Free Model Write Prohibition (POST returns 404)
        post_res = self.client.post("/api/v1/admin/ai/models", headers=self._get_headers(admin_token), json={
            "name": "Illegal Model",
            "model_id": "illegal/model"
        })
        pass_post = post_res.status_code == 404
        results.append(("Suite 6: Admin", "Prohibit Free Model Creation (POST=404)", pass_post, f"HTTP {post_res.status_code} (Immutable)"))

        # 4. Verify Free Model Update Prohibition (PUT returns 404)
        put_res = self.client.put("/api/v1/admin/ai/models/1", headers=self._get_headers(admin_token), json={"is_active": False})
        pass_put = put_res.status_code == 404
        results.append(("Suite 6: Admin", "Prohibit Free Model Update (PUT=404)", pass_put, f"HTTP {put_res.status_code} (Immutable)"))

        # 5. Verify Free Model Delete Prohibition (DELETE returns 404)
        del_res = self.client.delete("/api/v1/admin/ai/models/1", headers=self._get_headers(admin_token))
        pass_del = del_res.status_code == 404
        results.append(("Suite 6: Admin", "Prohibit Free Model Deletion (DELETE=404)", pass_del, f"HTTP {del_res.status_code} (Immutable)"))

        return results


banking_e2e_tester = BankingE2ETester()
