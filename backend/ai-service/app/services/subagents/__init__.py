"""
Sub-Agents Package for Tirenn Banking Microservice.
==================================================
Exports all domain sub-agents and provides the pre-configured SubAgentRegistry.
"""

from app.services.subagents.base import BaseSubAgent
from app.services.subagents.registry import SubAgentRegistry, subagent_registry
from app.services.subagents.transaction import TransactionSubAgent
from app.services.subagents.identity import IdentitySubAgent
from app.services.subagents.security import SecuritySubAgent
from app.services.subagents.wealth import WealthSubAgent
from app.services.subagents.support_faq import SupportFaqSubAgent

# Instantiate default sub-agents
default_transaction_agent = TransactionSubAgent()
default_identity_agent = IdentitySubAgent()
default_security_agent = SecuritySubAgent()
default_wealth_agent = WealthSubAgent()
default_support_faq_agent = SupportFaqSubAgent()

# Pre-register all sub-agents into the global registry (Open/Closed Principle)
subagent_registry.register("TRANSACTION", default_transaction_agent)
subagent_registry.register("IDENTITY", default_identity_agent)
subagent_registry.register("SECURITY", default_security_agent)
subagent_registry.register("WEALTH", default_wealth_agent)
subagent_registry.register("SUPPORT", default_support_faq_agent)

__all__ = [
    "BaseSubAgent",
    "SubAgentRegistry",
    "subagent_registry",
    "TransactionSubAgent",
    "IdentitySubAgent",
    "SecuritySubAgent",
    "WealthSubAgent",
    "SupportFaqSubAgent",
    "default_transaction_agent",
    "default_identity_agent",
    "default_security_agent",
    "default_wealth_agent",
    "default_support_faq_agent",
]
