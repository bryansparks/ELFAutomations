-- Cost Monitoring Schema for ElfAutomations
-- Stores detailed cost analytics and alerts in Supabase

-- API Usage table: Detailed usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    provider VARCHAR(50) NOT NULL, -- 'openai', 'anthropic'
    model VARCHAR(100) NOT NULL, -- 'gpt-4', 'claude-3-opus', etc
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    cost DECIMAL(10, 6) NOT NULL, -- Cost in USD
    request_duration FLOAT, -- Duration in seconds
    request_id VARCHAR(255),
    task_description TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Daily Cost Summary table: Aggregated daily costs
CREATE TABLE IF NOT EXISTS daily_cost_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    total_cost DECIMAL(10, 4) NOT NULL,
    total_tokens INTEGER NOT NULL,
    request_count INTEGER NOT NULL,
    model_breakdown JSONB NOT NULL, -- {model: {cost, tokens, requests}}
    hourly_breakdown JSONB DEFAULT '{}', -- {hour: {cost, tokens}}
    budget DECIMAL(10, 2) NOT NULL,
    budget_used_percentage DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(team_name, date)
);

-- Cost Alerts table: Track alerts and notifications
CREATE TABLE IF NOT EXISTS cost_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level VARCHAR(20) NOT NULL, -- 'info', 'warning', 'critical'
    team_name VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'budget_exceeded', 'high_usage', etc
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE
);

-- Team Budgets table: Budget configuration
CREATE TABLE IF NOT EXISTS team_budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(255) UNIQUE NOT NULL,
    daily_budget DECIMAL(10, 2) NOT NULL DEFAULT 10.00,
    monthly_budget DECIMAL(10, 2),
    warning_threshold DECIMAL(3, 2) DEFAULT 0.80, -- Warn at 80%
    critical_threshold DECIMAL(3, 2) DEFAULT 0.95, -- Critical at 95%
    auto_fallback BOOLEAN DEFAULT TRUE, -- Auto switch to cheaper models
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cost Optimization Recommendations table
CREATE TABLE IF NOT EXISTS cost_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recommendation_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    potential_savings DECIMAL(10, 2),
    effort_level VARCHAR(20), -- 'low', 'medium', 'high'
    impact_level VARCHAR(20), -- 'low', 'medium', 'high'
    implementation_guide TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'implemented', 'dismissed'
    implemented_at TIMESTAMP WITH TIME ZONE,
    implemented_by VARCHAR(255)
);

-- Indexes for performance
CREATE INDEX idx_api_usage_team_timestamp ON api_usage(team_name, timestamp DESC);
CREATE INDEX idx_api_usage_model ON api_usage(model);
CREATE INDEX idx_api_usage_cost ON api_usage(cost DESC);
CREATE INDEX idx_daily_summary_team_date ON daily_cost_summary(team_name, date DESC);
CREATE INDEX idx_daily_summary_budget_used ON daily_cost_summary(budget_used_percentage DESC);
CREATE INDEX idx_alerts_team ON cost_alerts(team_name, timestamp DESC);
CREATE INDEX idx_alerts_level ON cost_alerts(level, acknowledged);
CREATE INDEX idx_recommendations_team ON cost_recommendations(team_name, status);

-- Views for analytics

-- Current day usage view
CREATE OR REPLACE VIEW current_day_usage AS
SELECT
    team_name,
    COUNT(*) as request_count,
    SUM(total_tokens) as total_tokens,
    SUM(cost) as total_cost,
    AVG(cost) as avg_cost_per_request,
    MAX(cost) as max_request_cost,
    COUNT(DISTINCT model) as models_used
FROM api_usage
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY team_name;

-- Weekly cost trends view
CREATE OR REPLACE VIEW weekly_cost_trends AS
SELECT
    team_name,
    DATE_TRUNC('week', date) as week,
    SUM(total_cost) as weekly_cost,
    SUM(total_tokens) as weekly_tokens,
    SUM(request_count) as weekly_requests,
    AVG(budget_used_percentage) as avg_budget_used
FROM daily_cost_summary
WHERE date >= CURRENT_DATE - INTERVAL '4 weeks'
GROUP BY team_name, DATE_TRUNC('week', date)
ORDER BY team_name, week DESC;

-- High cost requests view
CREATE OR REPLACE VIEW high_cost_requests AS
SELECT
    team_name,
    timestamp,
    model,
    cost,
    total_tokens,
    task_description,
    request_duration
FROM api_usage
WHERE cost > 0.10 -- Requests over $0.10
ORDER BY cost DESC
LIMIT 100;

-- Functions for cost monitoring

-- Function: Record API usage
CREATE OR REPLACE FUNCTION record_api_usage(
    p_team_name VARCHAR,
    p_provider VARCHAR,
    p_model VARCHAR,
    p_input_tokens INTEGER,
    p_output_tokens INTEGER,
    p_cost DECIMAL,
    p_request_id VARCHAR DEFAULT NULL,
    p_task_description TEXT DEFAULT NULL,
    p_duration FLOAT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_usage_id UUID;
    v_daily_budget DECIMAL;
    v_current_usage DECIMAL;
BEGIN
    -- Insert usage record
    INSERT INTO api_usage (
        team_name, provider, model, input_tokens, output_tokens,
        cost, request_id, task_description, request_duration
    ) VALUES (
        p_team_name, p_provider, p_model, p_input_tokens, p_output_tokens,
        p_cost, p_request_id, p_task_description, p_duration
    ) RETURNING id INTO v_usage_id;

    -- Get team budget
    SELECT daily_budget INTO v_daily_budget
    FROM team_budgets
    WHERE team_name = p_team_name;

    IF v_daily_budget IS NULL THEN
        v_daily_budget := 10.00; -- Default budget
    END IF;

    -- Check current usage
    SELECT COALESCE(SUM(cost), 0) INTO v_current_usage
    FROM api_usage
    WHERE team_name = p_team_name
    AND DATE(timestamp) = CURRENT_DATE;

    -- Create alerts if needed
    IF v_current_usage > v_daily_budget THEN
        INSERT INTO cost_alerts (level, team_name, alert_type, message, details)
        VALUES (
            'critical',
            p_team_name,
            'budget_exceeded',
            p_team_name || ' has exceeded daily budget',
            jsonb_build_object(
                'budget', v_daily_budget,
                'used', v_current_usage,
                'overage', v_current_usage - v_daily_budget
            )
        );
    ELSIF v_current_usage > v_daily_budget * 0.8 THEN
        -- Check if we already alerted today
        IF NOT EXISTS (
            SELECT 1 FROM cost_alerts
            WHERE team_name = p_team_name
            AND alert_type = 'high_usage'
            AND DATE(timestamp) = CURRENT_DATE
        ) THEN
            INSERT INTO cost_alerts (level, team_name, alert_type, message, details)
            VALUES (
                'warning',
                p_team_name,
                'high_usage',
                p_team_name || ' is approaching budget limit',
                jsonb_build_object(
                    'budget', v_daily_budget,
                    'used', v_current_usage,
                    'percentage', (v_current_usage / v_daily_budget * 100)
                )
            );
        END IF;
    END IF;

    RETURN v_usage_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Update daily summary
CREATE OR REPLACE FUNCTION update_daily_summary(p_team_name VARCHAR, p_date DATE)
RETURNS VOID AS $$
DECLARE
    v_summary RECORD;
    v_model_breakdown JSONB;
    v_budget DECIMAL;
BEGIN
    -- Get aggregated data
    SELECT
        COUNT(*) as request_count,
        COALESCE(SUM(total_tokens), 0) as total_tokens,
        COALESCE(SUM(cost), 0) as total_cost,
        jsonb_object_agg(
            model,
            jsonb_build_object(
                'cost', model_cost,
                'tokens', model_tokens,
                'requests', model_requests
            )
        ) as model_breakdown
    INTO v_summary
    FROM (
        SELECT
            model,
            SUM(cost) as model_cost,
            SUM(total_tokens) as model_tokens,
            COUNT(*) as model_requests
        FROM api_usage
        WHERE team_name = p_team_name
        AND DATE(timestamp) = p_date
        GROUP BY model
    ) model_stats;

    -- Get budget
    SELECT COALESCE(daily_budget, 10.00) INTO v_budget
    FROM team_budgets
    WHERE team_name = p_team_name;

    -- Upsert daily summary
    INSERT INTO daily_cost_summary (
        team_name, date, total_cost, total_tokens, request_count,
        model_breakdown, budget, budget_used_percentage
    ) VALUES (
        p_team_name,
        p_date,
        v_summary.total_cost,
        v_summary.total_tokens,
        v_summary.request_count,
        COALESCE(v_summary.model_breakdown, '{}'::jsonb),
        v_budget,
        (v_summary.total_cost / v_budget * 100)
    )
    ON CONFLICT (team_name, date) DO UPDATE SET
        total_cost = EXCLUDED.total_cost,
        total_tokens = EXCLUDED.total_tokens,
        request_count = EXCLUDED.request_count,
        model_breakdown = EXCLUDED.model_breakdown,
        budget_used_percentage = EXCLUDED.budget_used_percentage,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update daily summary on new usage
CREATE OR REPLACE FUNCTION trigger_update_daily_summary()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_daily_summary(NEW.team_name, DATE(NEW.timestamp));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_summary_on_usage
AFTER INSERT ON api_usage
FOR EACH ROW
EXECUTE FUNCTION trigger_update_daily_summary();
