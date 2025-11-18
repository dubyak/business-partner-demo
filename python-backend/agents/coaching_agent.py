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
                print(f"[LANGFUSE-COACHING] ✓ Prompt fetched successfully (v{prompt_obj.version})")
                return self.system_prompt
            else:
                print(f"[LANGFUSE-COACHING] ✗ Prompt object missing 'prompt' property")

        except Exception as e:
            print(f"[LANGFUSE-COACHING] ✗ Error fetching prompt: {e}")

        # Fallback to default prompt
        print("[LANGFUSE-COACHING] → Using fallback prompt")
        return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback system prompt if Langfuse is unavailable."""
        return """You are an experienced business coach helping small business owners grow.

Your task: Provide 3-4 specific, actionable coaching tips based on:
- Business type and operations
- Visual insights from their photos
- Their stated goals for the loan

Be:
- Specific and actionable (not generic advice)
- Encouraging and supportive
- Focused on practical next steps
- Relevant to their specific business type

Format your response as a friendly paragraph with 3-4 concrete suggestions."""

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

        # Add Langfuse context
        langfuse_context.update_current_observation(
            input={"business_type": business_type, "loan_purpose": loan_purpose, "num_insights": len(insights_summary)},
            metadata={"agent": "coaching", "model": "claude-sonnet-4-20250514"},
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

        # Note: We don't add this to messages - the main conversation agent
        # will incorporate this into its response naturally

        return {
            "next_agent": None,
            # Could store coaching advice in state if needed
            # "coaching_advice": coaching_advice
        }


# Singleton instance (instantiated after env is loaded)
coaching_agent = None

def initialize_coaching_agent():
    global coaching_agent
    if coaching_agent is None:
        coaching_agent = CoachingAgent()
