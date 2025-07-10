-- Add chat interface support to teams table
ALTER TABLE teams ADD COLUMN IF NOT EXISTS is_top_level BOOLEAN DEFAULT FALSE;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS enable_chat_interface BOOLEAN DEFAULT FALSE;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS chat_config JSONB DEFAULT '{}';

-- Create index for finding top-level teams quickly
CREATE INDEX IF NOT EXISTS idx_teams_top_level ON teams(is_top_level) WHERE is_top_level = true;

-- Table for tracking chat sessions with teams
CREATE TABLE IF NOT EXISTS team_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL UNIQUE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    delegated BOOLEAN DEFAULT FALSE,
    delegation_task_id TEXT,
    session_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for session queries
CREATE INDEX IF NOT EXISTS idx_chat_sessions_team_id ON team_chat_sessions(team_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON team_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON team_chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON team_chat_sessions(created_at DESC);

-- Table for storing chat messages
CREATE TABLE IF NOT EXISTS team_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES team_chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for message queries
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON team_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON team_chat_messages(created_at);

-- Table for delegation outcomes from chat sessions
CREATE TABLE IF NOT EXISTS team_chat_delegations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES team_chat_sessions(id) ON DELETE CASCADE,
    from_team_id UUID REFERENCES teams(id),
    to_team_id UUID REFERENCES teams(id),
    task_specification JSONB NOT NULL,
    a2a_message_id TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'acknowledged', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for delegation queries
CREATE INDEX IF NOT EXISTS idx_chat_delegations_session_id ON team_chat_delegations(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_delegations_status ON team_chat_delegations(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_team_chat_sessions_updated_at ON team_chat_sessions;
CREATE TRIGGER update_team_chat_sessions_updated_at
    BEFORE UPDATE ON team_chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_team_chat_delegations_updated_at ON team_chat_delegations;
CREATE TRIGGER update_team_chat_delegations_updated_at
    BEFORE UPDATE ON team_chat_delegations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for active chat sessions
CREATE OR REPLACE VIEW active_chat_sessions AS
SELECT
    tcs.id,
    tcs.session_id,
    tcs.user_id,
    t.name as team_name,
    t.id as team_id,
    tcs.started_at,
    tcs.message_count,
    tcs.total_tokens,
    EXTRACT(EPOCH FROM (NOW() - tcs.started_at)) / 60 as duration_minutes
FROM team_chat_sessions tcs
JOIN teams t ON t.id = tcs.team_id
WHERE tcs.ended_at IS NULL
ORDER BY tcs.started_at DESC;

-- View for chat statistics by team
CREATE OR REPLACE VIEW team_chat_statistics AS
SELECT
    t.id as team_id,
    t.name as team_name,
    COUNT(DISTINCT tcs.id) as total_sessions,
    COUNT(DISTINCT tcs.user_id) as unique_users,
    SUM(tcs.message_count) as total_messages,
    SUM(tcs.total_tokens) as total_tokens,
    AVG(tcs.message_count)::INTEGER as avg_messages_per_session,
    COUNT(CASE WHEN tcs.delegated THEN 1 END) as delegated_sessions,
    MAX(tcs.created_at) as last_chat_at
FROM teams t
LEFT JOIN team_chat_sessions tcs ON t.id = tcs.team_id
WHERE t.enable_chat_interface = true
GROUP BY t.id, t.name
ORDER BY total_sessions DESC;

-- Grant permissions (adjust based on your role setup)
GRANT ALL ON team_chat_sessions TO authenticated;
GRANT ALL ON team_chat_messages TO authenticated;
GRANT ALL ON team_chat_delegations TO authenticated;
GRANT SELECT ON active_chat_sessions TO authenticated;
GRANT SELECT ON team_chat_statistics TO authenticated;

-- RLS policies for chat tables
ALTER TABLE team_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_chat_delegations ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to manage their own sessions
CREATE POLICY "Users can view their own chat sessions" ON team_chat_sessions
    FOR SELECT USING (auth.uid()::TEXT = user_id);

CREATE POLICY "Users can create their own chat sessions" ON team_chat_sessions
    FOR INSERT WITH CHECK (auth.uid()::TEXT = user_id);

CREATE POLICY "Users can update their own chat sessions" ON team_chat_sessions
    FOR UPDATE USING (auth.uid()::TEXT = user_id);

-- Allow users to view messages from their sessions
CREATE POLICY "Users can view messages from their sessions" ON team_chat_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM team_chat_sessions
            WHERE team_chat_sessions.id = team_chat_messages.session_id
            AND team_chat_sessions.user_id = auth.uid()::TEXT
        )
    );

CREATE POLICY "Users can create messages in their sessions" ON team_chat_messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM team_chat_sessions
            WHERE team_chat_sessions.id = team_chat_messages.session_id
            AND team_chat_sessions.user_id = auth.uid()::TEXT
        )
    );

-- Service role can do everything
CREATE POLICY "Service role full access to sessions" ON team_chat_sessions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to messages" ON team_chat_messages
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access to delegations" ON team_chat_delegations
    FOR ALL USING (auth.role() = 'service_role');
