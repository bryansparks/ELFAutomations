# RAG System Row Level Security (RLS) Setup Guide

## The RLS Issue

When you run the setup script and try to create test tenants, you get:
```
Failed to create elf_internal: {'code': '42501', 'details': None, 'hint': None,
'message': 'new row violates row-level security policy for table "rag_tenants"'}
```

This happens because Row Level Security (RLS) is enabled on the tables, which blocks inserts unless a tenant context is set.

## Solutions

### Option 1: Temporarily Disable RLS (Quickest)

1. **Run in Supabase SQL Editor**:
   ```sql
   -- Copy contents from:
   sql/disable_rag_rls_temporary.sql
   ```

2. **Run the setup script**:
   ```bash
   python scripts/setup_rag_public_schema.py
   ```

3. **Re-enable RLS** (optional but recommended):
   ```sql
   -- Copy contents from:
   sql/enable_rag_rls.sql
   ```

### Option 2: Fix RLS Policies (Better for Production)

1. **Run in Supabase SQL Editor**:
   ```sql
   -- Copy contents from:
   sql/fix_rag_rls_policies.sql
   ```

2. **Run the setup script**:
   ```bash
   python scripts/setup_rag_public_schema.py
   ```

The fixed policies allow operations when no tenant context is set, which is needed for initial setup.

### Option 3: Use Service Role Key (Most Secure)

If you have a service role key (bypasses RLS):

1. **Update your .env**:
   ```bash
   SUPABASE_SERVICE_KEY=your-service-role-key
   ```

2. **Use service key for setup only**:
   ```python
   # In setup scripts, use:
   key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
   ```

## Understanding RLS in the RAG System

### How It Works

1. **Tenant Isolation**: Each tenant can only see their own data
2. **Context Setting**: Applications must set `app.current_tenant_id` before queries
3. **Policy Enforcement**: Database automatically filters results

### Example Usage in Production

```python
# Set tenant context
client.rpc("rag_set_tenant_context", {"tenant_id": tenant_id}).execute()

# Now all queries are automatically filtered
documents = client.from_("rag_documents").select("*").execute()
# Only returns documents for the current tenant
```

### RLS Policies Explained

The RAG system uses these RLS policies:

1. **rag_tenants**: Special handling - allows reading all tenants but controlled writes
2. **Other tables**: Filtered by `tenant_id` column matching current context
3. **Shared tables**: `rag_document_types` is read-only for all users

## Development vs Production

### Development
- Temporarily disable RLS for easier setup
- Use fixed policies that allow null context
- Re-enable strict RLS before production

### Production
- Always use RLS
- Set tenant context for every session
- Use service role keys sparingly
- Monitor access patterns

## Quick Commands

```bash
# Check RLS status
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename LIKE 'rag_%';

# Disable RLS on a specific table
ALTER TABLE rag_tenants DISABLE ROW LEVEL SECURITY;

# Enable RLS on a specific table
ALTER TABLE rag_tenants ENABLE ROW LEVEL SECURITY;
```

## Troubleshooting

If you still have issues after disabling RLS:

1. **Check permissions**:
   ```sql
   GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
   ```

2. **Verify your API key type**:
   - `anon` key: Subject to RLS
   - `service_role` key: Bypasses RLS

3. **Test with direct SQL**:
   ```sql
   INSERT INTO rag_tenants (name, display_name)
   VALUES ('test', 'Test Tenant');
   ```

This should resolve the RLS issues and allow you to complete the setup!
