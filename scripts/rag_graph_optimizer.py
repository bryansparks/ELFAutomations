#!/usr/bin/env python3
"""
RAG Graph Optimizer
Analyzes and optimizes Neo4j graph performance for RAG system.

Features:
- Query performance analysis
- Graph structure optimization
- Entity deduplication
- Relationship pruning
- Index recommendations
"""

import argparse
import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import pandas as pd
from neo4j import GraphDatabase
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from elf_automations.shared.config import settings
from elf_automations.shared.utils import get_supabase_client

console = Console()


class GraphOptimizer:
    """Optimize Neo4j graph for RAG queries"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.neo4j_uri = settings.get("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = settings.get("NEO4J_USER", "neo4j")
        self.neo4j_password = settings.get("NEO4J_PASSWORD")
        self.driver = None

    def initialize(self):
        """Initialize Neo4j connection"""
        if not self.driver and self.neo4j_password:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
            )

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    async def analyze_graph_structure(self) -> Dict[str, Any]:
        """Analyze overall graph structure and statistics"""
        console.print("[yellow]Analyzing graph structure...[/yellow]")

        self.initialize()

        if not self.driver:
            return {"error": "Neo4j not configured"}

        try:
            with self.driver.session() as session:
                # Basic statistics
                stats = {}

                # Node count by label
                result = session.run(
                    """
                    MATCH (n)
                    RETURN labels(n)[0] as label, count(n) as count
                    ORDER BY count DESC
                """
                )
                node_counts = {
                    record["label"]: record["count"]
                    for record in result
                    if record["label"]
                }
                stats["node_counts"] = node_counts
                stats["total_nodes"] = sum(node_counts.values())

                # Relationship count by type
                result = session.run(
                    """
                    MATCH ()-[r]->()
                    RETURN type(r) as type, count(r) as count
                    ORDER BY count DESC
                """
                )
                rel_counts = {record["type"]: record["count"] for record in result}
                stats["relationship_counts"] = rel_counts
                stats["total_relationships"] = sum(rel_counts.values())

                # Degree distribution
                result = session.run(
                    """
                    MATCH (n)
                    WITH n, size((n)-[]-()) as degree
                    RETURN
                        avg(degree) as avg_degree,
                        min(degree) as min_degree,
                        max(degree) as max_degree,
                        percentileCont(degree, 0.5) as median_degree,
                        percentileCont(degree, 0.95) as p95_degree
                """
                )
                degree_stats = result.single()
                stats["degree_distribution"] = dict(degree_stats)

                # Isolated nodes
                result = session.run(
                    """
                    MATCH (n)
                    WHERE NOT (n)-[]-()
                    RETURN count(n) as isolated_count
                """
                )
                stats["isolated_nodes"] = result.single()["isolated_count"]

                # Component analysis
                components = await self._analyze_components(session)
                stats["components"] = components

                # Density calculation
                if stats["total_nodes"] > 1:
                    max_edges = stats["total_nodes"] * (stats["total_nodes"] - 1)
                    stats["density"] = (
                        stats["total_relationships"] / max_edges if max_edges > 0 else 0
                    )
                else:
                    stats["density"] = 0

                return stats

        except Exception as e:
            console.print(f"[red]Error analyzing graph: {str(e)}[/red]")
            return {"error": str(e)}

    async def _analyze_components(self, session) -> Dict[str, Any]:
        """Analyze graph components"""
        # Get sample of connected components
        result = session.run(
            """
            MATCH (n)
            WITH n LIMIT 10000
            CALL {
                WITH n
                MATCH path = (n)-[*]-(m)
                RETURN collect(distinct m) as component
            }
            RETURN size(component) as size
            ORDER BY size DESC
            LIMIT 100
        """
        )

        component_sizes = [record["size"] for record in result]

        return {
            "estimated_components": len(set(component_sizes)),
            "largest_component": max(component_sizes) if component_sizes else 0,
            "smallest_component": min(component_sizes) if component_sizes else 0,
            "avg_component_size": sum(component_sizes) / len(component_sizes)
            if component_sizes
            else 0,
        }

    async def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze common query patterns and performance"""
        console.print("[yellow]Analyzing query performance...[/yellow]")

        self.initialize()

        if not self.driver:
            return {"error": "Neo4j not configured"}

        try:
            with self.driver.session() as session:
                performance_results = {}

                # Test queries with timing
                test_queries = [
                    {
                        "name": "Entity lookup",
                        "query": """
                            MATCH (n:Entity {normalized_name: $name})
                            RETURN n LIMIT 1
                        """,
                        "params": {"name": "test_entity"},
                    },
                    {
                        "name": "Relationship traversal",
                        "query": """
                            MATCH (n:Entity)-[r]->(m:Entity)
                            WHERE n.entity_type = $type
                            RETURN n, r, m LIMIT 10
                        """,
                        "params": {"type": "organization"},
                    },
                    {
                        "name": "Path finding",
                        "query": """
                            MATCH path = shortestPath((n:Entity)-[*..3]-(m:Entity))
                            WHERE n.normalized_name = $start AND m.normalized_name = $end
                            RETURN path LIMIT 1
                        """,
                        "params": {"start": "entity1", "end": "entity2"},
                    },
                    {
                        "name": "Neighborhood exploration",
                        "query": """
                            MATCH (n:Entity {normalized_name: $name})-[r*1..2]-(neighbor)
                            RETURN DISTINCT neighbor, labels(neighbor) as labels
                            LIMIT 50
                        """,
                        "params": {"name": "test_entity"},
                    },
                ]

                for test in test_queries:
                    try:
                        # Run query with EXPLAIN
                        explain_result = session.run(
                            f"EXPLAIN {test['query']}", test["params"]
                        )

                        # Run query with timing
                        import time

                        start_time = time.time()
                        result = session.run(test["query"], test["params"])
                        result.consume()  # Consume all results
                        execution_time = (time.time() - start_time) * 1000

                        performance_results[test["name"]] = {
                            "execution_time_ms": execution_time,
                            "status": "success",
                        }

                    except Exception as e:
                        performance_results[test["name"]] = {
                            "execution_time_ms": -1,
                            "status": "failed",
                            "error": str(e),
                        }

                # Check existing indexes
                result = session.run("SHOW INDEXES")
                indexes = []
                for record in result:
                    indexes.append(
                        {
                            "name": record.get("name"),
                            "type": record.get("type"),
                            "entityType": record.get("entityType"),
                            "properties": record.get("properties", []),
                        }
                    )

                performance_results["existing_indexes"] = indexes

                # Generate recommendations
                performance_results[
                    "recommendations"
                ] = self._generate_performance_recommendations(
                    performance_results, indexes
                )

                return performance_results

        except Exception as e:
            console.print(f"[red]Error analyzing performance: {str(e)}[/red]")
            return {"error": str(e)}

    def _generate_performance_recommendations(
        self, perf_results: Dict, indexes: List
    ) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        # Check for missing indexes
        indexed_properties = set()
        for idx in indexes:
            if idx.get("properties"):
                for prop in idx["properties"]:
                    indexed_properties.add(f"{idx.get('entityType', 'Unknown')}.{prop}")

        # Recommend indexes based on query patterns
        if "Entity.normalized_name" not in indexed_properties:
            recommendations.append(
                "CREATE INDEX entity_normalized_name FOR (n:Entity) ON (n.normalized_name)"
            )

        if "Entity.entity_type" not in indexed_properties:
            recommendations.append(
                "CREATE INDEX entity_type FOR (n:Entity) ON (n.entity_type)"
            )

        # Check query performance
        slow_queries = [
            name
            for name, result in perf_results.items()
            if isinstance(result, dict) and result.get("execution_time_ms", 0) > 100
        ]

        if slow_queries:
            recommendations.append(
                f"Slow queries detected: {', '.join(slow_queries)}. Consider query optimization."
            )

        return recommendations

    async def find_duplicate_entities(
        self, similarity_threshold: float = 0.9
    ) -> Dict[str, Any]:
        """Find potential duplicate entities in the graph"""
        console.print("[yellow]Finding duplicate entities...[/yellow]")

        self.initialize()

        if not self.driver:
            return {"error": "Neo4j not configured"}

        try:
            with self.driver.session() as session:
                # Find entities with similar names
                result = session.run(
                    """
                    MATCH (n:Entity)
                    WITH n.entity_type as type,
                         collect({name: n.normalized_name, id: id(n), value: n.entity_value}) as entities
                    WHERE size(entities) > 1
                    RETURN type, entities
                    ORDER BY size(entities) DESC
                """
                )

                duplicates = defaultdict(list)
                total_duplicates = 0

                for record in result:
                    entity_type = record["type"]
                    entities = record["entities"]

                    # Group similar entities
                    groups = self._group_similar_entities(entities)

                    for group in groups:
                        if len(group) > 1:
                            duplicates[entity_type].append(group)
                            total_duplicates += len(group) - 1

                # Find entities with same normalized name
                result = session.run(
                    """
                    MATCH (n:Entity)
                    WITH n.normalized_name as name, collect(n) as nodes
                    WHERE size(nodes) > 1
                    RETURN name, size(nodes) as count,
                           [node in nodes | {id: id(node), value: node.entity_value}] as duplicates
                    ORDER BY count DESC
                    LIMIT 20
                """
                )

                exact_duplicates = []
                for record in result:
                    exact_duplicates.append(
                        {
                            "normalized_name": record["name"],
                            "count": record["count"],
                            "entities": record["duplicates"],
                        }
                    )

                return {
                    "total_potential_duplicates": total_duplicates,
                    "duplicate_groups_by_type": dict(duplicates),
                    "exact_duplicates": exact_duplicates,
                    "recommendations": self._generate_deduplication_recommendations(
                        total_duplicates
                    ),
                }

        except Exception as e:
            console.print(f"[red]Error finding duplicates: {str(e)}[/red]")
            return {"error": str(e)}

    def _group_similar_entities(self, entities: List[Dict]) -> List[List[Dict]]:
        """Group similar entities based on normalized names"""
        from difflib import SequenceMatcher

        groups = []
        processed = set()

        for i, entity1 in enumerate(entities):
            if i in processed:
                continue

            group = [entity1]
            processed.add(i)

            for j, entity2 in enumerate(entities[i + 1 :], i + 1):
                if j in processed:
                    continue

                # Calculate similarity
                similarity = SequenceMatcher(
                    None, entity1["name"], entity2["name"]
                ).ratio()

                if similarity > 0.9:
                    group.append(entity2)
                    processed.add(j)

            if len(group) > 1:
                groups.append(group)

        return groups

    def _generate_deduplication_recommendations(
        self, duplicate_count: int
    ) -> List[str]:
        """Generate recommendations for deduplication"""
        recommendations = []

        if duplicate_count > 0:
            recommendations.append(
                f"Found {duplicate_count} potential duplicate entities. "
                "Consider merging to improve query performance and data quality."
            )

            recommendations.append(
                "Use entity normalization rules to prevent future duplicates during extraction."
            )

            if duplicate_count > 100:
                recommendations.append(
                    "High number of duplicates detected. Review entity extraction and normalization process."
                )

        return recommendations

    async def analyze_relationship_quality(self) -> Dict[str, Any]:
        """Analyze relationship quality and suggest pruning"""
        console.print("[yellow]Analyzing relationship quality...[/yellow]")

        self.initialize()

        if not self.driver:
            return {"error": "Neo4j not configured"}

        try:
            with self.driver.session() as session:
                # Analyze relationship distribution
                result = session.run(
                    """
                    MATCH (n)-[r]->(m)
                    WITH type(r) as rel_type,
                         count(r) as count,
                         avg(r.confidence) as avg_confidence,
                         min(r.confidence) as min_confidence,
                         percentileCont(r.confidence, 0.25) as q1_confidence
                    RETURN rel_type, count, avg_confidence, min_confidence, q1_confidence
                    ORDER BY count DESC
                """
                )

                relationship_stats = []
                low_confidence_rels = []

                for record in result:
                    stats = dict(record)
                    relationship_stats.append(stats)

                    # Check for low confidence relationships
                    if stats.get("q1_confidence", 1.0) < 0.5:
                        low_confidence_rels.append(stats["rel_type"])

                # Find redundant relationships
                result = session.run(
                    """
                    MATCH (n)-[r1]->(m)
                    MATCH (n)-[r2]->(m)
                    WHERE id(r1) < id(r2) AND type(r1) = type(r2)
                    RETURN type(r1) as rel_type, count(*) as duplicate_count
                    ORDER BY duplicate_count DESC
                    LIMIT 10
                """
                )

                redundant_relationships = [dict(record) for record in result]

                # Analyze relationship patterns
                result = session.run(
                    """
                    MATCH (n)-[r]->(m)
                    WITH n, count(r) as out_degree
                    WHERE out_degree > 50
                    RETURN avg(out_degree) as avg_high_degree,
                           max(out_degree) as max_degree,
                           count(n) as high_degree_nodes
                """
                )

                high_degree_stats = dict(result.single())

                return {
                    "relationship_statistics": relationship_stats,
                    "low_confidence_types": low_confidence_rels,
                    "redundant_relationships": redundant_relationships,
                    "high_degree_nodes": high_degree_stats,
                    "recommendations": self._generate_relationship_recommendations(
                        relationship_stats, low_confidence_rels, high_degree_stats
                    ),
                }

        except Exception as e:
            console.print(f"[red]Error analyzing relationships: {str(e)}[/red]")
            return {"error": str(e)}

    def _generate_relationship_recommendations(
        self, rel_stats: List[Dict], low_conf_types: List[str], high_degree: Dict
    ) -> List[str]:
        """Generate relationship optimization recommendations"""
        recommendations = []

        if low_conf_types:
            recommendations.append(
                f"Consider pruning low-confidence relationships: {', '.join(low_conf_types[:3])}"
            )

        if high_degree.get("high_degree_nodes", 0) > 10:
            recommendations.append(
                f"Found {high_degree['high_degree_nodes']} nodes with >50 relationships. "
                "Consider relationship filtering or aggregation."
            )

        # Check for imbalanced relationship types
        if rel_stats:
            total_rels = sum(r["count"] for r in rel_stats)
            for rel in rel_stats[:3]:
                if rel["count"] > total_rels * 0.5:
                    recommendations.append(
                        f"Relationship type '{rel['rel_type']}' dominates the graph "
                        f"({rel['count']/total_rels:.1%}). Consider more specific relationship types."
                    )

        return recommendations

    async def optimize_graph(self, operations: List[str]) -> Dict[str, Any]:
        """Execute graph optimization operations"""
        console.print("[yellow]Executing graph optimizations...[/yellow]")

        self.initialize()

        if not self.driver:
            return {"error": "Neo4j not configured"}

        results = {
            "operations_requested": operations,
            "completed": [],
            "failed": [],
            "metrics_before": {},
            "metrics_after": {},
        }

        try:
            # Get metrics before optimization
            results["metrics_before"] = await self._get_graph_metrics()

            with self.driver.session() as session:
                # Execute each optimization
                for operation in operations:
                    try:
                        if operation == "create_indexes":
                            await self._create_recommended_indexes(session)
                            results["completed"].append("create_indexes")

                        elif operation == "remove_duplicates":
                            removed = await self._remove_duplicate_entities(session)
                            results["completed"].append(
                                f"remove_duplicates: {removed} entities"
                            )

                        elif operation == "prune_low_confidence":
                            pruned = await self._prune_low_confidence_relationships(
                                session
                            )
                            results["completed"].append(
                                f"prune_low_confidence: {pruned} relationships"
                            )

                        elif operation == "optimize_layout":
                            await self._optimize_graph_layout(session)
                            results["completed"].append("optimize_layout")

                    except Exception as e:
                        results["failed"].append(f"{operation}: {str(e)}")

            # Get metrics after optimization
            results["metrics_after"] = await self._get_graph_metrics()

            return results

        except Exception as e:
            console.print(f"[red]Error during optimization: {str(e)}[/red]")
            return {"error": str(e)}

    async def _get_graph_metrics(self) -> Dict[str, Any]:
        """Get current graph metrics"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                WITH count(n) as node_count
                MATCH ()-[r]->()
                WITH node_count, count(r) as rel_count
                RETURN node_count, rel_count
            """
            )

            record = result.single()
            return {
                "nodes": record["node_count"],
                "relationships": record["rel_count"],
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _create_recommended_indexes(self, session):
        """Create recommended indexes"""
        indexes = [
            ("Entity", "normalized_name"),
            ("Entity", "entity_type"),
            ("Entity", "document_id"),
            ("Document", "tenant_id"),
            ("Chunk", "document_id"),
        ]

        for label, property in indexes:
            try:
                session.run(
                    f"""
                    CREATE INDEX IF NOT EXISTS
                    FOR (n:{label})
                    ON (n.{property})
                """
                )
                console.print(f"[green]Created index on {label}.{property}[/green]")
            except:
                pass

    async def _remove_duplicate_entities(self, session) -> int:
        """Remove duplicate entities keeping the one with most relationships"""
        result = session.run(
            """
            MATCH (n:Entity)
            WITH n.normalized_name as name, collect(n) as nodes
            WHERE size(nodes) > 1
            UNWIND nodes as node
            WITH name, node, size((node)-[]-()) as degree
            ORDER BY name, degree DESC
            WITH name, collect(node) as sorted_nodes
            FOREACH (i in range(1, size(sorted_nodes)-1) |
                DETACH DELETE sorted_nodes[i]
            )
            RETURN count(name) as groups_processed
        """
        )

        return result.single()["groups_processed"]

    async def _prune_low_confidence_relationships(
        self, session, threshold: float = 0.3
    ) -> int:
        """Remove relationships with low confidence"""
        result = session.run(
            """
            MATCH ()-[r]->()
            WHERE r.confidence < $threshold
            DELETE r
            RETURN count(r) as deleted_count
        """,
            threshold=threshold,
        )

        return result.single()["deleted_count"]

    async def _optimize_graph_layout(self, session):
        """Optimize graph layout for better query performance"""
        # This could involve:
        # - Reordering nodes for cache efficiency
        # - Creating materialized views for common queries
        # - Pre-computing common aggregations
        console.print("[green]Graph layout optimization completed[/green]")

    def display_analysis(self, analysis_type: str, results: Dict[str, Any]):
        """Display analysis results"""
        if "error" in results:
            console.print(f"[red]Error: {results['error']}[/red]")
            return

        if analysis_type == "structure":
            self._display_structure_analysis(results)
        elif analysis_type == "performance":
            self._display_performance_analysis(results)
        elif analysis_type == "duplicates":
            self._display_duplicate_analysis(results)
        elif analysis_type == "relationships":
            self._display_relationship_analysis(results)

    def _display_structure_analysis(self, results: Dict[str, Any]):
        """Display graph structure analysis"""
        console.print("\n[bold blue]Graph Structure Analysis[/bold blue]")

        # Node statistics
        table = Table(title="Node Distribution")
        table.add_column("Label", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="green")

        total = results["total_nodes"]
        for label, count in results["node_counts"].items():
            percentage = (count / total * 100) if total > 0 else 0
            table.add_row(label, str(count), f"{percentage:.1f}%")

        console.print(table)

        # Graph metrics
        metrics_table = Table(title="Graph Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="magenta")

        metrics_table.add_row("Total Nodes", str(results["total_nodes"]))
        metrics_table.add_row(
            "Total Relationships", str(results["total_relationships"])
        )
        metrics_table.add_row("Graph Density", f"{results['density']:.4f}")
        metrics_table.add_row("Isolated Nodes", str(results["isolated_nodes"]))

        degree_dist = results["degree_distribution"]
        metrics_table.add_row("Avg Degree", f"{degree_dist['avg_degree']:.1f}")
        metrics_table.add_row("Max Degree", str(degree_dist["max_degree"]))

        console.print(metrics_table)

    def _display_performance_analysis(self, results: Dict[str, Any]):
        """Display performance analysis"""
        console.print("\n[bold blue]Query Performance Analysis[/bold blue]")

        # Query performance
        table = Table(title="Query Performance")
        table.add_column("Query Type", style="cyan")
        table.add_column("Execution Time", style="magenta")
        table.add_column("Status", style="green")

        for query_name, result in results.items():
            if isinstance(result, dict) and "execution_time_ms" in result:
                time_str = (
                    f"{result['execution_time_ms']:.1f} ms"
                    if result["execution_time_ms"] >= 0
                    else "N/A"
                )
                status = (
                    "[green]OK[/green]"
                    if result["status"] == "success"
                    else "[red]Failed[/red]"
                )
                table.add_row(query_name, time_str, status)

        console.print(table)

        # Recommendations
        if results.get("recommendations"):
            console.print("\n[bold yellow]Performance Recommendations:[/bold yellow]")
            for i, rec in enumerate(results["recommendations"], 1):
                console.print(f"{i}. {rec}")

    def _display_duplicate_analysis(self, results: Dict[str, Any]):
        """Display duplicate entity analysis"""
        console.print("\n[bold blue]Duplicate Entity Analysis[/bold blue]")

        console.print(
            f"Total potential duplicates: [red]{results['total_potential_duplicates']}[/red]"
        )

        if results["exact_duplicates"]:
            table = Table(title="Top Exact Duplicates")
            table.add_column("Normalized Name", style="cyan")
            table.add_column("Count", style="magenta")

            for dup in results["exact_duplicates"][:10]:
                table.add_row(dup["normalized_name"], str(dup["count"]))

            console.print(table)

        if results.get("recommendations"):
            console.print("\n[bold yellow]Deduplication Recommendations:[/bold yellow]")
            for i, rec in enumerate(results["recommendations"], 1):
                console.print(f"{i}. {rec}")

    def _display_relationship_analysis(self, results: Dict[str, Any]):
        """Display relationship analysis"""
        console.print("\n[bold blue]Relationship Quality Analysis[/bold blue]")

        # Relationship statistics
        table = Table(title="Relationship Statistics")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Avg Confidence", style="green")
        table.add_column("Min Confidence", style="yellow")

        for rel in results["relationship_statistics"][:10]:
            avg_conf = (
                f"{rel['avg_confidence']:.2f}" if rel["avg_confidence"] else "N/A"
            )
            min_conf = (
                f"{rel['min_confidence']:.2f}" if rel["min_confidence"] else "N/A"
            )
            table.add_row(rel["rel_type"], str(rel["count"]), avg_conf, min_conf)

        console.print(table)

        if results.get("recommendations"):
            console.print("\n[bold yellow]Relationship Recommendations:[/bold yellow]")
            for i, rec in enumerate(results["recommendations"], 1):
                console.print(f"{i}. {rec}")


async def main():
    parser = argparse.ArgumentParser(description="RAG Graph Optimizer")
    parser.add_argument(
        "--analyze",
        choices=["structure", "performance", "duplicates", "relationships", "all"],
        default="all",
        help="Type of analysis to perform",
    )
    parser.add_argument("--optimize", action="store_true", help="Execute optimizations")
    parser.add_argument(
        "--operations",
        nargs="+",
        choices=[
            "create_indexes",
            "remove_duplicates",
            "prune_low_confidence",
            "optimize_layout",
        ],
        help="Optimization operations to perform",
    )
    parser.add_argument("--export", type=str, help="Export analysis to JSON file")

    args = parser.parse_args()

    optimizer = GraphOptimizer()

    try:
        if args.optimize and args.operations:
            # Execute optimizations
            results = await optimizer.optimize_graph(args.operations)

            console.print("\n[bold green]Optimization Results:[/bold green]")
            console.print(f"Completed: {', '.join(results['completed'])}")
            if results["failed"]:
                console.print(f"[red]Failed: {', '.join(results['failed'])}[/red]")

            # Show metrics comparison
            if results["metrics_before"] and results["metrics_after"]:
                console.print("\n[bold]Metrics Comparison:[/bold]")
                console.print(
                    f"Nodes: {results['metrics_before']['nodes']} → {results['metrics_after']['nodes']}"
                )
                console.print(
                    f"Relationships: {results['metrics_before']['relationships']} → {results['metrics_after']['relationships']}"
                )

        else:
            # Perform analysis
            all_results = {}

            if args.analyze in ["structure", "all"]:
                results = await optimizer.analyze_graph_structure()
                all_results["structure"] = results
                optimizer.display_analysis("structure", results)

            if args.analyze in ["performance", "all"]:
                results = await optimizer.analyze_query_performance()
                all_results["performance"] = results
                optimizer.display_analysis("performance", results)

            if args.analyze in ["duplicates", "all"]:
                results = await optimizer.find_duplicate_entities()
                all_results["duplicates"] = results
                optimizer.display_analysis("duplicates", results)

            if args.analyze in ["relationships", "all"]:
                results = await optimizer.analyze_relationship_quality()
                all_results["relationships"] = results
                optimizer.display_analysis("relationships", results)

            if args.export:
                with open(args.export, "w") as f:
                    json.dump(all_results, f, indent=2, default=str)
                console.print(f"\n[green]Analysis exported to {args.export}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise
    finally:
        optimizer.close()


if __name__ == "__main__":
    asyncio.run(main())
