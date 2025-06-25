-- Migration script to move from existing workflow registry to unified schema
-- This preserves existing data while adding new capabilities

-- First, check if we need to migrate
DO $$
BEGIN
    -- Check if the old n8n_workflow_registry table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'n8n_workflow_registry') THEN
        RAISE NOTICE 'Starting migration from n8n_workflow_registry to unified schema...';

        -- Migrate basic workflow data
        INSERT INTO workflows (
            workflow_id,
            name,
            description,
            category,
            tags,
            owner_team,
            source,
            status,
            created_at,
            created_by
        )
        SELECT
            COALESCE(id::text, gen_random_uuid()::text),
            name,
            description,
            category,
            ARRAY[]::text[], -- Initialize empty tags
            owner_team,
            'synced', -- Mark as synced from N8N
            CASE
                WHEN is_active THEN 'active'
                ELSE 'inactive'
            END,
            created_at,
            created_by
        FROM n8n_workflow_registry
        ON CONFLICT (workflow_id) DO NOTHING;

        -- Migrate workflow JSON to versions table
        INSERT INTO workflow_versions (
            workflow_id,
            workflow_json,
            validation_status,
            created_at,
            created_by
        )
        SELECT
            w.id,
            nwr.workflow_json,
            'pending',
            nwr.created_at,
            nwr.created_by
        FROM n8n_workflow_registry nwr
        JOIN workflows w ON w.workflow_id = nwr.id::text;

        -- Extract metadata from workflow JSON
        INSERT INTO workflow_metadata (
            workflow_id,
            trigger_types
        )
        SELECT
            w.id,
            ARRAY(
                SELECT DISTINCT jsonb_object_keys(node_data->'parameters')
                FROM jsonb_array_elements(nwr.workflow_json->'nodes') AS node_data
                WHERE node_data->>'type' LIKE '%Trigger%'
            )
        FROM n8n_workflow_registry nwr
        JOIN workflows w ON w.workflow_id = nwr.id::text;

        RAISE NOTICE 'Migration completed. Migrated % workflows.',
            (SELECT COUNT(*) FROM n8n_workflow_registry);
    ELSE
        RAISE NOTICE 'No existing n8n_workflow_registry table found. Skipping migration.';
    END IF;
END $$;

-- Update node types and integrations from workflow JSON
UPDATE workflows w
SET
    node_types = ARRAY(
        SELECT DISTINCT node_data->>'type'
        FROM workflow_versions wv
        JOIN LATERAL jsonb_array_elements(wv.workflow_json->'nodes') AS node_data ON true
        WHERE wv.workflow_id = w.id AND wv.is_current = true
    ),
    integrations = ARRAY(
        SELECT DISTINCT
            CASE
                WHEN node_data->>'type' LIKE '%slack%' THEN 'slack'
                WHEN node_data->>'type' LIKE '%gmail%' THEN 'gmail'
                WHEN node_data->>'type' LIKE '%twilio%' THEN 'twilio'
                WHEN node_data->>'type' LIKE '%googleSheets%' THEN 'google_sheets'
                WHEN node_data->>'type' LIKE '%postgres%' THEN 'postgres'
                WHEN node_data->>'type' LIKE '%supabase%' THEN 'supabase'
                WHEN node_data->>'type' LIKE '%openAi%' THEN 'openai'
                WHEN node_data->>'type' LIKE '%anthropic%' THEN 'anthropic'
                ELSE NULL
            END
        FROM workflow_versions wv
        JOIN LATERAL jsonb_array_elements(wv.workflow_json->'nodes') AS node_data ON true
        WHERE wv.workflow_id = w.id AND wv.is_current = true
        AND node_data->>'type' NOT LIKE '%Trigger%'
    )
WHERE EXISTS (
    SELECT 1 FROM workflow_versions wv
    WHERE wv.workflow_id = w.id AND wv.is_current = true
);

-- Calculate complexity scores
UPDATE workflows w
SET complexity_score =
    CASE
        WHEN node_count < 5 THEN 1
        WHEN node_count < 10 THEN 3
        WHEN node_count < 20 THEN 5
        WHEN node_count < 30 THEN 7
        ELSE 9
    END
FROM (
    SELECT
        w.id,
        COUNT(*) as node_count
    FROM workflows w
    JOIN workflow_versions wv ON w.id = wv.workflow_id AND wv.is_current = true
    JOIN LATERAL jsonb_array_elements(wv.workflow_json->'nodes') AS node_data ON true
    GROUP BY w.id
) node_counts
WHERE node_counts.id = w.id;

-- Create some initial templates from popular workflows
INSERT INTO workflow_templates (
    workflow_id,
    template_name,
    template_description,
    template_category,
    is_official
)
SELECT
    w.id,
    'Template: ' || w.name,
    w.description,
    w.category,
    true
FROM workflows w
WHERE w.name IN (
    'AI Customer Support Agent',
    'Document Analysis RAG System',
    'Multi-Agent Research System',
    'ETL Data Pipeline',
    'Approval Workflow'
)
ON CONFLICT (template_name) DO NOTHING;

-- Add validation message
DO $$
DECLARE
    workflow_count INTEGER;
    version_count INTEGER;
    template_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO workflow_count FROM workflows;
    SELECT COUNT(*) INTO version_count FROM workflow_versions;
    SELECT COUNT(*) INTO template_count FROM workflow_templates;

    RAISE NOTICE 'Migration Summary:';
    RAISE NOTICE '  - Workflows: %', workflow_count;
    RAISE NOTICE '  - Versions: %', version_count;
    RAISE NOTICE '  - Templates: %', template_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Run validation on all imported workflows';
    RAISE NOTICE '  2. Process workflows to update credentials';
    RAISE NOTICE '  3. Sync with N8N instance for current status';
END $$;
