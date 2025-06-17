# Missing Capability #010: Team Module Import Structure

## The Problem
Teams can't import shared modules like A2A client because:
- Python path isn't set up correctly
- Teams are isolated in their own directories
- No clear import strategy for shared code

## Current State
- Teams try to import `agents.distributed.a2a.client`
- This fails because Python can't find the module
- Each team is in its own directory without access to shared code

## Desired State
Teams should be able to:
1. Import shared A2A client libraries
2. Import shared tools and utilities
3. Work both locally and in containers
4. Not duplicate code across teams

## Options

### Option 1: Package Structure
Create proper Python packages:
```
elf_automations/
  __init__.py
  shared/
    __init__.py
    a2a/
      client.py
  teams/
    product_team/
      ...
```

### Option 2: Environment Setup
Add PYTHONPATH in each team:
```python
import sys
sys.path.append('/path/to/elf_automations')
```

### Option 3: Shared Library Package
Create `elf-common` package that teams install:
```
pip install elf-common
from elf_common.a2a import A2AClient
```

## The Deeper Issue
Without proper module structure, teams can't:
- Share common code
- Use A2A communication
- Access shared MCPs
- Maintain consistency

## Priority
HIGH - Blocks team functionality
