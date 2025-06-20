"""
Storage utilities for ElfAutomations.

This module provides interfaces for various storage systems used in the platform.
"""

from .minio_manager import MinIOTenantManager, get_minio_manager, store_document_for_tenant

__all__ = [
    "MinIOTenantManager",
    "get_minio_manager",
    "store_document_for_tenant"
]