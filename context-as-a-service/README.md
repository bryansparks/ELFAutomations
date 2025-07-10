# Context-as-a-Service

A standalone service providing contextual knowledge through MCP (Model Context Protocol) servers,
powered by RAG (Retrieval Augmented Generation) and integrated with AI IDEs like Claude Code,
Cursor, and Windsurf.

## Overview

Context-as-a-Service provides:
- 🔍 RAG-powered document processing and retrieval
- 🌐 MCP servers for seamless AI IDE integration
- 📁 Google Drive document watching and ingestion
- 🚀 AgentGateway for MCP management and routing
- 🗄️ Multi-tenant support with Supabase
- 🎯 Domain-specific context servers

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AI IDEs       │────▶│  AgentGateway    │────▶│  Context MCPs   │
│ (Claude, Cursor)│     │  (MCP Router)    │     │  (Domain MCPs)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                            │
                                                            ▼
                                                  ┌─────────────────┐
                                                  │   Context API   │
                                                  │  (FastAPI/RAG)  │
                                                  └─────────────────┘
                                                            │
                                    ┌───────────────────────┴───────────────────────┐
                                    ▼                                               ▼
                          ┌─────────────────┐                             ┌─────────────────┐
                          │     Qdrant      │                             │    Supabase     │
                          │ (Vector Store)  │                             │   (Metadata)    │
                          └─────────────────┘                             └─────────────────┘
```

## Quick Start

1. **Clone and setup**:
   ```bash
   cd context-as-a-service
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Initialize database**:
   ```bash
   python scripts/init_database.py
   ```

4. **Register MCP servers**:
   ```bash
   python scripts/register_mcps.py
   ```

## Components

### Core RAG Processing (`/core/rag_processor/`)
- Document classification and chunking
- Entity extraction and graph building
- Embedding generation and storage
- Multi-stage processing pipeline

### MCP Servers (`/mcp-servers/`)
- Base context MCP template
- Google Drive watcher
- Domain-specific context servers

### Infrastructure (`/infrastructure/`)
- AgentGateway for MCP routing
- Kubernetes manifests
- Docker configurations

### API (`/api/`)
- REST endpoints for document ingestion
- Context retrieval and search
- Admin and monitoring endpoints

## Creating Custom Context MCPs

1. **Use the MCP factory**:
   ```bash
   python tools/mcp_server_factory.py \
     --name "my-context" \
     --type context \
     --domain "my-domain"
   ```

2. **Implement domain logic**:
   ```typescript
   export class MyContextMCP extends BaseContextMCP {
     protected setupDomainHandlers() {
       this.addTool({
         name: "get_my_context",
         handler: async (args) => {
           return await this.queryRAG({
             query: args.query,
             collection: "my_domain_docs"
           });
         }
       });
     }
   }
   ```

3. **Register with AgentGateway**:
   ```python
   await gateway.register_mcp({
     "name": "my-context",
     "endpoint": "http://my-context-mcp:8080",
     "capabilities": ["get_my_context"]
   })
   ```

## Deployment

### Local Development
```bash
docker-compose up
```

### Kubernetes
```bash
kubectl apply -k deployment/k8s/
```

### Helm
```bash
helm install context-service deployment/helm/context-service
```

## API Reference

See [docs/api-reference.md](docs/api-reference.md) for complete API documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
