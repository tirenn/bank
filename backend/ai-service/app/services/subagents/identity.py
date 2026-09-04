"""
Identity Sub-Agent for Tirenn Banking Microservice.
==================================================
Handles customer identity and profile management:
- Customer profile retrieval
- Residential address updates
- KYC identity verification & Tier-2 upgrades
"""

from app.services.subagents.base import BaseSubAgent


class IdentitySubAgent(BaseSubAgent):
    """
    Specialized agent for customer identity and profile operations.
    Dispatches to MCP tools in the 'identity' domain.
    """

    def __init__(self):
        super().__init__(
            name="IdentitySubAgent",
            domain="identity",
            prompt_file="identity_agent.md"
        )
