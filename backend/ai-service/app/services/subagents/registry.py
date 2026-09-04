"""
Sub-Agent Registry for Tirenn Banking Microservice.
=================================================
Implements the Open/Closed Principle (OCP):
The registry allows new banking sub-agents to be registered dynamically
without modifying the core dispatcher or router logic.
"""

from typing import Dict, List, Optional
from app.domain.interfaces import ISubAgent
from app.logger import app_logger as logger


class SubAgentRegistry:
    """
    Central registry for domain-specific sub-agents.
    Provides lookup and registration capabilities.
    """

    def __init__(self):
        self._agents: Dict[str, ISubAgent] = {}

    def register(self, domain: str, agent: ISubAgent) -> None:
        """
        Registers a sub-agent under a specific domain key.
        Args:
            domain: The uppercase domain identifier (e.g. 'TRANSACTION', 'WEALTH').
            agent: Instance conforming to the ISubAgent protocol.
        """
        key = domain.strip().upper()
        self._agents[key] = agent
        logger.debug(f"[SubAgentRegistry] Registered agent '{agent.name}' for domain '{key}'")

    def get(self, domain: str) -> Optional[ISubAgent]:
        """
        Retrieves the sub-agent for a given domain.
        Falls back to 'TRANSACTION' if the domain is not recognized.
        """
        key = domain.strip().upper()
        if key in self._agents:
            return self._agents[key]
        
        # Safe default fallback
        return self._agents.get("TRANSACTION")

    def list_domains(self) -> List[str]:
        """Returns a list of all currently registered domain keys."""
        return list(self._agents.keys())


# Singleton instance for the application
subagent_registry = SubAgentRegistry()
