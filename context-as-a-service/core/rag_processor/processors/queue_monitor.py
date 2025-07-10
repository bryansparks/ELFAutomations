"""
Queue Monitor Agent
Monitors the document processing queue and manages document status updates.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from shared.mcp import MCPClient
from shared.utils import get_supabase_client

logger = logging.getLogger(__name__)


class RAGQueueMonitorAgent:
    """Agent responsible for monitoring document processing queue"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.mcp_client = MCPClient()
        self.name = "queue_monitor"
        self.role = "Queue Monitor"
        self.backstory = "An efficient coordinator that ensures documents flow smoothly through the pipeline"

    async def get_next_document(self) -> Optional[Dict[str, Any]]:
        """Get the next document from the processing queue"""
        try:
            # Get highest priority pending document
            result = (
                self.supabase.table("rag_processing_queue")
                .select("*, rag_documents!inner(*)")
                .eq("status", "pending")
                .order("priority", desc=True)
                .order("created_at")
                .limit(1)
                .execute()
            )

            if result.data and len(result.data) > 0:
                queue_item = result.data[0]
                document = queue_item["rag_documents"]

                # Mark as processing
                self.supabase.table("rag_processing_queue").update(
                    {
                        "status": "processing",
                        "started_at": datetime.now().isoformat(),
                        "attempts": queue_item["attempts"] + 1,
                    }
                ).eq("id", queue_item["id"]).execute()

                logger.info(f"Retrieved document {document['id']} from queue")

                return {
                    "id": document["id"],
                    "tenant_id": document["tenant_id"],
                    "source_path": document["source_path"],
                    "source_type": document["source_type"],
                    "source_id": document["source_id"],
                    "filename": document["filename"],
                    "mime_type": document["mime_type"],
                    "queue_id": queue_item["id"],
                    "priority": queue_item["priority"],
                    "processor_type": queue_item["processor_type"],
                }

            return None

        except Exception as e:
            logger.error(f"Error getting next document: {str(e)}")
            return None

    async def fetch_document(self, document_id: str) -> Dict[str, Any]:
        """Fetch document content and metadata"""
        try:
            # Get document record
            doc_result = (
                self.supabase.table("rag_documents")
                .select("*")
                .eq("id", document_id)
                .single()
                .execute()
            )

            document = doc_result.data

            # Fetch content based on source type
            if document["source_type"] == "google_drive":
                # Use Google Drive MCP to get document
                content = await self._fetch_from_google_drive(document["source_id"])

            elif document["source_type"] == "minio":
                # Fetch from MinIO
                content = await self._fetch_from_minio(document["source_path"])

            else:
                raise ValueError(f"Unknown source type: {document['source_type']}")

            return {
                "content": content,
                "metadata": {
                    "filename": document["filename"],
                    "mime_type": document["mime_type"],
                    "size_bytes": document["size_bytes"],
                    "source_type": document["source_type"],
                    "extracted_metadata": document.get("extracted_metadata", {}),
                },
            }

        except Exception as e:
            logger.error(f"Error fetching document {document_id}: {str(e)}")
            raise

    async def _fetch_from_google_drive(self, file_id: str) -> str:
        """Fetch document content from Google Drive"""
        try:
            # Download to temporary location
            temp_path = f"/tmp/{file_id}.tmp"

            result = await self.mcp_client.call_tool(
                "google-drive-watcher",
                "download_document",
                {"fileId": file_id, "outputPath": temp_path},
            )

            # Read content
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Clean up
            import os

            os.remove(temp_path)

            return content

        except Exception as e:
            logger.error(f"Error fetching from Google Drive: {str(e)}")
            raise

    async def _fetch_from_minio(self, path: str) -> str:
        """Fetch document content from MinIO"""
        # TODO: Implement MinIO fetch
        raise NotImplementedError("MinIO fetch not yet implemented")

    async def update_status(
        self, document_id: str, status: str, metadata: Dict[str, Any] = None
    ) -> None:
        """Update document processing status"""
        try:
            # Update document status
            update_data = {"status": status, "updated_at": datetime.now().isoformat()}

            if metadata:
                if status == "processing":
                    update_data["processing_started_at"] = metadata.get("started_at")
                elif status == "completed":
                    update_data["processing_completed_at"] = metadata.get(
                        "completed_at"
                    )
                    update_data["processing_error"] = None
                elif status == "failed":
                    update_data["processing_error"] = metadata

            self.supabase.table("rag_documents").update(update_data).eq(
                "id", document_id
            ).execute()

            # Update queue status if we have queue_id
            if metadata and "queue_id" in metadata:
                queue_update = {
                    "status": "completed" if status == "completed" else status,
                    "completed_at": datetime.now().isoformat()
                    if status == "completed"
                    else None,
                }

                if status == "failed":
                    queue_update["last_error"] = str(
                        metadata.get("error", "Unknown error")
                    )

                self.supabase.table("rag_processing_queue").update(queue_update).eq(
                    "id", metadata["queue_id"]
                ).execute()

            logger.info(f"Updated document {document_id} status to {status}")

        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")

    async def requeue_document(self, document_id: str, reason: str) -> None:
        """Requeue a document for processing"""
        try:
            # Find the queue item
            queue_result = (
                self.supabase.table("rag_processing_queue")
                .select("*")
                .eq("document_id", document_id)
                .eq("status", "processing")
                .single()
                .execute()
            )

            if queue_result.data:
                queue_item = queue_result.data

                # Check if we've exceeded max attempts
                if queue_item["attempts"] >= queue_item["max_attempts"]:
                    await self.update_status(
                        document_id,
                        "failed",
                        {
                            "error": f"Max attempts exceeded. Last error: {reason}",
                            "queue_id": queue_item["id"],
                        },
                    )
                else:
                    # Requeue
                    self.supabase.table("rag_processing_queue").update(
                        {
                            "status": "pending",
                            "last_error": reason,
                            "scheduled_at": datetime.now().isoformat(),
                        }
                    ).eq("id", queue_item["id"]).execute()

                    logger.info(
                        f"Requeued document {document_id} (attempt {queue_item['attempts'] + 1})"
                    )

        except Exception as e:
            logger.error(f"Error requeuing document: {str(e)}")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            # Count by status
            pending = (
                self.supabase.table("rag_processing_queue")
                .select("id", count="exact")
                .eq("status", "pending")
                .execute()
            )

            processing = (
                self.supabase.table("rag_processing_queue")
                .select("id", count="exact")
                .eq("status", "processing")
                .execute()
            )

            completed = (
                self.supabase.table("rag_processing_queue")
                .select("id", count="exact")
                .eq("status", "completed")
                .execute()
            )

            failed = (
                self.supabase.table("rag_processing_queue")
                .select("id", count="exact")
                .eq("status", "failed")
                .execute()
            )

            return {
                "pending": pending.count,
                "processing": processing.count,
                "completed": completed.count,
                "failed": failed.count,
                "total": pending.count
                + processing.count
                + completed.count
                + failed.count,
            }

        except Exception as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            return {"error": str(e)}
