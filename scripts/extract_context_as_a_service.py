#!/usr/bin/env python3
"""
Extract Context-as-a-Service components from ElfAutomations.

This script copies all necessary components to create a standalone
Context-as-a-Service system that can be used independently.
"""

import argparse
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ContextServiceExtractor:
    """Extract and reorganize Context-as-a-Service components."""

    def __init__(self, source_dir: Path, target_dir: Path):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.components_to_extract = self._define_components()

    def _define_components(self) -> Dict[str, Dict]:
        """Define all components to extract with their mappings."""
        return {
            # RAG Processing Components
            "rag_processor": {
                "source": "src/teams/teams/rag-processor-team",
                "target": "core/rag_processor",
                "description": "RAG processing team with all agents",
                "files_to_exclude": ["k8s/", "Dockerfile", "build.sh"],
                "transformations": {
                    "remove_team_structure": True,
                    "simplify_imports": True,
                },
            },
            # AgentGateway
            "agentgateway": {
                "source": "third-party/agentgateway",
                "target": "infrastructure/agentgateway",
                "description": "AgentGateway for MCP management",
                "files_to_include": ["crates/", "Dockerfile", "Makefile", "README.md"],
            },
            # AgentGateway K8s configs
            "agentgateway_k8s": {
                "source": "infrastructure/k8s/k8s/base/agentgateway",
                "target": "infrastructure/k8s/agentgateway",
                "description": "AgentGateway Kubernetes configurations",
            },
            # MCP Server Factory
            "mcp_factory": {
                "source": "tools/mcp_server_factory.py",
                "target": "tools/mcp_server_factory.py",
                "description": "MCP server creation factory",
                "is_file": True,
            },
            # MCP Base Templates
            "mcp_templates": {
                "source": "src/mcps",
                "target": "mcp-servers/templates",
                "description": "MCP server templates",
                "files_to_include": ["shared/", "base-server.ts"],
            },
            # Google Drive Watcher
            "drive_watcher": {
                "source": "src/mcps/google-drive-watcher",
                "target": "mcp-servers/google-drive-watcher",
                "description": "Google Drive document watcher MCP",
                "files_to_exclude": ["node_modules/", "dist/"],
            },
            # Database Schemas
            "rag_schemas": {
                "source": "database/schemas/create_rag_system_tables.sql",
                "target": "database/schemas/01_rag_system_tables.sql",
                "description": "RAG system database schema",
                "is_file": True,
            },
            "rag_extraction_schemas": {
                "source": "database/schemas/create_rag_extraction_tables.sql",
                "target": "database/schemas/02_rag_extraction_tables.sql",
                "description": "RAG extraction database schema",
                "is_file": True,
            },
            "mcp_registry_schema": {
                "source": "database/schemas/create_mcp_registry.sql",
                "target": "database/schemas/03_mcp_registry.sql",
                "description": "MCP registry schema",
                "is_file": True,
            },
            # Shared Utilities - RAG specific
            "rag_utils": {
                "source": "src/elf_automations/elf_automations/shared/rag",
                "target": "shared/rag",
                "description": "RAG-specific utilities",
            },
            # Shared Utilities - Storage
            "storage_utils": {
                "source": "src/elf_automations/elf_automations/shared/storage",
                "target": "shared/storage",
                "description": "Storage utilities (MinIO, etc.)",
            },
            # Shared Utilities - MCP
            "mcp_utils": {
                "source": "src/elf_automations/elf_automations/shared/mcp",
                "target": "shared/mcp",
                "description": "MCP client and discovery utilities",
            },
            # Shared Utilities - Config
            "config_utils": {
                "source": "src/elf_automations/elf_automations/shared/config.py",
                "target": "shared/config.py",
                "description": "Configuration management",
                "is_file": True,
            },
            # Shared Utilities - LLM (for embeddings)
            "llm_utils": {
                "source": "src/elf_automations/elf_automations/shared/utils/llm_factory.py",
                "target": "shared/utils/llm_factory.py",
                "description": "LLM factory for embeddings",
                "is_file": True,
            },
        }

    def extract(self):
        """Execute the extraction process."""
        logger.info(f"Starting Context-as-a-Service extraction")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Target: {self.target_dir}")

        # Create target directory
        self.target_dir.mkdir(parents=True, exist_ok=True)

        # Extract each component
        for component_name, config in self.components_to_extract.items():
            logger.info(f"\nExtracting {component_name}: {config['description']}")
            self._extract_component(component_name, config)

        # Create additional structure
        self._create_project_structure()

        # Generate configuration files
        self._generate_configs()

        # Create documentation
        self._create_documentation()

        logger.info("\n✅ Extraction complete!")
        logger.info(f"Context-as-a-Service project created at: {self.target_dir}")

    def _extract_component(self, name: str, config: Dict):
        """Extract a single component."""
        source = self.source_dir / config["source"]
        target = self.target_dir / config["target"]

        if not source.exists():
            logger.warning(f"Source not found: {source}")
            return

        # Create target directory
        target.parent.mkdir(parents=True, exist_ok=True)

        if config.get("is_file", False):
            # Copy single file
            shutil.copy2(source, target)
            logger.info(f"  Copied file: {config['source']} -> {config['target']}")
        else:
            # Copy directory
            if target.exists():
                shutil.rmtree(target)

            # Apply filters if specified
            if "files_to_include" in config:
                # Copy only specified files/dirs
                target.mkdir(parents=True, exist_ok=True)
                for item in config["files_to_include"]:
                    src_item = source / item
                    if src_item.exists():
                        if src_item.is_file():
                            shutil.copy2(src_item, target / item)
                        else:
                            shutil.copytree(src_item, target / item)
            else:
                # Copy entire directory
                shutil.copytree(
                    source,
                    target,
                    ignore=self._get_ignore_function(
                        config.get("files_to_exclude", [])
                    ),
                )

            logger.info(f"  Copied directory: {config['source']} -> {config['target']}")

        # Apply transformations if needed
        if config.get("transformations"):
            self._apply_transformations(target, config["transformations"])

    def _get_ignore_function(self, excludes: List[str]):
        """Create ignore function for shutil.copytree."""

        def ignore_func(dir, files):
            ignored = set()
            for pattern in excludes:
                if pattern.endswith("/"):
                    # Directory pattern
                    ignored.update(f for f in files if f == pattern[:-1])
                else:
                    # File pattern
                    ignored.update(f for f in files if f == pattern)
            return ignored

        return ignore_func

    def _apply_transformations(self, target: Path, transformations: Dict):
        """Apply code transformations to extracted components."""
        if transformations.get("remove_team_structure"):
            # Transform RAG team agents to standalone processors
            self._transform_rag_agents(target)

        if transformations.get("simplify_imports"):
            # Update imports to remove ElfAutomations dependencies
            self._simplify_imports(target)

    def _transform_rag_agents(self, target: Path):
        """Transform RAG team agents to standalone processors."""
        agents_dir = target / "agents"
        if not agents_dir.exists():
            return

        # Rename agents directory to processors
        processors_dir = target / "processors"
        agents_dir.rename(processors_dir)

        # Update agent files to remove CrewAI dependencies
        for agent_file in processors_dir.glob("*.py"):
            if agent_file.name == "__init__.py":
                continue

            content = agent_file.read_text()
            # Remove CrewAI imports and base classes
            content = content.replace("from crewai import Agent", "")
            content = content.replace(
                "from ..config import", "from context_service.config import"
            )
            content = content.replace("class ", "class RAG")  # Prefix classes

            agent_file.write_text(content)

    def _simplify_imports(self, target: Path):
        """Simplify imports to remove ElfAutomations dependencies."""
        for py_file in target.rglob("*.py"):
            content = py_file.read_text()

            # Update imports
            content = content.replace("from elf_automations.shared.", "from shared.")
            content = content.replace("from elf_automations.", "from context_service.")
            content = content.replace(
                "import elf_automations", "import context_service"
            )

            py_file.write_text(content)

    def _create_project_structure(self):
        """Create additional project structure."""
        directories = [
            "api",
            "api/endpoints",
            "api/models",
            "clients/python",
            "clients/typescript",
            "deployment/docker",
            "deployment/k8s",
            "deployment/helm/context-service",
            "docs",
            "examples",
            "scripts",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
        ]

        for dir_path in directories:
            (self.target_dir / dir_path).mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        for dir_path in [
            "api",
            "api/endpoints",
            "api/models",
            "clients/python",
            "core",
        ]:
            init_file = self.target_dir / dir_path / "__init__.py"
            init_file.touch()

        # Copy template files
        self._copy_templates()

    def _copy_templates(self):
        """Copy template files if they exist."""
        templates_dir = Path(__file__).parent / "templates"

        # Copy API main template
        api_template = templates_dir / "context_api_main.py"
        if api_template.exists():
            shutil.copy2(api_template, self.target_dir / "api" / "main.py")
            logger.info("  Copied API main template")

        # Copy base context MCP template
        mcp_template = templates_dir / "base_context_mcp.ts"
        if mcp_template.exists():
            mcp_target = (
                self.target_dir / "mcp-servers" / "shared" / "base-context-mcp.ts"
            )
            mcp_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(mcp_template, mcp_target)
            logger.info("  Copied base context MCP template")

        # Copy Dockerfile for API
        dockerfile_api = templates_dir / "dockerfile_api"
        if dockerfile_api.exists():
            docker_target = self.target_dir / "deployment" / "docker" / "Dockerfile.api"
            docker_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dockerfile_api, docker_target)
            logger.info("  Copied Dockerfile for API")

        # Copy docker-compose template
        compose_template = templates_dir / "docker_compose.yml"
        if compose_template.exists():
            shutil.copy2(compose_template, self.target_dir / "docker-compose.yml")
            logger.info("  Copied docker-compose.yml template")

        # Copy database initialization script
        init_db_script = templates_dir / "init_database.py"
        if init_db_script.exists():
            scripts_dir = self.target_dir / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(init_db_script, scripts_dir / "init_database.py")
            logger.info("  Copied database initialization script")

    def _generate_configs(self):
        """Generate configuration files."""
        # Skip docker-compose if template was copied
        if not (self.target_dir / "docker-compose.yml").exists():
            # Generate basic docker-compose
            docker_compose = {
                "version": "3.8",
                "services": {
                    "context-api": {
                        "build": {
                            "context": ".",
                            "dockerfile": "deployment/docker/Dockerfile.api",
                        },
                        "ports": ["8080:8080"],
                        "environment": [
                            "SUPABASE_URL=${SUPABASE_URL}",
                            "SUPABASE_KEY=${SUPABASE_KEY}",
                            "QDRANT_URL=http://qdrant:6333",
                            "AGENTGATEWAY_URL=http://agentgateway:8081",
                        ],
                        "depends_on": ["qdrant", "agentgateway"],
                    },
                    "agentgateway": {
                        "build": "./infrastructure/agentgateway",
                        "ports": ["8081:8081"],
                        "environment": ["RUST_LOG=info"],
                    },
                    "qdrant": {
                        "image": "qdrant/qdrant:latest",
                        "ports": ["6333:6333"],
                        "volumes": ["qdrant_data:/qdrant/storage"],
                    },
                },
                "volumes": {"qdrant_data": {}},
            }

            with open(self.target_dir / "docker-compose.yml", "w") as f:
                yaml.dump(docker_compose, f, default_flow_style=False)

        # Requirements.txt
        requirements = """# Core dependencies
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# Database
supabase==2.0.3
asyncpg==0.29.0
sqlalchemy==2.0.23

# Vector storage
qdrant-client==1.7.0

# LLM and embeddings
openai==1.6.1
anthropic==0.8.1
langchain==0.0.350
sentence-transformers==2.2.2

# Utilities
python-dotenv==1.0.0
httpx==0.25.2
tenacity==8.2.3
structlog==23.2.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
"""

        (self.target_dir / "requirements.txt").write_text(requirements)

        # Package.json for MCP servers
        package_json = {
            "name": "context-mcp-servers",
            "version": "1.0.0",
            "description": "MCP servers for Context-as-a-Service",
            "scripts": {"build": "tsc", "dev": "tsx watch src/server.ts"},
            "dependencies": {
                "@modelcontextprotocol/sdk": "^0.6.0",
                "googleapis": "^128.0.0",
                "zod": "^3.22.0",
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "typescript": "^5.0.0",
                "tsx": "^4.0.0",
            },
        }

        (self.target_dir / "mcp-servers" / "package.json").write_text(
            json.dumps(package_json, indent=2)
        )

        # .env.example
        env_example = """# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional-api-key

# LLM Configuration
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Google Drive (for document watcher)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# AgentGateway
AGENTGATEWAY_URL=http://localhost:8081

# API Configuration
API_PORT=8080
API_HOST=0.0.0.0
LOG_LEVEL=info
"""

        (self.target_dir / ".env.example").write_text(env_example)

        # .gitignore
        gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.env

# Node
node_modules/
dist/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build
build/
*.egg-info/
.coverage
htmlcov/

# Docker
.dockerignore
"""

        (self.target_dir / ".gitignore").write_text(gitignore)

    def _create_documentation(self):
        """Create comprehensive documentation."""
        # README.md
        readme = """# Context-as-a-Service

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
   python tools/mcp_server_factory.py \\
     --name "my-context" \\
     --type context \\
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
"""

        (self.target_dir / "README.md").write_text(readme)

        # Getting Started Guide
        getting_started = """# Getting Started with Context-as-a-Service

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 18+
- Supabase account
- (Optional) Qdrant Cloud account

## Installation

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo>
cd context-as-a-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies for MCP servers
cd mcp-servers
npm install
cd ..
```

### 2. Configure Services

Edit `.env` file with your credentials:
- Supabase URL and keys
- OpenAI/Anthropic API keys
- Google OAuth credentials (for Drive watcher)

### 3. Database Setup

```sql
-- Run the SQL scripts in order:
psql $DATABASE_URL -f database/schemas/01_rag_system_tables.sql
psql $DATABASE_URL -f database/schemas/02_rag_extraction_tables.sql
psql $DATABASE_URL -f database/schemas/03_mcp_registry.sql
```

### 4. Start Services

```bash
# Start all services
docker-compose up

# Or start individually:
docker-compose up agentgateway
docker-compose up qdrant
docker-compose up context-api
```

## Using with AI IDEs

### Claude Code Configuration

Add to your MCP settings:
```json
{
  "mcpServers": {
    "context-service": {
      "command": "node",
      "args": ["http://localhost:8081/mcp/context-service"]
    }
  }
}
```

### Available Context Tools

- `search_context`: Search across all indexed documents
- `get_component_spec`: Get specifications for UI components
- `validate_implementation`: Validate code against standards
- `get_architecture_pattern`: Retrieve architectural patterns

## Next Steps

1. Index your documentation
2. Create domain-specific MCPs
3. Configure AI IDEs
4. Start building with context!
"""

        (self.target_dir / "docs" / "getting-started.md").write_text(getting_started)

        # API Reference
        api_reference = """# API Reference

## Base URL
`http://localhost:8080/api/v1`

## Authentication
All API requests require an API key in the header:
```
X-API-Key: your-api-key
```

## Endpoints

### Document Ingestion

#### POST /ingest/document
Ingest a single document for processing.

**Request Body:**
```json
{
  "content": "Document content...",
  "metadata": {
    "title": "Document Title",
    "source": "google-drive",
    "tags": ["tag1", "tag2"]
  }
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "status": "processing",
  "chunks_created": 15
}
```

### Context Retrieval

#### POST /search
Search for relevant context.

**Request Body:**
```json
{
  "query": "How do I implement authentication?",
  "collection": "documentation",
  "limit": 10,
  "filters": {
    "tags": ["auth", "security"]
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "Authentication implementation...",
      "score": 0.92,
      "metadata": {...}
    }
  ]
}
```

### MCP Management

#### GET /mcps
List all registered MCP servers.

#### POST /mcps/register
Register a new MCP server with AgentGateway.

**Request Body:**
```json
{
  "name": "my-context-mcp",
  "endpoint": "http://my-mcp:8080",
  "capabilities": ["search", "validate"]
}
```

## Error Responses

All errors follow this format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {...}
  }
}
```

## Rate Limits

- Document ingestion: 100 requests/hour
- Search queries: 1000 requests/hour
- MCP registration: 10 requests/hour
"""

        (self.target_dir / "docs" / "api-reference.md").write_text(api_reference)

        logger.info("📚 Documentation created")


def main():
    parser = argparse.ArgumentParser(
        description="Extract Context-as-a-Service components from ElfAutomations"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path.cwd(),
        help="Source directory (ElfAutomations root)",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd() / "context-as-a-service",
        help="Target directory for extracted project",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite target directory if it exists"
    )

    args = parser.parse_args()

    # Validate source directory
    if not (args.source / "CLAUDE.md").exists():
        logger.error(
            f"Source directory doesn't appear to be ElfAutomations root: {args.source}"
        )
        logger.error("Expected to find CLAUDE.md file")
        return 1

    # Check target directory
    if args.target.exists() and not args.force:
        logger.error(f"Target directory already exists: {args.target}")
        logger.error("Use --force to overwrite")
        return 1

    # Create extractor and run
    extractor = ContextServiceExtractor(args.source, args.target)
    extractor.extract()

    return 0


if __name__ == "__main__":
    exit(main())
