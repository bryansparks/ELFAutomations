# Context-as-a-Service Extraction Script

This script extracts all necessary components from ElfAutomations to create a standalone Context-as-a-Service system.

## What Gets Extracted

1. **RAG Processing Components**
   - Complete RAG processor team (7 agents)
   - Document processing pipeline
   - Embedding generation
   - Smart chunking
   - Entity extraction

2. **MCP Infrastructure**
   - MCP server factory
   - Base context MCP templates
   - Google Drive watcher MCP
   - Example context MCPs

3. **AgentGateway**
   - Complete AgentGateway source (Rust)
   - Kubernetes configurations
   - MCP registration/discovery

4. **Database Schemas**
   - RAG system tables
   - RAG extraction tables
   - MCP registry schema

5. **Supporting Infrastructure**
   - FastAPI-based Context API
   - Docker configurations
   - Kubernetes manifests
   - Client libraries templates

## Usage

```bash
# From ElfAutomations root directory
python scripts/extract_context_as_a_service.py

# Or specify custom paths
python scripts/extract_context_as_a_service.py \
  --source /path/to/ElfAutomations \
  --target /path/to/new/context-service

# Force overwrite existing target
python scripts/extract_context_as_a_service.py --force
```

## After Extraction

The script creates a complete standalone project at `./context-as-a-service/` with:

```
context-as-a-service/
├── README.md                 # Complete documentation
├── docker-compose.yml        # Full stack deployment
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── api/                     # Context API server
│   └── main.py             # FastAPI application
├── core/                    # RAG processing engine
│   └── rag_processor/      # Extracted from team
├── mcp-servers/            # MCP implementations
│   ├── shared/             # Base MCP templates
│   └── google-drive-watcher/
├── infrastructure/         # AgentGateway & K8s
├── database/              # SQL schemas
├── deployment/            # Docker & K8s configs
├── scripts/               # Setup scripts
└── docs/                  # Documentation
```

## Quick Start After Extraction

1. **Setup Environment**
   ```bash
   cd context-as-a-service
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Initialize Database**
   ```bash
   python scripts/init_database.py
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Register MCP Servers**
   ```bash
   python scripts/register_mcps.py
   ```

## Key Differences from ElfAutomations

- **No Teams Structure**: RAG agents converted to standalone processors
- **No N8N Integration**: Pure MCP-based architecture
- **Simplified Imports**: All `elf_automations` imports updated
- **Independent Deployment**: No dependency on ElfAutomations infrastructure
- **Multi-tenant Ready**: Built for SaaS deployment from day one

## Customization

The extracted project is ready for customization:

1. **Add Domain MCPs**: Use the base templates to create domain-specific context servers
2. **Extend RAG Pipeline**: Add custom processors or enhance existing ones
3. **Scale Infrastructure**: Deploy to Kubernetes for production
4. **Add Authentication**: Integrate with your auth provider

## Integration with AI IDEs

Configure AI IDEs to use the Context-as-a-Service:

### Claude Code
```json
{
  "mcpServers": {
    "context-service": {
      "command": "node",
      "args": ["http://localhost:8081/mcp/ui-system"]
    }
  }
}
```

### Cursor/Windsurf
Similar MCP configuration pointing to your deployed service endpoints.

## Troubleshooting

- **Missing Components**: Check that you're running from ElfAutomations root
- **Permission Errors**: Ensure write permissions to target directory
- **Import Errors**: The script automatically updates imports, but check for edge cases

## Next Steps

1. Review the generated README.md in the extracted project
2. Set up your Supabase project and update credentials
3. Deploy and start using Context-as-a-Service!
