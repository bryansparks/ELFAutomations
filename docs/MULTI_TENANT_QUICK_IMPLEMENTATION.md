# Multi-Tenant Quick Implementation Guide

## Immediate Implementation Steps

### 1. Update Document Model

```python
# elf_automations/shared/models/document.py
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class TenantContext:
    """Defines tenant isolation boundaries"""
    tenant_id: str          # e.g., "acme_corp"
    workspace: str          # e.g., "finance"
    doc_type: str          # e.g., "invoice"
    context: Optional[str]  # e.g., "2024_q1" or "vendor_xyz"

    def get_collection_name(self) -> str:
        """Generate consistent collection name"""
        parts = [self.tenant_id, self.workspace, self.doc_type]
        if self.context:
            parts.append(self.context)
        return "_".join(parts).lower().replace(" ", "_")

    def get_neo4j_labels(self) -> List[str]:
        """Generate Neo4j labels for this context"""
        labels = [
            "Document",
            f"Tenant_{self.tenant_id}",
            f"Workspace_{self.workspace}",
            f"Type_{self.doc_type}"
        ]
        if self.context:
            labels.append(f"Context_{self.context}")
        return labels

@dataclass
class Document:
    """Enhanced document with tenant context"""
    id: str
    content: str
    tenant_context: TenantContext
    metadata: Dict
    created_at: datetime = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow()
```

### 2. Create Collection Manager MCP

```bash
# Use the MCP factory to create a collection management MCP
cd tools
python mcp_factory.py

# Name: collection-manager
# Description: Manages multi-tenant collections across storage systems
# Tools to add:
# - create_collection
# - list_collections
# - delete_collection
# - migrate_collection
# - get_collection_stats
```

### 3. RAG Team Enhancement

```python
# teams/rag-free-agent-team/agents/document_intake_agent.py
def process_document(self, document: Document, tenant_context: TenantContext):
    """Process document with tenant isolation"""

    # Validate tenant access
    if not self.validate_tenant_access(tenant_context):
        raise PermissionError(f"No access to tenant {tenant_context.tenant_id}")

    # Ensure collections exist
    self._ensure_collections(tenant_context)

    # Process based on document type
    processor = self.get_processor(tenant_context.doc_type)
    result = processor.process(document)

    # Store with tenant isolation
    self._store_with_isolation(result, tenant_context)

    return result

def _ensure_collections(self, context: TenantContext):
    """Ensure all required collections exist"""

    # Qdrant collection
    collection_name = context.get_collection_name()
    if not self.qdrant.collection_exists(collection_name):
        self.qdrant.create_collection(
            collection_name,
            vectors_config=VectorParams(size=1536)
        )

    # Neo4j indexes for labels
    labels = context.get_neo4j_labels()
    for label in labels:
        self.neo4j.create_index_if_not_exists(label)

    # Supabase partitions
    self.supabase.ensure_partition(context.tenant_id)
```

### 4. Update Team Factory for Multi-Tenancy

```python
# tools/team_factory.py - Add to the team generation

def _generate_multi_tenant_support(self, team_name: str) -> str:
    """Generate multi-tenant aware code for teams"""
    return f'''
# Multi-tenant support
from elf_automations.shared.models.document import TenantContext

class {team_name}Agent:
    def __init__(self, tenant_context: TenantContext = None):
        self.tenant_context = tenant_context

    def set_tenant_context(self, context: TenantContext):
        """Set tenant context for all operations"""
        self.tenant_context = context

    def _get_collection(self, doc_type: str) -> str:
        """Get collection name for current tenant"""
        if not self.tenant_context:
            raise ValueError("Tenant context not set")
        return self.tenant_context.get_collection_name()
'''
```

### 5. Example Workflow Implementation

```python
# scripts/test_multi_tenant_rag.py
#!/usr/bin/env python3
"""Test multi-tenant RAG implementation"""

from elf_automations.shared.models.document import Document, TenantContext
from teams.rag_free_agent_team import RAGFreeAgentTeam

# Create tenant contexts
acme_invoices = TenantContext(
    tenant_id="acme_corp",
    workspace="finance",
    doc_type="invoice",
    context="2024_q1"
)

globex_invoices = TenantContext(
    tenant_id="globex_inc",
    workspace="accounting",
    doc_type="invoice",
    context="vendor_abc"
)

# Initialize RAG team
rag_team = RAGFreeAgentTeam()

# Process Acme invoice
acme_doc = Document(
    id="inv_001",
    content="Invoice from Software Vendor...",
    tenant_context=acme_invoices,
    metadata={"amount": 5000, "vendor": "TechCo"}
)
rag_team.process_document(acme_doc)

# Process Globex invoice
globex_doc = Document(
    id="inv_002",
    content="Invoice from Consulting Firm...",
    tenant_context=globex_invoices,
    metadata={"amount": 15000, "vendor": "ConsultCo"}
)
rag_team.process_document(globex_doc)

# Search within tenant boundaries
acme_results = rag_team.search(
    query="software expenses",
    tenant_context=acme_invoices
)

# This should return ZERO results (different tenant)
globex_results = rag_team.search(
    query="software expenses",
    tenant_context=globex_invoices
)
```

## Configuration Examples

### Environment Variables
```bash
# Default tenant for development
DEFAULT_TENANT_ID=dev_tenant
DEFAULT_WORKSPACE=development

# Multi-tenant mode
ENABLE_MULTI_TENANCY=true
ENFORCE_TENANT_ISOLATION=true

# Collection naming strategy
COLLECTION_NAMING_PATTERN={tenant}_{workspace}_{type}_{context}
```

### Team Configuration
```yaml
# teams/rag-free-agent-team/config/multi_tenant.yaml
multi_tenancy:
  enabled: true
  isolation_level: strict  # strict, workspace, tenant

  collection_strategies:
    invoice:
      partition_by: [quarter, vendor]
      retention_days: 730

    contract:
      partition_by: [year, party]
      retention_days: 2555  # 7 years

    email:
      partition_by: [month]
      retention_days: 365

  access_control:
    require_explicit_permission: true
    audit_all_access: true
```

## Common Patterns

### 1. Quarterly Financial Isolation
```python
def get_quarterly_context(tenant_id: str, year: int, quarter: int):
    return TenantContext(
        tenant_id=tenant_id,
        workspace="finance",
        doc_type="invoice",
        context=f"{year}_q{quarter}"
    )
```

### 2. Project-Based Isolation
```python
def get_project_context(tenant_id: str, project_code: str, doc_type: str):
    return TenantContext(
        tenant_id=tenant_id,
        workspace=f"project_{project_code}",
        doc_type=doc_type,
        context=None  # All project docs together
    )
```

### 3. Vendor-Specific Collections
```python
def get_vendor_context(tenant_id: str, vendor_id: str):
    return TenantContext(
        tenant_id=tenant_id,
        workspace="procurement",
        doc_type="invoice",
        context=f"vendor_{vendor_id}"
    )
```

## Migration Script

```python
# scripts/migrate_to_multi_tenant.py
"""Migrate existing data to multi-tenant structure"""

def migrate_existing_collections():
    # Get all existing collections
    collections = qdrant.get_collections()

    for collection in collections:
        # Parse existing name
        if "_" not in collection.name:
            # Assume single tenant
            tenant_id = "default_tenant"
            workspace = "default"
            doc_type = collection.name
        else:
            # Try to parse
            parts = collection.name.split("_")
            # Implement your parsing logic

        # Create new tenant context
        context = TenantContext(
            tenant_id=tenant_id,
            workspace=workspace,
            doc_type=doc_type
        )

        # Create new collection
        new_name = context.get_collection_name()

        # Migrate data
        migrate_collection_data(collection.name, new_name)
```

## Testing Multi-Tenancy

```python
# tests/test_multi_tenant_isolation.py
import pytest
from elf_automations.shared.models.document import TenantContext

def test_tenant_isolation():
    """Ensure complete isolation between tenants"""

    # Create two different tenant contexts
    tenant_a = TenantContext("tenant_a", "workspace1", "invoice")
    tenant_b = TenantContext("tenant_b", "workspace1", "invoice")

    # Store document for tenant A
    doc_a = Document("doc1", "Content A", tenant_a, {})
    storage.store_document(doc_a)

    # Search as tenant B - should find nothing
    results = storage.search("Content A", tenant_b)
    assert len(results) == 0

    # Search as tenant A - should find document
    results = storage.search("Content A", tenant_a)
    assert len(results) == 1

def test_workspace_isolation():
    """Test isolation within same tenant"""

    # Same tenant, different workspaces
    workspace_1 = TenantContext("acme", "finance", "invoice")
    workspace_2 = TenantContext("acme", "hr", "invoice")

    # Documents should be isolated by workspace
    # ... test implementation
```

This multi-tenant architecture ensures complete data isolation while maintaining flexibility for different use cases. The key is consistent naming and labeling across all storage systems.
