-- Fix RLS policies for RAG system to allow initial setup

-- Drop existing policies
DROP POLICY IF EXISTS rag_tenant_isolation ON rag_tenants;
DROP POLICY IF EXISTS rag_workspace_isolation ON rag_workspaces;
DROP POLICY IF EXISTS rag_document_isolation ON rag_documents;
DROP POLICY IF EXISTS rag_chunk_isolation ON rag_document_chunks;
DROP POLICY IF EXISTS rag_queue_isolation ON rag_processing_queue;
DROP POLICY IF EXISTS rag_entity_isolation ON rag_entities;
DROP POLICY IF EXISTS rag_relationship_isolation ON rag_relationships;
DROP POLICY IF EXISTS rag_search_isolation ON rag_search_queries;
DROP POLICY IF EXISTS rag_api_usage_isolation ON rag_api_usage;

-- Create new policies that allow service role and authenticated users full access
-- For production, you'd want more restrictive policies

-- Tenants: Allow authenticated users to see all tenants (needed for initial setup)
CREATE POLICY rag_tenant_read ON rag_tenants
    FOR SELECT
    USING (true);  -- All authenticated users can read tenants

CREATE POLICY rag_tenant_insert ON rag_tenants
    FOR INSERT
    WITH CHECK (true);  -- Allow creating new tenants

CREATE POLICY rag_tenant_update ON rag_tenants
    FOR UPDATE
    USING (true);  -- For now, allow updates

CREATE POLICY rag_tenant_delete ON rag_tenants
    FOR DELETE
    USING (false);  -- Prevent deletion

-- Workspaces: Tenant-scoped access
CREATE POLICY rag_workspace_access ON rag_workspaces
    FOR ALL
    USING (
        -- Either no tenant context is set (initial setup)
        -- Or the workspace belongs to the current tenant
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Documents: Tenant-scoped access
CREATE POLICY rag_document_access ON rag_documents
    FOR ALL
    USING (
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Document chunks: Tenant-scoped access
CREATE POLICY rag_chunk_access ON rag_document_chunks
    FOR ALL
    USING (
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Processing queue: Tenant-scoped access
CREATE POLICY rag_queue_access ON rag_processing_queue
    FOR ALL
    USING (
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Entities: Tenant-scoped access
CREATE POLICY rag_entity_access ON rag_entities
    FOR ALL
    USING (
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Relationships: Tenant-scoped access
CREATE POLICY rag_relationship_access ON rag_relationships
    FOR ALL
    USING (
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Search queries: Tenant-scoped access
CREATE POLICY rag_search_access ON rag_search_queries
    FOR ALL
    USING (
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- API usage: Tenant-scoped access
CREATE POLICY rag_api_usage_access ON rag_api_usage
    FOR ALL
    USING (
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Special tables without tenant_id

-- Watch folders: Allow all authenticated users to manage
DROP POLICY IF EXISTS rag_watch_folders_access ON rag_watch_folders;
CREATE POLICY rag_watch_folders_access ON rag_watch_folders
    FOR ALL
    USING (true);

-- OAuth events: Managed through tenant relationship
DROP POLICY IF EXISTS rag_oauth_events_access ON rag_oauth_events;
CREATE POLICY rag_oauth_events_access ON rag_oauth_events
    FOR ALL
    USING (
        current_setting('app.current_tenant_id', true) IS NULL 
        OR tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Document types: Read-only for all authenticated users
DROP POLICY IF EXISTS rag_document_types_read ON rag_document_types;
CREATE POLICY rag_document_types_read ON rag_document_types
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS rag_document_types_write ON rag_document_types;
CREATE POLICY rag_document_types_write ON rag_document_types
    FOR INSERT
    WITH CHECK (false);  -- Prevent inserts through API

-- Grant necessary permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;