"""
Servicing Agent - Handles post-loan customer support and loan management.

This agent:
- Processes disbursement after loan acceptance (mocked)
- Helps customers make repayments (mocked) via existing bank, new account, or in-person
- Explains payment schedules and repayment behavior implications
- Manages recovery conversations (promise to pay, payment plans, etc.)
- Helps customers understand their customer journey based on repayment behavior
"""

import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
import threading

from state import BusinessPartnerState
from db import update_loan_status


class ServicingAgent:
    """Agent specialized in loan servicing, repayments, and recovery."""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=1024,
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

    def get_system_prompt(self, servicing_type: str = "general") -> str:
        """
        Fetch system prompt from Langfuse with caching.
        Falls back to default if Langfuse fetch fails.
        
        Args:
            servicing_type: Type of servicing interaction ('disbursement', 'repayment', 'recovery', 'general')
        """
        import time

        now = time.time()

        # Return cached prompt if valid
        if self.system_prompt and self.prompt_cache_time and (now - self.prompt_cache_time < self.prompt_ttl):
            print(f"[LANGFUSE-SERVICING] Using cached prompt (age: {int(now - self.prompt_cache_time)}s)")
            return self.system_prompt

        # Try to fetch from Langfuse
        try:
            prompt_name = os.getenv("LANGFUSE_SERVICING_PROMPT_NAME", "servicing-agent-system")
            print(f"[LANGFUSE-SERVICING] Fetching prompt: {prompt_name}")

            prompt_obj = self.langfuse.get_prompt(prompt_name)

            if prompt_obj and hasattr(prompt_obj, "prompt"):
                self.system_prompt = prompt_obj.prompt
                self.prompt_cache_time = now
                self.prompt_name = prompt_name
                self.prompt_version = getattr(prompt_obj, "version", None)
                print(f"[LANGFUSE-SERVICING] ✓ Prompt fetched successfully (v{prompt_obj.version})")
                return self.system_prompt
            else:
                print(f"[LANGFUSE-SERVICING] ✗ Prompt object missing 'prompt' property")

        except Exception as e:
            print(f"[LANGFUSE-SERVICING] ✗ Error fetching prompt: {e}")

        # Fallback to default prompt
        print("[LANGFUSE-SERVICING] → Using fallback prompt")
        self.prompt_name = None
        self.prompt_version = None
        return self._get_fallback_prompt(servicing_type)

    def _get_fallback_prompt(self, servicing_type: str = "general") -> str:
        """Fallback system prompt if Langfuse is unavailable."""
        base_prompt = """You are a helpful loan servicing agent for a lending platform. You assist customers with:
- Disbursement after loan acceptance
- Making repayments (via bank account or in-person)
- Understanding payment schedules
- Managing recovery conversations and payment plans

Be:
- Clear and empathetic
- Helpful in explaining processes
- Supportive during difficult financial situations
- Professional and solution-oriented

Keep responses concise (2-3 paragraphs max)."""

        if servicing_type == "disbursement":
            return base_prompt + "\n\nFocus: Help customer complete disbursement process. Confirm bank account details and explain timeline."
        elif servicing_type == "repayment":
            return base_prompt + "\n\nFocus: Help customer make a repayment. Explain payment options (existing bank, new account, in-person)."
        elif servicing_type == "recovery":
            return base_prompt + "\n\nFocus: Help customer navigate financial difficulties. Work towards solutions like promise to pay, payment plans, or restructuring."
        else:
            return base_prompt

    @observe(name="servicing-agent-process-disbursement")
    def process_disbursement(self, state: BusinessPartnerState) -> Dict:
        """
        Process loan disbursement after acceptance (mocked).
        
        In production, this would:
        - Verify bank account details
        - Initiate transfer via payment gateway
        - Send confirmation notifications
        """
        loan_offer = state.get("loan_offer")
        if not loan_offer:
            return {
                "disbursement_status": "error",
                "disbursement_info": {"error": "No loan offer found"}
            }

        # Mock disbursement - in production, this would call payment API
        disbursement_info = {
            "amount": loan_offer.get("amount"),
            "status": "pending",
            "initiated_at": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(hours=2)).isoformat(),
            "bank_account": state.get("bank_account", "***1234"),  # Would come from user profile
            "reference_number": f"DISP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        }

        # In production: Call disbursement API
        # response = requests.post("https://api.lender.com/disburse", ...)
        # disbursement_info = response.json()

        print(f"[SERVICING] Mock disbursement initiated: {disbursement_info['reference_number']}")

        return {
            "disbursement_status": "initiated",
            "disbursement_info": disbursement_info,
        }

    @observe(name="servicing-agent-process-repayment")
    def process_repayment(self, state: BusinessPartnerState, repayment_method: str, amount: Optional[float] = None) -> Dict:
        """
        Process a repayment (mocked).
        
        Args:
            state: Current state
            repayment_method: 'existing_bank', 'new_account', or 'in_person'
            amount: Optional repayment amount (defaults to installment amount)
        """
        loan_offer = state.get("loan_offer")
        if not loan_offer:
            return {
                "repayment_status": "error",
                "repayment_info": {"error": "No loan offer found"}
            }

        # Determine repayment amount
        if amount is None:
            amount = loan_offer.get("installment_amount", loan_offer.get("amount") / loan_offer.get("installments", 1))

        # Mock repayment processing
        repayment_info = {
            "method": repayment_method,
            "amount": amount,
            "status": "processing",
            "initiated_at": datetime.now().isoformat(),
            "reference_number": f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        }

        if repayment_method == "existing_bank":
            repayment_info["bank_account"] = state.get("bank_account", "***1234")
            repayment_info["estimated_completion"] = (datetime.now() + timedelta(hours=1)).isoformat()
        elif repayment_method == "new_account":
            # Would collect bank account details from user
            repayment_info["bank_account"] = "pending_verification"
            repayment_info["estimated_completion"] = (datetime.now() + timedelta(hours=24)).isoformat()
        elif repayment_method == "in_person":
            repayment_info["location"] = "Visit any partner location"
            repayment_info["instructions"] = "Bring valid ID and reference number"
            repayment_info["estimated_completion"] = "immediate"

        # In production: Call payment processing API
        # response = requests.post("https://api.lender.com/repayment", ...)

        print(f"[SERVICING] Mock repayment initiated: {repayment_info['reference_number']} via {repayment_method}")

        return {
            "repayment_status": "processing",
            "repayment_info": repayment_info,
        }

    @observe(name="servicing-agent-generate-payment-schedule")
    def generate_payment_schedule(self, state: BusinessPartnerState) -> Dict:
        """
        Generate and explain payment schedule based on loan offer.
        """
        loan_offer = state.get("loan_offer")
        if not loan_offer:
            return {"payment_schedule": None}

        installments = loan_offer.get("installments", 1)
        term_days = loan_offer.get("term_days", 45)
        installment_amount = loan_offer.get("installment_amount", 0)
        days_between = term_days / installments

        # Calculate payment dates (starting from disbursement or today)
        disbursement_date = state.get("disbursement_info", {}).get("initiated_at")
        if disbursement_date:
            try:
                start_date = datetime.fromisoformat(disbursement_date.replace('Z', '+00:00'))
            except:
                start_date = datetime.now()
        else:
            start_date = datetime.now()

        schedule = []
        for i in range(installments):
            due_date = start_date + timedelta(days=days_between * (i + 1))
            schedule.append({
                "installment_number": i + 1,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "amount": installment_amount,
                "status": "pending"  # Would check actual payment status in production
            })

        payment_schedule = {
            "total_installments": installments,
            "installment_amount": installment_amount,
            "total_amount": loan_offer.get("total_repayment", 0),
            "schedule": schedule,
            "days_between_payments": int(days_between),
        }

        return {"payment_schedule": payment_schedule}

    @observe(name="servicing-agent-explain-repayment-impact")
    def explain_repayment_impact(self, state: BusinessPartnerState) -> str:
        """
        Explain how repayment behavior affects customer journey and future loan eligibility.
        """
        system_prompt = self.get_system_prompt("repayment")
        
        loan_offer = state.get("loan_offer")
        payment_schedule = state.get("payment_schedule", {})
        
        context = f"""Loan Details:
- Amount: {loan_offer.get('amount', 0):,.0f} pesos
- Term: {loan_offer.get('term_days', 0)} days
- Installments: {loan_offer.get('installments', 0)}
- Payment Amount: {loan_offer.get('installment_amount', 0):,.2f} pesos per installment

Payment Schedule:
{self._format_payment_schedule(payment_schedule)}

Explain to the customer:
1. How on-time payments improve their credit profile
2. How payment behavior affects future loan eligibility
3. Benefits of maintaining good repayment history
4. Consequences of late or missed payments (if applicable)
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context),
        ]

        langfuse_context.update_current_observation(
            input={"loan_amount": loan_offer.get('amount'), "installments": loan_offer.get('installments')},
            metadata={"agent": "servicing", "type": "repayment_impact", "model": "claude-sonnet-4-20250514"},
        )

        response = self.llm.invoke(messages)
        explanation = response.content

        langfuse_context.update_current_observation(output={"explanation_length": len(explanation)})

        return explanation

    def _format_payment_schedule(self, payment_schedule: Dict) -> str:
        """Format payment schedule for display."""
        if not payment_schedule or not payment_schedule.get("schedule"):
            return "No payment schedule available"
        
        lines = []
        for payment in payment_schedule.get("schedule", []):
            lines.append(f"Payment {payment['installment_number']}: {payment['amount']:,.2f} pesos due {payment['due_date']}")
        
        return "\n".join(lines)

    @observe(name="servicing-agent-handle-recovery")
    def handle_recovery_conversation(self, state: BusinessPartnerState, user_message: str) -> Dict:
        """
        Handle recovery conversations - work with customers to resolve payment issues.
        
        This agent helps customers:
        - Understand their situation
        - Explore options (promise to pay, payment plans, restructuring)
        - Navigate towards resolution
        """
        system_prompt = self.get_system_prompt("recovery")
        
        loan_offer = state.get("loan_offer")
        payment_schedule = state.get("payment_schedule", {})
        recovery_status = state.get("recovery_status", "initial")
        
        outstanding = self._calculate_outstanding(state)
        context = f"""Customer Situation:
- Loan Amount: {loan_offer.get('amount', 0):,.0f} pesos
- Outstanding Balance: {outstanding:,.2f} pesos
- Current Status: {recovery_status}

Payment Schedule:
{self._format_payment_schedule(payment_schedule)}

Customer Message: {user_message}

Your task:
1. Listen empathetically to their circumstances
2. Explain available options (promise to pay, payment plan, restructuring)
3. Help them understand the implications of each option
4. Work towards a mutually agreeable solution
5. Be supportive but clear about obligations

Be compassionate but professional. Focus on finding solutions."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context),
        ]

        langfuse_context.update_current_observation(
            input={"recovery_status": recovery_status, "outstanding": self._calculate_outstanding(state)},
            metadata={"agent": "servicing", "type": "recovery", "model": "claude-sonnet-4-20250514"},
        )

        response = self.llm.invoke(messages)
        recovery_response = response.content

        # Determine if we've reached a resolution
        recovery_info = {
            "status": recovery_status,
            "conversation_active": True,
            "last_interaction": datetime.now().isoformat(),
        }

        # Check if customer agreed to a solution (simple keyword detection - in production, use more sophisticated NLP)
        response_lower = recovery_response.lower()
        if any(keyword in response_lower for keyword in ["promise to pay", "payment plan", "agreed", "accepted"]):
            recovery_info["status"] = "resolution_pending"
            recovery_info["resolution_type"] = self._detect_resolution_type(recovery_response)

        langfuse_context.update_current_observation(
            output={"response_length": len(recovery_response), "resolution_reached": recovery_info.get("status") == "resolution_pending"}
        )

        return {
            "recovery_status": recovery_info["status"],
            "recovery_info": recovery_info,
            "recovery_response": recovery_response,  # This will be added to conversation by conversation agent
        }

    def _calculate_outstanding(self, state: BusinessPartnerState) -> float:
        """Calculate outstanding loan balance (mocked - would query actual payments in production)."""
        loan_offer = state.get("loan_offer")
        if not loan_offer:
            return 0.0
        
        total_repayment = loan_offer.get("total_repayment", loan_offer.get("amount", 0))
        # In production, would subtract actual payments made
        # For now, return full amount as outstanding
        return total_repayment

    def _detect_resolution_type(self, response: str) -> str:
        """Detect what type of resolution was reached (simple heuristic)."""
        response_lower = response.lower()
        if "promise to pay" in response_lower:
            return "promise_to_pay"
        elif "payment plan" in response_lower or "installment plan" in response_lower:
            return "payment_plan"
        elif "restructure" in response_lower or "restructuring" in response_lower:
            return "restructuring"
        else:
            return "other"

    @observe(name="servicing-agent-process")
    def process(self, state: BusinessPartnerState) -> Dict:
        """
        Main entry point for the Servicing Agent.
        
        Determines what type of servicing interaction is needed based on state and messages.
        """
        messages = state.get("messages", [])
        last_user_message = None
        
        # Get last user message if available
        if messages:
            for msg in reversed(messages):
                if hasattr(msg, "content") and isinstance(msg.content, str):
                    # Check if it's a user message (simple check)
                    if not hasattr(msg, "type") or msg.type == "human":
                        last_user_message = msg.content
                        break

        servicing_type = state.get("servicing_type", "general")
        result = {}

        if servicing_type == "disbursement":
            # Process disbursement
            disbursement_result = self.process_disbursement(state)
            result.update(disbursement_result)
            
            # Generate payment schedule after disbursement
            schedule_result = self.generate_payment_schedule(state)
            result.update(schedule_result)
            
        elif servicing_type == "repayment":
            # Determine repayment method from user message or state
            repayment_method = state.get("repayment_method", "existing_bank")
            if last_user_message:
                msg_lower = last_user_message.lower()
                if "new account" in msg_lower or "add account" in msg_lower:
                    repayment_method = "new_account"
                elif "in person" in msg_lower or "in-person" in msg_lower or "cash" in msg_lower:
                    repayment_method = "in_person"
                elif "existing" in msg_lower or "current" in msg_lower:
                    repayment_method = "existing_bank"
            
            repayment_result = self.process_repayment(state, repayment_method)
            result.update(repayment_result)
            
        elif servicing_type == "payment_schedule":
            # Generate and explain payment schedule
            schedule_result = self.generate_payment_schedule(state)
            result.update(schedule_result)
            
        elif servicing_type == "repayment_impact":
            # Explain repayment impact
            explanation = self.explain_repayment_impact(state)
            result["repayment_impact_explanation"] = explanation
            
        elif servicing_type == "recovery":
            # Handle recovery conversation
            user_message = last_user_message or "I'm having trouble making my payment"
            recovery_result = self.handle_recovery_conversation(state, user_message)
            result.update(recovery_result)
            
        else:
            # General servicing - determine what's needed
            if state.get("loan_accepted") and not state.get("disbursement_status"):
                # Need to process disbursement
                disbursement_result = self.process_disbursement(state)
                result.update(disbursement_result)
                schedule_result = self.generate_payment_schedule(state)
                result.update(schedule_result)
            elif last_user_message:
                # Try to detect intent
                msg_lower = last_user_message.lower()
                if any(keyword in msg_lower for keyword in ["payment", "repay", "installment"]):
                    repayment_method = "existing_bank"
                    if "new account" in msg_lower:
                        repayment_method = "new_account"
                    elif "in person" in msg_lower or "cash" in msg_lower:
                        repayment_method = "in_person"
                    repayment_result = self.process_repayment(state, repayment_method)
                    result.update(repayment_result)
                elif any(keyword in msg_lower for keyword in ["schedule", "when", "due", "payment dates"]):
                    schedule_result = self.generate_payment_schedule(state)
                    result.update(schedule_result)
                elif any(keyword in msg_lower for keyword in ["trouble", "difficulty", "can't pay", "late", "missed"]):
                    recovery_result = self.handle_recovery_conversation(state, last_user_message)
                    result.update(recovery_result)

        # Update loan status in database if needed (async)
        conversation_id = state.get('conversation_id')
        if conversation_id and result.get("disbursement_status") == "initiated":
            def run_async():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(update_loan_status(conversation_id, "disbursed"))
                finally:
                    loop.close()
            
            thread = threading.Thread(target=run_async)
            thread.daemon = True
            thread.start()

        result["next_agent"] = None  # Return to conversation agent
        return result


# Singleton instance (instantiated after env is loaded)
servicing_agent = None

def initialize_servicing_agent():
    global servicing_agent
    if servicing_agent is None:
        servicing_agent = ServicingAgent()

