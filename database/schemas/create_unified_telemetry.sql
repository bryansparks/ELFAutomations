-- Unified Communication Telemetry Schema
-- Captures lightweight telemetry for both MCP and A2A communications
-- Designed for minimal performance impact with fire-and-forget logging

-- Main telemetry table for all communication events
CREATE TABLE IF NOT EXISTS communication_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    protocol VARCHAR(10) NOT NULL CHECK (protocol IN ('mcp', 'a2a', 'n8n')),

    -- Common fields for all protocols
    source_id VARCHAR(255) NOT NULL, -- team_id, workflow_id, or service_id
    source_type VARCHAR(50) NOT NULL, -- 'team', 'workflow', 'service'
    target_id VARCHAR(255) NOT NULL, -- mcp_name, team_id, or external_service
    target_type VARCHAR(50) NOT NULL, -- 'mcp', 'team', 'external'
    operation VARCHAR(100) NOT NULL, -- 'tool_call', 'send_task', 'workflow_step'

    -- Performance metrics
    duration_ms INTEGER,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'error', 'timeout', 'cancelled')),

    -- MCP specific fields (null for A2A/N8N)
    tool_name VARCHAR(100),
    tool_category VARCHAR(50),

    -- A2A specific fields (null for MCP/N8N)
    task_description TEXT,
    capabilities_required TEXT[],
    message_type VARCHAR(50), -- 'task_request', 'task_response', 'status_update'

    -- N8N specific fields (null for MCP/A2A)
    workflow_id UUID,
    workflow_name VARCHAR(255),
    workflow_node VARCHAR(100),

    -- General metadata
    payload_size_bytes INTEGER,
    error_message TEXT,
    error_code VARCHAR(50),
    correlation_id VARCHAR(100), -- For tracing related communications
    parent_correlation_id VARCHAR(100), -- For nested operations

    -- Resource usage (optional)
    tokens_used INTEGER,
    estimated_cost DECIMAL(10,4),

    -- Additional context
    metadata JSONB DEFAULT '{}',

    -- Indexes for common queries
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_telemetry_timestamp ON communication_telemetry(timestamp DESC);
CREATE INDEX idx_telemetry_source ON communication_telemetry(source_id, source_type);
CREATE INDEX idx_telemetry_target ON communication_telemetry(target_id, target_type);
CREATE INDEX idx_telemetry_protocol ON communication_telemetry(protocol);
CREATE INDEX idx_telemetry_status ON communication_telemetry(status);
CREATE INDEX idx_telemetry_correlation ON communication_telemetry(correlation_id);

-- Materialized view for real-time metrics (refresh every minute)
CREATE MATERIALIZED VIEW communication_metrics_realtime AS
SELECT
    date_trunc('minute', timestamp) as minute,
    protocol,
    source_id,
    source_type,
    target_id,
    target_type,
    COUNT(*) as request_count,
    AVG(duration_ms)::INTEGER as avg_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)::INTEGER as p95_duration_ms,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
    ROUND(COUNT(CASE WHEN status = 'error' THEN 1 END)::NUMERIC / COUNT(*) * 100, 2) as error_rate
FROM communication_telemetry
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY 1, 2, 3, 4, 5, 6;

-- Create index on materialized view
CREATE INDEX idx_metrics_minute ON communication_metrics_realtime(minute DESC);

-- Communication patterns view for Control Center
CREATE VIEW communication_patterns AS
SELECT
    source_id,
    source_type,
    target_id,
    target_type,
    protocol,
    COUNT(*) as total_calls,
    AVG(duration_ms)::INTEGER as avg_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
    COUNT(DISTINCT DATE(timestamp)) as active_days,
    MAX(timestamp) as last_communication
FROM communication_telemetry
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY source_id, source_type, target_id, target_type, protocol;

-- System health overview
CREATE VIEW system_health_overview AS
SELECT
    protocol,
    COUNT(DISTINCT source_id) as active_sources,
    COUNT(DISTINCT target_id) as active_targets,
    COUNT(*) as total_requests_5min,
    AVG(duration_ms)::INTEGER as avg_duration_ms,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors_5min,
    ROUND(COUNT(CASE WHEN status = 'error' THEN 1 END)::NUMERIC / COUNT(*) * 100, 2) as error_rate
FROM communication_telemetry
WHERE timestamp > NOW() - INTERVAL '5 minutes'
GROUP BY protocol;

-- Top communication pairs
CREATE VIEW top_communication_pairs AS
SELECT
    source_id || ' (' || source_type || ')' as source,
    target_id || ' (' || target_type || ')' as target,
    protocol,
    COUNT(*) as call_count,
    AVG(duration_ms)::INTEGER as avg_duration_ms,
    SUM(COALESCE(tokens_used, 0)) as total_tokens,
    SUM(COALESCE(estimated_cost, 0))::DECIMAL(10,2) as total_cost
FROM communication_telemetry
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY source_id, source_type, target_id, target_type, protocol
ORDER BY call_count DESC
LIMIT 20;

-- Function to record telemetry (fire-and-forget)
CREATE OR REPLACE FUNCTION record_telemetry(
    p_protocol VARCHAR(10),
    p_source_id VARCHAR(255),
    p_source_type VARCHAR(50),
    p_target_id VARCHAR(255),
    p_target_type VARCHAR(50),
    p_operation VARCHAR(100),
    p_status VARCHAR(20),
    p_duration_ms INTEGER DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_telemetry_id UUID;
BEGIN
    INSERT INTO communication_telemetry (
        protocol, source_id, source_type, target_id, target_type,
        operation, status, duration_ms, metadata
    ) VALUES (
        p_protocol, p_source_id, p_source_type, p_target_id, p_target_type,
        p_operation, p_status, p_duration_ms, p_metadata
    ) RETURNING id INTO v_telemetry_id;

    RETURN v_telemetry_id;
END;
$$ LANGUAGE plpgsql;

-- Lightweight function for A2A telemetry
CREATE OR REPLACE FUNCTION record_a2a_telemetry(
    p_source_team VARCHAR(255),
    p_target_team VARCHAR(255),
    p_task_description TEXT,
    p_status VARCHAR(20),
    p_duration_ms INTEGER,
    p_correlation_id VARCHAR(100) DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO communication_telemetry (
        protocol, source_id, source_type, target_id, target_type,
        operation, status, duration_ms, task_description, correlation_id
    ) VALUES (
        'a2a', p_source_team, 'team', p_target_team, 'team',
        'send_task', p_status, p_duration_ms, p_task_description, p_correlation_id
    );
END;
$$ LANGUAGE plpgsql;

-- Lightweight function for MCP telemetry
CREATE OR REPLACE FUNCTION record_mcp_telemetry(
    p_source_id VARCHAR(255),
    p_mcp_name VARCHAR(255),
    p_tool_name VARCHAR(100),
    p_status VARCHAR(20),
    p_duration_ms INTEGER,
    p_tokens_used INTEGER DEFAULT NULL,
    p_correlation_id VARCHAR(100) DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO communication_telemetry (
        protocol, source_id, source_type, target_id, target_type,
        operation, tool_name, status, duration_ms, tokens_used, correlation_id
    ) VALUES (
        'mcp', p_source_id, 'team', p_mcp_name, 'mcp',
        'tool_call', p_tool_name, p_status, p_duration_ms, p_tokens_used, p_correlation_id
    );
END;
$$ LANGUAGE plpgsql;

-- Refresh function for materialized view (call via cron)
CREATE OR REPLACE FUNCTION refresh_telemetry_metrics() RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY communication_metrics_realtime;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT ON communication_telemetry TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON FUNCTION record_telemetry TO authenticated;
GRANT EXECUTE ON FUNCTION record_a2a_telemetry TO authenticated;
GRANT EXECUTE ON FUNCTION record_mcp_telemetry TO authenticated;
