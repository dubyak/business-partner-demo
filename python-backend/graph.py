"""
LangGraph Definition - Orchestrates the multi-agent flow.

The graph structure:
1. Start with business_partner agent (handles conversation + photo analysis)
2. Conditionally route to specialist agents based on state:
   - Underwriting agent (generates loan offers)
   - Servicing agent (disbursement, repayments, recovery)
   - Coaching agent (business advice)
3. Return to business_partner agent after specialist processing
4. End when no more agents need to be called
"""

import os
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Try to use SqliteSaver for persistent storage, fallback to MemorySaver
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    USE_SQLITE = True
except ImportError:
    USE_SQLITE = False
    print("[GRAPH] SqliteSaver not available, using MemorySaver (in-memory only)")

from state import BusinessPartnerState
from agents.onboarding_agent import OnboardingAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.servicing_agent import ServicingAgent
from agents.coaching_agent import CoachingAgent

# Module-level agent instances - will be initialized in build_graph()
_business_partner_agent = None
_underwriting_agent = None
_servicing_agent = None
_coaching_agent = None


def business_partner_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Business partner agent node - handles conversation, info gathering, and photo analysis."""
    result = _business_partner_agent.process(state)
    return result


def underwriting_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Underwriting agent node - generates loan offers."""
    result = _underwriting_agent.process(state)
    return result


def servicing_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Servicing agent node - handles disbursement, repayments, and recovery."""
    result = _servicing_agent.process(state)
    return result


def coaching_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Coaching agent node - provides business advice."""
    result = _coaching_agent.process(state)
    return result


def route_after_business_partner(state: BusinessPartnerState) -> Literal["underwriting", "servicing", "coaching", "end"]:
    """
    Routing function to determine which agent to call next after business_partner.

    Based on the `next_agent` field set by the business_partner agent.
    """
    next_agent = state.get("next_agent")

    if next_agent == "underwriting":
        return "underwriting"
    elif next_agent == "servicing":
        return "servicing"
    elif next_agent == "coaching":
        return "coaching"
    else:
        return "end"


def build_graph() -> StateGraph:
    """
    Build the LangGraph workflow.

    Flow:
    - Start → Business Partner
    - Business Partner → (Underwriting | Servicing | Coaching | End)
    - Specialist Agents → Business Partner (for integration)
    """

    # Initialize agents
    global _business_partner_agent, _underwriting_agent, _servicing_agent, _coaching_agent
    _business_partner_agent = OnboardingAgent()  # Class name stays same, but node is renamed
    _underwriting_agent = UnderwritingAgent()
    _servicing_agent = ServicingAgent()
    _coaching_agent = CoachingAgent()

    # Create the graph
    workflow = StateGraph(BusinessPartnerState)

    # Add nodes
    workflow.add_node("business_partner", business_partner_node)
    workflow.add_node("underwriting", underwriting_node)
    workflow.add_node("servicing", servicing_node)
    workflow.add_node("coaching", coaching_node)

    # Set entry point
    workflow.set_entry_point("business_partner")

    # Add conditional edges from business_partner
    workflow.add_conditional_edges(
        "business_partner",
        route_after_business_partner,
        {
            "underwriting": "underwriting",
            "servicing": "servicing",
            "coaching": "coaching",
            "end": END,
        },
    )

    # After specialist agents, return to business_partner to integrate results
    workflow.add_edge("underwriting", "business_partner")
    workflow.add_edge("servicing", "business_partner")
    workflow.add_edge("coaching", "business_partner")

    # Compile with checkpointer for conversation memory
    # Use SqliteSaver for persistent storage if available, otherwise MemorySaver
    if USE_SQLITE:
        # Use SQLite for persistent checkpoint storage
        # This ensures state persists across server restarts
        db_path = os.getenv("LANGRAPH_CHECKPOINT_DB", "checkpoints.db")
        checkpointer = SqliteSaver.from_conn_string(db_path)
        print(f"[GRAPH] Using SqliteSaver for persistent checkpoints: {db_path}")
    else:
        checkpointer = MemorySaver()
        print("[GRAPH] Using MemorySaver (in-memory only - state lost on restart)")
    
    app = workflow.compile(checkpointer=checkpointer)

    return app


# Create the compiled graph
graph = build_graph()
