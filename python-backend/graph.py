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
from langfuse.decorators import observe, langfuse_context

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


@observe(name="graph-node-business-partner")
def business_partner_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Business partner agent node - handles conversation, info gathering, and photo analysis."""
    langfuse_context.update_current_observation(
        input={
            "phase": state.get("phase"),
            "business_type": state.get("business_type"),
            "message_count": len(state.get("messages", [])),
        },
        metadata={"node": "business_partner", "agent_type": "onboarding"},
    )
    result = _business_partner_agent.process(state)
    langfuse_context.update_current_observation(
        output={
            "next_agent": result.get("next_agent"),
            "phase": result.get("phase"),
            "info_complete": result.get("info_complete"),
        }
    )
    return result


@observe(name="graph-node-underwriting")
def underwriting_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Underwriting agent node - generates loan offers."""
    langfuse_context.update_current_observation(
        input={
            "business_type": state.get("business_type"),
            "monthly_revenue": state.get("monthly_revenue"),
            "has_photo_insights": len(state.get("photo_insights", [])) > 0,
        },
        metadata={"node": "underwriting", "agent_type": "specialist"},
    )
    result = _underwriting_agent.process(state)
    langfuse_context.update_current_observation(
        output={
            "loan_offer_generated": result.get("loan_offer") is not None,
            "risk_score": result.get("risk_score"),
            "risk_tier": result.get("risk_tier"),
        }
    )
    return result


@observe(name="graph-node-servicing")
def servicing_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Servicing agent node - handles disbursement, repayments, and recovery."""
    langfuse_context.update_current_observation(
        input={
            "servicing_type": state.get("servicing_type"),
            "phase": state.get("phase"),
            "loan_accepted": state.get("loan_accepted"),
        },
        metadata={"node": "servicing", "agent_type": "specialist"},
    )
    result = _servicing_agent.process(state)
    langfuse_context.update_current_observation(
        output={
            "disbursement_status": result.get("disbursement_status"),
            "repayment_status": result.get("repayment_status"),
            "recovery_status": result.get("recovery_status"),
        }
    )
    return result


@observe(name="graph-node-coaching")
def coaching_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Coaching agent node - provides business advice."""
    langfuse_context.update_current_observation(
        input={
            "business_type": state.get("business_type"),
            "phase": state.get("phase"),
            "loan_accepted": state.get("loan_accepted"),
        },
        metadata={"node": "coaching", "agent_type": "specialist"},
    )
    result = _coaching_agent.process(state)
    langfuse_context.update_current_observation(
        output={
            "coaching_advice_generated": result.get("coaching_advice") is not None,
        }
    )
    return result


@observe(name="graph-routing")
def route_after_business_partner(state: BusinessPartnerState) -> Literal["underwriting", "servicing", "coaching", "end"]:
    """
    Routing function to determine which agent to call next after business_partner.

    Based on the `next_agent` field set by the business_partner agent.
    """
    next_agent = state.get("next_agent")
    
    langfuse_context.update_current_observation(
        input={"next_agent": next_agent, "phase": state.get("phase")},
        metadata={"routing_decision": True},
    )
    
    routing_result = None
    if next_agent == "underwriting":
        routing_result = "underwriting"
    elif next_agent == "servicing":
        routing_result = "servicing"
    elif next_agent == "coaching":
        routing_result = "coaching"
    else:
        routing_result = "end"
    
    langfuse_context.update_current_observation(output={"routed_to": routing_result})
    return routing_result


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
