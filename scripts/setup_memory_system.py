#!/usr/bin/env python3
"""Setup script for the Memory & Learning System.

This script:
1. Deploys Qdrant to Kubernetes
2. Creates memory tables in Supabase
3. Initializes default collections
4. Verifies the setup
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote_plus

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MemorySystemSetup:
    """Setup the Memory & Learning System infrastructure."""

    def __init__(self, skip_k8s: bool = False, skip_db: bool = False):
        self.skip_k8s = skip_k8s
        self.skip_db = skip_db

    def setup_all(self):
        """Run the complete setup process."""
        logger.info("Starting Memory & Learning System setup...")

        # Step 1: Deploy Qdrant
        if not self.skip_k8s:
            if not self.deploy_qdrant():
                logger.error("Failed to deploy Qdrant")
                return False
        else:
            logger.info("Skipping Qdrant deployment (--skip-k8s flag)")

        # Step 2: Create Supabase schema
        if not self.skip_db:
            if not self.create_supabase_schema():
                logger.error("Failed to create Supabase schema")
                return False
        else:
            logger.info("Skipping Supabase schema creation (--skip-db flag)")

        # Step 3: Verify setup
        if self.verify_setup():
            logger.info("✅ Memory & Learning System setup completed successfully!")
            return True
        else:
            logger.error("❌ Setup verification failed")
            return False

    def deploy_qdrant(self) -> bool:
        """Deploy Qdrant to Kubernetes."""
        logger.info("Deploying Qdrant vector database...")

        qdrant_path = "k8s/data-stores/qdrant"

        try:
            # Check if namespace exists
            logger.info("Checking namespace...")
            result = subprocess.run(
                ["kubectl", "get", "namespace", "elf-automations"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.info("Creating namespace elf-automations...")
                subprocess.run(
                    ["kubectl", "create", "namespace", "elf-automations"], check=True
                )

            # Apply Qdrant manifests
            logger.info("Applying Qdrant Kubernetes manifests...")
            subprocess.run(["kubectl", "apply", "-k", qdrant_path], check=True)

            # Wait for Qdrant to be ready
            logger.info("Waiting for Qdrant to be ready...")
            max_attempts = 30
            for i in range(max_attempts):
                result = subprocess.run(
                    [
                        "kubectl",
                        "get",
                        "pod",
                        "-n",
                        "elf-automations",
                        "-l",
                        "app=qdrant",
                        "-o",
                        "jsonpath={.items[0].status.phase}",
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.stdout.strip() == "Running":
                    logger.info("✓ Qdrant pod is running")

                    # Check if ready
                    result = subprocess.run(
                        [
                            "kubectl",
                            "get",
                            "pod",
                            "-n",
                            "elf-automations",
                            "-l",
                            "app=qdrant",
                            "-o",
                            "jsonpath={.items[0].status.conditions[?(@.type=='Ready')].status}",
                        ],
                        capture_output=True,
                        text=True,
                    )

                    if result.stdout.strip() == "True":
                        logger.info("✓ Qdrant is ready!")
                        break

                logger.info(f"Waiting for Qdrant... ({i+1}/{max_attempts})")
                time.sleep(5)
            else:
                logger.error("Qdrant failed to become ready")
                return False

            # Get service info
            logger.info("\nQdrant service information:")
            subprocess.run(
                ["kubectl", "get", "service", "qdrant", "-n", "elf-automations"],
                check=True,
            )

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to deploy Qdrant: {e}")
            return False

    def create_supabase_schema(self) -> bool:
        """Create memory tables in Supabase."""
        logger.info("Creating Supabase schema for memory system...")

        try:
            # Try to get Supabase database URL
            db_url = os.getenv("SUPABASE_DATABASE_URL")

            if not db_url:
                # Build from components
                supabase_url = os.getenv("SUPABASE_URL", "")
                db_password = os.getenv("SUPABASE_DB_PASSWORD") or os.getenv(
                    "SUPABASE_PASSWORD"
                )

                if not supabase_url:
                    logger.error("SUPABASE_URL environment variable not set")
                    return False

                if not db_password:
                    logger.error("SUPABASE_DB_PASSWORD or SUPABASE_PASSWORD not set")
                    logger.info(
                        "You can find this in your Supabase project settings under 'Database'"
                    )
                    return False

                # Extract the project ref from URL
                if "supabase.co" in supabase_url:
                    project_ref = supabase_url.replace("https://", "").split(
                        ".supabase.co"
                    )[0]
                    db_host = f"db.{project_ref}.supabase.co"
                    # URL encode the password to handle special characters
                    encoded_password = quote_plus(db_password)
                    db_url = f"postgresql://postgres:{encoded_password}@{db_host}:5432/postgres?sslmode=require"
                else:
                    logger.error("Invalid SUPABASE_URL format")
                    return False

            # Connect to database
            logger.info(f"Connecting to Supabase database...")
            conn = psycopg2.connect(db_url)

            with conn.cursor() as cur:
                # Read and execute SQL file
                sql_file = "sql/create_memory_system_tables.sql"
                logger.info(f"Executing {sql_file}...")

                with open(sql_file, "r") as f:
                    sql_content = f.read()

                # Execute the SQL
                cur.execute(sql_content)
                conn.commit()

                # Verify tables were created
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN (
                        'memory_entries',
                        'memory_collections',
                        'learning_patterns',
                        'memory_relationships',
                        'team_knowledge_profiles',
                        'memory_access_logs'
                    )
                    ORDER BY table_name;
                """
                )

                created_tables = [row[0] for row in cur.fetchall()]
                logger.info(f"✓ Created tables: {', '.join(created_tables)}")

                # Create default collection
                logger.info("Creating default memory collection...")
                cur.execute(
                    """
                    INSERT INTO memory_collections (name, description, collection_type)
                    VALUES ('default', 'Default memory collection for all teams', 'general')
                    ON CONFLICT (name) DO NOTHING;
                """
                )
                conn.commit()

            conn.close()
            logger.info("✓ Supabase schema created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create Supabase schema: {e}")
            return False

    def verify_setup(self) -> bool:
        """Verify the memory system is properly set up."""
        logger.info("\nVerifying Memory & Learning System setup...")

        all_good = True

        # Check Qdrant
        if not self.skip_k8s:
            logger.info("Checking Qdrant...")
            result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "pod",
                    "-n",
                    "elf-automations",
                    "-l",
                    "app=qdrant",
                    "-o",
                    "jsonpath={.items[0].status.phase}",
                ],
                capture_output=True,
                text=True,
            )

            if result.stdout.strip() == "Running":
                logger.info("✓ Qdrant is running")
            else:
                logger.error("✗ Qdrant is not running")
                all_good = False

        # Check Supabase tables
        if not self.skip_db:
            logger.info("Checking Supabase tables...")
            try:
                # Use same connection logic as create
                db_url = os.getenv("SUPABASE_DATABASE_URL")

                if not db_url:
                    supabase_url = os.getenv("SUPABASE_URL", "")
                    db_password = os.getenv("SUPABASE_DB_PASSWORD") or os.getenv(
                        "SUPABASE_PASSWORD"
                    )

                    if supabase_url and db_password and "supabase.co" in supabase_url:
                        project_ref = supabase_url.replace("https://", "").split(
                            ".supabase.co"
                        )[0]
                        db_host = f"db.{project_ref}.supabase.co"
                        encoded_password = quote_plus(db_password)
                        db_url = f"postgresql://postgres:{encoded_password}@{db_host}:5432/postgres?sslmode=require"
                    else:
                        logger.error("Missing database credentials")
                        return False

                conn = psycopg2.connect(db_url)

                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name LIKE 'memory_%'
                    """
                    )

                    table_count = cur.fetchone()[0]
                    if table_count >= 6:
                        logger.info(f"✓ Found {table_count} memory tables")
                    else:
                        logger.error(
                            f"✗ Only found {table_count} memory tables (expected 6+)"
                        )
                        all_good = False

                conn.close()

            except Exception as e:
                logger.error(f"✗ Failed to check Supabase: {e}")
                all_good = False

        return all_good

    def print_next_steps(self):
        """Print next steps after setup."""
        print("\n" + "=" * 60)
        print("🎉 Memory & Learning System Setup Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Port-forward to test Qdrant:")
        print("   kubectl port-forward -n elf-automations svc/qdrant 6333:6333")
        print("   Then visit: http://localhost:6333/dashboard")
        print("\n2. Create the Memory & Learning MCP server")
        print("   Location: mcp-servers-ts/src/memory-learning/")
        print("\n3. Build the RAG free-agent team")
        print("   Use: python tools/team_factory.py")
        print("\n4. Test memory storage and retrieval")
        print("   Use: python scripts/test_memory_system.py")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Memory & Learning System for ElfAutomations"
    )
    parser.add_argument(
        "--skip-k8s", action="store_true", help="Skip Kubernetes deployment (Qdrant)"
    )
    parser.add_argument(
        "--skip-db", action="store_true", help="Skip database setup (Supabase)"
    )
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify existing setup"
    )

    args = parser.parse_args()

    setup = MemorySystemSetup(skip_k8s=args.skip_k8s, skip_db=args.skip_db)

    if args.verify_only:
        if setup.verify_setup():
            logger.info("✅ Memory system verification passed!")
            sys.exit(0)
        else:
            logger.error("❌ Memory system verification failed!")
            sys.exit(1)

    if setup.setup_all():
        setup.print_next_steps()
        sys.exit(0)
    else:
        logger.error("Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
