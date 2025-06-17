# Team Registry MCP Server

This MCP (Model Context Protocol) server provides access to the ElfAutomations team registry stored in Supabase. It allows agents and teams to query and manage team information, relationships, and organizational structure.

## Features

- **Team Registration**: Register new teams with complete metadata
- **Team Members**: Add and query team members with roles and responsibilities
- **Organizational Hierarchy**: Track and query reporting relationships
- **Executive Management**: Manage executive-to-team relationships
- **Team Composition**: Get summaries of team structures

## Prerequisites

1. Supabase database with team registry schema installed
2. Environment variables:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_ANON_KEY`: Your Supabase anonymous key

## Installation

```bash
cd mcp-servers-ts
npm install
```

## Running the Server

```bash
# Set environment variables
export SUPABASE_URL="your-supabase-url"
export SUPABASE_ANON_KEY="your-supabase-anon-key"

# Run the server
npm run start:team-registry
```

## Available Tools

### 1. register_team
Register a new team in the team registry.

**Parameters:**
- `name`: Team identifier (e.g., "marketing-team")
- `display_name`: Human-readable name
- `department`: Department the team belongs to
- `placement`: Organizational placement (dot notation)
- `purpose`: Team's purpose/description
- `framework`: "CrewAI" or "LangGraph"
- `llm_provider`: "OpenAI" or "Anthropic"
- `llm_model`: Specific model name
- `reports_to`: (Optional) Who this team reports to

### 2. add_team_member
Add a member to an existing team.

**Parameters:**
- `team_name`: Name of the team
- `role`: Member's role
- `is_manager`: Boolean indicating if manager
- `responsibilities`: Array of responsibilities
- `skills`: Array of skills
- `system_prompt`: Agent's system prompt

### 3. query_teams
Query teams by various criteria.

**Parameters:**
- `team_name`: (Optional) Specific team to query
- `department`: (Optional) Filter by department
- `executive_role`: (Optional) Find teams managed by executive

### 4. get_team_hierarchy
Get the complete organizational hierarchy.

**Parameters:** None

### 5. get_executive_teams
Get all teams managed by a specific executive.

**Parameters:**
- `executive_role`: Executive role name

### 6. update_team_relationship
Update reporting relationships between teams.

**Parameters:**
- `child_team`: Team that reports
- `parent_entity`: Entity being reported to
- `entity_type`: "team" or "executive"
- `relationship_type`: "reports_to" or "collaborates_with"

### 7. get_team_members
Get all members of a specific team.

**Parameters:**
- `team_name`: Name of the team

### 8. get_team_composition
Get summary of all teams' composition.

**Parameters:** None

## Integration with AgentGateway

To use this MCP with AgentGateway, add the following to your AgentGateway config:

```json
{
  "mcps": [
    {
      "name": "team-registry",
      "command": "npm",
      "args": ["run", "start:team-registry"],
      "workingDirectory": "/path/to/mcp-servers-ts",
      "environment": {
        "SUPABASE_URL": "${SUPABASE_URL}",
        "SUPABASE_ANON_KEY": "${SUPABASE_ANON_KEY}"
      }
    }
  ]
}
```

## Usage Example

```typescript
// Query all marketing teams
const marketingTeams = await mcp.call('team-registry', 'query_teams', {
  department: 'marketing'
});

// Register a new team
const newTeam = await mcp.call('team-registry', 'register_team', {
  name: 'social-media-team',
  display_name: 'Social Media Team',
  department: 'marketing',
  placement: 'marketing.social',
  purpose: 'Manage social media presence and engagement',
  framework: 'CrewAI',
  llm_provider: 'Anthropic',
  llm_model: 'claude-3-haiku-20240307',
  reports_to: 'Chief Marketing Officer'
});
```

## Security Notes

- This MCP requires valid Supabase credentials
- All database operations go through Supabase RLS (Row Level Security)
- Teams should only be created through the team-factory tool to maintain integrity
