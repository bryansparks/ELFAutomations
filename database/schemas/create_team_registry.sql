-- Team Registry Schema for ElfAutomations
-- This schema tracks all teams, their relationships, and organizational structure
-- MUST be updated through team-factory.py to maintain integrity

-- Teams table: Core team information
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'marketing-team', 'brand-marketing-team'
    display_name VARCHAR(255) NOT NULL, -- e.g., 'Marketing Team', 'Brand Marketing Team'
    department VARCHAR(100) NOT NULL, -- e.g., 'marketing', 'engineering', 'executive'
    placement VARCHAR(255) NOT NULL, -- e.g., 'marketing', 'marketing.brand', 'executive'
    purpose TEXT NOT NULL, -- Team's purpose/description
    framework VARCHAR(50) NOT NULL, -- 'CrewAI' or 'LangGraph'
    llm_provider VARCHAR(50) NOT NULL, -- 'OpenAI' or 'Anthropic'
    llm_model VARCHAR(100) NOT NULL, -- Specific model used
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'archived'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}' -- Additional flexible data
);

-- Team Members table: Track individual agents in teams
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role VARCHAR(255) NOT NULL, -- e.g., 'Marketing Manager', 'Content Creator'
    is_manager BOOLEAN DEFAULT FALSE, -- True if this member is the team manager
    responsibilities TEXT[], -- Array of responsibilities
    skills TEXT[], -- Array of skills
    system_prompt TEXT, -- Agent's system prompt
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(team_id, role)
);

-- Team Relationships table: Who reports to whom
CREATE TABLE IF NOT EXISTS team_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    parent_entity_type VARCHAR(50) NOT NULL, -- 'team' or 'executive'
    parent_entity_name VARCHAR(255) NOT NULL, -- e.g., 'Chief Marketing Officer' or 'marketing-team'
    relationship_type VARCHAR(50) DEFAULT 'reports_to', -- 'reports_to', 'collaborates_with'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(child_team_id, parent_entity_name, relationship_type)
);

-- Executive Management table: Track which teams executives manage
CREATE TABLE IF NOT EXISTS executive_management (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    executive_role VARCHAR(255) NOT NULL, -- e.g., 'Chief Marketing Officer'
    executive_team VARCHAR(255) DEFAULT 'executive-team', -- Which team the executive belongs to
    managed_team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(executive_role, managed_team_id)
);

-- Intra-team Communications: Who talks to whom within teams
CREATE TABLE IF NOT EXISTS team_communication_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    from_role VARCHAR(255) NOT NULL,
    to_role VARCHAR(255) NOT NULL,
    communication_type VARCHAR(50) DEFAULT 'collaborates', -- 'collaborates', 'delegates', 'reports'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(team_id, from_role, to_role)
);

-- Team Creation Audit Log: Track all team creations and modifications
CREATE TABLE IF NOT EXISTS team_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL, -- 'created', 'updated', 'archived', 'relationship_added'
    description TEXT,
    performed_by VARCHAR(255), -- User or system that made the change
    details JSONB DEFAULT '{}', -- Detailed change information
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_teams_department ON teams(department);
CREATE INDEX idx_teams_placement ON teams(placement);
CREATE INDEX idx_teams_status ON teams(status);
CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_relationships_child ON team_relationships(child_team_id);
CREATE INDEX idx_team_relationships_parent ON team_relationships(parent_entity_name);
CREATE INDEX idx_executive_management_role ON executive_management(executive_role);
CREATE INDEX idx_executive_management_team ON executive_management(managed_team_id);
CREATE INDEX idx_audit_log_team ON team_audit_log(team_id);
CREATE INDEX idx_audit_log_created ON team_audit_log(created_at);

-- Views for common queries

-- View: Complete team hierarchy
CREATE OR REPLACE VIEW team_hierarchy AS
SELECT
    t.name AS team_name,
    t.display_name,
    t.department,
    t.placement,
    tr.parent_entity_type,
    tr.parent_entity_name,
    t.status,
    t.framework
FROM teams t
LEFT JOIN team_relationships tr ON t.id = tr.child_team_id
WHERE tr.relationship_type = 'reports_to';

-- View: Executive team management overview
CREATE OR REPLACE VIEW executive_overview AS
SELECT
    em.executive_role,
    em.executive_team,
    t.name AS managed_team,
    t.department,
    t.status
FROM executive_management em
JOIN teams t ON em.managed_team_id = t.id
ORDER BY em.executive_role, t.name;

-- View: Team composition summary
CREATE OR REPLACE VIEW team_composition AS
SELECT
    t.name AS team_name,
    t.department,
    COUNT(tm.id) AS member_count,
    COUNT(CASE WHEN tm.is_manager THEN 1 END) AS manager_count,
    ARRAY_AGG(tm.role ORDER BY tm.is_manager DESC, tm.role) AS members
FROM teams t
LEFT JOIN team_members tm ON t.id = tm.team_id
GROUP BY t.id, t.name, t.department;

-- Function: Get all teams managed by an executive
CREATE OR REPLACE FUNCTION get_executive_teams(exec_role VARCHAR)
RETURNS TABLE (
    team_name VARCHAR,
    team_id UUID,
    department VARCHAR,
    member_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.name,
        t.id,
        t.department,
        COUNT(tm.id) AS member_count
    FROM executive_management em
    JOIN teams t ON em.managed_team_id = t.id
    LEFT JOIN team_members tm ON t.id = tm.team_id
    WHERE em.executive_role = exec_role
    GROUP BY t.id, t.name, t.department;
END;
$$ LANGUAGE plpgsql;

-- Function: Register a new team (called by team-factory.py)
CREATE OR REPLACE FUNCTION register_team(
    p_team_name VARCHAR,
    p_display_name VARCHAR,
    p_department VARCHAR,
    p_placement VARCHAR,
    p_purpose TEXT,
    p_framework VARCHAR,
    p_llm_provider VARCHAR,
    p_llm_model VARCHAR,
    p_reports_to VARCHAR DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_team_id UUID;
BEGIN
    -- Insert the team
    INSERT INTO teams (name, display_name, department, placement, purpose, framework, llm_provider, llm_model)
    VALUES (p_team_name, p_display_name, p_department, p_placement, p_purpose, p_framework, p_llm_provider, p_llm_model)
    RETURNING id INTO v_team_id;

    -- Create reporting relationship if specified
    IF p_reports_to IS NOT NULL THEN
        -- Determine if reporting to executive or team
        IF p_reports_to LIKE 'Chief%Officer' THEN
            -- Reporting to executive
            INSERT INTO team_relationships (child_team_id, parent_entity_type, parent_entity_name)
            VALUES (v_team_id, 'executive', p_reports_to);

            -- Add to executive management
            INSERT INTO executive_management (executive_role, managed_team_id)
            VALUES (p_reports_to, v_team_id)
            ON CONFLICT (executive_role, managed_team_id) DO NOTHING;
        ELSE
            -- Reporting to another team
            INSERT INTO team_relationships (child_team_id, parent_entity_type, parent_entity_name)
            VALUES (v_team_id, 'team', p_reports_to);
        END IF;
    END IF;

    -- Log the creation
    INSERT INTO team_audit_log (team_id, action, description, performed_by)
    VALUES (v_team_id, 'created', 'Team registered via team-factory.py', 'team-factory');

    RETURN v_team_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_teams_updated_at
BEFORE UPDATE ON teams
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_relationships_updated_at
BEFORE UPDATE ON team_relationships
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
