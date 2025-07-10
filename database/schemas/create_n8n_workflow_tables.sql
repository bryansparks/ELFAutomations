-- Create tables for n8n workflow integration
-- These tables track workflow executions, registry, and errors

-- Workflow Registry: Catalog of available workflows
CREATE TABLE IF NOT EXISTS workflow_registry (
    workflow_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    webhook_path VARCHAR(255) NOT NULL,
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for active workflows
CREATE INDEX idx_workflow_registry_active ON workflow_registry(active);
CREATE INDEX idx_workflow_registry_tags ON workflow_registry USING gin(tags);

-- Workflow Executions: Track all workflow runs
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255) UNIQUE,
    webhook_path VARCHAR(255),
    payload JSONB DEFAULT '{}',
    response_data JSONB DEFAULT '{}',
    status VARCHAR(50) NOT NULL, -- triggered, running, completed, failed
    requested_by_team VARCHAR(255),
    requested_by_agent VARCHAR(255),
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflow_registry(workflow_id)
);

-- Create indexes for execution queries
CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_requested_by_team ON workflow_executions(requested_by_team);
CREATE INDEX idx_workflow_executions_triggered_at ON workflow_executions(triggered_at DESC);

-- Workflow Errors: Detailed error tracking
CREATE TABLE IF NOT EXISTS workflow_errors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255),
    error_type VARCHAR(100) NOT NULL, -- validation, execution, timeout, connection, etc.
    error_message TEXT NOT NULL,
    error_details JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflow_registry(workflow_id)
);

-- Create indexes for error analysis
CREATE INDEX idx_workflow_errors_workflow_id ON workflow_errors(workflow_id);
CREATE INDEX idx_workflow_errors_error_type ON workflow_errors(error_type);
CREATE INDEX idx_workflow_errors_occurred_at ON workflow_errors(occurred_at DESC);
CREATE INDEX idx_workflow_errors_resolved ON workflow_errors(resolved);

-- Workflow Metrics: Performance tracking
CREATE TABLE IF NOT EXISTS workflow_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    avg_execution_time_ms INTEGER,
    min_execution_time_ms INTEGER,
    max_execution_time_ms INTEGER,
    total_retries INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflow_registry(workflow_id),
    UNIQUE(workflow_id, date)
);

-- Create index for metrics queries
CREATE INDEX idx_workflow_metrics_workflow_date ON workflow_metrics(workflow_id, date DESC);

-- Create update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_workflow_registry_updated_at BEFORE UPDATE ON workflow_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_executions_updated_at BEFORE UPDATE ON workflow_executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_metrics_updated_at BEFORE UPDATE ON workflow_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for workflow execution summary
CREATE OR REPLACE VIEW workflow_execution_summary AS
SELECT
    w.workflow_id,
    w.name as workflow_name,
    COUNT(DISTINCT e.id) as total_executions,
    COUNT(DISTINCT CASE WHEN e.status = 'completed' THEN e.id END) as successful_executions,
    COUNT(DISTINCT CASE WHEN e.status = 'failed' THEN e.id END) as failed_executions,
    COUNT(DISTINCT e.requested_by_team) as unique_requesting_teams,
    MAX(e.triggered_at) as last_execution,
    AVG(EXTRACT(EPOCH FROM (e.completed_at - e.triggered_at)) * 1000)::INTEGER as avg_execution_time_ms
FROM workflow_registry w
LEFT JOIN workflow_executions e ON w.workflow_id = e.workflow_id
WHERE w.active = true
GROUP BY w.workflow_id, w.name;

-- Create view for recent errors
CREATE OR REPLACE VIEW recent_workflow_errors AS
SELECT
    we.id,
    we.workflow_id,
    wr.name as workflow_name,
    we.execution_id,
    we.error_type,
    we.error_message,
    we.retry_count,
    we.resolved,
    we.occurred_at
FROM workflow_errors we
JOIN workflow_registry wr ON we.workflow_id = wr.workflow_id
WHERE we.occurred_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY we.occurred_at DESC;

-- Grant permissions (adjust as needed for your setup)
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
