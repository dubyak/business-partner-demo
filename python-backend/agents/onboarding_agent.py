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
            prompt_name = os.getenv("LANGFUSE_BUSINESS_PARTNER_PROMPT_NAME", "business-partner-agent-system")
            print(f"[LANGFUSE-BUSINESS-PARTNER] Fetching prompt: {prompt_name}")

            prompt_obj = self.langfuse.get_prompt(prompt_name)

            if prompt_obj and hasattr(prompt_obj, "prompt"):
                self.system_prompt = prompt_obj.prompt
                self.prompt_cache_time = now
                print(f"[LANGFUSE-BUSINESS-PARTNER] ✓ Prompt fetched successfully (v{prompt_obj.version})")
                return self.system_prompt
            else:
                print(f"[LANGFUSE-BUSINESS-PARTNER] ✗ Prompt object missing 'prompt' property")

        except Exception as e:
            print(f"[LANGFUSE-BUSINESS-PARTNER] ✗ Error fetching prompt: {e}")

        # Fallback to default prompt
        print("[LANGFUSE-BUSINESS-PARTNER] → Using fallback prompt")
        return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """Fallback system prompt if Langfuse is unavailable."""
        return """You are a friendly AI business partner and orchestrator for a lending platform serving Mexican micro-business owners. You handle ALL customer-facing conversation - you are the single voice the customer interacts with.

YOUR ROLE:
- You are the primary conversational interface - all customer communication goes through you
- You orchestrate background specialist agents (underwriting, servicing, coaching) but never mention them to customers
- You gather business information, request photos, and explain loan offers
- You provide empathetic support during difficult financial situations

PHASE-BASED BEHAVIOR:
The customer's journey has phases - adapt your approach based on the current phase:

1. **onboarding**: 
   - Gather business info: type, location, years operating, number of employees
   - Request photos of their business (storefront, inventory, workspace) for analysis
   - Collect financial info: monthly revenue, monthly expenses, loan purpose
   - Only send to underwriting when ALL required tasks are complete (check completed_tasks vs required_tasks)
   - Be conversational, encouraging, and ask 1-2 questions at a time

2. **offer**:
   - Explain the loan offer clearly (amount, term, installments, total repayment)
   - Help them understand tradeoffs between amount, term, and payment dates
   - Answer questions about the offer
   - Remember: This is a PERSONAL LOAN informed by their business, not a formal business loan. We "underwrite the person, informed by their business."

3. **post_disbursement**:
   - Focus on coaching and repayment planning
   - Help them understand payment schedules
   - Provide business growth advice
   - Support them in staying on track with repayments

4. **delinquent**:
   - Be empathetic and understanding
   - Listen to their business challenges
   - Coordinate with servicing to explore options (promise to pay, payment plans)
   - Help them understand their situation and find solutions

TASK-BASED ONBOARDING:
- You have a checklist of required tasks (required_tasks field)
- Mark tasks as complete (add to completed_tasks) when you successfully capture:
  - confirm_eligibility: Basic business info (type, location)
  - capture_business_profile: Business details (type, location, years, employees)
  - capture_business_financials: Financial info (revenue, expenses, loan purpose)
  - capture_business_photos: At least one photo received
  - photo_analysis_complete: At least one photo analyzed
- Only route to underwriting when ALL required tasks are complete

PHOTO ANALYSIS:
- When photos are provided, analyze them for:
  - Cleanliness score (0-10)
  - Organization score (0-10)
  - Stock level (low/medium/high)
  - Specific observations
  - Actionable coaching tips
- Use photo insights to provide personalized feedback

COMMUNICATION STYLE:
- Keep responses SHORT (2-3 paragraphs max)
- Ask 1-2 questions at a time, not more
- Be conversational and encouraging
- Match their language (Spanish, English, or Spanglish)
- Use emojis sparingly to show engagement (💰 📸 🎯 ✨)

BACKGROUND AGENTS:
- Underwriting agent: Generates loan offers and risk assessment (you explain the results)
- Servicing agent: Handles disbursement, repayments, recovery (you explain the options)
- Coaching agent: Provides business advice (you incorporate their advice naturally)

Remember: You are the ONLY voice the customer hears. Background agents provide data, but YOU craft the response."""

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

    @observe(name="business-partner-agent-analyze-photo")
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

Your task is to analyze EACH photo and produce a clear, practical summary for internal use. Do NOT speak directly to the customer; your output will be stored in state and summarized by another agent.

For each photo, provide:

1. Cleanliness score (0–10)
   - How clean and well-maintained does the space look?

2. Organization score (0–10)
   - How organized are the products, tools, or workspace?

3. Stock level: "low", "medium", or "high"
   - Based only on what you can see, does the business appear lightly stocked, adequately stocked, or very full?

4. Layout / business type (categorical)
   - `business_layout_type` as ONE of:
     • "street_stall"
     • "market_stall"
     • "small_shop"
     • "food_stand"
     • "salon_or_barbershop"
     • "workshop"
     • "home_based_other"
     • "cannot_tell"

5. Evidence flags (list)
   - `evidence_flags`: an array with any that apply, e.g.:
     • "has_signage"
     • "visible_customers"
     • "multiple_employees"
     • "perishable_stock"
     • "non_perishable_stock"
     • "seating_area"
     • "cooking_equipment"
     • "refrigeration"

6. Authenticity & duplicates
   - `authenticity_flag`: "looks_genuine", "looks_like_stock_photo", or "unclear"
   - `duplicate_flag`: "new_angle_or_scene" or "possible_duplicate_of_previous"

7. Photo note (internal)
   - `photo_note`: 2–3 sentences summarizing what this photo suggests about:
     • how active or quiet the business seems,
     • how established or improvised it appears,
     • any obvious strength or concern.
   - This is **for internal use only** and will NOT be shown directly to the customer.

8. Coaching tips
   - 1–2 short, actionable suggestions related to what you see (e.g., better product grouping, clearer prices, improved display). These will be paraphrased by the business partner agent.

GENERAL RULES
- Be specific and practical; avoid generic advice.
- Be conservative: do not over-interpret unclear images.
- If a photo looks like a stock image or does not seem to match a real small business, mark `authenticity_flag = "looks_like_stock_photo"` and mention your concern in the photo_note."""

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
                        "text": f"Analyze this business photo. Context: {context_str}\n\nProvide your analysis in this exact format:\nCleanliness: [score]/10\nOrganization: [score]/10\nStock Level: [low/medium/high]\nBusiness Layout Type: [street_stall|market_stall|small_shop|food_stand|salon_or_barbershop|workshop|home_based_other|cannot_tell]\nEvidence Flags: [has_signage, visible_customers, multiple_employees, perishable_stock, non_perishable_stock, seating_area, cooking_equipment, refrigeration, etc.]\nAuthenticity Flag: [looks_genuine|looks_like_stock_photo|unclear]\nDuplicate Flag: [new_angle_or_scene|possible_duplicate_of_previous]\nPhoto Note (internal): [2-3 sentences about business activity, establishment level, strengths/concerns]\nObservations:\n- [observation 1]\n- [observation 2]\nCoaching Tips:\n- [tip 1]\n- [tip 2]",
                    },
                ]
            ),
        ]

        langfuse_context.update_current_observation(
            input={"photo_index": photo_index, "business_context": business_context},
            metadata={"agent": "business_partner", "type": "photo_analysis", "model": "claude-sonnet-4-20250514"},
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
        business_layout_type = "cannot_tell"
        evidence_flags = []
        authenticity_flag = "unclear"
        duplicate_flag = "new_angle_or_scene"
        photo_note = None
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
            
            elif line.lower().startswith("business_layout_type:") or line.lower().startswith("layout type:"):
                layout = line.split(":")[1].strip().lower()
                valid_layouts = ["street_stall", "market_stall", "small_shop", "food_stand", "salon_or_barbershop", "workshop", "home_based_other", "cannot_tell"]
                if layout in valid_layouts:
                    business_layout_type = layout
            
            elif line.lower().startswith("evidence_flags:") or line.lower().startswith("evidence:"):
                # Parse comma-separated flags or list format
                flags_text = line.split(":")[1].strip()
                # Remove brackets if present
                flags_text = flags_text.strip("[]")
                # Split by comma
                flags = [f.strip().strip('"').strip("'") for f in flags_text.split(",")]
                evidence_flags = [f for f in flags if f]
            
            elif line.lower().startswith("authenticity flag:"):
                auth = line.split(":")[1].strip().lower()
                if auth in ["looks_genuine", "looks_like_stock_photo", "unclear"]:
                    authenticity_flag = auth
            
            elif line.lower().startswith("duplicate flag:"):
                dup = line.split(":")[1].strip().lower()
                if dup in ["new_angle_or_scene", "possible_duplicate_of_previous"]:
                    duplicate_flag = dup
            
            elif line.lower().startswith("photo note") and ":" in line:
                # Extract photo note (may span multiple lines)
                note_text = line.split(":", 1)[1].strip()
                if note_text:
                    photo_note = note_text

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
            # Also collect photo note if it continues on next lines
            elif current_section is None and photo_note and not line.startswith(("Cleanliness", "Organization", "Stock", "Business", "Evidence", "Authenticity", "Duplicate", "Observations", "Coaching")):
                # Might be continuation of photo note
                if not any(line.lower().startswith(keyword) for keyword in ["cleanliness", "organization", "stock", "business", "evidence", "authenticity", "duplicate", "observations", "coaching"]):
                    if photo_note:
                        photo_note += " " + line

        return PhotoInsight(
            photo_index=photo_index,
            cleanliness_score=cleanliness_score,
            organization_score=organization_score,
            stock_level=stock_level,
            business_layout_type=business_layout_type,
            evidence_flags=evidence_flags if evidence_flags else [],
            authenticity_flag=authenticity_flag,
            duplicate_flag=duplicate_flag,
            photo_note=photo_note,
            insights=observations if observations else ["Photo analyzed successfully"],
            coaching_tips=coaching_tips if coaching_tips else ["Continue maintaining your business well"],
        )

    @observe(name="business-partner-agent-extract-info")
    def extract_business_info(self, state: BusinessPartnerState) -> Dict:
        """
        Extract structured business information from conversation messages.
        
        Uses the LLM to parse the conversation and extract:
        - business_type, location, years_operating, num_employees
        - monthly_revenue, monthly_expenses, loan_purpose
        """
        messages = state.get("messages", [])
        if not messages:
            return {}
        
        # Build conversation context for extraction
        # IMPORTANT: Look at ALL messages to catch information from earlier in the conversation
        # This is critical to prevent looping - we need to see what was already said
        conversation_text = ""
        user_message_count = 0
        for msg in messages:
            if hasattr(msg, "content"):
                # Check if it's a HumanMessage
                from langchain_core.messages import HumanMessage
                is_user = isinstance(msg, HumanMessage)
                role = "User" if is_user else "Assistant"
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                conversation_text += f"{role}: {content}\n"
                if is_user:
                    user_message_count += 1
        
        # Only extract if we have user messages
        if user_message_count == 0:
            return {}
        
        extraction_prompt = """Extract business information from this conversation. Return ONLY a JSON object with the following fields (use null if not mentioned):
{
  "business_type": "string or null",
  "location": "string or null", 
  "years_operating": "integer or null",
  "num_employees": "integer or null",
  "monthly_revenue": "float or null",
  "monthly_expenses": "float or null",
  "loan_purpose": "string or null"
}

Conversation:
""" + conversation_text + """

Return ONLY the JSON object, no other text:"""

        try:
            extraction_messages = [
                SystemMessage(content="You are a data extraction assistant. Extract business information from conversations and return only valid JSON."),
                HumanMessage(content=extraction_prompt)
            ]
            
            response = self.llm.invoke(extraction_messages)
            extracted_text = response.content.strip()
            
            # Remove markdown code blocks if present
            if extracted_text.startswith("```json"):
                extracted_text = extracted_text[7:]
            if extracted_text.startswith("```"):
                extracted_text = extracted_text[3:]
            if extracted_text.endswith("```"):
                extracted_text = extracted_text[:-3]
            extracted_text = extracted_text.strip()
            
            import json
            extracted_data = json.loads(extracted_text)
            
            # Update fields if extraction found values (even if state already has them)
            # This ensures we capture information from the latest messages
            updates = {}
            for key, value in extracted_data.items():
                if value is not None:  # If extraction found a value, use it
                    updates[key] = value
            
            if updates:
                print(f"[BUSINESS-PARTNER] Extracted business info: {updates}")
            
            return updates
            
        except Exception as e:
            print(f"[BUSINESS-PARTNER] Error extracting business info: {e}")
            return {}

    def _check_if_info_complete(self, state: BusinessPartnerState) -> bool:
        """Check if we have enough business info to proceed to underwriting."""
        required_fields = ["business_type", "location", "monthly_revenue", "loan_purpose"]

        return all(state.get(field) is not None for field in required_fields)
    
    def _mark_task_complete(self, state: BusinessPartnerState, task_id: str) -> None:
        """Mark a task as completed in the state."""
        completed_tasks = state.get("completed_tasks", [])
        if task_id not in completed_tasks:
            completed_tasks.append(task_id)
            state["completed_tasks"] = completed_tasks
            print(f"[BUSINESS-PARTNER] Task completed: {task_id}")
    
    def _check_all_tasks_complete(self, state: BusinessPartnerState) -> bool:
        """Check if all required tasks are completed."""
        required_tasks = state.get("required_tasks", [])
        completed_tasks = set(state.get("completed_tasks", []))
        
        return all(task in completed_tasks for task in required_tasks)

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
        # - All required tasks are completed (task-based check)
        # - At least one photo has been analyzed
        # - Loan hasn't been offered yet

        all_tasks_complete = self._check_all_tasks_complete(state)
        photos_analyzed = len(state.get("photo_insights", [])) > 0
        loan_offered = state.get("loan_offered", False)

        return all_tasks_complete and photos_analyzed and not loan_offered

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

    @observe(name="business-partner-agent-generate-response")
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
        
        # Add current business info to context so agent knows what's already collected
        # This is CRITICAL to prevent looping - the agent must see what it already knows
        business_info = []
        if state.get("business_type"):
            business_info.append(f"Business type: {state['business_type']}")
        if state.get("location"):
            business_info.append(f"Location: {state['location']}")
        if state.get("years_operating"):
            business_info.append(f"Years operating: {state['years_operating']}")
        if state.get("num_employees"):
            business_info.append(f"Employees: {state['num_employees']}")
        if state.get("monthly_revenue"):
            business_info.append(f"Monthly revenue: {state['monthly_revenue']:,.0f} pesos")
        if state.get("monthly_expenses"):
            business_info.append(f"Monthly expenses: {state['monthly_expenses']:,.0f} pesos")
        if state.get("loan_purpose"):
            business_info.append(f"Loan purpose: {state['loan_purpose']}")
        if state.get("business_name"):
            business_info.append(f"Business name: {state['business_name']}")
        
        if business_info:
            # Make this section VERY prominent - it's critical to prevent looping
            context_additions.append("\n" + "="*60)
            context_additions.append("[ALREADY COLLECTED INFORMATION - DO NOT ASK FOR THIS AGAIN]")
            context_additions.append("="*60)
            context_additions.append("\n".join(business_info))
            context_additions.append("\n" + "="*60)
            context_additions.append("**CRITICAL INSTRUCTION**: You MUST check this section before asking any questions.")
            context_additions.append("If information is listed above, you already have it. DO NOT ask for it again.")
            context_additions.append("Instead, acknowledge what you know and move forward with the next step.")
            context_additions.append("="*60)

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
        
        # Add coaching advice if available (from background coaching agent)
        coaching_advice = state.get("coaching_advice")
        if coaching_advice:
            context_additions.append(
                f"\n[COACHING ADVICE FROM SPECIALIST]\n"
                f"{coaching_advice}\n"
                f"Integrate this advice naturally into your response to the customer."
            )

        # Append context to system prompt
        # CRITICAL: Put the "ALREADY COLLECTED INFORMATION" section FIRST, before the main prompt
        # This ensures the agent sees it prominently
        if context_additions:
            # Find the "ALREADY COLLECTED INFORMATION" section and move it to the top
            collected_info_section = None
            other_sections = []
            for section in context_additions:
                if "ALREADY COLLECTED INFORMATION" in section:
                    collected_info_section = section
                else:
                    other_sections.append(section)
            
            # Build prompt with collected info FIRST
            if collected_info_section:
                full_system_prompt = f"{collected_info_section}\n\n{system_prompt}"
                if other_sections:
                    full_system_prompt += "\n\n" + "\n".join(other_sections)
            else:
                full_system_prompt = system_prompt + "\n\n" + "\n".join(context_additions)
        else:
            full_system_prompt = system_prompt

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
            metadata={"agent": "business_partner", "model": "claude-sonnet-4-20250514"},
        )

        response = self.llm.invoke(messages_for_llm)

        # Update Langfuse with output
        langfuse_context.update_current_observation(output={"response_length": len(response.content)})

        return response.content

    @observe(name="business-partner-agent-process")
    def process(self, state: BusinessPartnerState) -> Dict:
        """
        Main entry point for the Business Partner Agent.

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

        # Extract business information from conversation messages
        extracted_info = self.extract_business_info(state)
        if extracted_info:
            # Update state with extracted information
            # IMPORTANT: Always update if extraction found a value (even if state already has it)
            # This ensures we capture information from the latest messages
            for key, value in extracted_info.items():
                if value is not None:  # Only update if extraction found a value
                    state[key] = value
                    print(f"[BUSINESS-PARTNER] Updated state.{key} = {value}")
            
            # Mark tasks as complete based on extracted info
            if "business_type" in extracted_info or "location" in extracted_info or "years_operating" in extracted_info or "num_employees" in extracted_info:
                self._mark_task_complete(state, "capture_business_profile")
            if "monthly_revenue" in extracted_info or "monthly_expenses" in extracted_info or "loan_purpose" in extracted_info:
                self._mark_task_complete(state, "capture_business_financials")
        
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
            
            # Mark photo-related tasks as complete
            if num_photos > 0:
                self._mark_task_complete(state, "capture_business_photos")
            if len(photo_insights) > 0:
                self._mark_task_complete(state, "photo_analysis_complete")

        # Check info completeness
        info_complete = self._check_if_info_complete(state)
        
        # Mark eligibility task as complete if we have basic info (simplified check)
        if state.get("business_type") and state.get("location"):
            self._mark_task_complete(state, "confirm_eligibility")

        # Check for loan acceptance
        if state.get("loan_offered") and not state.get("loan_accepted"):
            if self._check_if_loan_accepted(state.get("messages", [])):
                state["loan_accepted"] = True

        # Update phase based on state
        # If underwriting has returned an offer, move to "offer" phase
        if state.get("loan_offer") and state.get("phase") == "onboarding":
            state["phase"] = "offer"
        
        # If loan is accepted and disbursed, move to "post_disbursement" phase
        if state.get("loan_accepted") and state.get("disbursement_status") == "completed":
            if state.get("phase") in ["onboarding", "offer"]:
                state["phase"] = "post_disbursement"
        
        # If there's a recovery status indicating delinquency, move to "delinquent" phase
        if state.get("recovery_status") and state.get("recovery_status") not in ["resolved", "escalated", None]:
            if state.get("phase") == "post_disbursement":
                state["phase"] = "delinquent"

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
            "phase": state.get("phase", "onboarding"),  # Include phase in result
            "completed_tasks": state.get("completed_tasks", []),  # Include completed tasks
        }
        
        # Include extracted business info in result so it updates state
        if extracted_info:
            result.update(extracted_info)
        
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

