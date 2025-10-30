"""
Conversation Agent - Main orchestrator for the Business Partner chat.

This agent:
- Maintains natural dialogue flow
- Fetches system prompt from Langfuse
- Detects when to delegate to specialist agents
- Integrates specialist results into conversation
- Manages onboarding progress
"""

import os
import re
from typing import Dict
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

from state import BusinessPartnerState


class ConversationAgent:
    """Main conversational agent that orchestrates the flow."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=1024,
        )

        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
        )

        self.system_prompt = None
        self.prompt_cache_time = None
        self.prompt_ttl = 60  # seconds

    def get_system_prompt(self) -> str:
        """
        Fetch system prompt from Langfuse with caching.

        Falls back to a default if Langfuse fetch fails.
        """
        import time

        now = time.time()

        # Return cached prompt if valid
        if self.system_prompt and self.prompt_cache_time and (now - self.prompt_cache_time < self.prompt_ttl):
            print(f"[LANGFUSE] Using cached prompt (age: {int(now - self.prompt_cache_time)}s)")
            return self.system_prompt

        # Try to fetch from Langfuse
        try:
            prompt_name = os.getenv("LANGFUSE_PROMPT_NAME", "business-partner-system")
            print(f"[LANGFUSE] Fetching prompt: {prompt_name}")

            prompt_obj = self.langfuse.get_prompt(prompt_name)

            if prompt_obj and hasattr(prompt_obj, "prompt"):
                self.system_prompt = prompt_obj.prompt
                self.prompt_cache_time = now
                print(f"[LANGFUSE] ✓ Prompt fetched successfully (v{prompt_obj.version})")
                return self.system_prompt
            else:
                print(f"[LANGFUSE] ✗ Prompt object missing 'prompt' property")

        except Exception as e:
            print(f"[LANGFUSE] ✗ Error fetching prompt: {e}")

        # Fallback to default prompt
        print("[LANGFUSE] → Using fallback prompt")
        return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback system prompt if Langfuse is unavailable."""
        return """You are a business partner agent for a lending platform. Help customers with loan onboarding.

FLOW:
1. Greet and welcome (acknowledge 3 completed loan cycles)
2. Gather business info: type, location, operations
3. Request photos for analysis
4. Collect financial info: revenue, expenses
5. Present loan offer (5,000 pesos, 45 days, 3 installments, 11% flat)
6. After acceptance: provide coaching

Keep responses SHORT (2-3 paragraphs max). Ask 1-2 questions at a time. Be conversational."""

    def _detect_photos_in_message(self, messages: list) -> list:
        """Extract base64 photos from the latest user message."""
        if not messages:
            return []

        last_message = messages[-1]

        # Check if it's a HumanMessage with content list (multimodal)
        if hasattr(last_message, "content") and isinstance(last_message.content, list):
            photos = []
            for item in last_message.content:
                if isinstance(item, dict) and item.get("type") == "image":
                    # Extract base64 data
                    source = item.get("source", {})
                    if source.get("type") == "base64":
                        photos.append(source.get("data"))
            return photos

        return []

    def _should_call_vision_agent(self, state: BusinessPartnerState) -> bool:
        """Determine if we should call the vision agent."""
        # Check if there are new photos that haven't been analyzed
        num_photos = len(state.get("photos", []))
        num_analyzed = len(state.get("photo_insights", []))

        return num_photos > num_analyzed

    def _should_call_underwriting_agent(self, state: BusinessPartnerState) -> bool:
        """Determine if we should call the underwriting agent."""
        # Call underwriting when:
        # - Info is complete
        # - Photos have been analyzed
        # - Loan hasn't been offered yet

        info_complete = state.get("info_complete", False)
        photos_analyzed = len(state.get("photo_insights", [])) > 0
        loan_offered = state.get("loan_offered", False)

        return info_complete and photos_analyzed and not loan_offered

    def _check_if_info_complete(self, state: BusinessPartnerState) -> bool:
        """Check if we have enough business info to proceed to underwriting."""
        required_fields = ["business_type", "location", "monthly_revenue", "loan_purpose"]

        return all(state.get(field) is not None for field in required_fields)

    def _check_if_loan_accepted(self, messages: list) -> bool:
        """Check if the user accepted the loan offer."""
        if not messages:
            return False

        # Look at the last user message
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            content = last_message.content
            if isinstance(content, str):
                content_lower = content.lower().strip()
                # Check for acceptance keywords
                return any(keyword in content_lower for keyword in ["yes", "sí", "si", "accept", "acepto", "okay", "ok"])

        return False

    @observe(name="conversation-agent-respond")
    def generate_response(self, state: BusinessPartnerState) -> str:
        """
        Generate a conversational response using Claude.

        Incorporates context from specialist agents if available.
        """

        system_prompt = state.get("system_prompt") or self.get_system_prompt()

        # Build context from state
        context_additions = []

        # Add photo insights if available
        photo_insights = state.get("photo_insights", [])
        if photo_insights:
            context_additions.append("\n[PHOTO ANALYSIS RESULTS]")
            for insight in photo_insights:
                context_additions.append(
                    f"Photo {insight['photo_index'] + 1}: Cleanliness: {insight['cleanliness_score']}/10, "
                    f"Organization: {insight['organization_score']}/10, Stock: {insight['stock_level']}"
                )
                if insight.get("insights"):
                    context_additions.append(f"  Observations: {', '.join(insight['insights'])}")

        # Add loan offer if available
        loan_offer = state.get("loan_offer")
        if loan_offer:
            context_additions.append(
                f"\n[LOAN OFFER READY]\n"
                f"Amount: {loan_offer['amount']:,.0f} pesos\n"
                f"Term: {loan_offer['term_days']} days ({loan_offer['installments']} installments)\n"
                f"Payment: {loan_offer['installment_amount']:,.2f} pesos every 15 days\n"
                f"Total: {loan_offer['total_repayment']:,.2f} pesos ({loan_offer['interest_rate_flat']}% flat rate)\n"
                f"Terms: {loan_offer['terms_url']}"
            )

        # Append context to system prompt
        full_system_prompt = system_prompt
        if context_additions:
            full_system_prompt += "\n\n" + "\n".join(context_additions)

        # Build messages for Claude
        messages_for_llm = [SystemMessage(content=full_system_prompt)]

        # Add conversation history
        for msg in state.get("messages", []):
            messages_for_llm.append(msg)

        # Add Langfuse context
        langfuse_context.update_current_observation(
            input={"message_count": len(state.get("messages", [])), "has_photo_insights": len(photo_insights) > 0, "has_loan_offer": loan_offer is not None},
            metadata={"agent": "conversation", "model": "claude-sonnet-4-20250514", "system_prompt_source": "langfuse" if state.get("system_prompt") else "fallback"},
        )

        response = self.llm.invoke(messages_for_llm)

        # Update Langfuse with output
        langfuse_context.update_current_observation(output={"response_length": len(response.content)})

        return response.content

    @observe(name="conversation-agent-process")
    def process(self, state: BusinessPartnerState) -> Dict:
        """
        Main entry point for the Conversation Agent.

        Manages conversation flow and determines which specialist agents to call.
        """

        # Fetch system prompt if not already in state
        if not state.get("system_prompt"):
            system_prompt = self.get_system_prompt()
        else:
            system_prompt = state.get("system_prompt")

        # Extract photos from latest message if any
        photos_in_message = self._detect_photos_in_message(state.get("messages", []))
        if photos_in_message:
            current_photos = state.get("photos", [])
            current_photos.extend(photos_in_message)
            state["photos"] = current_photos

        # Check info completeness
        info_complete = self._check_if_info_complete(state)

        # Check for loan acceptance
        if state.get("loan_offered") and not state.get("loan_accepted"):
            if self._check_if_loan_accepted(state.get("messages", [])):
                state["loan_accepted"] = True

        # Determine routing to specialist agents
        next_agent = None

        if self._should_call_vision_agent(state):
            next_agent = "vision"
        elif self._should_call_underwriting_agent(state):
            next_agent = "underwriting"
        elif state.get("loan_accepted") and not state.get("coaching_provided"):
            next_agent = "coaching"

        # Generate conversational response
        response_text = self.generate_response(state)

        # Add response to messages
        return {
            "messages": [AIMessage(content=response_text)],
            "system_prompt": system_prompt,
            "info_complete": info_complete,
            "next_agent": next_agent,
        }


# Singleton instance (instantiated after env is loaded)
conversation_agent = None

def initialize_conversation_agent():
    global conversation_agent
    if conversation_agent is None:
        conversation_agent = ConversationAgent()
