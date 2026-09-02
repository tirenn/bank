package security

import (
	"regexp"
	"strings"
)

var (
	// 15-16 digit Card Numbers
	cardRegex = regexp.MustCompile(`\b(?:\d[ -]*?){13,19}\b`)

	// CVV / CVC near keywords
	cvvRegex = regexp.MustCompile(`(?i)\b(?:cvv|cvc|cid|security\s*code)[\s:=]+(\d{3,4})\b`)

	// Passwords / Secrets in key-value strings
	passwordRegex = regexp.MustCompile(`(?i)("?(?:password|pass|secret|api_key|token)"?\s*[:=]\s*["'])([^"']+)(["'])`)

	// JWT Bearer tokens
	jwtRegex = regexp.MustCompile(`\bBearer\s+(eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+)\b`)

	// Emails
	emailRegex = regexp.MustCompile(`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b`)
)

func maskCard(s string) string {
	digits := regexp.MustCompile(`\D`).ReplaceAllString(s, "")
	if len(digits) == 15 || len(digits) == 16 {
		last4 := digits[len(digits)-4:]
		return "•••• •••• •••• " + last4
	}
	return s
}

// RedactText sanitizes plain text, masking credit cards, passwords, CVVs, and JWTs.
func RedactText(text string, maskEmail bool) string {
	if text == "" {
		return text
	}

	sanitized := jwtRegex.ReplaceAllString(text, "Bearer [AUTH_TOKEN_REDACTED]")
	sanitized = passwordRegex.ReplaceAllString(sanitized, "${1}[REDACTED]${3}")
	sanitized = cvvRegex.ReplaceAllString(sanitized, "CVV: [CVV_REDACTED]")
	sanitized = cardRegex.ReplaceAllStringFunc(sanitized, maskCard)

	if maskEmail {
		sanitized = emailRegex.ReplaceAllString(sanitized, "[EMAIL_REDACTED]")
	}

	return sanitized
}

// RedactMap recursively sanitizes key-value maps.
func RedactMap(data map[string]interface{}, maskEmail bool) map[string]interface{} {
	if data == nil {
		return nil
	}

	sanitized := make(map[string]interface{}, len(data))
	for k, v := range data {
		kLower := strings.ToLower(k)
		if strings.Contains(kLower, "password") || strings.Contains(kLower, "token") || strings.Contains(kLower, "secret") || strings.Contains(kLower, "cvv") {
			sanitized[k] = "[REDACTED]"
		} else if strings.Contains(kLower, "card_number") {
			if strVal, ok := v.(string); ok {
				digits := regexp.MustCompile(`\D`).ReplaceAllString(strVal, "")
				if len(digits) >= 4 {
					sanitized[k] = "•••• •••• •••• " + digits[len(digits)-4:]
				} else {
					sanitized[k] = "[CARD_REDACTED]"
				}
			} else {
				sanitized[k] = "[CARD_REDACTED]"
			}
		} else if strVal, ok := v.(string); ok {
			sanitized[k] = RedactText(strVal, maskEmail)
		} else if mapVal, ok := v.(map[string]interface{}); ok {
			sanitized[k] = RedactMap(mapVal, maskEmail)
		} else {
			sanitized[k] = v
		}
	}

	return sanitized
}
