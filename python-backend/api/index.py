"""
Vercel-optimized serverless handler for Business Partner AI
"""

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from langchain_core.messages import HumanMessage
import time

# Import the existing app components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from state import BusinessPartnerState
from graph import graph
from main import langfuse, ChatRequest, ChatResponse, _extract_agents_called

# Create FastAPI app
app = FastAPI(
    title="Business Partner AI - Multi-Agent Demo",
    description="LangGraph-powered lending assistant with specialist agents",
    version="2.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Business Partner AI (Python/LangGraph) is running", "version": "2.0.0"}

@app.get("/api")
def api_root():
    """API root endpoint."""
    return {"message": "Business Partner AI API", "version": "2.0.0"}

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Business Partner AI (Python/LangGraph) is running", "version": "2.0.0"}

@app.post("/api/chat")
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

        # Build initial state
        config = {"configurable": {"thread_id": session_id}}

        initial_state: BusinessPartnerState = {
            "messages": langchain_messages[-1:],  # Only the latest user message
            "session_id": session_id,
            "user_id": user_id,
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
            "system_prompt": request.system,
        }

        # Invoke the graph
        result = graph.invoke(initial_state, config=config)

        # Extract the assistant's response
        assistant_message = result["messages"][-1]
        response_text = assistant_message.content

        # Build response in Anthropic API format
        end_time = time.time()

        # Mock usage
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

# Export handler for Vercel
handler = app
