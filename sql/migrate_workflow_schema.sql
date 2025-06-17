-- Migration Script: Move data from old n8n schema to new workflow registry
-- Run this BEFORE dropping old tables if you have data to preserve

-- 1. Check what tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND (table_name LIKE 'n8n_%' OR table_name LIKE 'workflow_%')
ORDER BY table_name;

-- 2. Backup old data (if old tables exist)
-- This creates backup tables with _backup suffix

-- Backup n8n_workflow_registry if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'n8n_workflow_registry') THEN
        CREATE TABLE n8n_workflow_registry_backup AS SELECT * FROM n8n_workflow_registry;
        RAISE NOTICE 'Created backup of n8n_workflow_registry';
    END IF;
END $$;

-- Backup n8n_workflow_executions if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'n8n_workflow_executions') THEN
        CREATE TABLE n8n_workflow_executions_backup AS SELECT * FROM n8n_workflow_executions;
        RAISE NOTICE 'Created backup of n8n_workflow_executions';
    END IF;
END $$;

-- 3. Migrate data from old schema to new (if both exist)

-- Migrate workflow registry data
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'n8n_workflow_registry') 
    AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflow_registry') THEN
        
        -- Insert data that doesn't already exist
        INSERT INTO workflow_registry (
            n8n_workflow_id,
            n8n_workflow_name,
            description,
            category,
            status,
            owner_team,
            webhook_url,
            created_at,
            updated_at
        )
        SELECT 
            workflow_id,
            workflow_name,
            description,
            COALESCE(category::workflow_category, 'other'::workflow_category),
            COALESCE(status::workflow_status, 'draft'::workflow_status),
            owner_team,
            webhook_url,
            created_at,
            COALESCE(updated_at, created_at)
        FROM n8n_workflow_registry old
        WHERE NOT EXISTS (
            SELECT 1 FROM workflow_registry new
            WHERE new.n8n_workflow_id = old.workflow_id
        );
        
        RAISE NOTICE 'Migrated workflow registry data';
    END IF;
END $$;

-- Migrate execution data
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'n8n_workflow_executions') 
    AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflow_executions') THEN
        
        -- First, ensure we have the workflow IDs mapped
        INSERT INTO workflow_executions (
            workflow_id,
            execution_id,
            triggered_by,
            status,
            started_at,
            completed_at,
            duration_ms,
            input_data,
            output_data,
            error_message,
            created_at
        )
        SELECT 
            wr.id as workflow_id,
            old.execution_id,
            old.triggered_by,
            old.status,
            old.started_at,
            old.completed_at,
            old.duration_ms,
            old.input_data,
            old.output_data,
            old.error_message,
            old.created_at
        FROM n8n_workflow_executions old
        JOIN workflow_registry wr ON wr.n8n_workflow_id = old.workflow_id
        WHERE NOT EXISTS (
            SELECT 1 FROM workflow_executions new
            WHERE new.execution_id = old.execution_id
        );
        
        RAISE NOTICE 'Migrated workflow execution data';
    END IF;
END $$;

-- 4. Verify migration
SELECT 
    'Old Schema' as schema_version,
    COUNT(*) as workflow_count
FROM n8n_workflow_registry
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'n8n_workflow_registry')
UNION ALL
SELECT 
    'New Schema' as schema_version,
    COUNT(*) as workflow_count
FROM workflow_registry
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflow_registry');

-- 5. After verification, you can drop old tables
-- IMPORTANT: Only run these after confirming data is migrated!
/*
DROP TABLE IF EXISTS n8n_workflow_metrics CASCADE;
DROP TABLE IF EXISTS n8n_workflow_errors CASCADE;
DROP TABLE IF EXISTS n8n_workflow_executions CASCADE;
DROP TABLE IF EXISTS n8n_workflow_registry CASCADE;

-- Also drop backup tables when you're sure
DROP TABLE IF EXISTS n8n_workflow_registry_backup;
DROP TABLE IF EXISTS n8n_workflow_executions_backup;
*/

-- 6. Final schema state
SELECT 
    t.table_name,
    obj_description(c.oid) as table_comment
FROM information_schema.tables t
JOIN pg_class c ON c.relname = t.table_name
WHERE t.table_schema = 'public'
AND t.table_name IN (
    'workflow_registry',
    'workflow_executions', 
    'workflow_templates',
    'workflow_approvals'
)
ORDER BY t.table_name;