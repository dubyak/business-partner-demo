#!/usr/bin/env python3
"""
Script to check Langfuse traces and see what's happening with state persistence.
"""

import os
from dotenv import load_dotenv
from langfuse import Langfuse
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
)

def check_recent_traces(limit=10):
    """Check the most recent traces to see state information."""
    print("=" * 80)
    print("Checking Recent Langfuse Traces")
    print("=" * 80)
    
    try:
        # Get recent traces
        # Note: Langfuse Python SDK might not have a direct list_traces method
        # We'll need to use the API or check via the web interface
        
        print("\n📊 Recent Traces (last 10):")
        print("   Note: Use Langfuse web UI to see detailed trace information")
        print("   URL: https://us.cloud.langfuse.com/traces")
        print("\n💡 To check traces in detail:")
        print("   1. Go to https://us.cloud.langfuse.com/traces")
        print("   2. Filter by session_id or user_id")
        print("   3. Look for 'business-partner-conversation' traces")
        print("   4. Check the 'input' and 'output' fields in each observation")
        print("   5. Look for state information in the metadata")
        
        # Try to get traces if API supports it
        # This is a placeholder - actual implementation depends on Langfuse API
        print("\n🔍 Checking for traces with business-partner in name...")
        
    except Exception as e:
        print(f"❌ Error checking traces: {e}")
        print("\n💡 Alternative: Check Langfuse web UI directly")
        print("   https://us.cloud.langfuse.com/traces")

def check_specific_session(session_id):
    """Check traces for a specific session."""
    print(f"\n🔍 Checking session: {session_id}")
    print("   Go to: https://us.cloud.langfuse.com/traces?sessionId={session_id}")
    print("\n   Look for:")
    print("   - State information in trace metadata")
    print("   - Input/output of business-partner-agent-process")
    print("   - Whether collected info section is in the system prompt")
    print("   - State values (business_type, location, etc.) in observations")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        check_specific_session(session_id)
    else:
        check_recent_traces()
        
    print("\n" + "=" * 80)
    print("💡 To see detailed trace information:")
    print("   1. Open https://us.cloud.langfuse.com/traces")
    print("   2. Filter by your session_id")
    print("   3. Expand each trace to see observations")
    print("   4. Check the 'input' field of 'business-partner-agent-generate-response'")
    print("   5. Look for '[ALREADY COLLECTED INFORMATION]' in the system prompt")
    print("   6. Check state values in 'business-partner-agent-process' output")
    print("=" * 80)



