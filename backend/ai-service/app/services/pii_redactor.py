import re
from typing import Any, Dict, List, Union

# Compiled regular expressions for banking & personal PII
# 1. 16-digit Card Numbers with spaces, dashes, or plain digits
CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,19}\b')

# 2. CVV / CVC (3 or 4 digits near keywords like CVV, CVC, CID, security code)
CVV_KEYWORD_REGEX = re.compile(r'(?i)\b(?:cvv|cvc|cid|security\s*code)[\s:=]+(\d{3,4})\b')

# 3. Passwords / Secrets in key-value format (e.g., password: "...", "password": "...")
PASSWORD_KEYWORD_REGEX = re.compile(r'(?i)("?(?:password|pass|secret|api_key|token)"?\s*[:=]\s*["\'])([^"\']+)(["\'])')

# 4. Bearer Tokens & JWTs (e.g. Bearer eyJhbGciOi...)
JWT_REGEX = re.compile(r'\bBearer\s+(eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+)\b')

# 5. Email Addresses (in logs or raw payloads)
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')

# 6. Indonesian NIK / US SSN (16 digits ID or 9 digits SSN format)
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')


def _mask_card_match(match: re.Match) -> str:
    raw = match.group(0)
    clean_digits = re.sub(r'\D', '', raw)
    if len(clean_digits) in (15, 16):
        # Format as masked card: •••• •••• •••• <last4>
        last4 = clean_digits[-4:]
        return f"•••• •••• •••• {last4}"
    return raw


def redact_text(text: str, mask_email: bool = False) -> str:
    """
    Sanitizes plain text, masking sensitive banking PII like credit card PANs,
    CVVs, Passwords, and Auth tokens.
    """
    if not isinstance(text, str) or not text:
        return text

    # Redact JWT Bearer tokens
    sanitized = JWT_REGEX.sub(r'Bearer [AUTH_TOKEN_REDACTED]', text)

    # Redact passwords in key-value strings
    sanitized = PASSWORD_KEYWORD_REGEX.sub(r'\g<1>[REDACTED]\g<3>', sanitized)

    # Redact CVV / CVC codes
    sanitized = CVV_KEYWORD_REGEX.sub(r'CVV: [CVV_REDACTED]', sanitized)

    # Mask 15-16 digit Credit / Debit Card numbers
    sanitized = CARD_REGEX.sub(_mask_card_match, sanitized)

    # Redact SSN
    sanitized = SSN_REGEX.sub(r'[SSN_REDACTED]', sanitized)

    # Optional email masking for logs
    if mask_email:
        sanitized = EMAIL_REGEX.sub(r'[EMAIL_REDACTED]', sanitized)

    return sanitized


def redact_data(data: Any, mask_email: bool = False) -> Any:
    """
    Recursively redacts PII from dictionaries, lists, and strings.
    """
    if isinstance(data, str):
        return redact_text(data, mask_email=mask_email)
    elif isinstance(data, dict):
        sanitized_dict: Dict[str, Any] = {}
        for k, v in data.items():
            key_lower = str(k).lower()
            if any(secret_term in key_lower for secret_term in ("password", "token", "secret", "cvv", "card_cvv")):
                sanitized_dict[k] = "[REDACTED]"
            elif "card_number" in key_lower and isinstance(v, str):
                digits = re.sub(r'\D', '', v)
                if len(digits) >= 4:
                    sanitized_dict[k] = f"•••• •••• •••• {digits[-4:]}"
                else:
                    sanitized_dict[k] = "[CARD_REDACTED]"
            else:
                sanitized_dict[k] = redact_data(v, mask_email=mask_email)
        return sanitized_dict
    elif isinstance(data, list):
        return [redact_data(item, mask_email=mask_email) for item in data]
    return data
