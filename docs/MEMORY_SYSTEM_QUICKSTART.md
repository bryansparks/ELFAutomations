# Memory & Learning System Quick Start Guide

## Overview
The Memory & Learning System enables ElfAutomations teams to store, retrieve, and learn from experiences using Qdrant vector database and Supabase metadata storage.

## Phase 1 Complete: Infrastructure Setup ✅

### What's Been Created

1. **Qdrant Kubernetes Deployment** (`/k8s/data-stores/qdrant/`)
   - Deployment with persistent storage
   - Service for internal access
   - Resource limits and health checks
   - Ready for production use

2. **Supabase Schema** (`/sql/create_memory_system_tables.sql`)
   - `memory_entries` - Core memory metadata
   - `memory_collections` - Organize memories by purpose
   - `learning_patterns` - Extracted insights and patterns
   - `memory_relationships` - Connect related memories
   - `team_knowledge_profiles` - Team expertise tracking
   - `memory_access_logs` - Usage analytics

3. **Setup Automation** (`/scripts/setup_memory_system.py`)
   - One-command deployment
   - Automatic schema creation
   - Setup verification
   - Next steps guidance

4. **Testing Tools** (`/scripts/test_qdrant_connection.py`)
   - Verify Qdrant connectivity
   - Test vector operations
   - Example memory storage/retrieval

## Deployment Instructions

### Prerequisites
- GitOps with ArgoCD monitoring the repo
- K3s cluster on target machine (Mac Mini)
- Supabase project with credentials
- Python environment with requirements

### Step 1: Install Dependencies
```bash
pip install qdrant-client
```

### Step 2: Run GitOps Setup
```bash
# For GitOps deployment (recommended)
./scripts/setup_memory_gitops.sh

# OR manually:
# 1. Create Supabase schema only
python scripts/setup_memory_system.py --skip-k8s

# 2. Commit Qdrant manifests for ArgoCD
git add k8s/data-stores/qdrant/
git commit -m "feat: Add Qdrant vector database"
git push
```

### Step 3: Verify Deployment on K3s
```bash
# SSH to K3s machine
ssh bryan@192.168.6.5

# Check Qdrant deployment
kubectl get pods -n elf-automations -l app=qdrant
kubectl get svc -n elf-automations qdrant
```

### Step 4: Test Qdrant Connection
```bash
# Create SSH tunnel from dev machine to K3s
ssh -L 6333:localhost:6333 bryan@192.168.6.5 \
  'kubectl port-forward -n elf-automations svc/qdrant 6333:6333'

# In another terminal, test connection
python scripts/test_qdrant_connection.py
```

### Step 5: Access Qdrant Dashboard
Visit http://localhost:6333/dashboard while SSH tunnel is active

## Architecture Recap

```
Teams → Memory Tools → Memory MCP → { Qdrant (vectors) + Supabase (metadata) }
                                    ↓
                              RAG Team (free agent)
```

## What's Next

### Phase 2: Memory & Learning MCP Server
Location: `/mcp-servers-ts/src/memory-learning/`

Key tools to implement:
- `store_memory` - Save experiences with embeddings
- `retrieve_memories` - Semantic search for relevant memories
- `analyze_outcome` - Learn from successes/failures
- `find_similar_experiences` - Pattern matching

### Phase 3: RAG Free-Agent Team
Create with team factory:
```bash
python tools/team_factory.py
# Name: "RAG Team"
# Type: "knowledge"
# Department: "free-agent"
# Framework: CrewAI
```

Agents:
- Knowledge Researcher - Finds relevant information
- Memory Curator - Maintains knowledge quality
- Insight Generator - Discovers patterns

### Phase 4: Integration Tools
Add to all teams:
- `StoreMemoryTool` - Record important interactions
- `RetrieveMemoryTool` - Access past experiences
- `LearnFromOutcomeTool` - Track what works

## Key Concepts

### Memory Types
- **Interaction**: Team communications and decisions
- **Decision**: Choices made and their rationale
- **Learning**: Outcomes and insights
- **Experience**: Full scenarios with context
- **Insight**: Discovered patterns

### Learning Patterns
- **Success**: What worked and why
- **Failure**: What didn't work and lessons
- **Optimization**: Improvements discovered
- **Warning**: Risks to avoid
- **Insight**: Novel discoveries

### Memory Lifecycle
1. **Capture**: Store experience with context
2. **Embed**: Create vector representation
3. **Index**: Store in Qdrant with metadata
4. **Retrieve**: Semantic search when needed
5. **Learn**: Extract patterns from outcomes
6. **Share**: Make available to other teams

## Troubleshooting

### Qdrant Not Starting
```bash
# Check pod status
kubectl get pods -n elf-automations -l app=qdrant

# Check logs
kubectl logs -n elf-automations -l app=qdrant

# Check PVC
kubectl get pvc -n elf-automations
```

### Supabase Connection Issues
- Verify SUPABASE_URL and SUPABASE_DB_PASSWORD env vars
- Check if tables were created in Supabase dashboard
- Ensure database is accessible from your network

### Port Forwarding Issues
- Kill existing port-forward: `pkill -f "port-forward.*6333"`
- Try different local port: `kubectl port-forward -n elf-automations svc/qdrant 6334:6333`

## Resources
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Vector Embeddings Guide](https://qdrant.tech/documentation/concepts/vectors/)
- [Supabase pgvector](https://supabase.com/docs/guides/database/extensions/pgvector) (alternative approach)

## Summary
Phase 1 infrastructure is complete! Qdrant is ready for vector storage, Supabase schema is created for metadata, and test scripts verify everything works. Next step is building the Memory & Learning MCP server to give teams memory capabilities.