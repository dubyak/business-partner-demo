#!/usr/bin/env python3
"""
Test script to verify Supabase connection and database status.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection and verify database tables."""
    
    print("🔍 Testing Supabase Connection...\n")
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print("1. Checking environment variables...")
    if not supabase_url:
        print("   ❌ SUPABASE_URL not set")
        return False
    else:
        print(f"   ✅ SUPABASE_URL: {supabase_url}")
    
    if not supabase_key:
        print("   ❌ SUPABASE_SERVICE_ROLE_KEY not set")
        return False
    else:
        # Show only first 20 chars of key for security
        key_preview = supabase_key[:20] + "..." if len(supabase_key) > 20 else supabase_key
        print(f"   ✅ SUPABASE_SERVICE_ROLE_KEY: {key_preview}")
    
    # Try to initialize Supabase client
    print("\n2. Initializing Supabase client...")
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("   ✅ Client initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize client: {e}")
        return False
    
    # Test connection by listing tables
    print("\n3. Testing database connection...")
    try:
        # Try to query conversations table (should exist if migrations ran)
        response = supabase.table("conversations").select("id").limit(1).execute()
        print(f"   ✅ Successfully connected to database")
        print(f"   ✅ Conversations table is accessible")
    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            print(f"   ⚠️  Connection works, but 'conversations' table not found")
            print(f"      This means migrations may not have been applied")
            return False
        else:
            print(f"   ❌ Database query failed: {e}")
            return False
    
    # Check if all expected tables exist
    print("\n4. Verifying database schema...")
    expected_tables = [
        "conversations",
        "messages", 
        "user_profiles",
        "business_profiles",
        "loan_applications",
        "photo_analyses"
    ]
    
    tables_found = []
    tables_missing = []
    
    for table_name in expected_tables:
        try:
            response = supabase.table(table_name).select("id").limit(1).execute()
            tables_found.append(table_name)
            print(f"   ✅ Table '{table_name}' exists")
        except Exception as e:
            if "does not exist" in str(e).lower():
                tables_missing.append(table_name)
                print(f"   ❌ Table '{table_name}' missing")
            else:
                # Other error, but table might exist
                print(f"   ⚠️  Table '{table_name}' check failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 CONNECTION TEST SUMMARY")
    print("="*60)
    
    if tables_missing:
        print(f"\n⚠️  {len(tables_missing)} table(s) missing:")
        for table in tables_missing:
            print(f"   - {table}")
        print("\n💡 Action needed: Run migrations to create missing tables")
        print("   Command: supabase db push")
        return False
    elif len(tables_found) == len(expected_tables):
        print(f"\n✅ All {len(expected_tables)} tables exist and are accessible")
        print("✅ Supabase connection is fully operational!")
        return True
    else:
        print(f"\n⚠️  Partial success: {len(tables_found)}/{len(expected_tables)} tables found")
        return False


if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)

