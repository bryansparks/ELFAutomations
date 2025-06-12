# Memory System Development Guide

## Overview
This guide addresses the development and testing of the Memory & Learning System when you don't have access to the full infrastructure (Qdrant on K3s, AgentGateway, etc.).

## The Architecture

```
Teams → Memory Tools → Memory MCP → { Qdrant (vectors) + Supabase (metadata) }
```

## Development Without Infrastructure

### 1. Supabase Setup Options

Since direct PostgreSQL connection is having issues, you have several options:

#### Option A: Supabase Dashboard (Recommended for Now)
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy the contents of `/sql/create_memory_system_tables.sql`
4. Run the SQL directly in the dashboard
5. Verify tables were created in Table Editor

#### Option B: Supabase CLI
```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Link to your project
supabase link --project-ref lcyzpqydoqpcsdltsuyq

# Run migrations
supabase db push sql/create_memory_system_tables.sql
```

#### Option C: Fix Direct Connection
The issue with our script is the database host format. Supabase database URLs follow this pattern:
```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres
```
Note: Port is 6543 (not 5432) for direct connections.

### 2. Qdrant Development Mock

Since Qdrant will be deployed on K3s later, here's a development mock:

```python
# elf_automations/shared/memory/mock_qdrant.py
"""Mock Qdrant client for development without Qdrant server."""

import json
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class MockPoint:
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    score: float = 1.0

class MockQdrantClient:
    """Mock Qdrant client that stores vectors in memory."""
    
    def __init__(self):
        self.collections = {}
        self.points = {}
    
    def create_collection(self, collection_name: str, vectors_config: Any):
        """Create a mock collection."""
        self.collections[collection_name] = {
            "config": vectors_config,
            "points": {}
        }
        print(f"[MOCK] Created collection: {collection_name}")
    
    def upsert(self, collection_name: str, points: List[Any]):
        """Insert mock points."""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        
        for point in points:
            self.collections[collection_name]["points"][point.id] = point
        
        print(f"[MOCK] Inserted {len(points)} points into {collection_name}")
    
    def search(self, collection_name: str, query_vector: List[float], limit: int = 5):
        """Mock similarity search - returns random results."""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        
        # Return mock results
        points = list(self.collections[collection_name]["points"].values())[:limit]
        
        # Add mock scores
        for i, point in enumerate(points):
            point.score = 1.0 - (i * 0.1)  # Decreasing scores
        
        print(f"[MOCK] Searched {collection_name}, returning {len(points)} results")
        return points
    
    def get_collections(self):
        """List mock collections."""
        return {"collections": [{"name": name} for name in self.collections.keys()]}
```

### 3. Development Workflow

#### Step 1: Create Tables in Supabase
Use the dashboard method above to create tables manually.

#### Step 2: Build Memory MCP with Mock
```typescript
// mcp-servers-ts/src/memory-learning/server.ts
import { MockQdrantClient } from './mock-qdrant';

const qdrantClient = process.env.USE_MOCK_QDRANT 
  ? new MockQdrantClient() 
  : new QdrantClient({
      url: process.env.QDRANT_URL || 'http://localhost:6333'
    });
```

#### Step 3: Test Locally
```bash
# Use mock Qdrant
export USE_MOCK_QDRANT=true

# Run Memory MCP server locally
cd mcp-servers-ts
npm run dev:memory-learning

# Test with MCP client
python scripts/test_memory_mcp.py
```

## Production Deployment

When you have access to the K3s cluster:

### 1. Deploy Qdrant
```bash
# Commit Qdrant manifests
git add k8s/data-stores/qdrant/
git commit -m "feat: Add Qdrant vector database"
git push

# ArgoCD will deploy automatically
```

### 2. Verify Deployment
```bash
# SSH to K3s machine
ssh bryan@192.168.6.5

# Check Qdrant
kubectl get pods -n elf-automations -l app=qdrant
kubectl logs -n elf-automations -l app=qdrant

# Port forward for testing
kubectl port-forward -n elf-automations svc/qdrant 6333:6333
```

### 3. Switch from Mock to Real
```bash
# Remove mock flag
unset USE_MOCK_QDRANT

# Set real Qdrant URL
export QDRANT_URL=http://qdrant.elf-automations:6333
```

## Key Patterns We've Learned

### 1. MCP Access Pattern
```python
# Always use our MCPClient, never external 'mcp' package
from elf_automations.shared.mcp import MCPClient

client = MCPClient()
result = await client.call("server-name", "tool-name", {args})
```

### 2. Supabase Table Creation
- **Development**: Use dashboard or CLI
- **Production**: Use migrations in CI/CD
- **Why**: Direct SQL execution through clients is limited

### 3. Development vs Production
- **Development**: Use mocks and local services
- **Production**: Real services via K8s/ArgoCD

## Common Issues and Solutions

### Issue: "No module named 'mcp'"
**Solution**: Use `elf_automations.shared.mcp.MCPClient`, not external packages

### Issue: Database connection fails
**Solution**: 
1. Check port (6543 for direct, 5432 for pooler)
2. Verify password is URL-encoded
3. Use Supabase dashboard for one-time setup

### Issue: Can't test without Qdrant
**Solution**: Use the mock client above

### Issue: AgentGateway not accessible
**Solution**: 
1. For MCP development, run servers directly
2. For testing, mock the MCP responses

## Summary

The Memory & Learning System can be developed without full infrastructure by:
1. Using Supabase dashboard for table creation
2. Mocking Qdrant for vector operations
3. Running MCP servers locally
4. Following established patterns (no external 'mcp' package)

This approach lets you build and test the system locally, then deploy to production via GitOps when ready.