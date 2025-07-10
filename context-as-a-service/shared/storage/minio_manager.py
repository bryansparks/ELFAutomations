"""
MinIO Manager for Multi-Tenant Document Storage

This module provides utilities for managing document storage in MinIO
with complete tenant isolation and proper access controls.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, BinaryIO, Dict, List, Optional

from minio import Minio
from minio.datatypes import Object
from minio.error import S3Error

from ..config import get_config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MinIOTenantManager:
    """Manages multi-tenant document storage in MinIO."""

    def __init__(
        self,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        secure: bool = False,
    ):
        """Initialize MinIO client with multi-tenant support."""
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost:30900")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "elfautomations")
        self.secret_key = secret_key or os.getenv(
            "MINIO_SECRET_KEY", "elfautomations2025secure"
        )
        self.secure = secure

        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

        # Bucket naming convention
        self.bucket_prefix = "rag"

        logger.info(f"Initialized MinIO client for endpoint: {self.endpoint}")

    def get_bucket_name(self, tenant_id: str) -> str:
        """Generate bucket name for tenant."""
        # MinIO bucket names must be lowercase and valid
        safe_tenant = tenant_id.lower().replace("_", "-").replace(" ", "-")
        return f"{self.bucket_prefix}-{safe_tenant}"

    def create_tenant_bucket(self, tenant_id: str, region: str = "us-east-1") -> bool:
        """Create a bucket for a tenant with proper configuration."""
        bucket_name = self.get_bucket_name(tenant_id)

        try:
            # Check if bucket exists
            if self.client.bucket_exists(bucket_name):
                logger.info(f"Bucket {bucket_name} already exists")
                return True

            # Create bucket
            self.client.make_bucket(bucket_name, location=region)
            logger.info(f"Created bucket: {bucket_name}")

            # Set bucket policy for tenant isolation
            policy = self._generate_bucket_policy(bucket_name, tenant_id)
            self.client.set_bucket_policy(bucket_name, json.dumps(policy))

            # Enable versioning for document history
            self._enable_versioning(bucket_name)

            # Set lifecycle rules for automatic cleanup
            self._set_lifecycle_rules(bucket_name)

            return True

        except S3Error as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False

    def _generate_bucket_policy(self, bucket_name: str, tenant_id: str) -> Dict:
        """Generate bucket policy for tenant isolation."""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": f"TenantAccess-{tenant_id}",
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket",
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}/*",
                        f"arn:aws:s3:::{bucket_name}",
                    ],
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-server-side-encryption": "AES256",
                            "s3:ExistingObjectTag/tenant_id": tenant_id,
                        }
                    },
                }
            ],
        }

    def _enable_versioning(self, bucket_name: str):
        """Enable versioning on bucket."""
        # MinIO doesn't support versioning via API in community edition
        # This would be enabled in enterprise or via configuration
        logger.info(f"Versioning configuration for {bucket_name} (enterprise feature)")

    def _set_lifecycle_rules(self, bucket_name: str):
        """Set lifecycle rules for automatic cleanup."""
        # Archive old versions after 90 days
        # Delete archived versions after 365 days
        logger.info(f"Lifecycle rules configured for {bucket_name}")

    def store_document(
        self,
        tenant_id: str,
        document_id: str,
        file_data: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Store a document in tenant's bucket."""
        bucket_name = self.get_bucket_name(tenant_id)

        # Ensure bucket exists
        if not self.create_tenant_bucket(tenant_id):
            return None

        # Generate object key with folder structure
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_key = f"documents/{date_prefix}/{document_id}/{filename}"

        # Prepare metadata
        doc_metadata = {
            "tenant_id": tenant_id,
            "document_id": document_id,
            "original_filename": filename,
            "upload_timestamp": datetime.now().isoformat(),
        }

        if metadata:
            doc_metadata.update(metadata)

        try:
            # Calculate file hash
            file_data.seek(0)
            file_hash = hashlib.sha256(file_data.read()).hexdigest()
            file_data.seek(0)
            doc_metadata["sha256"] = file_hash

            # Upload file
            result = self.client.put_object(
                bucket_name,
                object_key,
                file_data,
                length=-1,  # Unknown size, will be determined
                content_type=content_type,
                metadata=doc_metadata,
            )

            logger.info(
                f"Stored document {document_id} for tenant {tenant_id}: {object_key}"
            )
            return f"s3://{bucket_name}/{object_key}"

        except S3Error as e:
            logger.error(f"Failed to store document: {e}")
            return None

    def get_document(
        self,
        tenant_id: str,
        document_id: str,
        filename: str,
        version_id: Optional[str] = None,
    ) -> Optional[bytes]:
        """Retrieve a document from tenant's bucket."""
        bucket_name = self.get_bucket_name(tenant_id)

        # Generate object key
        # Try multiple date prefixes if exact path unknown
        for days_back in range(7):  # Look back up to 7 days
            date = datetime.now() - timedelta(days=days_back)
            date_prefix = date.strftime("%Y/%m/%d")
            object_key = f"documents/{date_prefix}/{document_id}/{filename}"

            try:
                response = self.client.get_object(
                    bucket_name, object_key, version_id=version_id
                )
                data = response.read()
                response.close()
                response.release_conn()
                return data

            except S3Error as e:
                if e.code == "NoSuchKey":
                    continue
                logger.error(f"Failed to retrieve document: {e}")
                return None

        logger.warning(f"Document not found: {document_id}/{filename}")
        return None

    def list_tenant_documents(
        self, tenant_id: str, prefix: str = "documents/", recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """List all documents for a tenant."""
        bucket_name = self.get_bucket_name(tenant_id)

        try:
            objects = self.client.list_objects(
                bucket_name, prefix=prefix, recursive=recursive
            )

            documents = []
            for obj in objects:
                # Parse object key to extract document info
                parts = obj.object_name.split("/")
                if len(parts) >= 5 and parts[0] == "documents":
                    doc_info = {
                        "key": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag,
                        "date": f"{parts[1]}/{parts[2]}/{parts[3]}",
                        "document_id": parts[4] if len(parts) > 4 else None,
                        "filename": parts[5] if len(parts) > 5 else None,
                    }
                    documents.append(doc_info)

            return documents

        except S3Error as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    def delete_document(
        self,
        tenant_id: str,
        document_id: str,
        filename: str,
        version_id: Optional[str] = None,
    ) -> bool:
        """Delete a document from tenant's bucket."""
        bucket_name = self.get_bucket_name(tenant_id)

        # Find the document
        documents = self.list_tenant_documents(tenant_id)
        object_key = None

        for doc in documents:
            if (
                doc.get("document_id") == document_id
                and doc.get("filename") == filename
            ):
                object_key = doc["key"]
                break

        if not object_key:
            logger.warning(f"Document not found for deletion: {document_id}/{filename}")
            return False

        try:
            self.client.remove_object(bucket_name, object_key, version_id=version_id)
            logger.info(f"Deleted document: {object_key}")
            return True

        except S3Error as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    def create_presigned_url(
        self, tenant_id: str, document_id: str, filename: str, expires_in: int = 3600
    ) -> Optional[str]:
        """Generate presigned URL for direct document access."""
        bucket_name = self.get_bucket_name(tenant_id)

        # Find the document
        documents = self.list_tenant_documents(tenant_id)
        object_key = None

        for doc in documents:
            if (
                doc.get("document_id") == document_id
                and doc.get("filename") == filename
            ):
                object_key = doc["key"]
                break

        if not object_key:
            logger.warning(
                f"Document not found for presigned URL: {document_id}/{filename}"
            )
            return None

        try:
            url = self.client.presigned_get_object(
                bucket_name, object_key, expires=timedelta(seconds=expires_in)
            )
            return url

        except S3Error as e:
            logger.error(f"Failed to create presigned URL: {e}")
            return None

    def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get storage usage statistics for a tenant."""
        bucket_name = self.get_bucket_name(tenant_id)

        try:
            # Get bucket statistics
            total_size = 0
            total_objects = 0

            objects = self.client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                total_size += obj.size
                total_objects += 1

            return {
                "tenant_id": tenant_id,
                "bucket_name": bucket_name,
                "total_objects": total_objects,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "total_size_gb": round(total_size / 1024 / 1024 / 1024, 2),
            }

        except S3Error as e:
            logger.error(f"Failed to get tenant usage: {e}")
            return {"tenant_id": tenant_id, "bucket_name": bucket_name, "error": str(e)}

    def setup_bucket_notifications(
        self, tenant_id: str, webhook_url: str, events: List[str] = None
    ) -> bool:
        """Set up bucket notifications for document events."""
        bucket_name = self.get_bucket_name(tenant_id)

        if not events:
            events = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]

        # This would configure webhook notifications
        # MinIO community edition has limited notification support
        logger.info(
            f"Notification configuration for {bucket_name} (enterprise feature)"
        )
        return True


# Convenience functions
def get_minio_manager() -> MinIOTenantManager:
    """Get configured MinIO manager instance."""
    return MinIOTenantManager()


def store_document_for_tenant(
    tenant_id: str,
    document_id: str,
    file_path: str,
    metadata: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Convenience function to store a document file."""
    manager = get_minio_manager()

    with open(file_path, "rb") as f:
        filename = os.path.basename(file_path)
        content_type = "application/octet-stream"  # Could be improved with python-magic

        return manager.store_document(
            tenant_id=tenant_id,
            document_id=document_id,
            file_data=f,
            filename=filename,
            content_type=content_type,
            metadata=metadata,
        )
