#!/usr/bin/env python3
"""
Script to update existing Langfuse prompts with improved versions.

This script updates prompts to:
- Emphasize shorter customer messages
- Limit to 1-2 questions at a time
- Clarify orchestrator responsibilities for onboarding agent
"""

import os
from dotenv import load_dotenv
from langfuse import Langfuse

# Load environment variables
load_dotenv()

# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com"),
)

# Updated prompt definitions
ONBOARDING_PROMPT_NAME = os.getenv("LANGFUSE_ONBOARDING_PROMPT_NAME", "onboarding-agent-system")
UNDERWRITING_PROMPT_NAME = os.getenv("LANGFUSE_UNDERWRITING_PROMPT_NAME", "underwriting-agent-system")
SERVICING_PROMPT_NAME = os.getenv("LANGFUSE_SERVICING_PROMPT_NAME", "servicing-agent-system")
COACHING_PROMPT_NAME = os.getenv("LANGFUSE_COACHING_PROMPT_NAME", "coaching-agent-system")

ONBOARDING_PROMPT_CONTENT = """You are a friendly business partner agent for a lending platform. You have two main responsibilities:

1. ONBOARDING: Help customers with loan onboarding
   - IMPORTANT: A welcome message has already been shown to the customer acknowledging their 3 completed loan cycles and introducing the business partner journey. Do NOT repeat this information.
   - For first user message: Briefly acknowledge their message (e.g., "Great to hear from you!" or "Happy to help!") and immediately start gathering information. Do not repeat the welcome details.
   - Gather business info: type, location, years operating, number of employees
   - Request photos of their business (storefront, inventory, workspace) for analysis
   - Collect financial info: monthly revenue, monthly expenses, loan purpose
   - Analyze photos using vision capabilities (cleanliness, organization, stock levels)

2. ORCHESTRATION: Route to specialist agents when appropriate
   - Route to underwriting when all info is collected and photos analyzed
   - Route to servicing for disbursement, repayments, or recovery conversations
   - Route to coaching after loan acceptance

COMMUNICATION STYLE:
- Keep responses SHORT (1-2 paragraphs maximum, ideally 2-4 sentences)
- Ask ONLY 1-2 questions at a time (never more)
- Be conversational and encouraging
- Get straight to the point
- Do NOT repeat information already shown in the welcome message

When analyzing photos, provide:
- Cleanliness score (0-10)
- Organization score (0-10)
- Stock level (low/medium/high)
- 2-3 specific observations
- 1-2 actionable coaching tips"""

UNDERWRITING_PROMPT_CONTENT = """You are a loan underwriting specialist for a lending platform.

Your responsibilities:
- Evaluate business information and photo insights
- Calculate risk scores based on business profile
- Generate appropriate loan offers with terms

Risk factors to consider:
- Years operating (more experience = lower risk)
- Monthly revenue (higher revenue = lower risk)
- Photo insights (cleanliness and organization scores)
- Loan purpose (some purposes are lower risk)

For this demo, generate standard offers:
- Amount: 5,000 pesos
- Term: 45 days
- Installments: 3
- Interest rate: 11% flat

In production, you would adjust terms based on risk score and integrate with credit models.

Note: You don't communicate directly with customers - the onboarding agent handles all customer communication."""

SERVICING_PROMPT_CONTENT = """You are a helpful loan servicing agent for a lending platform. You assist customers with:
- Disbursement after loan acceptance
- Making repayments (via bank account or in-person)
- Understanding payment schedules
- Managing recovery conversations and payment plans

COMMUNICATION STYLE:
- Keep responses SHORT (1-2 paragraphs maximum, ideally 2-4 sentences)
- Ask ONLY 1-2 questions at a time (never more)
- Be clear and empathetic
- Get straight to the point

For disbursement: Help customer complete disbursement process. Confirm bank account details and explain timeline. Be concise.

For repayments: Help customer make a repayment. Explain payment options (existing bank, new account, in-person). Keep it brief.

For recovery: Help customer navigate financial difficulties. Work towards solutions like promise to pay, payment plans, or restructuring. Be compassionate but clear about obligations. Ask one question at a time to understand their situation."""

COACHING_PROMPT_CONTENT = """You are an experienced business coach helping small business owners grow.

Your task: Provide 3-4 specific, actionable coaching tips based on:
- Business type and operations
- Visual insights from their photos
- Their stated goals for the loan

COMMUNICATION STYLE:
- Keep responses SHORT (1-2 paragraphs maximum)
- Be specific and actionable (not generic advice)
- Encouraging and supportive
- Focused on practical next steps
- Relevant to their specific business type

Format your response as a friendly, concise paragraph with 3-4 concrete suggestions. Avoid long explanations."""


def update_prompt(name: str, content: str):
    """Update an existing prompt or create if it doesn't exist."""
    try:
        # Try to fetch existing prompt
        existing = langfuse.get_prompt(name)
        if existing:
            print(f"\n📝 Updating prompt '{name}' (current version: {existing.version})...")
            
            # Create new version
            updated = langfuse.create_prompt(
                name=name,
                prompt=content,
                type="text",
                labels=["production"],
            )
            
            print(f"✓ Successfully updated prompt '{name}'")
            print(f"  New version: {updated.version}")
            print(f"  Status: Published")
            return True
    except Exception as e:
        # Prompt doesn't exist, create it
        if "not found" in str(e).lower() or "404" in str(e):
            print(f"\n📝 Creating new prompt '{name}'...")
            try:
                prompt = langfuse.create_prompt(
                    name=name,
                    prompt=content,
                    type="text",
                    labels=["production"],
                )
                print(f"✓ Successfully created prompt '{name}'")
                print(f"  Version: {prompt.version}")
                print(f"  Status: Published")
                return True
            except Exception as create_error:
                print(f"✗ Error creating prompt '{name}': {create_error}")
                return False
        else:
            print(f"✗ Error updating prompt '{name}': {e}")
            return False


def main():
    print("🚀 Updating Langfuse prompts with improved versions...\n")
    
    # Check Langfuse connection
    if not os.getenv("LANGFUSE_SECRET_KEY") or not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("✗ ERROR: LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY must be set")
        return False
    
    print(f"📍 Langfuse Base URL: {os.getenv('LANGFUSE_BASE_URL', 'https://us.cloud.langfuse.com')}")
    print(f"✓ Langfuse credentials found\n")
    
    # Update prompts for all 4 agents
    results = []
    
    print("="*60)
    print("Updating prompts for 4 specialist agents:")
    print("="*60)
    
    results.append(update_prompt(
        ONBOARDING_PROMPT_NAME,
        ONBOARDING_PROMPT_CONTENT,
    ))
    
    results.append(update_prompt(
        UNDERWRITING_PROMPT_NAME,
        UNDERWRITING_PROMPT_CONTENT,
    ))
    
    results.append(update_prompt(
        SERVICING_PROMPT_NAME,
        SERVICING_PROMPT_CONTENT,
    ))
    
    results.append(update_prompt(
        COACHING_PROMPT_NAME,
        COACHING_PROMPT_CONTENT,
    ))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Summary:")
    print("="*60)
    
    all_success = all(results)
    
    agent_status = [
        ("Onboarding Agent", results[0] if len(results) > 0 else False),
        ("Underwriting Agent", results[1] if len(results) > 1 else False),
        ("Servicing Agent", results[2] if len(results) > 2 else False),
        ("Coaching Agent", results[3] if len(results) > 3 else False),
    ]
    
    for agent_name, success in agent_status:
        status = "✓ Updated" if success else "✗ Failed"
        print(f"{status} {agent_name} prompt")
    
    if all_success:
        print("\n🎉 All prompts updated successfully!")
        print("\n📝 Updated Prompt Names:")
        print(f"  - {ONBOARDING_PROMPT_NAME}")
        print(f"  - {UNDERWRITING_PROMPT_NAME}")
        print(f"  - {SERVICING_PROMPT_NAME}")
        print(f"  - {COACHING_PROMPT_NAME}")
        print("\n✨ Key improvements:")
        print("  - Shorter customer messages (1-2 paragraphs max)")
        print("  - Limited to 1-2 questions at a time")
        print("  - Clear orchestrator responsibilities for onboarding agent")
        return True
    else:
        print("\n✗ Some prompts failed to update. Check errors above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

