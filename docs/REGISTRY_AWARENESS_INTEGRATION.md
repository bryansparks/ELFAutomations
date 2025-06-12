# Registry Awareness Integration Guide

This guide explains how to make ElfAutomations teams registry-aware, enabling dynamic discovery, collaboration, and organizational intelligence.

## Overview

Registry awareness transforms teams from isolated units into a cohesive AI organization by enabling:
- **Dynamic Discovery**: Teams find each other based on capabilities
- **Smart Delegation**: Managers identify the right teams for tasks
- **Organizational Intelligence**: Teams understand their place in the hierarchy
- **Capability Broadcasting**: Teams announce their skills and availability

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Team/Agent                            │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Registry Client │  │Registry Tools│  │ A2A Client    │  │
│  └────────┬────────┘  └──────┬───────┘  └───────┬───────┘  │
└───────────┼──────────────────┼──────────────────┼──────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌───────────────────────────────────────────────────────────┐
│                      MCP Client                            │
└────────────────────────────┬──────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│                    AgentGateway                            │
└────────────────────────────┬──────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│              Team Registry MCP Server                      │
└────────────────────────────┬──────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│                      Supabase                              │
└───────────────────────────────────────────────────────────┘
```

## Integration Patterns

### 1. Manager Agents (with A2A)

Manager agents need registry awareness to:
- Find teams for delegation
- Understand reporting structure
- Coordinate multi-team efforts

```python
# In team's manager agent (e.g., marketing_manager.py)
from elf_automations.shared.registry import TeamRegistryClient
from elf_automations.shared.tools.registry_tools import (
    FindTeamByCapabilityTool,
    GetTeamHierarchyTool,
    FindCollaboratorsTool
)

def marketing_manager():
    # Initialize registry client
    registry_client = TeamRegistryClient()

    return Agent(
        role="Marketing Manager",
        goal="Lead marketing initiatives and coordinate teams",
        tools=[
            # Registry tools for team discovery
            FindTeamByCapabilityTool(registry_client),
            GetTeamHierarchyTool(registry_client),
            FindCollaboratorsTool(registry_client),
            # ... other tools
        ],
        # ... rest of agent config
    )
```

### 2. Regular Team Members

Regular agents may need limited registry access:
- Find subject matter experts
- Understand team structure
- Update their capabilities

```python
# In team member agent
def content_writer():
    registry_client = TeamRegistryClient()

    return Agent(
        role="Content Writer",
        goal="Create compelling marketing content",
        tools=[
            # Basic registry tool for finding experts
            FindTeamByCapabilityTool(registry_client),
            # ... other tools
        ],
        # ... rest of agent config
    )
```

### 3. Executive Agents

Executives need comprehensive registry access:

```python
# In executive agent (e.g., chief_marketing_officer.py)
def chief_marketing_officer():
    registry_client = TeamRegistryClient()

    return Agent(
        role="Chief Marketing Officer",
        goal="Drive company-wide marketing strategy",
        tools=[
            # Full suite of registry tools
            FindTeamByCapabilityTool(registry_client),
            FindTeamByTypeTool(registry_client),
            GetTeamHierarchyTool(registry_client),
            FindCollaboratorsTool(registry_client),
            GetExecutiveTeamsTool(registry_client),
            # ... other tools
        ],
        # ... rest of agent config
    )
```

## Implementation Steps

### Step 1: Update Team Factory

Modify the team factory to generate registry-aware agents:

```python
# In tools/team_factory.py

def _generate_agent_file(agent_info, team_name, framework):
    """Generate agent file with registry awareness."""

    # Add registry imports based on role
    imports = [
        "from elf_automations.shared.registry import TeamRegistryClient",
    ]

    # Add registry tools for managers
    if agent_info.get('is_manager'):
        imports.append(
            "from elf_automations.shared.tools.registry_tools import ("
            "    FindTeamByCapabilityTool,"
            "    GetTeamHierarchyTool,"
            "    FindCollaboratorsTool"
            ")"
        )

    # ... rest of generation logic
```

### Step 2: Auto-Registration on Team Creation

Teams should register themselves when created:

```python
# In team factory's registration method
def _register_team_via_mcp(team_name, team_type, parent_team, agents):
    """Register team using MCP instead of direct Supabase."""

    mcp_client = MCPClient()
    registry_client = TeamRegistryClient(mcp_client)

    # Register team
    team = registry_client.register_team_sync(
        name=team_name,
        type=team_type,
        parent_name=parent_team,
        metadata={
            'created_by': 'team_factory',
            'framework': framework,
            'llm_provider': llm_provider
        }
    )

    # Register team members
    for agent in agents:
        # Extract capabilities from agent's tools and role
        capabilities = _extract_capabilities(agent)

        registry_client.add_team_member_sync(
            team_name=team_name,
            agent_name=agent['name'],
            role=agent['role'],
            capabilities=capabilities,
            is_manager=agent.get('is_manager', False)
        )
```

### Step 3: Runtime Registration

Teams can also register on startup:

```python
# In crew.py or workflow.py
class MarketingTeam:
    def __init__(self):
        self.registry_client = TeamRegistryClient()
        self._register_team()

    def _register_team(self):
        """Register team on startup if not already registered."""
        try:
            # Check if team exists
            hierarchy = self.registry_client.get_team_hierarchy_sync("marketing-team")
            if not hierarchy:
                # Register team
                self.registry_client.register_team_sync(
                    name="marketing-team",
                    type="marketing",
                    parent_name="executive-team"
                )

                # Register members
                for agent in self.agents:
                    self._register_agent(agent)

        except Exception as e:
            logger.warning(f"Could not register team: {e}")
```

## Usage Examples

### Example 1: Finding Teams for Delegation

```python
# Marketing manager needs design help
result = find_team_by_capability_tool.run("graphic_design")

# Output:
# Found 2 team(s) with capability 'graphic_design':
#
# Team: design-team (Type: creative)
#   Capabilities: graphic_design, ui_design, branding, illustration
#   Members with this capability:
#     - senior_designer (Senior Designer)
#     - graphic_artist (Graphic Artist)
#   Manager: design_manager
```

### Example 2: Understanding Organization

```python
# New team member explores hierarchy
result = get_team_hierarchy_tool.run("marketing-team")

# Output:
# Organizational Hierarchy for marketing-team:
#
# Team: marketing-team (Type: marketing)
#   Members: 5
#   Manager: marketing_manager
#
# Reports to: executive-team
#   Parent Manager: chief_marketing_officer
#
# Subordinate Teams (3):
#   - content-team (Type: content)
#     Manager: content_manager
#   - social-team (Type: social_media)
#     Manager: social_manager
#   - brand-team (Type: branding)
#     Manager: brand_manager
```

### Example 3: Multi-Team Collaboration

```python
# Product launch needs multiple capabilities
result = find_collaborators_tool.run(
    '["product_marketing", "content_creation", "social_media", "web_development"]'
)

# Output:
# Found 4 team(s) for collaboration:
#
# Team: marketing-team (Type: marketing)
#   Manager: marketing_manager
#   Provides capabilities:
#     - product_marketing
#     - content_creation
#
# Team: social-team (Type: social_media)
#   Manager: social_manager
#   Provides capabilities:
#     - social_media
#
# Team: engineering-team (Type: engineering)
#   Manager: engineering_manager
#   Provides capabilities:
#     - web_development
#
# Capability Coverage Summary:
#   ✓ product_marketing: marketing-team
#   ✓ content_creation: marketing-team
#   ✓ social_media: social-team
#   ✓ web_development: engineering-team
```

## Best Practices

### 1. Capability Naming

Use consistent capability names across teams:
- Use underscores: `web_development` not `web-development`
- Be specific: `react_development` not just `frontend`
- Group related: `marketing_strategy`, `marketing_analytics`

### 2. Registry Tool Usage

- **Managers**: Get full registry tool suite
- **Specialists**: Get capability search only
- **Executives**: Get all tools plus executive queries

### 3. Caching Strategy

The registry client includes caching:
- 5-minute TTL for capability searches
- Clear cache when team updates capabilities
- Use `registry_client.clear_cache()` when needed

### 4. Error Handling

Always handle registry unavailability:

```python
try:
    teams = registry_client.find_teams_by_capability_sync("marketing")
except Exception as e:
    logger.warning(f"Registry unavailable: {e}")
    # Fallback to hardcoded team knowledge
    teams = self._get_known_teams()
```

## Migration Plan

### Phase 1: Core Infrastructure
1. Deploy Team Registry MCP server
2. Create registry client and tools
3. Test with manual integration

### Phase 2: Team Factory Update
1. Update team factory to use registry
2. Generate registry-aware agents
3. Auto-registration on creation

### Phase 3: Existing Teams
1. Update executive team first
2. Migrate department heads
3. Update individual teams

### Phase 4: Advanced Features
1. Real-time capability updates
2. Team availability tracking
3. Performance metrics

## Troubleshooting

### Registry Not Found
```
Error: Team registry MCP server not found
```
Solution: Ensure team-registry MCP is deployed and registered with AgentGateway

### Capability Mismatch
```
No teams found with capability 'X'
```
Solution: Check capability naming consistency, use registry client to list all capabilities

### Performance Issues
```
Registry queries taking too long
```
Solution:
- Enable caching in registry client
- Check AgentGateway performance
- Consider local registry cache

## Future Enhancements

1. **Real-time Updates**: WebSocket support for live capability changes
2. **Team Metrics**: Track team utilization and performance
3. **Skill Matching**: AI-powered capability matching
4. **Cross-Organization**: Federation with other AI organizations
5. **Audit Trail**: Complete history of team interactions

## Conclusion

Registry awareness transforms ElfAutomations from a collection of teams into an intelligent, self-organizing AI company. Teams can discover expertise, delegate effectively, and collaborate seamlessly - just like a real organization.
