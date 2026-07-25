-- Health Diagnostics Database Schema - Initial Migration
-- Run this migration to set up the Supabase database schema
-- Migration: 001_initial.sql
-- Created: 2026-05-05

-- ============================================================================
-- Users Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- ============================================================================
-- Reports Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Analysis data (JSONB for flexible schema)
    parameters JSONB NOT NULL DEFAULT '{}',
    analysis JSONB NOT NULL DEFAULT '{}',
    risks JSONB NOT NULL DEFAULT '[]',
    recommendations TEXT[] DEFAULT '{}',
    summary JSONB NOT NULL DEFAULT '{}',
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'error')),
    
    -- File metadata
    file_name VARCHAR(255),
    file_type VARCHAR(10),
    
    -- Audit trail
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_user_created ON reports(user_id, created_at DESC);

-- ============================================================================
-- Chat History Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID UNIQUE NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    messages JSONB NOT NULL DEFAULT '[]',
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_report_id ON chat_history(report_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at DESC);

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Users table policies
-- Users can view their own profile
CREATE POLICY "users_view_own_profile"
    ON users FOR SELECT
    USING (auth.uid()::text = id::text OR is_active = true);

-- Users can update their own profile
CREATE POLICY "users_update_own_profile"
    ON users FOR UPDATE
    USING (auth.uid()::text = id::text)
    WITH CHECK (auth.uid()::text = id::text);

-- Reports table policies
-- Users can view their own reports
CREATE POLICY "reports_view_own_reports"
    ON reports FOR SELECT
    USING (auth.uid()::text = user_id::text OR user_id IS NULL);

-- Users can insert their own reports
CREATE POLICY "reports_insert_own_reports"
    ON reports FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text OR user_id IS NULL);

-- Users can update their own reports
CREATE POLICY "reports_update_own_reports"
    ON reports FOR UPDATE
    USING (auth.uid()::text = user_id::text OR user_id IS NULL)
    WITH CHECK (auth.uid()::text = user_id::text OR user_id IS NULL);

-- Users can delete their own reports
CREATE POLICY "reports_delete_own_reports"
    ON reports FOR DELETE
    USING (auth.uid()::text = user_id::text OR user_id IS NULL);

-- Chat history policies
-- Users can view chat for their reports
CREATE POLICY "chat_history_view_own_reports"
    ON chat_history FOR SELECT
    USING (
        report_id IN (
            SELECT id FROM reports
            WHERE auth.uid()::text = reports.user_id::text OR reports.user_id IS NULL
        )
    );

-- Users can insert chat for their reports
CREATE POLICY "chat_history_insert_own_reports"
    ON chat_history FOR INSERT
    WITH CHECK (
        report_id IN (
            SELECT id FROM reports
            WHERE auth.uid()::text = reports.user_id::text OR reports.user_id IS NULL
        )
    );

-- Users can update chat for their reports
CREATE POLICY "chat_history_update_own_reports"
    ON chat_history FOR UPDATE
    USING (
        report_id IN (
            SELECT id FROM reports
            WHERE auth.uid()::text = reports.user_id::text OR reports.user_id IS NULL
        )
    )
    WITH CHECK (
        report_id IN (
            SELECT id FROM reports
            WHERE auth.uid()::text = reports.user_id::text OR reports.user_id IS NULL
        )
    );

-- ============================================================================
-- Functions for Auto-Update Timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for auto-update timestamps
CREATE TRIGGER users_update_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER reports_update_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER chat_history_update_updated_at BEFORE UPDATE ON chat_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Seed Data (Optional - Comment out if not needed)
-- ============================================================================

-- INSERT INTO users (email, full_name, is_active)
-- VALUES ('demo@health-diagnostics.com', 'Demo User', true)
-- ON CONFLICT (email) DO NOTHING;
