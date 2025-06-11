# Database Migration Guide

## Overview

ElfAutomations now has a comprehensive database migration system that provides:
- Version-controlled schema changes
- Rollback capability
- Validation and best practices enforcement
- Team isolation and credential integration
- Zero-downtime migration support

## Architecture

```
migrations/
├── 20250121_093000_initial_team_registry.sql
├── 20250121_093100_initial_cost_monitoring.sql
├── 20250121_093200_add_user_profiles.sql
└── ...

┌─────────────────────┐
│  Migration Manager  │
├─────────────────────┤
│ • Version ordering  │
│ • Dependency check  │
│ • Rollback support  │
└──────────┬──────────┘
           │
┌──────────┴──────────┐
│  Schema Validator   │
├─────────────────────┤
│ • Naming rules      │
│ • Best practices    │
│ • Security checks   │
└──────────┬──────────┘
           │
┌──────────┴──────────┐
│ Supabase Executor   │
├─────────────────────┤
│ • Direct SQL exec   │
│ • Transaction mgmt  │
│ • Error handling    │
└─────────────────────┘
```

## Migration File Format

Each migration follows this structure:

```sql
-- Migration: Add User Profiles
-- Version: 20250121_093000
-- Description: Adds user profile tables for team members
-- Dependencies: ["20250120_140000_initial_schema"]

-- ============= UP MIGRATION =============

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    team_id UUID REFERENCES teams(id),
    display_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_team_id ON user_profiles(team_id);

-- ============= DOWN MIGRATION ============

DROP TABLE IF EXISTS user_profiles;
```

## CLI Usage

### Initialize Migration System

```bash
# First time setup
./scripts/elf-migrate init

# This will:
# 1. Create migrations/ directory
# 2. Generate initial migrations for existing schemas
# 3. Set up migration tracking tables
```

### Create a New Migration

```bash
# Create a new migration file
./scripts/elf-migrate create "add_user_preferences" \
  --description "Add user preference storage"

# This creates: migrations/20250121_094532_add_user_preferences.sql
```

### List Migrations

```bash
# Show all migrations
./scripts/elf-migrate list

# Show only pending migrations
./scripts/elf-migrate list --pending
```

### Validate Migrations

```bash
# Validate all pending migrations
./scripts/elf-migrate validate

# Validate specific migration
./scripts/elf-migrate validate migrations/20250121_094532_add_user_preferences.sql
```

### Run Migrations

```bash
# Run all pending migrations
./scripts/elf-migrate up

# Dry run (show what would be done)
./scripts/elf-migrate up --dry-run

# Run up to specific version
./scripts/elf-migrate up --target 20250121_094532

# Skip validation (not recommended)
./scripts/elf-migrate up --skip-validation
```

### Rollback Migrations

```bash
# Rollback specific migration
./scripts/elf-migrate down 20250121_094532

# Dry run rollback
./scripts/elf-migrate down 20250121_094532 --dry-run
```

### Check Status

```bash
# Show current migration status
./scripts/elf-migrate status
```

## Validation Rules

The schema validator enforces these rules:

### Naming Conventions
- **Tables**: lowercase with underscores (e.g., `user_profiles`)
- **Columns**: lowercase with underscores (e.g., `created_at`)
- **Indexes**: prefix with `idx_` (e.g., `idx_users_email`)
- **Constraints**: descriptive names (e.g., `fk_posts_user_id`)

### Best Practices
- All tables must have a PRIMARY KEY
- Use `UUID` with `gen_random_uuid()` for IDs
- Include `created_at TIMESTAMP DEFAULT NOW()`
- Add `IF NOT EXISTS` for idempotent migrations
- Create indexes on foreign key columns
- Avoid `CASCADE DELETE` without careful consideration

### Data Types
- Prefer `VARCHAR` or `TEXT` over `CHAR`
- Use `NUMERIC` instead of `FLOAT` for precision
- Use `JSONB` for flexible metadata
- Use proper PostgreSQL types (not MySQL/SQLite)

## Integration with Teams

### Team-Specific Schemas

Each team can have its own schema/tables:

```sql
-- Migration: Add Marketing Team Analytics
-- Version: 20250121_100000
-- Description: Analytics tables for marketing team

CREATE SCHEMA IF NOT EXISTS marketing;

CREATE TABLE IF NOT EXISTS marketing.campaign_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    cost_usd NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Grant access to marketing team role
GRANT ALL ON SCHEMA marketing TO marketing_team_role;
GRANT ALL ON ALL TABLES IN SCHEMA marketing TO marketing_team_role;
```

### Credential Integration

The migration system uses the credential manager:

```python
# Credentials are automatically loaded from secure storage
# No hardcoded database passwords needed
```

## Advanced Features

### Dependencies

Specify migration dependencies:

```sql
-- Dependencies: ["20250120_140000_initial_schema", "20250121_090000_add_teams"]
```

### Conditional Logic

Use PostgreSQL features for conditional migrations:

```sql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'preferences'
    ) THEN
        ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';
    END IF;
END $$;
```

### Zero-Downtime Migrations

For production systems:

```sql
-- Add column with default (fast in PostgreSQL 11+)
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';

-- Create index concurrently
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_status ON users(status);

-- Add constraint without locking
ALTER TABLE users ADD CONSTRAINT check_status_valid
CHECK (status IN ('active', 'inactive', 'suspended')) NOT VALID;

ALTER TABLE users VALIDATE CONSTRAINT check_status_valid;
```

## Migration Tracking

The system tracks migrations in these tables:

```sql
-- schema_migrations: Current state of each migration
SELECT * FROM schema_migrations ORDER BY version DESC;

-- migration_history: Full audit trail
SELECT * FROM migration_history ORDER BY started_at DESC;
```

## Troubleshooting

### Migration Failed

1. Check the error in migration history:
```sql
SELECT * FROM schema_migrations WHERE status = 'failed';
```

2. Fix the issue in the SQL file

3. Reset the migration status:
```sql
UPDATE schema_migrations SET status = 'pending' WHERE version = 'xxx';
```

4. Run again:
```bash
./scripts/elf-migrate up
```

### Connection Issues

1. Check credentials:
```bash
ELF_MASTER_PASSWORD="your-password" python -c "
from elf_automations.shared.credentials import CredentialManager
mgr = CredentialManager()
print(mgr.get_credential('SUPABASE_URL', 'system', 'check'))
"
```

2. Test connection:
```python
from elf_automations.shared.database import SupabaseExecutor
executor = SupabaseExecutor()
print(executor.test_connection())
```

### Rollback Issues

If a migration can't be rolled back:

1. Check if DOWN migration SQL exists
2. Manually fix the schema if needed
3. Update migration status:
```sql
UPDATE schema_migrations SET status = 'rolled_back' WHERE version = 'xxx';
```

## Best Practices

1. **Always test migrations locally first**
   ```bash
   ./scripts/elf-migrate up --dry-run
   ```

2. **Write rollback SQL for every migration**
   - Test the rollback works
   - Some changes can't be rolled back (data loss)

3. **Keep migrations small and focused**
   - One logical change per migration
   - Easier to debug and rollback

4. **Use transactions for data migrations**
   ```sql
   BEGIN;
   -- Your data migration here
   COMMIT;
   ```

5. **Document complex migrations**
   - Add comments explaining why
   - Include examples of affected data

6. **Version control migrations**
   - Commit migration files to git
   - Never modify executed migrations

## Example Workflows

### Adding a New Feature

```bash
# 1. Create migration
./scripts/elf-migrate create "add_task_assignments"

# 2. Edit the migration file
vim migrations/20250121_095000_add_task_assignments.sql

# 3. Validate
./scripts/elf-migrate validate

# 4. Test with dry run
./scripts/elf-migrate up --dry-run

# 5. Apply
./scripts/elf-migrate up

# 6. Verify
./scripts/elf-migrate status
```

### Emergency Rollback

```bash
# 1. Check current state
./scripts/elf-migrate status

# 2. Identify problem migration
./scripts/elf-migrate list

# 3. Rollback
./scripts/elf-migrate down 20250121_095000

# 4. Fix and reapply
vim migrations/20250121_095000_add_task_assignments.sql
./scripts/elf-migrate up
```

## Security Considerations

1. **Migrations run with service role credentials**
   - Full database access
   - Be careful with destructive operations

2. **Validate all SQL**
   - No hardcoded secrets
   - No backdoors or unauthorized access

3. **Audit trail**
   - All migrations are logged
   - Check migration_history for suspicious activity

4. **Backup before major migrations**
   - Supabase provides automatic backups
   - Consider manual backup for critical changes
