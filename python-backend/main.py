"""
FastAPI backend for Business Partner AI - Multi-Agent LangGraph Demo

This provides a REST API compatible with the existing frontend,
but powered by LangGraph multi-agent orchestration with full Langfuse tracing.
"""

# Load environment variables FIRST - before any imports that need them
from dotenv import load_dotenv
load_dotenv()

import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langfuse import Langfuse
import time

from graph import graph
from state import BusinessPartnerState
from db import get_or_create_conversation, save_messages
from personas import get_persona, initialize_state_from_persona
from api.personas import router as personas_router

# Initialize FastAPI
app = FastAPI(
    title="Business Partner AI - Multi-Agent Demo",
    description="LangGraph-powered lending assistant with specialist agents",
    version="2.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include personas router
app.include_router(personas_router, prefix="/api", tags=["personas"])

# Initialize Langfuse
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
)

print("[LANGFUSE] Initialized with config:")
print(f"  - Base URL: {os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')}")
print(f"  - Secret Key: {'Set' if os.getenv('LANGFUSE_SECRET_KEY') else 'NOT SET'}")
print(f"  - Public Key: {'Set' if os.getenv('LANGFUSE_PUBLIC_KEY') else 'NOT SET'}")


# Request/Response Models
class Message(BaseModel):
    """Chat message."""

    role: str  # "user" or "assistant"
    content: str | List[Dict[str, Any]]  # String or multimodal content


class ChatRequest(BaseModel):
    """Request body for /api/chat endpoint."""

    messages: List[Message]
    session_id: Optional[str] = None
    user_id: Optional[str] = "demo-user"
    model: Optional[str] = "claude-sonnet-4-20250514"
    max_tokens: Optional[int] = 1024
    system: Optional[str] = None  # Allow system override for testing
    persona_id: Optional[str] = None  # Demo persona ID for demo mode


class ChatResponse(BaseModel):
    """Response body for /api/chat endpoint."""

    content: List[Dict[str, str]]
    model: str
    id: str
    type: str = "message"
    role: str = "assistant"
    stop_reason: Optional[str] = None
    usage: Dict[str, int]


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Business Partner AI (Python/LangGraph) is running", "version": "2.0.0"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - compatible with existing frontend.

    Processes messages through LangGraph multi-agent workflow with Langfuse tracing.
    """
    start_time = time.time()

    # Generate session ID if not provided
    session_id = request.session_id or f"session-{int(time.time())}"
    user_id = request.user_id or "demo-user"

    # Create Langfuse trace for this conversation turn
    # Include state information in metadata for debugging
    trace_metadata = {
        "model": request.model, 
        "architecture": "langgraph-multi-agent", 
        "timestamp": time.time(),
        "session_id": session_id,
    }
    
    # Add existing state info to metadata if available (for debugging state persistence)
    if existing_state:
        trace_metadata["existing_state"] = {
            "business_type": existing_state.get("business_type"),
            "location": existing_state.get("location"),
            "years_operating": existing_state.get("years_operating"),
            "num_employees": existing_state.get("num_employees"),
            "monthly_revenue": existing_state.get("monthly_revenue"),
            "monthly_expenses": existing_state.get("monthly_expenses"),
            "loan_purpose": existing_state.get("loan_purpose"),
        }
        print(f"[LANGFUSE] Trace metadata includes existing_state: {trace_metadata['existing_state']}")
    
    trace = langfuse.trace(
        name="business-partner-conversation",
        session_id=session_id,
        user_id=user_id,
        input=[msg.model_dump() for msg in request.messages],
        metadata=trace_metadata,
    )

    try:
        # Get or create conversation in database
        conversation = await get_or_create_conversation(user_id, session_id)
        
        # Extract conversation ID safely
        conversation_id = conversation.get('id')
        if not conversation_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to create or retrieve conversation ID from database"
            )
        # Convert request messages to LangChain format
        langchain_messages = []
        for msg in request.messages:
            if msg.role == "user":
                # Handle multimodal content (text + images)
                if isinstance(msg.content, list):
                    langchain_messages.append(HumanMessage(content=msg.content))
                else:
                    langchain_messages.append(HumanMessage(content=msg.content))
            # Note: We don't add assistant messages to input, they're in state history

        # Build config for LangGraph checkpointing
        config = {"configurable": {"thread_id": session_id}}
        
        # Try to get existing state from checkpoint (for continuing conversations)
        existing_state = None
        try:
            # Get the current state from the checkpoint
            state_snapshot = graph.get_state(config)
            if state_snapshot and state_snapshot.values:
                existing_state = state_snapshot.values
                print(f"[STATE] Loaded existing state from checkpoint for session {session_id}")
        except Exception as e:
            print(f"[STATE] No existing checkpoint found (new session): {e}")
        
        # Required tasks for onboarding phase
        required_tasks = [
            "confirm_eligibility",
            "capture_business_profile",
            "capture_business_financials",
            "capture_business_photos",
            "photo_analysis_complete"
        ]

        # Build initial state - merge with existing state if available
        if existing_state:
            # Continue existing conversation - merge messages properly
            # LangGraph's add_messages reducer will handle merging, but we need to include existing messages
            existing_messages = existing_state.get("messages", [])
            # Combine existing messages with new user message
            combined_messages = existing_messages + langchain_messages[-1:]
            
            # CRITICAL: Explicitly preserve ALL business fields from existing state
            # Don't rely on **existing_state spread alone - explicitly set each field
            initial_state: BusinessPartnerState = {
                **existing_state,  # Keep all existing state
                "messages": combined_messages,  # Include full conversation history + new message
                "conversation_id": conversation_id,  # Update conversation_id if changed
                "system_prompt": request.system if request.system else existing_state.get("system_prompt"),
                # Explicitly preserve business fields to ensure they persist
                "business_type": existing_state.get("business_type"),
                "location": existing_state.get("location"),
                "years_operating": existing_state.get("years_operating"),
                "num_employees": existing_state.get("num_employees"),
                "monthly_revenue": existing_state.get("monthly_revenue"),
                "monthly_expenses": existing_state.get("monthly_expenses"),
                "loan_purpose": existing_state.get("loan_purpose"),
                "business_name": existing_state.get("business_name"),
                "photos": existing_state.get("photos", []),
                "photo_insights": existing_state.get("photo_insights", []),
                "phase": existing_state.get("phase", "onboarding"),
                "completed_tasks": existing_state.get("completed_tasks", []),
            }
            print(f"[STATE] Continuing conversation - preserving existing business data")
            print(f"[STATE] Existing messages: {len(existing_messages)}, Adding: {len(langchain_messages[-1:])}")
            print(f"[STATE] Business type: {existing_state.get('business_type')}, Location: {existing_state.get('location')}")
            print(f"[STATE] Years: {existing_state.get('years_operating')}, Employees: {existing_state.get('num_employees')}")
            print(f"[STATE] Revenue: {existing_state.get('monthly_revenue')}, Expenses: {existing_state.get('monthly_expenses')}")
            print(f"[STATE] Loan purpose: {existing_state.get('loan_purpose')}")
        else:
            # New session - initialize fresh state
            initial_state: BusinessPartnerState = {
                "messages": langchain_messages[-1:],  # Only the latest user message
                "session_id": session_id,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "business_name": None,
                "business_type": None,
                "location": None,
                "years_operating": None,
                "monthly_revenue": None,
                "monthly_expenses": None,
                "num_employees": None,
                "loan_purpose": None,
                "photos": [],
                "photo_insights": [],
                "risk_score": None,
                "risk_tier": None,
                "key_risk_factors": [],
                "key_strengths": [],
                "loan_offer": None,
                "phase": "onboarding",  # Start in onboarding phase
                "onboarding_stage": "info_gathering",
                "info_complete": False,
                "photos_received": False,
                "loan_offered": False,
                "loan_accepted": False,
                "required_tasks": required_tasks,
                "completed_tasks": [],
                "next_agent": None,
                "system_prompt": request.system,  # Allow override for testing
                # Servicing fields (initialize as None)
                "servicing_type": None,
                "disbursement_status": None,
                "disbursement_info": None,
                "repayment_status": None,
                "repayment_info": None,
                "repayment_method": None,
                "payment_schedule": None,
                "repayment_impact_explanation": None,
                "recovery_status": None,
                "recovery_info": None,
                "recovery_response": None,
                "bank_account": None,
                "persona_id": None,
                "coaching_advice": None,
            }
            
            # If persona_id is provided, initialize state from persona (demo mode)
            if request.persona_id:
                persona = get_persona(request.persona_id)
                if persona:
                    initial_state = initialize_state_from_persona(initial_state, persona)
                    print(f"[DEMO] Initialized session with persona: {persona.name} ({persona.persona_id})")
                else:
                    print(f"[DEMO] Warning: Unknown persona_id: {request.persona_id}")

        # Invoke the graph
        result = graph.invoke(initial_state, config=config)

        # Save messages to database
        await save_messages(conversation_id, result["messages"])

        # Extract the assistant's response
        assistant_message = result["messages"][-1]
        response_text = assistant_message.content

        # Build response in Anthropic API format (for frontend compatibility)
        end_time = time.time()

        # Mock usage (in production, track actual token usage)
        usage = {"input_tokens": len(str(request.messages)) // 4, "output_tokens": len(response_text) // 4}

        response = ChatResponse(
            content=[{"type": "text", "text": response_text}],
            model=request.model,
            id=f"msg_{session_id}_{int(time.time())}",
            role="assistant",
            stop_reason="end_turn",
            usage={
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            },
        )

        # Update Langfuse trace with output and state information for debugging
        result_metadata = {
            "latency_ms": int((end_time - start_time) * 1000),
            "agents_called": _extract_agents_called(result),
            # Add state information for debugging
            "result_state": {
                "business_type": result.get("business_type"),
                "location": result.get("location"),
                "years_operating": result.get("years_operating"),
                "num_employees": result.get("num_employees"),
                "monthly_revenue": result.get("monthly_revenue"),
                "monthly_expenses": result.get("monthly_expenses"),
                "loan_purpose": result.get("loan_purpose"),
            },
        }
        trace.update(output=response.model_dump(), metadata=result_metadata)
        print(f"[LANGFUSE] Trace updated with result_state: {result_metadata['result_state']}")

        # Flush Langfuse
        langfuse.flush()

        return response

    except Exception as e:
        # Log error to Langfuse
        trace.update(level="ERROR", output={"error": str(e)})
        langfuse.flush()

        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


def _extract_agents_called(result: Dict) -> List[str]:
    """Extract which specialist agents were called from the result state."""
    agents_called = ["business_partner"]  # Always called

    if result.get("photo_insights"):
        agents_called.append("vision")
    if result.get("loan_offer"):
        agents_called.append("underwriting")
    if result.get("loan_accepted"):
        agents_called.append("coaching")

    return agents_called
handler = app

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    print(f"\n🚀 Starting Business Partner AI (Python/LangGraph)")
    print(f"📍 Server: http://localhost:{port}")
    print(f"🏥 Health: http://localhost:{port}/health")
    print(f"💬 Chat API: http://localhost:{port}/api/chat")
    print("\n")

    uvicorn.run(app, host="0.0.0.0", port=port)
