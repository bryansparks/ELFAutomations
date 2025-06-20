-- Re-enable RLS after initial setup
-- Run this after creating initial tenants

-- Enable RLS on all RAG tables
ALTER TABLE rag_tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_processing_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_search_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_watch_folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_oauth_events ENABLE ROW LEVEL SECURITY;

-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename LIKE 'rag_%'
ORDER BY tablename;