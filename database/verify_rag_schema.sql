-- Verify RAG Schema Setup
-- Run this in Supabase SQL Editor to check if the schema was created correctly

-- Check if schema exists
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name = 'rag';

-- List all tables in rag schema
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'rag'
ORDER BY table_name;

-- Count rows in each table
SELECT 'rag.tenants' as table_name, COUNT(*) as row_count FROM rag.tenants
UNION ALL
SELECT 'rag.workspaces', COUNT(*) FROM rag.workspaces
UNION ALL
SELECT 'rag.documents', COUNT(*) FROM rag.documents
UNION ALL
SELECT 'rag.document_chunks', COUNT(*) FROM rag.document_chunks
UNION ALL
SELECT 'rag.processing_queue', COUNT(*) FROM rag.processing_queue
UNION ALL
SELECT 'rag.document_types', COUNT(*) FROM rag.document_types
UNION ALL
SELECT 'rag.entities', COUNT(*) FROM rag.entities
UNION ALL
SELECT 'rag.relationships', COUNT(*) FROM rag.relationships
UNION ALL
SELECT 'rag.search_queries', COUNT(*) FROM rag.search_queries
UNION ALL
SELECT 'rag.api_usage', COUNT(*) FROM rag.api_usage
ORDER BY table_name;

-- Check if RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'rag'
ORDER BY tablename;

-- List all functions in rag schema
SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'rag'
ORDER BY routine_name;

-- Quick data check
SELECT 'Document Types:' as info;
SELECT name, display_name FROM rag.document_types;

SELECT 'Tenants:' as info;
SELECT name, display_name, status FROM rag.tenants;
