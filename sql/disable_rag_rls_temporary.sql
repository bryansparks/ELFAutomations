-- Temporarily disable RLS for initial setup
-- Run this to allow creating initial tenants

-- Disable RLS on all RAG tables
ALTER TABLE rag_tenants DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_workspaces DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_document_chunks DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_processing_queue DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_entities DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_relationships DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_search_queries DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_api_usage DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_watch_folders DISABLE ROW LEVEL SECURITY;
ALTER TABLE rag_oauth_events DISABLE ROW LEVEL SECURITY;

-- Verify RLS is disabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename LIKE 'rag_%'
ORDER BY tablename;
