"""
Coaching Agent - Provides personalized business advice and growth strategies.

This agent:
- Analyzes business profile and photo insights
- Generates specific, actionable coaching advice
- Tailors recommendations to business type and goals
- Helps customers succeed after loan acceptance
"""

import os
from typing import Dict, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

from state import BusinessPartnerState


class CoachingAgent:
    """Agent specialized in providing business coaching and advice."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=800,
        )

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
            print(f"[LANGFUSE-COACHING] Using cached prompt (age: {int(now - self.prompt_cache_time)}s)")
            return self.system_prompt

        # Try to fetch from Langfuse
        try:
            prompt_name = os.getenv("LANGFUSE_COACHING_PROMPT_NAME", "coaching-agent-system")
            print(f"[LANGFUSE-COACHING] Fetching prompt: {prompt_name}")

            prompt_obj = self.langfuse.get_prompt(prompt_name)

            if prompt_obj and hasattr(prompt_obj, "prompt"):
                self.system_prompt = prompt_obj.prompt
                self.prompt_cache_time = now
                self.prompt_name = prompt_name
                self.prompt_version = getattr(prompt_obj, "version", None)
                print(f"[LANGFUSE-COACHING] ✓ Prompt fetched successfully (v{prompt_obj.version})")
                return self.system_prompt
            else:
                print(f"[LANGFUSE-COACHING] ✗ Prompt object missing 'prompt' property")

        except Exception as e:
            print(f"[LANGFUSE-COACHING] ✗ Error fetching prompt: {e}")

        # Fallback to default prompt
        print("[LANGFUSE-COACHING] → Using fallback prompt")
        self.prompt_name = None  # Clear prompt metadata on fallback
        self.prompt_version = None
        return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback system prompt if Langfuse is unavailable."""
        return """You are an experienced business coach helping small business owners grow. You work in the BACKGROUND - you do NOT speak directly to customers.

YOUR ROLE:
You generate coaching advice based on business profile and context. The business_partner agent reads your advice and incorporates it naturally into customer-facing responses.

IMPORTANT: You are a BACKGROUND SERVICE. You do NOT generate user-facing messages. You generate coaching_advice (a string) that the business_partner agent will use.

COACHING THEMES:
Focus on 3 main themes in your advice:

1. **Cash Flow & Loan Usage**:
   - How to use the loan effectively
   - Managing cash flow to ensure repayment
   - Setting aside funds for installments

2. **Sales & Customer Growth (30-60 days)**:
   - Specific strategies to increase sales
   - Customer acquisition tactics
   - Marketing ideas relevant to their business type

3. **Debt & Obligations**:
   - Staying on track with repayments
   - Managing multiple obligations
   - Building good repayment history

PHASE-BASED COACHING:

**Pre-loan (onboarding/offer phases):**
- Help them decide if a bigger/longer loan is wise
- Assess if they're ready for the loan
- Suggest how to use funds effectively

**Post-loan (post_disbursement phase):**
- How to deploy loan funds for maximum impact
- Keeping cash reserves for installments
- Growth strategies while managing debt

**Delinquent phase:**
- Blend gentle coaching with the recovery plan from servicing
- Help them understand root causes
- Suggest business improvements that address payment difficulties

FORMAT:
Provide 3-4 specific, actionable tips as a friendly paragraph. Be:
- Specific and actionable (not generic advice)
- Encouraging and supportive
- Focused on practical next steps
- Relevant to their specific business type and phase

The business_partner agent will incorporate this naturally into their response."""

    @observe(name="coaching-agent-generate")
    def generate_coaching_advice(self, state: BusinessPartnerState) -> str:
        """
        Generate personalized coaching advice based on business profile and insights.

        Args:
            state: Current conversation state with business info and photo insights

        Returns:
            Formatted coaching advice as a string
        """

        # Fetch system prompt from Langfuse or use fallback
        system_prompt = self.get_system_prompt()

        # Build context from state
        business_type = state.get("business_type", "business")
        loan_purpose = state.get("loan_purpose", "growing the business")
        monthly_revenue = state.get("monthly_revenue", 0)

        # Extract photo insights
        photo_insights = state.get("photo_insights", [])
        insights_summary = []
        tips_summary = []

        for insight in photo_insights:
            insights_summary.extend(insight.get("insights", []))
            tips_summary.extend(insight.get("coaching_tips", []))

        insights_text = "\n".join([f"- {i}" for i in insights_summary]) if insights_summary else "No photos analyzed yet"
        tips_text = "\n".join([f"- {t}" for t in tips_summary]) if tips_summary else "No initial tips"

        context = f"""Business Profile:
- Type: {business_type}
- Loan Purpose: {loan_purpose}
- Monthly Revenue: {monthly_revenue:,.0f} pesos

Photo Analysis Observations:
{insights_text}

Initial Tips from Visual Analysis:
{tips_text}
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"Generate personalized coaching advice for this business owner:\n\n{context}\n\nProvide 3-4 specific, actionable tips to help them succeed."
            ),
        ]

        # Add Langfuse context with prompt information
        metadata = {
            "agent": "coaching",
            "model": "claude-sonnet-4-20250514",
        }
        # Link prompt to generation if available
        if self.prompt_name:
            metadata["prompt_name"] = self.prompt_name
        if self.prompt_version:
            metadata["prompt_version"] = self.prompt_version
        
        langfuse_context.update_current_observation(
            input={"business_type": business_type, "loan_purpose": loan_purpose, "num_insights": len(insights_summary)},
            metadata=metadata,
        )

        response = self.llm.invoke(messages)
        coaching_advice = response.content

        # Update Langfuse with output
        langfuse_context.update_current_observation(output={"advice_length": len(coaching_advice), "advice": coaching_advice})

        return coaching_advice

    @observe(name="coaching-agent-process")
    def process(self, state: BusinessPartnerState) -> Dict:
        """
        Main entry point for the Coaching Agent.

        Generates coaching advice and doesn't modify routing.
        """

        coaching_advice = self.generate_coaching_advice(state)

        # Store coaching advice in state for business_partner agent to use
        # The business_partner agent will read this and craft the user-facing response

        return {
            "next_agent": None,
            "coaching_advice": coaching_advice,  # Store in state for business_partner to use
        }


# Singleton instance (instantiated after env is loaded)
coaching_agent = None

def initialize_coaching_agent():
    global coaching_agent
    if coaching_agent is None:
        coaching_agent = CoachingAgent()
