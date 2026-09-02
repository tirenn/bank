import re
import html
from typing import Tuple, Optional, List, Dict, Any
from app.logger import app_logger as logger

class PromptInjectionGuardrail:
    """
    Edge Prompt Injection & Adversarial Jailbreak Defense Harness.
    Detects and intercepts malicious jailbreak attempts, prompt exfiltration,
    delimiter hijacking, and privilege escalation before LLM execution.
    """

    def __init__(self):
        # 1. System Prompt Leakage & Extraction Vectors
        self._leakage_patterns = [
            r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|rules|prompts)",
            r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|rules)",
            r"(output|print|show|reveal|display|repeat|echo|tell\s+me)\s+(your\s+)?(system\s+prompt|initial\s+prompt|instructions\s+verbatim|system\s+instructions|base\s+prompt)",
            r"what\s+(is|are)\s+your\s+(exact\s+)?(system\s+prompt|initial\s+instructions|original\s+prompt|system\s+rules)",
            r"(tampilkan|tuliskan|berikan|bocorkan)\s+(system\s+prompt|instruksi\s+awal|aturan\s+rahasia)",
            r"abaikan\s+(semua\s+)?(instruksi|perintah|aturan)\s+(sebelumnya|di\s+atas)"
        ]

        # 2. Persona Hijacking & Jailbreak Modes
        self._jailbreak_patterns = [
            r"\b(dan\s+mode|do\s+anything\s+now)\b",
            r"\b(developer\s+mode\s+(enabled|on|active))\b",
            r"\b(act\s+as\s+(an?\s+)?(unfiltered|unrestricted|uncensored|evil|jailbroken)\s+ai)\b",
            r"\b(you\s+have\s+no\s+(rules|ethics|guidelines|restrictions|limits))\b",
            r"\b(bypass\s+(all\s+)?(guardrails|safety\s+filters|content\s+policies))\b",
            r"\b(mode\s+tanpa\s+filter|tanpa\s+batasan)\b"
        ]

        # 3. Delimiter Hijacking & Fake System Headers
        self._delimiter_patterns = [
            r"</?system>",
            r"</?instructions?>",
            r"\[\s*system\s*(\s+message|\s+instruction|\s*:)?\s*\]",
            r"---+\s*(end\s+of\s+system|begin\s+unrestricted|system\s+override)\s*---+",
            r"###\s*(system\s+override|instruction\s+override|admin\s+directive)"
        ]

        # 4. Financial Privilege Escalation & Guardrail Bypass
        self._bypass_patterns = [
            r"(bypass|skip|ignore)\s+(all\s+)?(confirmation|otp|pin|kyc|two-factor|2fa|security\s+verification)",
            r"without\s+(any\s+)?(asking|confirmation|otp|pin|2fa|verification|authoriz\w+)",
            r"transfer\s+.*(without\s+asking|without\s+confirmation|without\s+otp|silently|immediately)",
            r"\b(sudo\s+|superuser\s+override|root\s+access\s+granted)\b"
        ]


        # Compile regular expressions for sub-millisecond execution
        self._compiled_leakage = [re.compile(p, re.IGNORECASE) for p in self._leakage_patterns]
        self._compiled_jailbreak = [re.compile(p, re.IGNORECASE) for p in self._jailbreak_patterns]
        self._compiled_delimiter = [re.compile(p, re.IGNORECASE) for p in self._delimiter_patterns]
        self._compiled_bypass = [re.compile(p, re.IGNORECASE) for p in self._bypass_patterns]

    def inspect_prompt(self, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Inspects an inbound customer prompt for prompt injection and adversarial attacks.
        Returns: (is_attack: bool, attack_category: Optional[str], refusal_message: Optional[str])
        """
        if not text or not isinstance(text, str):
            return False, None, None

        cleaned = text.strip()

        # Check Category 1: System Prompt Leakage / Extraction
        for pattern in self._compiled_leakage:
            if pattern.search(cleaned):
                return True, "SYSTEM_PROMPT_LEAKAGE", self._generate_refusal("system_prompt_leakage")

        # Check Category 2: Jailbreak & Persona Hijacking
        for pattern in self._compiled_jailbreak:
            if pattern.search(cleaned):
                return True, "JAILBREAK_ATTEMPT", self._generate_refusal("jailbreak_attempt")

        # Check Category 3: Delimiter Hijacking & Tag Injection
        for pattern in self._compiled_delimiter:
            if pattern.search(cleaned):
                return True, "DELIMITER_HIJACKING", self._generate_refusal("delimiter_hijacking")

        # Check Category 4: Financial Privilege Escalation
        for pattern in self._compiled_bypass:
            if pattern.search(cleaned):
                return True, "FINANCIAL_BYPASS_EXPLOIT", self._generate_refusal("financial_bypass")

        return False, None, None

    def sanitize_and_isolate(self, text: str) -> str:
        """
        Escapes dangerous markup and wraps customer content inside strict XML boundary tags.
        """
        if not text:
            return ""
        # Neutralize XML-like tag injections
        escaped = html.escape(text.strip())
        return f"<customer_message>\n{escaped}\n</customer_message>"

    def _generate_refusal(self, attack_type: str) -> str:
        refusals = {
            "system_prompt_leakage": (
                "🛡️ **Security Notice**: I cannot disclose, output, or modify my internal system instructions, "
                "prompts, or security architecture. How may I assist you with your banking services today?"
            ),
            "jailbreak_attempt": (
                "🛡️ **Security Notice**: Unauthorized persona overrides, developer modes, or unrestricted AI jailbreaks "
                "are prohibited by Tirenn Bank Security Protocols. All operations must strictly follow financial regulatory standards."
            ),
            "delimiter_hijacking": (
                "🛡️ **Security Notice**: Input contains invalid system delimiters or tag injection attempts. "
                "Your request has been blocked by the Banking Security Guardrail."
            ),
            "financial_bypass": (
                "🛡️ **Security Notice**: Financial security verifications, OTP, and customer confirmation guardrails "
                "cannot be bypassed under any circumstances. All transactions require explicit customer authorization."
            )
        }
        return refusals.get(
            attack_type,
            "🛡️ **Security Notice**: This request was blocked by Tirenn Bank Prompt Injection Security Guardrail."
        )


prompt_injection_guardrail = PromptInjectionGuardrail()
