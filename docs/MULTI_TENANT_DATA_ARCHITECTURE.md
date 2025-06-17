# Multi-Tenant Data Architecture for ElfAutomations

## Overview
A comprehensive multi-tenancy strategy across VectorDB (Qdrant), GraphDB (Neo4j), and SQL (Supabase) to ensure data isolation, security, and efficient querying.

## Tenancy Hierarchy

```
Organization (Top Level)
├── Workspace (Business Unit/Department)
│   ├── Project (Specific Initiative)
│   │   ├── Collection (Document Type + Context)
│   │   │   ├── Documents
│   │   │   ├── Metadata
│   │   │   └── Relationships
```

## Multi-Tenant Implementation by Storage System

### 1. Qdrant (VectorDB) - Native Collections

```python
class QdrantTenantManager:
    """Manages multi-tenant collections in Qdrant"""

    def __init__(self, client: QdrantClient):
        self.client = client

    def get_collection_name(self, tenant_id: str, workspace: str,
                          doc_type: str, context: str = None) -> str:
        """Generate consistent collection names"""
        # Pattern: {tenant}_{workspace}_{type}_{context}
        parts = [tenant_id, workspace, doc_type]
        if context:
            parts.append(context)
        return "_".join(parts).lower().replace(" ", "_")

    def create_tenant_collection(self, tenant_id: str, workspace: str,
                               doc_type: str, context: str = None):
        """Create isolated collection for tenant+type+context"""
        collection_name = self.get_collection_name(
            tenant_id, workspace, doc_type, context
        )

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,  # OpenAI embeddings
                distance=Distance.COSINE
            ),
            # Metadata for multi-tenant management
            payload_schema={
                "tenant_id": PayloadSchemaType.KEYWORD,
                "workspace": PayloadSchemaType.KEYWORD,
                "doc_type": PayloadSchemaType.KEYWORD,
                "context": PayloadSchemaType.KEYWORD,
                "created_at": PayloadSchemaType.DATETIME,
                "access_level": PayloadSchemaType.KEYWORD
            }
        )

    def search_tenant_data(self, tenant_id: str, workspace: str,
                          query_vector: List[float], doc_type: str = None,
                          context: str = None, cross_context: bool = False):
        """Search within tenant boundaries"""
        if cross_context:
            # Search across all contexts for this tenant/type
            collections = self._get_tenant_collections(
                tenant_id, workspace, doc_type
            )
            results = []
            for collection in collections:
                results.extend(
                    self.client.search(
                        collection_name=collection,
                        query_vector=query_vector,
                        limit=10
                    )
                )
            return self._merge_results(results)
        else:
            # Search specific collection
            collection_name = self.get_collection_name(
                tenant_id, workspace, doc_type, context
            )
            return self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=20
            )
```

### 2. Neo4j (GraphDB) - Label-Based Isolation

```python
class Neo4jTenantManager:
    """Manages multi-tenant graphs in Neo4j"""

    def __init__(self, driver: neo4j.Driver):
        self.driver = driver

    def get_tenant_labels(self, tenant_id: str, workspace: str,
                         doc_type: str, context: str = None) -> List[str]:
        """Generate node labels for tenant isolation"""
        labels = [
            "Document",
            f"Tenant_{tenant_id}",
            f"Workspace_{workspace}",
            f"Type_{doc_type}"
        ]
        if context:
            labels.append(f"Context_{context}")
        return labels

    def create_tenant_node(self, tenant_id: str, workspace: str,
                          doc_type: str, properties: dict, context: str = None):
        """Create node with tenant-specific labels"""
        labels = self.get_tenant_labels(tenant_id, workspace, doc_type, context)

        with self.driver.session() as session:
            query = f"""
            CREATE (n:{':'.join(labels)} $props)
            SET n.tenant_id = $tenant_id,
                n.workspace = $workspace,
                n.doc_type = $doc_type,
                n.context = $context,
                n.created_at = datetime()
            RETURN n
            """
            return session.run(
                query,
                props=properties,
                tenant_id=tenant_id,
                workspace=workspace,
                doc_type=doc_type,
                context=context
            )

    def search_tenant_graph(self, tenant_id: str, workspace: str,
                           query: str, doc_type: str = None,
                           context: str = None, max_depth: int = 3):
        """Search within tenant graph boundaries"""
        # Build label constraints
        label_constraints = [f"Tenant_{tenant_id}"]
        if workspace:
            label_constraints.append(f"Workspace_{workspace}")
        if doc_type:
            label_constraints.append(f"Type_{doc_type}")
        if context:
            label_constraints.append(f"Context_{context}")

        with self.driver.session() as session:
            # Example: Find related documents
            cypher = f"""
            MATCH (start:{':'.join(label_constraints)})
            WHERE start.content CONTAINS $query
            MATCH path = (start)-[*1..{max_depth}]-(related)
            WHERE ALL(n IN nodes(path) WHERE
                '{label_constraints[0]}' IN labels(n))
            RETURN path
            LIMIT 50
            """
            return session.run(cypher, query=query)

    def create_tenant_index(self, tenant_id: str, workspace: str):
        """Create indexes for efficient tenant queries"""
        with self.driver.session() as session:
            # Composite index for tenant queries
            session.run(f"""
            CREATE INDEX tenant_{tenant_id}_{workspace}_idx IF NOT EXISTS
            FOR (n:Tenant_{tenant_id})
            ON (n.workspace, n.doc_type, n.context, n.created_at)
            """)
```

### 3. Supabase (SQL) - Row Level Security

```sql
-- Enable RLS for multi-tenancy
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;

-- Create tenant isolation policies
CREATE POLICY "Tenant Isolation" ON documents
    FOR ALL USING (
        tenant_id = current_setting('app.current_tenant')::uuid
        AND workspace = current_setting('app.current_workspace')::text
    );

-- Create hierarchical access
CREATE POLICY "Workspace Access" ON documents
    FOR SELECT USING (
        tenant_id = current_setting('app.current_tenant')::uuid
        AND (
            workspace = current_setting('app.current_workspace')::text
            OR
            current_setting('app.user_role') = 'admin'
        )
    );
```

```python
class SupabaseTenantManager:
    """Manages multi-tenant data in Supabase"""

    def __init__(self, client: Client):
        self.client = client

    def set_tenant_context(self, tenant_id: str, workspace: str):
        """Set RLS context for queries"""
        self.client.rpc(
            'set_config',
            {
                'parameter': 'app.current_tenant',
                'value': tenant_id
            }
        )
        self.client.rpc(
            'set_config',
            {
                'parameter': 'app.current_workspace',
                'value': workspace
            }
        )

    def create_tenant_schema(self, tenant_id: str):
        """Create tenant-specific tables with partitioning"""
        # Partition by tenant for performance
        self.client.rpc(
            'create_tenant_partition',
            {'tenant_id': tenant_id}
        )
```

## Unified Multi-Tenant Interface

```python
class MultiTenantStorage:
    """Unified interface for multi-tenant operations across all stores"""

    def __init__(self):
        self.qdrant = QdrantTenantManager(...)
        self.neo4j = Neo4jTenantManager(...)
        self.supabase = SupabaseTenantManager(...)

    def store_document(self, tenant_id: str, workspace: str,
                      document: Document, context: str = None):
        """Store document with full tenant isolation"""

        # Determine document type
        doc_type = self.classify_document(document)

        # 1. Store metadata in Supabase with RLS
        self.supabase.set_tenant_context(tenant_id, workspace)
        doc_id = self.supabase.store_metadata(document, doc_type, context)

        # 2. Store embeddings in Qdrant collection
        collection = self.qdrant.get_collection_name(
            tenant_id, workspace, doc_type, context
        )
        self.qdrant.store_embeddings(
            collection, document.chunks, document.embeddings
        )

        # 3. Store graph structure in Neo4j with labels
        labels = self.neo4j.get_tenant_labels(
            tenant_id, workspace, doc_type, context
        )
        self.neo4j.store_graph(labels, document.entities, document.relationships)

        return doc_id

    def search(self, tenant_id: str, workspace: str, query: str,
               doc_types: List[str] = None, contexts: List[str] = None,
               cross_workspace: bool = False):
        """Search within tenant boundaries"""

        # Set tenant context
        self.supabase.set_tenant_context(tenant_id, workspace)

        # Parallel search across stores
        with ThreadPoolExecutor() as executor:
            # Vector search
            vector_future = executor.submit(
                self._vector_search,
                tenant_id, workspace, query, doc_types, contexts
            )

            # Graph search
            graph_future = executor.submit(
                self._graph_search,
                tenant_id, workspace, query, doc_types, contexts
            )

            # SQL search
            sql_future = executor.submit(
                self._sql_search,
                tenant_id, workspace, query, doc_types, contexts
            )

        # Combine results
        results = self._merge_results(
            vector_future.result(),
            graph_future.result(),
            sql_future.result()
        )

        return results
```

## Tenant Configuration Examples

### Example 1: Invoice Processing for Multiple Companies

```python
# Company A's invoices
storage.store_document(
    tenant_id="acme_corp",
    workspace="finance",
    document=invoice,
    context="2024_q1"  # Quarter-based isolation
)

# Company B's invoices
storage.store_document(
    tenant_id="globex_inc",
    workspace="finance",
    document=invoice,
    context="vendor_abc"  # Vendor-based isolation
)

# Search only Acme's Q1 invoices
results = storage.search(
    tenant_id="acme_corp",
    workspace="finance",
    query="invoices over $10000",
    doc_types=["invoice"],
    contexts=["2024_q1"]
)

# Search across all Acme's invoices
results = storage.search(
    tenant_id="acme_corp",
    workspace="finance",
    query="total spending on software",
    doc_types=["invoice"],
    contexts=None  # All contexts
)
```

### Example 2: Contract Management for Law Firm

```python
# Client-specific contract collections
storage.store_document(
    tenant_id="law_firm_xyz",
    workspace="client_amazon",
    document=contract,
    context="acquisition_2024"
)

storage.store_document(
    tenant_id="law_firm_xyz",
    workspace="client_microsoft",
    document=contract,
    context="licensing_2024"
)

# Search only Amazon acquisition contracts
results = storage.search(
    tenant_id="law_firm_xyz",
    workspace="client_amazon",
    query="intellectual property clauses",
    doc_types=["contract"],
    contexts=["acquisition_2024"]
)
```

### Example 3: Research Repository for University

```python
# Department-based isolation
storage.store_document(
    tenant_id="stanford_university",
    workspace="computer_science",
    document=paper,
    context="nlp_research"
)

storage.store_document(
    tenant_id="stanford_university",
    workspace="biology",
    document=paper,
    context="genomics_research"
)

# Cross-department search (with permissions)
results = storage.search(
    tenant_id="stanford_university",
    workspace=None,  # All workspaces
    query="machine learning applications",
    doc_types=["research_paper"],
    cross_workspace=True  # Requires permission
)
```

## Security & Access Control

```python
class TenantAccessControl:
    """Manages access permissions across tenants"""

    def __init__(self):
        self.permissions = SupabaseClient.table('tenant_permissions')

    def check_access(self, user_id: str, tenant_id: str,
                    workspace: str, operation: str) -> bool:
        """Verify user has access to tenant/workspace"""
        result = self.permissions.select("*").eq(
            'user_id', user_id
        ).eq(
            'tenant_id', tenant_id
        ).eq(
            'workspace', workspace
        ).single()

        if not result:
            return False

        return operation in result['allowed_operations']

    def grant_access(self, user_id: str, tenant_id: str,
                    workspace: str, operations: List[str]):
        """Grant user access to tenant/workspace"""
        self.permissions.insert({
            'user_id': user_id,
            'tenant_id': tenant_id,
            'workspace': workspace,
            'allowed_operations': operations,
            'granted_at': datetime.now()
        })
```

## Migration & Scaling Considerations

### 1. Data Migration Between Tenants
```python
def migrate_context(source_tenant: str, source_context: str,
                   target_tenant: str, target_context: str):
    """Migrate data between tenant contexts"""
    # Export from source
    data = export_tenant_data(source_tenant, source_context)

    # Transform if needed
    data = transform_for_new_context(data)

    # Import to target
    import_tenant_data(target_tenant, target_context, data)
```

### 2. Scaling Strategies
- **Qdrant**: Shard collections by tenant size
- **Neo4j**: Use fabric for multi-database tenancy
- **Supabase**: Partition tables by tenant_id

### 3. Monitoring
```python
class TenantUsageMonitor:
    """Track usage by tenant for billing/limits"""

    def track_operation(self, tenant_id: str, operation: str,
                       storage_type: str, size_bytes: int):
        # Record usage for billing
        # Check against quotas
        # Alert if approaching limits
```

## Best Practices

1. **Consistent Naming**: Use same pattern across all stores
2. **Index Strategy**: Create indexes per tenant for performance
3. **Backup Strategy**: Tenant-specific backup schedules
4. **Testing**: Always test with multiple tenants
5. **Documentation**: Document context meanings per tenant

## Implementation Priority

1. **Phase 1**: Basic tenant isolation (tenant_id + workspace)
2. **Phase 2**: Context-based collections (doc_type + context)
3. **Phase 3**: Cross-tenant search (with permissions)
4. **Phase 4**: Advanced features (migration, archival)
