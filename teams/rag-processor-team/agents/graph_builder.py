"""
Graph Builder Agent
Builds Neo4j knowledge graph from extracted entities and relationships.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase

from elf_automations.shared.utils import get_supabase_client

logger = logging.getLogger(__name__)


class GraphBuilderAgent:
    """Agent responsible for building knowledge graph in Neo4j"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.name = "graph_builder"
        self.role = "Graph Builder"
        self.backstory = (
            "A connection specialist who weaves information into rich networks"
        )

        # Neo4j connection
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = None

    async def initialize(self):
        """Initialize Neo4j connection"""
        if not self.driver:
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
            )

    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()

    async def build_graph(
        self,
        document_id: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
        chunk_relationships: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build graph from document entities and relationships"""
        try:
            await self.initialize()

            # Create document node
            doc_node_id = await self._create_document_node(document_id)

            # Create entity nodes
            entity_node_ids = await self._create_entity_nodes(entities, document_id)

            # Create relationships
            relationship_ids = await self._create_relationships(
                relationships, entity_node_ids, document_id
            )

            # Create chunk nodes and relationships
            chunk_node_ids = await self._create_chunk_graph(
                chunks, chunk_relationships, document_id
            )

            # Link entities to chunks
            await self._link_entities_to_chunks(
                entities, chunks, entity_node_ids, chunk_node_ids
            )

            logger.info(
                f"Built graph with {len(entity_node_ids)} entity nodes "
                f"and {len(relationship_ids)} relationships"
            )

            return {
                "node_ids": list(entity_node_ids.values()) + chunk_node_ids,
                "edge_ids": relationship_ids,
                "document_node_id": doc_node_id,
                "metadata": {
                    "entity_nodes": len(entity_node_ids),
                    "chunk_nodes": len(chunk_node_ids),
                    "relationships": len(relationship_ids),
                },
            }

        except Exception as e:
            logger.error(f"Graph building error: {str(e)}")
            raise

    async def _create_document_node(self, document_id: str) -> str:
        """Create document node in Neo4j"""
        async with self.driver.session() as session:
            query = """
            MERGE (d:Document {id: $document_id})
            ON CREATE SET
                d.created_at = datetime(),
                d.node_type = 'document'
            RETURN id(d) as node_id
            """

            result = await session.run(query, document_id=document_id)
            record = await result.single()

            return str(record["node_id"])

    async def _create_entity_nodes(
        self, entities: List[Dict[str, Any]], document_id: str
    ) -> Dict[str, str]:
        """Create entity nodes in Neo4j"""
        entity_node_ids = {}

        async with self.driver.session() as session:
            for entity in entities:
                # Determine node labels based on entity type
                labels = self._get_entity_labels(entity["type"])

                # Build properties
                properties = {
                    "value": entity["value"],
                    "normalized_value": entity.get("normalized_value", entity["value"]),
                    "type": entity["type"],
                    "confidence": entity.get("confidence", 1.0),
                    "source_document": document_id,
                }

                # Add custom properties
                if entity.get("properties"):
                    for key, value in entity["properties"].items():
                        if isinstance(value, (str, int, float, bool)):
                            properties[key] = value

                # Create node
                query = f"""
                MERGE (e:{':'.join(labels)} {{normalized_value: $normalized_value, type: $type}})
                ON CREATE SET e = $properties
                ON MATCH SET e.last_seen = datetime(), e.occurrence_count = coalesce(e.occurrence_count, 0) + 1
                WITH e
                MATCH (d:Document {{id: $document_id}})
                MERGE (e)-[:EXTRACTED_FROM]->(d)
                RETURN id(e) as node_id
                """

                result = await session.run(
                    query,
                    normalized_value=properties["normalized_value"],
                    type=entity["type"],
                    properties=properties,
                    document_id=document_id,
                )

                record = await result.single()
                if record:
                    node_id = str(record["node_id"])
                    entity_node_ids[entity["value"]] = node_id

                    # Update Supabase with Neo4j reference
                    if entity.get("id"):
                        self.supabase.table("rag_extracted_entities").update(
                            {"neo4j_node_id": node_id, "neo4j_labels": labels}
                        ).eq("id", entity["id"]).execute()

        return entity_node_ids

    def _get_entity_labels(self, entity_type: str) -> List[str]:
        """Get Neo4j labels for entity type"""
        label_mapping = {
            # Contract entities
            "party": ["Entity", "Party", "LegalEntity"],
            "jurisdiction": ["Entity", "Jurisdiction", "Location"],
            "term": ["Entity", "ContractTerm"],
            "obligation": ["Entity", "Obligation"],
            "date": ["Entity", "Date", "TemporalEntity"],
            "monetary_amount": ["Entity", "MonetaryAmount"],
            # Invoice entities
            "vendor": ["Entity", "Organization", "Vendor"],
            "customer": ["Entity", "Organization", "Customer"],
            "line_item": ["Entity", "LineItem"],
            "product": ["Entity", "Product"],
            "service": ["Entity", "Service"],
            # Technical entities
            "component": ["Entity", "Component", "TechnicalEntity"],
            "system": ["Entity", "System", "TechnicalEntity"],
            "requirement": ["Entity", "Requirement"],
            "procedure": ["Entity", "Procedure"],
            "concept": ["Entity", "Concept", "TechnicalEntity"],
            "version": ["Entity", "Version"],
            # Generic entities
            "person": ["Entity", "Person"],
            "organization": ["Entity", "Organization"],
            "location": ["Entity", "Location"],
            "amount": ["Entity", "Amount"],
        }

        return label_mapping.get(entity_type, ["Entity", entity_type.title()])

    async def _create_relationships(
        self,
        relationships: List[Dict[str, Any]],
        entity_node_ids: Dict[str, str],
        document_id: str,
    ) -> List[str]:
        """Create relationships between entities"""
        relationship_ids = []

        async with self.driver.session() as session:
            for rel in relationships:
                source_id = entity_node_ids.get(rel["source_entity"])
                target_id = entity_node_ids.get(rel["target_entity"])

                if not source_id or not target_id:
                    logger.warning(
                        f"Skipping relationship - missing nodes: "
                        f"{rel['source_entity']} -> {rel['target_entity']}"
                    )
                    continue

                # Create relationship
                rel_type = self._normalize_relationship_type(rel["relationship_type"])

                properties = {
                    "type": rel["relationship_type"],
                    "confidence": rel.get("confidence", 1.0),
                    "source_document": document_id,
                }

                # Add custom properties
                if rel.get("properties"):
                    for key, value in rel["properties"].items():
                        if isinstance(value, (str, int, float, bool)):
                            properties[key] = value

                query = f"""
                MATCH (s) WHERE id(s) = toInteger($source_id)
                MATCH (t) WHERE id(t) = toInteger($target_id)
                MERGE (s)-[r:{rel_type}]->(t)
                SET r = $properties
                RETURN id(r) as rel_id
                """

                result = await session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    properties=properties,
                )

                record = await result.single()
                if record:
                    rel_id = str(record["rel_id"])
                    relationship_ids.append(rel_id)

                    # Update Supabase with Neo4j reference
                    if rel.get("id"):
                        self.supabase.table("rag_entity_relationships").update(
                            {"neo4j_edge_id": rel_id, "neo4j_type": rel_type}
                        ).eq("id", rel["id"]).execute()

        return relationship_ids

    def _normalize_relationship_type(self, rel_type: str) -> str:
        """Normalize relationship type for Neo4j"""
        # Replace spaces and special characters
        normalized = rel_type.upper().replace(" ", "_").replace("-", "_")
        # Remove non-alphanumeric characters except underscore
        normalized = "".join(c for c in normalized if c.isalnum() or c == "_")
        return normalized

    async def _create_chunk_graph(
        self,
        chunks: List[Dict[str, Any]],
        chunk_relationships: List[Dict[str, Any]],
        document_id: str,
    ) -> List[str]:
        """Create chunk nodes and relationships"""
        chunk_node_ids = []

        async with self.driver.session() as session:
            # Create chunk nodes
            for chunk in chunks:
                query = """
                CREATE (c:Chunk {
                    index: $index,
                    type: $type,
                    token_count: $token_count,
                    document_id: $document_id
                })
                WITH c
                MATCH (d:Document {id: $document_id})
                MERGE (c)-[:PART_OF]->(d)
                RETURN id(c) as node_id
                """

                result = await session.run(
                    query,
                    index=chunk["chunk_index"],
                    type=chunk.get("type", "unknown"),
                    token_count=chunk.get("token_count", 0),
                    document_id=document_id,
                )

                record = await result.single()
                if record:
                    chunk_node_ids.append(str(record["node_id"]))

            # Create chunk relationships
            for rel in chunk_relationships:
                if rel["source_chunk_index"] < len(chunk_node_ids) and rel[
                    "target_chunk_index"
                ] < len(chunk_node_ids):
                    source_id = chunk_node_ids[rel["source_chunk_index"]]
                    target_id = chunk_node_ids[rel["target_chunk_index"]]
                    rel_type = self._normalize_relationship_type(
                        rel["relationship_type"]
                    )

                    query = f"""
                    MATCH (s) WHERE id(s) = toInteger($source_id)
                    MATCH (t) WHERE id(t) = toInteger($target_id)
                    MERGE (s)-[:{rel_type}]->(t)
                    """

                    await session.run(query, source_id=source_id, target_id=target_id)

        return chunk_node_ids

    async def _link_entities_to_chunks(
        self,
        entities: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
        entity_node_ids: Dict[str, str],
        chunk_node_ids: List[str],
    ) -> None:
        """Create relationships between entities and chunks they appear in"""
        async with self.driver.session() as session:
            for i, chunk in enumerate(chunks):
                if i >= len(chunk_node_ids):
                    continue

                chunk_node_id = chunk_node_ids[i]

                # Find entities in this chunk
                for entity in entities:
                    if (
                        entity["value"] in chunk["content"]
                        or entity.get("source_text", "") in chunk["content"]
                    ):
                        entity_node_id = entity_node_ids.get(entity["value"])
                        if entity_node_id:
                            query = """
                            MATCH (e) WHERE id(e) = toInteger($entity_id)
                            MATCH (c) WHERE id(c) = toInteger($chunk_id)
                            MERGE (e)-[:APPEARS_IN]->(c)
                            """

                            await session.run(
                                query, entity_id=entity_node_id, chunk_id=chunk_node_id
                            )

    async def query_entity_relationships(
        self,
        entity_value: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """Query relationships for an entity"""
        await self.initialize()

        async with self.driver.session() as session:
            # Build relationship filter
            rel_filter = ""
            if relationship_types:
                rel_types = [
                    self._normalize_relationship_type(rt) for rt in relationship_types
                ]
                rel_filter = f"[{'|'.join(f':{rt}' for rt in rel_types)}]"

            query = f"""
            MATCH (e:Entity {{normalized_value: $entity_value}})
            OPTIONAL MATCH path = (e)-{rel_filter}*1..{max_depth}-(related)
            RETURN e, collect(distinct path) as paths
            """

            result = await session.run(query, entity_value=entity_value)
            record = await result.single()

            if record:
                return {
                    "entity": dict(record["e"]),
                    "paths": [
                        self._path_to_dict(path) for path in record["paths"] if path
                    ],
                }

            return {"entity": None, "paths": []}

    def _path_to_dict(self, path) -> Dict[str, Any]:
        """Convert Neo4j path to dictionary"""
        nodes = []
        relationships = []

        for i, node in enumerate(path.nodes):
            nodes.append(
                {
                    "id": str(node.id),
                    "labels": list(node.labels),
                    "properties": dict(node),
                }
            )

        for rel in path.relationships:
            relationships.append(
                {
                    "id": str(rel.id),
                    "type": rel.type,
                    "start": str(rel.start_node.id),
                    "end": str(rel.end_node.id),
                    "properties": dict(rel),
                }
            )

        return {"nodes": nodes, "relationships": relationships}

    async def create_nodes(self, *args, **kwargs):
        """Alias for entity node creation"""
        return await self._create_entity_nodes(*args, **kwargs)

    async def create_relationships(self, *args, **kwargs):
        """Alias for relationship creation"""
        return await self._create_relationships(*args, **kwargs)

    async def update_graph_metadata(
        self, node_id: str, metadata: Dict[str, Any]
    ) -> None:
        """Update node metadata in Neo4j"""
        await self.initialize()

        async with self.driver.session() as session:
            query = """
            MATCH (n) WHERE id(n) = toInteger($node_id)
            SET n.updated_at = datetime(), n.metadata = $metadata
            """

            await session.run(query, node_id=node_id, metadata=metadata)

    async def validate_graph_integrity(self, document_id: str) -> Dict[str, Any]:
        """Validate graph integrity for a document"""
        await self.initialize()

        async with self.driver.session() as session:
            # Check orphaned nodes
            orphan_query = """
            MATCH (e:Entity {source_document: $document_id})
            WHERE NOT (e)-[]-()
            RETURN count(e) as orphan_count
            """

            orphan_result = await session.run(orphan_query, document_id=document_id)
            orphan_record = await orphan_result.single()

            # Check document connectivity
            connectivity_query = """
            MATCH (d:Document {id: $document_id})
            OPTIONAL MATCH (d)<-[:EXTRACTED_FROM]-(e:Entity)
            OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)
            RETURN count(distinct e) as entity_count, count(distinct c) as chunk_count
            """

            conn_result = await session.run(connectivity_query, document_id=document_id)
            conn_record = await conn_result.single()

            return {
                "valid": orphan_record["orphan_count"] == 0,
                "orphaned_entities": orphan_record["orphan_count"],
                "connected_entities": conn_record["entity_count"],
                "connected_chunks": conn_record["chunk_count"],
            }
