-- Unified Registry Schema
-- Ensures all entities (Teams, MCPs, N8N workflows) are registered with current state
-- This complements existing registries by providing a unified view and state tracking

-- Unified entity registry for all system components
CREATE TABLE IF NOT EXISTS unified_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('team', 'mcp_server', 'mcp_client', 'n8n_workflow', 'service')),
    entity_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    
    -- Registration metadata
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    registered_by VARCHAR(255) NOT NULL, -- 'system', 'team_factory', 'manual', etc.
    registration_source VARCHAR(100), -- 'gitops', 'api', 'factory', 'manual'
    
    -- Current state
    current_state VARCHAR(50) NOT NULL DEFAULT 'registered',
    state_updated_at TIMESTAMPTZ DEFAULT NOW(),
    health_status VARCHAR(50) DEFAULT 'unknown', -- 'healthy', 'degraded', 'unhealthy', 'unknown'
    last_health_check TIMESTAMPTZ,
    
    -- Location and access
    endpoint_url VARCHAR(500), -- HTTP endpoint, gRPC address, etc.
    namespace VARCHAR(100), -- K8s namespace
    deployment_type VARCHAR(50), -- 'k8s', 'docker', 'local', 'cloud'
    
    -- Capabilities and metadata
    capabilities TEXT[], -- What this entity can do
    tags TEXT[], -- Additional categorization
    metadata JSONB DEFAULT '{}', -- Flexible additional data
    
    -- Version and updates
    version VARCHAR(50),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    
    -- Relationships
    parent_entity_id VARCHAR(255), -- For hierarchical relationships
    department VARCHAR(100), -- Organizational unit
    
    -- Monitoring
    last_activity TIMESTAMPTZ,
    activity_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    
    -- Unique constraint
    CONSTRAINT unique_entity UNIQUE(entity_id, entity_type)
);

-- Create indexes
CREATE INDEX idx_registry_type ON unified_registry(entity_type);
CREATE INDEX idx_registry_state ON unified_registry(current_state);
CREATE INDEX idx_registry_health ON unified_registry(health_status);
CREATE INDEX idx_registry_updated ON unified_registry(last_updated DESC);

-- State transition tracking
CREATE TABLE IF NOT EXISTS registry_state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    health_status VARCHAR(50),
    transition_reason TEXT,
    transitioned_by VARCHAR(255) NOT NULL,
    transitioned_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Registration audit log
CREATE TABLE IF NOT EXISTS registration_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'registered', 'updated', 'deregistered', 'health_check'
    action_by VARCHAR(255) NOT NULL,
    action_at TIMESTAMPTZ DEFAULT NOW(),
    details JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT true,
    error_message TEXT
);

-- View for current system state
CREATE VIEW system_entity_state AS
SELECT 
    entity_type,
    current_state,
    health_status,
    COUNT(*) as count,
    COUNT(CASE WHEN last_activity > NOW() - INTERVAL '5 minutes' THEN 1 END) as active_last_5min,
    COUNT(CASE WHEN health_status = 'healthy' THEN 1 END) as healthy_count,
    COUNT(CASE WHEN health_status IN ('degraded', 'unhealthy') THEN 1 END) as unhealthy_count
FROM unified_registry
GROUP BY entity_type, current_state, health_status
ORDER BY entity_type, current_state;

-- View for entity relationships
CREATE VIEW entity_hierarchy AS
WITH RECURSIVE hierarchy AS (
    -- Base case: top-level entities
    SELECT 
        entity_id,
        entity_name,
        entity_type,
        parent_entity_id,
        department,
        current_state,
        health_status,
        0 as level,
        entity_id::TEXT as path
    FROM unified_registry
    WHERE parent_entity_id IS NULL
    
    UNION ALL
    
    -- Recursive case
    SELECT 
        r.entity_id,
        r.entity_name,
        r.entity_type,
        r.parent_entity_id,
        r.department,
        r.current_state,
        r.health_status,
        h.level + 1,
        h.path || ' > ' || r.entity_id
    FROM unified_registry r
    INNER JOIN hierarchy h ON r.parent_entity_id = h.entity_id
)
SELECT * FROM hierarchy ORDER BY path;

-- Registration functions

-- Register or update an entity
CREATE OR REPLACE FUNCTION register_entity(
    p_entity_id VARCHAR(255),
    p_entity_type VARCHAR(50),
    p_entity_name VARCHAR(255),
    p_registered_by VARCHAR(255),
    p_metadata JSONB DEFAULT '{}',
    p_capabilities TEXT[] DEFAULT NULL,
    p_endpoint_url VARCHAR(500) DEFAULT NULL,
    p_parent_entity_id VARCHAR(255) DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_registry_id UUID;
    v_existing_id UUID;
BEGIN
    -- Check if entity already exists
    SELECT id INTO v_existing_id
    FROM unified_registry
    WHERE entity_id = p_entity_id AND entity_type = p_entity_type;
    
    IF v_existing_id IS NOT NULL THEN
        -- Update existing
        UPDATE unified_registry
        SET 
            entity_name = p_entity_name,
            metadata = p_metadata,
            capabilities = COALESCE(p_capabilities, capabilities),
            endpoint_url = COALESCE(p_endpoint_url, endpoint_url),
            parent_entity_id = COALESCE(p_parent_entity_id, parent_entity_id),
            last_updated = NOW()
        WHERE id = v_existing_id
        RETURNING id INTO v_registry_id;
        
        -- Log update
        INSERT INTO registration_audit (entity_id, entity_type, action, action_by, details)
        VALUES (p_entity_id, p_entity_type, 'updated', p_registered_by, p_metadata);
    ELSE
        -- Insert new
        INSERT INTO unified_registry (
            entity_id, entity_type, entity_name, registered_by,
            metadata, capabilities, endpoint_url, parent_entity_id,
            current_state
        ) VALUES (
            p_entity_id, p_entity_type, p_entity_name, p_registered_by,
            p_metadata, p_capabilities, p_endpoint_url, p_parent_entity_id,
            'registered'
        ) RETURNING id INTO v_registry_id;
        
        -- Log registration
        INSERT INTO registration_audit (entity_id, entity_type, action, action_by, details)
        VALUES (p_entity_id, p_entity_type, 'registered', p_registered_by, p_metadata);
    END IF;
    
    RETURN v_registry_id;
END;
$$ LANGUAGE plpgsql;

-- Update entity state
CREATE OR REPLACE FUNCTION update_entity_state(
    p_entity_id VARCHAR(255),
    p_entity_type VARCHAR(50),
    p_new_state VARCHAR(50),
    p_health_status VARCHAR(50) DEFAULT NULL,
    p_updated_by VARCHAR(255) DEFAULT 'system',
    p_reason TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_old_state VARCHAR(50);
    v_old_health VARCHAR(50);
BEGIN
    -- Get current state
    SELECT current_state, health_status 
    INTO v_old_state, v_old_health
    FROM unified_registry
    WHERE entity_id = p_entity_id AND entity_type = p_entity_type;
    
    IF v_old_state IS NULL THEN
        RETURN FALSE; -- Entity not found
    END IF;
    
    -- Update registry
    UPDATE unified_registry
    SET 
        current_state = p_new_state,
        health_status = COALESCE(p_health_status, health_status),
        state_updated_at = NOW(),
        last_health_check = CASE 
            WHEN p_health_status IS NOT NULL THEN NOW() 
            ELSE last_health_check 
        END
    WHERE entity_id = p_entity_id AND entity_type = p_entity_type;
    
    -- Log transition
    INSERT INTO registry_state_transitions (
        entity_id, entity_type, from_state, to_state, 
        health_status, transition_reason, transitioned_by
    ) VALUES (
        p_entity_id, p_entity_type, v_old_state, p_new_state,
        COALESCE(p_health_status, v_old_health), p_reason, p_updated_by
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Record entity activity
CREATE OR REPLACE FUNCTION record_entity_activity(
    p_entity_id VARCHAR(255),
    p_entity_type VARCHAR(50),
    p_is_error BOOLEAN DEFAULT FALSE
) RETURNS VOID AS $$
BEGIN
    UPDATE unified_registry
    SET 
        last_activity = NOW(),
        activity_count = activity_count + 1,
        error_count = CASE 
            WHEN p_is_error THEN error_count + 1 
            ELSE error_count 
        END
    WHERE entity_id = p_entity_id AND entity_type = p_entity_type;
END;
$$ LANGUAGE plpgsql;

-- Check registration gaps
CREATE OR REPLACE FUNCTION check_registration_gaps()
RETURNS TABLE (
    gap_type VARCHAR(100),
    entity_identifier VARCHAR(255),
    details JSONB
) AS $$
BEGIN
    -- Teams not in unified registry
    RETURN QUERY
    SELECT 
        'missing_team'::VARCHAR(100) as gap_type,
        t.id::VARCHAR(255) as entity_identifier,
        jsonb_build_object(
            'team_name', t.name,
            'framework', t.framework,
            'created_at', t.created_at
        ) as details
    FROM teams t
    LEFT JOIN unified_registry ur ON ur.entity_id = t.id AND ur.entity_type = 'team'
    WHERE ur.id IS NULL;
    
    -- MCPs not in unified registry
    RETURN QUERY
    SELECT 
        'missing_mcp'::VARCHAR(100) as gap_type,
        m.id::VARCHAR(255) as entity_identifier,
        jsonb_build_object(
            'mcp_name', m.name,
            'type', m.type,
            'created_at', m.created_at
        ) as details
    FROM mcps m
    LEFT JOIN unified_registry ur ON ur.entity_id = m.id AND ur.entity_type = 'mcp_server'
    WHERE ur.id IS NULL;
    
    -- Stale registrations (no activity in 24 hours)
    RETURN QUERY
    SELECT 
        'stale_registration'::VARCHAR(100) as gap_type,
        ur.entity_id as entity_identifier,
        jsonb_build_object(
            'entity_type', ur.entity_type,
            'entity_name', ur.entity_name,
            'last_activity', ur.last_activity,
            'health_status', ur.health_status
        ) as details
    FROM unified_registry ur
    WHERE ur.last_activity < NOW() - INTERVAL '24 hours'
       OR ur.last_activity IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON unified_registry TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;