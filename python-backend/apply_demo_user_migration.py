#!/usr/bin/env python3
"""
Apply the demo user helper migration to Supabase.

This script creates the create_demo_user() function in your Supabase database.
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

# Supabase connection details
SUPABASE_PROJECT_REF = "svkwsubgcedffcfrgeev"
SUPABASE_DB_PASSWORD = "T@laTrust100"
SUPABASE_DB_HOST = f"db.{SUPABASE_PROJECT_REF}.supabase.co"
SUPABASE_DB_PORT = 5432
SUPABASE_DB_NAME = "postgres"
SUPABASE_DB_USER = "postgres"

# SQL migration to create the demo user helper function
migration_sql = """
-- Function to create a demo user if it doesn't exist
CREATE OR REPLACE FUNCTION create_demo_user(user_uuid UUID)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Check if user already exists
    IF EXISTS (SELECT 1 FROM auth.users WHERE id = user_uuid) THEN
        RETURN user_uuid;
    END IF;
    
    -- Create demo user in auth.users
    INSERT INTO auth.users (
        id,
        instance_id,
        email,
        encrypted_password,
        email_confirmed_at,
        created_at,
        updated_at,
        raw_app_meta_data,
        raw_user_meta_data,
        is_super_admin,
        role
    ) VALUES (
        user_uuid,
        '00000000-0000-0000-0000-000000000000'::uuid,
        'demo-' || user_uuid::text || '@demo.local',
        crypt('demo-password', gen_salt('bf')),
        NOW(),
        NOW(),
        NOW(),
        '{"provider": "demo", "providers": ["demo"]}'::jsonb,
        '{"demo": true}'::jsonb,
        false,
        'authenticated'
    ) ON CONFLICT (id) DO NOTHING;
    
    RETURN user_uuid;
END;
$$;

-- Grant execute permission to service role
GRANT EXECUTE ON FUNCTION create_demo_user(UUID) TO service_role;
"""

def apply_migration():
    """Apply the migration SQL to Supabase."""
    print("🚀 Applying demo user helper migration...")
    print(f"📍 Connecting to: {SUPABASE_DB_HOST}")
    
    try:
        # Connect to Supabase PostgreSQL database
        conn = psycopg2.connect(
            host=SUPABASE_DB_HOST,
            port=SUPABASE_DB_PORT,
            database=SUPABASE_DB_NAME,
            user=SUPABASE_DB_USER,
            password=SUPABASE_DB_PASSWORD
        )
        
        # Set isolation level to allow DDL statements
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✓ Connected to database")
        print("📝 Executing migration SQL...")
        
        # Execute the migration
        cursor.execute(migration_sql)
        
        print("✅ Migration applied successfully!")
        print("✓ Function create_demo_user() created")
        print("✓ Service role permissions granted")
        
        # Test the function
        print("\n🧪 Testing function...")
        cursor.execute("SELECT create_demo_user('00000000-0000-0000-0000-000000000001'::uuid)")
        result = cursor.fetchone()
        print(f"✓ Test user created: {result[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection error: {e}")
        print("\n💡 Make sure:")
        print("   - Database password is correct")
        print("   - Your IP is allowed in Supabase network settings")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = apply_migration()
    if success:
        print("\n🎉 Migration complete! The demo user helper function is now available.")
    else:
        print("\n⚠️  Migration failed. You may need to run the SQL manually in Supabase Dashboard.")
