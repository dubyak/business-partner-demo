-- =====================================================
-- Business Partner AI Demo - Initial Database Schema
-- =====================================================
-- Migration: 20241117000000_initial_schema
-- Description: Creates all tables, RLS policies, indexes, and triggers
-- =====================================================

-- =====================================================
-- 1. USER PROFILES TABLE
-- =====================================================
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    business_name TEXT,
    business_type TEXT,
    location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Index
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- =====================================================
-- 2. CONVERSATIONS TABLE
-- =====================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    title TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted'))
);

-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own conversations"
    ON conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversations"
    ON conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations"
    ON conversations FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations"
    ON conversations FOR DELETE
    USING (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC);

-- =====================================================
-- 3. MESSAGES TABLE
-- =====================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Enable RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view messages from own conversations"
    ON messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversations
            WHERE conversations.id = messages.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert messages to own conversations"
    ON messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations
            WHERE conversations.id = messages.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );

-- Indexes
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- =====================================================
-- 4. BUSINESS PROFILES TABLE
-- =====================================================
CREATE TABLE business_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    business_name TEXT,
    business_type TEXT,
    location TEXT,
    years_operating INT CHECK (years_operating >= 0),
    monthly_revenue DECIMAL(12, 2) CHECK (monthly_revenue >= 0),
    monthly_expenses DECIMAL(12, 2) CHECK (monthly_expenses >= 0),
    num_employees INT CHECK (num_employees >= 0),
    industry TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE business_profiles ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own business profiles"
    ON business_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own business profiles"
    ON business_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own business profiles"
    ON business_profiles FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own business profiles"
    ON business_profiles FOR DELETE
    USING (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_business_profiles_user_id ON business_profiles(user_id);
CREATE INDEX idx_business_profiles_conversation_id ON business_profiles(conversation_id);

-- =====================================================
-- 5. LOAN APPLICATIONS TABLE
-- =====================================================
CREATE TABLE loan_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    business_profile_id UUID REFERENCES business_profiles(id) ON DELETE SET NULL,
    loan_purpose TEXT,
    risk_score FLOAT CHECK (risk_score >= 0 AND risk_score <= 100),
    loan_amount DECIMAL(12, 2) CHECK (loan_amount > 0),
    term_days INT CHECK (term_days > 0),
    interest_rate DECIMAL(5, 2),
    status TEXT DEFAULT 'offered' CHECK (status IN ('offered', 'accepted', 'rejected', 'under_review', 'approved', 'declined')),
    offer_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE loan_applications ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own loan applications"
    ON loan_applications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own loan applications"
    ON loan_applications FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own loan applications"
    ON loan_applications FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_loan_applications_user_id ON loan_applications(user_id);
CREATE INDEX idx_loan_applications_conversation_id ON loan_applications(conversation_id);
CREATE INDEX idx_loan_applications_status ON loan_applications(status);
CREATE INDEX idx_loan_applications_created_at ON loan_applications(created_at DESC);

-- =====================================================
-- 6. PHOTO ANALYSES TABLE
-- =====================================================
CREATE TABLE photo_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    business_profile_id UUID REFERENCES business_profiles(id) ON DELETE SET NULL,
    photo_url TEXT,
    photo_data TEXT,
    cleanliness_score FLOAT CHECK (cleanliness_score >= 0 AND cleanliness_score <= 10),
    organization_score FLOAT CHECK (organization_score >= 0 AND organization_score <= 10),
    stock_level TEXT CHECK (stock_level IN ('empty', 'low', 'moderate', 'well-stocked', 'overstocked')),
    insights JSONB,
    coaching_tips JSONB,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE photo_analyses ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own photo analyses"
    ON photo_analyses FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own photo analyses"
    ON photo_analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own photo analyses"
    ON photo_analyses FOR DELETE
    USING (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_photo_analyses_user_id ON photo_analyses(user_id);
CREATE INDEX idx_photo_analyses_conversation_id ON photo_analyses(conversation_id);
CREATE INDEX idx_photo_analyses_analyzed_at ON photo_analyses(analyzed_at DESC);

-- =====================================================
-- 7. FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_business_profiles_updated_at
    BEFORE UPDATE ON business_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_loan_applications_updated_at
    BEFORE UPDATE ON loan_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update conversation last_message_at
CREATE OR REPLACE FUNCTION update_conversation_last_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET last_message_at = NEW.created_at
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update conversation timestamp
CREATE TRIGGER update_conversation_on_new_message
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_last_message();

-- =====================================================
-- 8. HELPFUL VIEWS
-- =====================================================

-- Conversation summaries with message counts
CREATE VIEW conversation_summaries AS
SELECT 
    c.id,
    c.user_id,
    c.session_id,
    c.title,
    c.started_at,
    c.last_message_at,
    c.status,
    COUNT(m.id) as message_count,
    MAX(m.created_at) as last_message_time
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id, c.user_id, c.session_id, c.title, c.started_at, c.last_message_at, c.status;

-- RLS for view
ALTER VIEW conversation_summaries SET (security_invoker = true);

-- =====================================================
-- 9. STORAGE BUCKET SETUP
-- =====================================================
-- Note: Storage buckets need to be created via Supabase CLI or Dashboard
-- Run this after migration completes:
-- 
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('business-photos', 'business-photos', false);
-- 
-- Then create storage policies in next migration

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

