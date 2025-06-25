#!/usr/bin/env python3
"""
RAG Analytics Dashboard
Real-time monitoring and analytics for the RAG processing system.

Features:
- Processing queue monitoring
- Document processing metrics
- Storage utilization tracking
- Entity extraction statistics
- Chunking strategy effectiveness
"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotext as plt
from rich.chart import Chart
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text

from elf_automations.shared.config import settings
from elf_automations.shared.utils import get_supabase_client

console = Console()


class RAGAnalyticsDashboard:
    """Real-time analytics dashboard for RAG system"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.refresh_interval = 5  # seconds
        self.time_window = 24  # hours

    async def get_queue_metrics(self) -> Dict[str, Any]:
        """Get processing queue metrics"""
        try:
            # Get queue status counts
            result = self.supabase.rpc("get_queue_status_counts").execute()
            queue_counts = result.data if result.data else {}

            # Get processing rates
            now = datetime.utcnow()
            window_start = now - timedelta(hours=self.time_window)

            # Documents processed in time window
            processed = (
                self.supabase.table("rag_processing_queue")
                .select("*")
                .eq("status", "completed")
                .gte("completed_at", window_start.isoformat())
                .execute()
            )

            # Average processing time
            processing_times = []
            if processed.data:
                for item in processed.data:
                    if item.get("started_at") and item.get("completed_at"):
                        start = datetime.fromisoformat(
                            item["started_at"].replace("Z", "+00:00")
                        )
                        end = datetime.fromisoformat(
                            item["completed_at"].replace("Z", "+00:00")
                        )
                        processing_times.append((end - start).total_seconds())

            avg_processing_time = (
                sum(processing_times) / len(processing_times) if processing_times else 0
            )

            # Queue backlog trend
            backlog_trend = (
                self.supabase.table("rag_processing_queue")
                .select("created_at")
                .eq("status", "pending")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )

            return {
                "counts": queue_counts,
                "processed_24h": len(processed.data) if processed.data else 0,
                "avg_processing_time": avg_processing_time,
                "processing_rate": len(processed.data) / 24 if processed.data else 0,
                "backlog_size": len(backlog_trend.data) if backlog_trend.data else 0,
                "oldest_pending": backlog_trend.data[-1]["created_at"]
                if backlog_trend.data
                else None,
            }

        except Exception as e:
            console.print(f"[red]Error getting queue metrics: {str(e)}[/red]")
            return {}

    async def get_document_metrics(self) -> Dict[str, Any]:
        """Get document processing metrics"""
        try:
            # Document status distribution
            status_result = self.supabase.rpc(
                "get_document_status_distribution"
            ).execute()
            status_dist = status_result.data if status_result.data else {}

            # Document types processed
            types_result = (
                self.supabase.table("rag_documents")
                .select(
                    "document_type_id, rag_document_types!inner(name, display_name)"
                )
                .eq("status", "completed")
                .execute()
            )

            type_counts = {}
            if types_result.data:
                for doc in types_result.data:
                    if doc.get("rag_document_types"):
                        type_name = doc["rag_document_types"]["display_name"]
                        type_counts[type_name] = type_counts.get(type_name, 0) + 1

            # Success/failure rates
            window_start = datetime.utcnow() - timedelta(hours=self.time_window)

            recent_docs = (
                self.supabase.table("rag_documents")
                .select("status, processing_error")
                .gte("created_at", window_start.isoformat())
                .execute()
            )

            total_recent = len(recent_docs.data) if recent_docs.data else 0
            failed_recent = sum(
                1 for doc in (recent_docs.data or []) if doc["status"] == "failed"
            )
            success_rate = (
                ((total_recent - failed_recent) / total_recent * 100)
                if total_recent > 0
                else 0
            )

            # Processing time by document type
            processing_times_by_type = {}
            completed_docs = (
                self.supabase.table("rag_documents")
                .select(
                    "document_type_id, processing_started_at, processing_completed_at, rag_document_types!inner(display_name)"
                )
                .eq("status", "completed")
                .not_.is_("processing_started_at", "null")
                .not_.is_("processing_completed_at", "null")
                .limit(100)
                .execute()
            )

            if completed_docs.data:
                for doc in completed_docs.data:
                    if doc.get("rag_document_types"):
                        type_name = doc["rag_document_types"]["display_name"]
                        start = datetime.fromisoformat(
                            doc["processing_started_at"].replace("Z", "+00:00")
                        )
                        end = datetime.fromisoformat(
                            doc["processing_completed_at"].replace("Z", "+00:00")
                        )
                        time_taken = (end - start).total_seconds()

                        if type_name not in processing_times_by_type:
                            processing_times_by_type[type_name] = []
                        processing_times_by_type[type_name].append(time_taken)

            # Calculate averages
            avg_times_by_type = {
                type_name: sum(times) / len(times)
                for type_name, times in processing_times_by_type.items()
            }

            return {
                "status_distribution": status_dist,
                "type_counts": type_counts,
                "success_rate": success_rate,
                "total_processed_24h": total_recent,
                "failed_24h": failed_recent,
                "avg_processing_times": avg_times_by_type,
            }

        except Exception as e:
            console.print(f"[red]Error getting document metrics: {str(e)}[/red]")
            return {}

    async def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage utilization metrics"""
        try:
            # Document storage stats
            storage_result = (
                self.supabase.table("rag_documents")
                .select("size_bytes, status")
                .eq("status", "completed")
                .execute()
            )

            total_size = sum(
                doc.get("size_bytes", 0) for doc in (storage_result.data or [])
            )
            total_docs = len(storage_result.data) if storage_result.data else 0
            avg_doc_size = total_size / total_docs if total_docs > 0 else 0

            # Chunk statistics
            chunks_result = (
                self.supabase.table("rag_document_chunks")
                .select("tokens, document_id")
                .execute()
            )

            total_chunks = len(chunks_result.data) if chunks_result.data else 0
            total_tokens = sum(
                chunk.get("tokens", 0) for chunk in (chunks_result.data or [])
            )

            # Chunks per document
            chunks_per_doc = {}
            if chunks_result.data:
                for chunk in chunks_result.data:
                    doc_id = chunk["document_id"]
                    chunks_per_doc[doc_id] = chunks_per_doc.get(doc_id, 0) + 1

            avg_chunks_per_doc = (
                sum(chunks_per_doc.values()) / len(chunks_per_doc)
                if chunks_per_doc
                else 0
            )

            # Vector storage (simulate Qdrant stats)
            vectors_result = (
                self.supabase.table("rag_document_chunks")
                .select("vector_id")
                .not_.is_("vector_id", "null")
                .execute()
            )

            total_vectors = len(vectors_result.data) if vectors_result.data else 0

            return {
                "total_size_gb": total_size / (1024**3),
                "total_documents": total_docs,
                "avg_document_size_mb": avg_doc_size / (1024**2),
                "total_chunks": total_chunks,
                "total_tokens": total_tokens,
                "avg_chunks_per_doc": avg_chunks_per_doc,
                "total_vectors": total_vectors,
                "vector_coverage": (total_vectors / total_chunks * 100)
                if total_chunks > 0
                else 0,
            }

        except Exception as e:
            console.print(f"[red]Error getting storage metrics: {str(e)}[/red]")
            return {}

    async def get_entity_metrics(self) -> Dict[str, Any]:
        """Get entity extraction metrics"""
        try:
            # Entity type distribution
            entities_result = (
                self.supabase.table("rag_extracted_entities")
                .select("entity_type, confidence")
                .execute()
            )

            entity_type_counts = {}
            confidence_by_type = {}

            if entities_result.data:
                for entity in entities_result.data:
                    etype = entity["entity_type"]
                    entity_type_counts[etype] = entity_type_counts.get(etype, 0) + 1

                    if etype not in confidence_by_type:
                        confidence_by_type[etype] = []
                    confidence_by_type[etype].append(entity.get("confidence", 1.0))

            # Calculate average confidence by type
            avg_confidence_by_type = {
                etype: sum(confs) / len(confs)
                for etype, confs in confidence_by_type.items()
            }

            # Relationships statistics
            relationships_result = (
                self.supabase.table("rag_entity_relationships")
                .select("relationship_type")
                .execute()
            )

            relationship_counts = {}
            if relationships_result.data:
                for rel in relationships_result.data:
                    rtype = rel["relationship_type"]
                    relationship_counts[rtype] = relationship_counts.get(rtype, 0) + 1

            # Entities per document
            entities_per_doc = (
                self.supabase.table("rag_extracted_entities")
                .select("document_id")
                .execute()
            )

            doc_entity_counts = {}
            if entities_per_doc.data:
                for entity in entities_per_doc.data:
                    doc_id = entity["document_id"]
                    doc_entity_counts[doc_id] = doc_entity_counts.get(doc_id, 0) + 1

            avg_entities_per_doc = (
                sum(doc_entity_counts.values()) / len(doc_entity_counts)
                if doc_entity_counts
                else 0
            )

            return {
                "total_entities": sum(entity_type_counts.values()),
                "entity_type_distribution": entity_type_counts,
                "avg_confidence_by_type": avg_confidence_by_type,
                "total_relationships": sum(relationship_counts.values()),
                "relationship_type_distribution": relationship_counts,
                "avg_entities_per_document": avg_entities_per_doc,
            }

        except Exception as e:
            console.print(f"[red]Error getting entity metrics: {str(e)}[/red]")
            return {}

    async def get_chunking_metrics(self) -> Dict[str, Any]:
        """Get chunking strategy effectiveness metrics"""
        try:
            # Get documents with chunking info
            docs_with_chunks = (
                self.supabase.table("rag_documents")
                .select(
                    "id, document_type_id, rag_document_chunks(chunk_index, tokens)"
                )
                .eq("status", "completed")
                .execute()
            )

            strategy_effectiveness = {}

            # Analyze chunking patterns
            if docs_with_chunks.data:
                for doc in docs_with_chunks.data:
                    chunks = doc.get("rag_document_chunks", [])
                    if chunks:
                        num_chunks = len(chunks)
                        total_tokens = sum(chunk.get("tokens", 0) for chunk in chunks)
                        avg_tokens = total_tokens / num_chunks if num_chunks > 0 else 0

                        # Estimate strategy based on patterns
                        if avg_tokens < 200:
                            strategy = "sliding_window"
                        elif avg_tokens > 500:
                            strategy = "structural"
                        else:
                            strategy = "semantic"

                        if strategy not in strategy_effectiveness:
                            strategy_effectiveness[strategy] = {
                                "count": 0,
                                "avg_chunks": 0,
                                "avg_tokens_per_chunk": 0,
                                "total_chunks": 0,
                                "total_tokens": 0,
                            }

                        stats = strategy_effectiveness[strategy]
                        stats["count"] += 1
                        stats["total_chunks"] += num_chunks
                        stats["total_tokens"] += total_tokens

            # Calculate averages
            for strategy, stats in strategy_effectiveness.items():
                if stats["count"] > 0:
                    stats["avg_chunks"] = stats["total_chunks"] / stats["count"]
                    stats["avg_tokens_per_chunk"] = (
                        stats["total_tokens"] / stats["total_chunks"]
                    )

            # Chunk size distribution
            all_chunks = (
                self.supabase.table("rag_document_chunks")
                .select("tokens")
                .limit(1000)
                .execute()
            )

            chunk_sizes = [
                chunk["tokens"]
                for chunk in (all_chunks.data or [])
                if chunk.get("tokens")
            ]

            size_distribution = {
                "small": sum(1 for size in chunk_sizes if size < 200),
                "medium": sum(1 for size in chunk_sizes if 200 <= size < 500),
                "large": sum(1 for size in chunk_sizes if size >= 500),
            }

            return {
                "strategy_effectiveness": strategy_effectiveness,
                "chunk_size_distribution": size_distribution,
                "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes)
                if chunk_sizes
                else 0,
                "total_chunks_analyzed": len(chunk_sizes),
            }

        except Exception as e:
            console.print(f"[red]Error getting chunking metrics: {str(e)}[/red]")
            return {}

    def create_queue_panel(self, metrics: Dict[str, Any]) -> Panel:
        """Create queue status panel"""
        table = Table(title="Processing Queue Status", expand=True)
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta")

        counts = metrics.get("counts", {})
        for status, count in counts.items():
            style = (
                "green"
                if status == "completed"
                else "yellow"
                if status == "processing"
                else "red"
                if status == "failed"
                else "white"
            )
            table.add_row(status.title(), f"[{style}]{count}[/{style}]")

        # Add summary stats
        table.add_section()
        table.add_row("Processed (24h)", str(metrics.get("processed_24h", 0)))
        table.add_row(
            "Avg Processing Time", f"{metrics.get('avg_processing_time', 0):.1f}s"
        )
        table.add_row(
            "Processing Rate", f"{metrics.get('processing_rate', 0):.1f}/hour"
        )

        if metrics.get("oldest_pending"):
            oldest = datetime.fromisoformat(
                metrics["oldest_pending"].replace("Z", "+00:00")
            )
            age = datetime.utcnow() - oldest.replace(tzinfo=None)
            table.add_row(
                "Oldest Pending", f"{age.total_seconds() / 3600:.1f} hours ago"
            )

        return Panel(table, title="Queue Analytics", border_style="blue")

    def create_document_panel(self, metrics: Dict[str, Any]) -> Panel:
        """Create document metrics panel"""
        table = Table(title="Document Processing Metrics", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        # Success rate
        success_rate = metrics.get("success_rate", 0)
        color = (
            "green" if success_rate > 90 else "yellow" if success_rate > 70 else "red"
        )
        table.add_row("Success Rate", f"[{color}]{success_rate:.1f}%[/{color}]")
        table.add_row("Total (24h)", str(metrics.get("total_processed_24h", 0)))
        table.add_row("Failed (24h)", f"[red]{metrics.get('failed_24h', 0)}[/red]")

        # Document types
        table.add_section()
        type_counts = metrics.get("type_counts", {})
        for doc_type, count in sorted(
            type_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            table.add_row(f"  {doc_type}", str(count))

        # Processing times
        table.add_section()
        avg_times = metrics.get("avg_processing_times", {})
        for doc_type, avg_time in sorted(avg_times.items(), key=lambda x: x[1])[:5]:
            table.add_row(f"  {doc_type}", f"{avg_time:.1f}s")

        return Panel(table, title="Document Analytics", border_style="green")

    def create_storage_panel(self, metrics: Dict[str, Any]) -> Panel:
        """Create storage metrics panel"""
        table = Table(title="Storage Utilization", expand=True)
        table.add_column("Resource", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Size", f"{metrics.get('total_size_gb', 0):.2f} GB")
        table.add_row("Documents", str(metrics.get("total_documents", 0)))
        table.add_row(
            "Avg Doc Size", f"{metrics.get('avg_document_size_mb', 0):.1f} MB"
        )

        table.add_section()
        table.add_row("Total Chunks", str(metrics.get("total_chunks", 0)))
        table.add_row("Total Tokens", f"{metrics.get('total_tokens', 0):,}")
        table.add_row("Avg Chunks/Doc", f"{metrics.get('avg_chunks_per_doc', 0):.1f}")

        table.add_section()
        table.add_row("Vector Count", str(metrics.get("total_vectors", 0)))
        coverage = metrics.get("vector_coverage", 0)
        color = "green" if coverage > 90 else "yellow" if coverage > 70 else "red"
        table.add_row("Vector Coverage", f"[{color}]{coverage:.1f}%[/{color}]")

        return Panel(table, title="Storage Analytics", border_style="yellow")

    def create_entity_panel(self, metrics: Dict[str, Any]) -> Panel:
        """Create entity extraction panel"""
        table = Table(title="Entity Extraction Stats", expand=True)
        table.add_column("Entity Type", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Avg Confidence", style="green")

        entity_types = metrics.get("entity_type_distribution", {})
        confidence = metrics.get("avg_confidence_by_type", {})

        for etype in sorted(entity_types.keys()):
            count = entity_types[etype]
            avg_conf = confidence.get(etype, 0)
            conf_color = (
                "green" if avg_conf > 0.8 else "yellow" if avg_conf > 0.6 else "red"
            )
            table.add_row(
                etype, str(count), f"[{conf_color}]{avg_conf:.2f}[/{conf_color}]"
            )

        table.add_section()
        table.add_row("Total Entities", str(metrics.get("total_entities", 0)), "")
        table.add_row(
            "Total Relationships", str(metrics.get("total_relationships", 0)), ""
        )
        table.add_row(
            "Avg Entities/Doc", f"{metrics.get('avg_entities_per_document', 0):.1f}", ""
        )

        return Panel(table, title="Entity Analytics", border_style="purple")

    def create_chunking_panel(self, metrics: Dict[str, Any]) -> Panel:
        """Create chunking strategy panel"""
        table = Table(title="Chunking Strategy Analysis", expand=True)
        table.add_column("Strategy", style="cyan")
        table.add_column("Documents", style="magenta")
        table.add_column("Avg Chunks", style="yellow")
        table.add_column("Avg Tokens", style="green")

        strategies = metrics.get("strategy_effectiveness", {})
        for strategy, stats in strategies.items():
            table.add_row(
                strategy.replace("_", " ").title(),
                str(stats["count"]),
                f"{stats['avg_chunks']:.1f}",
                f"{stats['avg_tokens_per_chunk']:.0f}",
            )

        # Chunk size distribution
        table.add_section()
        size_dist = metrics.get("chunk_size_distribution", {})
        table.add_row("Small (<200)", str(size_dist.get("small", 0)), "", "")
        table.add_row("Medium (200-500)", str(size_dist.get("medium", 0)), "", "")
        table.add_row("Large (>500)", str(size_dist.get("large", 0)), "", "")

        return Panel(table, title="Chunking Analytics", border_style="cyan")

    def create_layout(self) -> Layout:
        """Create dashboard layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        layout["main"].split_row(
            Layout(name="left"), Layout(name="center"), Layout(name="right")
        )

        layout["left"].split_column(Layout(name="queue"), Layout(name="storage"))

        layout["center"].split_column(Layout(name="documents"), Layout(name="entities"))

        layout["right"].split_column(Layout(name="chunking"), Layout(name="alerts"))

        return layout

    def create_header(self) -> Panel:
        """Create header panel"""
        return Panel(
            Text(
                "RAG System Analytics Dashboard", style="bold magenta", justify="center"
            ),
            border_style="bright_blue",
        )

    def create_footer(self) -> Panel:
        """Create footer panel"""
        return Panel(
            Text(
                f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Refresh: {self.refresh_interval}s",
                style="dim",
                justify="center",
            ),
            border_style="bright_blue",
        )

    def create_alerts_panel(self, all_metrics: Dict[str, Dict[str, Any]]) -> Panel:
        """Create alerts panel based on metrics"""
        alerts = []

        # Check queue backlog
        queue_metrics = all_metrics.get("queue", {})
        backlog = queue_metrics.get("backlog_size", 0)
        if backlog > 100:
            alerts.append(("[red]HIGH[/red]", f"Queue backlog: {backlog} documents"))

        # Check success rate
        doc_metrics = all_metrics.get("documents", {})
        success_rate = doc_metrics.get("success_rate", 100)
        if success_rate < 90:
            alerts.append(
                ("[yellow]WARN[/yellow]", f"Success rate: {success_rate:.1f}%")
            )

        # Check vector coverage
        storage_metrics = all_metrics.get("storage", {})
        coverage = storage_metrics.get("vector_coverage", 100)
        if coverage < 95:
            alerts.append(
                ("[yellow]WARN[/yellow]", f"Vector coverage: {coverage:.1f}%")
            )

        # Create alerts table
        table = Table(title="System Alerts", expand=True)
        table.add_column("Level", style="cyan")
        table.add_column("Alert", style="white")

        if alerts:
            for level, message in alerts:
                table.add_row(level, message)
        else:
            table.add_row("[green]OK[/green]", "All systems operational")

        return Panel(table, title="Alerts", border_style="red" if alerts else "green")

    async def run_dashboard(self):
        """Run the dashboard with live updates"""
        layout = self.create_layout()

        with Live(layout, refresh_per_second=1, console=console) as live:
            while True:
                try:
                    # Gather all metrics
                    queue_metrics = await self.get_queue_metrics()
                    doc_metrics = await self.get_document_metrics()
                    storage_metrics = await self.get_storage_metrics()
                    entity_metrics = await self.get_entity_metrics()
                    chunking_metrics = await self.get_chunking_metrics()

                    all_metrics = {
                        "queue": queue_metrics,
                        "documents": doc_metrics,
                        "storage": storage_metrics,
                        "entities": entity_metrics,
                        "chunking": chunking_metrics,
                    }

                    # Update layout
                    layout["header"].update(self.create_header())
                    layout["queue"].update(self.create_queue_panel(queue_metrics))
                    layout["documents"].update(self.create_document_panel(doc_metrics))
                    layout["storage"].update(self.create_storage_panel(storage_metrics))
                    layout["entities"].update(self.create_entity_panel(entity_metrics))
                    layout["chunking"].update(
                        self.create_chunking_panel(chunking_metrics)
                    )
                    layout["alerts"].update(self.create_alerts_panel(all_metrics))
                    layout["footer"].update(self.create_footer())

                    # Wait before next update
                    await asyncio.sleep(self.refresh_interval)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    console.print(f"[red]Dashboard error: {str(e)}[/red]")
                    await asyncio.sleep(self.refresh_interval)


async def export_metrics(dashboard: RAGAnalyticsDashboard, output_file: str):
    """Export metrics to JSON file"""
    console.print(f"[yellow]Exporting metrics to {output_file}...[/yellow]")

    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "queue": await dashboard.get_queue_metrics(),
        "documents": await dashboard.get_document_metrics(),
        "storage": await dashboard.get_storage_metrics(),
        "entities": await dashboard.get_entity_metrics(),
        "chunking": await dashboard.get_chunking_metrics(),
    }

    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    console.print(f"[green]Metrics exported to {output_file}[/green]")


def main():
    parser = argparse.ArgumentParser(description="RAG Analytics Dashboard")
    parser.add_argument("--export", type=str, help="Export metrics to JSON file")
    parser.add_argument(
        "--refresh", type=int, default=5, help="Refresh interval in seconds"
    )
    parser.add_argument("--window", type=int, default=24, help="Time window in hours")

    args = parser.parse_args()

    dashboard = RAGAnalyticsDashboard()
    dashboard.refresh_interval = args.refresh
    dashboard.time_window = args.window

    if args.export:
        asyncio.run(export_metrics(dashboard, args.export))
    else:
        try:
            asyncio.run(dashboard.run_dashboard())
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped[/yellow]")


if __name__ == "__main__":
    main()
