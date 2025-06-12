-- A/B Testing Framework for Agent Evolution
-- Tracks controlled experiments comparing base vs evolved agents

-- Main A/B test tracking table
CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    agent_role VARCHAR(255) NOT NULL,
    evolution_id UUID REFERENCES agent_evolutions(id) ON DELETE CASCADE,
    
    -- Test configuration
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'completed', 'cancelled')),
    traffic_split FLOAT NOT NULL CHECK (traffic_split >= 0 AND traffic_split <= 1),
    
    -- Timing
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    
    -- Configurations being tested
    control_config TEXT NOT NULL,  -- Base agent config
    treatment_config TEXT NOT NULL,  -- Evolved agent config
    
    -- Aggregated metrics
    metrics JSONB NOT NULL DEFAULT '{
        "control": {"requests": 0, "successes": 0, "errors": 0, "duration_sum": 0},
        "treatment": {"requests": 0, "successes": 0, "errors": 0, "duration_sum": 0}
    }',
    
    -- Results
    final_recommendation TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual test result records for detailed analysis
CREATE TABLE IF NOT EXISTS ab_test_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
    
    -- Assignment
    group_name VARCHAR(20) NOT NULL CHECK (group_name IN ('control', 'treatment')),
    
    -- Outcome
    success BOOLEAN NOT NULL,
    duration_seconds FLOAT NOT NULL,
    error TEXT,
    
    -- Context (optional)
    task_type VARCHAR(100),
    task_complexity VARCHAR(20),
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_ab_tests_team_status ON ab_tests(team_id, status);
CREATE INDEX idx_ab_tests_evolution ON ab_tests(evolution_id);
CREATE INDEX idx_ab_test_results_test ON ab_test_results(test_id);
CREATE INDEX idx_ab_test_results_created ON ab_test_results(created_at DESC);

-- View for active tests by team
CREATE OR REPLACE VIEW active_ab_tests AS
SELECT 
    t.id,
    t.team_id,
    t.agent_role,
    t.traffic_split,
    t.start_time,
    t.end_time,
    t.metrics,
    ae.confidence_score as evolution_confidence,
    tm.name as team_name
FROM ab_tests t
JOIN agent_evolutions ae ON t.evolution_id = ae.id
JOIN teams tm ON t.team_id = tm.id
WHERE t.status = 'active'
AND t.end_time > CURRENT_TIMESTAMP;

-- View for test performance comparison
CREATE OR REPLACE VIEW ab_test_performance AS
SELECT 
    test_id,
    group_name,
    COUNT(*) as total_requests,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
    AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate,
    AVG(duration_seconds) as avg_duration,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_seconds) as median_duration,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds) as p95_duration,
    MIN(created_at) as first_request,
    MAX(created_at) as last_request
FROM ab_test_results
GROUP BY test_id, group_name;

-- Function to check if an agent should use evolved version
CREATE OR REPLACE FUNCTION get_agent_assignment(
    p_team_id UUID,
    p_agent_role VARCHAR(255)
)
RETURNS TABLE (
    use_evolved BOOLEAN,
    test_id UUID,
    evolution_id UUID,
    config TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH active_test AS (
        SELECT 
            t.id as test_id,
            t.evolution_id,
            t.traffic_split,
            t.control_config,
            t.treatment_config
        FROM ab_tests t
        WHERE t.team_id = p_team_id
        AND t.agent_role = p_agent_role
        AND t.status = 'active'
        AND t.end_time > CURRENT_TIMESTAMP
        ORDER BY t.created_at DESC
        LIMIT 1
    )
    SELECT 
        CASE 
            WHEN random() < at.traffic_split THEN true
            ELSE false
        END as use_evolved,
        at.test_id,
        at.evolution_id,
        CASE 
            WHEN random() < at.traffic_split THEN at.treatment_config
            ELSE at.control_config
        END as config
    FROM active_test at;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-finalize completed tests
CREATE OR REPLACE FUNCTION finalize_completed_tests()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE ab_tests
    SET status = 'completed',
        completed_at = CURRENT_TIMESTAMP
    WHERE status = 'active'
    AND end_time <= CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Run finalization check on any test update
CREATE TRIGGER trigger_finalize_tests
AFTER INSERT OR UPDATE ON ab_test_results
FOR EACH STATEMENT
EXECUTE FUNCTION finalize_completed_tests();

-- Grant permissions
GRANT ALL ON ab_tests TO authenticated;
GRANT ALL ON ab_test_results TO authenticated;
GRANT ALL ON active_ab_tests TO authenticated;
GRANT ALL ON ab_test_performance TO authenticated;