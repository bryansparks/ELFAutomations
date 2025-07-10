"""
Context-as-a-Service API Server.

Provides REST endpoints for document ingestion, context retrieval,
and MCP management.
"""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import structlog
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Configure logging
logger = structlog.get_logger()

# Import core components (these will be available after extraction)
from core.rag_processor.workflows.document_pipeline import DocumentPipeline
from shared.config import Settings
from shared.mcp.client import MCPRegistryClient
from shared.storage.qdrant_client import QdrantClient

# Initialize settings
settings = Settings()

# Global instances
document_pipeline: Optional[DocumentPipeline] = None
mcp_registry: Optional[MCPRegistryClient] = None
qdrant_client: Optional[QdrantClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global document_pipeline, mcp_registry, qdrant_client

    # Initialize services
    logger.info("Initializing Context-as-a-Service API")

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY
    )

    # Initialize document pipeline
    document_pipeline = DocumentPipeline(
        qdrant_client=qdrant_client,
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_KEY,
    )

    # Initialize MCP registry client
    mcp_registry = MCPRegistryClient(agentgateway_url=settings.AGENTGATEWAY_URL)

    logger.info("Context-as-a-Service API initialized successfully")

    yield

    # Cleanup
    logger.info("Shutting down Context-as-a-Service API")


# Create FastAPI app
app = FastAPI(
    title="Context-as-a-Service API",
    description="Contextual knowledge service with MCP integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class DocumentIngestionRequest(BaseModel):
    """Request model for document ingestion."""

    content: str = Field(..., description="Document content to ingest")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
    collection: str = Field(default="default", description="Target collection name")


class DocumentIngestionResponse(BaseModel):
    """Response model for document ingestion."""

    document_id: str
    status: str
    chunks_created: int
    message: str


class ContextSearchRequest(BaseModel):
    """Request model for context search."""

    query: str = Field(..., description="Search query")
    collection: str = Field(default="default", description="Collection to search")
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum results to return"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional filters"
    )
    include_metadata: bool = Field(
        default=True, description="Include metadata in results"
    )


class ContextSearchResult(BaseModel):
    """Single search result."""

    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class ContextSearchResponse(BaseModel):
    """Response model for context search."""

    results: List[ContextSearchResult]
    total_results: int
    query: str


class MCPRegistrationRequest(BaseModel):
    """Request model for MCP registration."""

    name: str = Field(..., description="MCP server name")
    endpoint: str = Field(..., description="MCP server endpoint URL")
    capabilities: List[str] = Field(..., description="List of capabilities")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


# Authentication dependency
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header."""
    # In production, validate against database
    if not x_api_key or len(x_api_key) < 10:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "context-as-a-service", "version": "1.0.0"}


# Document ingestion endpoints
@app.post("/api/v1/ingest/document", response_model=DocumentIngestionResponse)
async def ingest_document(
    request: DocumentIngestionRequest, api_key: str = Depends(verify_api_key)
):
    """Ingest a document for RAG processing."""
    try:
        # Process document through pipeline
        result = await document_pipeline.process_document(
            content=request.content,
            metadata=request.metadata,
            collection=request.collection,
        )

        return DocumentIngestionResponse(
            document_id=result["document_id"],
            status="processing",
            chunks_created=result["chunks_created"],
            message="Document ingestion started successfully",
        )
    except Exception as e:
        logger.error("Document ingestion failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Context search endpoints
@app.post("/api/v1/search", response_model=ContextSearchResponse)
async def search_context(
    request: ContextSearchRequest, api_key: str = Depends(verify_api_key)
):
    """Search for relevant context."""
    try:
        # Search in Qdrant
        results = await qdrant_client.search(
            collection_name=request.collection,
            query_text=request.query,
            limit=request.limit,
            filters=request.filters,
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                ContextSearchResult(
                    content=result.payload.get("content", ""),
                    score=result.score,
                    metadata=result.payload if request.include_metadata else None,
                )
            )

        return ContextSearchResponse(
            results=formatted_results,
            total_results=len(formatted_results),
            query=request.query,
        )
    except Exception as e:
        logger.error("Context search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# MCP management endpoints
@app.get("/api/v1/mcps")
async def list_mcps(api_key: str = Depends(verify_api_key)):
    """List all registered MCP servers."""
    try:
        mcps = await mcp_registry.list_mcps()
        return {"mcps": mcps}
    except Exception as e:
        logger.error("Failed to list MCPs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/mcps/register")
async def register_mcp(
    request: MCPRegistrationRequest, api_key: str = Depends(verify_api_key)
):
    """Register a new MCP server."""
    try:
        result = await mcp_registry.register_mcp(
            name=request.name,
            endpoint=request.endpoint,
            capabilities=request.capabilities,
            metadata=request.metadata,
        )
        return {"status": "registered", "mcp_id": result["id"]}
    except Exception as e:
        logger.error("MCP registration failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints
@app.get("/api/v1/admin/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get system statistics."""
    try:
        # Get collection stats from Qdrant
        collections = await qdrant_client.get_collections()

        stats = {"collections": [], "total_documents": 0, "total_chunks": 0}

        for collection in collections:
            info = await qdrant_client.get_collection_info(collection.name)
            stats["collections"].append(
                {
                    "name": collection.name,
                    "vectors_count": info.vectors_count,
                    "points_count": info.points_count,
                }
            )
            stats["total_chunks"] += info.vectors_count

        return stats
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8080"))
    host = os.getenv("API_HOST", "0.0.0.0")

    uvicorn.run("main:app", host=host, port=port, reload=True, log_level="info")
