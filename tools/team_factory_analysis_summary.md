# Team Factory Feature Analysis

## File Statistics
- Total Lines: 4,714
- Functions: 16
- Classes: 8

## Core Components

### Classes (8)
- TeamMember (line 58)
- SubTeamRecommendation (line 77)
- TeamSpecification (line 87)
- TeamFactory (line 109)
- MemoryAwareCrewAIAgent (line 1653)
- TeamState (line 3207)
- TaskState (line 3220)
- CommunicationState (line 3233)

### Key Functions (13)
- get_orchestrator() (line 2106)
- create_deployable_team() (line 2210)
- create_team_server() (line 2236)
- create_dockerfile() (line 2340)
- create_requirements() (line 2381)
- create_health_check() (line 2415)
- get_workflow() (line 3607)
- create_deployable_team() (line 3649)
- create_team_server() (line 3675)
- create_dockerfile() (line 3784)
- create_requirements() (line 3826)
- create_health_check() (line 3863)
- main() (line 4684)


### Generated Files (4)
- /logs
- add_{new_team_name}_{timestamp}.yaml
- {team_spec.name}.py
- {team_spec.name}_context.yaml


### Integrations (10)
- a2a
- docker
- kubernetes
- llm_providers
- logging
- mcp
- monitoring
- prometheus
- qdrant
- supabase

### UI Components (9)
- Confirm
- Confirm.ask
- Console
- Markdown
- Panel
- Prompt
- Prompt.ask
- Table
- console.w+

### Personality Traits (7)
- analyzer
- collaborator
- detail-oriented
- innovator
- optimist
- pragmatist
- skeptic

### LLM Configuration
- Providers: Anthropic, OpenAI
- Models: claude-3-haiku-20240307, claude-3-opus-20240229, claude-3-sonnet-20240229, gpt-3.5-turbo, gpt-4, gpt-4-turbo-preview
- Fallback System: Yes

### Department Mappings


### Validation Rules (6)
- directory_check
- framework_check
- manager_check
- name_validation
- skeptic_rule
- team_size

### Template Blocks (24)
- analysis_prompt (708 chars, line 470)
- a2a_imports (171 chars, line 1561)
- a2a_init (159 chars, line 1566)
- agent_content (7,017 chars, line 1588)
- crew_content (3,458 chars, line 1911)
- _orchestrator_instance (877 chars, line 2110)
- description (217 chars, line 2150)
- description (216 chars, line 2163)
- script_content (6,403 chars, line 2193)
- implementation (819 chars, line 2453)
... and 14 more

## Refactoring Considerations

1. **Large Templates**: 11 templates over 500 characters
2. **Complex Functions**: Identify functions that need breaking down
3. **External Dependencies**: 59 imports to manage
4. **File Generation Logic**: Extensive file creation patterns to preserve
