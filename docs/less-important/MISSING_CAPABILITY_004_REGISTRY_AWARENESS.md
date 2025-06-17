# Missing Capability #004: Team Registry Self-Awareness

## The Problem
Teams and the CEO have no way to check what teams exist, what infrastructure is set up, or the current state of the organization. This leads to duplicate setup attempts and no organizational memory.

## Current State
- No way to query existing teams
- No way to check if registry exists
- Scripts blindly try to create tables
- CEO can't tell you what teams exist

## Desired State
ElfAutomations should be able to:
1. CEO: "What teams do I have?"
2. CEO: "Is the infrastructure ready?"
3. Any team: "Who else exists in the organization?"
4. Automatic detection before creating duplicates

## Proposed Solution: Registry MCP

### Create `team-registry-mcp`
An internal MCP that provides:
```typescript
interface TeamRegistryMCP {
  // Query capabilities
  checkRegistryExists(): boolean
  listAllTeams(): Team[]
  getTeamDetails(teamId: string): TeamDetails
  getTeamHierarchy(): OrgChart
  findTeamByRole(role: string): Team[]

  // Setup capabilities
  initializeRegistry(): void
  validateRegistrySchema(): boolean

  // Reporting
  getOrganizationStats(): OrgStats
  getTeamRelationships(): Relationships[]
}
```

## How It Should Work

### Scenario 1: First Request Ever
```
User: "Build me an app"
CEO: [Checks registry via MCP]
     "I notice this is our first project. Let me set up the organization."
CEO → CTO: "Initialize team registry"
CTO → DevOps: "Set up infrastructure"
DevOps: [Uses team-registry-mcp.initializeRegistry()]
CEO: "Infrastructure ready. Now let's build your app..."
```

### Scenario 2: Checking Organization State
```
User: "What teams do we have?"
CEO: [Uses team-registry-mcp.listAllTeams()]
     "We currently have:
      - Executive Team (5 members)
      - Product Team (5 members)
      - Engineering Team (5 members)
      With 3 teams reporting to CTO..."
```

### Scenario 3: Before Creating Teams
```
Team Factory: [Before creating any team]
  - Check if registry exists
  - Check if team name already taken
  - Validate parent team exists
  - Then proceed with creation
```

## Integration Points

1. **CEO Agent**: Add registry awareness
   - Check on startup
   - Query before delegating
   - Report organization status

2. **Team Factory**: Use MCP before creating
   - Validate registry exists
   - Check for duplicates
   - Ensure parent teams exist

3. **All Managers**: Can query who exists
   - Find teams to collaborate with
   - Understand reporting structure
   - Know who to delegate to

## Implementation Priority
**HIGH** - This is blocking smooth operation

Without this:
- We blindly run setup scripts
- We can't check what exists
- CEO can't answer basic questions
- Teams don't know who else exists

## Recommended Next Step
1. Create team-registry-mcp first
2. Use it to check if tables exist
3. If not, create them via MCP
4. Then proceed with team creation

This makes ElfAutomations self-aware!
