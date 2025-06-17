# Memory & Learning MCP Server

This MCP server provides organizational memory and learning capabilities for ElfAutomations teams.

## Features

- **Semantic Memory Storage**: Store experiences with vector embeddings
- **Intelligent Retrieval**: Find relevant memories using semantic search
- **Pattern Recognition**: Identify successful patterns and learn from failures
- **Team Insights**: Analytics and knowledge profiles per team
- **Knowledge Management**: Collections, retention policies, and export capabilities

## Development Setup

This MCP currently uses a mock Qdrant client for development. When Qdrant is deployed to the cluster, update the constructor to use the real client.

## Environment Variables

Required:
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service key for full access

Optional (for future):
- `QDRANT_URL`: Qdrant server URL (defaults to mock client)
- `QDRANT_API_KEY`: Qdrant API key
- `OPENAI_API_KEY`: For real embeddings (currently using mock)

## Tools

### Storage & Retrieval
- `store_memory`: Store experiences with embeddings
- `retrieve_memories`: Semantic search for memories
- `get_similar_experiences`: Find related past situations

### Learning & Analytics
- `find_successful_patterns`: Identify what works
- `analyze_outcome`: Learn from results
- `update_pattern_confidence`: Adjust pattern confidence
- `get_team_insights`: Team-specific analytics

### Management
- `create_collection`: Organize memory spaces
- `prune_old_memories`: Apply retention policies
- `export_knowledge_base`: Export in JSON/CSV/Markdown

## Usage Example

```typescript
// Store a memory
await store_memory({
  content: "Successfully deployed new feature using blue-green strategy",
  type: "learning",
  context: {
    team: "devops",
    deployment_type: "blue-green",
    downtime: 0,
    rollback_needed: false
  },
  importance_score: 0.9
});

// Find similar experiences
await get_similar_experiences({
  situation: "Need to deploy critical update with zero downtime",
  min_similarity: 0.7
});

// Analyze outcome
await analyze_outcome({
  action: "blue-green deployment",
  result: { success: true, metrics: {...} },
  context: { environment: "production" },
  success: true
});
```

## Testing

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build
```

## Integration with Teams

Teams can access this MCP through the AgentGateway. Add memory tools to agents:

```python
from elf_automations.shared.tools import MemoryTools

agent = Agent(
    tools=[
        MemoryTools.store_memory,
        MemoryTools.retrieve_memories,
        MemoryTools.find_patterns
    ]
)
```

## Mock vs Production

Currently using:
- **MockQdrantClient**: In-memory vector storage
- **Mock Embeddings**: Deterministic embeddings based on text

When ready for production:
1. Deploy Qdrant to K8s cluster
2. Update constructor to use real Qdrant client
3. Implement real embedding generation (OpenAI/local model)
4. Update environment variables

## Database Schema

See `/sql/create_memory_system_tables.sql` for the complete Supabase schema.