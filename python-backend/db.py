"""
Database operations for Supabase integration.

This module provides helper functions for persisting conversation state
to Supabase during the agent workflow.
"""

import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime
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


def _ensure_uuid(user_id: str) -> str:
    """
    Convert user_id to UUID format for database compatibility.
    For demo purposes, generates a consistent UUID from the user_id string.
    """
    try:
        # Try to parse as UUID first
        uuid.UUID(user_id)
        return user_id
    except (ValueError, TypeError):
        # Generate a consistent UUID from the string using namespace UUID
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        return str(uuid.uuid5(namespace, user_id))


def _ensure_user_exists(user_uuid: str) -> None:
    """
    Ensure a user exists in auth.users table for demo purposes.
    Uses service role key to bypass RLS and create user if needed.
    """
    try:
        # Try to check if user exists
        # Note: We can't directly query auth.users via Supabase client easily
        # Instead, we'll try to insert and catch the error, or use a workaround
        # For now, we'll use a PostgreSQL function approach via RPC if available
        # But the simplest is to just try the insert and let the FK constraint fail gracefully
        # Actually, we can use the service role to insert into auth.users directly
        pass  # Will handle in the calling function
    except Exception:
        pass  # If user creation fails, the FK constraint will catch it


async def get_or_create_conversation(user_id: str, session_id: str) -> Dict:
    """
    Get existing conversation or create a new one.
    
    Args:
        user_id: The authenticated user's ID (will be converted to UUID if needed)
        session_id: The session identifier from the client
        
    Returns:
        Dict containing conversation record with 'id', 'user_id', 'session_id'
    """
    try:
        # Convert user_id to UUID format for database
        user_uuid = _ensure_uuid(user_id)
        
        # For demo: ensure user exists in auth.users (create if needed)
        try:
            # Call the create_demo_user function to ensure user exists
            supabase.rpc('create_demo_user', {'user_uuid': user_uuid}).execute()
            print(f"[DB] ✓ Ensured demo user exists: {user_uuid}")
        except Exception as e:
            # If RPC fails, log but continue - might already exist or function not deployed
            error_msg = str(e).lower()
            if 'already exists' not in error_msg and 'duplicate' not in error_msg:
                print(f"[DB] Note: Could not ensure user exists (may need migration): {e}")
        
        # Try to find existing conversation
        response = supabase.table("conversations").select("*").eq(
            "user_id", user_uuid
        ).eq("session_id", session_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"[DB] Found existing conversation: {response.data[0]['id']}")
            return response.data[0]
        
        # Create new conversation
        print(f"[DB] Creating new conversation for user {user_uuid}, session {session_id}")
        response = supabase.table("conversations").insert({
            "user_id": user_uuid,
            "session_id": session_id,
            "title": "Loan Inquiry"  # Can be updated later with first message
        }).execute()
        
        print(f"[DB] ✓ Created conversation: {response.data[0]['id']}")
        return response.data[0]
        
    except Exception as e:
        error_msg = str(e)
        print(f"[DB] ✗ Error in get_or_create_conversation: {error_msg}")
        
        # Provide more helpful error messages for common issues
        if "Invalid API key" in error_msg or "401" in error_msg:
            raise ValueError(
                "Supabase authentication failed. Please check that SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY are correctly set in your environment variables. "
                f"Error details: {error_msg}"
            )
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
        
        user_uuid = _ensure_uuid(state['user_id'])
        response = supabase.table("loan_applications").insert({
            "user_id": user_uuid,
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
        
        user_uuid = _ensure_uuid(state['user_id'])
        response = supabase.table("business_profiles").insert({
            "user_id": user_uuid,
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
        user_uuid = _ensure_uuid(state['user_id'])
        for i, insight in enumerate(photo_insights):
            response = supabase.table("photo_analyses").insert({
                "user_id": user_uuid,
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


# =====================================================
# SERVICING-RELATED DATABASE FUNCTIONS
# =====================================================

async def create_loan_from_application(conversation_id: str, state: Dict) -> Optional[Dict]:
    """
    Create an active loan record after loan acceptance.
    
    Args:
        conversation_id: The conversation UUID
        state: The BusinessPartnerState dictionary
        
    Returns:
        Dict containing the created loan record
    """
    try:
        loan_offer = state.get('loan_offer')
        if not loan_offer:
            print(f"[DB] No loan offer in state, cannot create loan")
            return None
        
        # Find the loan application
        app_response = supabase.table("loan_applications").select("id").eq(
            "conversation_id", conversation_id
        ).eq("status", "accepted").execute()
        
        if not app_response.data:
            print(f"[DB] No accepted loan application found for conversation {conversation_id}")
            return None
        
        loan_application_id = app_response.data[0]['id']
        
        print(f"[DB] Creating loan from application {loan_application_id}")
        
        user_uuid = _ensure_uuid(state['user_id'])
        response = supabase.table("loans").insert({
            "user_id": user_uuid,
            "loan_application_id": loan_application_id,
            "conversation_id": conversation_id,
            "loan_amount": loan_offer.get('amount'),
            "term_days": loan_offer.get('term_days'),
            "installments": loan_offer.get('installments'),
            "installment_amount": loan_offer.get('installment_amount'),
            "total_repayment": loan_offer.get('total_repayment'),
            "interest_rate": loan_offer.get('interest_rate_flat'),
            "status": "active"
        }).execute()
        
        print(f"[DB] ✓ Created loan: {response.data[0]['id']}")
        return response.data[0]
        
    except Exception as e:
        print(f"[DB] ✗ Error in create_loan_from_application: {e}")
        raise


async def save_disbursement(loan_id: str, disbursement_info: Dict) -> Optional[Dict]:
    """
    Save disbursement record.
    
    Args:
        loan_id: The loan UUID
        disbursement_info: Disbursement details from state
        
    Returns:
        Dict containing the saved disbursement record
    """
    try:
        print(f"[DB] Saving disbursement for loan {loan_id}")
        
        user_id = disbursement_info.get('user_id')
        user_uuid = _ensure_uuid(user_id) if user_id else None
        response = supabase.table("disbursements").insert({
            "loan_id": loan_id,
            "user_id": user_uuid,
            "amount": disbursement_info.get('amount'),
            "bank_account": disbursement_info.get('bank_account'),
            "status": disbursement_info.get('status', 'initiated'),
            "reference_number": disbursement_info.get('reference_number'),
            "initiated_at": disbursement_info.get('initiated_at'),
            "estimated_completion": disbursement_info.get('estimated_completion'),
            "metadata": disbursement_info  # Store full info as JSONB
        }).execute()
        
        print(f"[DB] ✓ Saved disbursement: {response.data[0]['id']}")
        return response.data[0]
        
    except Exception as e:
        print(f"[DB] ✗ Error in save_disbursement: {e}")
        raise


async def save_repayment(loan_id: str, repayment_info: Dict) -> Optional[Dict]:
    """
    Save repayment record.
    
    Args:
        loan_id: The loan UUID
        repayment_info: Repayment details from state
        
    Returns:
        Dict containing the saved repayment record
    """
    try:
        print(f"[DB] Saving repayment for loan {loan_id}")
        
        # Calculate due date from payment schedule if available
        due_date = repayment_info.get('due_date')
        if not due_date:
            # Default to 15 days from now (would be calculated from schedule in production)
            from datetime import datetime, timedelta
            due_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
        response = supabase.table("repayments").insert({
            "loan_id": loan_id,
            "user_id": _ensure_uuid(repayment_info.get('user_id')) if repayment_info.get('user_id') else None,
            "installment_number": repayment_info.get('installment_number', 1),
            "amount": repayment_info.get('amount'),
            "method": repayment_info.get('method'),
            "bank_account": repayment_info.get('bank_account'),
            "status": repayment_info.get('status', 'processing'),
            "reference_number": repayment_info.get('reference_number'),
            "due_date": due_date,
            "initiated_at": repayment_info.get('initiated_at'),
            "estimated_completion": repayment_info.get('estimated_completion'),
            "metadata": repayment_info  # Store full info as JSONB
        }).execute()
        
        print(f"[DB] ✓ Saved repayment: {response.data[0]['id']}")
        return response.data[0]
        
    except Exception as e:
        print(f"[DB] ✗ Error in save_repayment: {e}")
        raise


async def get_or_create_recovery_conversation(loan_id: str, user_id: str, conversation_id: str, outstanding_balance: float) -> Dict:
    """
    Get existing recovery conversation or create a new one.
    
    Args:
        loan_id: The loan UUID
        user_id: The user UUID
        conversation_id: The conversation UUID
        outstanding_balance: Current outstanding balance
        
    Returns:
        Dict containing the recovery conversation record
    """
    try:
        # Try to find existing active recovery conversation
        response = supabase.table("recovery_conversations").select("*").eq(
            "loan_id", loan_id
        ).in_("status", ["initial", "in_conversation", "resolution_pending"]).execute()
        
        if response.data and len(response.data) > 0:
            # Update last interaction time
            recovery_id = response.data[0]['id']
            supabase.table("recovery_conversations").update({
                "last_interaction_at": datetime.now().isoformat(),
                "outstanding_balance": outstanding_balance
            }).eq("id", recovery_id).execute()
            
            print(f"[DB] Found existing recovery conversation: {recovery_id}")
            return response.data[0]
        
        # Create new recovery conversation
        print(f"[DB] Creating new recovery conversation for loan {loan_id}")
        user_uuid = _ensure_uuid(user_id)
        response = supabase.table("recovery_conversations").insert({
            "loan_id": loan_id,
            "user_id": user_uuid,
            "conversation_id": conversation_id,
            "status": "initial",
            "outstanding_balance": outstanding_balance
        }).execute()
        
        print(f"[DB] ✓ Created recovery conversation: {response.data[0]['id']}")
        return response.data[0]
        
    except Exception as e:
        print(f"[DB] ✗ Error in get_or_create_recovery_conversation: {e}")
        raise


async def update_recovery_conversation(recovery_id: str, status: str, resolution_type: Optional[str] = None, resolution_details: Optional[Dict] = None) -> bool:
    """
    Update recovery conversation status and resolution details.
    
    Args:
        recovery_id: The recovery conversation UUID
        status: New status
        resolution_type: Type of resolution (if resolved)
        resolution_details: Details of the resolution
        
    Returns:
        True if update successful
    """
    try:
        print(f"[DB] Updating recovery conversation {recovery_id} to status '{status}'")
        
        update_data = {
            "status": status,
            "last_interaction_at": datetime.now().isoformat()
        }
        
        if resolution_type:
            update_data["resolution_type"] = resolution_type
        
        if resolution_details:
            update_data["resolution_details"] = resolution_details
        
        if status == "resolved":
            update_data["resolved_at"] = datetime.now().isoformat()
        elif status == "escalated":
            update_data["escalated_at"] = datetime.now().isoformat()
        
        response = supabase.table("recovery_conversations").update(update_data).eq(
            "id", recovery_id
        ).execute()
        
        if response.data:
            print(f"[DB] ✓ Updated recovery conversation to '{status}'")
            return True
        else:
            print(f"[DB] No recovery conversation found to update")
            return False
        
    except Exception as e:
        print(f"[DB] ✗ Error in update_recovery_conversation: {e}")
        raise

