# GraphDB Quick Start Guide

## Option 1: Neo4j Community (Recommended for Start)

### Local Development Setup
```bash
# Using Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/elfautomations2025 \
  -v $HOME/neo4j/data:/data \
  -v $HOME/neo4j/logs:/logs \
  neo4j:5.15-community

# Access browser UI at http://localhost:7474
# Bolt connection at bolt://localhost:7687
```

### K8s Deployment
```yaml
# k8s/infrastructure/neo4j/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neo4j
  namespace: elf-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.15-community
        ports:
        - containerPort: 7474  # HTTP
        - containerPort: 7687  # Bolt
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: auth
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: neo4j-pvc
```

## Option 2: ArangoDB (Multi-Model Alternative)

### Why Consider ArangoDB?
- Single database for documents AND graphs
- No need to sync between systems
- Built-in full-text search
- More flexible schema

### Setup
```bash
docker run -d \
  --name arangodb \
  -p 8529:8529 \
  -e ARANGO_ROOT_PASSWORD=elfautomations2025 \
  arangodb/arangodb:3.11
```

## Quick Proof of Concept

### 1. Create Simple GraphDB MCP
```bash
cd tools
python mcp_factory.py

# Name: graph-knowledge-base
# Type: typescript
# Use template: database
# Add tools: create_node, find_relationships, graph_search
```

### 2. Test Document Processing
```python
# scripts/test_graph_rag.py
import neo4j
from langchain.text_splitter import RecursiveCharacterTextSplitter
from elf_automations.shared.utils.llm_factory import LLMFactory

class GraphRAGDemo:
    def __init__(self):
        self.driver = neo4j.GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "elfautomations2025")
        )
        self.llm = LLMFactory.create_llm()

    def process_document(self, text, doc_type="general"):
        # 1. Chunk document
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_text(text)

        # 2. Extract entities per chunk
        with self.driver.session() as session:
            doc_id = self.create_document(session, doc_type)

            for i, chunk in enumerate(chunks):
                # Create chunk node
                chunk_id = self.create_chunk(session, doc_id, chunk, i)

                # Extract entities
                entities = self.extract_entities(chunk)

                # Create entity nodes and relationships
                for entity in entities:
                    self.create_entity_graph(session, chunk_id, entity)

    def hybrid_search(self, query):
        # Vector search in Qdrant
        vector_results = self.vector_search(query)

        # Graph search in Neo4j
        graph_results = self.graph_search(query)

        # Combine and rank
        return self.merge_results(vector_results, graph_results)
```

### 3. Sample GraphDB Schema
```cypher
// Create constraints and indexes
CREATE CONSTRAINT doc_id IF NOT EXISTS
FOR (d:Document) REQUIRE d.id IS UNIQUE;

CREATE INDEX doc_type IF NOT EXISTS
FOR (d:Document) ON (d.type);

// Sample data structure
CREATE (d:Document {
    id: 'doc_001',
    title: 'Service Agreement',
    type: 'contract',
    created_at: datetime()
})

CREATE (c:Chunk {
    id: 'chunk_001',
    text: 'This agreement between...',
    position: 0
})

CREATE (e1:Entity {
    name: 'ACME Corp',
    type: 'organization'
})

CREATE (e2:Entity {
    name: 'John Doe',
    type: 'person'
})

// Relationships
CREATE (d)-[:CONTAINS]->(c)
CREATE (c)-[:MENTIONS]->(e1)
CREATE (c)-[:MENTIONS]->(e2)
CREATE (e1)-[:PARTY_TO]->(d)
CREATE (e2)-[:SIGNATORY_OF]->(d)
```

## Decision Framework

### Choose Neo4j if:
- You want a dedicated graph database
- You need advanced graph algorithms
- You want the most mature ecosystem
- You plan to scale significantly

### Choose ArangoDB if:
- You want a unified multi-model database
- You prefer fewer moving parts
- You need flexible document storage
- You want built-in search

### Start Simple:
1. Deploy Neo4j locally
2. Create basic MCP with 3-4 tools
3. Process 10 test documents
4. Build simple hybrid search
5. Evaluate performance

## Recommended First Week Plan

### Day 1-2: Infrastructure
- Deploy Neo4j locally
- Create K8s manifests
- Test connectivity

### Day 3-4: Basic MCP
- Use mcp_factory to create graph-knowledge-base
- Implement create_node and find_relationships
- Test with simple data

### Day 5-7: Document Processing
- Create simple NER pipeline
- Process sample contracts/invoices
- Build basic graph structure
- Test queries

## Key Integration Points

### With Existing System
```python
# Extend document processing
class EnhancedDocumentProcessor:
    def __init__(self):
        self.vector_store = QdrantClient(...)  # Existing
        self.graph_store = Neo4jDriver(...)    # New
        self.metadata_store = SupabaseClient(...)  # Existing

    def process(self, document):
        # 1. Store metadata in Supabase
        doc_id = self.store_metadata(document)

        # 2. Generate embeddings for Qdrant
        chunks, embeddings = self.chunk_and_embed(document)
        self.vector_store.upsert(chunks, embeddings)

        # 3. Extract graph structure for Neo4j
        entities, relationships = self.extract_graph(document)
        self.graph_store.create_graph(entities, relationships)

        return doc_id
```

### Query Router
```python
class IntelligentQueryRouter:
    def route(self, query):
        # Analyze query intent
        intent = self.analyze_intent(query)

        if intent == "find_similar":
            return self.vector_store.search(query)
        elif intent == "find_connected":
            return self.graph_store.traverse(query)
        elif intent == "find_facts":
            return self.metadata_store.query(query)
        else:  # Complex query
            return self.hybrid_search(query)
```

## Common Pitfalls to Avoid

1. **Over-engineering the schema** - Start simple, evolve based on needs
2. **Ignoring performance** - Graph queries can be expensive
3. **Not planning for scale** - Design for 10x current volume
4. **Tight coupling** - Keep stores independent
5. **Manual entity extraction** - Use NER models from start

## Resources

### Neo4j
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Graph Data Science Library](https://neo4j.com/docs/graph-data-science/current/)

### NER/Entity Extraction
- spaCy with custom models
- Hugging Face token classification
- OpenAI function calling for extraction

### Integration Examples
- [LangChain Neo4j](https://python.langchain.com/docs/integrations/graphs/neo4j)
- [LlamaIndex Knowledge Graphs](https://docs.llamaindex.ai/en/stable/examples/index_structs/knowledge_graph/)
