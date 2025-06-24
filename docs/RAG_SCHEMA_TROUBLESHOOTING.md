# RAG Schema Troubleshooting Guide

## Issue: Tables created in `rag` schema but Python scripts can't access them

### The Problem
The SQL file creates all tables in a custom schema called `rag`:
```sql
CREATE SCHEMA IF NOT EXISTS rag;
CREATE TABLE IF NOT EXISTS rag.tenants (...);
```

But the Python Supabase client needs to access them with the schema prefix: `rag.tenants`

### Solutions

#### 1. Verify Schema Creation
First, run this SQL in your Supabase SQL Editor:
```sql
-- Check if rag schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'rag';

-- List tables in rag schema
SELECT table_name FROM information_schema.tables WHERE table_schema = 'rag';
```

#### 2. Test Python Access
Run the diagnostic script:
```bash
python scripts/test_rag_schema_access.py
```

This will show you exactly what's accessible from Python.

#### 3. Common Issues & Fixes

**Issue: Tables not accessible via API**
- By default, Supabase only exposes the `public` schema via the API
- Custom schemas need explicit configuration

**Fix Option 1: Add API exposure for rag schema**
Run this SQL in Supabase:
```sql
-- Grant usage on rag schema to anon and authenticated roles
GRANT USAGE ON SCHEMA rag TO anon, authenticated;

-- Grant permissions on all tables
GRANT ALL ON ALL TABLES IN SCHEMA rag TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA rag TO anon, authenticated;
GRANT ALL ON ALL ROUTINES IN SCHEMA rag TO anon, authenticated;

-- Make sure the schema is exposed in the API
-- Note: This might require Supabase dashboard configuration
```

**Fix Option 2: Create views in public schema (Alternative)**
If the above doesn't work, create views in the public schema:
```sql
-- Create views in public schema that reference rag schema tables
CREATE OR REPLACE VIEW public.rag_tenants AS SELECT * FROM rag.tenants;
CREATE OR REPLACE VIEW public.rag_documents AS SELECT * FROM rag.documents;
-- ... repeat for other tables

-- Grant permissions on views
GRANT ALL ON public.rag_tenants TO anon, authenticated;
GRANT ALL ON public.rag_documents TO anon, authenticated;
-- ... repeat for other views
```

Then update Python code to use:
```python
client.from_("rag_tenants")  # Instead of "rag.tenants"
```

**Fix Option 3: Move tables to public schema**
If custom schemas aren't working, you can move everything to the public schema:
```sql
-- This would require modifying the create_rag_system_tables.sql file
-- Replace all "rag." prefixes with "public." or remove them
```

#### 4. Updated Setup Process

1. **Run the SQL schema creation**:
   - Copy contents of `sql/create_rag_system_tables.sql`
   - Paste in Supabase SQL Editor
   - Run the query

2. **Grant permissions** (if needed):
   ```sql
   GRANT USAGE ON SCHEMA rag TO anon, authenticated;
   GRANT ALL ON ALL TABLES IN SCHEMA rag TO anon, authenticated;
   ```

3. **Test access**:
   ```bash
   python scripts/test_rag_schema_access.py
   ```

4. **Run setup**:
   ```bash
   python scripts/setup_rag_with_env.py
   ```

### Supabase Schema Configuration

In some Supabase projects, you may need to:

1. Go to Settings > API in your Supabase dashboard
2. Look for "Exposed schemas" configuration
3. Add `rag` to the list of exposed schemas

This makes the schema accessible via the PostgREST API.

### Quick Test

To quickly test if the issue is schema access, try this in your Python script:
```python
# Test different access patterns
client.from_("rag.tenants").select("*").execute()  # With schema
client.table("rag.tenants").select("*").execute()  # Alternative syntax
client.from_("tenants").select("*").execute()      # Without schema (if in search_path)
```

### If All Else Fails

Consider modifying the schema to use the default `public` schema:
1. Update `sql/create_rag_system_tables.sql` to remove the `rag.` prefix
2. Re-run the SQL
3. Update all Python scripts to remove the `rag.` prefix

This is less ideal architecturally but ensures compatibility with all Supabase configurations.
