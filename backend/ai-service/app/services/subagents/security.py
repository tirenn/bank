"""
Security Sub-Agent for Tirenn Banking Microservice.
==================================================
Handles debit card safety and risk governance:
- Freezing and unfreezing debit cards
- Adjusting daily transfer and spending limits
- Card status verification
"""

from app.services.subagents.base import BaseSubAgent


class SecuritySubAgent(BaseSubAgent):
    """
    Specialized agent for debit card protection and security limit controls.
    Dispatches to MCP tools in the 'security' domain.
    """

    def __init__(self):
        super().__init__(
            name="SecuritySubAgent",
            domain="security",
            prompt_file="security_agent.md"
        )
