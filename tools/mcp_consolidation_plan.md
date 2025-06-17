# MCP Directory Consolidation Plan

## Current State
We have 3 different MCP directories:
1. `./mcp/` - Contains some internal/external structure with team-registry
2. `./mcp-servers-ts/` - Contains TypeScript MCP servers (business-tools, memory-learning, etc.)
3. `./mcp_servers/` - Contains Python base classes

## Target Structure
Single `./mcp/` directory with clear organization:

```
./mcp/
├── README.md              # Overview of MCP structure
├── typescript/            # TypeScript MCPs
│   ├── package.json      # Shared dependencies
│   ├── tsconfig.json     # Shared TypeScript config
│   ├── shared/           # Shared utilities
│   │   └── base-server.ts
│   └── servers/          # Individual MCP servers
│       ├── business-tools/
│       ├── memory-learning/
│       ├── project-management/
│       ├── supabase/
│       └── team-registry/
├── python/               # Python MCPs
│   ├── __init__.py
│   ├── base.py          # Base MCP class
│   └── servers/         # Individual servers
│       └── business_tools.py
├── external/            # External MCP integrations
│   ├── official/        # Official MCP servers
│   └── community/       # Community MCP servers
└── internal/            # Internal deployment artifacts
    └── manifests/       # K8s manifests, configs, etc.
```

## Migration Steps
1. Create new structure in `./mcp/`
2. Move TypeScript servers from `mcp-servers-ts/src/` to `mcp/typescript/servers/`
3. Move Python servers from `mcp_servers/` to `mcp/python/`
4. Update all imports and references
5. Remove old directories
6. Update mcp_factory.py to use new structure