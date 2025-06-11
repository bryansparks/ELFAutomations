# Missing Capability #006: MCP Client Library for Teams

## The Problem
Teams have no standard way to communicate with MCPs. The architecture assumes AgentGateway handles this, but teams need a client library to make MCP calls through the gateway.

## Current State
- MCPs exist as TypeScript servers
- AgentGateway can route to MCPs
- But teams have no client library
- Scripts try to import MCPs directly (wrong!)

## Desired State
Every team should have access to:
```python
from elf_automations.mcp import MCPClient

class MyAgent:
    def __init__(self):
        self.mcp = MCPClient(via='agentgateway')

    async def check_registry(self):
        result = await self.mcp.call(
            server='supabase',
            tool='query_database',
            arguments={'query': 'SELECT * FROM teams'}
        )
        return result
```

## The Architecture Gap
```
Team Agent → [MISSING: MCP Client] → AgentGateway → MCP Server
```

We have:
- ✅ Team Agents (CrewAI/LangGraph)
- ❌ MCP Client Library
- ✅ AgentGateway
- ✅ MCP Servers

## Immediate Workaround
For now, teams could use HTTP calls to AgentGateway:
```python
import httpx

async def call_mcp(server, tool, args):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://agentgateway:8080/mcp/{server}/{tool}",
            json=args
        )
        return response.json()
```

## Proper Solution
Create `elf_automations.mcp` package that:
1. Handles AgentGateway communication
2. Provides type-safe tool interfaces
3. Manages authentication
4. Handles retries and errors
5. Supports both sync and async

## Priority
**CRITICAL** - Without this, teams can't use MCPs at all!

This is why setup scripts are failing - they're trying to import MCPs directly instead of going through the proper client → gateway → server architecture.
