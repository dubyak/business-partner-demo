#!/usr/bin/env python3
"""
Script to create Langfuse prompts for all agents.

This script will create prompts for:
1. Onboarding Agent - handles conversation, info gathering, and photo analysis
2. Underwriting Agent - generates loan offers based on risk assessment
3. Servicing Agent - handles disbursement, repayments, and recovery
4. Coaching Agent - provides business advice

Run this after setting up your Langfuse credentials.
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
    host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
)

# Prompt definitions
ONBOARDING_PROMPT_NAME = os.getenv("LANGFUSE_ONBOARDING_PROMPT_NAME", "onboarding-agent-system")
UNDERWRITING_PROMPT_NAME = os.getenv("LANGFUSE_UNDERWRITING_PROMPT_NAME", "underwriting-agent-system")
SERVICING_PROMPT_NAME = os.getenv("LANGFUSE_SERVICING_PROMPT_NAME", "servicing-agent-system")
COACHING_PROMPT_NAME = os.getenv("LANGFUSE_COACHING_PROMPT_NAME", "coaching-agent-system")

ONBOARDING_PROMPT_CONTENT = """You are a friendly business partner agent for a lending platform. Help customers with loan onboarding.

FLOW:
1. Greet and welcome (acknowledge if they've completed previous loan cycles)
2. Gather business info: type, location, years operating, number of employees
3. Request photos of their business (storefront, inventory, workspace) for analysis
4. Collect financial info: monthly revenue, monthly expenses, loan purpose
5. Once all info is collected, route to underwriting for loan offer

Keep responses SHORT (2-3 paragraphs max). Ask 1-2 questions at a time. Be conversational and encouraging.

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

In production, you would adjust terms based on risk score and integrate with credit models."""

SERVICING_PROMPT_CONTENT = """You are a helpful loan servicing agent for a lending platform. You assist customers with:
- Disbursement after loan acceptance
- Making repayments (via bank account or in-person)
- Understanding payment schedules
- Managing recovery conversations and payment plans

Be:
- Clear and empathetic
- Helpful in explaining processes
- Supportive during difficult financial situations
- Professional and solution-oriented

Keep responses concise (2-3 paragraphs max).

For disbursement: Help customer complete disbursement process. Confirm bank account details and explain timeline.

For repayments: Help customer make a repayment. Explain payment options (existing bank, new account, in-person).

For recovery: Help customer navigate financial difficulties. Work towards solutions like promise to pay, payment plans, or restructuring. Be compassionate but clear about obligations."""

COACHING_PROMPT_CONTENT = """You are an experienced business coach helping small business owners grow.

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


def check_or_create_prompt(name: str, content: str, description: str = ""):
    """Check if prompt exists, create if it doesn't."""
    try:
        # Try to fetch existing prompt
        existing = langfuse.get_prompt(name)
        if existing:
            print(f"✓ Prompt '{name}' already exists (version {existing.version})")
            print(f"  Content preview: {existing.prompt[:100]}...")
            return True
    except Exception as e:
        # Prompt doesn't exist, create it
        pass

    try:
        print(f"\n📝 Creating prompt '{name}'...")
        
        # Create new prompt using Langfuse SDK
        # Note: is_active is deprecated, use labels=["production"] instead
        prompt = langfuse.create_prompt(
            name=name,
            prompt=content,
            type="text",  # Prompt type
            labels=["production"],  # Auto-label as production (makes it active)
        )
        
        print(f"✓ Successfully created prompt '{name}'")
        if hasattr(prompt, 'version'):
            print(f"  Version: {prompt.version}")
        print(f"  Status: Published")
        return True
        
    except Exception as e:
        print(f"✗ Error creating prompt '{name}': {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🚀 Setting up Langfuse prompts for all agents...\n")
    
    # Check Langfuse connection
    if not os.getenv("LANGFUSE_SECRET_KEY") or not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("✗ ERROR: LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY must be set")
        print("\nPlease set these environment variables:")
        print("  export LANGFUSE_SECRET_KEY=your_secret_key")
        print("  export LANGFUSE_PUBLIC_KEY=your_public_key")
        return False
    
    print(f"📍 Langfuse Base URL: {os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')}")
    print(f"✓ Langfuse credentials found\n")
    
    # Create prompts for all 4 agents
    results = []
    
    print("="*60)
    print("Creating prompts for 4 specialist agents:")
    print("="*60)
    
    results.append(check_or_create_prompt(
        ONBOARDING_PROMPT_NAME,
        ONBOARDING_PROMPT_CONTENT,
        "Onboarding agent system prompt - handles conversation, info gathering, and photo analysis"
    ))
    
    results.append(check_or_create_prompt(
        UNDERWRITING_PROMPT_NAME,
        UNDERWRITING_PROMPT_CONTENT,
        "Underwriting agent system prompt - generates loan offers based on risk assessment"
    ))
    
    results.append(check_or_create_prompt(
        SERVICING_PROMPT_NAME,
        SERVICING_PROMPT_CONTENT,
        "Servicing agent system prompt - handles disbursement, repayments, and recovery"
    ))
    
    results.append(check_or_create_prompt(
        COACHING_PROMPT_NAME,
        COACHING_PROMPT_CONTENT,
        "Coaching agent system prompt - provides business advice"
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
        status = "✓ Ready" if success else "✗ Failed"
        print(f"{status} {agent_name} prompt")
    
    if all_success:
        print("\n🎉 All prompts are ready!")
        print("\n📝 Prompt Names:")
        print(f"  - {ONBOARDING_PROMPT_NAME}")
        print(f"  - {UNDERWRITING_PROMPT_NAME}")
        print(f"  - {SERVICING_PROMPT_NAME}")
        print(f"  - {COACHING_PROMPT_NAME}")
        return True
    else:
        print("\n✗ Some prompts failed to create. Check errors above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

