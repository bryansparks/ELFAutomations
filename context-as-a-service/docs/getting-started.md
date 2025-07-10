# Getting Started with Context-as-a-Service

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
source venv/bin/activate  # On Windows: venv\Scripts\activate

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
