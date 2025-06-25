-- Unified N8N Workflow Registry Schema
-- Comprehensive workflow management with import/export, versioning, and validation

-- Drop existing tables if needed (be careful in production!)
-- DROP TABLE IF EXISTS workflow_validation_logs CASCADE;
-- DROP TABLE IF EXISTS workflow_versions CASCADE;
-- DROP TABLE IF EXISTS workflow_templates CASCADE;
-- DROP TABLE IF EXISTS workflow_metadata CASCADE;
-- DROP TABLE IF EXISTS workflows CASCADE;

-- Main workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) UNIQUE NOT NULL, -- N8N workflow ID
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    tags TEXT[], -- Array of tags for search
    owner_team VARCHAR(255),

    -- Source tracking
    source VARCHAR(50) NOT NULL DEFAULT 'created', -- created, imported, cloned, synced
    source_url TEXT, -- If imported from URL
    imported_from UUID REFERENCES workflows(id), -- If cloned

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, validated, deployed, active, inactive, archived
    validation_status VARCHAR(50), -- pending, passed, failed, warnings
    last_validation TIMESTAMP WITH TIME ZONE,

    -- N8N sync
    n8n_id VARCHAR(255), -- ID in N8N instance
    n8n_active BOOLEAN DEFAULT false,
    n8n_last_sync TIMESTAMP WITH TIME ZONE,
    n8n_execution_count INTEGER DEFAULT 0,
    n8n_success_rate DECIMAL(5,2),

    -- Search optimization
    node_types TEXT[], -- Array of node types used
    integrations TEXT[], -- Slack, Gmail, etc.
    complexity_score INTEGER, -- 1-10
    estimated_cost_per_run DECIMAL(10,4),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),

    -- Indexes
    CONSTRAINT workflow_name_team_unique UNIQUE(name, owner_team)
);

-- Workflow versions table (stores complete JSON)
CREATE TABLE IF NOT EXISTS workflow_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,

    -- Complete workflow definition
    workflow_json JSONB NOT NULL, -- Full N8N workflow JSON
    processed_json JSONB, -- Our processed version

    -- Version metadata
    change_summary TEXT,
    is_current BOOLEAN DEFAULT false,
    validation_status VARCHAR(50),
    validation_report JSONB,

    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),

    -- Ensure unique version numbers per workflow
    CONSTRAINT unique_workflow_version UNIQUE(workflow_id, version_number)
);

-- Workflow templates table
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    template_name VARCHAR(255) UNIQUE NOT NULL,
    template_description TEXT,
    template_category VARCHAR(100),

    -- Template metadata
    use_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2),
    is_official BOOLEAN DEFAULT false,

    -- Customization points
    variable_definitions JSONB, -- Variables that can be customized
    required_credentials TEXT[], -- Types of credentials needed

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

-- Workflow metadata (additional searchable data)
CREATE TABLE IF NOT EXISTS workflow_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,

    -- Extracted metadata
    trigger_types TEXT[], -- webhook, schedule, manual, etc.
    input_sources TEXT[], -- Sources of data
    output_destinations TEXT[], -- Where data goes

    -- Requirements
    required_credentials JSONB, -- {type: name} mapping
    environment_variables TEXT[],
    webhook_urls TEXT[],

    -- Performance metrics
    avg_execution_time_ms INTEGER,
    max_memory_usage_mb INTEGER,

    -- AI analysis
    ai_generated_description TEXT,
    ai_suggested_improvements JSONB,
    ai_detected_patterns TEXT[],

    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Validation logs
CREATE TABLE IF NOT EXISTS workflow_validation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    version_id UUID REFERENCES workflow_versions(id) ON DELETE CASCADE,

    validation_type VARCHAR(50), -- security, compatibility, performance, best_practices
    validation_status VARCHAR(50), -- passed, failed, warning

    -- Detailed results
    errors JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    suggestions JSONB DEFAULT '[]',

    -- Specific checks
    security_issues JSONB,
    missing_nodes TEXT[],
    missing_credentials TEXT[],
    estimated_cost DECIMAL(10,4),
    complexity_score INTEGER,

    validated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    validated_by VARCHAR(255)
);

-- Import/Export audit trail
CREATE TABLE IF NOT EXISTS workflow_import_export_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,

    operation VARCHAR(50) NOT NULL, -- import, export, sync
    operation_status VARCHAR(50), -- success, failed, partial

    -- Import details
    source_format VARCHAR(50), -- json, url, file
    source_data TEXT, -- URL or filename
    original_json JSONB, -- Original before processing

    -- Export details
    export_format VARCHAR(50), -- json, archive, markdown
    export_path TEXT,

    -- Results
    error_message TEXT,
    processing_notes JSONB,

    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    performed_by VARCHAR(255)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_owner_team ON workflows(owner_team);
CREATE INDEX IF NOT EXISTS idx_workflows_category ON workflows(category);
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_workflows_node_types ON workflows USING GIN(node_types);
CREATE INDEX IF NOT EXISTS idx_workflows_integrations ON workflows USING GIN(integrations);
CREATE INDEX IF NOT EXISTS idx_workflows_search ON workflows USING GIN(
    to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, ''))
);
CREATE INDEX IF NOT EXISTS idx_workflow_versions_current ON workflow_versions(workflow_id, is_current) WHERE is_current = true;
CREATE INDEX IF NOT EXISTS idx_validation_logs_workflow ON workflow_validation_logs(workflow_id, validation_status);

-- Views for common queries
CREATE OR REPLACE VIEW active_workflows AS
SELECT
    w.*,
    wv.workflow_json,
    wv.processed_json,
    wm.required_credentials,
    wm.trigger_types
FROM workflows w
JOIN workflow_versions wv ON w.id = wv.workflow_id AND wv.is_current = true
LEFT JOIN workflow_metadata wm ON w.id = wm.workflow_id
WHERE w.status = 'active';

CREATE OR REPLACE VIEW workflow_templates_view AS
SELECT
    wt.*,
    w.name as workflow_name,
    w.description as workflow_description,
    w.node_types,
    w.integrations,
    wv.workflow_json
FROM workflow_templates wt
JOIN workflows w ON wt.workflow_id = w.id
JOIN workflow_versions wv ON w.id = wv.workflow_id AND wv.is_current = true
WHERE wt.is_official = true OR wt.use_count > 10;

-- Functions
CREATE OR REPLACE FUNCTION increment_workflow_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Set all versions to not current
    UPDATE workflow_versions
    SET is_current = false
    WHERE workflow_id = NEW.workflow_id;

    -- Set new version as current
    NEW.is_current = true;

    -- Calculate version number
    NEW.version_number = COALESCE(
        (SELECT MAX(version_number) + 1
         FROM workflow_versions
         WHERE workflow_id = NEW.workflow_id),
        1
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_workflow_version
BEFORE INSERT ON workflow_versions
FOR EACH ROW
EXECUTE FUNCTION increment_workflow_version();

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workflows_updated_at
BEFORE UPDATE ON workflows
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_metadata_updated_at
BEFORE UPDATE ON workflow_metadata
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
