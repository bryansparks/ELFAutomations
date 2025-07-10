# Database Schemas for Context-as-a-Service

This directory contains all SQL schemas needed for the Context-as-a-Service system.

## Schema Files

1. **01_rag_system_tables.sql**
   - Core RAG tables: tenants, workspaces, documents, chunks
   - Multi-tenant structure with RLS (Row Level Security)
   - Document processing pipeline tables

2. **02_rag_extraction_tables.sql**
   - Entity extraction tables
   - Relationship graphs
   - Processing queue management

3. **03_mcp_registry.sql**
   - MCP server registration
   - Capability tracking
   - Service discovery

4. **04_auth_tables.sql** (Added for standalone operation)
   - API key management
   - Usage tracking and rate limiting
   - Audit logging
   - Optional user authentication

5. **05_qdrant_collections.sql** (Added for standalone operation)
   - Vector collection metadata
   - Collection statistics
   - Default collections setup

## Setup Instructions

### Option 1: Using the init script (Recommended)

```bash
cd context-as-a-service
python scripts/init_database.py
```

This will:
- Create all schemas
- Execute all SQL files in order
- Create initial API keys
- Set up default collections

### Option 2: Manual setup

If you prefer to run the SQL manually:

```bash
# Connect to your database
psql $DATABASE_URL

# Run each schema file in order
\i database/schemas/01_rag_system_tables.sql
\i database/schemas/02_rag_extraction_tables.sql
\i database/schemas/03_mcp_registry.sql
\i database/schemas/04_auth_tables.sql
\i database/schemas/05_qdrant_collections.sql
```

## Database Requirements

- PostgreSQL 14+ (for gen_random_uuid() function)
- Supabase or any PostgreSQL-compatible database
- Extensions needed: pgcrypto (usually pre-installed)

## Multi-Tenancy

The system is designed for multi-tenancy from the ground up:

- Each tenant has isolated data
- Row Level Security (RLS) enforces isolation
- API keys are tenant-specific
- Collections can be shared or tenant-specific

## Default Data

The schemas include some default data:

- Default document types and processors
- Default vector collections (design_system_docs, architecture_decisions, etc.)
- Sample configuration for common use cases

## Customization

You can customize the schemas for your needs:

1. **Change embedding dimensions**: Update the dimension in collection configs
2. **Add custom document types**: Insert into `rag.document_types`
3. **Modify rate limits**: Adjust in `auth.api_keys` table
4. **Add indexes**: For performance optimization based on your queries

## Backup and Migration

Always backup your database before making schema changes:

```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

For migrations, consider using tools like:
- Flyway
- Liquibase
- golang-migrate

## Security Notes

1. **API Keys**: Store hashed, never plain text
2. **RLS**: Ensure RLS policies match your security model
3. **Audit**: All actions are logged in auth.audit_log
4. **Secrets**: Use environment variables, never hardcode
