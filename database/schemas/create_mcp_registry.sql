-- MCP Registry Schema for Supabase
-- Provides central source of truth for all MCPs (internal and external)
-- Similar structure to team registry for consistency

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- MCPs table (similar to teams table)
CREATE TABLE IF NOT EXISTS mcps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL CHECK (type IN ('internal', 'external')),
    protocol VARCHAR(50) NOT NULL DEFAULT 'stdio' CHECK (protocol IN ('stdio', 'http', 'sse')),
    source VARCHAR(500), -- npm package, github repo, docker image, etc.
    install_type VARCHAR(50) CHECK (install_type IN ('npm', 'github', 'docker', 'local')),
    install_command TEXT,
    language VARCHAR(50), -- For internal MCPs: typescript, python, etc.
    author VARCHAR(255),
    verified BOOLEAN DEFAULT FALSE,
    stars INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
    config JSONB DEFAULT '{}',
    env_vars JSONB DEFAULT '[]', -- Required environment variables
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- MCP tools table (what capabilities each MCP provides)
CREATE TABLE IF NOT EXISTS mcp_tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID NOT NULL REFERENCES mcps(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parameters JSONB DEFAULT '{}', -- Tool parameter schema
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mcp_id, name)
);

-- MCP resources table (for resource-based MCPs)
CREATE TABLE IF NOT EXISTS mcp_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID NOT NULL REFERENCES mcps(id) ON DELETE CASCADE,
    uri VARCHAR(500) NOT NULL,
    name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mcp_id, uri)
);

-- MCP endpoints table (for tracking actual endpoints)
CREATE TABLE IF NOT EXISTS mcp_endpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID NOT NULL REFERENCES mcps(id) ON DELETE CASCADE,
    endpoint_url VARCHAR(500),
    endpoint_type VARCHAR(50) CHECK (endpoint_type IN ('tool', 'resource', 'prompt')),
    method VARCHAR(10) DEFAULT 'POST',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- MCP installations table (track where MCPs are installed)
CREATE TABLE IF NOT EXISTS mcp_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID NOT NULL REFERENCES mcps(id) ON DELETE CASCADE,
    installed_by VARCHAR(255),
    installation_path TEXT,
    agentgateway_registered BOOLEAN DEFAULT FALSE,
    installed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_status VARCHAR(50) DEFAULT 'unknown'
);

-- MCP audit log
CREATE TABLE IF NOT EXISTS mcp_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID REFERENCES mcps(id),
    action VARCHAR(50) NOT NULL,
    performed_by VARCHAR(255),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_mcps_name ON mcps(name);
CREATE INDEX idx_mcps_type ON mcps(type);
CREATE INDEX idx_mcps_status ON mcps(status);
CREATE INDEX idx_mcp_tools_mcp_id ON mcp_tools(mcp_id);
CREATE INDEX idx_mcp_audit_log_mcp_id ON mcp_audit_log(mcp_id);
CREATE INDEX idx_mcp_audit_log_created_at ON mcp_audit_log(created_at DESC);

-- Views for common queries
CREATE OR REPLACE VIEW mcp_overview AS
SELECT
    m.id,
    m.name,
    m.display_name,
    m.type,
    m.status,
    m.verified,
    COUNT(DISTINCT mt.id) as tool_count,
    COUNT(DISTINCT mr.id) as resource_count,
    COUNT(DISTINCT mi.id) as installation_count,
    MAX(mi.last_health_check) as last_health_check,
    m.created_at,
    m.updated_at
FROM mcps m
LEFT JOIN mcp_tools mt ON m.id = mt.mcp_id
LEFT JOIN mcp_resources mr ON m.id = mr.mcp_id
LEFT JOIN mcp_installations mi ON m.id = mi.mcp_id
GROUP BY m.id;

-- View for AgentGateway configuration
CREATE OR REPLACE VIEW agentgateway_mcp_config AS
SELECT
    m.name,
    m.protocol,
    m.source,
    m.install_command,
    m.config,
    m.env_vars,
    json_agg(
        json_build_object(
            'name', mt.name,
            'description', mt.description,
            'parameters', mt.parameters
        )
    ) FILTER (WHERE mt.id IS NOT NULL) as tools
FROM mcps m
LEFT JOIN mcp_tools mt ON m.id = mt.mcp_id
WHERE m.status = 'active'
GROUP BY m.id;

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_mcps_updated_at BEFORE UPDATE ON mcps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to log MCP changes
CREATE OR REPLACE FUNCTION log_mcp_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO mcp_audit_log (mcp_id, action, details)
        VALUES (NEW.id, 'created', row_to_json(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO mcp_audit_log (mcp_id, action, details)
        VALUES (NEW.id, 'updated',
            jsonb_build_object(
                'old', row_to_json(OLD),
                'new', row_to_json(NEW)
            )
        );
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO mcp_audit_log (mcp_id, action, details)
        VALUES (OLD.id, 'deleted', row_to_json(OLD));
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Audit triggers
CREATE TRIGGER mcp_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON mcps
    FOR EACH ROW EXECUTE FUNCTION log_mcp_change();

-- RLS Policies (similar to team registry)
ALTER TABLE mcps ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_endpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_installations ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_audit_log ENABLE ROW LEVEL SECURITY;

-- Allow full access to authenticated users (for now)
-- Read policies
CREATE POLICY "mcps_read_policy" ON mcps FOR SELECT USING (true);
CREATE POLICY "mcp_tools_read_policy" ON mcp_tools FOR SELECT USING (true);
CREATE POLICY "mcp_resources_read_policy" ON mcp_resources FOR SELECT USING (true);
CREATE POLICY "mcp_endpoints_read_policy" ON mcp_endpoints FOR SELECT USING (true);
CREATE POLICY "mcp_installations_read_policy" ON mcp_installations FOR SELECT USING (true);
CREATE POLICY "mcp_audit_log_read_policy" ON mcp_audit_log FOR SELECT USING (true);

-- Insert policies (allow authenticated users to insert)
CREATE POLICY "mcps_insert_policy" ON mcps FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_tools_insert_policy" ON mcp_tools FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_resources_insert_policy" ON mcp_resources FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_endpoints_insert_policy" ON mcp_endpoints FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_installations_insert_policy" ON mcp_installations FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_audit_log_insert_policy" ON mcp_audit_log FOR INSERT WITH CHECK (true);

-- Update policies (allow authenticated users to update)
CREATE POLICY "mcps_update_policy" ON mcps FOR UPDATE USING (true);
CREATE POLICY "mcp_tools_update_policy" ON mcp_tools FOR UPDATE USING (true);
CREATE POLICY "mcp_resources_update_policy" ON mcp_resources FOR UPDATE USING (true);
CREATE POLICY "mcp_endpoints_update_policy" ON mcp_endpoints FOR UPDATE USING (true);
CREATE POLICY "mcp_installations_update_policy" ON mcp_installations FOR UPDATE USING (true);

-- Delete policies (allow authenticated users to delete - be careful!)
CREATE POLICY "mcps_delete_policy" ON mcps FOR DELETE USING (true);
CREATE POLICY "mcp_tools_delete_policy" ON mcp_tools FOR DELETE USING (true);
CREATE POLICY "mcp_resources_delete_policy" ON mcp_resources FOR DELETE USING (true);
CREATE POLICY "mcp_endpoints_delete_policy" ON mcp_endpoints FOR DELETE USING (true);
CREATE POLICY "mcp_installations_delete_policy" ON mcp_installations FOR DELETE USING (true);

-- Sample data comment
COMMENT ON TABLE mcps IS 'Central registry for all Model Context Protocol servers (internal and external)';
COMMENT ON TABLE mcp_tools IS 'Tools/capabilities provided by each MCP';
COMMENT ON TABLE mcp_resources IS 'Resources exposed by resource-based MCPs';
COMMENT ON TABLE mcp_installations IS 'Track MCP installations and health status';
COMMENT ON TABLE mcp_audit_log IS 'Audit trail for all MCP operations';
