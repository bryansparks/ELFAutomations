"""Patches for integrating registry awareness into team factory.

This file contains the code snippets needed to update team_factory.py
to generate registry-aware agents and teams.
"""

# PATCH 1: Add registry imports to agent generation
REGISTRY_IMPORTS_PATCH = """
# Add to the imports section of _generate_agent_file()

    # Registry imports for team discovery
    if agent_info.get('is_manager') or 'executive' in agent_info.get('role', '').lower():
        imports.extend([
            "from elf_automations.shared.registry import TeamRegistryClient",
            "from elf_automations.shared.tools.registry_tools import (",
            "    FindTeamByCapabilityTool,",
            "    FindTeamByTypeTool,",
            "    GetTeamHierarchyTool,",
            "    FindCollaboratorsTool,",
            "    GetExecutiveTeamsTool,",
            "    UpdateTeamStatusTool",
            ")",
        ])
    elif any(keyword in agent_info.get('role', '').lower() for keyword in ['lead', 'senior', 'principal']):
        imports.extend([
            "from elf_automations.shared.registry import TeamRegistryClient",
            "from elf_automations.shared.tools.registry_tools import (",
            "    FindTeamByCapabilityTool,",
            "    FindCollaboratorsTool",
            ")",
        ])
"""

# PATCH 2: Add registry client initialization
REGISTRY_CLIENT_INIT = """
# Add to agent function generation, right after def {agent_name}():

    # Initialize registry client for team discovery
    registry_client = TeamRegistryClient()
"""

# PATCH 3: Add registry tools to agent tools list
REGISTRY_TOOLS_PATCH = """
# Add to tools list based on agent role

    # Registry tools for team discovery and coordination
    registry_tools = []

    if is_manager or 'executive' in role.lower():
        # Managers and executives get full registry access
        registry_tools = [
            FindTeamByCapabilityTool(registry_client),
            FindTeamByTypeTool(registry_client),
            GetTeamHierarchyTool(registry_client),
            FindCollaboratorsTool(registry_client),
            GetExecutiveTeamsTool(registry_client),
            UpdateTeamStatusTool(registry_client),
        ]
    elif any(keyword in role.lower() for keyword in ['lead', 'senior', 'principal']):
        # Senior members get basic discovery tools
        registry_tools = [
            FindTeamByCapabilityTool(registry_client),
            FindCollaboratorsTool(registry_client),
        ]
    else:
        # Regular members get capability search only
        registry_tools = [
            FindTeamByCapabilityTool(registry_client),
        ]

    # Add registry tools to the agent's tool list
    tools.extend(registry_tools)
"""

# PATCH 4: Update team registration to use MCP
REGISTRATION_VIA_MCP_PATCH = '''
def _register_team_in_registry(self, team_name: str, team_type: str,
                              parent_team: str, agents: List[Dict],
                              llm_provider: str, framework: str) -> bool:
    """Register team in registry via MCP instead of direct Supabase."""
    try:
        # Initialize MCP client for registry access
        from elf_automations.shared.mcp.client import MCPClient
        from elf_automations.shared.registry import TeamRegistryClient

        mcp_client = MCPClient()
        registry_client = TeamRegistryClient(mcp_client)

        # Register the team
        logger.info(f"Registering team {team_name} via MCP...")
        team = registry_client.register_team_sync(
            name=team_name,
            type=team_type,
            parent_name=parent_team,
            metadata={
                'created_by': 'team_factory',
                'framework': framework,
                'llm_provider': llm_provider,
                'created_at': datetime.utcnow().isoformat()
            }
        )

        if not team:
            logger.error(f"Failed to register team {team_name}")
            return False

        # Register team members
        for agent in agents:
            # Extract capabilities from agent
            capabilities = self._extract_agent_capabilities(agent)

            success = registry_client.add_team_member_sync(
                team_name=team_name,
                agent_name=agent['name'],
                role=agent['role'],
                capabilities=capabilities,
                is_manager=agent.get('is_manager', False)
            )

            if success:
                logger.info(f"Registered agent {agent['name']} in team {team_name}")
            else:
                logger.warning(f"Failed to register agent {agent['name']}")

        logger.info(f"Team {team_name} successfully registered in registry")
        return True

    except Exception as e:
        logger.error(f"Error registering team in registry: {e}")
        # Don't fail team creation if registry is unavailable
        return False

def _extract_agent_capabilities(self, agent: Dict) -> List[str]:
    """Extract capabilities from agent definition."""
    capabilities = []

    # Extract from role
    role = agent.get('role', '').lower()
    role_capabilities = {
        'marketing': ['marketing_strategy', 'campaign_planning'],
        'engineer': ['software_development', 'system_design'],
        'designer': ['graphic_design', 'ui_design'],
        'writer': ['content_creation', 'copywriting'],
        'analyst': ['data_analysis', 'reporting'],
        'manager': ['team_leadership', 'project_management'],
        'executive': ['strategic_planning', 'decision_making'],
    }

    for keyword, caps in role_capabilities.items():
        if keyword in role:
            capabilities.extend(caps)

    # Extract from goal
    goal = agent.get('goal', '').lower()
    if 'develop' in goal:
        capabilities.append('development')
    if 'design' in goal:
        capabilities.append('design')
    if 'analyze' in goal:
        capabilities.append('analysis')
    if 'coordinate' in goal:
        capabilities.append('coordination')

    # Extract from agent name
    name = agent.get('name', '').lower()
    if 'frontend' in name:
        capabilities.extend(['frontend_development', 'react_development'])
    if 'backend' in name:
        capabilities.extend(['backend_development', 'api_development'])
    if 'database' in name:
        capabilities.extend(['database_design', 'sql'])

    # Remove duplicates
    return list(set(capabilities))
'''

# PATCH 5: Add crew-level registry integration
CREW_REGISTRY_PATCH = '''
# Add to crew.py generation

    def __init__(self):
        """Initialize the crew with registry awareness."""
        self.agents = self._create_agents()
        self.tasks = self._create_tasks()

        # Initialize registry client
        from elf_automations.shared.registry import TeamRegistryClient
        self.registry_client = TeamRegistryClient()

        # Register team on startup
        self._register_team_if_needed()

    def _register_team_if_needed(self):
        """Register team in registry if not already registered."""
        try:
            # Check if team exists
            hierarchy = self.registry_client.get_team_hierarchy_sync("{team_name}")
            if hierarchy:
                logger.info(f"Team {team_name} already registered")
                return

            # Register team
            logger.info(f"Registering team {team_name} on startup...")
            team = self.registry_client.register_team_sync(
                name="{team_name}",
                type="{team_type}",
                parent_name="{parent_team}",
                metadata={{
                    'framework': '{framework}',
                    'llm_provider': '{llm_provider}',
                    'auto_registered': True
                }}
            )

            # Register agents
            for agent in self.agents:
                # Simple capability extraction
                capabilities = []
                if hasattr(agent, 'role'):
                    capabilities.append(agent.role.lower().replace(' ', '_'))
                if hasattr(agent, 'goal'):
                    if 'develop' in agent.goal.lower():
                        capabilities.append('development')
                    if 'design' in agent.goal.lower():
                        capabilities.append('design')

                self.registry_client.add_team_member_sync(
                    team_name="{team_name}",
                    agent_name=getattr(agent, 'name', 'unknown'),
                    role=getattr(agent, 'role', 'Team Member'),
                    capabilities=capabilities,
                    is_manager='manager' in getattr(agent, 'role', '').lower()
                )

            logger.info(f"Team {team_name} registered successfully")

        except Exception as e:
            logger.warning(f"Could not register team: {{e}}")
            # Don't fail initialization if registry is unavailable
'''


# Example of how to apply these patches
def apply_registry_patches():
    """Example of how to integrate these patches into team_factory.py"""

    print("To integrate registry awareness into team_factory.py:")
    print("\n1. Add registry imports to agent generation:")
    print(REGISTRY_IMPORTS_PATCH)

    print("\n2. Initialize registry client in agents:")
    print(REGISTRY_CLIENT_INIT)

    print("\n3. Add registry tools to agents:")
    print(REGISTRY_TOOLS_PATCH)

    print("\n4. Replace direct Supabase registration with MCP:")
    print(REGISTRATION_VIA_MCP_PATCH)

    print("\n5. Add crew-level registry integration:")
    print(CREW_REGISTRY_PATCH)

    print("\nThese patches enable:")
    print("- Agents to discover other teams by capability")
    print("- Managers to find teams for delegation")
    print("- Teams to auto-register on creation")
    print("- Organizational hierarchy awareness")
    print("- Dynamic collaboration across teams")


if __name__ == "__main__":
    apply_registry_patches()
