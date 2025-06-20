-- Grant permissions for RAG schema access via Supabase API
-- Run this AFTER creating the RAG schema

-- Grant usage on the rag schema to API roles
GRANT USAGE ON SCHEMA rag TO anon, authenticated, service_role;

-- Grant permissions on all tables in the rag schema
GRANT ALL ON ALL TABLES IN SCHEMA rag TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA rag TO service_role;

-- Grant permissions on all sequences (for auto-generated IDs)
GRANT ALL ON ALL SEQUENCES IN SCHEMA rag TO anon, authenticated, service_role;

-- Grant permissions on all functions/procedures
GRANT ALL ON ALL FUNCTIONS IN SCHEMA rag TO anon, authenticated, service_role;

-- Make sure future tables also get permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA rag
    GRANT ALL ON TABLES TO anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA rag
    GRANT ALL ON SEQUENCES TO anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA rag
    GRANT ALL ON FUNCTIONS TO anon, authenticated;

-- Add rag schema to search path for easier access (optional)
-- This allows accessing tables without the schema prefix
-- ALTER DATABASE your_database_name SET search_path TO public, rag;

-- Verify permissions were granted
SELECT 
    schemaname,
    tablename,
    has_table_privilege('anon', schemaname||'.'||tablename, 'SELECT') as anon_select,
    has_table_privilege('anon', schemaname||'.'||tablename, 'INSERT') as anon_insert,
    has_table_privilege('authenticated', schemaname||'.'||tablename, 'SELECT') as auth_select,
    has_table_privilege('authenticated', schemaname||'.'||tablename, 'INSERT') as auth_insert
FROM pg_tables 
WHERE schemaname = 'rag'
ORDER BY tablename;

-- Show current search path
SHOW search_path;

-- If you need to expose the schema in PostgREST (Supabase's API layer):
-- Note: This usually requires configuration in Supabase dashboard or environment variables
-- The config looks like: PGRST_DB_SCHEMAS="public,rag"