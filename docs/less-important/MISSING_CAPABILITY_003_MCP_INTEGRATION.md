# Missing Capability #003: Teams Using MCPs for Infrastructure Tasks

## The Problem
The `setup_team_registry.py` script tries to connect to Supabase directly instead of using the Supabase MCP that's already configured and working.

## Current State
- Scripts use direct database connections
- Require additional credentials (SUPABASE_DB_URL)
- Don't leverage existing MCP infrastructure
- Inconsistent with how teams should work

## Desired State
Teams and setup scripts should:
1. Use MCPs for all external service interactions
2. Never need direct database credentials
3. Leverage the MCP's existing authentication
4. Follow the same patterns teams will use

## The Realization
This setup script predates our MCP architecture! It should be rewritten to:
```python
# Instead of direct connection
def setup_team_registry():
    db = connect_to_supabase(SUPABASE_DB_URL)  # OLD WAY

# Should use MCP
def setup_team_registry():
    mcp = get_mcp_client('supabase')
    mcp.execute_sql(CREATE_TABLES_SQL)  # NEW WAY
```

## How Teams Should Handle Infrastructure
When the DevOps team needs to set up infrastructure:
1. CEO: "Set up team registry"
2. CTO → DevOps team
3. DevOps team uses Supabase MCP to:
   - Create tables
   - Set up indexes
   - Configure permissions
4. Never touches raw credentials

## Immediate Solution
Let's check if we already have the tables from our earlier work today. If so, we can skip this setup entirely and proceed with team creation.

## Long-term Solution
1. Rewrite all setup scripts to use MCPs
2. DevOps team only interacts via MCPs
3. No team ever needs database credentials
4. All infrastructure tasks go through MCPs

Should we:
A. Check if tables already exist (via MCP) and skip setup
B. Load .env and run the old script
C. Rewrite the script to use MCP first

I recommend Option A - let's check if the tables exist!
