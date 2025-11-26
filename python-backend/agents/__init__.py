"""
Business Partner AI - Agent Modules

This package contains all specialized agents:
- onboarding_agent: Handles customer onboarding, conversation, and photo analysis
- underwriting_agent: Loan risk assessment and offer generation
- servicing_agent: Handles disbursement, repayments, and recovery
- coaching_agent: Business advice and growth strategies

Legacy agents (kept for reference):
- conversation_agent: Legacy orchestrator (replaced by onboarding_agent)
- vision_agent: Legacy photo analysis (integrated into onboarding_agent)
"""

from .onboarding_agent import onboarding_agent, initialize_onboarding_agent
from .underwriting_agent import underwriting_agent, initialize_underwriting_agent
from .servicing_agent import servicing_agent, initialize_servicing_agent
from .coaching_agent import coaching_agent, initialize_coaching_agent

# Legacy imports (kept for backward compatibility)
from .conversation_agent import conversation_agent, initialize_conversation_agent
from .vision_agent import vision_agent, initialize_vision_agent

__all__ = [
    "onboarding_agent",
    "underwriting_agent",
    "servicing_agent",
    "coaching_agent",
    "initialize_onboarding_agent",
    "initialize_underwriting_agent",
    "initialize_servicing_agent",
    "initialize_coaching_agent",
    # Legacy exports
    "conversation_agent",
    "vision_agent",
    "initialize_conversation_agent",
    "initialize_vision_agent",
]
