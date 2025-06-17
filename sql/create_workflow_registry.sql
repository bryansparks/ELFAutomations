-- Workflow Registry for n8n Automations in ElfAutomations
-- Tracks configured workflows, their status, and execution history

-- Workflow lifecycle states
CREATE TYPE workflow_status AS ENUM (
    'draft',        -- Being developed in n8n UI
    'testing',      -- Under test/validation
    'configured',   -- Approved and ready for use
    'running',      -- Actively deployed and executable
    'paused',       -- Temporarily disabled
    'deprecated'    -- Phased out, kept for history
);

-- Workflow categories for organization
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

-- Main workflow registry table
CREATE TABLE workflow_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- n8n workflow identification
    n8n_workflow_id VARCHAR(255) UNIQUE NOT NULL,
    n8n_workflow_name VARCHAR(255) NOT NULL,
    
    -- Metadata
    description TEXT,
    category workflow_category DEFAULT 'other',
    version INTEGER DEFAULT 1,
    
    -- Status tracking
    status workflow_status DEFAULT 'draft',
    configured_at TIMESTAMP WITH TIME ZONE,
    configured_by VARCHAR(255),
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ownership and access
    owner_team VARCHAR(255),  -- Which team owns this workflow
    allowed_teams TEXT[],     -- Teams allowed to trigger this workflow
    
    -- Configuration
    webhook_url VARCHAR(500),
    input_schema JSONB,       -- Expected input parameters
    output_schema JSONB,      -- Expected output format
    configuration JSONB,      -- Additional config parameters
    
    -- Performance metrics
    avg_execution_time_ms INTEGER,
    success_rate DECIMAL(5,2),
    last_execution TIMESTAMP WITH TIME ZONE,
    execution_count INTEGER DEFAULT 0,
    
    -- Tags for searchability
    tags TEXT[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workflow execution history
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflow_registry(id),
    
    -- Execution details
    execution_id VARCHAR(255),  -- n8n execution ID
    triggered_by VARCHAR(255),  -- Team or system that triggered
    trigger_method VARCHAR(50), -- 'webhook', 'schedule', 'manual', 'a2a'
    
    -- Status
    status VARCHAR(50),  -- 'running', 'success', 'error', 'timeout'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Data
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    
    -- Tracking
    team_request_id UUID,  -- Link to team's A2A request
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workflow templates library
CREATE TABLE workflow_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Template identification
    template_name VARCHAR(255) UNIQUE NOT NULL,
    category workflow_category,
    description TEXT,
    
    -- Template data
    n8n_template JSONB,  -- Exportable n8n workflow JSON
    required_inputs JSONB,
    expected_outputs JSONB,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    tags TEXT[],
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workflow approval log
CREATE TABLE workflow_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflow_registry(id),
    
    -- Approval details
    action VARCHAR(50), -- 'approve', 'reject', 'request_changes'
    from_status workflow_status,
    to_status workflow_status,
    
    -- Who and why
    approved_by VARCHAR(255),
    approval_notes TEXT,
    conditions TEXT[], -- Any conditions for approval
    
    -- Testing results
    test_results JSONB,
    test_passed BOOLEAN,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_workflow_status ON workflow_registry(status);
CREATE INDEX idx_workflow_category ON workflow_registry(category);
CREATE INDEX idx_workflow_owner ON workflow_registry(owner_team);
CREATE INDEX idx_workflow_tags ON workflow_registry USING gin(tags);
CREATE INDEX idx_execution_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_execution_status ON workflow_executions(status);
CREATE INDEX idx_execution_triggered_by ON workflow_executions(triggered_by);
CREATE INDEX idx_execution_created ON workflow_executions(created_at DESC);

-- Views for common queries

-- Active workflows view
CREATE VIEW active_workflows AS
SELECT 
    wr.*,
    COUNT(we.id) as recent_executions,
    AVG(we.duration_ms) as avg_duration_ms
FROM workflow_registry wr
LEFT JOIN workflow_executions we ON wr.id = we.workflow_id
    AND we.created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
WHERE wr.status = 'running'
GROUP BY wr.id;

-- Workflow performance view
CREATE VIEW workflow_performance AS
SELECT 
    wr.id,
    wr.n8n_workflow_name,
    wr.category,
    wr.owner_team,
    COUNT(we.id) as total_executions,
    COUNT(CASE WHEN we.status = 'success' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN we.status = 'error' THEN 1 END) as failed_executions,
    ROUND(100.0 * COUNT(CASE WHEN we.status = 'success' THEN 1 END) / NULLIF(COUNT(we.id), 0), 2) as success_rate,
    AVG(we.duration_ms) as avg_duration_ms,
    MAX(we.duration_ms) as max_duration_ms,
    MIN(we.duration_ms) as min_duration_ms
FROM workflow_registry wr
LEFT JOIN workflow_executions we ON wr.id = we.workflow_id
GROUP BY wr.id;

-- Team workflow usage view
CREATE VIEW team_workflow_usage AS
SELECT 
    we.triggered_by as team_name,
    wr.category,
    COUNT(DISTINCT wr.id) as unique_workflows_used,
    COUNT(we.id) as total_executions,
    AVG(we.duration_ms) as avg_execution_time,
    MAX(we.created_at) as last_execution
FROM workflow_executions we
JOIN workflow_registry wr ON we.workflow_id = wr.id
GROUP BY we.triggered_by, wr.category;

-- Functions

-- Function to register a new workflow
CREATE OR REPLACE FUNCTION register_workflow(
    p_n8n_workflow_id VARCHAR(255),
    p_n8n_workflow_name VARCHAR(255),
    p_description TEXT,
    p_category workflow_category,
    p_owner_team VARCHAR(255),
    p_webhook_url VARCHAR(500) DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_workflow_id UUID;
BEGIN
    INSERT INTO workflow_registry (
        n8n_workflow_id,
        n8n_workflow_name,
        description,
        category,
        owner_team,
        webhook_url,
        status
    ) VALUES (
        p_n8n_workflow_id,
        p_n8n_workflow_name,
        p_description,
        p_category,
        p_owner_team,
        p_webhook_url,
        'draft'
    )
    RETURNING id INTO v_workflow_id;
    
    RETURN v_workflow_id;
END;
$$ LANGUAGE plpgsql;

-- Function to approve workflow for production
CREATE OR REPLACE FUNCTION approve_workflow(
    p_workflow_id UUID,
    p_approved_by VARCHAR(255),
    p_notes TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Update workflow status
    UPDATE workflow_registry
    SET 
        status = 'configured',
        configured_at = CURRENT_TIMESTAMP,
        configured_by = p_approved_by
    WHERE id = p_workflow_id AND status IN ('draft', 'testing');
    
    -- Log approval
    INSERT INTO workflow_approvals (
        workflow_id,
        action,
        from_status,
        to_status,
        approved_by,
        approval_notes
    ) VALUES (
        p_workflow_id,
        'approve',
        'testing',
        'configured',
        p_approved_by,
        p_notes
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to activate workflow
CREATE OR REPLACE FUNCTION activate_workflow(
    p_workflow_id UUID
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE workflow_registry
    SET status = 'running'
    WHERE id = p_workflow_id AND status = 'configured';
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to record workflow execution
CREATE OR REPLACE FUNCTION record_workflow_execution(
    p_workflow_id UUID,
    p_execution_id VARCHAR(255),
    p_triggered_by VARCHAR(255),
    p_status VARCHAR(50),
    p_duration_ms INTEGER DEFAULT NULL,
    p_input_data JSONB DEFAULT NULL,
    p_output_data JSONB DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_execution_id UUID;
BEGIN
    INSERT INTO workflow_executions (
        workflow_id,
        execution_id,
        triggered_by,
        status,
        duration_ms,
        input_data,
        output_data,
        error_message,
        completed_at
    ) VALUES (
        p_workflow_id,
        p_execution_id,
        p_triggered_by,
        p_status,
        p_duration_ms,
        p_input_data,
        p_output_data,
        p_error_message,
        CASE WHEN p_status IN ('success', 'error', 'timeout') THEN CURRENT_TIMESTAMP ELSE NULL END
    )
    RETURNING id INTO v_execution_id;
    
    -- Update workflow metrics
    UPDATE workflow_registry
    SET 
        execution_count = execution_count + 1,
        last_execution = CURRENT_TIMESTAMP,
        avg_execution_time_ms = (
            SELECT AVG(duration_ms) 
            FROM workflow_executions 
            WHERE workflow_id = p_workflow_id 
            AND status = 'success'
        ),
        success_rate = (
            SELECT ROUND(100.0 * COUNT(CASE WHEN status = 'success' THEN 1 END) / COUNT(*), 2)
            FROM workflow_executions 
            WHERE workflow_id = p_workflow_id
        )
    WHERE id = p_workflow_id;
    
    RETURN v_execution_id;
END;
$$ LANGUAGE plpgsql;

-- Triggers

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workflow_registry_updated_at 
    BEFORE UPDATE ON workflow_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_templates_updated_at 
    BEFORE UPDATE ON workflow_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing
INSERT INTO workflow_registry (
    n8n_workflow_id,
    n8n_workflow_name,
    description,
    category,
    owner_team,
    status
) VALUES 
    ('test-001', 'Customer Welcome Email', 'Sends welcome email to new customers', 'customer_onboarding', 'marketing-team', 'draft'),
    ('test-002', 'Daily Sales Report', 'Generates and distributes daily sales metrics', 'reporting', 'sales-team', 'draft'),
    ('test-003', 'Invoice Processing', 'Processes incoming invoices and updates accounting', 'order_processing', 'finance-team', 'draft');