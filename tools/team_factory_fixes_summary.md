# Team Factory Fixes Applied

## 1. Team Name Sanitization
- Added `sanitize_team_name()` method to ensure filesystem and Docker compatibility
- Converts to lowercase, replaces special chars with hyphens
- Truncates long names to 50 chars max at word boundaries
- Applied to all team name generation points

## 2. Import Path Fixes
- Added sys.path manipulation at top of generated files
- Fixed relative imports with try/except blocks for module vs direct execution
- Import agents as functions (e.g., `marketing_manager_agent`) not classes
- Added proper imports for elf_automations shared modules

## 3. Simplified Agent Generation
- Changed from class-based to function-based agents (matching product team pattern)
- Agents now return Agent instances directly
- Use LLMFactory for automatic OpenAI->Anthropic fallback
- Cleaner agent function naming (role.lower().replace(' ', '_') + '_agent')

## 4. Key Code Changes

### In team name generation:
```python
# Before
team_spec.name = f"{department}-{subteam}-team"

# After
team_spec.name = self.sanitize_team_name(f"{department}-{subteam}-team")
```

### In crew.py generation:
```python
# Added at top
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Fixed imports
try:
    from .agents import (agent_functions...)
except ImportError:
    from agents import (agent_functions...)
```

### In agent files:
```python
# Simplified to function pattern
def marketing_manager_agent(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None
) -> Agent:
    if not llm:
        llm = LLMFactory.create_llm(...)
    return Agent(...)
```

## Testing Required
1. Create a team with a long description
2. Verify team name is properly sanitized
3. Check that imports work in generated files
4. Test that agents use Anthropic when OpenAI quota exceeded
