-- Memory & Learning System Schema for ElfAutomations
-- This schema stores metadata for the memory system while vectors are stored in Qdrant

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Memory entries metadata
CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    agent_name VARCHAR(255),
    entry_type VARCHAR(50) NOT NULL CHECK (entry_type IN ('interaction', 'decision', 'learning', 'experience', 'insight')),
    title VARCHAR(500),
    content TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    
    -- Vector reference
    vector_id VARCHAR(255) UNIQUE, -- Qdrant point ID
    collection_name VARCHAR(255) DEFAULT 'default',
    embedding_model VARCHAR(50) DEFAULT 'text-embedding-ada-002',
    embedding_dimension INTEGER DEFAULT 1536,
    
    -- Usage tracking
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- For temporary memories
    is_archived BOOLEAN DEFAULT FALSE
);

-- Indexes for efficient querying
CREATE INDEX idx_memory_entries_team_id ON memory_entries(team_id);
CREATE INDEX idx_memory_entries_entry_type ON memory_entries(entry_type);
CREATE INDEX idx_memory_entries_created_at ON memory_entries(created_at DESC);
CREATE INDEX idx_memory_entries_tags ON memory_entries USING GIN(tags);
CREATE INDEX idx_memory_entries_vector_id ON memory_entries(vector_id);

-- Memory collections for organizing memories
CREATE TABLE IF NOT EXISTS memory_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    collection_type VARCHAR(50) DEFAULT 'general',
    team_id UUID REFERENCES teams(id), -- NULL means shared across all teams
    
    -- Configuration
    config JSONB DEFAULT '{}',
    embedding_config JSONB DEFAULT '{}',
    retention_policy JSONB DEFAULT '{"days": 365}',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Learning patterns extracted from experiences
CREATE TABLE IF NOT EXISTS learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL CHECK (pattern_type IN ('success', 'failure', 'optimization', 'warning', 'insight')),
    category VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    
    -- Pattern details
    conditions JSONB NOT NULL, -- When this pattern applies
    actions JSONB, -- What was done
    outcomes JSONB NOT NULL, -- What happened
    recommendations JSONB, -- What to do next time
    
    -- Statistical tracking
    occurrence_count INTEGER DEFAULT 1,
    success_rate FLOAT,
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Related memories
    supporting_memories UUID[] DEFAULT '{}',
    contradicting_memories UUID[] DEFAULT '{}',
    
    -- Metadata
    discovered_by_team UUID REFERENCES teams(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_observed TIMESTAMP DEFAULT NOW(),
    is_validated BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_learning_patterns_type ON learning_patterns(pattern_type);
CREATE INDEX idx_learning_patterns_category ON learning_patterns(category);
CREATE INDEX idx_learning_patterns_confidence ON learning_patterns(confidence_score DESC);

-- Track memory relationships
CREATE TABLE IF NOT EXISTS memory_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id UUID REFERENCES memory_entries(id) ON DELETE CASCADE,
    target_memory_id UUID REFERENCES memory_entries(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- 'caused_by', 'similar_to', 'contradicts', 'supports', 'follows'
    strength FLOAT DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(source_memory_id, target_memory_id, relationship_type)
);

-- Team knowledge profiles
CREATE TABLE IF NOT EXISTS team_knowledge_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) UNIQUE,
    
    -- Expertise areas based on memories
    expertise_areas JSONB DEFAULT '[]',
    knowledge_domains TEXT[] DEFAULT '{}',
    
    -- Statistics
    total_memories INTEGER DEFAULT 0,
    total_patterns_discovered INTEGER DEFAULT 0,
    avg_memory_importance FLOAT,
    most_accessed_topics JSONB DEFAULT '[]',
    
    -- Learning metrics
    learning_velocity FLOAT, -- How fast the team learns
    pattern_recognition_rate FLOAT, -- How well they identify patterns
    knowledge_sharing_score FLOAT, -- How much they share with others
    
    -- Metadata
    last_calculated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Memory access logs for analytics
CREATE TABLE IF NOT EXISTS memory_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES memory_entries(id) ON DELETE CASCADE,
    accessed_by_team UUID REFERENCES teams(id),
    accessed_by_agent VARCHAR(255),
    access_type VARCHAR(50), -- 'search', 'direct', 'related', 'pattern_match'
    query_text TEXT,
    relevance_score FLOAT,
    was_helpful BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_memory_access_logs_memory_id ON memory_access_logs(memory_id);
CREATE INDEX idx_memory_access_logs_team ON memory_access_logs(accessed_by_team);
CREATE INDEX idx_memory_access_logs_created ON memory_access_logs(created_at DESC);

-- Functions for memory management

-- Update accessed count and timestamp
CREATE OR REPLACE FUNCTION update_memory_access()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE memory_entries 
    SET accessed_count = accessed_count + 1,
        last_accessed = NOW()
    WHERE id = NEW.memory_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_memory_access
AFTER INSERT ON memory_access_logs
FOR EACH ROW
EXECUTE FUNCTION update_memory_access();

-- Update pattern confidence based on outcomes
CREATE OR REPLACE FUNCTION update_pattern_confidence(
    pattern_id UUID,
    was_successful BOOLEAN
)
RETURNS VOID AS $$
DECLARE
    current_confidence FLOAT;
    current_count INTEGER;
BEGIN
    SELECT confidence_score, occurrence_count 
    INTO current_confidence, current_count
    FROM learning_patterns 
    WHERE id = pattern_id;
    
    -- Bayesian update of confidence
    UPDATE learning_patterns
    SET confidence_score = CASE 
            WHEN was_successful THEN 
                LEAST(1.0, current_confidence + (1.0 - current_confidence) / (current_count + 1))
            ELSE 
                GREATEST(0.0, current_confidence - current_confidence / (current_count + 1))
        END,
        occurrence_count = occurrence_count + 1,
        last_observed = NOW(),
        updated_at = NOW()
    WHERE id = pattern_id;
END;
$$ LANGUAGE plpgsql;

-- Views for easy querying

-- Most valuable memories by team
CREATE OR REPLACE VIEW team_valuable_memories AS
SELECT 
    me.team_id,
    t.name as team_name,
    me.id,
    me.title,
    me.entry_type,
    me.importance_score * LOG(me.accessed_count + 1) as value_score,
    me.accessed_count,
    me.created_at
FROM memory_entries me
JOIN teams t ON me.team_id = t.id
WHERE me.is_archived = FALSE
ORDER BY value_score DESC;

-- Active learning patterns with high confidence
CREATE OR REPLACE VIEW high_confidence_patterns AS
SELECT 
    lp.*,
    t.name as discovered_by_team_name
FROM learning_patterns lp
LEFT JOIN teams t ON lp.discovered_by_team = t.id
WHERE lp.confidence_score > 0.7
AND lp.occurrence_count >= 3
ORDER BY lp.confidence_score DESC, lp.occurrence_count DESC;

-- Row Level Security (RLS) Policies

ALTER TABLE memory_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_access_logs ENABLE ROW LEVEL SECURITY;

-- Policies would be added based on your auth strategy
-- For now, we'll keep it simple for MCP access

-- Grants for MCP server access (adjust the role name as needed)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO mcp_memory_server;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO mcp_memory_server;

-- Insert default memory collection
INSERT INTO memory_collections (name, description, collection_type)
VALUES ('default', 'Default memory collection for all teams', 'general')
ON CONFLICT (name) DO NOTHING;