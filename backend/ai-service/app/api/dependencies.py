import json
import base64
import logging
from fastapi import Header, HTTPException

logger = logging.getLogger("ai_service.api.dependencies")

def require_admin_role(authorization: str = Header(None, description="Bearer JWT token")) -> dict:
    """
    Enforces Role-Based Access Control (RBAC).
    Verifies that the caller's JWT token contains role == 'ADMIN'.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authentication required: missing or invalid Bearer authorization header."
        )

    token = authorization.split(" ")[1]
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed JWT format.")
        
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_json)

        role = payload.get("role", "CUSTOMER")
        if str(role).upper() != "ADMIN":
            logger.warning(f"Access denied: user {payload.get('email')} with role '{role}' tried to access admin RAG endpoint.")
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: role '{role}' is not authorized to manage RAG knowledge base. Admin privilege required."
            )

        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing JWT token for RBAC: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid authorization token: {str(e)}")
