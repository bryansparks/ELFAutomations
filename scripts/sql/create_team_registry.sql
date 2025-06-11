
-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    framework VARCHAR(50) NOT NULL CHECK (framework IN ('crewai', 'langgraph')),
    department VARCHAR(255),
    manager_agent VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Team members table
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    agent_name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    capabilities TEXT[],
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    is_manager BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(team_id, agent_name)
);

-- Team relationships table (who reports to whom)
CREATE TABLE IF NOT EXISTS team_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    child_team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'reports_to',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(parent_team_id, child_team_id)
);

-- Audit log for team activities
CREATE TABLE IF NOT EXISTS team_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    performed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_teams_department ON teams(department);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_relationships_parent ON team_relationships(parent_team_id);
CREATE INDEX IF NOT EXISTS idx_team_relationships_child ON team_relationships(child_team_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_team_id ON team_audit_log(team_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON team_audit_log(created_at);
