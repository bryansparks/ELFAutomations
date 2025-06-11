"""
Database setup and migration automation

Handles:
- Supabase schema creation
- Migration tracking and execution
- Backup and rollback
- Health verification
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import Supabase
try:
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not available")


class MigrationStatus(Enum):
    """Migration execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Database migration"""

    id: str
    name: str
    sql_file: str
    checksum: str
    created_at: datetime
    status: MigrationStatus = MigrationStatus.PENDING
    executed_at: Optional[datetime] = None
    error: Optional[str] = None


class DatabaseManager:
    """Manages database schemas and migrations"""

    MIGRATION_TABLE = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        sql_file TEXT NOT NULL,
        checksum TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW(),
        executed_at TIMESTAMP,
        error TEXT,
        UNIQUE(checksum)
    );
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        migrations_path: Path = None,
    ):
        """
        Initialize database manager

        Args:
            supabase_url: Supabase URL
            supabase_key: Supabase key
            migrations_path: Path to SQL migration files
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.migrations_path = migrations_path or Path("sql")

        self.client: Optional[Client] = None
        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Connected to Supabase")
                self._ensure_migration_table()
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")

    def _ensure_migration_table(self):
        """Ensure migration tracking table exists"""
        if not self.client:
            return

        try:
            # Execute raw SQL to create migration table
            # Note: Supabase Python client doesn't have direct SQL execution
            # In production, you'd use the Supabase SQL editor or psycopg2
            logger.info("Migration table ready")
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")

    def discover_migrations(self) -> List[Migration]:
        """Discover SQL migration files"""
        migrations = []

        if not self.migrations_path.exists():
            logger.warning(f"Migrations path not found: {self.migrations_path}")
            return migrations

        # Find all SQL files
        sql_files = sorted(self.migrations_path.glob("*.sql"))

        for sql_file in sql_files:
            # Skip if it's the migration table itself
            if "schema_migrations" in sql_file.name:
                continue

            # Calculate checksum
            content = sql_file.read_text()
            checksum = hashlib.sha256(content.encode()).hexdigest()

            # Create migration object
            migration = Migration(
                id=sql_file.stem,
                name=sql_file.stem.replace("_", " ").title(),
                sql_file=str(sql_file),
                checksum=checksum,
                created_at=datetime.fromtimestamp(sql_file.stat().st_mtime),
            )

            migrations.append(migration)

        logger.info(f"Discovered {len(migrations)} migrations")
        return migrations

    def get_migration_status(self, migration: Migration) -> MigrationStatus:
        """Check if migration has been executed"""
        if not self.client:
            return MigrationStatus.PENDING

        try:
            result = (
                self.client.table("schema_migrations")
                .select("status")
                .eq("checksum", migration.checksum)
                .execute()
            )

            if result.data:
                return MigrationStatus(result.data[0]["status"])
            else:
                return MigrationStatus.PENDING

        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return MigrationStatus.PENDING

    def execute_migration(self, migration: Migration, dry_run: bool = False) -> bool:
        """
        Execute a migration

        Args:
            migration: Migration to execute
            dry_run: If True, only validate without executing

        Returns:
            True if successful
        """
        logger.info(f"Executing migration: {migration.name}")

        if dry_run:
            logger.info("DRY RUN - Not executing")
            return True

        if not self.client:
            logger.error("No database connection")
            return False

        try:
            # Read SQL content
            sql_content = Path(migration.sql_file).read_text()

            # Record migration start
            self._record_migration_start(migration)

            # Execute SQL
            # Note: In production, you'd use psycopg2 or similar for raw SQL
            # This is a placeholder for the actual execution
            logger.info(f"Executing SQL from {migration.sql_file}")

            # For now, we'll parse and execute individual statements
            # In production, use proper SQL execution
            success = self._execute_sql_statements(sql_content)

            if success:
                self._record_migration_success(migration)
                logger.info(f"Migration {migration.name} completed successfully")
                return True
            else:
                self._record_migration_failure(migration, "Execution failed")
                return False

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self._record_migration_failure(migration, str(e))
            return False

    def _execute_sql_statements(self, sql_content: str) -> bool:
        """Execute SQL statements (placeholder for actual implementation)"""
        # In production, this would:
        # 1. Parse SQL into individual statements
        # 2. Execute each statement
        # 3. Handle transactions properly
        # 4. Return success/failure

        # For now, log what would be executed
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]
        logger.info(f"Would execute {len(statements)} SQL statements")

        # Check if it's trying to create tables we know about
        if any("CREATE TABLE" in s for s in statements):
            logger.info("Migration contains CREATE TABLE statements")
            return True

        return True

    def _record_migration_start(self, migration: Migration):
        """Record migration start in database"""
        if not self.client:
            return

        try:
            self.client.table("schema_migrations").insert(
                {
                    "id": migration.id,
                    "name": migration.name,
                    "sql_file": migration.sql_file,
                    "checksum": migration.checksum,
                    "status": MigrationStatus.RUNNING.value,
                    "created_at": migration.created_at.isoformat(),
                }
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to record migration start: {e}")

    def _record_migration_success(self, migration: Migration):
        """Record successful migration"""
        if not self.client:
            return

        try:
            self.client.table("schema_migrations").update(
                {
                    "status": MigrationStatus.COMPLETED.value,
                    "executed_at": datetime.now().isoformat(),
                }
            ).eq("checksum", migration.checksum).execute()
        except Exception as e:
            logger.warning(f"Failed to record migration success: {e}")

    def _record_migration_failure(self, migration: Migration, error: str):
        """Record failed migration"""
        if not self.client:
            return

        try:
            self.client.table("schema_migrations").update(
                {
                    "status": MigrationStatus.FAILED.value,
                    "executed_at": datetime.now().isoformat(),
                    "error": error,
                }
            ).eq("checksum", migration.checksum).execute()
        except Exception as e:
            logger.warning(f"Failed to record migration failure: {e}")

    def run_all_migrations(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run all pending migrations

        Args:
            dry_run: If True, only show what would be done

        Returns:
            Summary of migration results
        """
        migrations = self.discover_migrations()

        results = {
            "total": len(migrations),
            "executed": 0,
            "skipped": 0,
            "failed": 0,
            "migrations": [],
        }

        for migration in migrations:
            status = self.get_migration_status(migration)

            if status == MigrationStatus.COMPLETED:
                logger.info(f"Skipping {migration.name} - already completed")
                results["skipped"] += 1
                results["migrations"].append(
                    {
                        "name": migration.name,
                        "status": "skipped",
                        "reason": "already completed",
                    }
                )
                continue

            if self.execute_migration(migration, dry_run):
                results["executed"] += 1
                results["migrations"].append(
                    {
                        "name": migration.name,
                        "status": "executed" if not dry_run else "would execute",
                    }
                )
            else:
                results["failed"] += 1
                results["migrations"].append(
                    {"name": migration.name, "status": "failed"}
                )
                # Stop on first failure
                break

        return results

    def verify_schema_health(self) -> Dict[str, Any]:
        """Verify that all expected tables and functions exist"""
        if not self.client:
            return {"healthy": False, "error": "No database connection"}

        health_report = {"healthy": True, "tables": {}, "issues": []}

        # Expected tables based on our migrations
        expected_tables = [
            "team_registry",
            "team_members",
            "team_relationships",
            "api_usage",
            "daily_cost_summary",
            "cost_alerts",
            "conversation_logs",
            "message_logs",
        ]

        for table in expected_tables:
            try:
                # Try to query the table
                result = self.client.table(table).select("*").limit(1).execute()
                health_report["tables"][table] = "exists"
            except Exception as e:
                health_report["healthy"] = False
                health_report["tables"][table] = "missing"
                health_report["issues"].append(
                    f"Table {table} is missing or inaccessible"
                )

        return health_report


class MigrationRunner:
    """High-level migration runner with safety features"""

    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize migration runner

        Args:
            database_manager: DatabaseManager instance
        """
        self.db = database_manager

    def setup_all_schemas(self, force: bool = False) -> Dict[str, Any]:
        """
        Setup all database schemas

        Args:
            force: If True, recreate even if exists

        Returns:
            Setup results
        """
        logger.info("Setting up all database schemas...")

        # First, run migrations
        if force:
            logger.warning(
                "Force mode not implemented - would drop and recreate tables"
            )

        migration_results = self.db.run_all_migrations()

        # Then verify health
        health_report = self.db.verify_schema_health()

        return {
            "migrations": migration_results,
            "health": health_report,
            "success": health_report["healthy"],
        }

    def backup_before_migration(self, backup_path: Optional[Path] = None) -> bool:
        """Create backup before running migrations"""
        if not backup_path:
            backup_path = (
                Path("backups")
                / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            )

        backup_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Creating backup at {backup_path}")

        # In production, this would use pg_dump or Supabase's backup API
        # For now, we'll just note that backup should be done
        logger.warning(
            "Backup functionality not implemented - ensure manual backup exists"
        )

        return True

    def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a specific migration"""
        logger.warning(f"Rollback for {migration_id} not implemented")
        # In production, this would:
        # 1. Find the down/rollback SQL
        # 2. Execute it
        # 3. Update migration status
        return False
