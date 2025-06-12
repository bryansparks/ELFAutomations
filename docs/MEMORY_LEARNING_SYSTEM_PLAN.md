# Memory & Learning System Implementation Plan

## Overview
Build a persistent memory and learning system that enables teams to:
- Store and retrieve knowledge from past interactions
- Learn from successes and failures
- Share knowledge across teams
- Improve performance over time

## Architecture Options

### Option A: Supabase with pgvector
**Pros:**
- Single database for everything (operational simplicity)
- Tight integration with existing data
- Built-in auth and RLS
- No additional infrastructure
- Can JOIN vectors with relational data

**Cons:**
- Less optimized for vector operations
- Limited to PostgreSQL vector capabilities
- May hit performance limits at scale

### Option B: Dedicated Vector DB (Qdrant/Weaviate/Pinecone)
**Pros:**
- Purpose-built for vector operations
- Better performance for similarity search
- Advanced features (hybrid search, filtering)
- Scales independently from operational data

**Cons:**
- Another system to manage
- Data synchronization complexity
- Additional infrastructure costs

## Recommended Architecture: Hybrid Approach

Use **Qdrant** for vector operations with **Supabase** for metadata and operational data:

```
┌─────────────────────────────────────────────────────────┐
│                     Teams/Agents                         │
└────────────────────┬───────────────────┬────────────────┘
                     │                   │
                     ▼                   ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│   Memory/RAG Team       │   │    Memory Tools          │
│   (Free Agent)          │   │  (For all teams)         │
└───────────┬─────────────┘   └────────┬─────────────────┘
            │                           │
            ▼                           ▼
┌─────────────────────────────────────────────────────────┐
│                Memory & Learning MCP                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Ingestion  │  │   Retrieval  │  │   Learning   │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼────────────────┼──────────────────┼──────────┘
          │                │                  │
          ▼                ▼                  ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
│     Qdrant      │ │   Supabase   │ │  Analytics DB   │
│  (Vectors)      │ │  (Metadata)  │ │  (Patterns)     │
└─────────────────┘ └──────────────┘ └──────────────────┘
```

## Implementation Plan

### Phase 1: Infrastructure Setup (Week 1)

#### 1.1 Deploy Qdrant
```yaml
# k8s/data-stores/qdrant-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: elf-automations
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
```

#### 1.2 Create Supabase Schema
```sql
-- Memory metadata tables
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    entry_type VARCHAR(50), -- 'interaction', 'decision', 'learning'
    content TEXT,
    context JSONB,
    vector_id VARCHAR(255), -- Reference to Qdrant
    embedding_model VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE TABLE memory_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE,
    description TEXT,
    team_id UUID REFERENCES teams(id),
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50), -- 'success', 'failure', 'optimization'
    description TEXT,
    conditions JSONB,
    outcomes JSONB,
    frequency INTEGER DEFAULT 1,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 2: Memory & Learning MCP (Week 2)

#### 2.1 MCP Server Structure
```typescript
// mcp-servers-ts/src/memory-learning/server.ts
interface MemoryTools {
  // Storage
  'store_memory': (content, type, context) => MemoryEntry
  'store_team_learning': (team_id, pattern, outcome) => Learning

  // Retrieval
  'retrieve_memories': (query, filters?, top_k?) => Memory[]
  'get_similar_experiences': (situation, team_id?) => Experience[]
  'find_successful_patterns': (task_type) => Pattern[]

  // Learning
  'analyze_outcome': (action, result, context) => Analysis
  'update_pattern_confidence': (pattern_id, success) => void
  'get_team_insights': (team_id, timeframe?) => Insights

  // Management
  'create_collection': (name, description, config) => Collection
  'prune_old_memories': (retention_policy) => Stats
  'export_knowledge_base': (format) => Export
}
```

#### 2.2 Core Capabilities
1. **Semantic Memory Storage**
   - Embed all significant interactions
   - Store with rich metadata
   - Link to team/agent/task context

2. **Intelligent Retrieval**
   - Semantic similarity search
   - Hybrid search (keyword + vector)
   - Contextual filtering

3. **Pattern Recognition**
   - Track repeated successes/failures
   - Identify optimization opportunities
   - Build confidence scores

4. **Knowledge Sharing**
   - Cross-team knowledge access
   - Privacy controls (team-private vs shared)
   - Expertise location

### Phase 3: RAG Team Implementation (Week 3)

#### 3.1 RAG Team Structure
```python
# teams/rag-team/agents/knowledge_researcher.py
def knowledge_researcher():
    return Agent(
        role="Knowledge Researcher",
        goal="Find relevant information from organizational memory",
        tools=[
            MemorySearchTool(),
            PatternAnalysisTool(),
            KnowledgeSynthesisTool(),
        ]
    )

# teams/rag-team/agents/memory_curator.py
def memory_curator():
    return Agent(
        role="Memory Curator",
        goal="Organize and maintain organizational knowledge",
        tools=[
            MemoryOrganizationTool(),
            DuplicateDetectionTool(),
            KnowledgeGraphTool(),
        ]
    )
```

#### 3.2 RAG Team Capabilities
- **On-Demand Research**: Any team can request knowledge retrieval
- **Continuous Learning**: Monitors all team interactions for learning
- **Knowledge Curation**: Maintains quality and relevance
- **Insight Generation**: Proactive pattern detection

### Phase 4: Integration Tools (Week 4)

#### 4.1 Memory Tools for All Teams
```python
# elf_automations/shared/tools/memory_tools.py
class StoreMemoryTool(BaseTool):
    """Store important interactions or decisions in memory"""

class RetrieveMemoryTool(BaseTool):
    """Retrieve relevant memories for current context"""

class LearnFromOutcomeTool(BaseTool):
    """Record outcome of actions for future learning"""

class FindSimilarCasesTool(BaseTool):
    """Find how similar situations were handled before"""
```

#### 4.2 Automatic Memory Integration
```python
# Add to team base class
class MemoryAwareTeam:
    def __init__(self):
        self.memory_client = MemoryClient()

    async def before_task(self, task):
        """Retrieve relevant memories before starting task"""
        memories = await self.memory_client.get_relevant_memories(task)
        return self.augment_context_with_memories(task, memories)

    async def after_task(self, task, result):
        """Store outcome for learning"""
        await self.memory_client.store_outcome(task, result)
        await self.memory_client.analyze_patterns(task, result)
```

## Data Flow Examples

### Example 1: Marketing Campaign Memory
```python
# Marketing team stores campaign results
memory_entry = {
    "type": "campaign_outcome",
    "content": "Social media campaign for product X",
    "context": {
        "budget": 10000,
        "duration": "2 weeks",
        "platforms": ["twitter", "linkedin"],
        "metrics": {
            "engagement": 15000,
            "conversions": 250,
            "roi": 2.5
        }
    },
    "outcome": "success",
    "learnings": [
        "LinkedIn performed 3x better than Twitter",
        "Video content had highest engagement",
        "Tuesday/Thursday posting optimal"
    ]
}

# Later, another team queries
similar_campaigns = retrieve_memories(
    "social media campaign strategies that worked",
    filters={"outcome": "success", "roi": {">": 2.0}}
)
```

### Example 2: Engineering Pattern Learning
```python
# Engineering team encounters and solves a bug
store_memory({
    "type": "problem_solution",
    "content": "Database connection pool exhaustion",
    "context": {
        "symptoms": ["timeout errors", "slow queries"],
        "root_cause": "connection leak in async handlers",
        "solution": "implement connection context manager"
    }
})

# System learns pattern
pattern = {
    "condition": "timeout errors + async code",
    "likelihood": "connection leak",
    "solution": "check connection cleanup",
    "confidence": 0.85
}
```

## Success Metrics

1. **Memory Utilization**
   - % of decisions informed by past memory
   - Memory retrieval accuracy
   - Cross-team knowledge sharing rate

2. **Learning Effectiveness**
   - Pattern recognition accuracy
   - Reduction in repeated mistakes
   - Performance improvement over time

3. **System Intelligence**
   - Novel insight generation
   - Proactive problem prevention
   - Autonomous optimization actions

## Next Steps

1. **Choose Vector DB**: Recommend Qdrant for performance, unless you prefer Supabase simplicity
2. **Create Memory MCP**: Start with basic store/retrieve operations
3. **Build RAG Team**: Free agent team for knowledge services
4. **Integrate Tools**: Add memory tools to existing teams
5. **Monitor & Iterate**: Track usage and effectiveness

This system would give ElfAutomations true organizational memory - a critical step toward autonomy!
