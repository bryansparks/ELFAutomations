# Missing Capability #001: Automated Infrastructure Setup

## The Problem
Currently, setting up the Team Registry requires manual execution of `setup_team_registry.py`. This breaks the autonomous operation model where you should just be able to talk to the CEO.

## Current State
- User must manually run setup scripts
- User needs to know what infrastructure exists
- User needs technical knowledge of the system

## Desired State
When you send your first request to the CEO, the system should:
1. Auto-detect missing infrastructure
2. Create necessary schemas/tables
3. Initialize required services
4. Then proceed with the request

## Proposed Solution: Infrastructure Management Team

### Option 1: DevOps Team Enhancement
Add infrastructure management capabilities to the DevOps team:
- Auto-detect missing schemas
- Run setup scripts automatically
- Monitor infrastructure health
- Self-heal when possible

### Option 2: New Infrastructure Team
Create `infrastructure-team` reporting to CTO:
- Database Administrator (manages schemas)
- Infrastructure Engineer (manages services)
- Automation Specialist (creates setup workflows)
- Monitoring Engineer (health checks)

### Option 3: CEO Capability Enhancement
Give the CEO agent ability to:
- Check infrastructure status on startup
- Delegate infrastructure setup to CTO
- CTO's DevOps team handles setup
- Then proceed with original request

## Recommended Approach
**Option 3** - CEO-driven infrastructure checks

When CEO receives any request:
```python
# In CEO agent logic
if first_request_ever:
    check_infrastructure_status()
    if not team_registry_exists:
        delegate_to_cto("Set up team registry infrastructure")
        wait_for_completion()
    proceed_with_request()
```

## How ElfAutomations Would Work Without Claude Code

1. **Single Entry Point**: Web UI or CLI that talks to CEO
   ```bash
   elf-automations "Build me a construction PM platform"
   ```

2. **CEO Receives Request**:
   - Checks infrastructure (auto-setup if needed)
   - Analyzes request
   - Delegates to teams

3. **Autonomous Operation**:
   - No manual script running
   - No technical knowledge required
   - Just describe what you want

## Implementation Path
1. Enhance CEO to check infrastructure
2. Create DevOps team with setup capabilities
3. All setup scripts become MCP tools for DevOps
4. CEO delegates infrastructure tasks like any other task

## Decision Needed
Should we:
A. Continue with manual setup for now (faster development)
B. Build infrastructure automation first (better long-term)
C. Hybrid: Manual now, add automation after core teams exist

What's your preference?
