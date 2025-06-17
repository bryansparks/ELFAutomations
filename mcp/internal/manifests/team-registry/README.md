# Team Registry MCP

This MCP provides access to the ElfAutomations team registry stored in Supabase.

## Purpose

The team-registry MCP enables agents and teams to:
- Register new teams in the organization
- Query team information and relationships
- Manage team members and roles
- Track organizational hierarchy
- Support executive oversight of managed teams

## Tools Available

1. **register_team** - Register a new team with full metadata
2. **add_team_member** - Add members to existing teams
3. **query_teams** - Query teams by name, department, or executive
4. **get_team_hierarchy** - View complete organizational structure
5. **get_executive_teams** - List teams managed by an executive
6. **update_team_relationship** - Modify reporting relationships
7. **get_team_members** - List all members of a team
8. **get_team_composition** - Get team composition summary

## Configuration

Requires environment variables:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key

## Integration

This MCP integrates with:
- **AgentGateway** - For tool access
- **Supabase** - For data storage
- **Team Factory** - For team creation workflow

## Usage Example

```yaml
# In AgentGateway config
mcps:
  - name: team-registry
    endpoint: http://team-registry-mcp:5000
```

Teams can then use the registry:
```python
# Query marketing teams
teams = await mcp_client.call('team-registry', 'query_teams', {
    'department': 'marketing'
})

# Get team members
members = await mcp_client.call('team-registry', 'get_team_members', {
    'team_name': 'marketing-team'
})
```

## Security

- All operations go through Supabase RLS
- Teams should only be created via team-factory.py
- Read access is generally available
- Write access is restricted to authorized agents
