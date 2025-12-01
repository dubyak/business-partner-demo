"""
Underwriting Agent - Generates loan offers based on business data and risk assessment.

This agent:
- Evaluates business information and photo insights
- Calculates risk score
- Generates appropriate loan offer
- (In production: would integrate with credit models and lending platform)
"""

import os
from typing import Dict
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
import threading

from state import BusinessPartnerState, LoanOffer, PhotoInsight

# Optional database import - only use if available
try:
    from db import save_loan_application
except (ImportError, ValueError):
    # Database not available (e.g., in eval environment)
    # Stub must be async to match the real function signature
    async def save_loan_application(*args, **kwargs):
        print("[UNDERWRITING] Database not available - skipping loan application save")
        return None


class UnderwritingAgent:
    """Agent specialized in loan underwriting and offer generation."""

    def __init__(self):
        # Initialize Langfuse for prompt management
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
        )

        # Prompt caching
        self.system_prompt = None
        self.prompt_cache_time = None
        self.prompt_ttl = 60  # seconds
        self.prompt_name = None
        self.prompt_version = None

    def get_system_prompt(self) -> str:
        """
        Fetch system prompt from Langfuse with caching.
        Falls back to default if Langfuse fetch fails.
        """
        import time

        now = time.time()

        # Return cached prompt if valid
        if self.system_prompt and self.prompt_cache_time and (now - self.prompt_cache_time < self.prompt_ttl):
            print(f"[LANGFUSE-UNDERWRITING] Using cached prompt (age: {int(now - self.prompt_cache_time)}s)")
            return self.system_prompt

        # Try to fetch from Langfuse
        try:
            prompt_name = os.getenv("LANGFUSE_UNDERWRITING_PROMPT_NAME", "underwriting-agent-system")
            print(f"[LANGFUSE-UNDERWRITING] Fetching prompt: {prompt_name}")

            prompt_obj = self.langfuse.get_prompt(prompt_name)

            if prompt_obj and hasattr(prompt_obj, "prompt"):
                self.system_prompt = prompt_obj.prompt
                self.prompt_cache_time = now
                self.prompt_name = prompt_name
                self.prompt_version = getattr(prompt_obj, "version", None)
                print(f"[LANGFUSE-UNDERWRITING] ✓ Prompt fetched successfully (v{prompt_obj.version})")
                return self.system_prompt
            else:
                print(f"[LANGFUSE-UNDERWRITING] ✗ Prompt object missing 'prompt' property")

        except Exception as e:
            print(f"[LANGFUSE-UNDERWRITING] ✗ Error fetching prompt: {e}")

        # Fallback to default prompt
        print("[LANGFUSE-UNDERWRITING] → Using fallback prompt")
        self.prompt_name = None
        self.prompt_version = None
        return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback system prompt if Langfuse is unavailable."""
        return """You are a loan underwriting specialist for a lending platform. You work in the BACKGROUND - you do NOT speak directly to customers.

YOUR ROLE:
- Evaluate business information and photo insights
- Calculate risk scores based on business profile
- Generate appropriate loan offers with terms
- Provide risk assessment details

IMPORTANT: You are a BACKGROUND SERVICE. You do NOT generate user-facing messages. You only:
- Calculate risk_score (0-100, higher is better)
- Generate loan_offer (amount, term, installments, etc.)
- Provide risk_tier ("low" | "medium" | "high")
- List key_risk_factors (short reasons)
- List key_strengths (short strengths)

The business_partner agent will read your results and craft the customer-facing response.

RISK ASSESSMENT:
Risk factors to consider:
- Years operating (more experience = lower risk)
- Monthly revenue (higher revenue = lower risk)
- Photo insights (cleanliness and organization scores)
- Loan purpose (some purposes are lower risk)

DEMO OFFER STANDARDS:
For consistency in demos, generate standard offers:
- Amount: 5,000 pesos
- Term: 45 days
- Installments: 3
- Interest rate: 11% flat
- Installment amount: ~1,850 pesos per payment
- Total repayment: 5,550 pesos

RISK TIER CALCULATION:
- risk_score >= 80: "low" risk
- risk_score >= 60: "medium" risk
- risk_score < 60: "high" risk

Generate key_risk_factors and key_strengths as short bullet points (2-3 each).

In production, you would integrate with credit models and adjust terms based on risk score."""

    @observe(name="underwriting-agent-calculate-risk")
    def calculate_risk_score(self, state: BusinessPartnerState) -> float:
        """
        Calculate a risk score based on business data and photo insights.

        In production, this would call your actual credit models.
        For demo purposes, uses simple heuristics.

        Returns:
            Risk score from 0-100 (higher is better/less risky)
        """

        score = 60.0  # Base score

        # Factor 1: Years operating (more experience = lower risk)
        years = state.get("years_operating", 0)
        if years:
            score += min(years * 2, 15)  # Up to +15 for longevity

        # Factor 2: Monthly revenue
        revenue = state.get("monthly_revenue", 0)
        if revenue:
            if revenue >= 50000:
                score += 10
            elif revenue >= 30000:
                score += 5

        # Factor 3: Photo insights (cleanliness + organization)
        photo_insights = state.get("photo_insights", [])
        if photo_insights:
            avg_cleanliness = sum(p["cleanliness_score"] for p in photo_insights) / len(photo_insights)
            avg_organization = sum(p["organization_score"] for p in photo_insights) / len(photo_insights)

            # Normalize to 0-10 scale and add up to +10 points
            score += ((avg_cleanliness + avg_organization) / 2) * 1.0

        # Factor 4: Loan purpose (some purposes are lower risk)
        loan_purpose = state.get("loan_purpose", "").lower()
        if any(keyword in loan_purpose for keyword in ["inventory", "stock", "supplies"]):
            score += 5  # Working capital for inventory is relatively safe

        # Cap at 100
        return min(score, 100.0)

    def _calculate_risk_tier(self, risk_score: float) -> str:
        """Calculate risk tier from risk score."""
        if risk_score >= 80:
            return "low"
        elif risk_score >= 60:
            return "medium"
        else:
            return "high"
    
    def _generate_risk_factors(self, risk_score: float, state: BusinessPartnerState) -> tuple[list[str], list[str]]:
        """
        Generate key risk factors and strengths based on business profile.
        
        Returns:
            (key_risk_factors, key_strengths) as lists of short descriptions
        """
        risk_factors = []
        strengths = []
        
        # Analyze years operating
        years = state.get("years_operating", 0)
        if years < 1:
            risk_factors.append("Less than 1 year in business")
        elif years >= 3:
            strengths.append(f"{years} years of business experience")
        
        # Analyze revenue
        revenue = state.get("monthly_revenue", 0)
        if revenue < 20000:
            risk_factors.append("Low monthly revenue")
        elif revenue >= 40000:
            strengths.append(f"Strong monthly revenue ({revenue:,.0f} pesos)")
        
        # Analyze photo insights
        photo_insights = state.get("photo_insights", [])
        if photo_insights:
            avg_cleanliness = sum(p.get("cleanliness_score", 7) for p in photo_insights) / len(photo_insights)
            avg_organization = sum(p.get("organization_score", 7) for p in photo_insights) / len(photo_insights)
            if avg_cleanliness >= 8 and avg_organization >= 8:
                strengths.append("Well-maintained and organized business space")
            elif avg_cleanliness < 6 or avg_organization < 6:
                risk_factors.append("Business space needs improvement")
        
        # Default if empty
        if not risk_factors:
            risk_factors.append("Standard risk profile")
        if not strengths:
            strengths.append("Eligible for loan consideration")
        
        return (risk_factors[:3], strengths[:3])  # Limit to 3 each

    @observe(name="underwriting-agent-generate-offer")
    def generate_loan_offer(self, risk_score: float, state: BusinessPartnerState) -> LoanOffer:
        """
        Generate a loan offer based on risk score and business profile.

        In production, this would use your lending platform's pricing engine.
        """

        # Demo offer structure (matching your current demo)
        base_amount = 5000.0  # pesos
        term_days = 45
        num_installments = 3
        flat_interest_rate = 11.0  # 11% flat

        # Could adjust based on risk score in production
        # For demo, keep it simple and consistent
        if risk_score >= 80:
            # High quality borrower - could offer better terms
            pass  # Keep standard for demo consistency

        total_repayment = base_amount * (1 + flat_interest_rate / 100)
        installment_amount = total_repayment / num_installments

        return LoanOffer(
            amount=base_amount,
            term_days=term_days,
            installments=num_installments,
            installment_amount=round(installment_amount, 2),
            total_repayment=round(total_repayment, 2),
            interest_rate_flat=flat_interest_rate,
            terms_url="https://lender.com.mx/terms/msme-loan-agreement",
        )

    @observe(name="underwriting-agent-process")
    def process(self, state: BusinessPartnerState) -> Dict:
        """
        Main entry point for the Underwriting Agent.

        Calculates risk and generates loan offer.
        """

        # Fetch system prompt (for consistency with other agents and tracking)
        # Note: Underwriting agent uses algorithmic logic, but prompt is available for documentation
        self.get_system_prompt()

        # Calculate risk score
        risk_score = self.calculate_risk_score(state)
        
        # Calculate risk tier
        risk_tier = self._calculate_risk_tier(risk_score)
        
        # Generate risk factors and strengths
        key_risk_factors, key_strengths = self._generate_risk_factors(risk_score, state)

        # Generate loan offer
        loan_offer = self.generate_loan_offer(risk_score, state)

        # Add Langfuse context
        metadata = {"agent": "underwriting", "demo_mode": True}
        if self.prompt_name:
            metadata["prompt_name"] = self.prompt_name
        if self.prompt_version:
            metadata["prompt_version"] = self.prompt_version

        langfuse_context.update_current_observation(
            input={
                "business_info": {
                    "business_type": state.get("business_type"),
                    "years_operating": state.get("years_operating"),
                    "monthly_revenue": state.get("monthly_revenue"),
                    "num_photos": len(state.get("photos", [])),
                }
            },
            output={"risk_score": risk_score, "loan_offer": loan_offer},
            metadata=metadata,
        )

        # Save loan application to database
        conversation_id = state.get('conversation_id')
        if conversation_id and not state.get('_loan_saved'):
            try:
                # Run async function in background thread (fire-and-forget)
                def run_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(save_loan_application(conversation_id, state))
                    finally:
                        loop.close()
                
                thread = threading.Thread(target=run_async)
                thread.daemon = True
                thread.start()
                print(f"[UNDERWRITING] Scheduled loan application save for conversation {conversation_id}")
            except Exception as e:
                print(f"[UNDERWRITING] Error scheduling loan save: {e}")

        # Return state updates
        return {
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "key_risk_factors": key_risk_factors,
            "key_strengths": key_strengths,
            "loan_offer": loan_offer,
            "loan_offered": True,
            "_loan_saved": True,
            "next_agent": None,
        }


# TODO: Production integration
"""
In production, this agent would:

1. Call your credit model API:
   response = requests.post(
       "https://your-platform.com/api/credit/assess",
       json={
           "business_id": state["user_id"],
           "business_data": {...},
           "photo_insights": state["photo_insights"],
       },
       headers={"Authorization": f"Bearer {API_KEY}"}
   )
   risk_score = response.json()["risk_score"]

2. Query your lending platform for offer:
   offer_response = requests.post(
       "https://your-platform.com/api/loans/generate-offer",
       json={
           "customer_id": state["user_id"],
           "risk_score": risk_score,
           "requested_amount": 5000,
       }
   )
   loan_terms = offer_response.json()

3. Create loan application:
   if state["loan_accepted"]:
       app_response = requests.post(
           "https://your-platform.com/api/loans/applications",
           json={
               "customer_id": state["user_id"],
               "loan_offer_id": loan_terms["offer_id"],
               "accepted_at": datetime.now().isoformat(),
           }
       )
"""

# Singleton instance (instantiated after env is loaded)
underwriting_agent = None

def initialize_underwriting_agent():
    global underwriting_agent
    if underwriting_agent is None:
        underwriting_agent = UnderwritingAgent()
