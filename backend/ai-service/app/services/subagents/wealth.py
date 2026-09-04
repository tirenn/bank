"""
Wealth & Financial Calculations Sub-Agent for Tirenn Banking Microservice.
=========================================================================
Handles wealth advisory and mathematical calculators:
- Real-time foreign exchange (Forex) currency conversions
- Loan and mortgage compound amortization monthly payment calculations
- Managing saved trusted beneficiaries/payees
"""

from app.services.subagents.base import BaseSubAgent


class WealthSubAgent(BaseSubAgent):
    """
    Specialized agent for wealth management, forex, and loan simulations.
    Dispatches to MCP tools in the 'wealth' domain.
    """

    def __init__(self):
        super().__init__(
            name="WealthSubAgent",
            domain="wealth",
            prompt_file="wealth_agent.md"
        )
