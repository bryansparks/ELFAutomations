#!/usr/bin/env python3
"""
Initialize database for Context-as-a-Service.

This script sets up the necessary tables and initial data for the
Context-as-a-Service system.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import asyncpg
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


class DatabaseInitializer:
    """Initialize Context-as-a-Service database."""

    def __init__(self):
        self.database_url = os.getenv("SUPABASE_URL", "").replace(
            "https://", "postgresql://"
        )
        if not self.database_url:
            raise ValueError("SUPABASE_URL not set in environment")

        # Extract database connection info
        self._parse_database_url()

    def _parse_database_url(self):
        """Parse database URL to extract connection parameters."""
        # This is a simplified parser - in production use urllib.parse
        import re

        pattern = r"postgresql://([^:]+):([^@]+)@([^/]+)/(.+)"
        match = re.match(pattern, self.database_url)
        if match:
            self.db_user, self.db_pass, self.db_host, self.db_name = match.groups()
        else:
            raise ValueError(f"Invalid database URL format: {self.database_url}")

    async def initialize(self):
        """Run the initialization process."""
        console.print(
            Panel(
                "[bold cyan]Context-as-a-Service Database Initialization[/bold cyan]\n\n"
                "This will set up the necessary database tables and initial data.",
                title="🚀 Setup",
            )
        )

        # Connect to database
        conn = await self._connect()
        if not conn:
            return False

        try:
            # Run initialization steps
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Create schemas
                task1 = progress.add_task("Creating database schemas...", total=3)
                await self._create_schemas(conn)
                progress.update(task1, advance=1)

                # Create RAG tables
                progress.update(task1, description="Creating RAG system tables...")
                await self._create_rag_tables(conn)
                progress.update(task1, advance=1)

                # Create MCP registry
                progress.update(task1, description="Creating MCP registry...")
                await self._create_mcp_registry(conn)
                progress.update(task1, advance=1)

                # Create initial data
                task2 = progress.add_task("Setting up initial data...", total=2)
                await self._create_default_collections(conn)
                progress.update(task2, advance=1)

                await self._create_api_keys(conn)
                progress.update(task2, advance=1)

            console.print("\n✅ [green]Database initialization complete![/green]")
            return True

        except Exception as e:
            console.print(f"\n❌ [red]Error during initialization: {str(e)}[/red]")
            return False
        finally:
            await conn.close()

    async def _connect(self) -> Optional[asyncpg.Connection]:
        """Connect to the database."""
        try:
            conn = await asyncpg.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_pass,
            )
            console.print("✅ Connected to database")
            return conn
        except Exception as e:
            console.print(f"❌ [red]Failed to connect to database: {str(e)}[/red]")
            return None

    async def _create_schemas(self, conn: asyncpg.Connection):
        """Create database schemas."""
        schemas = ["rag", "mcp", "auth"]

        for schema in schemas:
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    async def _create_rag_tables(self, conn: asyncpg.Connection):
        """Create RAG system tables."""
        # Read schema files
        schema_dir = Path("database/schemas")

        sql_files = ["01_rag_system_tables.sql", "02_rag_extraction_tables.sql"]

        for sql_file in sql_files:
            file_path = schema_dir / sql_file
            if file_path.exists():
                sql_content = file_path.read_text()
                await conn.execute(sql_content)
                logger.info(f"Executed {sql_file}")
            else:
                logger.warning(f"Schema file not found: {sql_file}")

    async def _create_mcp_registry(self, conn: asyncpg.Connection):
        """Create MCP registry tables."""
        schema_file = Path("database/schemas/03_mcp_registry.sql")

        if schema_file.exists():
            sql_content = schema_file.read_text()
            await conn.execute(sql_content)
            logger.info("Created MCP registry")

    async def _create_default_collections(self, conn: asyncpg.Connection):
        """Create default Qdrant collections metadata."""
        collections = [
            {
                "name": "default",
                "description": "Default document collection",
                "dimension": 1536,
                "distance": "cosine",
            },
            {
                "name": "design_system_docs",
                "description": "UI/UX design system documentation",
                "dimension": 1536,
                "distance": "cosine",
            },
            {
                "name": "architecture_decisions",
                "description": "Architecture decisions and patterns",
                "dimension": 1536,
                "distance": "cosine",
            },
            {
                "name": "business_processes",
                "description": "Business process documentation",
                "dimension": 1536,
                "distance": "cosine",
            },
        ]

        # Store collection metadata in database
        for collection in collections:
            await conn.execute(
                """
                INSERT INTO rag.collections (name, description, config)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO NOTHING
            """,
                collection["name"],
                collection["description"],
                {
                    "dimension": collection["dimension"],
                    "distance": collection["distance"],
                },
            )

    async def _create_api_keys(self, conn: asyncpg.Connection):
        """Create initial API keys."""
        import hashlib
        import secrets

        # Generate a default API key
        api_key = f"caas_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Store hashed key
        await conn.execute(
            """
            INSERT INTO auth.api_keys (name, key_hash, permissions)
            VALUES ($1, $2, $3)
        """,
            "Default API Key",
            api_key_hash,
            ["read", "write", "admin"],
        )

        # Save the actual key to a file (for initial setup only)
        with open(".api_key", "w") as f:
            f.write(api_key)

        console.print(f"\n📝 Default API key saved to: [cyan].api_key[/cyan]")
        console.print("   [yellow]Keep this key secure![/yellow]")


async def main():
    """Main entry point."""
    initializer = DatabaseInitializer()
    success = await initializer.initialize()

    if success:
        console.print("\n🎉 [bold green]Setup complete![/bold green]")
        console.print("\nNext steps:")
        console.print("1. Copy the API key from [cyan].api_key[/cyan]")
        console.print("2. Add it to your [cyan].env[/cyan] file as CONTEXT_API_KEY")
        console.print("3. Run [cyan]docker-compose up[/cyan] to start services")
        console.print(
            "4. Register MCP servers with [cyan]python scripts/register_mcps.py[/cyan]"
        )
    else:
        console.print("\n❌ [red]Setup failed. Please check the errors above.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
