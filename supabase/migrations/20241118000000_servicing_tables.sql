-- =====================================================
-- Business Partner AI Demo - Servicing Tables
-- =====================================================
-- Migration: 20241118000000_servicing_tables
-- Description: Creates tables for loan servicing, disbursements, repayments, and recovery
-- =====================================================

-- =====================================================
-- 1. LOANS TABLE (Active loans after acceptance)
-- =====================================================
CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    loan_application_id UUID NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    loan_amount DECIMAL(12, 2) NOT NULL CHECK (loan_amount > 0),
    term_days INT NOT NULL CHECK (term_days > 0),
    installments INT NOT NULL CHECK (installments > 0),
    installment_amount DECIMAL(12, 2) NOT NULL CHECK (installment_amount > 0),
    total_repayment DECIMAL(12, 2) NOT NULL CHECK (total_repayment > 0),
    interest_rate DECIMAL(5, 2) NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paid_off', 'defaulted', 'closed', 'restructured')),
    disbursed_at TIMESTAMP WITH TIME ZONE,
    paid_off_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own loans"
    ON loans FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own loans"
    ON loans FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own loans"
    ON loans FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_loans_user_id ON loans(user_id);
CREATE INDEX idx_loans_loan_application_id ON loans(loan_application_id);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_loans_disbursed_at ON loans(disbursed_at DESC);

-- =====================================================
-- 2. DISBURSEMENTS TABLE
-- =====================================================
CREATE TABLE disbursements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL CHECK (amount > 0),
    bank_account TEXT,  -- Masked bank account info
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'initiated', 'processing', 'completed', 'failed', 'cancelled')),
    reference_number TEXT UNIQUE,
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    estimated_completion TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    failure_reason TEXT,
    metadata JSONB,  -- Additional disbursement details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE disbursements ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own disbursements"
    ON disbursements FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own disbursements"
    ON disbursements FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own disbursements"
    ON disbursements FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_disbursements_loan_id ON disbursements(loan_id);
CREATE INDEX idx_disbursements_user_id ON disbursements(user_id);
CREATE INDEX idx_disbursements_status ON disbursements(status);
CREATE INDEX idx_disbursements_reference_number ON disbursements(reference_number);

-- =====================================================
-- 3. REPAYMENTS TABLE
-- =====================================================
CREATE TABLE repayments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    installment_number INT NOT NULL CHECK (installment_number > 0),
    amount DECIMAL(12, 2) NOT NULL CHECK (amount > 0),
    method TEXT NOT NULL CHECK (method IN ('existing_bank', 'new_account', 'in_person', 'other')),
    bank_account TEXT,  -- Bank account used (masked)
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded')),
    reference_number TEXT UNIQUE,
    due_date DATE NOT NULL,
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    estimated_completion TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    failure_reason TEXT,
    metadata JSONB,  -- Additional repayment details (location for in-person, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE repayments ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own repayments"
    ON repayments FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own repayments"
    ON repayments FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own repayments"
    ON repayments FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_repayments_loan_id ON repayments(loan_id);
CREATE INDEX idx_repayments_user_id ON repayments(user_id);
CREATE INDEX idx_repayments_status ON repayments(status);
CREATE INDEX idx_repayments_due_date ON repayments(due_date);
CREATE INDEX idx_repayments_reference_number ON repayments(reference_number);

-- =====================================================
-- 4. RECOVERY CONVERSATIONS TABLE
-- =====================================================
CREATE TABLE recovery_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'initial' CHECK (status IN ('initial', 'in_conversation', 'resolution_pending', 'resolved', 'escalated', 'closed')),
    resolution_type TEXT CHECK (resolution_type IN ('promise_to_pay', 'payment_plan', 'restructuring', 'settlement', 'other', NULL)),
    outstanding_balance DECIMAL(12, 2) NOT NULL CHECK (outstanding_balance >= 0),
    resolution_details JSONB,  -- Details of the resolution (payment plan terms, promise to pay date, etc.)
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    escalated_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,  -- Additional recovery conversation metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE recovery_conversations ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own recovery conversations"
    ON recovery_conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own recovery conversations"
    ON recovery_conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own recovery conversations"
    ON recovery_conversations FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_recovery_conversations_loan_id ON recovery_conversations(loan_id);
CREATE INDEX idx_recovery_conversations_user_id ON recovery_conversations(user_id);
CREATE INDEX idx_recovery_conversations_status ON recovery_conversations(status);
CREATE INDEX idx_recovery_conversations_conversation_id ON recovery_conversations(conversation_id);

-- =====================================================
-- 5. UPDATE LOAN APPLICATIONS STATUS ENUM
-- =====================================================
-- Add new statuses to loan_applications table
ALTER TABLE loan_applications 
DROP CONSTRAINT IF EXISTS loan_applications_status_check;

ALTER TABLE loan_applications
ADD CONSTRAINT loan_applications_status_check 
CHECK (status IN ('offered', 'accepted', 'rejected', 'under_review', 'approved', 'declined', 'disbursed', 'cancelled'));

-- =====================================================
-- 6. TRIGGERS FOR UPDATED_AT
-- =====================================================

-- Trigger for loans
CREATE TRIGGER update_loans_updated_at
    BEFORE UPDATE ON loans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for disbursements
CREATE TRIGGER update_disbursements_updated_at
    BEFORE UPDATE ON disbursements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for repayments
CREATE TRIGGER update_repayments_updated_at
    BEFORE UPDATE ON repayments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for recovery_conversations
CREATE TRIGGER update_recovery_conversations_updated_at
    BEFORE UPDATE ON recovery_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 7. HELPFUL VIEWS
-- =====================================================

-- Active loans with payment status
CREATE VIEW active_loans_summary AS
SELECT 
    l.id,
    l.user_id,
    l.loan_amount,
    l.total_repayment,
    l.installments,
    l.installment_amount,
    l.status,
    l.disbursed_at,
    COUNT(r.id) FILTER (WHERE r.status = 'completed') as payments_completed,
    COUNT(r.id) FILTER (WHERE r.status IN ('pending', 'processing')) as payments_pending,
    COUNT(r.id) FILTER (WHERE r.due_date < CURRENT_DATE AND r.status != 'completed') as payments_overdue,
    COALESCE(SUM(r.amount) FILTER (WHERE r.status = 'completed'), 0) as total_paid,
    (l.total_repayment - COALESCE(SUM(r.amount) FILTER (WHERE r.status = 'completed'), 0)) as outstanding_balance
FROM loans l
LEFT JOIN repayments r ON l.id = r.loan_id
WHERE l.status = 'active'
GROUP BY l.id, l.user_id, l.loan_amount, l.total_repayment, l.installments, l.installment_amount, l.status, l.disbursed_at;

-- RLS for view
ALTER VIEW active_loans_summary SET (security_invoker = true);

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

