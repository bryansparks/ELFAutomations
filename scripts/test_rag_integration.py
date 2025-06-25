#!/usr/bin/env python3
"""
RAG Integration Test Suite
End-to-end tests for the RAG processing pipeline.

Tests:
- Document ingestion flow
- Processing pipeline stages
- Multi-tenant isolation
- Search and retrieval
- Performance benchmarks
"""

import argparse
import asyncio
import json
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from elf_automations.shared.config import settings
from elf_automations.shared.mcp import MCPClient
from elf_automations.shared.rag import RAGHealthMonitor
from elf_automations.shared.utils import get_supabase_client

console = Console()


class RAGIntegrationTester:
    """Integration test suite for RAG system"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.mcp_client = MCPClient()
        self.health_monitor = RAGHealthMonitor()
        self.test_results = []

    async def setup_test_data(self) -> Dict[str, Any]:
        """Create test documents and tenants"""
        console.print("[yellow]Setting up test data...[/yellow]")

        # Create test tenant
        test_tenant = {
            "name": f"test_tenant_{uuid.uuid4().hex[:8]}",
            "display_name": "Integration Test Tenant",
            "settings": {"test": True},
        }

        try:
            result = self.supabase.table("rag_tenants").insert(test_tenant).execute()
            tenant_id = result.data[0]["id"]
            console.print(f"[green]Created test tenant: {tenant_id}[/green]")

            # Create test documents
            test_docs = []

            # Contract document
            contract_content = """
            CONTRACT AGREEMENT

            This agreement is entered into between ACME Corporation ("Buyer")
            and TechSupply Inc. ("Seller") on January 15, 2024.

            Terms:
            1. The Seller agrees to provide 100 units of Model X200 processors
            2. Total purchase price: $50,000 USD
            3. Delivery date: February 28, 2024
            4. Payment terms: Net 30 days

            This contract is governed by the laws of California, USA.

            Signed,
            John Smith, CEO ACME Corporation
            Jane Doe, President TechSupply Inc.
            """

            # Technical document
            tech_content = """
            # System Architecture Guide

            ## Overview
            The RAG processing system consists of multiple components:

            ### Document Processor
            - Handles PDF, TXT, and DOCX formats
            - Extracts text and metadata
            - Performs OCR when needed

            ### Entity Extractor
            - Uses NLP to identify entities
            - Supports custom entity types
            - Normalizes extracted data

            ### Vector Storage
            - Qdrant for semantic search
            - 3072-dimensional embeddings
            - Supports multi-tenant isolation

            ### Graph Database
            - Neo4j for relationship queries
            - Stores entity relationships
            - Enables complex traversals
            """

            # Create temp files
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(contract_content)
                contract_path = f.name

            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(tech_content)
                tech_path = f.name

            # Insert documents
            docs = [
                {
                    "tenant_id": tenant_id,
                    "source_type": "upload",
                    "source_id": str(uuid.uuid4()),
                    "source_path": contract_path,
                    "filename": "test_contract.txt",
                    "mime_type": "text/plain",
                    "size_bytes": len(contract_content.encode()),
                    "status": "pending",
                },
                {
                    "tenant_id": tenant_id,
                    "source_type": "upload",
                    "source_id": str(uuid.uuid4()),
                    "source_path": tech_path,
                    "filename": "test_tech_doc.md",
                    "mime_type": "text/markdown",
                    "size_bytes": len(tech_content.encode()),
                    "status": "pending",
                },
            ]

            result = self.supabase.table("rag_documents").insert(docs).execute()
            test_docs = result.data

            # Queue documents for processing
            queue_items = []
            for doc in test_docs:
                queue_items.append(
                    {
                        "tenant_id": tenant_id,
                        "document_id": doc["id"],
                        "priority": 10,  # High priority for tests
                        "processor_type": "auto",
                    }
                )

            self.supabase.table("rag_processing_queue").insert(queue_items).execute()

            console.print(f"[green]Created {len(test_docs)} test documents[/green]")

            return {
                "tenant_id": tenant_id,
                "documents": test_docs,
                "temp_files": [contract_path, tech_path],
            }

        except Exception as e:
            console.print(f"[red]Setup failed: {str(e)}[/red]")
            raise

    async def test_document_ingestion(
        self, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test document ingestion flow"""
        test_name = "Document Ingestion"
        console.print(f"\n[blue]Testing: {test_name}[/blue]")

        start_time = time.time()
        success = True
        errors = []

        try:
            # Check documents were created
            docs = (
                self.supabase.table("rag_documents")
                .select("*")
                .eq("tenant_id", test_data["tenant_id"])
                .execute()
            )

            if len(docs.data) != 2:
                errors.append(f"Expected 2 documents, found {len(docs.data)}")
                success = False

            # Check queue entries
            queue = (
                self.supabase.table("rag_processing_queue")
                .select("*")
                .eq("tenant_id", test_data["tenant_id"])
                .execute()
            )

            if len(queue.data) != 2:
                errors.append(f"Expected 2 queue entries, found {len(queue.data)}")
                success = False

            # Verify document metadata
            for doc in docs.data:
                if not doc.get("source_path"):
                    errors.append(f"Document {doc['id']} missing source_path")
                    success = False
                if doc.get("status") != "pending":
                    errors.append(
                        f"Document {doc['id']} has unexpected status: {doc.get('status')}"
                    )
                    success = False

        except Exception as e:
            errors.append(str(e))
            success = False

        duration = time.time() - start_time

        return {
            "test": test_name,
            "success": success,
            "duration": duration,
            "errors": errors,
        }

    async def test_processing_pipeline(
        self, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test document processing stages"""
        test_name = "Processing Pipeline"
        console.print(f"\n[blue]Testing: {test_name}[/blue]")

        start_time = time.time()
        success = True
        errors = []
        stages_completed = []

        try:
            # Simulate processing stages
            for doc in test_data["documents"]:
                doc_id = doc["id"]

                # Update to processing
                self.supabase.table("rag_documents").update(
                    {
                        "status": "processing",
                        "processing_started_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", doc_id).execute()

                # Simulate classification
                classification = {
                    "document_id": doc_id,
                    "detected_type": "contract"
                    if "contract" in doc["filename"]
                    else "technical_doc",
                    "confidence": 0.95,
                    "classification_method": "test",
                }

                self.supabase.table("rag_document_classifications").insert(
                    classification
                ).execute()
                stages_completed.append("classification")

                # Simulate entity extraction
                entities = []
                if "contract" in doc["filename"]:
                    entities = [
                        {
                            "tenant_id": test_data["tenant_id"],
                            "document_id": doc_id,
                            "entity_type": "organization",
                            "entity_value": "ACME Corporation",
                            "normalized_value": "acme_corporation",
                            "confidence": 0.9,
                        },
                        {
                            "tenant_id": test_data["tenant_id"],
                            "document_id": doc_id,
                            "entity_type": "monetary_amount",
                            "entity_value": "$50,000 USD",
                            "normalized_value": "50000.00",
                            "properties": {"currency": "USD"},
                            "confidence": 0.95,
                        },
                    ]

                if entities:
                    self.supabase.table("rag_extracted_entities").insert(
                        entities
                    ).execute()
                    stages_completed.append("extraction")

                # Simulate chunking
                chunks = []
                for i in range(3):  # Create 3 chunks per document
                    chunks.append(
                        {
                            "document_id": doc_id,
                            "tenant_id": test_data["tenant_id"],
                            "chunk_index": i,
                            "content": f"Test chunk {i} content for {doc['filename']}",
                            "tokens": 50 + (i * 10),
                            "metadata": {"type": "test"},
                        }
                    )

                self.supabase.table("rag_document_chunks").insert(chunks).execute()
                stages_completed.append("chunking")

                # Update document as completed
                self.supabase.table("rag_documents").update(
                    {
                        "status": "completed",
                        "processing_completed_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", doc_id).execute()

                # Update queue
                self.supabase.table("rag_processing_queue").update(
                    {
                        "status": "completed",
                        "completed_at": datetime.utcnow().isoformat(),
                    }
                ).eq("document_id", doc_id).execute()

            # Verify all stages completed
            expected_stages = ["classification", "extraction", "chunking"]
            unique_stages = list(set(stages_completed))

            if not all(stage in unique_stages for stage in expected_stages):
                missing = [s for s in expected_stages if s not in unique_stages]
                errors.append(f"Missing stages: {missing}")
                success = False

        except Exception as e:
            errors.append(str(e))
            success = False

        duration = time.time() - start_time

        return {
            "test": test_name,
            "success": success,
            "duration": duration,
            "errors": errors,
            "metadata": {"stages_completed": unique_stages},
        }

    async def test_multi_tenant_isolation(
        self, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test multi-tenant data isolation"""
        test_name = "Multi-Tenant Isolation"
        console.print(f"\n[blue]Testing: {test_name}[/blue]")

        start_time = time.time()
        success = True
        errors = []

        try:
            # Create second tenant
            second_tenant = {
                "name": f"test_tenant2_{uuid.uuid4().hex[:8]}",
                "display_name": "Second Test Tenant",
                "settings": {"test": True},
            }

            result = self.supabase.table("rag_tenants").insert(second_tenant).execute()
            tenant2_id = result.data[0]["id"]

            # Create document for second tenant
            doc2 = {
                "tenant_id": tenant2_id,
                "source_type": "upload",
                "source_id": str(uuid.uuid4()),
                "source_path": "/tmp/test2.txt",
                "filename": "tenant2_doc.txt",
                "mime_type": "text/plain",
                "size_bytes": 100,
                "status": "completed",
            }

            self.supabase.table("rag_documents").insert(doc2).execute()

            # Test isolation - try to access tenant1's documents with tenant2 context
            # This would normally be enforced by RLS, but we'll simulate the check

            # Get all documents (without tenant filter)
            all_docs = (
                self.supabase.table("rag_documents").select("tenant_id").execute()
            )

            # Check that both tenants have documents
            tenant_ids = set(doc["tenant_id"] for doc in all_docs.data)
            if test_data["tenant_id"] not in tenant_ids:
                errors.append("Test tenant 1 documents not found")
                success = False
            if tenant2_id not in tenant_ids:
                errors.append("Test tenant 2 documents not found")
                success = False

            # Verify tenant-specific queries work correctly
            tenant1_docs = (
                self.supabase.table("rag_documents")
                .select("*")
                .eq("tenant_id", test_data["tenant_id"])
                .execute()
            )

            tenant2_docs = (
                self.supabase.table("rag_documents")
                .select("*")
                .eq("tenant_id", tenant2_id)
                .execute()
            )

            # Check document counts
            if len(tenant1_docs.data) != 2:
                errors.append(
                    f"Tenant 1 should have 2 documents, found {len(tenant1_docs.data)}"
                )
                success = False

            if len(tenant2_docs.data) != 1:
                errors.append(
                    f"Tenant 2 should have 1 document, found {len(tenant2_docs.data)}"
                )
                success = False

            # Cleanup tenant 2
            self.supabase.table("rag_tenants").delete().eq("id", tenant2_id).execute()

        except Exception as e:
            errors.append(str(e))
            success = False

        duration = time.time() - start_time

        return {
            "test": test_name,
            "success": success,
            "duration": duration,
            "errors": errors,
        }

    async def test_search_retrieval(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test search and retrieval functionality"""
        test_name = "Search & Retrieval"
        console.print(f"\n[blue]Testing: {test_name}[/blue]")

        start_time = time.time()
        success = True
        errors = []
        search_results = []

        try:
            # Test 1: Search by content
            chunks = (
                self.supabase.table("rag_document_chunks")
                .select("*")
                .eq("tenant_id", test_data["tenant_id"])
                .ilike("content", "%chunk%")
                .execute()
            )

            if not chunks.data:
                errors.append("No chunks found with content search")
                success = False
            else:
                search_results.append(f"Content search: {len(chunks.data)} chunks")

            # Test 2: Entity search
            entities = (
                self.supabase.table("rag_extracted_entities")
                .select("*")
                .eq("tenant_id", test_data["tenant_id"])
                .eq("entity_type", "organization")
                .execute()
            )

            if entities.data:
                search_results.append(
                    f"Entity search: {len(entities.data)} organizations"
                )

            # Test 3: Document metadata search
            docs = (
                self.supabase.table("rag_documents")
                .select("*")
                .eq("tenant_id", test_data["tenant_id"])
                .eq("status", "completed")
                .execute()
            )

            if len(docs.data) != 2:
                errors.append(f"Expected 2 completed documents, found {len(docs.data)}")
                success = False
            else:
                search_results.append(f"Status search: {len(docs.data)} completed")

            # Test 4: Join query - documents with their chunks
            docs_with_chunks = (
                self.supabase.table("rag_documents")
                .select("*, rag_document_chunks(content, chunk_index)")
                .eq("tenant_id", test_data["tenant_id"])
                .execute()
            )

            total_chunks = sum(
                len(doc.get("rag_document_chunks", [])) for doc in docs_with_chunks.data
            )
            search_results.append(
                f"Join query: {len(docs_with_chunks.data)} docs with {total_chunks} chunks"
            )

            # Simulate a search query record
            search_query = {
                "tenant_id": test_data["tenant_id"],
                "query_text": "test search for contracts",
                "query_type": "hybrid",
                "result_count": len(chunks.data),
                "execution_time_ms": 50,
            }

            self.supabase.table("rag_search_queries").insert(search_query).execute()

        except Exception as e:
            errors.append(str(e))
            success = False

        duration = time.time() - start_time

        return {
            "test": test_name,
            "success": success,
            "duration": duration,
            "errors": errors,
            "metadata": {"search_results": search_results},
        }

    async def test_performance_benchmarks(
        self, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test performance benchmarks"""
        test_name = "Performance Benchmarks"
        console.print(f"\n[blue]Testing: {test_name}[/blue]")

        start_time = time.time()
        success = True
        errors = []
        benchmarks = {}

        try:
            # Benchmark 1: Document insertion
            insert_start = time.time()
            bulk_docs = []
            for i in range(10):
                bulk_docs.append(
                    {
                        "tenant_id": test_data["tenant_id"],
                        "source_type": "benchmark",
                        "source_id": str(uuid.uuid4()),
                        "source_path": f"/tmp/bench_{i}.txt",
                        "filename": f"benchmark_{i}.txt",
                        "mime_type": "text/plain",
                        "size_bytes": 1000,
                        "status": "pending",
                    }
                )

            self.supabase.table("rag_documents").insert(bulk_docs).execute()
            benchmarks["bulk_insert_10_docs"] = (time.time() - insert_start) * 1000

            # Benchmark 2: Query performance
            query_start = time.time()
            self.supabase.table("rag_documents").select("id, filename, status").eq(
                "tenant_id", test_data["tenant_id"]
            ).limit(100).execute()
            benchmarks["simple_query"] = (time.time() - query_start) * 1000

            # Benchmark 3: Complex join
            join_start = time.time()
            self.supabase.table("rag_documents").select(
                "*, rag_document_chunks(*), rag_extracted_entities(*)"
            ).eq("tenant_id", test_data["tenant_id"]).limit(10).execute()
            benchmarks["complex_join"] = (time.time() - join_start) * 1000

            # Benchmark 4: Aggregation
            agg_start = time.time()
            self.supabase.table("rag_documents").select("status", count="exact").eq(
                "tenant_id", test_data["tenant_id"]
            ).execute()
            benchmarks["aggregation"] = (time.time() - agg_start) * 1000

            # Check if benchmarks are within acceptable ranges
            thresholds = {
                "bulk_insert_10_docs": 500,  # 500ms
                "simple_query": 100,  # 100ms
                "complex_join": 300,  # 300ms
                "aggregation": 150,  # 150ms
            }

            for bench_name, duration in benchmarks.items():
                if duration > thresholds.get(bench_name, float("inf")):
                    errors.append(
                        f"{bench_name} exceeded threshold: {duration:.1f}ms > {thresholds[bench_name]}ms"
                    )
                    success = False

        except Exception as e:
            errors.append(str(e))
            success = False

        duration = time.time() - start_time

        return {
            "test": test_name,
            "success": success,
            "duration": duration,
            "errors": errors,
            "metadata": {"benchmarks": benchmarks},
        }

    async def cleanup_test_data(self, test_data: Dict[str, Any]):
        """Clean up test data"""
        console.print("\n[yellow]Cleaning up test data...[/yellow]")

        try:
            # Delete test tenant (cascades to all related data)
            self.supabase.table("rag_tenants").delete().eq(
                "id", test_data["tenant_id"]
            ).execute()

            # Clean up temp files
            for temp_file in test_data.get("temp_files", []):
                try:
                    Path(temp_file).unlink()
                except:
                    pass

            console.print("[green]Cleanup completed[/green]")

        except Exception as e:
            console.print(f"[red]Cleanup error: {str(e)}[/red]")

    async def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all integration tests"""
        console.print("[bold blue]RAG Integration Test Suite[/bold blue]\n")

        # Check system health first
        console.print("[yellow]Checking system health...[/yellow]")
        await self.health_monitor.initialize()
        health_summary = await self.health_monitor.get_health_summary()

        if health_summary["overall_status"] == "critical":
            console.print("[red]System health is critical. Aborting tests.[/red]")
            return []

        # Setup test data
        test_data = await self.setup_test_data()

        # Run tests
        tests = [
            self.test_document_ingestion,
            self.test_processing_pipeline,
            self.test_multi_tenant_isolation,
            self.test_search_retrieval,
            self.test_performance_benchmarks,
        ]

        results = []

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}")
        ) as progress:
            for test_func in tests:
                task = progress.add_task(f"Running {test_func.__name__}...", total=None)
                result = await test_func(test_data)
                results.append(result)
                progress.remove_task(task)

        # Cleanup
        await self.cleanup_test_data(test_data)

        return results

    def display_results(self, results: List[Dict[str, Any]]):
        """Display test results"""
        console.print("\n[bold blue]Test Results Summary[/bold blue]\n")

        # Summary table
        table = Table(show_header=True)
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Errors", style="red")

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["success"])

        for result in results:
            status = (
                "[green]PASSED[/green]" if result["success"] else "[red]FAILED[/red]"
            )
            duration = f"{result['duration']:.2f}s"
            errors = "\n".join(result["errors"][:2]) if result["errors"] else "-"

            table.add_row(result["test"], status, duration, errors)

        console.print(table)

        # Overall summary
        console.print(f"\n[bold]Total Tests:[/bold] {total_tests}")
        console.print(f"[bold green]Passed:[/bold green] {passed_tests}")
        console.print(f"[bold red]Failed:[/bold red] {total_tests - passed_tests}")
        console.print(f"[bold]Success Rate:[/bold] {passed_tests/total_tests*100:.1f}%")

        # Detailed results for failed tests
        failed_tests = [r for r in results if not r["success"]]
        if failed_tests:
            console.print("\n[bold red]Failed Test Details:[/bold red]")
            for test in failed_tests:
                console.print(f"\n[yellow]{test['test']}:[/yellow]")
                for error in test["errors"]:
                    console.print(f"  - {error}")

        # Performance benchmarks
        for result in results:
            if "benchmarks" in result.get("metadata", {}):
                console.print("\n[bold yellow]Performance Benchmarks:[/bold yellow]")
                bench_table = Table()
                bench_table.add_column("Operation", style="cyan")
                bench_table.add_column("Duration (ms)", style="magenta")

                for op, duration in result["metadata"]["benchmarks"].items():
                    bench_table.add_row(op.replace("_", " ").title(), f"{duration:.1f}")

                console.print(bench_table)
                break


async def main():
    parser = argparse.ArgumentParser(description="RAG Integration Test Suite")
    parser.add_argument("--test", type=str, help="Run specific test")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    parser.add_argument(
        "--skip-cleanup", action="store_true", help="Skip cleanup after tests"
    )

    args = parser.parse_args()

    tester = RAGIntegrationTester()

    try:
        if args.test:
            # Run specific test
            console.print(f"[yellow]Running specific test: {args.test}[/yellow]")
            test_data = await tester.setup_test_data()

            test_map = {
                "ingestion": tester.test_document_ingestion,
                "pipeline": tester.test_processing_pipeline,
                "isolation": tester.test_multi_tenant_isolation,
                "search": tester.test_search_retrieval,
                "performance": tester.test_performance_benchmarks,
            }

            if args.test in test_map:
                result = await test_map[args.test](test_data)
                tester.display_results([result])
            else:
                console.print(f"[red]Unknown test: {args.test}[/red]")
                console.print(f"Available tests: {', '.join(test_map.keys())}")

            if not args.skip_cleanup:
                await tester.cleanup_test_data(test_data)
        else:
            # Run all tests
            results = await tester.run_all_tests()
            tester.display_results(results)

            if args.export:
                with open(args.export, "w") as f:
                    json.dump(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "results": results,
                        },
                        f,
                        indent=2,
                        default=str,
                    )
                console.print(f"\n[green]Results exported to {args.export}[/green]")

    except Exception as e:
        console.print(f"[red]Test suite error: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())
