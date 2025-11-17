"""
Underwriting Agent - Generates loan offers based on business data and risk assessment.

This agent:
- Evaluates business information and photo insights
- Calculates risk score
- Generates appropriate loan offer
- (In production: would integrate with credit models and lending platform)
"""

from typing import Dict
from langfuse.decorators import observe, langfuse_context
import threading

from state import BusinessPartnerState, LoanOffer, PhotoInsight
from db import save_loan_application


class UnderwritingAgent:
    """Agent specialized in loan underwriting and offer generation."""

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

        # Calculate risk score
        risk_score = self.calculate_risk_score(state)

        # Generate loan offer
        loan_offer = self.generate_loan_offer(risk_score, state)

        # Add Langfuse context
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
            metadata={"agent": "underwriting", "demo_mode": True},
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
