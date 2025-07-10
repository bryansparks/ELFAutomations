-- Agent Evolution Tracking System
-- Stores how agents evolve their prompts, workflows, and tools based on learnings

CREATE TABLE IF NOT EXISTS agent_evolutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    agent_role VARCHAR(255) NOT NULL,
    evolution_type VARCHAR(50) NOT NULL CHECK (evolution_type IN ('prompt', 'workflow', 'tools', 'behavior')),

    -- Version tracking
    original_version TEXT NOT NULL,
    evolved_version TEXT NOT NULL,

    -- Performance metrics
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    performance_delta FLOAT DEFAULT 0.0,  -- Percentage change in performance

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP,  -- When this evolution was actually applied
    rollback_at TIMESTAMP,  -- If this evolution was rolled back
    rollback_reason TEXT,

    -- A/B testing data
    test_group VARCHAR(10) CHECK (test_group IN ('control', 'treatment')),
    test_metrics JSONB,  -- Stores detailed test results

    -- Index for quick lookups
    UNIQUE(team_id, agent_role, evolution_type, created_at)
);

-- Indexes for performance
CREATE INDEX idx_agent_evolutions_team_role ON agent_evolutions(team_id, agent_role);
CREATE INDEX idx_agent_evolutions_confidence ON agent_evolutions(confidence_score) WHERE confidence_score >= 0.9;
CREATE INDEX idx_agent_evolutions_created ON agent_evolutions(created_at DESC);

-- View for active evolutions (latest non-rolled-back evolution per agent)
CREATE OR REPLACE VIEW active_agent_evolutions AS
SELECT DISTINCT ON (team_id, agent_role, evolution_type)
    ae.*,
    t.name as team_name
FROM agent_evolutions ae
JOIN teams t ON ae.team_id = t.id
WHERE ae.rollback_at IS NULL
ORDER BY team_id, agent_role, evolution_type, created_at DESC;

-- View for evolution performance metrics
CREATE OR REPLACE VIEW evolution_performance_summary AS
SELECT
    team_id,
    agent_role,
    evolution_type,
    COUNT(*) as total_evolutions,
    AVG(confidence_score) as avg_confidence,
    AVG(performance_delta) as avg_performance_delta,
    SUM(CASE WHEN performance_delta > 0 THEN 1 ELSE 0 END) as positive_evolutions,
    SUM(CASE WHEN rollback_at IS NOT NULL THEN 1 ELSE 0 END) as rollback_count
FROM agent_evolutions
GROUP BY team_id, agent_role, evolution_type;

-- Function to get evolution chain for an agent
CREATE OR REPLACE FUNCTION get_agent_evolution_chain(
    p_team_id UUID,
    p_agent_role VARCHAR(255),
    p_evolution_type VARCHAR(50)
)
RETURNS TABLE (
    evolution_id UUID,
    version_number INT,
    evolved_version TEXT,
    confidence_score FLOAT,
    performance_delta FLOAT,
    created_at TIMESTAMP,
    is_active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH numbered_evolutions AS (
        SELECT
            id,
            ROW_NUMBER() OVER (ORDER BY created_at) as version_number,
            evolved_version,
            ae.confidence_score,
            ae.performance_delta,
            ae.created_at,
            (ae.rollback_at IS NULL AND ae.created_at = (
                SELECT MAX(created_at)
                FROM agent_evolutions
                WHERE team_id = p_team_id
                AND agent_role = p_agent_role
                AND evolution_type = p_evolution_type
            )) as is_active
        FROM agent_evolutions ae
        WHERE ae.team_id = p_team_id
        AND ae.agent_role = p_agent_role
        AND ae.evolution_type = p_evolution_type
        ORDER BY ae.created_at
    )
    SELECT * FROM numbered_evolutions;
END;
$$ LANGUAGE plpgsql;

-- Trigger to limit evolution history (keep last 10 per agent)
CREATE OR REPLACE FUNCTION limit_evolution_history()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete old evolutions beyond the 10 most recent
    DELETE FROM agent_evolutions
    WHERE id IN (
        SELECT id FROM (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY team_id, agent_role, evolution_type
                       ORDER BY created_at DESC
                   ) as rn
            FROM agent_evolutions
            WHERE team_id = NEW.team_id
            AND agent_role = NEW.agent_role
            AND evolution_type = NEW.evolution_type
        ) t
        WHERE rn > 10
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_limit_evolution_history
AFTER INSERT ON agent_evolutions
FOR EACH ROW
EXECUTE FUNCTION limit_evolution_history();

-- Grant permissions
GRANT ALL ON agent_evolutions TO authenticated;
GRANT ALL ON active_agent_evolutions TO authenticated;
GRANT ALL ON evolution_performance_summary TO authenticated;
