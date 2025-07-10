-- Comprehensive Cleanup and Recreation Script for Workflow Registry
-- This will ensure you have the correct schema regardless of current state

-- STEP 1: Backup any existing data
CREATE SCHEMA IF NOT EXISTS workflow_backup;

-- Backup existing tables if they have data
DO $$
DECLARE
    table_record RECORD;
    backup_count INTEGER;
BEGIN
    FOR table_record IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND (table_name LIKE 'workflow_%' OR table_name LIKE 'n8n_%')
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', table_record.table_name) INTO backup_count;

        IF backup_count > 0 THEN
            EXECUTE format('CREATE TABLE workflow_backup.%I AS SELECT * FROM %I',
                          table_record.table_name || '_backup',
                          table_record.table_name);
            RAISE NOTICE 'Backed up % rows from %', backup_count, table_record.table_name;
        END IF;
    END LOOP;
END $$;

-- STEP 2: Drop all workflow-related objects
DO $$
BEGIN
    -- Drop views first
    DROP VIEW IF EXISTS active_workflows CASCADE;
    DROP VIEW IF EXISTS workflow_performance CASCADE;
    DROP VIEW IF EXISTS team_workflow_usage CASCADE;

    -- Drop functions
    DROP FUNCTION IF EXISTS register_workflow CASCADE;
    DROP FUNCTION IF EXISTS approve_workflow CASCADE;
    DROP FUNCTION IF EXISTS activate_workflow CASCADE;
    DROP FUNCTION IF EXISTS record_workflow_execution CASCADE;
    DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;

    -- Drop tables
    DROP TABLE IF EXISTS workflow_approvals CASCADE;
    DROP TABLE IF EXISTS workflow_executions CASCADE;
    DROP TABLE IF EXISTS workflow_templates CASCADE;
    DROP TABLE IF EXISTS workflow_registry CASCADE;

    -- Drop old n8n tables
    DROP TABLE IF EXISTS n8n_workflow_metrics CASCADE;
    DROP TABLE IF EXISTS n8n_workflow_errors CASCADE;
    DROP TABLE IF EXISTS n8n_workflow_executions CASCADE;
    DROP TABLE IF EXISTS n8n_workflow_registry CASCADE;

    -- Drop types
    DROP TYPE IF EXISTS workflow_status CASCADE;
    DROP TYPE IF EXISTS workflow_category CASCADE;

    RAISE NOTICE 'Cleaned up all existing workflow objects';
END $$;

-- STEP 3: Now run the correct schema creation
-- Copy the entire content from create_workflow_registry.sql here
-- Or run it separately after this cleanup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create types
CREATE TYPE workflow_status AS ENUM (
    'draft',        -- Being developed in n8n UI
    'testing',      -- Under test/validation
    'configured',   -- Approved and ready for use
    'running',      -- Actively deployed and executable
    'paused',       -- Temporarily disabled
    'deprecated'    -- Phased out, kept for history
);

CREATE TYPE workflow_category AS ENUM (
    'customer_onboarding',
    'order_processing',
    'data_sync',
    'reporting',
    'marketing_automation',
    'team_coordination',
    'maintenance',
    'integration',
    'other'
);

-- STEP 4: Verify final state
DO $$
DECLARE
    obj_count INTEGER;
BEGIN
    -- Count tables
    SELECT COUNT(*) INTO obj_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('workflow_registry', 'workflow_executions', 'workflow_templates', 'workflow_approvals');

    RAISE NOTICE 'Created % tables', obj_count;

    -- Count types
    SELECT COUNT(*) INTO obj_count
    FROM pg_type
    WHERE typname IN ('workflow_status', 'workflow_category');

    RAISE NOTICE 'Created % types', obj_count;
END $$;

-- STEP 5: Show backup information
SELECT
    'Backup created in schema: workflow_backup' as info
UNION ALL
SELECT
    'Tables backed up: ' || string_agg(table_name, ', ')
FROM information_schema.tables
WHERE table_schema = 'workflow_backup';

-- STEP 6: Instructions
SELECT '
NEXT STEPS:
1. Run create_workflow_registry.sql to create the correct schema
2. Check backups in workflow_backup schema if you need to restore data
3. Use migrate_workflow_schema.sql if you need to move data from old to new
4. Drop workflow_backup schema when no longer needed: DROP SCHEMA workflow_backup CASCADE;
' as instructions;
