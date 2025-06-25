#!/usr/bin/env python3
"""
RAG Query Analyzer
Analyzes query performance, search relevance, and provides optimization suggestions.

Features:
- Query performance tracking
- Search result relevance scoring
- Vector similarity distribution analysis
- Graph traversal optimization
- Query pattern analysis
"""

import argparse
import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotext as plt
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table

from elf_automations.shared.config import settings
from elf_automations.shared.utils import get_supabase_client

console = Console()


class RAGQueryAnalyzer:
    """Analyze RAG query performance and effectiveness"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.analysis_window = 7  # days

    async def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance metrics"""
        try:
            # Get recent queries
            window_start = datetime.utcnow() - timedelta(days=self.analysis_window)

            queries = (
                self.supabase.table("rag_search_queries")
                .select("*")
                .gte("created_at", window_start.isoformat())
                .order("created_at", desc=True)
                .execute()
            )

            if not queries.data:
                return {"error": "No queries found in analysis window"}

            # Performance metrics
            execution_times = [
                q["execution_time_ms"]
                for q in queries.data
                if q.get("execution_time_ms")
            ]
            result_counts = [
                q["result_count"]
                for q in queries.data
                if q.get("result_count") is not None
            ]

            # Query type distribution
            query_types = defaultdict(int)
            for q in queries.data:
                query_types[q.get("query_type", "unknown")] += 1

            # Time-based analysis
            queries_by_hour = defaultdict(list)
            for q in queries.data:
                created = datetime.fromisoformat(q["created_at"].replace("Z", "+00:00"))
                hour = created.hour
                queries_by_hour[hour].append(q["execution_time_ms"] or 0)

            # Calculate percentiles
            exec_percentiles = {}
            if execution_times:
                exec_percentiles = {
                    "p50": np.percentile(execution_times, 50),
                    "p90": np.percentile(execution_times, 90),
                    "p95": np.percentile(execution_times, 95),
                    "p99": np.percentile(execution_times, 99),
                }

            # Identify slow queries
            slow_threshold = (
                exec_percentiles.get("p95", 1000) if exec_percentiles else 1000
            )
            slow_queries = [
                {
                    "query": q["query_text"][:100],
                    "execution_time": q["execution_time_ms"],
                    "result_count": q.get("result_count", 0),
                    "type": q.get("query_type", "unknown"),
                }
                for q in queries.data
                if q.get("execution_time_ms", 0) > slow_threshold
            ]

            return {
                "total_queries": len(queries.data),
                "avg_execution_time": np.mean(execution_times)
                if execution_times
                else 0,
                "median_execution_time": np.median(execution_times)
                if execution_times
                else 0,
                "percentiles": exec_percentiles,
                "avg_results": np.mean(result_counts) if result_counts else 0,
                "query_type_distribution": dict(query_types),
                "queries_by_hour": {
                    h: np.mean(times) for h, times in queries_by_hour.items()
                },
                "slow_queries": slow_queries[:10],  # Top 10 slowest
            }

        except Exception as e:
            console.print(f"[red]Error analyzing query performance: {str(e)}[/red]")
            return {"error": str(e)}

    async def analyze_search_relevance(self) -> Dict[str, Any]:
        """Analyze search result relevance"""
        try:
            # Get queries with cached results
            queries_with_results = (
                self.supabase.table("rag_search_queries")
                .select("query_text, cached_results, query_config")
                .not_.is_("cached_results", "null")
                .limit(100)
                .execute()
            )

            if not queries_with_results.data:
                return {"error": "No queries with results found"}

            relevance_scores = []
            coverage_stats = []

            for query in queries_with_results.data:
                results = query.get("cached_results", [])
                if not isinstance(results, list):
                    continue

                # Analyze result distribution
                if results:
                    scores = [r.get("score", 0) for r in results if isinstance(r, dict)]
                    if scores:
                        relevance_scores.extend(scores)

                        # Coverage: how many results have high relevance
                        high_relevance = sum(1 for s in scores if s > 0.8)
                        coverage = high_relevance / len(scores) if scores else 0
                        coverage_stats.append(coverage)

            # Analyze score distribution
            score_distribution = {}
            if relevance_scores:
                score_distribution = {
                    "0.0-0.2": sum(1 for s in relevance_scores if 0 <= s < 0.2),
                    "0.2-0.4": sum(1 for s in relevance_scores if 0.2 <= s < 0.4),
                    "0.4-0.6": sum(1 for s in relevance_scores if 0.4 <= s < 0.6),
                    "0.6-0.8": sum(1 for s in relevance_scores if 0.6 <= s < 0.8),
                    "0.8-1.0": sum(1 for s in relevance_scores if 0.8 <= s <= 1.0),
                }

            return {
                "avg_relevance_score": np.mean(relevance_scores)
                if relevance_scores
                else 0,
                "median_relevance_score": np.median(relevance_scores)
                if relevance_scores
                else 0,
                "score_distribution": score_distribution,
                "avg_coverage": np.mean(coverage_stats) if coverage_stats else 0,
                "total_results_analyzed": len(relevance_scores),
            }

        except Exception as e:
            console.print(f"[red]Error analyzing search relevance: {str(e)}[/red]")
            return {"error": str(e)}

    async def analyze_vector_distribution(self) -> Dict[str, Any]:
        """Analyze vector similarity distribution"""
        try:
            # Sample chunks with embeddings
            chunks = (
                self.supabase.table("rag_document_chunks")
                .select("id, document_id, vector_id, metadata")
                .not_.is_("vector_id", "null")
                .limit(1000)
                .execute()
            )

            if not chunks.data:
                return {"error": "No chunks with vectors found"}

            # Group by document
            docs_with_chunks = defaultdict(list)
            for chunk in chunks.data:
                docs_with_chunks[chunk["document_id"]].append(chunk)

            # Analyze chunk distribution
            chunks_per_doc = [len(chunks) for chunks in docs_with_chunks.values()]

            # Estimate vector space coverage
            # (In real implementation, would query Qdrant for actual similarity scores)
            vector_coverage = {
                "total_vectors": len(chunks.data),
                "unique_documents": len(docs_with_chunks),
                "avg_chunks_per_doc": np.mean(chunks_per_doc) if chunks_per_doc else 0,
                "chunk_distribution": {
                    "min": min(chunks_per_doc) if chunks_per_doc else 0,
                    "max": max(chunks_per_doc) if chunks_per_doc else 0,
                    "std": np.std(chunks_per_doc) if chunks_per_doc else 0,
                },
            }

            # Analyze metadata distribution
            metadata_keys = defaultdict(int)
            for chunk in chunks.data:
                if chunk.get("metadata") and isinstance(chunk["metadata"], dict):
                    for key in chunk["metadata"].keys():
                        metadata_keys[key] += 1

            return {
                "vector_coverage": vector_coverage,
                "metadata_distribution": dict(metadata_keys),
                "recommendations": self._generate_vector_recommendations(
                    vector_coverage
                ),
            }

        except Exception as e:
            console.print(f"[red]Error analyzing vector distribution: {str(e)}[/red]")
            return {"error": str(e)}

    async def analyze_graph_traversals(self) -> Dict[str, Any]:
        """Analyze graph query patterns and performance"""
        try:
            # Get entities and relationships
            entities = (
                self.supabase.table("rag_extracted_entities")
                .select("entity_type")
                .limit(1000)
                .execute()
            )

            relationships = (
                self.supabase.table("rag_entity_relationships")
                .select("relationship_type")
                .limit(1000)
                .execute()
            )

            if not entities.data and not relationships.data:
                return {"error": "No graph data found"}

            # Entity type distribution
            entity_types = defaultdict(int)
            for e in entities.data or []:
                entity_types[e["entity_type"]] += 1

            # Relationship type distribution
            rel_types = defaultdict(int)
            for r in relationships.data or []:
                rel_types[r["relationship_type"]] += 1

            # Calculate graph density metrics
            total_entities = len(entities.data) if entities.data else 0
            total_relationships = len(relationships.data) if relationships.data else 0

            # Average degree (relationships per entity)
            avg_degree = (
                (2 * total_relationships) / total_entities if total_entities > 0 else 0
            )

            # Identify most connected entity types
            # (In real implementation, would query Neo4j for actual connectivity)

            return {
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "entity_type_distribution": dict(entity_types),
                "relationship_type_distribution": dict(rel_types),
                "graph_metrics": {
                    "avg_degree": avg_degree,
                    "density": total_relationships
                    / (total_entities * (total_entities - 1))
                    if total_entities > 1
                    else 0,
                },
                "recommendations": self._generate_graph_recommendations(
                    avg_degree, entity_types
                ),
            }

        except Exception as e:
            console.print(f"[red]Error analyzing graph traversals: {str(e)}[/red]")
            return {"error": str(e)}

    async def analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze common query patterns"""
        try:
            # Get recent queries
            queries = (
                self.supabase.table("rag_search_queries")
                .select("query_text, query_type, result_count")
                .order("created_at", desc=True)
                .limit(500)
                .execute()
            )

            if not queries.data:
                return {"error": "No queries found"}

            # Extract query patterns
            patterns = defaultdict(int)
            term_frequency = defaultdict(int)

            for q in queries.data:
                query_text = q["query_text"].lower()

                # Simple pattern extraction
                words = query_text.split()

                # Identify query patterns
                if any(
                    w in ["what", "how", "why", "when", "where", "who"] for w in words
                ):
                    patterns["question"] += 1
                if any(w in ["find", "search", "locate", "get"] for w in words):
                    patterns["search"] += 1
                if any(w in ["compare", "versus", "vs", "difference"] for w in words):
                    patterns["comparison"] += 1
                if len(words) <= 3:
                    patterns["short"] += 1
                elif len(words) > 10:
                    patterns["long"] += 1
                else:
                    patterns["medium"] += 1

                # Term frequency
                for word in words:
                    if len(word) > 3:  # Skip short words
                        term_frequency[word] += 1

            # Get top terms
            top_terms = sorted(
                term_frequency.items(), key=lambda x: x[1], reverse=True
            )[:20]

            # Analyze result distribution by pattern
            pattern_effectiveness = {}
            for pattern in patterns:
                pattern_queries = [
                    q
                    for q in queries.data
                    if self._matches_pattern(q["query_text"], pattern)
                ]
                if pattern_queries:
                    avg_results = np.mean(
                        [q.get("result_count", 0) for q in pattern_queries]
                    )
                    pattern_effectiveness[pattern] = avg_results

            return {
                "total_queries_analyzed": len(queries.data),
                "query_patterns": dict(patterns),
                "top_terms": top_terms,
                "pattern_effectiveness": pattern_effectiveness,
                "recommendations": self._generate_pattern_recommendations(
                    patterns, pattern_effectiveness
                ),
            }

        except Exception as e:
            console.print(f"[red]Error analyzing query patterns: {str(e)}[/red]")
            return {"error": str(e)}

    def _generate_vector_recommendations(self, coverage: Dict[str, Any]) -> List[str]:
        """Generate recommendations for vector optimization"""
        recommendations = []

        avg_chunks = coverage.get("avg_chunks_per_doc", 0)
        if avg_chunks < 5:
            recommendations.append(
                "Consider more granular chunking for better search precision"
            )
        elif avg_chunks > 50:
            recommendations.append(
                "High chunk count per document may impact search performance"
            )

        chunk_std = coverage.get("chunk_distribution", {}).get("std", 0)
        if chunk_std > avg_chunks * 0.5:
            recommendations.append(
                "High variance in chunk distribution - consider normalizing chunking strategy"
            )

        return recommendations

    def _generate_graph_recommendations(
        self, avg_degree: float, entity_types: Dict[str, int]
    ) -> List[str]:
        """Generate recommendations for graph optimization"""
        recommendations = []

        if avg_degree < 2:
            recommendations.append(
                "Low graph connectivity - consider extracting more relationships"
            )
        elif avg_degree > 10:
            recommendations.append(
                "High graph density may impact traversal performance"
            )

        if len(entity_types) < 3:
            recommendations.append(
                "Limited entity types - consider expanding entity extraction"
            )

        # Check for imbalanced distribution
        if entity_types:
            counts = list(entity_types.values())
            max_count = max(counts)
            min_count = min(counts)
            if max_count > min_count * 10:
                recommendations.append("Highly imbalanced entity distribution detected")

        return recommendations

    def _generate_pattern_recommendations(
        self, patterns: Dict[str, int], effectiveness: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations for query optimization"""
        recommendations = []

        total_queries = sum(patterns.values())

        # Check for pattern distribution
        if patterns.get("short", 0) > total_queries * 0.5:
            recommendations.append(
                "Many short queries - consider query expansion or suggestions"
            )

        if patterns.get("long", 0) > total_queries * 0.3:
            recommendations.append("Many long queries - consider query summarization")

        # Check effectiveness
        for pattern, avg_results in effectiveness.items():
            if avg_results < 1:
                recommendations.append(
                    f"Low results for {pattern} queries - review indexing strategy"
                )

        return recommendations

    def _matches_pattern(self, query_text: str, pattern: str) -> bool:
        """Check if query matches a pattern"""
        query_lower = query_text.lower()

        if pattern == "question":
            return any(
                w in query_lower for w in ["what", "how", "why", "when", "where", "who"]
            )
        elif pattern == "search":
            return any(w in query_lower for w in ["find", "search", "locate", "get"])
        elif pattern == "comparison":
            return any(
                w in query_lower for w in ["compare", "versus", "vs", "difference"]
            )
        elif pattern == "short":
            return len(query_lower.split()) <= 3
        elif pattern == "long":
            return len(query_lower.split()) > 10

        return False

    def display_performance_analysis(self, analysis: Dict[str, Any]):
        """Display query performance analysis"""
        table = Table(title="Query Performance Analysis", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Queries", str(analysis.get("total_queries", 0)))
        table.add_row(
            "Avg Execution Time", f"{analysis.get('avg_execution_time', 0):.1f} ms"
        )
        table.add_row(
            "Median Execution Time",
            f"{analysis.get('median_execution_time', 0):.1f} ms",
        )

        # Percentiles
        percentiles = analysis.get("percentiles", {})
        if percentiles:
            table.add_section()
            for p, value in percentiles.items():
                table.add_row(f"{p.upper()} Latency", f"{value:.1f} ms")

        # Query types
        table.add_section()
        query_types = analysis.get("query_type_distribution", {})
        for qtype, count in query_types.items():
            table.add_row(f"{qtype.title()} Queries", str(count))

        console.print(table)

        # Show slow queries
        slow_queries = analysis.get("slow_queries", [])
        if slow_queries:
            console.print("\n[yellow]Slowest Queries:[/yellow]")
            slow_table = Table()
            slow_table.add_column("Query", style="white")
            slow_table.add_column("Time (ms)", style="red")
            slow_table.add_column("Results", style="cyan")

            for sq in slow_queries[:5]:
                slow_table.add_row(
                    sq["query"][:60] + "...",
                    str(sq["execution_time"]),
                    str(sq["result_count"]),
                )

            console.print(slow_table)

    def display_relevance_analysis(self, analysis: Dict[str, Any]):
        """Display search relevance analysis"""
        table = Table(title="Search Relevance Analysis", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row(
            "Avg Relevance Score", f"{analysis.get('avg_relevance_score', 0):.3f}"
        )
        table.add_row(
            "Median Relevance Score", f"{analysis.get('median_relevance_score', 0):.3f}"
        )
        table.add_row("Avg Coverage", f"{analysis.get('avg_coverage', 0):.1%}")
        table.add_row("Total Results", str(analysis.get("total_results_analyzed", 0)))

        console.print(table)

        # Score distribution
        dist = analysis.get("score_distribution", {})
        if dist:
            console.print("\n[yellow]Score Distribution:[/yellow]")
            dist_table = Table()
            dist_table.add_column("Range", style="cyan")
            dist_table.add_column("Count", style="magenta")
            dist_table.add_column("Percentage", style="green")

            total = sum(dist.values())
            for range_key, count in sorted(dist.items()):
                percentage = (count / total * 100) if total > 0 else 0
                dist_table.add_row(range_key, str(count), f"{percentage:.1f}%")

            console.print(dist_table)

    def display_recommendations(self, all_analyses: Dict[str, Dict[str, Any]]):
        """Display all recommendations"""
        console.print("\n[bold yellow]Optimization Recommendations:[/bold yellow]")

        recommendation_count = 0

        for analysis_type, analysis in all_analyses.items():
            if "recommendations" in analysis and analysis["recommendations"]:
                console.print(
                    f"\n[cyan]{analysis_type.replace('_', ' ').title()}:[/cyan]"
                )
                for rec in analysis["recommendations"]:
                    recommendation_count += 1
                    console.print(f"  {recommendation_count}. {rec}")

        if recommendation_count == 0:
            console.print(
                "[green]No specific optimizations recommended at this time.[/green]"
            )

    async def generate_report(self, output_file: str):
        """Generate comprehensive analysis report"""
        console.print("[yellow]Generating RAG query analysis report...[/yellow]")

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_window_days": self.analysis_window,
            "performance": await self.analyze_query_performance(),
            "relevance": await self.analyze_search_relevance(),
            "vector_distribution": await self.analyze_vector_distribution(),
            "graph_traversals": await self.analyze_graph_traversals(),
            "query_patterns": await self.analyze_query_patterns(),
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        console.print(f"[green]Report saved to {output_file}[/green]")
        return report


async def main():
    parser = argparse.ArgumentParser(description="RAG Query Analyzer")
    parser.add_argument("--window", type=int, default=7, help="Analysis window in days")
    parser.add_argument("--report", type=str, help="Generate report to file")
    parser.add_argument(
        "--component",
        choices=["performance", "relevance", "vectors", "graph", "patterns", "all"],
        default="all",
        help="Component to analyze",
    )

    args = parser.parse_args()

    analyzer = RAGQueryAnalyzer()
    analyzer.analysis_window = args.window

    try:
        if args.report:
            report = await analyzer.generate_report(args.report)
            # Display summary
            analyzer.display_performance_analysis(report["performance"])
            analyzer.display_relevance_analysis(report["relevance"])
            analyzer.display_recommendations(report)
        else:
            # Interactive analysis
            if args.component in ["performance", "all"]:
                console.print("\n[bold blue]Query Performance Analysis[/bold blue]")
                perf = await analyzer.analyze_query_performance()
                analyzer.display_performance_analysis(perf)

            if args.component in ["relevance", "all"]:
                console.print("\n[bold blue]Search Relevance Analysis[/bold blue]")
                rel = await analyzer.analyze_search_relevance()
                analyzer.display_relevance_analysis(rel)

            if args.component in ["vectors", "all"]:
                console.print("\n[bold blue]Vector Distribution Analysis[/bold blue]")
                vec = await analyzer.analyze_vector_distribution()
                console.print(Panel(json.dumps(vec, indent=2), title="Vector Analysis"))

            if args.component in ["graph", "all"]:
                console.print("\n[bold blue]Graph Traversal Analysis[/bold blue]")
                graph = await analyzer.analyze_graph_traversals()
                console.print(
                    Panel(json.dumps(graph, indent=2), title="Graph Analysis")
                )

            if args.component in ["patterns", "all"]:
                console.print("\n[bold blue]Query Pattern Analysis[/bold blue]")
                patterns = await analyzer.analyze_query_patterns()
                console.print(
                    Panel(json.dumps(patterns, indent=2), title="Pattern Analysis")
                )

            # Show recommendations
            if args.component == "all":
                all_analyses = {
                    "performance": perf if "perf" in locals() else {},
                    "relevance": rel if "rel" in locals() else {},
                    "vectors": vec if "vec" in locals() else {},
                    "graph": graph if "graph" in locals() else {},
                    "patterns": patterns if "patterns" in locals() else {},
                }
                analyzer.display_recommendations(all_analyses)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())
