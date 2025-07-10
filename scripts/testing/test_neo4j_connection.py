#!/usr/bin/env python3
"""
Test Neo4j Connection and Basic Operations

This script verifies Neo4j is properly deployed and accessible.
"""

import sys
from pathlib import Path

import neo4j
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_neo4j_connection(
    uri: str = "bolt://localhost:30687",
    username: str = "neo4j",
    password: str = "elfautomations2025",
):
    """Test Neo4j connection and perform basic operations"""

    console.print("\n[bold cyan]Neo4j Connection Test[/bold cyan]\n")

    # Connection details table
    table = Table(title="Connection Details")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_row("URI", uri)
    table.add_row("Username", username)
    table.add_row("Password", "*" * len(password))
    console.print(table)

    try:
        # Create driver
        console.print("\n[yellow]Creating driver...[/yellow]")
        driver = neo4j.GraphDatabase.driver(uri, auth=(username, password))

        # Verify connectivity
        console.print("[yellow]Verifying connectivity...[/yellow]")
        driver.verify_connectivity()
        console.print("[green]✓ Connected successfully![/green]")

        # Run basic operations
        with driver.session() as session:
            # 1. Clear test data
            console.print("\n[yellow]Clearing test data...[/yellow]")
            session.run("MATCH (n:TestNode) DETACH DELETE n")

            # 2. Create test nodes with multi-tenant labels
            console.print("[yellow]Creating multi-tenant test nodes...[/yellow]")

            # Acme Corp invoice
            result = session.run(
                """
                CREATE (d:Document:Tenant_acme_corp:Type_invoice:Context_2024_q1 {
                    id: 'test_inv_001',
                    title: 'Test Invoice',
                    amount: 5000,
                    vendor: 'TestVendor',
                    created_at: datetime()
                })
                RETURN d
            """
            )
            acme_node = result.single()
            console.print(f"[green]✓ Created Acme invoice node[/green]")

            # Globex Inc invoice (different tenant)
            result = session.run(
                """
                CREATE (d:Document:Tenant_globex_inc:Type_invoice:Context_2024_q1 {
                    id: 'test_inv_002',
                    title: 'Test Invoice 2',
                    amount: 7500,
                    vendor: 'AnotherVendor',
                    created_at: datetime()
                })
                RETURN d
            """
            )
            globex_node = result.single()
            console.print(f"[green]✓ Created Globex invoice node[/green]")

            # 3. Test tenant isolation
            console.print("\n[yellow]Testing tenant isolation...[/yellow]")

            # Query for Acme documents only
            result = session.run(
                """
                MATCH (d:Tenant_acme_corp)
                RETURN count(d) as count
            """
            )
            acme_count = result.single()["count"]
            console.print(f"[green]✓ Acme documents: {acme_count}[/green]")

            # Query for Globex documents only
            result = session.run(
                """
                MATCH (d:Tenant_globex_inc)
                RETURN count(d) as count
            """
            )
            globex_count = result.single()["count"]
            console.print(f"[green]✓ Globex documents: {globex_count}[/green]")

            # 4. Create indexes for multi-tenant queries
            console.print("\n[yellow]Creating multi-tenant indexes...[/yellow]")

            # Create constraint for document IDs
            try:
                session.run(
                    """
                    CREATE CONSTRAINT doc_id IF NOT EXISTS
                    FOR (d:Document) REQUIRE d.id IS UNIQUE
                """
                )
                console.print("[green]✓ Created document ID constraint[/green]")
            except Exception as e:
                console.print(f"[yellow]Constraint might already exist: {e}[/yellow]")

            # Create index for tenant queries
            try:
                session.run(
                    """
                    CREATE INDEX tenant_acme IF NOT EXISTS
                    FOR (n:Tenant_acme_corp) ON (n.created_at)
                """
                )
                console.print("[green]✓ Created Acme tenant index[/green]")
            except Exception as e:
                console.print(f"[yellow]Index might already exist: {e}[/yellow]")

            # 5. Test graph traversal
            console.print("\n[yellow]Testing graph capabilities...[/yellow]")

            # Create relationship
            session.run(
                """
                MATCH (d1:Document {id: 'test_inv_001'})
                MATCH (d2:Document {id: 'test_inv_002'})
                CREATE (d1)-[:SIMILAR_TO {score: 0.85}]->(d2)
            """
            )
            console.print("[green]✓ Created relationship between documents[/green]")

            # Query relationships
            result = session.run(
                """
                MATCH (d:Tenant_acme_corp)-[r]->()
                RETURN count(r) as rel_count
            """
            )
            rel_count = result.single()["rel_count"]
            console.print(f"[green]✓ Acme relationships: {rel_count}[/green]")

            # 6. Show database info
            console.print("\n[yellow]Database information...[/yellow]")
            result = session.run("CALL dbms.components()")
            components = result.single()

            info_table = Table(title="Neo4j Info")
            info_table.add_column("Component", style="cyan")
            info_table.add_column("Version", style="yellow")
            info_table.add_row("Neo4j", components["versions"][0])
            info_table.add_row("Edition", components["edition"])
            console.print(info_table)

            # 7. Cleanup
            console.print("\n[yellow]Cleaning up test data...[/yellow]")
            session.run(
                """
                MATCH (n)
                WHERE n.id STARTS WITH 'test_'
                DETACH DELETE n
            """
            )
            console.print("[green]✓ Cleaned up test nodes[/green]")

        driver.close()

        # Success summary
        console.print(
            Panel.fit(
                "[bold green]✅ All Neo4j tests passed successfully![/bold green]\n\n"
                + "Neo4j is ready for multi-tenant graph storage.",
                title="Test Summary",
                border_style="green",
            )
        )

        # Next steps
        console.print("\n[bold yellow]Next Steps:[/bold yellow]")
        console.print(
            "1. Apply the K8s manifests: kubectl apply -k k8s/infrastructure/neo4j/"
        )
        console.print("2. Access Neo4j Browser at: http://<node-ip>:30474")
        console.print("3. Create the GraphDB MCP using: python tools/mcp_factory.py")
        console.print("4. Update RAG team to use Neo4j for graph storage")

        return True

    except neo4j.exceptions.ServiceUnavailable as e:
        console.print(f"\n[red]❌ Could not connect to Neo4j: {e}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print(
            "1. Check if Neo4j pod is running: kubectl get pods -n elf-infrastructure"
        )
        console.print("2. Check service status: kubectl get svc -n elf-infrastructure")
        console.print(
            "3. Check logs: kubectl logs -n elf-infrastructure deployment/neo4j"
        )
        console.print("4. Verify NodePort is accessible from your machine")
        return False

    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Neo4j connection")
    parser.add_argument(
        "--uri",
        default="bolt://localhost:30687",
        help="Neo4j Bolt URI (default: bolt://localhost:30687)",
    )
    parser.add_argument(
        "--username", default="neo4j", help="Neo4j username (default: neo4j)"
    )
    parser.add_argument(
        "--password",
        default="elfautomations2025",
        help="Neo4j password (default: elfautomations2025)",
    )

    args = parser.parse_args()

    # Run test
    success = test_neo4j_connection(args.uri, args.username, args.password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
