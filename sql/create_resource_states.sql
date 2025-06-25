-- Unified Resource State Management Schema
-- Tracks lifecycle states for all resources: workflows, MCP servers, teams

-- Resource states table: tracks current and historical states
CREATE TABLE IF NOT EXISTS resource_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) NOT NULL, -- 'workflow', 'mcp_server', 'mcp_client', 'team'
    resource_id UUID NOT NULL,
    resource_name VARCHAR(255) NOT NULL, -- Human-readable identifier
    current_state VARCHAR(50) NOT NULL,
    previous_state VARCHAR(50),
    state_metadata JSONB DEFAULT '{}', -- Additional state-specific data
    state_reason TEXT, -- Why the state changed
    transitioned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    transitioned_by VARCHAR(255) NOT NULL, -- User, system, or service that made the change
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_resource UNIQUE(resource_type, resource_id)
);

-- State transition history: audit log of all state changes
CREATE TABLE IF NOT EXISTS state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    resource_name VARCHAR(255) NOT NULL,
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    transition_reason TEXT,
    transition_metadata JSONB DEFAULT '{}',
    transitioned_by VARCHAR(255) NOT NULL,
    transitioned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT true,
    error_message TEXT
);

-- MCP Registry: Track MCP servers and clients
CREATE TABLE IF NOT EXISTS mcp_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    mcp_type VARCHAR(50) NOT NULL, -- 'server' or 'client'
    category VARCHAR(100), -- 'document-ingestion', 'data-processing', etc.
    description TEXT,
    source_path VARCHAR(500), -- Path to source code
    docker_image VARCHAR(255), -- Image name for deployment
    port INTEGER DEFAULT 50051, -- Default gRPC port
    protocol VARCHAR(50) DEFAULT 'grpc', -- 'grpc', 'http', 'websocket'
    capabilities JSONB DEFAULT '[]', -- List of MCP capabilities
    configuration JSONB DEFAULT '{}', -- Default configuration
    health_check_endpoint VARCHAR(255) DEFAULT '/health',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255)
);

-- Deployment requirements: Track what's needed before activation
CREATE TABLE IF NOT EXISTS deployment_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    requirement_type VARCHAR(100) NOT NULL, -- 'credential', 'dependency', 'configuration'
    requirement_name VARCHAR(255) NOT NULL,
    requirement_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'satisfied', 'failed'
    requirement_details JSONB DEFAULT '{}',
    checked_at TIMESTAMP WITH TIME ZONE,
    satisfied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_requirement UNIQUE(resource_type, resource_id, requirement_type, requirement_name)
);

-- Update workflows table to include deployment status
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS deployment_status VARCHAR(50) DEFAULT 'created';
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS deployment_metadata JSONB DEFAULT '{}';
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS last_state_change TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS state_changed_by VARCHAR(255);

-- Create indexes for performance
CREATE INDEX idx_resource_states_type_id ON resource_states(resource_type, resource_id);
CREATE INDEX idx_resource_states_current ON resource_states(current_state);
CREATE INDEX idx_resource_states_updated ON resource_states(updated_at DESC);
CREATE INDEX idx_transitions_resource ON state_transitions(resource_type, resource_id);
CREATE INDEX idx_transitions_time ON state_transitions(transitioned_at DESC);
CREATE INDEX idx_mcp_registry_type ON mcp_registry(mcp_type);
CREATE INDEX idx_mcp_registry_category ON mcp_registry(category);
CREATE INDEX idx_deployment_reqs_resource ON deployment_requirements(resource_type, resource_id);
CREATE INDEX idx_deployment_reqs_status ON deployment_requirements(requirement_status);

-- Views for common queries

-- Current state overview
CREATE OR REPLACE VIEW resource_state_overview AS
SELECT
    rs.resource_type,
    rs.current_state,
    COUNT(*) as count,
    MAX(rs.transitioned_at) as last_transition
FROM resource_states rs
GROUP BY rs.resource_type, rs.current_state
ORDER BY rs.resource_type, rs.current_state;

-- Resources awaiting action
CREATE OR REPLACE VIEW resources_awaiting_action AS
SELECT
    rs.resource_type,
    rs.resource_id,
    rs.resource_name,
    rs.current_state,
    rs.transitioned_at,
    rs.state_reason
FROM resource_states rs
WHERE rs.current_state IN ('created', 'registered', 'deployed', 'failed')
ORDER BY rs.transitioned_at DESC;

-- MCP deployment status
CREATE OR REPLACE VIEW mcp_deployment_status AS
SELECT
    m.name,
    m.display_name,
    m.mcp_type,
    m.category,
    rs.current_state,
    rs.state_reason,
    rs.transitioned_at
FROM mcp_registry m
LEFT JOIN resource_states rs ON rs.resource_id = m.id AND rs.resource_type = 'mcp_server'
ORDER BY m.name;

-- Workflow deployment pipeline
CREATE OR REPLACE VIEW workflow_deployment_pipeline AS
SELECT
    w.name,
    w.category,
    w.owner_team,
    w.deployment_status,
    w.validation_status,
    w.n8n_active,
    rs.current_state as state_tracking,
    w.last_state_change,
    w.state_changed_by
FROM workflows w
LEFT JOIN resource_states rs ON rs.resource_id = w.id AND rs.resource_type = 'workflow'
ORDER BY w.last_state_change DESC;

-- Functions for state management

-- Function: Transition resource state
CREATE OR REPLACE FUNCTION transition_resource_state(
    p_resource_type VARCHAR,
    p_resource_id UUID,
    p_resource_name VARCHAR,
    p_new_state VARCHAR,
    p_reason TEXT,
    p_transitioned_by VARCHAR,
    p_metadata JSONB DEFAULT '{}'
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_state VARCHAR;
    v_success BOOLEAN := true;
BEGIN
    -- Get current state
    SELECT current_state INTO v_current_state
    FROM resource_states
    WHERE resource_type = p_resource_type AND resource_id = p_resource_id;

    -- Insert or update resource state
    INSERT INTO resource_states (
        resource_type, resource_id, resource_name,
        current_state, previous_state, state_reason,
        transitioned_by, state_metadata
    ) VALUES (
        p_resource_type, p_resource_id, p_resource_name,
        p_new_state, v_current_state, p_reason,
        p_transitioned_by, p_metadata
    )
    ON CONFLICT (resource_type, resource_id) DO UPDATE SET
        current_state = p_new_state,
        previous_state = EXCLUDED.previous_state,
        state_reason = p_reason,
        state_metadata = p_metadata,
        transitioned_by = p_transitioned_by,
        transitioned_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP;

    -- Log transition
    INSERT INTO state_transitions (
        resource_type, resource_id, resource_name,
        from_state, to_state, transition_reason,
        transition_metadata, transitioned_by, success
    ) VALUES (
        p_resource_type, p_resource_id, p_resource_name,
        v_current_state, p_new_state, p_reason,
        p_metadata, p_transitioned_by, v_success
    );

    -- Update workflow table if applicable
    IF p_resource_type = 'workflow' THEN
        UPDATE workflows
        SET deployment_status = p_new_state,
            deployment_metadata = p_metadata,
            last_state_change = CURRENT_TIMESTAMP,
            state_changed_by = p_transitioned_by
        WHERE id = p_resource_id;
    END IF;

    RETURN v_success;
END;
$$ LANGUAGE plpgsql;

-- Function: Check deployment requirements
CREATE OR REPLACE FUNCTION check_deployment_requirements(
    p_resource_type VARCHAR,
    p_resource_id UUID
) RETURNS TABLE (
    all_satisfied BOOLEAN,
    pending_count INTEGER,
    failed_count INTEGER,
    requirements JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(bool_and(requirement_status = 'satisfied'), false) as all_satisfied,
        COUNT(*) FILTER (WHERE requirement_status = 'pending')::INTEGER as pending_count,
        COUNT(*) FILTER (WHERE requirement_status = 'failed')::INTEGER as failed_count,
        jsonb_agg(jsonb_build_object(
            'type', requirement_type,
            'name', requirement_name,
            'status', requirement_status,
            'details', requirement_details
        )) as requirements
    FROM deployment_requirements
    WHERE resource_type = p_resource_type AND resource_id = p_resource_id;
END;
$$ LANGUAGE plpgsql;

-- Initial state data for common transitions
INSERT INTO resource_states (resource_type, resource_id, resource_name, current_state, transitioned_by)
SELECT 'workflow', id, name, deployment_status, COALESCE(state_changed_by, 'system')
FROM workflows
WHERE NOT EXISTS (
    SELECT 1 FROM resource_states rs
    WHERE rs.resource_type = 'workflow' AND rs.resource_id = workflows.id
);

-- Triggers
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_resource_states_updated_at
BEFORE UPDATE ON resource_states
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_mcp_registry_updated_at
BEFORE UPDATE ON mcp_registry
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- Grant permissions
GRANT ALL ON resource_states TO anon;
GRANT ALL ON resource_states TO authenticated;
GRANT ALL ON state_transitions TO anon;
GRANT ALL ON state_transitions TO authenticated;
GRANT ALL ON mcp_registry TO anon;
GRANT ALL ON mcp_registry TO authenticated;
GRANT ALL ON deployment_requirements TO anon;
GRANT ALL ON deployment_requirements TO authenticated;
