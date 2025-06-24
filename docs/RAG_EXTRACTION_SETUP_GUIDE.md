# RAG Extraction Schema Setup Guide

## Overview

The RAG extraction system uses a flexible schema to handle different document types (contracts, invoices, technical docs, etc.) with type-specific entity extraction and relationship mapping.

## Setup Instructions

### 1. Apply Database Schema

The extraction schema extends the base RAG tables with flexible entity storage and relationship tracking.

**Run in Supabase SQL Editor:**
1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Copy contents of `sql/create_rag_extraction_tables.sql`
4. Click "Run" to execute

This creates:
- `rag_extraction_schemas` - Document type definitions
- `rag_extracted_entities` - Flexible entity storage
- `rag_entity_relationships` - Entity connections
- `rag_chunk_relationships` - Chunk connections
- `rag_document_classifications` - Document type detection
- `rag_extraction_history` - Processing audit trail

### 2. Verify Tables

After running the SQL, verify the tables exist:

```bash
python scripts/verify_rag_extraction_tables.py
```

Expected output:
```
✅ rag_extraction_schemas exists
✅ rag_extracted_entities exists
✅ rag_entity_relationships exists
✅ rag_chunk_relationships exists
✅ rag_document_classifications exists
✅ rag_extraction_history exists

📄 Found 3 extraction schemas:
   • contract: Legal Contract
     Entity types: party, jurisdiction, term, obligation, date, monetary_amount
   • invoice: Invoice
     Entity types: vendor, customer, line_item, product, service, monetary_amount, date
   • technical_doc: Technical Documentation
     Entity types: component, system, requirement, procedure, concept, version
```

## Schema Design

### Flexible Entity Storage

Each entity has:
- **Type**: What kind of entity (party, date, amount, etc.)
- **Value**: The actual extracted value
- **Properties**: Type-specific attributes stored as JSON

Example contract party:
```json
{
  "entity_type": "party",
  "entity_value": "ACME Corporation",
  "properties": {
    "name": "ACME Corporation",
    "type": "corporation",
    "jurisdiction": "Delaware",
    "role": "vendor"
  }
}
```

### Relationship Tracking

Relationships connect entities:
```json
{
  "source_entity": "ACME Corporation",
  "target_entity": "Service Agreement",
  "relationship_type": "PARTY_TO",
  "properties": {
    "role": "service_provider",
    "effective_date": "2024-01-01"
  }
}
```

### Document Type Schemas

Each document type defines:
1. **Entity Types**: What to extract
2. **Relationship Types**: How entities connect
3. **Extraction Config**: LLM settings and prompts
4. **Chunking Strategy**: How to split documents
5. **Graph Schema**: Neo4j node/edge definitions

## Adding New Document Types

To support a new document type:

```sql
INSERT INTO rag_extraction_schemas (
    document_type,
    display_name,
    description,
    entity_types,
    relationship_types,
    extraction_config,
    chunking_strategy,
    graph_schema
) VALUES (
    'purchase_order',
    'Purchase Order',
    'Purchase orders and procurement documents',
    '["buyer", "seller", "item", "delivery_date", "payment_terms"]'::jsonb,
    '["ORDERS_FROM", "DELIVERS_TO", "CONTAINS_ITEM"]'::jsonb,
    '{
        "llm_model": "gpt-4",
        "temperature": 0.1,
        "extraction_prompt_template": "Extract buyer, seller, items, and terms..."
    }'::jsonb,
    '{
        "primary_strategy": "structural",
        "preserve_tables": true
    }'::jsonb,
    '{
        "node_labels": {
            "buyer": "Organization",
            "seller": "Organization",
            "item": "Product"
        }
    }'::jsonb
);
```

## Next Steps

1. ✅ Database schema created
2. ⏳ Create RAG processor team
3. ⏳ Implement document processing pipeline
4. ⏳ Test with sample documents

The flexible schema allows the system to adapt to new document types without code changes!
