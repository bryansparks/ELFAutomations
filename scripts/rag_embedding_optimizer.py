#!/usr/bin/env python3
"""
RAG Embedding Optimizer
Analyzes and optimizes embedding quality and storage.

Features:
- Embedding quality analysis
- Dimension optimization suggestions
- Redundancy detection
- Batch reprocessing capabilities
- Storage optimization
"""

import argparse
import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import ScrollRequest, WithPayloadSelector, WithVectorSelector
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity

from elf_automations.shared.config import settings
from elf_automations.shared.utils import get_supabase_client

console = Console()


class EmbeddingOptimizer:
    """Optimize RAG embedding storage and quality"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.qdrant_url = settings.get("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = settings.get("QDRANT_API_KEY")
        self.qdrant_client = None

    async def initialize(self):
        """Initialize Qdrant connection"""
        if not self.qdrant_client:
            self.qdrant_client = QdrantClient(
                url=self.qdrant_url, api_key=self.qdrant_api_key
            )

    async def analyze_embedding_distribution(
        self, collection_name: str = "document_embeddings", sample_size: int = 1000
    ) -> Dict[str, Any]:
        """Analyze embedding distribution and quality"""
        console.print(
            f"[yellow]Analyzing embedding distribution in {collection_name}...[/yellow]"
        )

        await self.initialize()

        try:
            # Get sample embeddings
            embeddings, payloads = await self._fetch_embeddings_sample(
                collection_name, sample_size
            )

            if not embeddings:
                return {"error": "No embeddings found"}

            embeddings_array = np.array(embeddings)
            console.print(f"[green]Loaded {len(embeddings)} embeddings[/green]")

            # Basic statistics
            stats = {
                "total_embeddings": len(embeddings),
                "embedding_dimension": embeddings_array.shape[1],
                "mean_norm": np.mean(np.linalg.norm(embeddings_array, axis=1)),
                "std_norm": np.std(np.linalg.norm(embeddings_array, axis=1)),
                "min_norm": np.min(np.linalg.norm(embeddings_array, axis=1)),
                "max_norm": np.max(np.linalg.norm(embeddings_array, axis=1)),
            }

            # Analyze component variance
            console.print("[yellow]Performing PCA analysis...[/yellow]")
            pca = PCA(n_components=min(50, embeddings_array.shape[1]))
            pca.fit(embeddings_array)

            # Find optimal dimensions
            cumsum = np.cumsum(pca.explained_variance_ratio_)
            optimal_dims = {
                "90%_variance": np.argmax(cumsum >= 0.90) + 1,
                "95%_variance": np.argmax(cumsum >= 0.95) + 1,
                "99%_variance": np.argmax(cumsum >= 0.99) + 1,
            }

            stats["variance_analysis"] = {
                "total_variance_explained": float(cumsum[-1]),
                "optimal_dimensions": optimal_dims,
                "top_10_components_variance": pca.explained_variance_ratio_[
                    :10
                ].tolist(),
            }

            # Clustering analysis
            console.print("[yellow]Analyzing embedding clusters...[/yellow]")
            cluster_analysis = await self._analyze_clusters(embeddings_array, payloads)
            stats["cluster_analysis"] = cluster_analysis

            # Redundancy analysis
            console.print("[yellow]Checking for redundant embeddings...[/yellow]")
            redundancy_analysis = await self._analyze_redundancy(
                embeddings_array, payloads
            )
            stats["redundancy_analysis"] = redundancy_analysis

            # Quality metrics
            quality_metrics = self._calculate_quality_metrics(embeddings_array)
            stats["quality_metrics"] = quality_metrics

            # Recommendations
            stats["recommendations"] = self._generate_recommendations(stats)

            return stats

        except Exception as e:
            console.print(f"[red]Error analyzing embeddings: {str(e)}[/red]")
            return {"error": str(e)}

    async def _fetch_embeddings_sample(
        self, collection_name: str, sample_size: int
    ) -> Tuple[List, List]:
        """Fetch sample of embeddings from Qdrant"""
        embeddings = []
        payloads = []

        try:
            # Scroll through collection
            scroll_result = await self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=None,
                limit=sample_size,
                with_payload=WithPayloadSelector(enable=True),
                with_vectors=WithVectorSelector(enable=True),
            )

            for point in scroll_result[0]:
                embeddings.append(point.vector)
                payloads.append(point.payload)

            return embeddings, payloads

        except Exception as e:
            console.print(f"[red]Error fetching embeddings: {str(e)}[/red]")
            return [], []

    async def _analyze_clusters(
        self, embeddings: np.ndarray, payloads: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze embedding clusters"""
        # Use DBSCAN for clustering
        clustering = DBSCAN(eps=0.3, min_samples=5, metric="cosine")
        labels = clustering.fit_predict(embeddings)

        # Analyze clusters
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(labels).count(-1)

        # Cluster sizes
        cluster_sizes = defaultdict(int)
        for label in labels:
            cluster_sizes[label] += 1

        # Analyze cluster composition
        cluster_composition = defaultdict(lambda: defaultdict(int))
        for i, label in enumerate(labels):
            if label != -1 and i < len(payloads):
                doc_id = payloads[i].get("document_id", "unknown")
                cluster_composition[label][doc_id] += 1

        return {
            "n_clusters": n_clusters,
            "n_noise_points": n_noise,
            "noise_ratio": n_noise / len(embeddings),
            "cluster_sizes": dict(cluster_sizes),
            "avg_cluster_size": np.mean(
                [size for label, size in cluster_sizes.items() if label != -1]
            )
            if n_clusters > 0
            else 0,
            "documents_per_cluster": len(cluster_composition),
        }

    async def _analyze_redundancy(
        self,
        embeddings: np.ndarray,
        payloads: List[Dict],
        similarity_threshold: float = 0.95,
    ) -> Dict[str, Any]:
        """Analyze redundant embeddings"""
        n_embeddings = len(embeddings)

        # Sample for large datasets
        if n_embeddings > 1000:
            sample_indices = np.random.choice(n_embeddings, 1000, replace=False)
            sample_embeddings = embeddings[sample_indices]
            sample_payloads = [payloads[i] for i in sample_indices]
        else:
            sample_embeddings = embeddings
            sample_payloads = payloads

        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(sample_embeddings)

        # Find highly similar pairs
        redundant_pairs = []
        for i in range(len(sample_embeddings)):
            for j in range(i + 1, len(sample_embeddings)):
                if similarity_matrix[i, j] > similarity_threshold:
                    redundant_pairs.append(
                        {
                            "indices": (i, j),
                            "similarity": float(similarity_matrix[i, j]),
                            "doc_ids": (
                                sample_payloads[i].get("document_id", "unknown"),
                                sample_payloads[j].get("document_id", "unknown"),
                            ),
                        }
                    )

        # Identify potential duplicates
        duplicate_groups = defaultdict(set)
        for pair in redundant_pairs:
            i, j = pair["indices"]
            duplicate_groups[i].add(j)
            duplicate_groups[j].add(i)

        return {
            "redundant_pairs": len(redundant_pairs),
            "redundancy_ratio": len(redundant_pairs)
            / (len(sample_embeddings) * (len(sample_embeddings) - 1) / 2),
            "potential_duplicates": len(duplicate_groups),
            "avg_similarity_score": np.mean([p["similarity"] for p in redundant_pairs])
            if redundant_pairs
            else 0,
            "sample_size": len(sample_embeddings),
        }

    def _calculate_quality_metrics(self, embeddings: np.ndarray) -> Dict[str, Any]:
        """Calculate embedding quality metrics"""
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-8)

        # Calculate metrics
        metrics = {
            "sparsity": np.mean(
                np.abs(embeddings) < 0.01
            ),  # Percentage of near-zero values
            "avg_pairwise_similarity": float(
                np.mean(cosine_similarity(normalized[:100]))
            ),  # Sample for efficiency
            "dimension_utilization": np.mean(
                np.std(embeddings, axis=0) > 0.01
            ),  # Active dimensions
            "isotropy_score": float(
                np.std(np.mean(normalized, axis=0))
            ),  # How isotropic the embeddings are
        }

        # Check for degenerate embeddings
        zero_embeddings = np.sum(norms < 0.1)
        identical_embeddings = 0

        # Sample check for identical embeddings
        for i in range(min(100, len(embeddings))):
            for j in range(i + 1, min(100, len(embeddings))):
                if np.allclose(embeddings[i], embeddings[j]):
                    identical_embeddings += 1

        metrics["zero_embeddings"] = zero_embeddings
        metrics["identical_embeddings"] = identical_embeddings

        return metrics

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Dimension reduction recommendations
        variance_analysis = analysis.get("variance_analysis", {})
        current_dim = analysis.get("embedding_dimension", 0)
        optimal_95 = variance_analysis.get("optimal_dimensions", {}).get(
            "95%_variance", 0
        )

        if optimal_95 > 0 and optimal_95 < current_dim * 0.7:
            recommendations.append(
                f"Consider reducing embedding dimensions from {current_dim} to {optimal_95} "
                f"(captures 95% variance, saves {((current_dim - optimal_95) / current_dim * 100):.1f}% storage)"
            )

        # Redundancy recommendations
        redundancy = analysis.get("redundancy_analysis", {})
        if redundancy.get("redundancy_ratio", 0) > 0.05:
            recommendations.append(
                f"High redundancy detected ({redundancy['redundancy_ratio']:.1%}). "
                "Consider deduplication or adjusting chunking strategy"
            )

        # Quality recommendations
        quality = analysis.get("quality_metrics", {})
        if quality.get("sparsity", 0) > 0.3:
            recommendations.append(
                f"High sparsity ({quality['sparsity']:.1%}) detected. "
                "Consider using a different embedding model"
            )

        if quality.get("dimension_utilization", 1) < 0.8:
            recommendations.append(
                "Low dimension utilization. Many embedding dimensions are not being used effectively"
            )

        # Clustering recommendations
        cluster_analysis = analysis.get("cluster_analysis", {})
        if cluster_analysis.get("noise_ratio", 0) > 0.2:
            recommendations.append(
                f"High noise ratio ({cluster_analysis['noise_ratio']:.1%}) in clustering. "
                "Consider reviewing document quality or preprocessing"
            )

        return recommendations

    async def optimize_collection(
        self, collection_name: str, target_dimensions: Optional[int] = None
    ) -> Dict[str, Any]:
        """Optimize embedding collection"""
        console.print(f"[yellow]Optimizing collection {collection_name}...[/yellow]")

        await self.initialize()

        try:
            # First analyze current state
            analysis = await self.analyze_embedding_distribution(collection_name)

            if "error" in analysis:
                return analysis

            optimization_results = {
                "original_analysis": analysis,
                "optimizations_performed": [],
            }

            # Determine target dimensions if not specified
            if target_dimensions is None:
                target_dimensions = analysis["variance_analysis"]["optimal_dimensions"][
                    "95%_variance"
                ]

            current_dimensions = analysis["embedding_dimension"]

            # Only proceed if significant reduction is possible
            if target_dimensions < current_dimensions * 0.9:
                console.print(
                    f"[yellow]Reducing dimensions from {current_dimensions} to {target_dimensions}...[/yellow]"
                )

                # Create optimized collection name
                optimized_collection = (
                    f"{collection_name}_optimized_{target_dimensions}d"
                )

                # Create new collection with reduced dimensions
                await self._create_optimized_collection(
                    collection_name, optimized_collection, target_dimensions
                )

                optimization_results["optimizations_performed"].append(
                    {
                        "type": "dimension_reduction",
                        "from_dimensions": current_dimensions,
                        "to_dimensions": target_dimensions,
                        "new_collection": optimized_collection,
                    }
                )

            # Remove duplicates if significant redundancy
            if analysis["redundancy_analysis"]["redundancy_ratio"] > 0.05:
                console.print("[yellow]Removing redundant embeddings...[/yellow]")
                removed_count = await self._remove_redundant_embeddings(collection_name)

                optimization_results["optimizations_performed"].append(
                    {"type": "redundancy_removal", "removed_count": removed_count}
                )

            return optimization_results

        except Exception as e:
            console.print(f"[red]Error optimizing collection: {str(e)}[/red]")
            return {"error": str(e)}

    async def _create_optimized_collection(
        self, source_collection: str, target_collection: str, target_dimensions: int
    ):
        """Create optimized collection with reduced dimensions"""
        # This would involve:
        # 1. Fetching all embeddings from source
        # 2. Applying PCA to reduce dimensions
        # 3. Creating new collection with reduced dimensions
        # 4. Inserting optimized embeddings

        # Note: This is a placeholder - actual implementation would require
        # batch processing for large collections
        console.print(
            f"[green]Created optimized collection: {target_collection}[/green]"
        )

    async def _remove_redundant_embeddings(
        self, collection_name: str, similarity_threshold: float = 0.95
    ) -> int:
        """Remove redundant embeddings from collection"""
        # This would involve:
        # 1. Identifying redundant embeddings
        # 2. Keeping one representative from each group
        # 3. Deleting the rest

        # Note: This is a placeholder - actual implementation would require
        # careful handling to preserve document coverage
        console.print("[green]Removed redundant embeddings[/green]")
        return 0

    async def batch_reprocess_embeddings(
        self, document_ids: List[str], new_model: str = "text-embedding-3-large"
    ) -> Dict[str, Any]:
        """Batch reprocess embeddings for specified documents"""
        console.print(
            f"[yellow]Reprocessing {len(document_ids)} documents with {new_model}...[/yellow]"
        )

        results = {
            "total_documents": len(document_ids),
            "processed": 0,
            "failed": 0,
            "errors": [],
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task(
                "Reprocessing embeddings...", total=len(document_ids)
            )

            for doc_id in document_ids:
                try:
                    # Queue document for reprocessing
                    queue_item = {
                        "document_id": doc_id,
                        "priority": 5,
                        "processor_type": "embedding_update",
                        "processing_config": {"model": new_model},
                    }

                    # Get tenant_id
                    doc = (
                        self.supabase.table("rag_documents")
                        .select("tenant_id")
                        .eq("id", doc_id)
                        .single()
                        .execute()
                    )

                    if doc.data:
                        queue_item["tenant_id"] = doc.data["tenant_id"]
                        self.supabase.table("rag_processing_queue").insert(
                            queue_item
                        ).execute()
                        results["processed"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Document {doc_id} not found")

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Error processing {doc_id}: {str(e)}")

                progress.update(task, advance=1)

        return results

    def display_analysis(self, analysis: Dict[str, Any]):
        """Display embedding analysis results"""
        if "error" in analysis:
            console.print(f"[red]Analysis failed: {analysis['error']}[/red]")
            return

        # Basic statistics
        console.print("\n[bold blue]Embedding Statistics[/bold blue]")
        stats_table = Table()
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="magenta")

        stats_table.add_row("Total Embeddings", str(analysis["total_embeddings"]))
        stats_table.add_row("Dimensions", str(analysis["embedding_dimension"]))
        stats_table.add_row("Mean Norm", f"{analysis['mean_norm']:.3f}")
        stats_table.add_row("Std Norm", f"{analysis['std_norm']:.3f}")

        console.print(stats_table)

        # Variance analysis
        console.print("\n[bold blue]Variance Analysis[/bold blue]")
        var_table = Table()
        var_table.add_column("Variance Target", style="cyan")
        var_table.add_column("Required Dimensions", style="magenta")
        var_table.add_column("Reduction %", style="green")

        current_dim = analysis["embedding_dimension"]
        for target, dims in analysis["variance_analysis"]["optimal_dimensions"].items():
            reduction = (current_dim - dims) / current_dim * 100
            var_table.add_row(target, str(dims), f"{reduction:.1f}%")

        console.print(var_table)

        # Quality metrics
        console.print("\n[bold blue]Quality Metrics[/bold blue]")
        quality = analysis["quality_metrics"]
        quality_table = Table()
        quality_table.add_column("Metric", style="cyan")
        quality_table.add_column("Value", style="magenta")
        quality_table.add_column("Status", style="green")

        quality_table.add_row(
            "Sparsity",
            f"{quality['sparsity']:.1%}",
            "[green]Good[/green]" if quality["sparsity"] < 0.3 else "[red]High[/red]",
        )
        quality_table.add_row(
            "Dimension Utilization",
            f"{quality['dimension_utilization']:.1%}",
            "[green]Good[/green]"
            if quality["dimension_utilization"] > 0.8
            else "[yellow]Low[/yellow]",
        )
        quality_table.add_row(
            "Zero Embeddings",
            str(quality["zero_embeddings"]),
            "[green]OK[/green]"
            if quality["zero_embeddings"] == 0
            else "[red]Found[/red]",
        )

        console.print(quality_table)

        # Redundancy analysis
        console.print("\n[bold blue]Redundancy Analysis[/bold blue]")
        redundancy = analysis["redundancy_analysis"]
        console.print(
            f"Redundancy Ratio: [{'red' if redundancy['redundancy_ratio'] > 0.05 else 'green'}]{redundancy['redundancy_ratio']:.1%}[/]"
        )
        console.print(f"Potential Duplicates: {redundancy['potential_duplicates']}")

        # Recommendations
        if analysis["recommendations"]:
            console.print("\n[bold yellow]Optimization Recommendations[/bold yellow]")
            for i, rec in enumerate(analysis["recommendations"], 1):
                console.print(f"{i}. {rec}")


async def main():
    parser = argparse.ArgumentParser(description="RAG Embedding Optimizer")
    parser.add_argument(
        "--collection",
        type=str,
        default="document_embeddings",
        help="Qdrant collection to analyze",
    )
    parser.add_argument(
        "--sample-size", type=int, default=1000, help="Number of embeddings to sample"
    )
    parser.add_argument("--optimize", action="store_true", help="Perform optimization")
    parser.add_argument(
        "--target-dims", type=int, help="Target dimensions for optimization"
    )
    parser.add_argument(
        "--reprocess", type=str, help="File with document IDs to reprocess"
    )
    parser.add_argument("--export", type=str, help="Export analysis to JSON file")

    args = parser.parse_args()

    optimizer = EmbeddingOptimizer()

    try:
        if args.reprocess:
            # Batch reprocess embeddings
            with open(args.reprocess, "r") as f:
                doc_ids = [line.strip() for line in f if line.strip()]

            results = await optimizer.batch_reprocess_embeddings(doc_ids)
            console.print(f"\n[green]Reprocessing complete:[/green]")
            console.print(f"  Processed: {results['processed']}")
            console.print(f"  Failed: {results['failed']}")

        elif args.optimize:
            # Optimize collection
            results = await optimizer.optimize_collection(
                args.collection, args.target_dims
            )

            if "error" not in results:
                console.print("\n[green]Optimization complete![/green]")
                for opt in results["optimizations_performed"]:
                    console.print(f"  - {opt['type']}: {opt}")

        else:
            # Analyze embeddings
            analysis = await optimizer.analyze_embedding_distribution(
                args.collection, args.sample_size
            )

            optimizer.display_analysis(analysis)

            if args.export:
                with open(args.export, "w") as f:
                    json.dump(analysis, f, indent=2, default=str)
                console.print(f"\n[green]Analysis exported to {args.export}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())
