# ElfAutomations Autonomy Fix Plan

## Goal
Fix the critical missing pieces so ElfAutomations can autonomously build your construction PM platform.

## Phase 1: Foundation (Week 1) - "Make Teams Work"

### 1.1 Python Module Structure (Day 1)
**Why First**: Nothing works without proper imports
```bash
# Create proper package structure
elf_automations/
├── __init__.py
├── shared/
│   ├── __init__.py
│   ├── a2a/
│   │   ├── __init__.py
│   │   ├── client.py      # A2A client interface
│   │   └── mock_client.py # For testing
│   └── mcp/
│       ├── __init__.py
│       └── client.py      # MCP client for AgentGateway
├── teams/
│   └── (existing teams)
└── setup.py               # Make it pip installable
```

### 1.2 MCP Client Library (Day 2)
**Why Next**: Teams need to access external services
```python
# elf_automations/shared/mcp/client.py
class MCPClient:
    def __init__(self, gateway_url="http://agentgateway.dev"):
        self.gateway_url = gateway_url

    async def call(self, server: str, tool: str, args: dict):
        # Routes through AgentGateway
        endpoint = f"{self.gateway_url}/mcp/{server}/{tool}"
        return await self._post(endpoint, args)
```

### 1.3 Fix Team Factory (Day 3-4)
**Critical Bugs to Fix**:
1. Filename length issue (use team name, not description)
2. Template variable bug (crew_class undefined)
3. Add error handling
4. Test with various inputs

### 1.4 Team Registry MCP (Day 5)
**Self-Awareness Foundation**:
```yaml
# mcps/team-registry/config.yaml
name: team-registry
type: internal
capabilities:
  - check_registry_exists
  - list_all_teams
  - get_team_details
  - register_team
  - get_organization_stats
```

## Phase 2: Resource Management (Week 2) - "Don't Hit Limits"

### 2.1 API Quota Manager (Day 1-2)
```python
# elf_automations/shared/quota/manager.py
class QuotaManager:
    def check_usage(self, team: str) -> dict
    def can_make_request(self, team: str, cost: float) -> bool
    def track_usage(self, team: str, model: str, tokens: int)
    def get_remaining_budget(self, team: str) -> float
```

### 2.2 Model Fallback System (Day 3)
- Start with GPT-4
- Fall back to GPT-3.5 at 80% quota
- Alert CEO when approaching limits
- Daily/weekly reports to CFO

### 2.3 Cost Tracking Integration (Day 4-5)
- Per-team budgets in Supabase
- Real-time usage tracking
- Automatic alerts
- Usage analytics

## Phase 3: True Autonomy (Week 3) - "No Manual Steps"

### 3.1 Infrastructure Automation (Day 1-2)
**CEO Enhancement**:
```python
# When CEO receives first request:
if not self.check_infrastructure():
    self.delegate_to_cto("Initialize infrastructure")
    # CTO's DevOps team runs all setup
```

### 3.2 Credential Management (Day 3)
**One-Time Setup Wizard**:
```bash
elf-automations init
> Welcome! Let's set up your credentials.
> Supabase URL: [user enters]
> OpenAI API Key: [user enters]
> [Encrypted and stored locally]
```

### 3.3 Database Migration System (Day 4-5)
- Migration MCP that tracks schema versions
- Automatic migration on startup
- Rollback capability
- Version control for schemas

## Implementation Order & Why

### Week 1 Priority: "Make It Work"
1. **Module Structure** - Everything depends on imports
2. **MCP Client** - Teams need external services
3. **Team Factory** - Can't create teams without it
4. **Registry MCP** - Need self-awareness

### Week 2 Priority: "Make It Sustainable"
1. **Quota Management** - Prevent failures
2. **Model Fallback** - Graceful degradation
3. **Cost Tracking** - Financial visibility

### Week 3 Priority: "Make It Autonomous"
1. **Infrastructure Auto** - No manual setup
2. **Credential Mgmt** - One-time config
3. **Migration System** - Schema management

## Quick Wins (Can Do Today)

### 1. Create Module Structure
```bash
mkdir -p elf_automations/shared/{a2a,mcp,quota}
touch elf_automations/__init__.py
touch elf_automations/shared/__init__.py
# ... etc
```

### 2. Simple MCP Client Stub
Create basic client that teams can import (even if not fully functional)

### 3. Fix Team Factory Filename Bug
One-line fix for the filename issue

### 4. Add Anthropic as Fallback
When OpenAI quota exceeded, use Claude

## Success Criteria
After Phase 3, you should be able to:
1. Say: "Build me a construction PM platform"
2. CEO delegates to teams
3. Teams create PRD, build product, create marketing
4. No manual intervention required
5. Automatic fallbacks when quotas hit
6. Full visibility into costs and usage

## Next Step
Should we start with the module structure fix? It's the foundation everything else builds on, and we can do it right now.

Ready to begin making ElfAutomations truly autonomous?
