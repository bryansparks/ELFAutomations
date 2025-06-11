# Missing Capability #005: Unclear MCP Module Structure

## The Problem
Cannot import MCP servers as Python modules. The MCP structure isn't clear:
- Are they TypeScript or Python?
- How do teams import and use them?
- What's the proper import path?

## Current State
- MCPs exist in `/mcp-servers-ts/` (TypeScript)
- Also `/mcp_servers/` (Python)
- Import paths are unclear
- Teams can't easily use MCPs

## Desired State
Clear, consistent MCP architecture:
1. MCPs accessible to all teams
2. Standardized client libraries
3. Clear import patterns
4. Language-agnostic interface

## How Teams Should Use MCPs

### Current (Unclear)
```python
# In a team agent
from ??? import SupabaseMCP  # Where is this?
mcp = SupabaseMCP()
result = mcp.query("SELECT * FROM teams")
```

### Desired (Clear)
```python
# In any team agent
from elf_automations.mcp import get_mcp_client

# MCPs accessed through gateway
supabase = get_mcp_client('supabase')
result = await supabase.execute_sql("SELECT * FROM teams")
```

## The Realization
MCPs should be accessed through AgentGateway, not imported directly! Teams shouldn't need to know if an MCP is TypeScript or Python.

## Proposed Architecture
1. All MCPs register with AgentGateway
2. Teams get MCP clients from a standard library
3. Communication via JSON-RPC through gateway
4. Language-agnostic for both MCPs and teams

## What This Means
We've been thinking about MCPs wrong. They're not libraries to import, they're services to call through the gateway!

This explains why setup scripts fail - they're trying to import MCPs directly instead of calling them through the proper architecture.
