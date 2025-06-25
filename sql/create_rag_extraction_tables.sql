-- =====================================================
-- RAG System - Flexible Extraction Schema Extensions
-- =====================================================
-- This extends the base RAG schema with tables for dynamic
-- document type handling and flexible entity extraction
-- =====================================================

-- Document type extraction schemas
CREATE TABLE IF NOT EXISTS rag_extraction_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,

    -- Entity types this document type can have
    entity_types JSONB NOT NULL DEFAULT '[]',
    -- Example: ["party", "jurisdiction", "term", "obligation"]

    -- Relationship types between entities
    relationship_types JSONB NOT NULL DEFAULT '[]',
    -- Example: ["PARTY_TO", "GOVERNED_BY", "CONTAINS_TERM"]

    -- Extraction configuration
    extraction_config JSONB NOT NULL DEFAULT '{}',
    -- Example: {
    --   "llm_model": "gpt-4",
    --   "temperature": 0.1,
    --   "extraction_prompt_template": "...",
    --   "confidence_threshold": 0.8
    -- }

    -- Chunking strategy for this document type
    chunking_strategy JSONB NOT NULL DEFAULT '{}',
    -- Example: {
    --   "primary_strategy": "semantic",
    --   "fallback_strategy": "sliding_window",
    --   "chunk_size": 1000,
    --   "overlap": 200,
    --   "preserve_entities": true
    -- }

    -- Neo4j schema configuration
    graph_schema JSONB NOT NULL DEFAULT '{}',
    -- Example: {
    --   "node_labels": {"party": "Party", "term": "ContractTerm"},
    --   "relationship_types": {"PARTY_TO": "IS_PARTY_TO"},
    --   "node_properties": {"party": ["name", "type", "jurisdiction"]}
    -- }

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Extracted entities with flexible schema
CREATE TABLE IF NOT EXISTS rag_extracted_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag_tenants(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,

    -- Entity information
    entity_type TEXT NOT NULL,
    entity_value TEXT NOT NULL,
    normalized_value TEXT, -- Standardized version

    -- Flexible properties based on entity type
    properties JSONB NOT NULL DEFAULT '{}',
    -- Example for party: {"name": "ACME Corp", "type": "corporation", "jurisdiction": "Delaware"}
    -- Example for date: {"date": "2024-01-20", "type": "expiration", "timezone": "UTC"}

    -- Extraction metadata
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    extraction_method TEXT, -- "llm", "regex", "ner", etc.
    source_chunk_id UUID REFERENCES rag_document_chunks(id),
    source_text TEXT, -- Original text where entity was found
    source_offset INTEGER, -- Character offset in document

    -- Graph storage reference
    neo4j_node_id TEXT,
    neo4j_labels TEXT[], -- Multiple labels possible

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure uniqueness per document and entity
    UNIQUE(document_id, entity_type, normalized_value)
);

-- Relationships between extracted entities
CREATE TABLE IF NOT EXISTS rag_entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag_tenants(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,

    -- Relationship endpoints
    source_entity_id UUID NOT NULL REFERENCES rag_extracted_entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES rag_extracted_entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,

    -- Flexible properties for the relationship
    properties JSONB NOT NULL DEFAULT '{}',
    -- Example: {"effective_date": "2024-01-01", "conditions": ["payment received"]}

    -- Metadata
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    extraction_method TEXT,
    source_text TEXT, -- Text that indicates this relationship

    -- Graph storage reference
    neo4j_edge_id TEXT,
    neo4j_type TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicate relationships
    UNIQUE(document_id, source_entity_id, target_entity_id, relationship_type)
);

-- Chunk relationships for maintaining document structure
CREATE TABLE IF NOT EXISTS rag_chunk_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag_tenants(id) ON DELETE CASCADE,
    source_chunk_id UUID NOT NULL REFERENCES rag_document_chunks(id) ON DELETE CASCADE,
    target_chunk_id UUID NOT NULL REFERENCES rag_document_chunks(id) ON DELETE CASCADE,

    relationship_type TEXT NOT NULL CHECK (relationship_type IN (
        'NEXT_CHUNK', 'PREVIOUS_CHUNK', 'PARENT_SECTION', 'CHILD_SECTION',
        'REFERENCES', 'RELATED_TO', 'CONTINUATION_OF'
    )),

    -- Additional metadata
    properties JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicate relationships
    UNIQUE(source_chunk_id, target_chunk_id, relationship_type)
);

-- Document type detection results
CREATE TABLE IF NOT EXISTS rag_document_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,

    -- Classification results
    detected_type TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence BETWEEN 0 AND 1),

    -- Alternative classifications
    alternatives JSONB DEFAULT '[]',
    -- Example: [{"type": "invoice", "confidence": 0.3}, {"type": "receipt", "confidence": 0.1}]

    -- Classification metadata
    classification_method TEXT NOT NULL, -- "llm", "ml_model", "rule_based"
    model_used TEXT,
    classification_time_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Processing history for extraction
CREATE TABLE IF NOT EXISTS rag_extraction_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES rag_tenants(id) ON DELETE CASCADE,

    -- What was extracted
    extraction_type TEXT NOT NULL, -- "entities", "relationships", "metadata"
    items_extracted INTEGER NOT NULL DEFAULT 0,

    -- Performance metrics
    extraction_time_ms INTEGER,
    tokens_used INTEGER,
    cost_estimate DECIMAL(10, 4),

    -- Status
    status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'failed', 'partial')),
    error_details JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- =====================================================
-- DEFAULT EXTRACTION SCHEMAS
-- =====================================================

-- Insert default schemas for common document types
INSERT INTO rag_extraction_schemas (document_type, display_name, description, entity_types, relationship_types, extraction_config, chunking_strategy, graph_schema)
VALUES
-- Contract schema
('contract', 'Legal Contract', 'Legal agreements and contracts',
 '["party", "jurisdiction", "term", "obligation", "date", "monetary_amount"]'::jsonb,
 '["PARTY_TO", "GOVERNED_BY", "CONTAINS_OBLIGATION", "EXPIRES_ON", "REFERENCES"]'::jsonb,
 '{
   "llm_model": "gpt-4",
   "temperature": 0.1,
   "extraction_prompt_template": "Extract all parties, jurisdictions, key terms, obligations, and important dates from this contract.",
   "confidence_threshold": 0.8
 }'::jsonb,
 '{
   "primary_strategy": "semantic",
   "fallback_strategy": "structural",
   "preserve_entities": true,
   "respect_boundaries": ["clause", "section", "article"]
 }'::jsonb,
 '{
   "node_labels": {
     "party": "Party",
     "jurisdiction": "Jurisdiction",
     "term": "ContractTerm",
     "obligation": "Obligation"
   },
   "relationship_types": {
     "PARTY_TO": "IS_PARTY_TO",
     "GOVERNED_BY": "GOVERNED_BY"
   }
 }'::jsonb),

-- Invoice schema
('invoice', 'Invoice', 'Invoices and bills',
 '["vendor", "customer", "line_item", "product", "service", "monetary_amount", "date"]'::jsonb,
 '["BILLED_TO", "PROVIDED_BY", "CONTAINS", "TOTALS", "DUE_ON"]'::jsonb,
 '{
   "llm_model": "gpt-4",
   "temperature": 0.1,
   "extraction_prompt_template": "Extract vendor, customer, line items, amounts, and dates from this invoice.",
   "confidence_threshold": 0.9
 }'::jsonb,
 '{
   "primary_strategy": "structural",
   "preserve_tables": true,
   "preserve_entities": true
 }'::jsonb,
 '{
   "node_labels": {
     "vendor": "Organization",
     "customer": "Organization",
     "line_item": "LineItem",
     "product": "Product"
   }
 }'::jsonb),

-- Technical documentation schema
('technical_doc', 'Technical Documentation', 'Technical manuals and documentation',
 '["component", "system", "requirement", "procedure", "concept", "version"]'::jsonb,
 '["DESCRIBES", "DEPENDS_ON", "IMPLEMENTS", "PREREQUISITE_OF", "VERSION_OF", "REFERENCES"]'::jsonb,
 '{
   "llm_model": "gpt-4",
   "temperature": 0.2,
   "extraction_prompt_template": "Extract technical components, systems, requirements, and their relationships from this documentation.",
   "confidence_threshold": 0.7
 }'::jsonb,
 '{
   "primary_strategy": "structural",
   "fallback_strategy": "semantic",
   "preserve_hierarchy": true,
   "respect_boundaries": ["chapter", "section", "subsection"]
 }'::jsonb,
 '{
   "node_labels": {
     "component": "Component",
     "system": "System",
     "requirement": "Requirement",
     "procedure": "Procedure"
   }
 }'::jsonb);

-- =====================================================
-- INDEXES
-- =====================================================

-- Extraction schemas
CREATE INDEX IF NOT EXISTS idx_rag_extraction_schemas_active ON rag_extraction_schemas(document_type) WHERE is_active = true;

-- Extracted entities
CREATE INDEX IF NOT EXISTS idx_rag_extracted_entities_document ON rag_extracted_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_rag_extracted_entities_type ON rag_extracted_entities(document_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_rag_extracted_entities_normalized ON rag_extracted_entities(normalized_value);
CREATE INDEX IF NOT EXISTS idx_rag_extracted_entities_neo4j ON rag_extracted_entities(neo4j_node_id);

-- Entity relationships
CREATE INDEX IF NOT EXISTS idx_rag_entity_relationships_document ON rag_entity_relationships(document_id);
CREATE INDEX IF NOT EXISTS idx_rag_entity_relationships_source ON rag_entity_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_rag_entity_relationships_target ON rag_entity_relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_rag_entity_relationships_type ON rag_entity_relationships(relationship_type);

-- Chunk relationships
CREATE INDEX IF NOT EXISTS idx_rag_chunk_relationships_source ON rag_chunk_relationships(source_chunk_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunk_relationships_target ON rag_chunk_relationships(target_chunk_id);

-- Document classifications
CREATE INDEX IF NOT EXISTS idx_rag_document_classifications_document ON rag_document_classifications(document_id);
CREATE INDEX IF NOT EXISTS idx_rag_document_classifications_type ON rag_document_classifications(detected_type);

-- Extraction history
CREATE INDEX IF NOT EXISTS idx_rag_extraction_history_document ON rag_extraction_history(document_id);
CREATE INDEX IF NOT EXISTS idx_rag_extraction_history_status ON rag_extraction_history(status, created_at DESC);

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to get extraction schema for a document
CREATE OR REPLACE FUNCTION get_extraction_schema(doc_type TEXT)
RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT row_to_json(es.*)
        FROM rag_extraction_schemas es
        WHERE es.document_type = doc_type
        AND es.is_active = true
    );
END;
$$ LANGUAGE plpgsql;

-- Function to calculate extraction completeness
CREATE OR REPLACE FUNCTION calculate_extraction_completeness(doc_id UUID)
RETURNS FLOAT AS $$
DECLARE
    total_expected INTEGER;
    total_extracted INTEGER;
BEGIN
    -- Get expected entity types from schema
    SELECT array_length(
        (SELECT entity_types::text[]
         FROM rag_extraction_schemas es
         JOIN rag_documents d ON d.document_type_id = es.id
         WHERE d.id = doc_id), 1
    ) INTO total_expected;

    -- Count distinct entity types extracted
    SELECT COUNT(DISTINCT entity_type)
    FROM rag_extracted_entities
    WHERE document_id = doc_id
    INTO total_extracted;

    IF total_expected IS NULL OR total_expected = 0 THEN
        RETURN 0;
    END IF;

    RETURN (total_extracted::FLOAT / total_expected::FLOAT);
END;
$$ LANGUAGE plpgsql;
