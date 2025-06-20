-- Multi-Tenant RAG System Database Schema
-- This schema supports complete tenant isolation with RLS

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS rag;

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Tenants table - Organizations using the RAG system
CREATE TABLE IF NOT EXISTS rag.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    drive_folder_id TEXT, -- Google Drive folder ID
    storage_quota_gb INTEGER DEFAULT 10,
    api_quota_daily INTEGER DEFAULT 1000,
    settings JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workspaces - Subdivisions within tenants (departments, projects, etc)
CREATE TABLE IF NOT EXISTS rag.workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    drive_folder_id TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

-- Document types configuration
CREATE TABLE IF NOT EXISTS rag.document_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    processor_config JSONB NOT NULL, -- Processing pipeline configuration
    storage_strategy JSONB NOT NULL, -- Which storage systems to use
    extraction_rules JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents - Master record for all ingested documents
CREATE TABLE IF NOT EXISTS rag.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES rag.workspaces(id) ON DELETE CASCADE,
    document_type_id UUID REFERENCES rag.document_types(id),
    
    -- Source information
    source_type TEXT NOT NULL DEFAULT 'google_drive', -- google_drive, s3, upload, etc
    source_id TEXT NOT NULL, -- Drive file ID, S3 key, etc
    source_path TEXT, -- Full path in source system
    
    -- Document metadata
    filename TEXT NOT NULL,
    mime_type TEXT,
    size_bytes BIGINT,
    checksum TEXT, -- SHA-256 hash
    
    -- Processing status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'queued', 'processing', 'completed', 'failed', 'archived'
    )),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_error JSONB,
    
    -- Extracted metadata
    title TEXT,
    author TEXT,
    extracted_metadata JSONB DEFAULT '{}',
    
    -- Storage locations
    storage_locations JSONB DEFAULT '{}', -- {minio: "path", drive: "id", etc}
    
    -- Versioning
    version INTEGER DEFAULT 1,
    parent_document_id UUID REFERENCES rag.documents(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document chunks - For vector search
CREATE TABLE IF NOT EXISTS rag.document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    tokens INTEGER,
    
    -- Vector storage reference
    vector_id TEXT, -- ID in Qdrant
    collection_name TEXT, -- Qdrant collection
    
    -- Metadata for filtering
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Processing queue - For async document processing
CREATE TABLE IF NOT EXISTS rag.processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'processing', 'completed', 'failed', 'cancelled'
    )),
    
    processor_type TEXT NOT NULL, -- Which processor to use
    processing_config JSONB DEFAULT '{}',
    
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_error TEXT,
    
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Entities extracted from documents
CREATE TABLE IF NOT EXISTS rag.entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    
    entity_type TEXT NOT NULL, -- person, organization, location, etc
    name TEXT NOT NULL,
    normalized_name TEXT, -- Standardized version
    
    -- Graph storage reference
    neo4j_node_id TEXT,
    
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Relationships between entities
CREATE TABLE IF NOT EXISTS rag.relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    source_entity_id UUID NOT NULL REFERENCES rag.entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES rag.entities(id) ON DELETE CASCADE,
    
    relationship_type TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    
    -- Graph storage reference
    neo4j_edge_id TEXT,
    
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search queries - For analytics and caching
CREATE TABLE IF NOT EXISTS rag.search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES rag.workspaces(id),
    
    query_text TEXT NOT NULL,
    query_type TEXT DEFAULT 'hybrid', -- vector, graph, sql, hybrid
    query_config JSONB DEFAULT '{}',
    
    result_count INTEGER,
    execution_time_ms INTEGER,
    
    -- Caching
    cached_results JSONB,
    cache_expires_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS rag.api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    execution_time_ms INTEGER,
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Documents indexes
CREATE INDEX idx_documents_tenant_status ON rag.documents(tenant_id, status);
CREATE INDEX idx_documents_source ON rag.documents(source_type, source_id);
CREATE INDEX idx_documents_created ON rag.documents(tenant_id, created_at DESC);
CREATE INDEX idx_documents_type ON rag.documents(document_type_id);

-- Chunks indexes
CREATE INDEX idx_chunks_document ON rag.document_chunks(document_id);
CREATE INDEX idx_chunks_tenant ON rag.document_chunks(tenant_id);

-- Queue indexes
CREATE INDEX idx_queue_status_priority ON rag.processing_queue(status, priority DESC);
CREATE INDEX idx_queue_tenant ON rag.processing_queue(tenant_id, status);

-- Entities indexes
CREATE INDEX idx_entities_tenant_type ON rag.entities(tenant_id, entity_type);
CREATE INDEX idx_entities_normalized ON rag.entities(normalized_name);

-- Search indexes
CREATE INDEX idx_search_tenant_created ON rag.search_queries(tenant_id, created_at DESC);

-- API usage indexes
CREATE INDEX idx_api_usage_tenant_created ON rag.api_usage(tenant_id, created_at DESC);

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE rag.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.processing_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.search_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag.api_usage ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Note: These use current_setting('app.current_tenant_id') which must be set by the application

-- Tenants: Only see your own tenant
CREATE POLICY tenant_isolation ON rag.tenants
    FOR ALL
    USING (id = current_setting('app.current_tenant_id', true)::uuid);

-- Workspaces: Only see workspaces in your tenant
CREATE POLICY workspace_isolation ON rag.workspaces
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Documents: Only see documents in your tenant
CREATE POLICY document_isolation ON rag.documents
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Chunks: Only see chunks in your tenant
CREATE POLICY chunk_isolation ON rag.document_chunks
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Queue: Only see your tenant's queue items
CREATE POLICY queue_isolation ON rag.processing_queue
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Entities: Only see your tenant's entities
CREATE POLICY entity_isolation ON rag.entities
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Relationships: Only see your tenant's relationships
CREATE POLICY relationship_isolation ON rag.relationships
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Search queries: Only see your tenant's queries
CREATE POLICY search_isolation ON rag.search_queries
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- API usage: Only see your tenant's usage
CREATE POLICY api_usage_isolation ON rag.api_usage
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to set tenant context for RLS
CREATE OR REPLACE FUNCTION rag.set_tenant_context(tenant_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_id::text, false);
END;
$$ LANGUAGE plpgsql;

-- Function to get current tenant context
CREATE OR REPLACE FUNCTION rag.get_current_tenant()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_tenant_id', true)::uuid;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION rag.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON rag.tenants
    FOR EACH ROW EXECUTE FUNCTION rag.update_updated_at_column();

CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON rag.workspaces
    FOR EACH ROW EXECUTE FUNCTION rag.update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON rag.documents
    FOR EACH ROW EXECUTE FUNCTION rag.update_updated_at_column();

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert default document types
INSERT INTO rag.document_types (name, display_name, processor_config, storage_strategy) VALUES
('invoice', 'Invoice', 
    '{"processor": "InvoiceProcessor", "extract_line_items": true, "ocr_enabled": true}',
    '{"primary": "graph", "secondary": "sql", "embeddings": "minimal"}'
),
('contract', 'Contract',
    '{"processor": "ContractProcessor", "extract_clauses": true, "extract_parties": true}',
    '{"primary": "graph", "secondary": "vector", "embeddings": "full"}'
),
('research_paper', 'Research Paper',
    '{"processor": "ResearchProcessor", "extract_citations": true, "extract_abstract": true}',
    '{"primary": "vector", "secondary": "graph", "embeddings": "detailed"}'
),
('email', 'Email',
    '{"processor": "EmailProcessor", "extract_threads": true, "privacy_mode": true}',
    '{"primary": "graph", "secondary": "vector", "embeddings": "privacy_aware"}'
),
('general', 'General Document',
    '{"processor": "GeneralProcessor", "auto_detect": true}',
    '{"primary": "vector", "secondary": "sql", "embeddings": "standard"}'
)
ON CONFLICT (name) DO NOTHING;

-- Create internal ELF tenant
INSERT INTO rag.tenants (name, display_name, settings) VALUES
('elf_internal', 'ELF Automations Internal', 
    '{"is_internal": true, "unlimited_quota": true}'
)
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- VIEWS
-- =====================================================

-- Document processing status view
CREATE OR REPLACE VIEW rag.document_status AS
SELECT 
    t.name as tenant_name,
    w.name as workspace_name,
    d.filename,
    d.status,
    d.processing_started_at,
    d.processing_completed_at,
    d.processing_error,
    dt.name as document_type
FROM rag.documents d
JOIN rag.tenants t ON d.tenant_id = t.id
LEFT JOIN rag.workspaces w ON d.workspace_id = w.id
LEFT JOIN rag.document_types dt ON d.document_type_id = dt.id;

-- Tenant usage summary
CREATE OR REPLACE VIEW rag.tenant_usage AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    COUNT(DISTINCT d.id) as total_documents,
    COUNT(DISTINCT d.id) FILTER (WHERE d.status = 'completed') as processed_documents,
    COUNT(DISTINCT d.id) FILTER (WHERE d.status = 'failed') as failed_documents,
    SUM(d.size_bytes) / 1024 / 1024 / 1024 as total_size_gb,
    COUNT(DISTINCT sq.id) as total_searches,
    COUNT(DISTINCT au.id) as total_api_calls
FROM rag.tenants t
LEFT JOIN rag.documents d ON t.id = d.tenant_id
LEFT JOIN rag.search_queries sq ON t.id = sq.tenant_id
LEFT JOIN rag.api_usage au ON t.id = au.tenant_id
GROUP BY t.id, t.name;

-- Processing queue status
CREATE OR REPLACE VIEW rag.queue_status AS
SELECT 
    t.name as tenant_name,
    pq.status,
    COUNT(*) as count,
    MIN(pq.scheduled_at) as oldest_item,
    MAX(pq.scheduled_at) as newest_item
FROM rag.processing_queue pq
JOIN rag.tenants t ON pq.tenant_id = t.id
GROUP BY t.name, pq.status
ORDER BY t.name, pq.status;

COMMENT ON SCHEMA rag IS 'Multi-tenant RAG system schema with complete data isolation';
COMMENT ON TABLE rag.tenants IS 'Organizations using the RAG system';
COMMENT ON TABLE rag.documents IS 'Master record for all ingested documents with multi-tenant isolation';
COMMENT ON TABLE rag.processing_queue IS 'Async processing queue for document ingestion';