# Architecture Clarification #001: AgentGateway MCP Integration

## Current Understanding
- AgentGateway is already implemented and running
- It authorizes and manages MCP access
- Domain: agentgateway.dev
- Teams should communicate with MCPs through AgentGateway

## The Gap
- Teams don't have a client library to talk to MCPs via AgentGateway
- This blocks teams from using any MCP functionality
- Current scripts try to import MCPs directly (architectural violation)

## Correct Architecture
```
Team Agent → MCP Client Library → AgentGateway → MCP Server
                    ↑
                [MISSING]
```

## Temporary Workaround
For now, proceed without MCPs:
- Use direct database connections where needed
- Teams will handle their own integrations
- Track where MCP usage would be beneficial

## Future Implementation
When building the MCP client library:
1. Standard client for all teams
2. Routes all calls through agentgateway.dev
3. Handles authentication/authorization
4. Provides typed interfaces for each MCP
5. Both sync and async support

## Impact on Current Work
- Can't use Supabase MCP for team registry
- Teams will need direct credentials (temporary)
- Manual setup required for now
- But we can continue building teams!

## Note for Future
Every time we do something manually that should use an MCP, we're identifying where the system needs automation. This is valuable discovery!
