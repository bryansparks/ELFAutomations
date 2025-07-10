-- Qdrant Collections Metadata Schema
-- Tracks vector collections and their configurations

-- =====================================================
-- COLLECTIONS TABLE
-- =====================================================

-- Metadata about Qdrant collections
CREATE TABLE IF NOT EXISTS rag.collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    tenant_id UUID REFERENCES rag.tenants(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES rag.workspaces(id) ON DELETE CASCADE,
    config JSONB NOT NULL DEFAULT '{}', -- dimension, distance metric, etc
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'creating', 'deleting', 'error')),
    vector_count BIGINT DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    last_indexed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_collections_tenant ON rag.collections(tenant_id);
CREATE INDEX idx_collections_workspace ON rag.collections(workspace_id);
CREATE INDEX idx_collections_name ON rag.collections(name);

-- =====================================================
-- COLLECTION STATS
-- =====================================================

-- Historical statistics for collections
CREATE TABLE IF NOT EXISTS rag.collection_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL REFERENCES rag.collections(id) ON DELETE CASCADE,
    vector_count BIGINT NOT NULL,
    total_size_bytes BIGINT NOT NULL,
    avg_search_latency_ms FLOAT,
    search_count_daily INTEGER,
    index_operations_daily INTEGER,
    error_count_daily INTEGER,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_collection_stats_collection_time ON rag.collection_stats(collection_id, recorded_at DESC);

-- =====================================================
-- DEFAULT COLLECTIONS
-- =====================================================

-- Insert default collections (these will be created in Qdrant on first use)
INSERT INTO rag.collections (name, description, config) VALUES
    ('default', 'Default document collection',
     '{"dimension": 1536, "distance": "cosine", "on_disk": false}'::jsonb),

    ('design_system_docs', 'UI/UX design system documentation',
     '{"dimension": 1536, "distance": "cosine", "on_disk": false}'::jsonb),

    ('architecture_decisions', 'Architecture decisions and patterns',
     '{"dimension": 1536, "distance": "cosine", "on_disk": false}'::jsonb),

    ('business_processes', 'Business process documentation',
     '{"dimension": 1536, "distance": "cosine", "on_disk": false}'::jsonb),

    ('code_examples', 'Code snippets and examples',
     '{"dimension": 1536, "distance": "cosine", "on_disk": false}'::jsonb),

    ('api_documentation', 'API specifications and docs',
     '{"dimension": 1536, "distance": "cosine", "on_disk": false}'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to get or create a collection for a tenant
CREATE OR REPLACE FUNCTION rag.get_or_create_collection(
    p_tenant_id UUID,
    p_collection_name TEXT,
    p_config JSONB DEFAULT '{"dimension": 1536, "distance": "cosine"}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    collection_id UUID;
BEGIN
    -- Try to get existing collection
    SELECT id INTO collection_id
    FROM rag.collections
    WHERE tenant_id = p_tenant_id AND name = p_collection_name;

    -- Create if not exists
    IF collection_id IS NULL THEN
        INSERT INTO rag.collections (tenant_id, name, config)
        VALUES (p_tenant_id, p_collection_name, p_config)
        RETURNING id INTO collection_id;
    END IF;

    RETURN collection_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update collection statistics
CREATE OR REPLACE FUNCTION rag.update_collection_stats(
    p_collection_id UUID,
    p_vector_count BIGINT,
    p_size_bytes BIGINT
)
RETURNS VOID AS $$
BEGIN
    -- Update main collection record
    UPDATE rag.collections
    SET
        vector_count = p_vector_count,
        total_size_bytes = p_size_bytes,
        last_indexed_at = NOW(),
        updated_at = NOW()
    WHERE id = p_collection_id;

    -- Insert historical record
    INSERT INTO rag.collection_stats (
        collection_id, vector_count, total_size_bytes
    ) VALUES (
        p_collection_id, p_vector_count, p_size_bytes
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update updated_at timestamp
CREATE TRIGGER update_collections_updated_at
    BEFORE UPDATE ON rag.collections
    FOR EACH ROW
    EXECUTE FUNCTION auth.update_updated_at();
