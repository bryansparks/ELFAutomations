"""
Storage Coordinator Agent
Manages storage across multiple systems (Qdrant, Neo4j, Supabase) and ensures consistency.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from shared.utils import get_supabase_client

logger = logging.getLogger(__name__)


class RAGStorageCoordinatorAgent:
    """Agent responsible for coordinating storage across multiple systems"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.name = "storage_coordinator"
        self.role = "Storage Coordinator"
        self.backstory = "A meticulous organizer who ensures nothing is lost and everything is findable"

        # Qdrant configuration
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.qdrant_client = None

        # Collection names
        self.collections = {
            "documents": "document_embeddings",
            "entities": "entity_embeddings",
        }

    async def initialize(self):
        """Initialize connections"""
        if not self.qdrant_client:
            self.qdrant_client = QdrantClient(
                url=self.qdrant_url, api_key=self.qdrant_api_key
            )

            # Ensure collections exist
            await self._ensure_collections()

    async def _ensure_collections(self):
        """Ensure Qdrant collections exist"""
        for collection_type, collection_name in self.collections.items():
            try:
                # Check if collection exists
                collections = await self.qdrant_client.get_collections()
                collection_names = [c.name for c in collections.collections]

                if collection_name not in collection_names:
                    # Create collection with appropriate vector size
                    vector_size = 3072 if collection_type == "documents" else 1536

                    await self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=vector_size, distance=Distance.COSINE
                        ),
                    )

                    logger.info(f"Created Qdrant collection: {collection_name}")

            except Exception as e:
                logger.error(f"Error ensuring collection {collection_name}: {str(e)}")

    async def store_embeddings(
        self,
        tenant_id: str,
        document_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Store embeddings in Qdrant with metadata"""
        try:
            await self.initialize()

            # Prepare points for Qdrant
            points = []
            vector_ids = []

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Generate unique ID
                point_id = f"{document_id}_{chunk['chunk_index']}"
                vector_ids.append(point_id)

                # Prepare payload with metadata
                payload = {
                    "tenant_id": tenant_id,
                    "document_id": document_id,
                    "chunk_index": chunk["chunk_index"],
                    "chunk_type": chunk.get("type", "unknown"),
                    "content": chunk["content"][:1000],  # Truncate for storage
                    "token_count": chunk.get("token_count", 0),
                    "entities": chunk.get("entities", []),
                    "entity_count": chunk.get("entity_count", 0),
                    "created_at": datetime.now().isoformat(),
                }

                # Add heading for structural chunks
                if chunk.get("heading"):
                    payload["heading"] = chunk["heading"]

                # Create point
                point = PointStruct(
                    id=point_id, vector=embedding["embedding"], payload=payload
                )

                points.append(point)

            # Batch upload to Qdrant
            collection_name = self.collections["documents"]
            await self.qdrant_client.upsert(
                collection_name=collection_name, points=points
            )

            # Update chunk records in Supabase
            for chunk, vector_id in zip(chunks, vector_ids):
                if "id" in chunk:
                    self.supabase.table("rag_document_chunks").update(
                        {"vector_id": vector_id, "collection_name": collection_name}
                    ).eq("id", chunk["id"]).execute()

            logger.info(f"Stored {len(points)} embeddings in Qdrant")

            return {
                "vector_ids": vector_ids,
                "collection": collection_name,
                "total_stored": len(points),
            }

        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            raise

    async def store_entity_embeddings(
        self, tenant_id: str, entity_embeddings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Store entity embeddings in Qdrant"""
        try:
            await self.initialize()

            points = []
            vector_ids = []

            for entity_emb in entity_embeddings:
                entity = entity_emb["entity"]

                # Generate unique ID
                point_id = (
                    f"entity_{tenant_id}_{entity['type']}_{entity['normalized_value']}"
                )
                vector_ids.append(point_id)

                # Prepare payload
                payload = {
                    "tenant_id": tenant_id,
                    "entity_type": entity["type"],
                    "entity_value": entity["value"],
                    "normalized_value": entity.get("normalized_value", entity["value"]),
                    "properties": entity.get("properties", {}),
                    "confidence": entity.get("confidence", 1.0),
                    "created_at": datetime.now().isoformat(),
                }

                # Create point
                point = PointStruct(
                    id=point_id, vector=entity_emb["embedding"], payload=payload
                )

                points.append(point)

            # Upload to Qdrant
            collection_name = self.collections["entities"]
            await self.qdrant_client.upsert(
                collection_name=collection_name, points=points
            )

            logger.info(f"Stored {len(points)} entity embeddings")

            return {
                "vector_ids": vector_ids,
                "collection": collection_name,
                "total_stored": len(points),
            }

        except Exception as e:
            logger.error(f"Error storing entity embeddings: {str(e)}")
            raise

    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        tenant_id: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks in Qdrant"""
        try:
            await self.initialize()

            # Build filter conditions
            must_conditions = [{"key": "tenant_id", "match": {"value": tenant_id}}]

            if filters:
                for key, value in filters.items():
                    must_conditions.append({"key": key, "match": {"value": value}})

            # Search in Qdrant
            search_result = await self.qdrant_client.search(
                collection_name=self.collections["documents"],
                query_vector=query_embedding,
                limit=limit,
                query_filter={"must": must_conditions},
            )

            # Format results
            results = []
            for hit in search_result:
                results.append(
                    {
                        "id": hit.id,
                        "score": hit.score,
                        "document_id": hit.payload.get("document_id"),
                        "chunk_index": hit.payload.get("chunk_index"),
                        "content": hit.payload.get("content"),
                        "metadata": hit.payload,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error searching chunks: {str(e)}")
            return []

    async def coordinate_storage(
        self, document_id: str, storage_operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Coordinate storage operations across systems"""
        results = {"successful": [], "failed": [], "rollback_needed": False}

        completed_operations = []

        try:
            # Execute operations in order
            for operation in storage_operations:
                op_type = operation["type"]
                op_data = operation["data"]

                if op_type == "qdrant_store":
                    result = await self.store_embeddings(**op_data)
                    completed_operations.append(("qdrant", result))

                elif op_type == "neo4j_update":
                    # Neo4j operations handled by graph_builder
                    completed_operations.append(("neo4j", {"status": "delegated"}))

                elif op_type == "supabase_update":
                    # Update document status
                    self.supabase.table("rag_documents").update(
                        {
                            "storage_locations": operation.get("storage_locations", {}),
                            "updated_at": datetime.now().isoformat(),
                        }
                    ).eq("id", document_id).execute()
                    completed_operations.append(("supabase", {"status": "updated"}))

                results["successful"].append(op_type)

        except Exception as e:
            logger.error(f"Storage coordination error: {str(e)}")
            results["failed"].append(
                {
                    "operation": op_type if "op_type" in locals() else "unknown",
                    "error": str(e),
                }
            )
            results["rollback_needed"] = True

            # Attempt rollback
            await self._rollback_operations(completed_operations)

        return results

    async def _rollback_operations(self, completed_operations: List[Tuple[str, Any]]):
        """Rollback completed operations on failure"""
        logger.warning("Attempting to rollback storage operations")

        for system, result in reversed(completed_operations):
            try:
                if system == "qdrant" and "vector_ids" in result:
                    # Delete vectors
                    await self.qdrant_client.delete(
                        collection_name=result["collection"],
                        points_selector={
                            "filter": {
                                "must": [
                                    {
                                        "key": "id",
                                        "match": {"any": result["vector_ids"]},
                                    }
                                ]
                            }
                        },
                    )
                    logger.info(
                        f"Rolled back Qdrant vectors: {len(result['vector_ids'])}"
                    )

            except Exception as e:
                logger.error(f"Rollback failed for {system}: {str(e)}")

    async def verify_storage_integrity(
        self, document_id: str, tenant_id: str
    ) -> Dict[str, Any]:
        """Verify storage integrity across systems"""
        issues = []

        try:
            # Check Supabase records
            doc_result = (
                self.supabase.table("rag_documents")
                .select("*")
                .eq("id", document_id)
                .single()
                .execute()
            )

            if not doc_result.data:
                issues.append("Document not found in Supabase")

            # Check chunks
            chunks_result = (
                self.supabase.table("rag_document_chunks")
                .select("*")
                .eq("document_id", document_id)
                .execute()
            )

            chunk_count = len(chunks_result.data) if chunks_result.data else 0

            # Check Qdrant vectors
            await self.initialize()

            qdrant_filter = {
                "must": [
                    {"key": "tenant_id", "match": {"value": tenant_id}},
                    {"key": "document_id", "match": {"value": document_id}},
                ]
            }

            # Count vectors
            vector_count = 0
            try:
                # Search with dummy vector to get count
                dummy_vector = [0.0] * 3072
                search_result = await self.qdrant_client.search(
                    collection_name=self.collections["documents"],
                    query_vector=dummy_vector,
                    limit=1000,
                    query_filter=qdrant_filter,
                )
                vector_count = len(search_result)
            except:
                pass

            # Compare counts
            if chunk_count != vector_count:
                issues.append(
                    f"Chunk/vector mismatch: {chunk_count} chunks, {vector_count} vectors"
                )

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "stats": {"chunks": chunk_count, "vectors": vector_count},
            }

        except Exception as e:
            logger.error(f"Integrity check error: {str(e)}")
            return {"valid": False, "issues": [str(e)], "stats": {}}

    async def update_document_status(
        self, document_id: str, status: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update document status in Supabase"""
        try:
            update_data = {"status": status, "updated_at": datetime.now().isoformat()}

            if metadata:
                update_data.update(metadata)

            self.supabase.table("rag_documents").update(update_data).eq(
                "id", document_id
            ).execute()

            logger.info(f"Updated document {document_id} status to {status}")

        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")

    async def handle_storage_errors(
        self, document_id: str, errors: List[Dict[str, Any]]
    ) -> None:
        """Handle and log storage errors"""
        try:
            # Log to extraction history
            self.supabase.table("rag_extraction_history").insert(
                {
                    "document_id": document_id,
                    "extraction_type": "storage",
                    "status": "failed",
                    "error_details": {"errors": errors},
                    "created_at": datetime.now().isoformat(),
                }
            ).execute()

            # Update document with error
            self.supabase.table("rag_documents").update(
                {"status": "failed", "processing_error": {"storage_errors": errors}}
            ).eq("id", document_id).execute()

        except Exception as e:
            logger.error(f"Error logging storage errors: {str(e)}")

    async def log_error(
        self, document_id: str, error: Dict[str, Any], state: str, retry_count: int
    ) -> None:
        """Log processing error"""
        try:
            error_record = {
                "document_id": document_id,
                "stage": error.get("stage", state),
                "error_message": error.get("error", "Unknown error"),
                "retry_count": retry_count,
                "timestamp": error.get("timestamp", datetime.now()).isoformat(),
                "details": error,
            }

            # Log to a dedicated error table if it exists
            # For now, update document record
            self.supabase.table("rag_documents").update(
                {"processing_error": error_record}
            ).eq("id", document_id).execute()

        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")
