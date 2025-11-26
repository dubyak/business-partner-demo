"""
Onboarding Agent - Handles customer onboarding, information gathering, and photo analysis.

This agent combines conversation management and vision capabilities to:
- Maintain natural dialogue flow
- Gather business information (type, location, revenue, etc.)
- Request and analyze business photos
- Route to underwriting when information is complete
- Fetches system prompt from Langfuse
"""

import os
import re
from typing import Dict, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

from state import BusinessPartnerState, PhotoInsight


class OnboardingAgent:
    """Agent specialized in customer onboarding, information gathering, and photo analysis."""

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
            print(f"[LANGFUSE-ONBOARDING] Using cached prompt (age: {int(now - self.prompt_cache_time)}s)")
            return self.system_prompt

        # Try to fetch from Langfuse
        try:
            prompt_name = os.getenv("LANGFUSE_ONBOARDING_PROMPT_NAME", "onboarding-agent-system")
            print(f"[LANGFUSE-ONBOARDING] Fetching prompt: {prompt_name}")

            prompt_obj = self.langfuse.get_prompt(prompt_name)

            if prompt_obj and hasattr(prompt_obj, "prompt"):
                self.system_prompt = prompt_obj.prompt
                self.prompt_cache_time = now
                print(f"[LANGFUSE-ONBOARDING] ✓ Prompt fetched successfully (v{prompt_obj.version})")
                return self.system_prompt
            else:
                print(f"[LANGFUSE-ONBOARDING] ✗ Prompt object missing 'prompt' property")

        except Exception as e:
            print(f"[LANGFUSE-ONBOARDING] ✗ Error fetching prompt: {e}")

        # Fallback to default prompt
        print("[LANGFUSE-ONBOARDING] → Using fallback prompt")
        return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback system prompt if Langfuse is unavailable."""
        return """You are a friendly business partner agent for a lending platform. Help customers with loan onboarding.

FLOW:
1. Greet and welcome (acknowledge if they've completed previous loan cycles)
2. Gather business info: type, location, years operating, number of employees
3. Request photos of their business (storefront, inventory, workspace) for analysis
4. Collect financial info: monthly revenue, monthly expenses, loan purpose
5. Once all info is collected, route to underwriting for loan offer

Keep responses SHORT (2-3 paragraphs max). Ask 1-2 questions at a time. Be conversational and encouraging."""

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

    @observe(name="onboarding-agent-analyze-photo")
    def analyze_photo(self, photo_b64: str, photo_index: int, business_context: Dict) -> PhotoInsight:
        """
        Analyze a single business photo using Claude's vision capabilities.

        Args:
            photo_b64: Base64 encoded image
            photo_index: Index of the photo in the list
            business_context: Dictionary with business_type, location, etc.

        Returns:
            PhotoInsight with structured analysis
        """
        system_prompt = """You are a business consultant analyzing photos of small businesses.

Your task: Analyze the photo and provide:
1. Cleanliness score (0-10): How clean and well-maintained is the space?
2. Organization score (0-10): How organized is the inventory/workspace?
3. Stock level: "low", "medium", or "high" - how well-stocked does it appear?
4. 2-3 specific observations about what you see
5. 1-2 actionable coaching tips to improve the business

Be specific, practical, and encouraging. Focus on visual signals that indicate business health."""

        # Determine media type from base64 prefix if present, default to jpeg
        media_type = "image/jpeg"
        if photo_b64.startswith("data:"):
            if "image/png" in photo_b64:
                media_type = "image/png"
            elif "image/webp" in photo_b64:
                media_type = "image/webp"
            # Strip the data:image/xxx;base64, prefix
            photo_b64 = photo_b64.split(",", 1)[1]

        context_str = f"Business type: {business_context.get('business_type', 'unknown')}, Location: {business_context.get('location', 'unknown')}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=[
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": photo_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"Analyze this business photo. Context: {context_str}\n\nProvide your analysis in this exact format:\nCleanliness: [score]/10\nOrganization: [score]/10\nStock Level: [low/medium/high]\nObservations:\n- [observation 1]\n- [observation 2]\nCoaching Tips:\n- [tip 1]\n- [tip 2]",
                    },
                ]
            ),
        ]

        langfuse_context.update_current_observation(
            input={"photo_index": photo_index, "business_context": business_context},
            metadata={"agent": "onboarding", "type": "photo_analysis", "model": "claude-sonnet-4-20250514"},
        )

        response = self.llm.invoke(messages)
        analysis_text = response.content

        # Parse the response
        insight = self._parse_analysis(analysis_text, photo_index)

        langfuse_context.update_current_observation(output=insight)

        return insight

    def _parse_analysis(self, analysis_text: str, photo_index: int) -> PhotoInsight:
        """Parse the LLM response into structured PhotoInsight."""
        lines = analysis_text.strip().split("\n")
        cleanliness_score = 7.5
        organization_score = 7.5
        stock_level = "medium"
        observations = []
        coaching_tips = []

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse scores
            if line.lower().startswith("cleanliness:"):
                try:
                    score_str = line.split(":")[1].strip().split("/")[0]
                    cleanliness_score = float(score_str)
                except:
                    pass

            elif line.lower().startswith("organization:"):
                try:
                    score_str = line.split(":")[1].strip().split("/")[0]
                    organization_score = float(score_str)
                except:
                    pass

            elif line.lower().startswith("stock level:"):
                level = line.split(":")[1].strip().lower()
                if level in ["low", "medium", "high"]:
                    stock_level = level

            # Track sections
            elif line.lower().startswith("observations:"):
                current_section = "observations"
            elif line.lower().startswith("coaching tips:"):
                current_section = "coaching"

            # Collect bullet points
            elif line.startswith("-") or line.startswith("•"):
                text = line[1:].strip()
                if current_section == "observations":
                    observations.append(text)
                elif current_section == "coaching":
                    coaching_tips.append(text)

        return PhotoInsight(
            photo_index=photo_index,
            cleanliness_score=cleanliness_score,
            organization_score=organization_score,
            stock_level=stock_level,
            insights=observations if observations else ["Photo analyzed successfully"],
            coaching_tips=coaching_tips if coaching_tips else ["Continue maintaining your business well"],
        )

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

    def _should_call_underwriting_agent(self, state: BusinessPartnerState) -> bool:
        """Determine if we should call the underwriting agent."""
        # Call underwriting when:
        # - Info is complete
        # - Photos have been analyzed
        # - Loan hasn't been offered yet

        info_complete = self._check_if_info_complete(state)
        photos_analyzed = len(state.get("photo_insights", [])) > 0
        loan_offered = state.get("loan_offered", False)

        return info_complete and photos_analyzed and not loan_offered

    def _should_call_servicing_agent(self, state: BusinessPartnerState) -> bool:
        """Determine if we should call the servicing agent."""
        # Call servicing agent when:
        # 1. Loan is accepted and disbursement hasn't been initiated
        # 2. User asks about repayments, payment schedule, or has payment issues
        # 3. User needs help with recovery conversations
        
        loan_accepted = state.get("loan_accepted", False)
        disbursement_status = state.get("disbursement_status")
        
        # Check if loan accepted and needs disbursement
        if loan_accepted and not disbursement_status:
            return True
        
        # Check user messages for servicing-related keywords
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content") and isinstance(last_message.content, str):
                content_lower = last_message.content.lower()
                servicing_keywords = [
                    "payment", "repay", "installment", "due date", "schedule",
                    "disbursement", "when will I receive", "bank account",
                    "trouble paying", "can't pay", "late payment", "missed payment",
                    "recovery", "payment plan", "promise to pay"
                ]
                if any(keyword in content_lower for keyword in servicing_keywords):
                    return True
        
        # Check if there's an active recovery conversation
        recovery_status = state.get("recovery_status")
        if recovery_status and recovery_status not in ["resolved", "escalated"]:
            return True
        
        return False

    def _detect_servicing_type(self, state: BusinessPartnerState) -> str:
        """Detect what type of servicing interaction is needed."""
        messages = state.get("messages", [])
        last_message_content = ""
        
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content") and isinstance(last_message.content, str):
                last_message_content = last_message.content.lower()
        
        # Check for disbursement
        if state.get("loan_accepted") and not state.get("disbursement_status"):
            return "disbursement"
        
        # Check for recovery
        if any(keyword in last_message_content for keyword in ["trouble", "difficulty", "can't pay", "late", "missed", "help"]):
            return "recovery"
        
        # Check for repayment
        if any(keyword in last_message_content for keyword in ["payment", "repay", "installment", "pay now"]):
            return "repayment"
        
        # Check for payment schedule
        if any(keyword in last_message_content for keyword in ["schedule", "when", "due date", "payment dates"]):
            return "payment_schedule"
        
        # Check for repayment impact explanation
        if any(keyword in last_message_content for keyword in ["impact", "affect", "future loan", "credit", "eligibility"]):
            return "repayment_impact"
        
        return "general"

    @observe(name="onboarding-agent-generate-response")
    def generate_response(self, state: BusinessPartnerState) -> str:
        """
        Generate a conversational response using Claude.

        Incorporates context from photo analysis if available.
        """
        # Get base system prompt from Langfuse
        base_system_prompt = self.get_system_prompt()
        
        # If frontend sent language instruction, extract and prepend it prominently
        if state.get("system_prompt") and ("LANGUAGE REQUIREMENT" in state.get("system_prompt", "") or "CRITICAL LANGUAGE REQUIREMENT" in state.get("system_prompt", "")):
            frontend_prompt = state.get("system_prompt")
            # Extract the language instruction - find it and get the full instruction
            lang_keyword = "CRITICAL LANGUAGE REQUIREMENT" if "CRITICAL LANGUAGE REQUIREMENT" in frontend_prompt else "LANGUAGE REQUIREMENT"
            if lang_keyword in frontend_prompt:
                lang_start = frontend_prompt.find(lang_keyword)
                # Get everything from LANGUAGE REQUIREMENT to the end of that line or next newline
                lang_section = frontend_prompt[lang_start:]
                # Extract up to the first double newline or end of string
                if "\n\n" in lang_section:
                    lang_instruction = lang_section.split("\n\n")[0]
                elif "\n" in lang_section:
                    # Get the full line if no double newline
                    lang_instruction = lang_section.split("\n")[0]
                else:
                    lang_instruction = lang_section
                
                # Prepend language instruction prominently to the prompt
                system_prompt = f"{lang_instruction}\n\n{base_system_prompt}"
            else:
                system_prompt = base_system_prompt
        else:
            system_prompt = base_system_prompt

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

        # Add servicing information if available
        disbursement_info = state.get("disbursement_info")
        if disbursement_info:
            context_additions.append(
                f"\n[DISBURSEMENT STATUS]\n"
                f"Status: {state.get('disbursement_status', 'unknown')}\n"
                f"Reference: {disbursement_info.get('reference_number', 'N/A')}\n"
                f"Amount: {disbursement_info.get('amount', 0):,.0f} pesos\n"
                f"Estimated Completion: {disbursement_info.get('estimated_completion', 'N/A')}"
            )

        payment_schedule = state.get("payment_schedule")
        if payment_schedule:
            schedule_text = "\n".join([
                f"Payment {p['installment_number']}: {p['amount']:,.2f} pesos due {p['due_date']}"
                for p in payment_schedule.get("schedule", [])
            ])
            context_additions.append(f"\n[PAYMENT SCHEDULE]\n{schedule_text}")

        repayment_info = state.get("repayment_info")
        if repayment_info:
            context_additions.append(
                f"\n[REPAYMENT STATUS]\n"
                f"Status: {state.get('repayment_status', 'unknown')}\n"
                f"Method: {repayment_info.get('method', 'N/A')}\n"
                f"Amount: {repayment_info.get('amount', 0):,.2f} pesos\n"
                f"Reference: {repayment_info.get('reference_number', 'N/A')}"
            )

        recovery_info = state.get("recovery_info")
        if recovery_info:
            context_additions.append(
                f"\n[RECOVERY CONVERSATION]\n"
                f"Status: {state.get('recovery_status', 'unknown')}\n"
                f"Active: {recovery_info.get('conversation_active', False)}"
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
            input={
                "message_count": len(state.get("messages", [])),
                "has_photo_insights": len(photo_insights) > 0,
                "info_complete": self._check_if_info_complete(state),
            },
            metadata={"agent": "onboarding", "model": "claude-sonnet-4-20250514"},
        )

        response = self.llm.invoke(messages_for_llm)

        # Update Langfuse with output
        langfuse_context.update_current_observation(output={"response_length": len(response.content)})

        return response.content

    @observe(name="onboarding-agent-process")
    def process(self, state: BusinessPartnerState) -> Dict:
        """
        Main entry point for the Onboarding Agent.

        Manages conversation flow, analyzes photos, and determines routing.
        """
        # Fetch system prompt if not already in state
        # Always use Langfuse prompt as base
        base_system_prompt = self.get_system_prompt()
        
        # If frontend sent language instruction, extract and prepend it prominently
        if state.get("system_prompt") and ("LANGUAGE REQUIREMENT" in state.get("system_prompt", "") or "CRITICAL LANGUAGE REQUIREMENT" in state.get("system_prompt", "")):
            frontend_prompt = state.get("system_prompt")
            # Extract the language instruction - find it and get the full instruction
            lang_keyword = "CRITICAL LANGUAGE REQUIREMENT" if "CRITICAL LANGUAGE REQUIREMENT" in frontend_prompt else "LANGUAGE REQUIREMENT"
            if lang_keyword in frontend_prompt:
                lang_start = frontend_prompt.find(lang_keyword)
                lang_section = frontend_prompt[lang_start:]
                # Extract up to the first double newline or end of string
                if "\n\n" in lang_section:
                    lang_instruction = lang_section.split("\n\n")[0]
                elif "\n" in lang_section:
                    # Get the full line if no double newline
                    lang_instruction = lang_section.split("\n")[0]
                else:
                    lang_instruction = lang_section
                
                # Prepend language instruction prominently to the prompt
                system_prompt = f"{lang_instruction}\n\n{base_system_prompt}"
            else:
                system_prompt = base_system_prompt
        else:
            system_prompt = base_system_prompt

        # Extract photos from latest message if any
        photos_in_message = self._detect_photos_in_message(state.get("messages", []))
        if photos_in_message:
            current_photos = state.get("photos", [])
            current_photos.extend(photos_in_message)
            state["photos"] = current_photos

        # Analyze any new photos that haven't been analyzed yet
        num_photos = len(state.get("photos", []))
        num_analyzed = len(state.get("photo_insights", []))
        
        if num_photos > num_analyzed:
            # Extract business context
            business_context = {
                "business_type": state.get("business_type"),
                "location": state.get("location"),
                "business_name": state.get("business_name"),
            }

            # Analyze new photos
            photo_insights = state.get("photo_insights", [])
            for idx in range(num_analyzed, num_photos):
                photo_b64 = state.get("photos", [])[idx]
                if photo_b64:
                    insight = self.analyze_photo(photo_b64, idx, business_context)
                    photo_insights.append(insight)

            state["photo_insights"] = photo_insights

        # Check info completeness
        info_complete = self._check_if_info_complete(state)

        # Check for loan acceptance
        if state.get("loan_offered") and not state.get("loan_accepted"):
            if self._check_if_loan_accepted(state.get("messages", [])):
                state["loan_accepted"] = True

        # Determine routing to specialist agents
        next_agent = None
        servicing_type = None

        if self._should_call_underwriting_agent(state):
            next_agent = "underwriting"
        elif state.get("loan_accepted") and not state.get("coaching_provided"):
            next_agent = "coaching"
        elif self._should_call_servicing_agent(state):
            next_agent = "servicing"
            servicing_type = self._detect_servicing_type(state)

        # Generate conversational response
        response_text = self.generate_response(state)

        # Add response to messages
        result = {
            "messages": [AIMessage(content=response_text)],
            "system_prompt": system_prompt,
            "info_complete": info_complete,
            "photos_received": num_photos > 0,
            "next_agent": next_agent,
        }
        
        # Add servicing type if routing to servicing agent
        if servicing_type:
            result["servicing_type"] = servicing_type
        
        return result


# Singleton instance (instantiated after env is loaded)
onboarding_agent = None

def initialize_onboarding_agent():
    global onboarding_agent
    if onboarding_agent is None:
        onboarding_agent = OnboardingAgent()

