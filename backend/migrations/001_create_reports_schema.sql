-- Migration: Create Reports Schema for Saving User Reports
-- Purpose: Store AI-generated SQL queries that users want to save and re-run
-- Created: 2025-12-15

-- ============================================================================
-- STEP 1: Create dedicated schema for report management
-- ============================================================================
-- Why separate schema? 
-- - Logical organization: keeps report tables separate from analytics data
-- - Security: easier to manage permissions per schema
-- - Maintenance: can backup/restore independently

CREATE SCHEMA IF NOT EXISTS analytics_llm;

-- ============================================================================
-- STEP 2: Main table - saved_reports
-- ============================================================================
-- This is the core table that stores all saved reports metadata

CREATE TABLE analytics_llm.saved_reports (
    -- Primary Key: Unique identifier for each report
    -- SERIAL = auto-incrementing integer (PostgreSQL specific)
    report_id SERIAL PRIMARY KEY,
    
    -- User Identification
    -- VARCHAR(100): Stores user ID from your auth system
    -- NOT NULL: Every report MUST have an owner
    -- This enables multi-user support and data isolation
    user_id VARCHAR(100) NOT NULL,
    
    -- Report Metadata (USER PROVIDED)
    -- These fields describe what the report is about
    -- Users will type these in the frontend when saving a report
    report_name VARCHAR(255) NOT NULL,           -- 👤 USER TYPES THIS (e.g., "My Sales Dashboard")
    report_description TEXT,                      -- 👤 USER TYPES THIS (optional longer description)
    
    -- Query Information
    -- Store both the original question and generated SQL
    user_question TEXT NOT NULL,                  -- "Show top 10 customers by sales"
    generated_sql TEXT NOT NULL,                  -- "SELECT ... FROM ... ORDER BY ..."
    
    -- Timestamps
    -- Track when report was created and modified
    created_at TIMESTAMP DEFAULT NOW(),           -- Auto-set on creation
    updated_at TIMESTAMP DEFAULT NOW(),           -- Update manually when changed
    last_executed_at TIMESTAMP,                   -- NULL until first execution
    
    -- Usage Statistics
    -- Track how often this report is used
    execution_count INTEGER DEFAULT 0,            -- Increments each time report runs
    
    -- User Preferences
    is_favorite BOOLEAN DEFAULT FALSE,            -- User can mark favorites
    
    -- Categorization
    -- PostgreSQL array type for flexible tagging
    tags TEXT[],                                  -- ['sales', 'monthly', 'executive']
    
    -- Status Management
    -- For future: soft delete, archiving
    status VARCHAR(20) DEFAULT 'active'           -- active, archived, deleted
);

-- ============================================================================
-- STEP 3: Indexes for Performance
-- ============================================================================
-- Without indexes, queries slow down as data grows
-- With proper indexes, 10ms query time even with millions of rows

-- Index 1: User Reports (MOST IMPORTANT)
-- Pattern: Users query "show MY reports, newest first"
-- This index makes that query super fast
CREATE INDEX idx_user_reports 
ON analytics_llm.saved_reports(user_id, created_at DESC);

-- Why this works:
-- SELECT * FROM saved_reports WHERE user_id = 'user123' ORDER BY created_at DESC
-- PostgreSQL uses the index to:
-- 1. Find all rows for user123 (user_id part)
-- 2. Already sorted by date (created_at DESC part)
-- Result: 10ms instead of 500ms

-- Index 2: Search by Name (for autocomplete/search features)
-- GIN index enables fast full-text search
CREATE INDEX idx_report_search 
ON analytics_llm.saved_reports 
USING gin(to_tsvector('english', report_name));

-- Example query this helps:
-- SELECT * FROM saved_reports 
-- WHERE to_tsvector('english', report_name) @@ to_tsquery('sales & report')

-- Index 3: Favorites (optional, for future feature)
-- Partial index: only indexes rows where is_favorite = true
-- Saves space and makes favorite queries faster
CREATE INDEX idx_favorite_reports 
ON analytics_llm.saved_reports(user_id) 
WHERE is_favorite = TRUE;

-- Index 4: Tags (for filtering by category)
-- GIN index for array searching
CREATE INDEX idx_report_tags 
ON analytics_llm.saved_reports 
USING gin(tags);

-- Example: Find all reports tagged 'sales'
-- SELECT * FROM saved_reports WHERE 'sales' = ANY(tags)

-- ============================================================================
-- STEP 4: Execution History Table (Optional but Recommended)
-- ============================================================================
-- Tracks every time a report is executed
-- Why separate table? 
-- - saved_reports: one row per report (small, fast)
-- - report_executions: many rows per report (can grow large)
-- - This keeps main table fast while preserving history

CREATE TABLE analytics_llm.report_executions (
    -- Primary key for each execution
    execution_id SERIAL PRIMARY KEY,
    
    -- Foreign key: links to saved_reports
    -- ON DELETE CASCADE: if report deleted, delete all its executions too
    report_id INTEGER NOT NULL 
        REFERENCES analytics_llm.saved_reports(report_id) 
        ON DELETE CASCADE,
    
    -- Who ran this report (may differ from report owner if shared)
    user_id VARCHAR(100) NOT NULL,
    
    -- When and how long
    executed_at TIMESTAMP DEFAULT NOW(),
    execution_time_ms INTEGER,                    -- How long query took
    
    -- Results summary
    row_count INTEGER,                            -- How many rows returned
    
    -- Error tracking
    error_message TEXT                            -- NULL if successful
);

-- Index for execution history
-- Pattern: "Show me recent executions of this report"
CREATE INDEX idx_executions 
ON analytics_llm.report_executions(report_id, executed_at DESC);

-- Index for user activity tracking
-- Pattern: "What reports did this user run today?"
CREATE INDEX idx_user_executions 
ON analytics_llm.report_executions(user_id, executed_at DESC);

-- ============================================================================
-- STEP 5: Comments and Documentation
-- ============================================================================
-- PostgreSQL allows adding descriptions to tables and columns
-- Helpful for other developers and database admins

COMMENT ON SCHEMA analytics_llm IS 
    'Schema for AI-powered report management system';

COMMENT ON TABLE analytics_llm.saved_reports IS 
    'Stores user-saved reports with AI-generated SQL queries';

COMMENT ON COLUMN analytics_llm.saved_reports.user_id IS 
    'User identifier from authentication system - enables data isolation';

COMMENT ON COLUMN analytics_llm.saved_reports.report_name IS 
    'User-provided name for the report - entered in frontend when saving';

COMMENT ON COLUMN analytics_llm.saved_reports.generated_sql IS 
    'SQL query generated by AI from natural language question';

COMMENT ON TABLE analytics_llm.report_executions IS 
    'Audit trail of report executions for analytics and debugging';

-- ============================================================================
-- STEP 6: Sample Data (for testing)
-- ============================================================================
-- Insert a test report so we can verify everything works

-- Sample data showing realistic user-provided names
-- Note: In production, users will type these names in the frontend
INSERT INTO analytics_llm.saved_reports 
    (user_id, report_name, report_description, user_question, generated_sql, tags)
VALUES 
    (
        'demo_user',
        'My Monthly Top Performers',  -- 👈 User typed this name
        'Shows the highest revenue generating customers for the current year',
        'Show me top 10 customers by YTD sales',
        'SELECT gws_cust_code, gws_cust_name, SUM(gws_ytd_sales) as total_sales FROM public.gwanalytics GROUP BY gws_cust_code, gws_cust_name ORDER BY total_sales DESC LIMIT 10',
        ARRAY['sales', 'customers', 'top-performers']
    ),
    (
        'demo_user',
        'Overdue Payments - High Risk',  -- 👈 User typed this name
        'Lists all customers with outstanding payments over 180 days',
        'Which customers have outstanding above 180 days?',
        'SELECT gws_cust_code, gws_cust_name, gws_os_abv_180 FROM public.gwanalytics WHERE gws_os_abv_180 > 0 ORDER BY gws_os_abv_180 DESC',
        ARRAY['finance', 'outstanding', 'risk']
    ),
    (
        'demo_user',
        'Executive Dashboard - Sales vs Budget',  -- 👈 User's custom name
        'Quick view of sales performance against targets',
        'What is sales vs budget by company?',
        'SELECT gws_company_code, SUM(gws_ytd_sales) as sales, SUM(gws_ytd_budget) as budget FROM public.gwanalytics GROUP BY gws_company_code',
        ARRAY['executive', 'sales', 'budget']
    );

-- Verify the data was inserted
SELECT report_id, report_name, user_id, created_at 
FROM analytics_llm.saved_reports;

-- ============================================================================
-- ROLLBACK SCRIPT (for development/testing)
-- ============================================================================
-- If you need to undo this migration, run these commands:
/*
DROP TABLE IF EXISTS analytics_llm.report_executions CASCADE;
DROP TABLE IF EXISTS analytics_llm.saved_reports CASCADE;
DROP SCHEMA IF EXISTS analytics_llm CASCADE;
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify everything is working:

-- 1. Check table structure
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'analytics_llm'
ORDER BY table_name, ordinal_position;

-- 2. Check indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'analytics_llm';

-- 3. Check table sizes (should be very small initially)
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'analytics_llm';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

