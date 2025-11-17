"""
Database operations for Supabase integration.

This module provides helper functions for persisting conversation state
to Supabase during the agent workflow.
"""

import os
from typing import List, Dict, Optional
from supabase import create_client, Client
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables"
    )

supabase: Client = create_client(supabase_url, supabase_key)


async def get_or_create_conversation(user_id: str, session_id: str) -> Dict:
    """
    Get existing conversation or create a new one.
    
    Args:
        user_id: The authenticated user's ID
        session_id: The session identifier from the client
        
    Returns:
        Dict containing conversation record with 'id', 'user_id', 'session_id'
    """
    try:
        # Try to find existing conversation
        response = supabase.table("conversations").select("*").eq(
            "user_id", user_id
        ).eq("session_id", session_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"[DB] Found existing conversation: {response.data[0]['id']}")
            return response.data[0]
        
        # Create new conversation
        print(f"[DB] Creating new conversation for user {user_id}, session {session_id}")
        response = supabase.table("conversations").insert({
            "user_id": user_id,
            "session_id": session_id,
            "title": "Loan Inquiry"  # Can be updated later with first message
        }).execute()
        
        print(f"[DB] ✓ Created conversation: {response.data[0]['id']}")
        return response.data[0]
        
    except Exception as e:
        print(f"[DB] ✗ Error in get_or_create_conversation: {e}")
        raise


async def save_messages(conversation_id: str, messages: List[BaseMessage], last_saved_count: int = 0) -> int:
    """
    Save new messages to the database.
    
    Args:
        conversation_id: The conversation UUID
        messages: List of LangChain messages
        last_saved_count: Number of messages previously saved (to avoid duplicates)
        
    Returns:
        Total number of messages now saved
    """
    try:
        # Only save messages that haven't been saved yet
        new_messages = messages[last_saved_count:]
        
        if not new_messages:
            print(f"[DB] No new messages to save")
            return last_saved_count
        
        print(f"[DB] Saving {len(new_messages)} new messages to conversation {conversation_id}")
        
        for msg in new_messages:
            # Determine role
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                role = "system"
            
            # Extract content (handle both string and list content)
            if isinstance(msg.content, str):
                content = {"text": msg.content}
            elif isinstance(msg.content, list):
                # Handle multi-part content (text + images)
                content = {"parts": msg.content}
            else:
                content = {"text": str(msg.content)}
            
            # Insert message
            supabase.table("messages").insert({
                "conversation_id": conversation_id,
                "role": role,
                "content": content
            }).execute()
        
        new_count = len(messages)
        print(f"[DB] ✓ Saved {len(new_messages)} messages (total: {new_count})")
        return new_count
        
    except Exception as e:
        print(f"[DB] ✗ Error in save_messages: {e}")
        raise


async def save_loan_application(conversation_id: str, state: Dict) -> Optional[Dict]:
    """
    Save loan application after underwriting agent generates offer.
    
    Args:
        conversation_id: The conversation UUID
        state: The BusinessPartnerState dictionary
        
    Returns:
        Dict containing the saved loan application record
    """
    try:
        loan_offer = state.get('loan_offer')
        if not loan_offer:
            print(f"[DB] No loan offer in state, skipping save")
            return None
        
        print(f"[DB] Saving loan application for conversation {conversation_id}")
        
        response = supabase.table("loan_applications").insert({
            "user_id": state['user_id'],
            "conversation_id": conversation_id,
            "loan_purpose": state.get('loan_purpose'),
            "risk_score": state.get('risk_score'),
            "loan_amount": loan_offer.get('amount'),
            "term_days": loan_offer.get('term_days'),
            "interest_rate": loan_offer.get('interest_rate_flat'),
            "status": "offered",
            "offer_details": loan_offer  # Store full offer as JSONB
        }).execute()
        
        print(f"[DB] ✓ Saved loan application: {response.data[0]['id']}")
        return response.data[0]
        
    except Exception as e:
        print(f"[DB] ✗ Error in save_loan_application: {e}")
        raise


async def update_loan_status(conversation_id: str, status: str) -> bool:
    """
    Update loan application status (e.g., when user accepts).
    
    Args:
        conversation_id: The conversation UUID
        status: New status ('accepted', 'rejected', 'under_review', etc.)
        
    Returns:
        True if update successful
    """
    try:
        print(f"[DB] Updating loan status to '{status}' for conversation {conversation_id}")
        
        response = supabase.table("loan_applications").update({
            "status": status
        }).eq("conversation_id", conversation_id).eq("status", "offered").execute()
        
        if response.data:
            print(f"[DB] ✓ Updated loan status to '{status}'")
            return True
        else:
            print(f"[DB] No loan application found to update")
            return False
        
    except Exception as e:
        print(f"[DB] ✗ Error in update_loan_status: {e}")
        raise


async def get_conversation_history(conversation_id: str) -> List[Dict]:
    """
    Retrieve all messages for a conversation (for resuming sessions).
    
    Args:
        conversation_id: The conversation UUID
        
    Returns:
        List of message dictionaries
    """
    try:
        print(f"[DB] Fetching conversation history for {conversation_id}")
        
        response = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at", desc=False).execute()
        
        print(f"[DB] ✓ Retrieved {len(response.data)} messages")
        return response.data
        
    except Exception as e:
        print(f"[DB] ✗ Error in get_conversation_history: {e}")
        raise


# Optional: Phase 2 functions (implement later)

async def save_business_profile(state: Dict) -> Optional[Dict]:
    """
    Save business profile when info gathering is complete.
    
    PHASE 2: Implement this when you need historical data for better underwriting.
    """
    try:
        print(f"[DB] Saving business profile for user {state['user_id']}")
        
        response = supabase.table("business_profiles").insert({
            "user_id": state['user_id'],
            "business_name": state.get('business_name'),
            "business_type": state.get('business_type'),
            "location": state.get('location'),
            "years_operating": state.get('years_operating'),
            "monthly_revenue": state.get('monthly_revenue'),
            "monthly_expenses": state.get('monthly_expenses'),
            "num_employees": state.get('num_employees'),
            "description": state.get('loan_purpose')
        }).execute()
        
        print(f"[DB] ✓ Saved business profile: {response.data[0]['id']}")
        return response.data[0]
        
    except Exception as e:
        print(f"[DB] ✗ Error in save_business_profile: {e}")
        raise


async def save_photo_analysis(conversation_id: str, state: Dict) -> List[Dict]:
    """
    Save photo analysis results from vision agent.
    
    PHASE 3: Implement this if you need photo quality analytics.
    Currently, photo insights are already saved in messages.
    """
    try:
        photo_insights = state.get('photo_insights', [])
        photos = state.get('photos', [])
        
        if not photo_insights:
            return []
        
        print(f"[DB] Saving {len(photo_insights)} photo analyses")
        
        saved = []
        for i, insight in enumerate(photo_insights):
            response = supabase.table("photo_analyses").insert({
                "user_id": state['user_id'],
                "conversation_id": conversation_id,
                "photo_data": photos[i] if i < len(photos) else None,
                "cleanliness_score": insight.get('cleanliness_score'),
                "organization_score": insight.get('organization_score'),
                "stock_level": insight.get('stock_level'),
                "insights": insight.get('insights'),
                "coaching_tips": insight.get('coaching_tips')
            }).execute()
            
            saved.append(response.data[0])
        
        print(f"[DB] ✓ Saved {len(saved)} photo analyses")
        return saved
        
    except Exception as e:
        print(f"[DB] ✗ Error in save_photo_analysis: {e}")
        raise

