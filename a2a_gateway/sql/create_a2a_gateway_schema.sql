-- A2A Gateway Schema for Supabase
-- Manages team registrations, routing decisions, and analytics

-- Drop existing tables if they exist
DROP TABLE IF EXISTS a2a_routing_log CASCADE;
DROP TABLE IF EXISTS a2a_teams CASCADE;

-- Teams registered with the gateway
CREATE TABLE a2a_teams (
    team_id VARCHAR(255) PRIMARY KEY,
    team_name VARCHAR(255) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    capabilities JSONB DEFAULT '[]'::jsonb,
    department VARCHAR(100),
    framework VARCHAR(50) DEFAULT 'CrewAI',
    metadata JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'healthy',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_health_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    health_stats JSONB DEFAULT '{
        "error_count": 0,
        "success_count": 0,
        "total_response_time_ms": 0,
        "consecutive_failures": 0,
        "circuit_breaker_open": false
    }'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Routing log for analytics and debugging
CREATE TABLE a2a_routing_log (
    id SERIAL PRIMARY KEY,
    from_team VARCHAR(255) NOT NULL,
    to_team VARCHAR(255) NOT NULL,
    task_description TEXT,
    required_capabilities JSONB DEFAULT '[]'::jsonb,
    routing_decision JSONB DEFAULT '{}'::jsonb,
    response_time_ms FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    routed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Foreign key constraints
    FOREIGN KEY (from_team) REFERENCES a2a_teams(team_id) ON DELETE CASCADE,
    FOREIGN KEY (to_team) REFERENCES a2a_teams(team_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_a2a_teams_status ON a2a_teams(status);
CREATE INDEX idx_a2a_teams_department ON a2a_teams(department);
CREATE INDEX idx_a2a_teams_capabilities ON a2a_teams USING GIN(capabilities);
CREATE INDEX idx_a2a_routing_log_from_team ON a2a_routing_log(from_team);
CREATE INDEX idx_a2a_routing_log_to_team ON a2a_routing_log(to_team);
CREATE INDEX idx_a2a_routing_log_routed_at ON a2a_routing_log(routed_at DESC);
CREATE INDEX idx_a2a_routing_log_status ON a2a_routing_log(status);

-- Function to update team health stats
CREATE OR REPLACE FUNCTION update_team_health_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the updated_at timestamp
    NEW.updated_at = NOW();
    
    -- Calculate average response time if stats were updated
    IF NEW.health_stats IS NOT NULL AND 
       (NEW.health_stats->>'success_count')::int > 0 THEN
        NEW.health_stats = jsonb_set(
            NEW.health_stats,
            '{average_response_time_ms}',
            to_jsonb(
                (NEW.health_stats->>'total_response_time_ms')::float / 
                (NEW.health_stats->>'success_count')::int
            )
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update health stats
CREATE TRIGGER update_team_health_stats_trigger
BEFORE UPDATE ON a2a_teams
FOR EACH ROW
EXECUTE FUNCTION update_team_health_stats();

-- View for team capabilities
CREATE OR REPLACE VIEW v_team_capabilities AS
SELECT 
    t.team_id,
    t.team_name,
    t.department,
    jsonb_array_elements_text(t.capabilities) as capability
FROM a2a_teams t
WHERE t.status = 'healthy';

-- View for routing analytics
CREATE OR REPLACE VIEW v_routing_analytics AS
SELECT 
    DATE_TRUNC('hour', routed_at) as hour,
    from_team,
    to_team,
    COUNT(*) as request_count,
    AVG(response_time_ms) as avg_response_time_ms,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failure_count,
    ROUND(
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)::numeric / 
        COUNT(*)::numeric * 100, 
        2
    ) as success_rate
FROM a2a_routing_log
WHERE routed_at > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', routed_at), from_team, to_team
ORDER BY hour DESC;

-- View for team health dashboard
CREATE OR REPLACE VIEW v_team_health_dashboard AS
SELECT 
    t.team_id,
    t.team_name,
    t.department,
    t.status,
    t.last_health_check,
    EXTRACT(EPOCH FROM (NOW() - t.last_health_check)) as seconds_since_last_check,
    (t.health_stats->>'error_count')::int as error_count,
    (t.health_stats->>'success_count')::int as success_count,
    (t.health_stats->>'average_response_time_ms')::float as avg_response_time_ms,
    (t.health_stats->>'consecutive_failures')::int as consecutive_failures,
    (t.health_stats->>'circuit_breaker_open')::boolean as circuit_breaker_open,
    CASE 
        WHEN (t.health_stats->>'success_count')::int + (t.health_stats->>'error_count')::int > 0 
        THEN ROUND(
            (t.health_stats->>'success_count')::numeric / 
            ((t.health_stats->>'success_count')::int + (t.health_stats->>'error_count')::int)::numeric * 100, 
            2
        )
        ELSE 0
    END as success_rate,
    array_length(ARRAY(SELECT jsonb_array_elements_text(t.capabilities)), 1) as capability_count
FROM a2a_teams t
ORDER BY t.department, t.team_name;

-- Function to find teams by capability
CREATE OR REPLACE FUNCTION find_teams_by_capability(required_capabilities text[])
RETURNS TABLE(team_id varchar, team_name varchar, endpoint varchar, match_score int) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.team_id,
        t.team_name,
        t.endpoint,
        COUNT(*)::int as match_score
    FROM a2a_teams t
    WHERE 
        t.status = 'healthy' AND
        t.capabilities ?| required_capabilities
    GROUP BY t.team_id, t.team_name, t.endpoint
    HAVING COUNT(*) = array_length(required_capabilities, 1)
    ORDER BY match_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get routing recommendations
CREATE OR REPLACE FUNCTION get_routing_recommendation(
    p_task_description text,
    p_required_capabilities text[] DEFAULT NULL
)
RETURNS TABLE(
    team_id varchar, 
    team_name varchar, 
    recommendation_score float,
    reason text
) AS $$
BEGIN
    RETURN QUERY
    WITH team_scores AS (
        SELECT 
            t.team_id,
            t.team_name,
            -- Base score from capabilities match
            CASE 
                WHEN p_required_capabilities IS NOT NULL THEN
                    (SELECT COUNT(*) 
                     FROM unnest(p_required_capabilities) rc 
                     WHERE t.capabilities ? rc)::float / 
                     GREATEST(array_length(p_required_capabilities, 1), 1)::float * 50
                ELSE 0
            END as capability_score,
            -- Health score (0-30 points)
            CASE 
                WHEN (t.health_stats->>'circuit_breaker_open')::boolean THEN 0
                WHEN t.status = 'healthy' THEN 30
                WHEN t.status = 'degraded' THEN 15
                ELSE 0
            END as health_score,
            -- Performance score (0-20 points based on success rate)
            CASE 
                WHEN (t.health_stats->>'success_count')::int > 0 THEN
                    ((t.health_stats->>'success_count')::float / 
                     ((t.health_stats->>'success_count')::int + (t.health_stats->>'error_count')::int)::float) * 20
                ELSE 10 -- Default score for new teams
            END as performance_score
        FROM a2a_teams t
        WHERE t.status != 'unhealthy'
    )
    SELECT 
        ts.team_id,
        ts.team_name,
        ROUND((ts.capability_score + ts.health_score + ts.performance_score)::numeric, 2) as recommendation_score,
        CASE 
            WHEN ts.capability_score > 0 THEN 
                'Capability match: ' || ROUND(ts.capability_score::numeric, 0) || '%, ' ||
                'Health: ' || ROUND(ts.health_score::numeric, 0) || '/30, ' ||
                'Performance: ' || ROUND(ts.performance_score::numeric, 0) || '/20'
            ELSE
                'Health: ' || ROUND(ts.health_score::numeric, 0) || '/30, ' ||
                'Performance: ' || ROUND(ts.performance_score::numeric, 0) || '/20'
        END as reason
    FROM team_scores ts
    WHERE ts.capability_score > 0 OR p_required_capabilities IS NULL
    ORDER BY (ts.capability_score + ts.health_score + ts.performance_score) DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing (commented out for production)
/*
INSERT INTO a2a_teams (team_id, team_name, endpoint, capabilities, department) VALUES
('sales-team', 'Sales Team', 'http://sales-team:8090', 
 '["sales", "customer-engagement", "proposal-generation", "lead-qualification"]'::jsonb, 
 'sales'),
('marketing-team', 'Marketing Team', 'http://marketing-team:8090', 
 '["marketing", "content-creation", "campaign-management", "social-media"]'::jsonb, 
 'marketing'),
('product-team', 'Product Team', 'http://product-team:8090', 
 '["product-management", "feature-planning", "roadmap", "user-research"]'::jsonb, 
 'product'),
('engineering-team', 'Engineering Team', 'http://engineering-team:8090', 
 '["development", "architecture", "code-review", "technical-documentation"]'::jsonb, 
 'engineering');
*/