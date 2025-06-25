# RAG System Monitoring Guide

## Overview

This guide provides comprehensive instructions for monitoring, analyzing, and optimizing the ELF Automations RAG (Retrieval-Augmented Generation) system. The monitoring tools help ensure system health, performance, and quality of document processing.

## Monitoring Components

### 1. RAG Analytics Dashboard
Real-time monitoring dashboard for the entire RAG system.

**Features:**
- Processing queue status
- Document processing metrics
- Storage utilization
- Entity extraction statistics
- Chunking strategy effectiveness

**Usage:**
```bash
# Run interactive dashboard
python scripts/rag_analytics_dashboard.py

# Custom refresh interval (default: 5 seconds)
python scripts/rag_analytics_dashboard.py --refresh 10

# Export metrics to JSON
python scripts/rag_analytics_dashboard.py --export metrics.json

# Set time window for analysis (default: 24 hours)
python scripts/rag_analytics_dashboard.py --window 48
```

**Key Metrics:**
- **Queue Health**: Backlog size, processing rate, failure rate
- **Document Processing**: Success rate, processing times by type
- **Storage**: Total size, chunk distribution, vector coverage
- **Entities**: Types extracted, confidence levels, relationships

### 2. Query Performance Analyzer
Analyzes search queries and provides optimization recommendations.

**Features:**
- Query latency analysis
- Search relevance scoring
- Vector similarity distribution
- Graph traversal optimization
- Query pattern detection

**Usage:**
```bash
# Analyze all components
python scripts/rag_query_analyzer.py

# Analyze specific component
python scripts/rag_query_analyzer.py --component performance
python scripts/rag_query_analyzer.py --component relevance
python scripts/rag_query_analyzer.py --component vectors
python scripts/rag_query_analyzer.py --component graph
python scripts/rag_query_analyzer.py --component patterns

# Generate comprehensive report
python scripts/rag_query_analyzer.py --report analysis_report.json

# Set analysis window (default: 7 days)
python scripts/rag_query_analyzer.py --window 30
```

**Performance Thresholds:**
- P50 latency: < 50ms
- P90 latency: < 200ms
- P95 latency: < 500ms
- P99 latency: < 1000ms

### 3. Health Monitor
Continuous health monitoring for RAG components.

**Features:**
- Qdrant connectivity and performance
- Neo4j health and query performance
- Supabase queue monitoring
- Embedding generation latency
- Alert generation

**Usage in code:**
```python
from elf_automations.shared.rag import RAGHealthMonitor

monitor = RAGHealthMonitor()

# Get health summary
summary = await monitor.get_health_summary()

# Continuous monitoring
await monitor.monitor_continuously(interval=60, callback=alert_handler)
```

**Health Thresholds:**
```python
latency_thresholds = {
    "qdrant": {"warning": 100, "critical": 500},
    "neo4j": {"warning": 200, "critical": 1000},
    "supabase": {"warning": 150, "critical": 750},
    "embedding": {"warning": 1000, "critical": 5000}
}

queue_thresholds = {
    "backlog": {"warning": 50, "critical": 200},
    "failed_rate": {"warning": 0.1, "critical": 0.25},
    "processing_time": {"warning": 300, "critical": 600}
}
```

### 4. Integration Test Suite
End-to-end testing for the RAG pipeline.

**Features:**
- Document ingestion testing
- Processing pipeline validation
- Multi-tenant isolation verification
- Search and retrieval testing
- Performance benchmarking

**Usage:**
```bash
# Run all tests
python scripts/test_rag_integration.py

# Run specific test
python scripts/test_rag_integration.py --test ingestion
python scripts/test_rag_integration.py --test pipeline
python scripts/test_rag_integration.py --test isolation
python scripts/test_rag_integration.py --test search
python scripts/test_rag_integration.py --test performance

# Export test results
python scripts/test_rag_integration.py --export test_results.json

# Skip cleanup (for debugging)
python scripts/test_rag_integration.py --skip-cleanup
```

### 5. Embedding Optimizer
Analyzes and optimizes vector embeddings.

**Features:**
- Embedding quality analysis
- Dimension reduction recommendations
- Redundancy detection
- Batch reprocessing
- Storage optimization

**Usage:**
```bash
# Analyze embeddings
python scripts/rag_embedding_optimizer.py

# Analyze specific collection
python scripts/rag_embedding_optimizer.py --collection document_embeddings

# Set sample size for analysis
python scripts/rag_embedding_optimizer.py --sample-size 5000

# Optimize collection
python scripts/rag_embedding_optimizer.py --optimize

# Optimize to specific dimensions
python scripts/rag_embedding_optimizer.py --optimize --target-dims 1536

# Batch reprocess documents
python scripts/rag_embedding_optimizer.py --reprocess document_ids.txt

# Export analysis
python scripts/rag_embedding_optimizer.py --export embedding_analysis.json
```

**Key Metrics:**
- **Sparsity**: < 30% (percentage of near-zero values)
- **Dimension Utilization**: > 80% (active dimensions)
- **Redundancy Ratio**: < 5% (duplicate embeddings)
- **Isotropy Score**: Lower is better (embedding distribution)

### 6. Graph Optimizer
Optimizes Neo4j graph performance.

**Features:**
- Graph structure analysis
- Query performance profiling
- Duplicate entity detection
- Relationship quality analysis
- Index recommendations

**Usage:**
```bash
# Analyze all aspects
python scripts/rag_graph_optimizer.py

# Specific analysis
python scripts/rag_graph_optimizer.py --analyze structure
python scripts/rag_graph_optimizer.py --analyze performance
python scripts/rag_graph_optimizer.py --analyze duplicates
python scripts/rag_graph_optimizer.py --analyze relationships

# Execute optimizations
python scripts/rag_graph_optimizer.py --optimize --operations create_indexes
python scripts/rag_graph_optimizer.py --optimize --operations remove_duplicates
python scripts/rag_graph_optimizer.py --optimize --operations prune_low_confidence
python scripts/rag_graph_optimizer.py --optimize --operations optimize_layout

# Export analysis
python scripts/rag_graph_optimizer.py --export graph_analysis.json
```

**Graph Health Indicators:**
- Average degree: 2-10 (connectivity)
- Isolated nodes: < 5%
- Graph density: 0.001-0.1
- Component size: Most nodes in single component

### 7. Watcher Setup & Management
Automated setup for document watchers.

**Features:**
- Google Drive folder configuration
- Multi-tenant folder setup
- OAuth token management
- Sync scheduling
- Health monitoring

**Usage:**
```bash
# Interactive setup wizard
python scripts/setup_rag_watchers.py

# Automated setup from config
python scripts/setup_rag_watchers.py --automated config.json

# Check watcher health only
python scripts/setup_rag_watchers.py --check-health

# Export health status
python scripts/setup_rag_watchers.py --check-health --export-config health.json
```

**Example config.json:**
```json
{
  "watchers": {
    "google_drive": {
      "enabled": true
    }
  },
  "tenants": [
    {
      "id": "tenant-uuid",
      "name": "acme_corp",
      "folder_id": "1ABC123DEF456"
    }
  ],
  "sync_interval": 300
}
```

## Performance Tuning

### Document Processing

**Optimal Settings:**
```yaml
# Chunking strategies by document type
contracts:
  strategy: semantic
  chunk_size: 800
  overlap: 200
  preserve_entities: true

technical_docs:
  strategy: structural
  chunk_size: 1000
  overlap: 100
  respect_boundaries: ["chapter", "section"]

general:
  strategy: sliding_window
  chunk_size: 500
  overlap: 50
```

### Vector Storage

**Qdrant Optimization:**
```python
# Collection configuration
vectors_config = {
    "size": 3072,  # For text-embedding-3-large
    "distance": "Cosine",
    "on_disk": True  # For large collections
}

# Indexing parameters
optimizer_config = {
    "deleted_threshold": 0.2,
    "vacuum_min_vector_number": 1000,
    "default_segment_number": 4
}
```

### Graph Database

**Neo4j Optimization:**
```cypher
-- Essential indexes
CREATE INDEX entity_normalized FOR (n:Entity) ON (n.normalized_name);
CREATE INDEX entity_type FOR (n:Entity) ON (n.entity_type);
CREATE INDEX entity_doc FOR (n:Entity) ON (n.document_id);

-- Relationship indexes
CREATE INDEX rel_confidence FOR ()-[r:RELATES_TO]->() ON (r.confidence);

-- Memory configuration
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=2g
```

## Troubleshooting

### Common Issues

#### 1. High Queue Backlog
**Symptoms:**
- Queue backlog > 200 documents
- Processing rate < ingestion rate

**Solutions:**
- Scale RAG processor replicas
- Increase processing priority for older documents
- Check for stuck documents in processing state
- Review document complexity causing slowdowns

#### 2. Low Embedding Quality
**Symptoms:**
- High sparsity (> 30%)
- Low dimension utilization (< 80%)
- Poor search relevance

**Solutions:**
- Switch to different embedding model
- Adjust chunking strategy
- Review document preprocessing
- Consider dimension reduction

#### 3. Graph Performance Issues
**Symptoms:**
- Slow relationship queries
- High memory usage
- Timeout errors

**Solutions:**
- Create missing indexes
- Remove duplicate entities
- Prune low-confidence relationships
- Optimize query patterns

#### 4. Search Relevance Problems
**Symptoms:**
- Low relevance scores
- Missing expected results
- Inconsistent results

**Solutions:**
- Review chunking boundaries
- Enhance entity extraction
- Adjust similarity thresholds
- Implement query expansion

### Debug Commands

```bash
# Check system logs
kubectl logs -n elf-teams deployment/rag-processor-team -f

# Database queries
# Check processing queue
SELECT status, COUNT(*) FROM rag_processing_queue GROUP BY status;

# Find stuck documents
SELECT * FROM rag_documents
WHERE status = 'processing'
AND processing_started_at < NOW() - INTERVAL '1 hour';

# Entity extraction success
SELECT document_type_id,
       AVG(CASE WHEN extracted_entities > 0 THEN 1 ELSE 0 END) as success_rate
FROM rag_documents
GROUP BY document_type_id;
```

## Best Practices

### 1. Regular Monitoring
- Run analytics dashboard during business hours
- Check health status every hour
- Review query performance weekly
- Analyze embeddings monthly

### 2. Proactive Optimization
- Create indexes before performance degrades
- Remove duplicates regularly
- Prune low-quality data
- Update embedding models periodically

### 3. Capacity Planning
- Monitor storage growth trends
- Plan for vector database scaling
- Allocate resources for peak processing
- Set quotas per tenant

### 4. Data Quality
- Validate extraction schemas
- Review entity normalization rules
- Check chunking effectiveness
- Ensure consistent document types

### 5. Security & Isolation
- Verify tenant isolation regularly
- Audit access patterns
- Monitor API usage
- Review OAuth token expiration

## Automation Scripts

### Daily Health Check
```bash
#!/bin/bash
# rag_daily_check.sh

# Export health status
python scripts/setup_rag_watchers.py --check-health --export-config /tmp/health.json

# Run analytics export
python scripts/rag_analytics_dashboard.py --export /tmp/metrics.json

# Check for alerts
python -c "
import json
with open('/tmp/health.json') as f:
    health = json.load(f)
if any(w['status'] != 'healthy' for w in health['watchers'].values()):
    print('ALERT: Unhealthy watchers detected!')
"
```

### Weekly Optimization
```bash
#!/bin/bash
# rag_weekly_optimize.sh

# Analyze and optimize embeddings
python scripts/rag_embedding_optimizer.py --export /tmp/embedding_analysis.json

# Analyze and optimize graph
python scripts/rag_graph_optimizer.py --export /tmp/graph_analysis.json

# Remove duplicates if needed
python scripts/rag_graph_optimizer.py --optimize --operations remove_duplicates

# Generate performance report
python scripts/rag_query_analyzer.py --report /tmp/weekly_performance.json
```

## Metrics to Track

### Key Performance Indicators (KPIs)

1. **Processing Efficiency**
   - Documents processed per hour
   - Average processing time by type
   - Queue backlog size
   - Failure rate

2. **Storage Efficiency**
   - Storage per document (MB)
   - Embedding dimensions used
   - Vector coverage percentage
   - Duplicate entity ratio

3. **Query Performance**
   - P95 query latency
   - Search relevance score
   - Cache hit rate
   - Query diversity

4. **System Health**
   - Component availability
   - Error rates by component
   - Resource utilization
   - API quota usage

## Conclusion

Effective monitoring of the RAG system requires:
1. Regular health checks using automated tools
2. Proactive optimization based on metrics
3. Quick response to alerts and anomalies
4. Continuous improvement of processing quality

Use this guide to maintain optimal performance and ensure high-quality document processing and retrieval across the ELF Automations ecosystem.
