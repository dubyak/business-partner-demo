"""
State schema for the Business Partner LangGraph application.

This defines the shared state that flows through all agents in the graph.
"""

from typing import Annotated, Optional, TypedDict, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class PhotoInsight(TypedDict):
    """Structure for photo analysis results."""
    photo_index: int
    cleanliness_score: float  # 0-10
    organization_score: float  # 0-10
    stock_level: str  # "low", "medium", "high"
    insights: List[str]  # Observations
    coaching_tips: List[str]  # Actionable advice


class LoanOffer(TypedDict):
    """Structure for loan offer details."""
    amount: float  # in pesos
    term_days: int
    installments: int
    installment_amount: float
    total_repayment: float
    interest_rate_flat: float  # as percentage
    terms_url: str


class BusinessPartnerState(TypedDict):
    """
    Main state for the Business Partner conversation flow.

    This state is shared across all agents and maintains the full
    context of the customer interaction.
    """

    # Conversation history - automatically managed by add_messages
    messages: Annotated[List[BaseMessage], add_messages]

    # Session tracking
    session_id: str
    user_id: str
    conversation_id: Optional[str]

    # Business information collected during onboarding
    business_name: Optional[str]
    business_type: Optional[str]
    location: Optional[str]
    years_operating: Optional[int]
    monthly_revenue: Optional[float]
    monthly_expenses: Optional[float]
    num_employees: Optional[int]
    loan_purpose: Optional[str]

    # Photos and analysis
    photos: List[str]  # base64 encoded images
    photo_insights: List[PhotoInsight]  # Results from Vision Agent

    # Underwriting results
    risk_score: Optional[float]  # 0-100, higher is better
    loan_offer: Optional[LoanOffer]

    # Progress tracking
    onboarding_stage: str  # "greeting", "info_gathering", "photo_analysis", "underwriting", "coaching", "servicing"
    info_complete: bool
    photos_received: bool
    loan_offered: bool
    loan_accepted: bool

    # Servicing-related fields
    servicing_type: Optional[str]  # "disbursement", "repayment", "payment_schedule", "repayment_impact", "recovery", "general"
    disbursement_status: Optional[str]  # "pending", "initiated", "completed", "failed", "error"
    disbursement_info: Optional[dict]  # Disbursement details (amount, bank account, reference, dates)
    repayment_status: Optional[str]  # "pending", "processing", "completed", "failed", "error"
    repayment_info: Optional[dict]  # Repayment details (method, amount, reference, dates)
    repayment_method: Optional[str]  # "existing_bank", "new_account", "in_person"
    payment_schedule: Optional[dict]  # Payment schedule with installments and due dates
    repayment_impact_explanation: Optional[str]  # Explanation of repayment behavior impact
    recovery_status: Optional[str]  # "initial", "in_conversation", "resolution_pending", "resolved", "escalated"
    recovery_info: Optional[dict]  # Recovery conversation details
    recovery_response: Optional[str]  # Response from recovery conversation
    bank_account: Optional[str]  # User's bank account info (masked)

    # Agent routing
    next_agent: Optional[str]  # Which specialist agent to call next, if any

    # System prompt (fetched from Langfuse)
    system_prompt: Optional[str]
