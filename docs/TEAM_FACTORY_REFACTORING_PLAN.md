# Team Factory Refactoring Plan

## Overview

The `team_factory.py` has grown to over 44,000 tokens (4,700+ lines), making it difficult to maintain and extend. This document outlines a plan to refactor it into a well-organized package structure.

## Current Issues

1. **Size**: Single file is too large for effective maintenance
2. **Mixed Concerns**: UI, business logic, generation, and integrations all in one file
3. **Testing Difficulty**: Hard to test specific components in isolation
4. **Extension Challenges**: Adding new frameworks or features requires modifying a massive file
5. **Code Navigation**: Finding specific functionality is time-consuming

## Proposed Package Structure

```
tools/
└── team_factory/
    ├── __init__.py                 # Package exports and version
    ├── cli.py                      # Command-line interface
    │
    ├── models/                     # Data models
    │   ├── __init__.py
    │   ├── team_member.py         # TeamMember dataclass
    │   ├── sub_team.py            # SubTeamRecommendation dataclass
    │   └── team_spec.py           # TeamSpecification dataclass
    │
    ├── core/                       # Core business logic
    │   ├── __init__.py
    │   ├── factory.py             # Main TeamFactory class
    │   ├── team_analyzer.py       # LLM-based team analysis
    │   ├── team_builder.py        # Team composition logic
    │   └── personality.py         # Personality trait management
    │
    ├── generators/                 # Code generation modules
    │   ├── __init__.py
    │   ├── base.py                # Base generator interface
    │   │
    │   ├── agents/                # Agent generation
    │   │   ├── __init__.py
    │   │   ├── crewai.py          # CrewAI agent generator
    │   │   └── langgraph.py       # LangGraph agent generator
    │   │
    │   ├── orchestrators/         # Orchestration generation
    │   │   ├── __init__.py
    │   │   ├── crew.py            # CrewAI crew.py generator
    │   │   └── workflow.py        # LangGraph workflow generator
    │   │
    │   ├── infrastructure/        # Infrastructure generation
    │   │   ├── __init__.py
    │   │   ├── kubernetes.py      # K8s manifests
    │   │   ├── docker.py          # Dockerfile generation
    │   │   ├── deployment.py      # Deployment scripts
    │   │   └── fastapi_server.py  # FastAPI server generation
    │   │
    │   ├── config/                # Configuration generation
    │   │   ├── __init__.py
    │   │   ├── a2a.py             # A2A configuration
    │   │   ├── team_config.py     # Team configuration
    │   │   └── llm_config.py      # LLM configuration
    │   │
    │   └── documentation/         # Documentation generation
    │       ├── __init__.py
    │       ├── readme.py          # README generator
    │       └── mermaid.py         # Diagram generator
    │
    ├── integrations/              # External system integrations
    │   ├── __init__.py
    │   ├── registry.py            # Supabase team registry
    │   ├── memory.py              # Memory system integration
    │   ├── prompt_system.py       # Enhanced prompt templates
    │   ├── mcp_optimizer.py       # MCP optimization
    │   └── executive_patch.py     # Executive team updates
    │
    ├── ui/                        # User interface components
    │   ├── __init__.py
    │   ├── console.py             # Rich console UI
    │   ├── prompts.py             # User interaction prompts
    │   ├── display.py             # Tables, panels, progress
    │   └── styles.py              # UI styling constants
    │
    ├── utils/                     # Utility functions
    │   ├── __init__.py
    │   ├── sanitizers.py          # Name/string sanitization
    │   ├── validators.py          # Input validation
    │   ├── constants.py           # Constants and mappings
    │   └── helpers.py             # General helper functions
    │
    └── templates/                 # File templates
        ├── __init__.py
        ├── base/                  # Framework-agnostic templates
        ├── crewai/                # CrewAI-specific templates
        └── langgraph/             # LangGraph-specific templates
```

## Refactoring Benefits

### 1. **Maintainability**
- Smaller, focused files (target: <500 lines each)
- Clear separation of concerns
- Easier to locate and modify specific functionality

### 2. **Testability**
- Unit test individual components
- Mock dependencies easily
- Test generators without side effects

### 3. **Extensibility**
- Add new frameworks by creating new generator modules
- Add integrations without touching core logic
- Plugin architecture for future enhancements

### 4. **Performance**
- Lazy loading of modules
- Only import what's needed
- Faster development iteration

### 5. **Collaboration**
- Multiple developers can work on different modules
- Reduced merge conflicts
- Clear ownership boundaries

## Migration Plan

### Phase 1: Setup (1 hour)
1. Create package directory structure
2. Move existing `team_factory.py` to `team_factory/legacy.py`
3. Create `__init__.py` files with proper exports

### Phase 2: Extract Models (2 hours)
1. Move dataclasses to `models/` directory
2. Update imports
3. Add type hints and validation

### Phase 3: Extract UI Components (2 hours)
1. Move Rich console code to `ui/console.py`
2. Extract user prompts to `ui/prompts.py`
3. Create reusable display components

### Phase 4: Extract Generators (4 hours)
1. Create base generator interface
2. Move CrewAI generation logic
3. Move LangGraph generation logic
4. Move infrastructure generation

### Phase 5: Extract Integrations (3 hours)
1. Move registry operations
2. Move memory system integration
3. Move MCP optimization
4. Create integration interfaces

### Phase 6: Refactor Core (3 hours)
1. Create main factory class
2. Extract team analysis logic
3. Extract team building logic
4. Wire everything together

### Phase 7: Testing & Documentation (2 hours)
1. Create comprehensive tests
2. Update documentation
3. Create migration guide for users

## Usage Examples

### Before (Current)
```python
python team_factory.py
```

### After (Refactored)
```python
# CLI usage (same as before)
python -m team_factory

# Programmatic usage
from team_factory import TeamFactory

factory = TeamFactory()
spec = factory.create_team_from_description(
    "I need a marketing team with 5 members",
    framework="CrewAI",
    llm_provider="OpenAI"
)
factory.generate_team(spec)

# Custom usage
from team_factory.generators.agents import CrewAIAgentGenerator
from team_factory.models import TeamMember

generator = CrewAIAgentGenerator()
agent_code = generator.generate(
    TeamMember(name="Marketing Manager", role="manager", ...)
)
```

## Backward Compatibility

To maintain compatibility:
1. Keep `team_factory.py` as a wrapper that imports from the package
2. Maintain same CLI interface
3. Document any breaking changes
4. Provide migration script if needed

## Testing Strategy

### Unit Tests
- Test each generator independently
- Test model validation
- Test utility functions

### Integration Tests
- Test full team generation flow
- Test registry integration
- Test memory system integration

### End-to-End Tests
- Test CLI interface
- Test generated team deployment
- Test inter-team communication

## Future Enhancements

Once refactored, we can easily add:
1. **Plugin System**: Load custom generators dynamically
2. **Template Customization**: Override default templates
3. **Web UI**: Flask/FastAPI interface
4. **Team Templates**: Pre-built team configurations
5. **Validation Rules**: Custom team validation logic

## Timeline

- **Total Estimated Time**: 17 hours
- **Approach**: Incremental (can use old and new simultaneously)
- **Risk**: Low (keeping original file as backup)

## Decision Points

1. Should we use abstract base classes or protocols for interfaces?
2. Should templates be in Python strings or separate files?
3. Should we add a configuration file format (YAML/JSON)?
4. Should we version the generated output?
5. Should we add a plugin system from the start?

## Conclusion

This refactoring will transform the team factory from a monolithic script into a professional, maintainable package that can grow with our needs. The modular structure will make it easier to add new features, fix bugs, and onboard new developers.
