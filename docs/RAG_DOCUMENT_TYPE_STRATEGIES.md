# RAG Document Type Processing Strategies

## Document Type Analysis

### 1. Invoices
**Characteristics:**
- Highly structured
- Numerical data dominant
- Clear relationships (vendor → line items → totals)
- Temporal patterns important

**Optimal Processing:**
```python
class InvoiceProcessor:
    storage_strategy = {
        "primary": "graph",      # Vendor relationships, payment flows
        "secondary": "sql",      # Financial queries, aggregations
        "embeddings": "minimal"  # Only for item descriptions
    }

    def extract(self, invoice):
        return {
            "entities": [
                {"type": "vendor", "name": vendor_name, "id": tax_id},
                {"type": "amount", "value": total, "currency": currency},
                {"type": "date", "value": invoice_date}
            ],
            "relationships": [
                ("vendor", "ISSUED", "invoice"),
                ("invoice", "CONTAINS", "line_item"),
                ("invoice", "DUE_ON", "date")
            ],
            "structured_data": {
                "line_items": [...],  # For SQL storage
                "totals": {...},
                "payment_terms": {...}
            }
        }
```

**Query Examples:**
- "Show all invoices from vendor X over $10,000"
- "Find unusual spending patterns"
- "Which vendors have increasing costs?"

### 2. Contracts
**Characteristics:**
- Semi-structured with legal language
- Complex entity relationships
- Temporal aspects (terms, deadlines)
- Cross-references common

**Optimal Processing:**
```python
class ContractProcessor:
    storage_strategy = {
        "primary": "graph",      # Party relationships, obligations
        "secondary": "vector",   # Semantic search for clauses
        "embeddings": "full"     # Every section embedded
    }

    def extract(self, contract):
        return {
            "entities": [
                {"type": "party", "name": name, "role": role},
                {"type": "term", "name": term_name, "value": value},
                {"type": "clause", "type": clause_type, "text": text},
                {"type": "date", "type": date_type, "value": date}
            ],
            "relationships": [
                ("party1", "CONTRACTS_WITH", "party2"),
                ("party", "OBLIGATED_BY", "clause"),
                ("clause", "EXPIRES_ON", "date"),
                ("contract", "REFERENCES", "other_contract")
            ],
            "semantic_chunks": [
                # Each major section for vector search
            ]
        }
```

**Query Examples:**
- "Find all contracts with penalty clauses"
- "Show contracts expiring next quarter"
- "Which contracts reference document X?"

### 3. Research Papers
**Characteristics:**
- Highly unstructured content
- Citation networks crucial
- Topic clustering important
- Semantic similarity primary

**Optimal Processing:**
```python
class ResearchPaperProcessor:
    storage_strategy = {
        "primary": "vector",     # Semantic search dominant
        "secondary": "graph",    # Citation networks
        "embeddings": "detailed" # Multiple embedding strategies
    }

    def extract(self, paper):
        return {
            "entities": [
                {"type": "author", "name": name, "affiliation": org},
                {"type": "concept", "name": concept, "definition": def},
                {"type": "citation", "title": title, "doi": doi}
            ],
            "relationships": [
                ("paper", "AUTHORED_BY", "author"),
                ("paper", "CITES", "other_paper"),
                ("paper", "DISCUSSES", "concept"),
                ("author", "COLLABORATES_WITH", "author")
            ],
            "embeddings": {
                "abstract": embed_abstract(),
                "sections": embed_sections(),
                "figures": embed_figure_captions()
            }
        }
```

**Query Examples:**
- "Papers similar to X on topic Y"
- "Most cited papers by author Z"
- "Recent work building on concept A"

### 4. Emails
**Characteristics:**
- Conversation threads
- Network effects important
- Mixed content types
- Privacy considerations

**Optimal Processing:**
```python
class EmailProcessor:
    storage_strategy = {
        "primary": "graph",      # Communication networks
        "secondary": "vector",   # Content search
        "embeddings": "privacy_aware"  # Sanitized embeddings
    }

    def extract(self, email):
        return {
            "entities": [
                {"type": "person", "email": addr, "name": name},
                {"type": "topic", "keywords": keywords},
                {"type": "attachment", "name": filename, "type": filetype}
            ],
            "relationships": [
                ("sender", "EMAILED", "recipient"),
                ("email", "IN_THREAD", "thread"),
                ("email", "MENTIONS", "topic"),
                ("person", "CC_ON", "email")
            ],
            "privacy_filtered": {
                "content": redact_pii(content),
                "metadata": anonymize_metadata(metadata)
            }
        }
```

### 5. Blog Posts/Articles
**Characteristics:**
- Public content
- SEO/topic focused
- Multimedia possible
- Temporal relevance

**Optimal Processing:**
```python
class BlogPostProcessor:
    storage_strategy = {
        "primary": "vector",     # Content similarity
        "secondary": "graph",    # Topic relationships
        "embeddings": "multimodal"  # Text + images
    }
```

## Unified Processing Pipeline

```python
class UnifiedDocumentProcessor:
    """Single processor with type-specific strategies"""

    def __init__(self):
        self.processors = {
            "invoice": InvoiceProcessor(),
            "contract": ContractProcessor(),
            "research": ResearchPaperProcessor(),
            "email": EmailProcessor(),
            "blog": BlogPostProcessor(),
            "general": GeneralDocumentProcessor()
        }

    def process(self, document, doc_type=None):
        # Auto-detect type if not provided
        if not doc_type:
            doc_type = self.classify_document(document)

        # Get appropriate processor
        processor = self.processors.get(doc_type, self.processors["general"])

        # Process according to type
        result = processor.extract(document)

        # Store in appropriate systems
        self.store_results(result, processor.storage_strategy)

        return result
```

## Query Strategy Selection

```python
class QueryStrategySelector:
    """Determines optimal retrieval strategy based on query and context"""

    def select_strategy(self, query, context=None):
        # Analyze query
        query_type = self.classify_query(query)
        entities = self.extract_query_entities(query)

        # Determine document types likely to contain answer
        target_doc_types = self.predict_relevant_doc_types(query)

        # Build retrieval plan
        if query_type == "relationship":
            return GraphTraversalStrategy(entities)
        elif query_type == "similarity":
            return VectorSimilarityStrategy(query)
        elif query_type == "aggregation":
            return SQLAggregationStrategy(query)
        elif query_type == "complex":
            return HybridStrategy(query, target_doc_types)
```

## Storage Optimization

### Document Type → Storage Mapping
```yaml
Storage Recommendations:
  Invoice:
    - Graph: 70% (vendor networks, payment flows)
    - SQL: 25% (financial aggregations)
    - Vector: 5% (item descriptions only)

  Contract:
    - Graph: 50% (party relationships, obligations)
    - Vector: 40% (clause similarity)
    - SQL: 10% (metadata, dates)

  Research:
    - Vector: 60% (semantic search)
    - Graph: 30% (citation networks)
    - SQL: 10% (metadata)

  Email:
    - Graph: 60% (communication networks)
    - Vector: 30% (content search)
    - SQL: 10% (metadata)

  Blog/Article:
    - Vector: 70% (content similarity)
    - Graph: 20% (topic relationships)
    - SQL: 10% (metadata)
```

## Implementation Recommendations

### 1. Start with Document Classification
```python
# Use small LLM for fast classification
classifier = LLMFactory.create_llm(
    preferred_provider="openrouter",
    preferred_model="auto",
    preferences={"prefer_faster": True}
)

doc_type = classifier.classify(document_sample)
```

### 2. Build Type-Specific Processors Incrementally
- Week 1: General document processor
- Week 2: Contract processor (high value)
- Week 3: Invoice processor (structured)
- Week 4: Email processor (volume)
- Week 5: Research processor (complex)

### 3. Implement Hybrid Retrieval Early
- Don't wait for all processors
- Start with vector + graph basics
- Add SQL aggregations later
- Refine based on usage

### 4. Monitor and Optimize
```python
class ProcessingMetrics:
    def track(self, doc_type, processing_time, storage_used):
        # Track efficiency by document type
        # Identify optimization opportunities
        # Adjust strategies based on results
```

## Key Design Decision: Single vs Multiple RAGs

### Recommendation: Single RAG with Pluggable Processors

**Advantages:**
- Unified query interface
- Shared infrastructure (embeddings, LLMs)
- Consistent user experience
- Easier monitoring and maintenance
- Cross-document-type queries supported

**Architecture:**
```
User Query
    ↓
RAG Free Agent Team
    ↓
Query Analyzer → Document Type Predictor
    ↓              ↓
Strategy Selector ←
    ↓
Parallel Retrieval
    ├── Graph Search (Neo4j)
    ├── Vector Search (Qdrant)
    └── SQL Query (Supabase)
    ↓
Result Fusion & Ranking
    ↓
Answer Generation
```

This approach gives you the flexibility of specialized processing while maintaining a simple, unified interface for users.
