"""
Transaction Sub-Agent for Tirenn Banking Microservice.
=====================================================
Handles core banking transactions:
- Account balance inquiries
- Peer-to-Peer (P2P) fund transfers
- Transaction history streaming & spending summaries
- Account provisioning and statement downloads
"""

from app.services.subagents.base import BaseSubAgent


class TransactionSubAgent(BaseSubAgent):
    """
    Specialized agent for transactional financial operations.
    Dispatches to MCP tools in the 'transaction' domain.
    """

    def __init__(self):
        super().__init__(
            name="TransactionSubAgent",
            domain="transaction",
            prompt_file="transaction_agent.md"
        )
