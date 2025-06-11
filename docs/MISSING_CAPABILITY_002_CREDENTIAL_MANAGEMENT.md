# Missing Capability #002: Autonomous Credential Management

## The Problem
Setup scripts require environment variables (SUPABASE_DB_URL) that must be manually configured. This breaks autonomous operation.

## Current State
- User must manually set environment variables
- User needs to find credentials in Supabase dashboard
- User needs to know which env vars are required
- Credentials are scattered across different services

## Desired State
ElfAutomations should be able to:
1. Detect missing credentials
2. Guide user through one-time secure credential storage
3. Retrieve credentials autonomously when needed
4. Rotate credentials when necessary

## Proposed Solution: Credentials Management Service

### Option 1: Executive Assistant Team
Create `executive.assistant-team` reporting to CEO:
- Credentials Manager (secure storage)
- Onboarding Specialist (guides setup)
- Security Officer (manages access)
- Integration Specialist (connects services)

### Option 2: Enhanced CEO Capabilities
CEO could have built-in credential management:
- Detect missing credentials
- Prompt user for one-time setup
- Store securely (local encrypted vault)
- Provide to teams as needed

### Option 3: Operations Team Enhancement
Add to the planned operations team:
- Systems Administrator role
- Manages all credentials and secrets
- Handles initial setup flow
- Maintains credential lifecycle

## How It Should Work

### First-Time Setup
```
User: "Build me a construction PM platform"
CEO: "Welcome! I need to set up some connections first."
CEO: "Please provide your Supabase credentials:"
     - Project URL: [user provides]
     - Anon Key: [user provides]
     - Service Key: [user provides securely]
     - Database URL: [user provides]
CEO: "Credentials stored securely. Setting up infrastructure..."
[Continues with request]
```

### Subsequent Requests
```
User: "Build me another app"
CEO: [Retrieves stored credentials automatically]
CEO: [Proceeds with request]
```

## Security Considerations
1. Credentials encrypted at rest
2. Only accessible to authorized agents
3. Audit log of credential access
4. Support for credential rotation
5. Optional: Integration with external vaults

## Implementation Path
1. Create simple credential storage MCP
2. Enhance CEO to detect and request missing creds
3. Store in encrypted local file or vault
4. Pass to teams via secure A2A messages

## Current Workaround
For now, let's check what credentials we need:
1. SUPABASE_URL (already set)
2. SUPABASE_ANON_KEY (already set)
3. SUPABASE_DB_URL (missing - PostgreSQL connection string)

## Decision Needed
Should we:
A. Set credentials manually now and continue
B. Build credential management first
C. Create a simple setup wizard script

Recommendation: Set manually now (Option A), build proper solution later.
