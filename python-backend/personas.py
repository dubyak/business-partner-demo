"""
Demo Personas Configuration

Predefined personas for demo mode that represent different stages of the loan lifecycle.
Each persona pre-populates state with realistic business data and loan context.
"""

from typing import Dict, Any, Literal
from state import BusinessPartnerState, LoanOffer

# Phase type
Phase = Literal["onboarding", "offer", "post_disbursement", "delinquent"]

# Persona definition structure
class Persona:
    """Definition of a demo persona."""
    
    def __init__(
        self,
        persona_id: str,
        name: str,
        description: str,
        phase: Phase,
        business_data: Dict[str, Any],
        loan_context: Dict[str, Any],
        completed_tasks: list[str],
        suggested_first_message: str,
    ):
        self.persona_id = persona_id
        self.name = name
        self.description = description
        self.phase = phase
        self.business_data = business_data
        self.loan_context = loan_context
        self.completed_tasks = completed_tasks
        self.suggested_first_message = suggested_first_message


# Define personas
PERSONAS: Dict[str, Persona] = {
    "pre_loan_tienda": Persona(
        persona_id="pre_loan_tienda",
        name="Pre-Loan Tienda Owner",
        description="Corner shop owner exploring loan options for inventory expansion",
        phase="onboarding",
        business_data={
            "business_type": "corner shop / tiendita",
            "location": "Mexico City, CDMX",
            "years_operating": 3,
            "num_employees": 1,
            "monthly_revenue": 25000.0,
            "monthly_expenses": 18000.0,
            "loan_purpose": "Buy more inventory for the holiday season",
        },
        loan_context={
            "loan_offer": None,
            "loan_accepted": False,
            "loan_offered": False,
            "days_past_due": None,
            "recovery_status": None,
        },
        completed_tasks=[],  # Start fresh in onboarding
        suggested_first_message="Hola, I'm interested in getting a loan for my tiendita. Can you help me?",
    ),
    
    "active_loan_salon": Persona(
        persona_id="active_loan_salon",
        name="Active Loan Beauty Salon",
        description="Beauty salon with an active loan and payment schedule",
        phase="post_disbursement",
        business_data={
            "business_type": "beauty salon",
            "location": "Guadalajara, Jalisco",
            "years_operating": 5,
            "num_employees": 3,
            "monthly_revenue": 45000.0,
            "monthly_expenses": 30000.0,
            "loan_purpose": "Equipment upgrade and renovation",
        },
        loan_context={
            "loan_offer": {
                "amount": 5000.0,
                "term_days": 45,
                "installments": 3,
                "installment_amount": 1850.0,
                "total_repayment": 5550.0,
                "interest_rate_flat": 11.0,
                "terms_url": "https://lender.com.mx/terms/msme-loan-agreement",
            },
            "loan_accepted": True,
            "loan_offered": True,
            "disbursement_status": "completed",
            "days_past_due": 0,
            "recovery_status": None,
            "payment_schedule": {
                "total_installments": 3,
                "installment_amount": 1850.0,
                "total_amount": 5550.0,
                "schedule": [
                    {"installment_number": 1, "due_date": "2024-12-15", "amount": 1850.0, "status": "completed"},
                    {"installment_number": 2, "due_date": "2024-12-30", "amount": 1850.0, "status": "pending"},
                    {"installment_number": 3, "due_date": "2025-01-14", "amount": 1850.0, "status": "pending"},
                ],
                "days_between_payments": 15,
            },
        },
        completed_tasks=[
            "confirm_eligibility",
            "capture_business_profile",
            "capture_business_financials",
            "capture_business_photos",
            "photo_analysis_complete",
        ],
        suggested_first_message="Hi, I have an active loan and want to check my payment schedule.",
    ),
    
    "past_due_food_cart": Persona(
        persona_id="past_due_food_cart",
        name="Past-Due Food Cart",
        description="Street food cart with payment difficulties, needs recovery support",
        phase="delinquent",
        business_data={
            "business_type": "street food cart",
            "location": "Monterrey, Nuevo León",
            "years_operating": 2,
            "num_employees": 0,
            "monthly_revenue": 20000.0,
            "monthly_expenses": 15000.0,
            "loan_purpose": "Buy new equipment and supplies",
        },
        loan_context={
            "loan_offer": {
                "amount": 5000.0,
                "term_days": 45,
                "installments": 3,
                "installment_amount": 1850.0,
                "total_repayment": 5550.0,
                "interest_rate_flat": 11.0,
                "terms_url": "https://lender.com.mx/terms/msme-loan-agreement",
            },
            "loan_accepted": True,
            "loan_offered": True,
            "disbursement_status": "completed",
            "days_past_due": 10,
            "recovery_status": "in_conversation",
            "payment_schedule": {
                "total_installments": 3,
                "installment_amount": 1850.0,
                "total_amount": 5550.0,
                "schedule": [
                    {"installment_number": 1, "due_date": "2024-12-05", "amount": 1850.0, "status": "overdue"},
                    {"installment_number": 2, "due_date": "2024-12-20", "amount": 1850.0, "status": "pending"},
                    {"installment_number": 3, "due_date": "2025-01-04", "amount": 1850.0, "status": "pending"},
                ],
                "days_between_payments": 15,
            },
        },
        completed_tasks=[
            "confirm_eligibility",
            "capture_business_profile",
            "capture_business_financials",
            "capture_business_photos",
            "photo_analysis_complete",
        ],
        suggested_first_message="I'm having trouble making my payment. Can you help me?",
    ),
    
    "coaching_only_market": Persona(
        persona_id="coaching_only_market",
        name="Coaching-Only Market Stall",
        description="Market stall owner seeking business advice, not interested in credit",
        phase="post_disbursement",
        business_data={
            "business_type": "market stall (fruits/vegetables)",
            "location": "Puebla, Puebla",
            "years_operating": 4,
            "num_employees": 1,
            "monthly_revenue": 35000.0,
            "monthly_expenses": 25000.0,
            "loan_purpose": None,  # Not seeking a loan
        },
        loan_context={
            "loan_offer": None,
            "loan_accepted": False,
            "loan_offered": False,
            "days_past_due": None,
            "recovery_status": None,
        },
        completed_tasks=[
            "confirm_eligibility",
            "capture_business_profile",
            "capture_business_financials",
        ],
        suggested_first_message="I want to grow my business but I'm not looking for a loan. Can you give me advice?",
    ),
}


def get_persona(persona_id: str) -> Persona:
    """Get a persona by ID."""
    return PERSONAS.get(persona_id)


def list_personas() -> list[Dict[str, Any]]:
    """List all available personas with their metadata."""
    return [
        {
            "persona_id": p.persona_id,
            "name": p.name,
            "description": p.description,
            "phase": p.phase,
            "suggested_first_message": p.suggested_first_message,
        }
        for p in PERSONAS.values()
    ]


def initialize_state_from_persona(state: BusinessPartnerState, persona: Persona) -> BusinessPartnerState:
    """
    Initialize or update state with persona data.
    
    This pre-populates business data, loan context, phase, and completed tasks.
    """
    # Update business data
    for key, value in persona.business_data.items():
        if state.get(key) is None:  # Only set if not already set
            state[key] = value
    
    # Update loan context
    for key, value in persona.loan_context.items():
        if state.get(key) is None:  # Only set if not already set
            state[key] = value
    
    # Set phase
    state["phase"] = persona.phase
    
    # Set required tasks (default set for onboarding)
    if not state.get("required_tasks"):
        state["required_tasks"] = [
            "confirm_eligibility",
            "capture_business_profile",
            "capture_business_financials",
            "capture_business_photos",
            "photo_analysis_complete",
        ]
    
    # Set completed tasks from persona
    state["completed_tasks"] = persona.completed_tasks.copy()
    
    # Set persona_id in state
    state["persona_id"] = persona.persona_id
    
    return state

