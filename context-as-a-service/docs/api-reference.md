# API Reference

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
