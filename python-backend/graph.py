"""
LangGraph Definition - Orchestrates the multi-agent flow.

The graph structure:
1. Start with onboarding agent (handles conversation + photo analysis)
2. Conditionally route to specialist agents based on state:
   - Underwriting agent (generates loan offers)
   - Servicing agent (disbursement, repayments, recovery)
   - Coaching agent (business advice)
3. Return to onboarding agent after specialist processing
4. End when no more agents need to be called
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import BusinessPartnerState
from agents.onboarding_agent import OnboardingAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.servicing_agent import ServicingAgent
from agents.coaching_agent import CoachingAgent

# Module-level agent instances - will be initialized in build_graph()
_onboarding_agent = None
_underwriting_agent = None
_servicing_agent = None
_coaching_agent = None


def onboarding_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Onboarding agent node - handles conversation, info gathering, and photo analysis."""
    result = _onboarding_agent.process(state)
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


def route_after_onboarding(state: BusinessPartnerState) -> Literal["underwriting", "servicing", "coaching", "end"]:
    """
    Routing function to determine which agent to call next after onboarding.

    Based on the `next_agent` field set by the onboarding agent.
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
    - Start → Onboarding
    - Onboarding → (Underwriting | Servicing | Coaching | End)
    - Specialist Agents → Onboarding (for integration)
    """

    # Initialize agents
    global _onboarding_agent, _underwriting_agent, _servicing_agent, _coaching_agent
    _onboarding_agent = OnboardingAgent()
    _underwriting_agent = UnderwritingAgent()
    _servicing_agent = ServicingAgent()
    _coaching_agent = CoachingAgent()

    # Create the graph
    workflow = StateGraph(BusinessPartnerState)

    # Add nodes
    workflow.add_node("onboarding", onboarding_node)
    workflow.add_node("underwriting", underwriting_node)
    workflow.add_node("servicing", servicing_node)
    workflow.add_node("coaching", coaching_node)

    # Set entry point
    workflow.set_entry_point("onboarding")

    # Add conditional edges from onboarding
    workflow.add_conditional_edges(
        "onboarding",
        route_after_onboarding,
        {
            "underwriting": "underwriting",
            "servicing": "servicing",
            "coaching": "coaching",
            "end": END,
        },
    )

    # After specialist agents, return to onboarding to integrate results
    workflow.add_edge("underwriting", "onboarding")
    workflow.add_edge("servicing", "onboarding")
    workflow.add_edge("coaching", "onboarding")

    # Compile with checkpointer for conversation memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


# Create the compiled graph
graph = build_graph()
