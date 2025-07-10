-- Fix RLS policies for MCP registry to allow inserts/updates/deletes

-- Drop existing read-only policies if they exist
DROP POLICY IF EXISTS "mcps_read_policy" ON mcps;
DROP POLICY IF EXISTS "mcp_tools_read_policy" ON mcp_tools;
DROP POLICY IF EXISTS "mcp_resources_read_policy" ON mcp_resources;
DROP POLICY IF EXISTS "mcp_endpoints_read_policy" ON mcp_endpoints;
DROP POLICY IF EXISTS "mcp_installations_read_policy" ON mcp_installations;
DROP POLICY IF EXISTS "mcp_audit_log_read_policy" ON mcp_audit_log;

-- Recreate with full CRUD permissions for authenticated users

-- MCPs table
CREATE POLICY "mcps_select" ON mcps FOR SELECT USING (true);
CREATE POLICY "mcps_insert" ON mcps FOR INSERT WITH CHECK (true);
CREATE POLICY "mcps_update" ON mcps FOR UPDATE USING (true);
CREATE POLICY "mcps_delete" ON mcps FOR DELETE USING (true);

-- MCP tools table
CREATE POLICY "mcp_tools_select" ON mcp_tools FOR SELECT USING (true);
CREATE POLICY "mcp_tools_insert" ON mcp_tools FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_tools_update" ON mcp_tools FOR UPDATE USING (true);
CREATE POLICY "mcp_tools_delete" ON mcp_tools FOR DELETE USING (true);

-- MCP resources table
CREATE POLICY "mcp_resources_select" ON mcp_resources FOR SELECT USING (true);
CREATE POLICY "mcp_resources_insert" ON mcp_resources FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_resources_update" ON mcp_resources FOR UPDATE USING (true);
CREATE POLICY "mcp_resources_delete" ON mcp_resources FOR DELETE USING (true);

-- MCP endpoints table
CREATE POLICY "mcp_endpoints_select" ON mcp_endpoints FOR SELECT USING (true);
CREATE POLICY "mcp_endpoints_insert" ON mcp_endpoints FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_endpoints_update" ON mcp_endpoints FOR UPDATE USING (true);
CREATE POLICY "mcp_endpoints_delete" ON mcp_endpoints FOR DELETE USING (true);

-- MCP installations table
CREATE POLICY "mcp_installations_select" ON mcp_installations FOR SELECT USING (true);
CREATE POLICY "mcp_installations_insert" ON mcp_installations FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_installations_update" ON mcp_installations FOR UPDATE USING (true);
CREATE POLICY "mcp_installations_delete" ON mcp_installations FOR DELETE USING (true);

-- MCP audit log table
CREATE POLICY "mcp_audit_log_select" ON mcp_audit_log FOR SELECT USING (true);
CREATE POLICY "mcp_audit_log_insert" ON mcp_audit_log FOR INSERT WITH CHECK (true);
CREATE POLICY "mcp_audit_log_update" ON mcp_audit_log FOR UPDATE USING (true);
CREATE POLICY "mcp_audit_log_delete" ON mcp_audit_log FOR DELETE USING (true);
