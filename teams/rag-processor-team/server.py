"""
FastAPI server wrapper for RAG Processor Team
Exposes HTTP endpoints for A2A communication and health checks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from main import health_check
from pydantic import BaseModel
from workflows.document_pipeline import workflow

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RAG Processor Team API",
    description="Document processing pipeline with entity extraction and embedding generation",
    version="1.0.0",
)


class ProcessDocumentRequest(BaseModel):
    """Request model for document processing"""

    document_id: str
    tenant_id: str
    source_path: str
    priority: Optional[int] = 5
    metadata: Optional[Dict[str, Any]] = {}


class ProcessDocumentResponse(BaseModel):
    """Response model for document processing"""

    status: str
    message: str
    document_id: str
    queue_position: Optional[int] = None


class SearchRequest(BaseModel):
    """Request model for document search"""

    query: str
    tenant_id: str
    limit: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = {}
    include_entities: Optional[bool] = True


class StatusResponse(BaseModel):
    """Response model for document status"""

    document_id: str
    status: str
    progress: Dict[str, Any]
    errors: Optional[List[Dict[str, Any]]] = []
    completed_at: Optional[str] = None


# Background task queue for document processing
processing_tasks = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RAG Processor Team",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/ready",
            "/process",
            "/status/{document_id}",
            "/search",
            "/capabilities",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    result = await health_check()

    if result["status"] != "healthy":
        raise HTTPException(status_code=503, detail=result)

    return result


@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    # Check if we can process documents
    health_result = await health_check()

    ready_status = {
        "ready": health_result["status"] == "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": health_result["checks"],
    }

    if not ready_status["ready"]:
        raise HTTPException(status_code=503, detail=ready_status)

    return ready_status


@app.post("/process", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest, background_tasks: BackgroundTasks
):
    """Process a document through the RAG pipeline"""
    try:
        # Add to background processing
        task_id = f"{request.document_id}_{datetime.now().timestamp()}"

        # Start processing in background
        background_tasks.add_task(
            process_document_task,
            request.document_id,
            request.tenant_id,
            request.source_path,
            task_id,
        )

        # Store task reference
        processing_tasks[request.document_id] = {
            "task_id": task_id,
            "started_at": datetime.now().isoformat(),
            "status": "queued",
        }

        return ProcessDocumentResponse(
            status="accepted",
            message="Document queued for processing",
            document_id=request.document_id,
        )

    except Exception as e:
        logger.error(f"Error queuing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_task(
    document_id: str, tenant_id: str, source_path: str, task_id: str
):
    """Background task to process document"""
    try:
        # Update task status
        if document_id in processing_tasks:
            processing_tasks[document_id]["status"] = "processing"

        # Process through workflow
        result = await workflow.process_document(document_id, tenant_id, source_path)

        # Update task status
        if document_id in processing_tasks:
            processing_tasks[document_id]["status"] = "completed"
            processing_tasks[document_id]["completed_at"] = datetime.now().isoformat()
            processing_tasks[document_id]["result"] = result

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        if document_id in processing_tasks:
            processing_tasks[document_id]["status"] = "failed"
            processing_tasks[document_id]["error"] = str(e)


@app.get("/status/{document_id}", response_model=StatusResponse)
async def get_status(document_id: str):
    """Get processing status for a document"""
    try:
        # Check if we have a processing task
        if document_id in processing_tasks:
            task_info = processing_tasks[document_id]

            return StatusResponse(
                document_id=document_id,
                status=task_info["status"],
                progress={
                    "started_at": task_info.get("started_at"),
                    "completed_at": task_info.get("completed_at"),
                    "current_state": task_info.get("result", {}).get(
                        "current_state", "unknown"
                    ),
                },
                errors=task_info.get("result", {}).get("errors", []),
                completed_at=task_info.get("completed_at"),
            )

        # Check database for status
        from elf_automations.shared.utils import get_supabase_client

        supabase = get_supabase_client()

        result = (
            supabase.table("rag_documents")
            .select("*")
            .eq("id", document_id)
            .single()
            .execute()
        )

        if result.data:
            doc = result.data
            return StatusResponse(
                document_id=document_id,
                status=doc.get("status", "unknown"),
                progress={
                    "processing_started_at": doc.get("processing_started_at"),
                    "processing_completed_at": doc.get("processing_completed_at"),
                },
                errors=[doc.get("processing_error")]
                if doc.get("processing_error")
                else [],
                completed_at=doc.get("processing_completed_at"),
            )
        else:
            raise HTTPException(status_code=404, detail="Document not found")

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_documents(request: SearchRequest):
    """Search processed documents"""
    try:
        from agents.embedding_generator import EmbeddingGeneratorAgent
        from agents.storage_coordinator import StorageCoordinatorAgent

        # Generate query embedding
        embedding_agent = EmbeddingGeneratorAgent()
        query_embedding = await embedding_agent.generate_query_embedding(request.query)

        # Search in Qdrant
        storage_agent = StorageCoordinatorAgent()
        results = await storage_agent.search_similar_chunks(
            query_embedding, request.tenant_id, request.limit, request.filters
        )

        # Enrich with entities if requested
        if request.include_entities:
            # TODO: Add entity enrichment from Neo4j
            pass

        return {"query": request.query, "results": results, "total": len(results)}

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/capabilities")
async def get_capabilities():
    """Get team capabilities"""
    return {
        "team": "rag-processor-team",
        "capabilities": [
            {
                "name": "document_processing",
                "description": "Process documents through extraction, chunking, and embedding pipeline",
            },
            {
                "name": "entity_extraction",
                "description": "Extract entities and relationships based on document type",
            },
            {
                "name": "embedding_generation",
                "description": "Generate embeddings for semantic search",
            },
            {"name": "graph_building", "description": "Build knowledge graph in Neo4j"},
            {
                "name": "multi_store_coordination",
                "description": "Coordinate storage across Qdrant, Neo4j, and Supabase",
            },
        ],
        "supported_document_types": ["contract", "invoice", "technical_doc", "generic"],
        "supported_formats": [
            "text/plain",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.google-apps.document",
        ],
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting RAG Processor Team API")

    # Initialize workflow
    await workflow.initialize()

    # Start background queue processor
    asyncio.create_task(process_queue_background())


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down RAG Processor Team API")

    # Cleanup connections
    # TODO: Add cleanup logic


async def process_queue_background():
    """Background task to process document queue"""
    from workflows.document_pipeline import process_document_queue

    try:
        await process_document_queue()
    except Exception as e:
        logger.error(f"Queue processor error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
