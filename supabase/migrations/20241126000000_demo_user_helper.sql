-- =====================================================
-- Demo User Helper Function
-- =====================================================
-- Migration: 20241126000000_demo_user_helper
-- Description: Creates a function to ensure demo users exist in auth.users
-- =====================================================

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
        '00000000-0000-0000-0000-000000000000'::uuid,  -- Default instance
        'demo-' || user_uuid::text || '@demo.local',  -- Demo email
        crypt('demo-password', gen_salt('bf')),  -- Encrypted password (not used)
        NOW(),  -- Email confirmed
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

