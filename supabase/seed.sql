-- =====================================================
-- Seed Data for Development/Testing
-- =====================================================
-- This file contains test data for local development
-- Run with: supabase db reset (applies migrations + seed)
-- =====================================================

-- Note: Seed data will only work after you create a test user
-- You can create a test user via:
-- 1. supabase start (starts local instance)
-- 2. Go to http://localhost:54323 (Studio)
-- 3. Authentication → Users → Add user
-- 4. Then run: supabase db reset

-- Example seed data (uncomment and add test user_id after creating user)

-- INSERT INTO user_profiles (user_id, business_name, business_type, location)
-- VALUES (
--     'YOUR_TEST_USER_ID'::uuid,
--     'Test Cafe',
--     'Restaurant',
--     'San Francisco, CA'
-- );

-- INSERT INTO conversations (user_id, session_id, title)
-- VALUES (
--     'YOUR_TEST_USER_ID'::uuid,
--     'test-session-123',
--     'Initial Loan Inquiry'
-- );

-- Add more seed data as needed for testing

