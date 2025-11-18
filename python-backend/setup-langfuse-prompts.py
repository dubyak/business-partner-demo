#!/usr/bin/env python3
"""
Script to create Langfuse prompts for all agents.

This script will:
1. Create vision-agent-system prompt (if it doesn't exist)
2. Create coaching-agent-system prompt (if it doesn't exist)
3. Verify business-partner-system prompt exists

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
VISION_PROMPT_NAME = os.getenv("LANGFUSE_VISION_PROMPT_NAME", "vision-agent-system")
COACHING_PROMPT_NAME = os.getenv("LANGFUSE_COACHING_PROMPT_NAME", "coaching-agent-system")
CONVERSATION_PROMPT_NAME = os.getenv("LANGFUSE_PROMPT_NAME", "business-partner-system")

VISION_PROMPT_CONTENT = """You are a business consultant analyzing photos of small businesses.

Your task: Analyze the photo and provide:
1. Cleanliness score (0-10): How clean and well-maintained is the space?
2. Organization score (0-10): How organized is the inventory/workspace?
3. Stock level: "low", "medium", or "high" - how well-stocked does it appear?
4. 2-3 specific observations about what you see
5. 1-2 actionable coaching tips to improve the business

Be specific, practical, and encouraging. Focus on visual signals that indicate business health."""

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
    
    # Create prompts
    results = []
    
    results.append(check_or_create_prompt(
        VISION_PROMPT_NAME,
        VISION_PROMPT_CONTENT,
        "Vision agent system prompt for photo analysis"
    ))
    
    results.append(check_or_create_prompt(
        COACHING_PROMPT_NAME,
        COACHING_PROMPT_CONTENT,
        "Coaching agent system prompt for business advice"
    ))
    
    # Check conversation prompt (don't create, just verify)
    print(f"\n🔍 Checking conversation prompt '{CONVERSATION_PROMPT_NAME}'...")
    try:
        existing = langfuse.get_prompt(CONVERSATION_PROMPT_NAME)
        if existing:
            print(f"✓ Prompt '{CONVERSATION_PROMPT_NAME}' exists (version {existing.version})")
            results.append(True)
        else:
            print(f"⚠️  Prompt '{CONVERSATION_PROMPT_NAME}' not found")
            print(f"   This prompt should be created manually from system-instructions.md")
            results.append(False)
    except Exception as e:
        print(f"⚠️  Could not verify prompt '{CONVERSATION_PROMPT_NAME}': {e}")
        print(f"   This prompt should be created manually from system-instructions.md")
        results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("📊 Summary:")
    print("="*60)
    
    all_success = all(results[:2])  # Vision and Coaching should succeed
    conversation_exists = results[2] if len(results) > 2 else False
    
    if all_success:
        print("✓ Vision Agent prompt: Ready")
        print("✓ Coaching Agent prompt: Ready")
        if conversation_exists:
            print("✓ Conversation Agent prompt: Ready")
        else:
            print("⚠️  Conversation Agent prompt: Needs manual creation")
            print("   Run this to create it:")
            print(f"   Create prompt '{CONVERSATION_PROMPT_NAME}' in Langfuse UI")
            print("   Or copy content from system-instructions.md")
        
        print("\n🎉 All prompts are ready!")
        return True
    else:
        print("✗ Some prompts failed to create. Check errors above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

