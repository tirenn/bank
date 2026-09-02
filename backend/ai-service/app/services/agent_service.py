import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI
from app.config import settings
from app.domain.schemas import ChatMessage, ChatResponse
from app.repositories.mcp_repository import mcp_repository
from app.repositories.faq_repository import faq_repository

logger = logging.getLogger("ai_service.services.agent")

class BaseSubAgent:
    def __init__(self, name: str, domain: str, system_prompt: str):
        self.name = name
        self.domain = domain
        self.system_prompt = system_prompt
        self._cached_tools: Optional[List[Dict[str, Any]]] = None

    async def get_tools(self) -> List[Dict[str, Any]]:
        if self._cached_tools is None:
            self._cached_tools = await mcp_repository.list_tools(self.domain)
        return self._cached_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], auth_token: Optional[str] = None) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        return await mcp_repository.call_tool(self.domain, tool_name, arguments, auth_token)

    async def run(
        self,
        messages: List[ChatMessage],
        auth_token: Optional[str] = None,
        openai_client: Optional[AsyncOpenAI] = None,
        model: str = "meta-llama/llama-3.3-70b-instruct:free"
    ) -> ChatResponse:
        tools = await self.get_tools()

        if openai_client and tools:
            try:
                llm_messages = [{"role": "system", "content": self.system_prompt}]
                for m in messages:
                    llm_messages.append({"role": m.role, "content": m.content})

                response = await openai_client.chat.completions.create(
                    model=model,
                    messages=llm_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.1,
                )

                choice = response.choices[0].message
                if choice.tool_calls:
                    tools_used = []
                    reply_parts = []
                    last_action_type = None
                    last_action_data = None

                    for tc in choice.tool_calls:
                        t_name = tc.function.name
                        try:
                            t_args = json.loads(tc.function.arguments)
                        except Exception:
                            t_args = {}

                        tools_used.append(t_name)
                        res_text, act_type, act_data = await self.execute_tool(t_name, t_args, auth_token)
                        reply_parts.append(res_text)
                        if act_type:
                            last_action_type = act_type
                            last_action_data = act_data

                    reply = "\n\n".join(reply_parts)
                    return ChatResponse(
                        reply=reply,
                        action_type=last_action_type,
                        action_data=last_action_data,
                        tools_used=tools_used
                    )
                else:
                    return ChatResponse(
                        reply=choice.content or "How else can I assist with your transaction?",
                        action_type=None,
                        action_data=None,
                        tools_used=[]
                    )
            except Exception as e:
                logger.error(f"Error in SubAgent {self.name} LLM execution: {e}", exc_info=True)

        return await self.fallback_run(messages, auth_token)

    async def fallback_run(self, messages: List[ChatMessage], auth_token: Optional[str] = None) -> ChatResponse:
        raise NotImplementedError("Sub-agents must implement fallback_run")


class TransactionSubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="TransactionSubAgent",
            domain="transaction",
            system_prompt=(
                "You are Nova's Transaction & Ledger Sub-Agent. You specialize exclusively in account balances, "
                "wire transfers, transaction histories, audit receipts, monthly bank statements, listing all user bank accounts, "
                "and instantly opening new bank accounts (with auto-generated credit/debit card numbers). "
                "Always invoke the appropriate transaction tool."
            )
        )

    async def fallback_run(self, messages: List[ChatMessage], auth_token: Optional[str] = None) -> ChatResponse:
        last_msg = messages[-1].content.lower() if messages else ""

        if any(w in last_msg for w in ["open account", "buka rekening", "create account", "buat akun", "new account", "rekening baru"]):
            acc_type = "SAVINGS"
            if "checking" in last_msg or "giro" in last_msg:
                acc_type = "CHECKING"
            elif "invest" in last_msg:
                acc_type = "INVESTMENT"

            card_brand = "VISA"
            if "mastercard" in last_msg:
                card_brand = "MASTERCARD"

            acc_name = "New Savings Account"
            if "liburan" in last_msg or "vacation" in last_msg:
                acc_name = "Vacation Savings"
            elif "invest" in last_msg:
                acc_name = "Investment Growth Account"
            elif "emergency" in last_msg or "darurat" in last_msg:
                acc_name = "Emergency Reserve"

            res_str, act_type, act_data = await self.execute_tool("open_new_account", {
                "account_name": acc_name,
                "account_type": acc_type,
                "currency": "USD",
                "card_brand": card_brand,
                "initial_deposit_dollars": 500.0
            }, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["open_new_account"])

        if any(w in last_msg for w in ["all accounts", "semua rekening", "list accounts", "my accounts", "daftar rekening"]):
            res_str, act_type, act_data = await self.execute_tool("get_all_accounts", {}, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["get_all_accounts"])

        if any(w in last_msg for w in ["balance", "saldo", "how much money", "account details"]):
            res_str, act_type, act_data = await self.execute_tool("get_balance", {}, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["get_balance"])

        if any(w in last_msg for w in ["history", "recent", "spent", "mutasi", "activities"]):
            res_str, act_type, act_data = await self.execute_tool("get_transactions", {"limit": 5}, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["get_transactions"])

        if any(w in last_msg for w in ["statement", "rekening koran", "laporan"]):
            res_str, act_type, act_data = await self.execute_tool("request_account_statement", {}, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["request_account_statement"])

        if any(w in last_msg for w in ["transfer", "send", "kirim", "pay"]):
            res_str, act_type, act_data = await self.execute_tool("draft_transfer", {
                "to_account_number": "ACC-83920194",
                "amount": 50.0,
                "description": "AI Assistant Transfer"
            }, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["draft_transfer"])

        res_str, act_type, act_data = await self.execute_tool("get_balance", {}, auth_token)
        return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["get_balance"])


class IdentitySubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="IdentitySubAgent",
            domain="identity",
            system_prompt=(
                "You are Nova's Identity & KYC Sub-Agent. You specialize exclusively in user profiles, "
                "residential address changes, and government document KYC verifications."
            )
        )

    async def fallback_run(self, messages: List[ChatMessage], auth_token: Optional[str] = None) -> ChatResponse:
        last_msg = messages[-1].content.lower() if messages else ""

        if any(w in last_msg for w in ["address to", "change address", "update address", "ganti alamat"]):
            res_str, act_type, act_data = await self.execute_tool("update_user_address", {
                "street": "450 Wall St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10005",
                "country": "United States"
            }, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["update_user_address"])

        if any(w in last_msg for w in ["submit kyc", "passport", "national id", "verifikasi kyc"]):
            res_str, act_type, act_data = await self.execute_tool("submit_kyc_verification", {
                "doc_type": "PASSPORT",
                "doc_number": "US-PASS-992019"
            }, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["submit_kyc_verification"])

        res_str, act_type, act_data = await self.execute_tool("get_user_profile", {}, auth_token)
        return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["get_user_profile"])


class SecuritySubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="SecuritySubAgent",
            domain="security",
            system_prompt=(
                "You are Nova's Security & Risk Sub-Agent. You handle emergency card locking/freezing "
                "and setting account daily spending limits."
            )
        )

    async def fallback_run(self, messages: List[ChatMessage], auth_token: Optional[str] = None) -> ChatResponse:
        last_msg = messages[-1].content.lower() if messages else ""

        if any(w in last_msg for w in ["unfreeze", "unlock", "unblock", "buka kunci"]):
            res_str, act_type, act_data = await self.execute_tool("lock_unlock_card", {"freeze": False, "reason": "User requested card unfreeze"}, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["lock_unlock_card"])

        if any(w in last_msg for w in ["freeze", "lock", "block", "bekukan", "blokir"]):
            res_str, act_type, act_data = await self.execute_tool("lock_unlock_card", {"freeze": True, "reason": "Emergency card freeze requested"}, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["lock_unlock_card"])

        if any(w in last_msg for w in ["spending limit", "transfer limit", "daily limit", "set limit", "atur limit"]):
            res_str, act_type, act_data = await self.execute_tool("set_spending_limit", {"daily_limit_dollars": 8000.0}, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["set_spending_limit"])

        res_str, act_type, act_data = await self.execute_tool("lock_unlock_card", {"freeze": True, "reason": "Security status check"}, auth_token)
        return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["lock_unlock_card"])


class WealthSubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="WealthSubAgent",
            domain="wealth",
            system_prompt=(
                "You are Nova's Wealth & Financial Planning Sub-Agent. You handle live currency exchange calculations (forex), "
                "loan and mortgage amortization simulations, and trusted transfer contacts / beneficiaries."
            )
        )

    async def fallback_run(self, messages: List[ChatMessage], auth_token: Optional[str] = None) -> ChatResponse:
        last_msg = messages[-1].content.lower() if messages else ""

        if any(w in last_msg for w in ["convert", "exchange", "kurs", "valas", "forex", "idr", "eur", "usd"]):
            res_str, act_type, act_data = await self.execute_tool("calculate_forex_conversion", {
                "amount": 500.0,
                "from_currency": "USD",
                "to_currency": "IDR" if "idr" in last_msg else "EUR"
            }, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["calculate_forex_conversion"])

        if any(w in last_msg for w in ["loan", "mortgage", "pinjaman", "kpr", "cicilan", "installment"]):
            res_str, act_type, act_data = await self.execute_tool("calculate_loan_mortgage", {
                "principal": 35000.0,
                "annual_rate_pct": 6.5,
                "term_months": 60,
                "loan_type": "PERSONAL"
            }, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["calculate_loan_mortgage"])

        if any(w in last_msg for w in ["beneficiar", "payee", "kontak", "penerima"]):
            action = "add" if "add" in last_msg or "tambah" in last_msg else "list"
            res_str, act_type, act_data = await self.execute_tool("manage_beneficiaries", {
                "action": action,
                "nickname": "Sarah Smith",
                "account_number": "ACC-83920194",
                "bank_name": "AURA Core Bank"
            }, auth_token)
            return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["manage_beneficiaries"])

        res_str, act_type, act_data = await self.execute_tool("manage_beneficiaries", {"action": "list"}, auth_token)
        return ChatResponse(reply=res_str, action_type=act_type, action_data=act_data, tools_used=["manage_beneficiaries"])


class SupportFaqSubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            name="SupportFaqSubAgent",
            domain="support",
            system_prompt=(
                "You are Nova's Bank Policy & Knowledge Store Sub-Agent. You answer general banking questions, "
                "interest rates, security policies, wire fees, and customer support inquiries."
            )
        )

    async def get_tools(self) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "function": {
                "name": "search_bank_faq",
                "description": "Search banking policy, limits, fees, and FAQ in ChromaDB vector store.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            }
        }]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], auth_token: Optional[str] = None) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        query = arguments.get("query", "")
        res_text = faq_repository.search(query, n_results=3)
        return res_text, None, None

    async def fallback_run(self, messages: List[ChatMessage], auth_token: Optional[str] = None) -> ChatResponse:
        last_raw = messages[-1].content if messages else ""
        res_str, _, _ = await self.execute_tool("search_bank_faq", {"query": last_raw}, auth_token)
        reply = f"Bank Knowledge Base results:\n\n{res_str}"
        return ChatResponse(reply=reply, action_type=None, action_data=None, tools_used=["search_bank_faq"])


class AgentService:
    def __init__(self):
        self.tx_agent = TransactionSubAgent()
        self.id_agent = IdentitySubAgent()
        self.sec_agent = SecuritySubAgent()
        self.wlt_agent = WealthSubAgent()
        self.faq_agent = SupportFaqSubAgent()

    def _classify_intent(self, message: str) -> str:
        msg = message.lower()

        if any(w in msg for w in ["profile", "kyc", "address to", "change address", "update address", "passport", "who am i", "my details", "identity"]):
            return "IDENTITY"

        if any(w in msg for w in ["freeze", "lock", "block", "unfreeze", "unlock", "unblock", "spending limit", "transfer limit", "daily limit", "set limit"]):
            return "SECURITY"

        if any(w in msg for w in ["convert", "exchange", "rate", "forex", "loan", "mortgage", "installment", "beneficiar", "saved payee", "trusted contact", "my payees", "add payee"]):
            return "WEALTH"

        if any(w in msg for w in ["fee", "interest", "apy", "policy", "fdic", "wire fee", "swift", "international", "help", "faq"]):
            return "SUPPORT"

        return "TRANSACTION"

    async def process_chat(
        self,
        messages: List[ChatMessage],
        auth_token: str,
        api_key_override: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> ChatResponse:
        api_key = api_key_override or settings.OPENROUTER_API_KEY
        model_name = model_override or settings.OPENROUTER_MODEL
        last_msg = messages[-1].content if messages else ""

        openai_client = None
        if api_key and api_key.strip() and api_key != "YOUR_OPENROUTER_API_KEY_HERE":
            try:
                openai_client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key.strip(),
                    default_headers={
                        "HTTP-Referer": "http://localhost:5173",
                        "X-Title": "Antigravity Bank AI Assistant",
                    }
                )
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")

        domain = self._classify_intent(last_msg)
        logger.info(f"Supervisor Orchestrator routed message to SubAgent domain '{domain}'")

        if domain == "IDENTITY":
            return await self.id_agent.run(messages, auth_token, openai_client, model_name)
        elif domain == "SECURITY":
            return await self.sec_agent.run(messages, auth_token, openai_client, model_name)
        elif domain == "WEALTH":
            return await self.wlt_agent.run(messages, auth_token, openai_client, model_name)
        elif domain == "SUPPORT":
            return await self.faq_agent.run(messages, auth_token, openai_client, model_name)
        else:
            return await self.tx_agent.run(messages, auth_token, openai_client, model_name)

agent_service = AgentService()
