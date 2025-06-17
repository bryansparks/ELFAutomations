# MCP (Model Context Protocol) Servers

This directory contains all MCP servers for the ElfAutomations platform.

## Directory Structure

### `/typescript/`
TypeScript-based MCP servers using the MCP SDK.

- **`/shared/`** - Shared utilities and base classes
- **`/servers/`** - Individual MCP server implementations
  - `business-tools/` - Business operations tools
  - `memory-learning/` - Organizational memory and learning system
  - `project-management/` - Project and task management
  - `supabase/` - Supabase database operations
  - `team-registry/` - Team registration and management

### `/python/`
Python-based MCP servers.

- **`base.py`** - Base MCP server class
- **`/servers/`** - Individual server implementations

### `/external/`
External MCP server integrations.

- **`/official/`** - Official MCP servers from Anthropic and partners
- **`/community/`** - Community-contributed MCP servers

### `/internal/`
Internal deployment and configuration artifacts.

- **`/manifests/`** - Kubernetes manifests and deployment configs

## Development

### TypeScript MCPs
```bash
cd typescript/servers/[server-name]
npm install
npm run dev
```

### Python MCPs
```bash
cd python/servers
python [server-name].py
```

## Creating New MCPs

Use the MCP factory tool:
```bash
python tools/mcp_factory.py
```

The factory will:
1. Determine if your MCP is simple or complex
2. Generate appropriate scaffolding
3. Place files in the correct location
4. Update necessary configurations