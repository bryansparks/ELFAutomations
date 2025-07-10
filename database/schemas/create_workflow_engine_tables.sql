-- Workflow Engine Schema for ElfAutomations
-- Enables complex multi-team orchestration with state management

-- Workflow definitions table
CREATE TABLE IF NOT EXISTS workflow_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    definition JSONB NOT NULL, -- The workflow DSL (YAML converted to JSON)
    schema_version VARCHAR(20) DEFAULT '1.0', -- For future DSL evolution
    category VARCHAR(100), -- e.g., 'customer', 'operations', 'development'
    tags TEXT[], -- For search and filtering

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Status management
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, deprecated, archived
    published_at TIMESTAMP WITH TIME ZONE,
    deprecated_at TIMESTAMP WITH TIME ZONE,
    deprecation_reason TEXT,

    -- Constraints and indexes
    CONSTRAINT unique_workflow_version UNIQUE(name, version),
    INDEX idx_workflow_status (status),
    INDEX idx_workflow_tags USING GIN (tags)
);

-- Workflow instances (running workflows)
CREATE TABLE IF NOT EXISTS workflow_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id UUID NOT NULL REFERENCES workflow_definitions(id),

    -- Instance details
    name VARCHAR(255) NOT NULL, -- Human-readable instance name
    status VARCHAR(50) NOT NULL DEFAULT 'initializing',
    -- statuses: initializing, running, paused, completed, failed, cancelled, timed_out

    -- State management
    current_step VARCHAR(255),
    context JSONB DEFAULT '{}', -- Workflow variables and state

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    paused_at TIMESTAMP WITH TIME ZONE,
    resumed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE, -- Calculated from workflow timeout

    -- Error handling
    error_details JSONB,
    error_count INTEGER DEFAULT 0,
    last_error_at TIMESTAMP WITH TIME ZONE,

    -- Hierarchy (for sub-workflows)
    parent_instance_id UUID REFERENCES workflow_instances(id),
    root_instance_id UUID, -- Top-level workflow in the hierarchy
    depth INTEGER DEFAULT 0, -- Nesting depth

    -- Metadata
    triggered_by VARCHAR(255), -- team_id, user_id, or system event
    trigger_source VARCHAR(100), -- manual, scheduled, event, api
    priority INTEGER DEFAULT 5, -- 1-10, higher = more important

    -- Indexes
    INDEX idx_instance_status (status),
    INDEX idx_instance_started (started_at DESC),
    INDEX idx_instance_deadline (deadline),
    INDEX idx_instance_parent (parent_instance_id)
);

-- Step executions tracking
CREATE TABLE IF NOT EXISTS workflow_step_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,

    -- Step identification
    step_id VARCHAR(255) NOT NULL, -- From workflow definition
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(50) NOT NULL, -- task, parallel, sequence, condition, loop, subworkflow, approval

    -- Execution state
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- statuses: pending, ready, running, completed, failed, skipped, cancelled, timed_out

    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ready_at TIMESTAMP WITH TIME ZONE, -- When dependencies were met
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Assignment
    assigned_team VARCHAR(255),
    assigned_agent VARCHAR(255),
    claimed_at TIMESTAMP WITH TIME ZONE,

    -- Data flow
    input_data JSONB,
    output_data JSONB,

    -- Error handling
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Dependencies
    depends_on TEXT[], -- Array of step_ids that must complete first

    -- Indexes
    INDEX idx_step_instance_status (instance_id, status),
    INDEX idx_step_assigned_team (assigned_team, status),
    INDEX idx_step_created (created_at DESC)
);

-- Team task queue for workflow assignments
CREATE TABLE IF NOT EXISTS workflow_team_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Workflow reference
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    step_execution_id UUID NOT NULL REFERENCES workflow_step_executions(id) ON DELETE CASCADE,

    -- Task details
    team_id VARCHAR(255) NOT NULL,
    task_type VARCHAR(255) NOT NULL, -- The action to perform
    task_title VARCHAR(500), -- Human-readable title
    task_description TEXT, -- Detailed description

    -- Priority and timing
    priority INTEGER DEFAULT 5, -- 1-10, inherited from workflow
    deadline TIMESTAMP WITH TIME ZONE,
    estimated_duration INTERVAL,

    -- Input/Output
    input_data JSONB NOT NULL,
    output_schema JSONB, -- Expected output format

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending', -- pending, claimed, in_progress, completed, failed, cancelled
    claimed_at TIMESTAMP WITH TIME ZONE,
    claimed_by VARCHAR(255), -- Specific agent that claimed it
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Results
    output_data JSONB,
    error_message TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_task_team_status (team_id, status, priority DESC),
    INDEX idx_task_created (created_at),
    INDEX idx_task_deadline (deadline)
);

-- Workflow triggers configuration
CREATE TABLE IF NOT EXISTS workflow_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id UUID NOT NULL REFERENCES workflow_definitions(id),

    -- Trigger configuration
    trigger_name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL, -- event, schedule, webhook, condition, manual
    trigger_config JSONB NOT NULL,
    /* Example configs:
       Event: {"event_type": "project_created", "filters": {"priority": "high"}}
       Schedule: {"cron": "0 9 * * MON", "timezone": "UTC"}
       Webhook: {"endpoint": "/webhooks/workflow/customer-onboard", "auth": "bearer"}
       Condition: {"query": "SELECT COUNT(*) FROM tasks WHERE status='pending'", "threshold": 10}
    */

    -- Input mapping
    input_mapping JSONB, -- How to map trigger data to workflow inputs

    -- State
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),

    -- Constraints
    CONSTRAINT unique_trigger_name UNIQUE(workflow_definition_id, trigger_name),
    INDEX idx_trigger_active (is_active, trigger_type)
);

-- Workflow metrics for analytics
CREATE TABLE IF NOT EXISTS workflow_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,

    -- Timing metrics
    total_duration INTERVAL,
    active_duration INTERVAL, -- Excluding paused time
    queue_time INTERVAL, -- Time steps spent waiting for teams

    -- Step metrics
    total_steps INTEGER,
    completed_steps INTEGER,
    failed_steps INTEGER,
    skipped_steps INTEGER,

    -- Team metrics
    teams_involved TEXT[],
    team_response_times JSONB, -- {"team_id": avg_response_time_seconds}

    -- Cost metrics
    estimated_llm_cost DECIMAL(10, 2),
    actual_llm_cost DECIMAL(10, 2),

    -- Calculated at workflow completion
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_metrics_instance (instance_id)
);

-- Audit log for compliance and debugging
CREATE TABLE IF NOT EXISTS workflow_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,

    -- Event details
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    /* Event types:
       workflow_started, workflow_completed, workflow_failed, workflow_cancelled,
       step_started, step_completed, step_failed, step_retried,
       task_assigned, task_claimed, task_completed, task_failed,
       approval_requested, approval_granted, approval_denied,
       error_occurred, timeout_occurred, manual_intervention
    */

    -- Context
    step_id VARCHAR(255),
    team_id VARCHAR(255),
    agent_id VARCHAR(255),

    -- Details
    details JSONB NOT NULL,

    -- Indexes
    INDEX idx_audit_instance_time (instance_id, timestamp DESC),
    INDEX idx_audit_event_type (event_type, timestamp DESC)
);

-- Helper views for common queries

-- Active workflows view
CREATE OR REPLACE VIEW active_workflows AS
SELECT
    wi.id,
    wi.name,
    wd.name as workflow_type,
    wi.status,
    wi.current_step,
    wi.started_at,
    wi.deadline,
    wi.triggered_by,
    COUNT(DISTINCT wse.assigned_team) as teams_involved,
    SUM(CASE WHEN wse.status = 'completed' THEN 1 ELSE 0 END) as completed_steps,
    COUNT(wse.id) as total_steps
FROM workflow_instances wi
JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
LEFT JOIN workflow_step_executions wse ON wi.id = wse.instance_id
WHERE wi.status IN ('running', 'paused')
GROUP BY wi.id, wi.name, wd.name, wi.status, wi.current_step,
         wi.started_at, wi.deadline, wi.triggered_by;

-- Team workload view
CREATE OR REPLACE VIEW team_workflow_workload AS
SELECT
    team_id,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_tasks,
    COUNT(CASE WHEN status = 'completed' AND completed_at > NOW() - INTERVAL '24 hours' THEN 1 END) as completed_today,
    AVG(EXTRACT(EPOCH FROM (completed_at - claimed_at))) as avg_completion_seconds,
    MIN(deadline) as next_deadline
FROM workflow_team_tasks
WHERE status IN ('pending', 'in_progress')
   OR completed_at > NOW() - INTERVAL '24 hours'
GROUP BY team_id;

-- Workflow performance view
CREATE OR REPLACE VIEW workflow_performance AS
SELECT
    wd.name as workflow_name,
    wd.version,
    COUNT(wi.id) as total_runs,
    AVG(EXTRACT(EPOCH FROM (wi.completed_at - wi.started_at))) as avg_duration_seconds,
    SUM(CASE WHEN wi.status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN wi.status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    SUM(CASE WHEN wi.status = 'timed_out' THEN 1 ELSE 0 END) as timed_out_runs
FROM workflow_definitions wd
LEFT JOIN workflow_instances wi ON wd.id = wi.workflow_definition_id
WHERE wi.started_at > NOW() - INTERVAL '30 days'
GROUP BY wd.name, wd.version
ORDER BY total_runs DESC;

-- Functions for workflow operations

-- Function to check if step dependencies are met
CREATE OR REPLACE FUNCTION check_step_dependencies(
    p_instance_id UUID,
    p_step_id VARCHAR(255),
    p_depends_on TEXT[]
) RETURNS BOOLEAN AS $$
BEGIN
    -- If no dependencies, return true
    IF p_depends_on IS NULL OR array_length(p_depends_on, 1) IS NULL THEN
        RETURN TRUE;
    END IF;

    -- Check if all dependencies are completed
    RETURN NOT EXISTS (
        SELECT 1
        FROM unnest(p_depends_on) AS dep_step_id
        LEFT JOIN workflow_step_executions wse
            ON wse.instance_id = p_instance_id
            AND wse.step_id = dep_step_id
        WHERE wse.status IS NULL
           OR wse.status NOT IN ('completed', 'skipped')
    );
END;
$$ LANGUAGE plpgsql;

-- Trigger to update workflow instance status
CREATE OR REPLACE FUNCTION update_workflow_instance_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the workflow instance when a step completes
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- Check if all steps are completed
        UPDATE workflow_instances wi
        SET status = CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM workflow_step_executions
                WHERE instance_id = NEW.instance_id
                AND status NOT IN ('completed', 'skipped')
            ) THEN 'completed'
            ELSE status
        END,
        completed_at = CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM workflow_step_executions
                WHERE instance_id = NEW.instance_id
                AND status NOT IN ('completed', 'skipped')
            ) THEN NOW()
            ELSE completed_at
        END
        WHERE id = NEW.instance_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_workflow_status
AFTER UPDATE ON workflow_step_executions
FOR EACH ROW
EXECUTE FUNCTION update_workflow_instance_status();

-- Trigger to update task timestamps
CREATE OR REPLACE FUNCTION update_task_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();

    IF NEW.status = 'claimed' AND OLD.status = 'pending' THEN
        NEW.claimed_at = NOW();
    ELSIF NEW.status = 'in_progress' AND OLD.status = 'claimed' THEN
        NEW.started_at = NOW();
    ELSIF NEW.status IN ('completed', 'failed') AND OLD.status = 'in_progress' THEN
        NEW.completed_at = NOW();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_task_timestamps
BEFORE UPDATE ON workflow_team_tasks
FOR EACH ROW
EXECUTE FUNCTION update_task_timestamps();

-- Add comments for documentation
COMMENT ON TABLE workflow_definitions IS 'Stores workflow templates that can be instantiated';
COMMENT ON TABLE workflow_instances IS 'Running instances of workflows with their current state';
COMMENT ON TABLE workflow_step_executions IS 'Tracks execution of individual workflow steps';
COMMENT ON TABLE workflow_team_tasks IS 'Queue of tasks assigned to teams by workflows';
COMMENT ON TABLE workflow_triggers IS 'Configures automatic workflow triggers';
COMMENT ON TABLE workflow_metrics IS 'Performance metrics for completed workflows';
COMMENT ON TABLE workflow_audit_log IS 'Detailed audit trail of all workflow events';
