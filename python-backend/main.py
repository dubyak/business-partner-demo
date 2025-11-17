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

    # Get or create conversation in database
    conversation = await get_or_create_conversation(user_id, session_id)
    
    # Extract conversation ID safely
    conversation_id = conversation.get('id')
    if not conversation_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to create or retrieve conversation ID from database"
        )

    # Create Langfuse trace for this conversation turn
    trace = langfuse.trace(
        name="business-partner-conversation",
        session_id=session_id,
        user_id=user_id,
        input=[msg.model_dump() for msg in request.messages],
        metadata={"model": request.model, "architecture": "langgraph-multi-agent", "timestamp": time.time()},
    )

    try:
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

        # Build initial state
        config = {"configurable": {"thread_id": session_id}}

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
            "loan_offer": None,
            "onboarding_stage": "info_gathering",
            "info_complete": False,
            "photos_received": False,
            "loan_offered": False,
            "loan_accepted": False,
            "next_agent": None,
            "system_prompt": request.system,  # Allow override for testing
        }

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

        # Update Langfuse trace with output
        trace.update(output=response.model_dump(), metadata={"latency_ms": int((end_time - start_time) * 1000), "agents_called": _extract_agents_called(result)})

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
    agents_called = ["conversation"]  # Always called

    if result.get("photo_insights"):
        agents_called.append("vision")
    if result.get("loan_offer"):
        agents_called.append("underwriting")
    if result.get("loan_accepted"):
        agents_called.append("coaching")

    return agents_called


# Vercel serverless handler
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
