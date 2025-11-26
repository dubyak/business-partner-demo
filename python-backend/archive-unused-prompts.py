#!/usr/bin/env python3
"""
Script to archive unused prompts in Langfuse.

This archives prompts that are not currently used in the graph:
- business-partner-system (legacy ConversationAgent)
- vision-agent-system (legacy VisionAgent)
- onboarding-agent-system (old name, replaced by business-partner-agent-system)
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

# Prompts to archive (unused/legacy)
UNUSED_PROMPTS = [
    "business-partner-system",  # Legacy ConversationAgent (not in graph)
    "vision-agent-system",       # Legacy VisionAgent (photo analysis now in business_partner)
    "onboarding-agent-system",   # Old name (replaced by business-partner-agent-system)
]

# Currently active prompts (DO NOT archive these)
ACTIVE_PROMPTS = [
    "business-partner-agent-system",  # Used by OnboardingAgent (business_partner node)
    "underwriting-agent-system",      # Used by UnderwritingAgent
    "servicing-agent-system",         # Used by ServicingAgent
    "coaching-agent-system",         # Used by CoachingAgent
]


def archive_prompt(prompt_name: str) -> bool:
    """Archive a prompt by renaming it with 'archived_' prefix."""
    try:
        # Check if already archived
        if prompt_name.startswith("archived_"):
            print(f"  ✓ Prompt '{prompt_name}' is already archived")
            return True
        
        # Try to fetch the prompt first
        prompt = langfuse.get_prompt(prompt_name)
        
        if not prompt:
            print(f"  ⚠️  Prompt '{prompt_name}' not found - skipping")
            return False
        
        print(f"  📦 Prompt '{prompt_name}' found (version {prompt.version})")
        
        # Create new name with archived prefix
        archived_name = f"archived_{prompt_name}"
        
        # Check if archived version already exists
        try:
            existing = langfuse.get_prompt(archived_name)
            if existing:
                print(f"     ⚠️  Archived version '{archived_name}' already exists")
                print(f"     → Skipping rename (may already be archived)")
                return True
        except:
            pass  # Archived version doesn't exist, proceed with rename
        
        # Rename by creating a new prompt with archived name and same content
        try:
            # Get the prompt content
            prompt_content = prompt.prompt if hasattr(prompt, 'prompt') else None
            
            if not prompt_content:
                print(f"     ✗ Cannot get prompt content - skipping")
                return False
            
            # Create archived version
            archived_prompt = langfuse.create_prompt(
                name=archived_name,
                prompt=prompt_content,
                type="text",
                labels=["archived"],  # Add archived label
            )
            
            print(f"     ✓ Created archived version: '{archived_name}'")
            print(f"     → Original prompt '{prompt_name}' still exists")
            print(f"     → You can delete the original in Langfuse UI if desired")
            return True
            
        except Exception as e:
            print(f"     ✗ Error creating archived version: {e}")
            print(f"     → Please archive manually in Langfuse UI")
            return False
            
    except Exception as e:
        # Prompt doesn't exist or error fetching
        if "not found" in str(e).lower() or "404" in str(e):
            print(f"  ⚠️  Prompt '{prompt_name}' not found - skipping")
            return False
        else:
            print(f"  ✗ Error checking '{prompt_name}': {e}")
            return False


def list_all_prompts():
    """List all prompts in Langfuse (if API supports it)."""
    try:
        # Note: Langfuse SDK might not have a list_all_prompts method
        # This is a placeholder - you may need to check Langfuse API docs
        print("\n📋 Listing all prompts in Langfuse...")
        print("   (Note: Langfuse SDK may not support listing all prompts)")
        print("   Check Langfuse UI at: https://us.cloud.langfuse.com/prompts")
        return []
    except Exception as e:
        print(f"  ⚠️  Cannot list prompts: {e}")
        return []


def main():
    print("=" * 60)
    print("🗄️  Archiving Unused Prompts in Langfuse")
    print("=" * 60)
    
    # Check Langfuse connection
    if not os.getenv("LANGFUSE_SECRET_KEY") or not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("✗ ERROR: LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY must be set")
        return False
    
    print(f"📍 Langfuse Base URL: {os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')}")
    print(f"✓ Langfuse credentials found\n")
    
    print("📌 Active Prompts (DO NOT ARCHIVE):")
    for prompt_name in ACTIVE_PROMPTS:
        print(f"   ✓ {prompt_name}")
    
    print("\n📦 Prompts to Archive:")
    results = []
    
    for prompt_name in UNUSED_PROMPTS:
        print(f"\n📦 Checking '{prompt_name}'...")
        result = archive_prompt(prompt_name)
        results.append((prompt_name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    
    archived_count = sum(1 for _, result in results if result)
    not_found_count = sum(1 for _, result in results if not result)
    
    for prompt_name, result in results:
        status = "✓ Found (archive manually)" if result else "⚠️  Not found"
        print(f"{status} {prompt_name}")
    
    print(f"\n📦 Found: {archived_count} prompts")
    print(f"⚠️  Not found: {not_found_count} prompts")
    
    print("\n" + "=" * 60)
    print("📝 Next Steps:")
    print("=" * 60)
    print("1. Go to Langfuse UI: https://us.cloud.langfuse.com/prompts")
    print("2. Find the unused prompts listed above")
    print("3. Archive them manually (or add 'archived' label if supported)")
    print("\n💡 Note: Langfuse SDK may not support direct archiving.")
    print("   Use the Langfuse UI to archive prompts.")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

