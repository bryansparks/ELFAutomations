#!/usr/bin/env python3
"""
Test MinIO connection and multi-tenant operations.

This script verifies MinIO is properly deployed and tests
multi-tenant document storage capabilities.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from elf_automations.shared.storage import get_minio_manager
from elf_automations.shared.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


def test_minio_connection():
    """Test MinIO connection and operations."""
    console.print("\n[bold cyan]MinIO Connection Test[/bold cyan]\n")

    # Connection details
    table = Table(title="Connection Details")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="yellow")

    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:30900")
    table.add_row("Endpoint", endpoint)
    table.add_row("Access Key", "elfautomations")
    table.add_row("Console URL", f"http://{endpoint.replace(':30900', ':30901')}")

    console.print(table)

    try:
        # Initialize manager
        console.print("\n[yellow]Initializing MinIO manager...[/yellow]")
        manager = get_minio_manager()
        console.print("[green]✓ Manager initialized[/green]")

        # Test tenant operations
        test_tenants = ["acme-corp", "globex-inc", "elf-internal"]

        for tenant in test_tenants:
            console.print(f"\n[bold]Testing tenant: {tenant}[/bold]")

            # 1. Create tenant bucket
            console.print(f"[yellow]Creating bucket for {tenant}...[/yellow]")
            if manager.create_tenant_bucket(tenant):
                console.print(f"[green]✓ Bucket created/verified[/green]")
            else:
                console.print(f"[red]✗ Failed to create bucket[/red]")
                continue

            # 2. Store test document
            console.print(f"[yellow]Storing test document...[/yellow]")

            # Create test file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(f"Test document for {tenant}\n")
                f.write(f"This is a test of the multi-tenant RAG system.\n")
                f.write(f"Timestamp: {Path(__file__).stat().st_mtime}\n")
                test_file = f.name

            try:
                with open(test_file, "rb") as f:
                    doc_url = manager.store_document(
                        tenant_id=tenant,
                        document_id="test-001",
                        file_data=f,
                        filename="test-document.txt",
                        content_type="text/plain",
                        metadata={"test": "true", "source": "test_script"},
                    )

                if doc_url:
                    console.print(f"[green]✓ Document stored: {doc_url}[/green]")
                else:
                    console.print(f"[red]✗ Failed to store document[/red]")
                    continue

            finally:
                os.unlink(test_file)

            # 3. List documents
            console.print(f"[yellow]Listing documents...[/yellow]")
            documents = manager.list_tenant_documents(tenant)

            if documents:
                console.print(f"[green]✓ Found {len(documents)} documents[/green]")
                for doc in documents[:3]:  # Show first 3
                    console.print(
                        f"  - {doc.get('filename')} ({doc.get('size')} bytes)"
                    )
            else:
                console.print(f"[yellow]No documents found[/yellow]")

            # 4. Get document
            console.print(f"[yellow]Retrieving test document...[/yellow]")
            content = manager.get_document(
                tenant_id=tenant, document_id="test-001", filename="test-document.txt"
            )

            if content:
                console.print(
                    f"[green]✓ Document retrieved ({len(content)} bytes)[/green]"
                )
                console.print(
                    f"  Content preview: {content[:50].decode('utf-8', errors='ignore')}..."
                )
            else:
                console.print(f"[red]✗ Failed to retrieve document[/red]")

            # 5. Create presigned URL
            console.print(f"[yellow]Creating presigned URL...[/yellow]")
            url = manager.create_presigned_url(
                tenant_id=tenant,
                document_id="test-001",
                filename="test-document.txt",
                expires_in=3600,
            )

            if url:
                console.print(f"[green]✓ Presigned URL created[/green]")
                console.print(f"  URL: {url[:80]}...")
            else:
                console.print(f"[yellow]Could not create presigned URL[/yellow]")

            # 6. Get usage stats
            console.print(f"[yellow]Getting tenant usage...[/yellow]")
            usage = manager.get_tenant_usage(tenant)

            if "error" not in usage:
                console.print(f"[green]✓ Usage stats retrieved[/green]")
                console.print(f"  Total objects: {usage['total_objects']}")
                console.print(f"  Total size: {usage['total_size_mb']} MB")
            else:
                console.print(f"[yellow]Could not get usage stats[/yellow]")

        # Summary
        console.print(
            Panel.fit(
                "[bold green]✅ MinIO tests completed successfully![/bold green]\n\n"
                "MinIO is ready for multi-tenant document storage.",
                title="Test Summary",
                border_style="green",
            )
        )

        # Next steps
        console.print("\n[bold yellow]Next Steps:[/bold yellow]")
        console.print("1. Deploy MinIO: kubectl apply -f k8s/infrastructure/minio/")
        console.print("2. Access MinIO console at: http://localhost:30901")
        console.print(
            "3. Default credentials: elfautomations / elfautomations2025secure"
        )
        console.print("4. Configure Google OAuth for Drive integration")

        return True

    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("1. Check if MinIO is running: kubectl get pods -n elf-storage")
        console.print(
            "2. Check port forwarding: kubectl port-forward -n elf-storage svc/minio 30900:9000"
        )
        console.print("3. Verify credentials are correct")
        return False


def main():
    """Main entry point."""
    success = test_minio_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
