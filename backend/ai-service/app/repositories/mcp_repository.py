import logging
import httpx
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings

logger = logging.getLogger("ai_service.repositories.mcp")

class MCPRepository:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.CORE_BANKING_URL
        self.secret = settings.INTERNAL_MCP_SECRET

    def _get_headers(self, auth_token: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-Internal-MCP-Secret": self.secret,
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}" if not auth_token.startswith("Bearer ") else auth_token
        return headers

    async def list_tools(self, domain: str) -> List[Dict[str, Any]]:
        """
        Query private MCP Server for available tool definitions in a domain.
        Domain can be: 'transaction', 'identity', 'security', 'wealth'
        """
        endpoint = f"{self.base_url}/mcp/v1/{domain}"
        payload = {
            "jsonrpc": "2.0",
            "id": f"list-{domain}",
            "method": "tools/list",
            "params": {}
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(endpoint, headers=self._get_headers(), json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    tools = result.get("tools", [])
                    # Convert to OpenAI function calling format
                    openai_tools = []
                    for t in tools:
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": t.get("name"),
                                "description": t.get("description"),
                                "parameters": t.get("inputSchema", {}),
                            }
                        })
                    return openai_tools
                else:
                    logger.error(f"Failed to list tools for domain {domain}: {resp.status_code} {resp.text}")
                    return []
        except Exception as e:
            logger.error(f"Error connecting to MCP Server ({domain}): {e}", exc_info=True)
            return []

    async def call_tool(
        self, domain: str, name: str, arguments: Dict[str, Any], auth_token: Optional[str] = None
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        Execute tool via Private MCP Server over JSON-RPC 2.0.
        Returns: (result_text, action_type, action_data)
        """
        endpoint = f"{self.base_url}/mcp/v1/{domain}"
        payload = {
            "jsonrpc": "2.0",
            "id": f"call-{name}",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            }
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(endpoint, headers=self._get_headers(auth_token), json=payload)
                if resp.status_code != 200:
                    return f"MCP Server Error ({resp.status_code}): {resp.text}", None, None

                data = resp.json()
                if "error" in data and data["error"]:
                    err = data["error"]
                    return f"MCP Tool Error: {err.get('message', 'Unknown error')}", None, None

                res = data.get("result", {})
                content = res.get("content", [])
                text_out = "\n".join([c.get("text", "") for c in content if c.get("type") == "text"])
                action_type = res.get("action_type")
                action_data = res.get("action_data")

                return text_out, action_type, action_data
        except Exception as e:
            logger.error(f"Error calling MCP tool '{name}' on domain '{domain}': {e}", exc_info=True)
            return f"An error occurred executing {name} via MCP: {str(e)}", None, None

mcp_repository = MCPRepository()
