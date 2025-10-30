"""
LangGraph Definition - Orchestrates the multi-agent flow.

The graph structure:
1. Start with conversation agent
2. Conditionally route to specialist agents based on state
3. Return to conversation agent after specialist processing
4. End when no more agents need to be called
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import BusinessPartnerState
from agents.conversation_agent import ConversationAgent
from agents.vision_agent import VisionAgent
from agents.underwriting_agent import UnderwritingAgent
from agents.coaching_agent import CoachingAgent

# Module-level agent instances - will be initialized in build_graph()
_conversation_agent = None
_vision_agent = None
_underwriting_agent = None
_coaching_agent = None


def conversation_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Main conversation node - handles dialogue and routing."""
    result = _conversation_agent.process(state)
    return result


def vision_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Vision agent node - analyzes photos."""
    result = _vision_agent.process(state)
    return result


def underwriting_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Underwriting agent node - generates loan offers."""
    result = _underwriting_agent.process(state)
    return result


def coaching_node(state: BusinessPartnerState) -> BusinessPartnerState:
    """Coaching agent node - provides business advice."""
    result = _coaching_agent.process(state)
    return result


def route_after_conversation(state: BusinessPartnerState) -> Literal["vision", "underwriting", "coaching", "end"]:
    """
    Routing function to determine which agent to call next after conversation.

    Based on the `next_agent` field set by the conversation agent.
    """
    next_agent = state.get("next_agent")

    if next_agent == "vision":
        return "vision"
    elif next_agent == "underwriting":
        return "underwriting"
    elif next_agent == "coaching":
        return "coaching"
    else:
        return "end"


def build_graph() -> StateGraph:
    """
    Build the LangGraph workflow.

    Flow:
    - Start → Conversation
    - Conversation → (Vision | Underwriting | Coaching | End)
    - Specialist Agents → Conversation (for integration)
    """

    # Initialize agents
    global _conversation_agent, _vision_agent, _underwriting_agent, _coaching_agent
    _conversation_agent = ConversationAgent()
    _vision_agent = VisionAgent()
    _underwriting_agent = UnderwritingAgent()
    _coaching_agent = CoachingAgent()

    # Create the graph
    workflow = StateGraph(BusinessPartnerState)

    # Add nodes
    workflow.add_node("conversation", conversation_node)
    workflow.add_node("vision", vision_node)
    workflow.add_node("underwriting", underwriting_node)
    workflow.add_node("coaching", coaching_node)

    # Set entry point
    workflow.set_entry_point("conversation")

    # Add conditional edges from conversation
    workflow.add_conditional_edges(
        "conversation",
        route_after_conversation,
        {
            "vision": "vision",
            "underwriting": "underwriting",
            "coaching": "coaching",
            "end": END,
        },
    )

    # After specialist agents, return to conversation to integrate results
    workflow.add_edge("vision", "conversation")
    workflow.add_edge("underwriting", "conversation")
    workflow.add_edge("coaching", "conversation")

    # Compile with checkpointer for conversation memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


# Create the compiled graph
graph = build_graph()
