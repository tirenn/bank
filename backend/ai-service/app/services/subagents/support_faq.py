"""
Support & FAQ Knowledge Base Sub-Agent for Tirenn Banking Microservice.
======================================================================
Handles semantic retrieval across the vector FAQ knowledge base:
- Banking policies, international wire transfer fees, and branch rules
- Minimum balance requirements and overdraft protection policies
- APY interest rates and certificate of deposit (CD) details
"""

from typing import List, Dict, Any, Optional, Tuple
from app.services.subagents.base import BaseSubAgent
from app.repositories.faq_repository import faq_repository


class SupportFaqSubAgent(BaseSubAgent):
    """
    Specialized agent for bank policies and FAQ inquiries.
    Uses ChromaDB dense vector search instead of external REST endpoints.
    """

    def __init__(self):
        super().__init__(
            name="SupportFaqSubAgent",
            domain="support",
            prompt_file="support_faq_agent.md"
        )

    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Defines the function schema for vector FAQ search.
        Cached in-memory to prevent rebuilding JSON schema on every turn.
        """
        if self._cached_tools is None:
            self._cached_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_bank_faq",
                        "description": (
                            "Semantic search across Tirenn Bank vector FAQ knowledge base "
                            "for policies, wire fees, rules, APY interest, and help articles."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language query to search in vector knowledge base"
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "Number of top matching FAQ entries to retrieve (default: 3)",
                                    "default": 3
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            ]
        return self._cached_tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        auth_token: Optional[str] = None
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        Executes vector search against ChromaDB and formats top matches.
        """
        if tool_name == "search_bank_faq":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 3)
            # Delegate to the 5-stage Hybrid Search, RRF, and Deduplication pipeline
            from app.services.rag_pipeline_service import rag_pipeline_service
            return await rag_pipeline_service.search_and_format(query=query, top_k_final=top_k)

        return f"Unknown FAQ tool: {tool_name}", None, None
