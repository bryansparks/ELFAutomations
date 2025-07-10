-- Create Workflows Tables for Control Center
-- Simple version without migration logic

-- Main workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    tags TEXT[],
    owner_team VARCHAR(255),
    source VARCHAR(50) NOT NULL DEFAULT 'created',
    source_url TEXT,
    imported_from UUID REFERENCES workflows(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    validation_status VARCHAR(50),
    last_validation TIMESTAMP WITH TIME ZONE,
    n8n_id VARCHAR(255),
    n8n_active BOOLEAN DEFAULT false,
    n8n_last_sync TIMESTAMP WITH TIME ZONE,
    n8n_execution_count INTEGER DEFAULT 0,
    n8n_success_rate DECIMAL(5,2),
    node_types TEXT[],
    integrations TEXT[],
    complexity_score INTEGER,
    estimated_cost_per_run DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    CONSTRAINT workflow_name_team_unique UNIQUE(name, owner_team)
);

-- Workflow versions table
CREATE TABLE IF NOT EXISTS workflow_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    workflow_json JSONB NOT NULL,
    processed_json JSONB,
    change_summary TEXT,
    is_current BOOLEAN DEFAULT false,
    validation_status VARCHAR(50),
    validation_report JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    CONSTRAINT unique_workflow_version UNIQUE(workflow_id, version_number)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_owner_team ON workflows(owner_team);
CREATE INDEX IF NOT EXISTS idx_workflows_category ON workflows(category);

-- Enable RLS
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_versions ENABLE ROW LEVEL SECURITY;

-- Create policies that allow all operations (adjust as needed for security)
CREATE POLICY "Enable all for authenticated users" ON workflows
    FOR ALL USING (true);

CREATE POLICY "Enable all for authenticated users" ON workflow_versions
    FOR ALL USING (true);

-- Grant permissions
GRANT ALL ON workflows TO anon;
GRANT ALL ON workflows TO authenticated;
GRANT ALL ON workflow_versions TO anon;
GRANT ALL ON workflow_versions TO authenticated;
