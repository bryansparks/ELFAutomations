# Missing Capability #007: Automated Database Migrations

## The Problem
Creating database tables requires manual intervention:
- Go to Supabase dashboard
- Navigate to SQL Editor
- Copy and paste SQL
- Run manually

This breaks autonomous operation.

## Current State
- SQL files exist but must be run manually
- No automated migration system
- Teams can't create their own tables
- Infrastructure setup is manual

## Desired State
When CEO receives first request:
1. CEO detects missing infrastructure
2. Delegates to CTO: "Set up database"
3. DevOps team runs migrations automatically
4. Uses version control for schema changes
5. Tracks what's been applied

## How Teams Would Handle This

### Option 1: Migration MCP
Create a `database-migration-mcp` that:
- Tracks migration history
- Applies pending migrations
- Rolls back if needed
- Version controls schema

### Option 2: DevOps Team Capability
DevOps team has migration tools:
- Check current schema state
- Apply new migrations
- Handle rollbacks
- Report status

### Option 3: Supabase Edge Functions
Create edge functions that:
- Teams can call to run migrations
- Check permissions
- Apply schema changes
- Return status

## The Manual Reality
For now:
1. We generate SQL files
2. User runs them manually
3. This is OK for bootstrap
4. But breaks true autonomy

## What This Teaches Us
Every manual step reveals where automation is needed. ElfAutomations can't be truly autonomous until it can:
- Set up its own infrastructure
- Manage its own schema
- Handle its own migrations
- Self-heal when needed

## Priority
Medium - Can work around for now, but needed for true autonomy
