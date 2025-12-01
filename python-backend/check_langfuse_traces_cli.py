#!/usr/bin/env python3
"""
CLI tool to check Langfuse traces directly via the Python SDK.

Usage:
    python check_langfuse_traces_cli.py [--session-id SESSION_ID] [--limit N] [--recent]
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional

# Load environment variables
load_dotenv()

from langfuse import Langfuse

def get_langfuse_client() -> Optional[Langfuse]:
    """Initialize Langfuse client from environment variables."""
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    
    if not secret_key or not public_key:
        print("❌ Error: LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY must be set")
        return None
    
    try:
        client = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=base_url,
        )
        return client
    except Exception as e:
        print(f"❌ Error initializing Langfuse client: {e}")
        return None


def list_recent_traces(client: Langfuse, limit: int = 10):
    """List recent traces using the Langfuse API."""
    try:
        # Note: Langfuse Python SDK 2.53.0 may not have a direct list_traces method
        # We'll use the API directly via the client's internal methods
        print(f"\n📊 Fetching last {limit} traces...")
        print("=" * 80)
        
        # Try to use the client's fetch_traces method if available
        # This is a workaround - the exact API may vary by version
        try:
            # For Langfuse 2.53.0, we might need to use the HTTP client directly
            import httpx
            
            base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip('/')
            api_url = f"{base_url}/api/public/traces"
            
            # Langfuse API authentication format
            # Based on Langfuse SDK, it uses Basic auth with public_key:secret_key
            import base64
            
            public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
            secret_key = os.getenv('LANGFUSE_SECRET_KEY')
            
            if not public_key or not secret_key:
                print("❌ LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set")
                return
            
            # Create Basic auth header
            auth_string = f"{public_key}:{secret_key}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/json",
            }
            
            params = {
                "limit": limit,
                "page": 1,
            }
            
            response = httpx.get(api_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                traces = data.get("data", [])
                
                if not traces:
                    print("No traces found.")
                    return
                
                print(f"\n✅ Found {len(traces)} trace(s):\n")
                
                for i, trace in enumerate(traces, 1):
                    trace_id = trace.get("id", "unknown")
                    name = trace.get("name", "unnamed")
                    session_id = trace.get("sessionId")
                    user_id = trace.get("userId")
                    timestamp = trace.get("timestamp")
                    metadata = trace.get("metadata", {})
                    
                    print(f"{i}. Trace: {name}")
                    print(f"   ID: {trace_id}")
                    if session_id:
                        print(f"   Session: {session_id}")
                    if user_id:
                        print(f"   User: {user_id}")
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            print(f"   Time: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                        except:
                            print(f"   Time: {timestamp}")
                    if metadata:
                        print(f"   Metadata: {metadata}")
                    print()
                    
                    # Print URL to view in UI
                    project_id = os.getenv("LANGFUSE_PROJECT_ID", "")
                    if project_id:
                        base_url_clean = base_url.replace("https://", "").replace("http://", "")
                        print(f"   🔗 View: https://{base_url_clean}/project/{project_id}/traces/{trace_id}")
                    print()
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                print("\n💡 Tip: Check your LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY")
                
        except ImportError:
            print("⚠️  httpx not available. Install it with: pip install httpx")
            print("\n💡 Alternative: Use the Langfuse web UI to view traces")
            print(f"   URL: {os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')}/traces")
        except Exception as e:
            print(f"❌ Error fetching traces: {e}")
            print("\n💡 Alternative: Use the Langfuse web UI to view traces")
            print(f"   URL: {os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')}/traces")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def get_trace_by_session(client: Langfuse, session_id: str):
    """Get traces for a specific session."""
    print(f"\n🔍 Searching for traces with session_id: {session_id}")
    print("=" * 80)
    
    try:
        import httpx
        
        base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip('/')
        api_url = f"{base_url}/api/public/traces"
        
        import base64
        
        public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
        secret_key = os.getenv('LANGFUSE_SECRET_KEY')
        
        if not public_key or not secret_key:
            print("❌ LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set")
            return
        
        auth_string = f"{public_key}:{secret_key}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
        }
        
        params = {
            "sessionId": session_id,
            "limit": 50,
        }
        
        response = httpx.get(api_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            traces = data.get("data", [])
            
            if not traces:
                print(f"❌ No traces found for session: {session_id}")
                return
            
            print(f"\n✅ Found {len(traces)} trace(s) for this session:\n")
            
            for i, trace in enumerate(traces, 1):
                trace_id = trace.get("id", "unknown")
                name = trace.get("name", "unnamed")
                timestamp = trace.get("timestamp")
                metadata = trace.get("metadata", {})
                input_data = trace.get("input")
                output_data = trace.get("output")
                
                print(f"{i}. {name}")
                print(f"   ID: {trace_id}")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        print(f"   Time: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    except:
                        print(f"   Time: {timestamp}")
                
                if metadata:
                    print(f"   Metadata:")
                    for key, value in metadata.items():
                        print(f"     - {key}: {value}")
                
                if input_data:
                    print(f"   Input: {str(input_data)[:100]}...")
                
                if output_data:
                    print(f"   Output: {str(output_data)[:100]}...")
                
                print()
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except ImportError:
        print("⚠️  httpx not available. Install it with: pip install httpx")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Langfuse traces via CLI")
    parser.add_argument("--session-id", help="Filter by session ID")
    parser.add_argument("--limit", type=int, default=10, help="Number of traces to fetch (default: 10)")
    parser.add_argument("--recent", action="store_true", help="Show recent traces")
    
    args = parser.parse_args()
    
    client = get_langfuse_client()
    if not client:
        sys.exit(1)
    
    print("🔍 Langfuse Trace Checker")
    print("=" * 80)
    print(f"Base URL: {os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')}")
    print(f"Public Key: {os.getenv('LANGFUSE_PUBLIC_KEY', 'NOT SET')[:20]}...")
    print()
    
    if args.session_id:
        get_trace_by_session(client, args.session_id)
    else:
        list_recent_traces(client, args.limit)


if __name__ == "__main__":
    main()

