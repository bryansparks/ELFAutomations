"""
RAG Document Processing Pipeline using LangGraph
This workflow orchestrates the entire document processing flow from
queue monitoring through entity extraction, chunking, embedding, and storage.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

import langgraph.checkpoint as checkpoint
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

# Import our agents
from agents import (
    document_classifier,
    embedding_generator,
    entity_extractor,
    graph_builder,
    queue_monitor,
    smart_chunker,
    storage_coordinator,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingState(str, Enum):
    """Document processing states"""

    QUEUED = "QUEUED"
    CLASSIFYING = "CLASSIFYING"
    EXTRACTING = "EXTRACTING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    STORING = "STORING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY = "RETRY"


class DocumentState(TypedDict):
    """State for document processing"""

    # Document identification
    document_id: str
    tenant_id: str
    source_path: str

    # Processing state
    current_state: ProcessingState
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]

    # Document content and metadata
    content: Optional[str]
    metadata: Dict[str, Any]

    # Classification results
    document_type: Optional[str]
    classification_confidence: Optional[float]
    extraction_schema: Optional[Dict[str, Any]]

    # Extraction results
    extracted_entities: List[Dict[str, Any]]
    extracted_relationships: List[Dict[str, Any]]

    # Chunking results
    chunks: List[Dict[str, Any]]
    chunk_relationships: List[Dict[str, Any]]
    chunking_strategy: Optional[str]

    # Embedding results
    embeddings: List[Dict[str, Any]]
    embedding_model: Optional[str]

    # Storage references
    neo4j_nodes: List[str]
    neo4j_edges: List[str]
    qdrant_ids: List[str]

    # Error handling
    errors: List[Dict[str, Any]]
    retry_count: int
    max_retries: int


class RAGProcessingWorkflow:
    """Main workflow for RAG document processing"""

    def __init__(self):
        self.workflow = self._build_workflow()
        self.checkpointer = checkpoint.MemorySaver()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(DocumentState)

        # Add nodes for each processing stage
        workflow.add_node("monitor_queue", self.monitor_queue_node)
        workflow.add_node("classify", self.classify_document_node)
        workflow.add_node("extract", self.extract_entities_node)
        workflow.add_node("chunk", self.chunk_document_node)
        workflow.add_node("embed", self.generate_embeddings_node)
        workflow.add_node("store", self.store_results_node)
        workflow.add_node("complete", self.complete_processing_node)
        workflow.add_node("handle_error", self.handle_error_node)

        # Define edges (transitions)
        workflow.add_edge("monitor_queue", "classify")
        workflow.add_edge("classify", "extract")
        workflow.add_edge("extract", "chunk")
        workflow.add_edge("chunk", "embed")
        workflow.add_edge("embed", "store")
        workflow.add_edge("store", "complete")
        workflow.add_edge("complete", END)

        # Conditional edges for error handling
        workflow.add_conditional_edges(
            "classify",
            self.check_for_errors,
            {"continue": "extract", "error": "handle_error"},
        )

        workflow.add_conditional_edges(
            "extract",
            self.check_for_errors,
            {"continue": "chunk", "error": "handle_error"},
        )

        workflow.add_conditional_edges(
            "handle_error", self.should_retry, {"retry": "monitor_queue", "fail": END}
        )

        # Set entry point
        workflow.set_entry_point("monitor_queue")

        return workflow.compile()

    async def monitor_queue_node(self, state: DocumentState) -> DocumentState:
        """Monitor queue and fetch document for processing"""
        logger.info(f"Monitoring queue for document {state['document_id']}")

        # Update state
        state["current_state"] = ProcessingState.QUEUED
        state["processing_started_at"] = datetime.now()

        # Fetch document content and metadata
        result = await queue_monitor.fetch_document(state["document_id"])
        state["content"] = result["content"]
        state["metadata"] = result["metadata"]

        # Update document status in queue
        await queue_monitor.update_status(
            state["document_id"],
            "processing",
            {"started_at": state["processing_started_at"]},
        )

        return state

    async def classify_document_node(self, state: DocumentState) -> DocumentState:
        """Classify document type"""
        logger.info(f"Classifying document {state['document_id']}")
        state["current_state"] = ProcessingState.CLASSIFYING

        try:
            # Classify document
            classification = await document_classifier.classify(
                content=state["content"], metadata=state["metadata"]
            )

            state["document_type"] = classification["type"]
            state["classification_confidence"] = classification["confidence"]

            # Get extraction schema for document type
            schema = await document_classifier.get_extraction_schema(
                classification["type"]
            )
            state["extraction_schema"] = schema

            logger.info(
                f"Classified as {classification['type']} "
                f"with confidence {classification['confidence']}"
            )

        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            state["errors"].append(
                {
                    "stage": "classification",
                    "error": str(e),
                    "timestamp": datetime.now(),
                }
            )

        return state

    async def extract_entities_node(self, state: DocumentState) -> DocumentState:
        """Extract entities and relationships"""
        logger.info(f"Extracting entities from document {state['document_id']}")
        state["current_state"] = ProcessingState.EXTRACTING

        try:
            # Extract based on schema
            extraction_result = await entity_extractor.extract(
                content=state["content"],
                schema=state["extraction_schema"],
                document_type=state["document_type"],
            )

            state["extracted_entities"] = extraction_result["entities"]
            state["extracted_relationships"] = extraction_result["relationships"]

            logger.info(
                f"Extracted {len(state['extracted_entities'])} entities "
                f"and {len(state['extracted_relationships'])} relationships"
            )

            # Store extracted data
            await entity_extractor.store_entities(
                document_id=state["document_id"],
                tenant_id=state["tenant_id"],
                entities=state["extracted_entities"],
                relationships=state["extracted_relationships"],
            )

        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            state["errors"].append(
                {"stage": "extraction", "error": str(e), "timestamp": datetime.now()}
            )

        return state

    async def chunk_document_node(self, state: DocumentState) -> DocumentState:
        """Chunk document using appropriate strategy"""
        logger.info(f"Chunking document {state['document_id']}")
        state["current_state"] = ProcessingState.CHUNKING

        try:
            # Get chunking strategy from schema
            strategy = state["extraction_schema"].get(
                "chunking_strategy", {"primary_strategy": "sliding_window"}
            )
            state["chunking_strategy"] = strategy["primary_strategy"]

            # Chunk document
            chunking_result = await smart_chunker.chunk(
                content=state["content"],
                strategy=strategy,
                entities=state["extracted_entities"],
                preserve_entities=strategy.get("preserve_entities", True),
            )

            state["chunks"] = chunking_result["chunks"]
            state["chunk_relationships"] = chunking_result["relationships"]

            logger.info(
                f"Created {len(state['chunks'])} chunks using "
                f"{state['chunking_strategy']} strategy"
            )

        except Exception as e:
            logger.error(f"Chunking error: {str(e)}")
            state["errors"].append(
                {"stage": "chunking", "error": str(e), "timestamp": datetime.now()}
            )

        return state

    async def generate_embeddings_node(self, state: DocumentState) -> DocumentState:
        """Generate embeddings for chunks"""
        logger.info(f"Generating embeddings for document {state['document_id']}")
        state["current_state"] = ProcessingState.EMBEDDING

        try:
            # Generate embeddings
            embedding_result = await embedding_generator.generate(
                chunks=state["chunks"], model="text-embedding-3-large"
            )

            state["embeddings"] = embedding_result["embeddings"]
            state["embedding_model"] = embedding_result["model"]

            logger.info(f"Generated {len(state['embeddings'])} embeddings")

        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            state["errors"].append(
                {"stage": "embedding", "error": str(e), "timestamp": datetime.now()}
            )

        return state

    async def store_results_node(self, state: DocumentState) -> DocumentState:
        """Store results in Neo4j, Qdrant, and Supabase"""
        logger.info(f"Storing results for document {state['document_id']}")
        state["current_state"] = ProcessingState.STORING

        try:
            # Store in Neo4j
            neo4j_result = await graph_builder.build_graph(
                document_id=state["document_id"],
                entities=state["extracted_entities"],
                relationships=state["extracted_relationships"],
                chunks=state["chunks"],
                chunk_relationships=state["chunk_relationships"],
            )

            state["neo4j_nodes"] = neo4j_result["node_ids"]
            state["neo4j_edges"] = neo4j_result["edge_ids"]

            # Store in Qdrant
            qdrant_result = await storage_coordinator.store_embeddings(
                tenant_id=state["tenant_id"],
                document_id=state["document_id"],
                chunks=state["chunks"],
                embeddings=state["embeddings"],
            )

            state["qdrant_ids"] = qdrant_result["vector_ids"]

            logger.info(
                f"Stored {len(state['neo4j_nodes'])} nodes in Neo4j, "
                f"{len(state['qdrant_ids'])} vectors in Qdrant"
            )

        except Exception as e:
            logger.error(f"Storage error: {str(e)}")
            state["errors"].append(
                {"stage": "storage", "error": str(e), "timestamp": datetime.now()}
            )

        return state

    async def complete_processing_node(self, state: DocumentState) -> DocumentState:
        """Complete processing and update status"""
        logger.info(f"Completing processing for document {state['document_id']}")
        state["current_state"] = ProcessingState.COMPLETED
        state["processing_completed_at"] = datetime.now()

        # Calculate processing time
        processing_time = (
            state["processing_completed_at"] - state["processing_started_at"]
        ).total_seconds()

        # Update document status
        await queue_monitor.update_status(
            state["document_id"],
            "completed",
            {
                "completed_at": state["processing_completed_at"],
                "processing_time_seconds": processing_time,
                "entities_extracted": len(state["extracted_entities"]),
                "chunks_created": len(state["chunks"]),
                "embeddings_generated": len(state["embeddings"]),
            },
        )

        logger.info(
            f"Document {state['document_id']} processed successfully "
            f"in {processing_time:.2f} seconds"
        )

        return state

    async def handle_error_node(self, state: DocumentState) -> DocumentState:
        """Handle errors and determine retry strategy"""
        logger.error(f"Handling error for document {state['document_id']}")

        latest_error = state["errors"][-1] if state["errors"] else None

        if latest_error:
            # Log to error tracking
            await storage_coordinator.log_error(
                document_id=state["document_id"],
                error=latest_error,
                state=state["current_state"],
                retry_count=state["retry_count"],
            )

        state["retry_count"] += 1

        return state

    def check_for_errors(self, state: DocumentState) -> str:
        """Check if there are errors in the current state"""
        if (
            state["errors"]
            and state["errors"][-1]["stage"] == state["current_state"].value.lower()
        ):
            return "error"
        return "continue"

    def should_retry(self, state: DocumentState) -> str:
        """Determine if we should retry or fail"""
        if state["retry_count"] < state["max_retries"]:
            logger.info(
                f"Retrying document {state['document_id']} "
                f"(attempt {state['retry_count'] + 1}/{state['max_retries']})"
            )
            return "retry"
        else:
            logger.error(f"Max retries reached for document {state['document_id']}")
            return "fail"

    async def process_document(
        self, document_id: str, tenant_id: str, source_path: str
    ) -> Dict[str, Any]:
        """Process a single document through the pipeline"""
        initial_state: DocumentState = {
            "document_id": document_id,
            "tenant_id": tenant_id,
            "source_path": source_path,
            "current_state": ProcessingState.QUEUED,
            "processing_started_at": None,
            "processing_completed_at": None,
            "content": None,
            "metadata": {},
            "document_type": None,
            "classification_confidence": None,
            "extraction_schema": None,
            "extracted_entities": [],
            "extracted_relationships": [],
            "chunks": [],
            "chunk_relationships": [],
            "chunking_strategy": None,
            "embeddings": [],
            "embedding_model": None,
            "neo4j_nodes": [],
            "neo4j_edges": [],
            "qdrant_ids": [],
            "errors": [],
            "retry_count": 0,
            "max_retries": 3,
        }

        # Run the workflow
        result = await self.workflow.ainvoke(
            initial_state, {"configurable": {"thread_id": document_id}}
        )

        return result


# Create singleton workflow instance
workflow = RAGProcessingWorkflow()


async def process_document_queue():
    """Main entry point - continuously process documents from queue"""
    logger.info("Starting RAG document processor")

    while True:
        try:
            # Get next document from queue
            next_doc = await queue_monitor.get_next_document()

            if next_doc:
                logger.info(f"Processing document: {next_doc['id']}")

                # Process through workflow
                result = await workflow.process_document(
                    document_id=next_doc["id"],
                    tenant_id=next_doc["tenant_id"],
                    source_path=next_doc["source_path"],
                )

                if result["current_state"] == ProcessingState.COMPLETED:
                    logger.info(f"Successfully processed document {next_doc['id']}")
                else:
                    logger.error(f"Failed to process document {next_doc['id']}")
            else:
                # No documents in queue, wait
                await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Queue processing error: {str(e)}")
            await asyncio.sleep(30)


if __name__ == "__main__":
    # Run the queue processor
    asyncio.run(process_document_queue())
