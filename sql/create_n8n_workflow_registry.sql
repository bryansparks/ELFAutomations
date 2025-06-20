-- N8N Workflow Registry Schema
-- Tracks all n8n workflows and their executions

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Workflow registry table
CREATE TABLE IF NOT EXISTS n8n_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    category TEXT NOT NULL CHECK (category IN ('data-pipeline', 'integration', 'automation', 'notification', 'approval')),
    owner_team TEXT NOT NULL,
    n8n_workflow_id TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK (trigger_type IN ('webhook', 'schedule', 'manual', 'event')),
    webhook_url TEXT,
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'
);

-- Workflow execution tracking
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES n8n_workflows(id) ON DELETE CASCADE,
    triggered_by TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failed')),
    input_data JSONB DEFAULT '{}',
    output_data JSONB,
    error_message TEXT,
    execution_metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX idx_workflows_name ON n8n_workflows(name);
CREATE INDEX idx_workflows_owner_team ON n8n_workflows(owner_team);
CREATE INDEX idx_workflows_category ON n8n_workflows(category);
CREATE INDEX idx_workflows_active ON n8n_workflows(is_active);

CREATE INDEX idx_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_executions_triggered_by ON workflow_executions(triggered_by);
CREATE INDEX idx_executions_status ON workflow_executions(status);
CREATE INDEX idx_executions_started_at ON workflow_executions(started_at DESC);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_n8n_workflows_updated_at BEFORE UPDATE
    ON n8n_workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for analytics
CREATE VIEW workflow_execution_stats AS
SELECT 
    w.id,
    w.name,
    w.owner_team,
    w.category,
    COUNT(e.id) as total_executions,
    COUNT(CASE WHEN e.status = 'success' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN e.status = 'failed' THEN 1 END) as failed_executions,
    COUNT(CASE WHEN e.status = 'running' THEN 1 END) as running_executions,
    AVG(EXTRACT(EPOCH FROM (e.completed_at - e.started_at))) as avg_duration_seconds,
    MAX(e.started_at) as last_execution
FROM n8n_workflows w
LEFT JOIN workflow_executions e ON w.id = e.workflow_id
GROUP BY w.id, w.name, w.owner_team, w.category;

-- View for recent executions
CREATE VIEW recent_workflow_executions AS
SELECT 
    e.*,
    w.name as workflow_name,
    w.owner_team,
    w.category,
    EXTRACT(EPOCH FROM (e.completed_at - e.started_at)) as duration_seconds
FROM workflow_executions e
JOIN n8n_workflows w ON e.workflow_id = w.id
ORDER BY e.started_at DESC
LIMIT 100;

-- Function to get workflow success rate
CREATE OR REPLACE FUNCTION get_workflow_success_rate(workflow_name TEXT)
RETURNS TABLE(
    success_rate NUMERIC,
    total_executions INTEGER,
    successful_executions INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN COUNT(*) = 0 THEN 0
            ELSE ROUND(COUNT(CASE WHEN e.status = 'success' THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100, 2)
        END as success_rate,
        COUNT(*)::INTEGER as total_executions,
        COUNT(CASE WHEN e.status = 'success' THEN 1 END)::INTEGER as successful_executions
    FROM workflow_executions e
    JOIN n8n_workflows w ON e.workflow_id = w.id
    WHERE w.name = workflow_name
    AND e.completed_at IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing (commented out by default)
/*
INSERT INTO n8n_workflows (name, description, category, owner_team, n8n_workflow_id, trigger_type, webhook_url, input_schema, output_schema) VALUES
('test-webhook-workflow', 'Test webhook workflow', 'automation', 'test-team', 'abc123', 'webhook', 'http://n8n.n8n.svc.cluster.local:5678/webhook/test', '{"message": "string"}', '{"result": "string"}'),
('daily-report-generator', 'Generate daily reports', 'data-pipeline', 'executive-team', 'def456', 'schedule', NULL, '{}', '{"report_url": "string"}');
*/