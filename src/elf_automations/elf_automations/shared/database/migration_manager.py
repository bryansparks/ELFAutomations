"""
Enhanced database migration manager with version control
"""

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..credentials import CredentialManager
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class MigrationStatus(Enum):
    """Migration execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


@dataclass
class Migration:
    """Database migration with metadata"""

    version: str  # Format: YYYYMMDD_HHMMSS
    name: str
    description: str
    sql_file: Path
    checksum: str
    dependencies: List[str] = field(default_factory=list)
    rollback_sql: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    status: MigrationStatus = MigrationStatus.PENDING
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None

    @property
    def filename(self) -> str:
        """Get standardized filename"""
        return f"{self.version}_{self.name.lower().replace(' ', '_')}.sql"

    def __lt__(self, other):
        """Sort migrations by version"""
        return self.version < other.version


class MigrationManager:
    """
    Enhanced migration manager with:
    - Version-based ordering
    - Dependency management
    - Rollback support
    - Dry run capability
    - Schema validation
    """

    MIGRATION_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(20) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        checksum VARCHAR(64) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        executed_at TIMESTAMP,
        execution_time_ms INTEGER,
        error TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(checksum)
    );

    CREATE INDEX IF NOT EXISTS idx_migrations_status ON schema_migrations(status);
    CREATE INDEX IF NOT EXISTS idx_migrations_executed ON schema_migrations(executed_at);
    """

    MIGRATION_HISTORY_SQL = """
    CREATE TABLE IF NOT EXISTS migration_history (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        version VARCHAR(20) NOT NULL,
        action VARCHAR(20) NOT NULL, -- 'apply', 'rollback', 'skip'
        started_at TIMESTAMP DEFAULT NOW(),
        completed_at TIMESTAMP,
        success BOOLEAN DEFAULT FALSE,
        details JSONB DEFAULT '{}',
        FOREIGN KEY (version) REFERENCES schema_migrations(version)
    );
    """

    def __init__(
        self,
        migrations_dir: Path = None,
        executor: Optional[Any] = None,
        credential_manager: Optional[CredentialManager] = None,
    ):
        """
        Initialize migration manager

        Args:
            migrations_dir: Directory containing migration files
            executor: Database executor (e.g., SupabaseExecutor)
            credential_manager: For secure credential access
        """
        self.migrations_dir = migrations_dir or Path("migrations")
        self.executor = executor
        self.cred_manager = credential_manager or CredentialManager()

        # Ensure migrations directory exists
        self.migrations_dir.mkdir(exist_ok=True)

        # Migration file patterns
        self.migration_pattern = re.compile(r"^(\d{8}_\d{6})_(.+)\.sql$")

        # Initialize database tables
        if self.executor:
            self._ensure_migration_tables()

    def _ensure_migration_tables(self):
        """Ensure migration tracking tables exist"""
        try:
            self.executor.execute(self.MIGRATION_TABLE_SQL)
            self.executor.execute(self.MIGRATION_HISTORY_SQL)
            logger.info("Migration tables ready")
        except Exception as e:
            logger.error(f"Failed to create migration tables: {e}")

    def create_migration(self, name: str, description: str = "") -> Path:
        """
        Create a new migration file

        Args:
            name: Migration name (e.g., "add_user_profiles")
            description: Migration description

        Returns:
            Path to created migration file
        """
        # Generate version timestamp
        version = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Sanitize name
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower())

        # Create filename
        filename = f"{version}_{safe_name}.sql"
        filepath = self.migrations_dir / filename

        # Migration template
        template = f"""-- Migration: {name}
-- Version: {version}
-- Description: {description}
-- Dependencies: []

-- ============= UP MIGRATION =============

-- Add your schema changes here
-- Example:
-- CREATE TABLE IF NOT EXISTS example (
--     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP DEFAULT NOW()
-- );

-- ============= DOWN MIGRATION ============

-- Add rollback SQL after this marker
-- Example:
-- DROP TABLE IF EXISTS example;
"""

        # Write migration file
        filepath.write_text(template)
        logger.info(f"Created migration: {filepath}")

        return filepath

    def discover_migrations(self) -> List[Migration]:
        """Discover all migration files"""
        migrations = []

        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            match = self.migration_pattern.match(file_path.name)
            if not match:
                logger.warning(f"Skipping invalid migration filename: {file_path.name}")
                continue

            version = match.group(1)
            name = match.group(2).replace("_", " ").title()

            # Parse migration file
            content = file_path.read_text()
            migration = self._parse_migration_file(version, name, file_path, content)

            if migration:
                migrations.append(migration)

        return sorted(migrations)

    def _parse_migration_file(
        self, version: str, name: str, file_path: Path, content: str
    ) -> Optional[Migration]:
        """Parse migration file content"""
        try:
            # Extract metadata from comments
            description = ""
            dependencies = []

            for line in content.split("\n"):
                if line.startswith("-- Description:"):
                    description = line.replace("-- Description:", "").strip()
                elif line.startswith("-- Dependencies:"):
                    deps_str = line.replace("-- Dependencies:", "").strip()
                    if deps_str and deps_str != "[]":
                        dependencies = json.loads(deps_str)

            # Split UP and DOWN migrations
            parts = content.split("-- ============= DOWN MIGRATION ============")
            up_sql = parts[0]
            rollback_sql = parts[1] if len(parts) > 1 else None

            # Calculate checksum
            checksum = hashlib.sha256(content.encode()).hexdigest()

            return Migration(
                version=version,
                name=name,
                description=description,
                sql_file=file_path,
                checksum=checksum,
                dependencies=dependencies,
                rollback_sql=rollback_sql,
            )

        except Exception as e:
            logger.error(f"Failed to parse migration {file_path}: {e}")
            return None

    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been executed"""
        all_migrations = self.discover_migrations()

        if not self.executor:
            return all_migrations

        try:
            # Get executed migrations
            result = self.executor.query(
                "SELECT version, checksum FROM schema_migrations WHERE status = 'completed'"
            )

            executed_versions = {row["version"] for row in result}
            executed_checksums = {row["checksum"] for row in result}

            # Filter pending migrations
            pending = []
            for migration in all_migrations:
                if migration.version not in executed_versions:
                    # Check if content changed (different checksum)
                    if migration.checksum in executed_checksums:
                        logger.warning(
                            f"Migration {migration.name} has different version "
                            f"but same content as an executed migration"
                        )
                    pending.append(migration)

            return pending

        except Exception as e:
            logger.error(f"Failed to get pending migrations: {e}")
            return all_migrations

    def validate_dependencies(self, migration: Migration) -> Tuple[bool, List[str]]:
        """
        Validate migration dependencies

        Returns:
            (is_valid, missing_dependencies)
        """
        if not migration.dependencies:
            return True, []

        if not self.executor:
            return True, []  # Can't validate without DB connection

        try:
            result = self.executor.query(
                "SELECT version FROM schema_migrations WHERE status = 'completed'"
            )

            executed_versions = {row["version"] for row in result}
            missing = [
                dep for dep in migration.dependencies if dep not in executed_versions
            ]

            return len(missing) == 0, missing

        except Exception as e:
            logger.error(f"Failed to validate dependencies: {e}")
            return False, migration.dependencies

    def execute_migration(
        self, migration: Migration, dry_run: bool = False, skip_validation: bool = False
    ) -> bool:
        """
        Execute a single migration

        Args:
            migration: Migration to execute
            dry_run: If True, only show what would be done
            skip_validation: Skip dependency validation

        Returns:
            True if successful
        """
        logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Executing migration: {migration.name}"
        )

        # Validate dependencies
        if not skip_validation:
            is_valid, missing = self.validate_dependencies(migration)
            if not is_valid:
                logger.error(f"Missing dependencies: {missing}")
                return False

        if dry_run:
            logger.info(f"Would execute SQL from: {migration.sql_file}")
            return True

        if not self.executor:
            logger.error("No database executor configured")
            return False

        start_time = datetime.now()

        try:
            # Record migration start
            self._record_migration_start(migration)

            # Read SQL content
            sql_content = migration.sql_file.read_text()

            # Extract only UP migration part
            up_sql = sql_content.split("-- ============= DOWN MIGRATION ============")[
                0
            ]

            # Execute migration
            self.executor.execute(up_sql)

            # Record success
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self._record_migration_success(migration, execution_time)

            logger.info(f"Migration {migration.name} completed in {execution_time}ms")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self._record_migration_failure(migration, str(e))
            return False

    def rollback_migration(self, version: str, dry_run: bool = False) -> bool:
        """
        Rollback a specific migration

        Args:
            version: Migration version to rollback
            dry_run: If True, only show what would be done

        Returns:
            True if successful
        """
        # Find migration
        migrations = self.discover_migrations()
        migration = next((m for m in migrations if m.version == version), None)

        if not migration:
            logger.error(f"Migration {version} not found")
            return False

        if not migration.rollback_sql:
            logger.error(f"Migration {version} has no rollback SQL")
            return False

        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Rolling back: {migration.name}")

        if dry_run:
            logger.info("Would execute rollback SQL")
            return True

        if not self.executor:
            logger.error("No database executor configured")
            return False

        try:
            # Execute rollback
            self.executor.execute(migration.rollback_sql)

            # Update migration status
            self._record_migration_rollback(migration)

            logger.info(f"Successfully rolled back {migration.name}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def migrate(
        self, target_version: Optional[str] = None, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run all pending migrations up to target version

        Args:
            target_version: Stop at this version (None = latest)
            dry_run: If True, only show what would be done

        Returns:
            Migration results
        """
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("No pending migrations")
            return {"executed": [], "failed": [], "skipped": []}

        # Filter by target version
        if target_version:
            pending = [m for m in pending if m.version <= target_version]

        logger.info(f"Found {len(pending)} pending migrations")

        results = {"executed": [], "failed": [], "skipped": []}

        for migration in pending:
            # Check dependencies
            is_valid, missing = self.validate_dependencies(migration)
            if not is_valid:
                logger.warning(
                    f"Skipping {migration.name} due to missing dependencies: {missing}"
                )
                results["skipped"].append(migration.name)
                continue

            # Execute migration
            success = self.execute_migration(migration, dry_run=dry_run)

            if success:
                results["executed"].append(migration.name)
            else:
                results["failed"].append(migration.name)

                # Stop on first failure
                logger.error("Stopping due to migration failure")
                break

        # Summary
        logger.info(
            f"Migration complete: {len(results['executed'])} executed, "
            f"{len(results['failed'])} failed, {len(results['skipped'])} skipped"
        )

        return results

    def _record_migration_start(self, migration: Migration):
        """Record migration start in database"""
        try:
            self.executor.execute(
                """
                INSERT INTO schema_migrations
                (version, name, description, checksum, status)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (version)
                DO UPDATE SET status = %s, error = NULL
            """,
                (
                    migration.version,
                    migration.name,
                    migration.description,
                    migration.checksum,
                    MigrationStatus.RUNNING.value,
                    MigrationStatus.RUNNING.value,
                ),
            )

            self.executor.execute(
                """
                INSERT INTO migration_history (version, action)
                VALUES (%s, 'apply')
            """,
                (migration.version,),
            )

        except Exception as e:
            logger.warning(f"Failed to record migration start: {e}")

    def _record_migration_success(self, migration: Migration, execution_time: int):
        """Record successful migration"""
        try:
            self.executor.execute(
                """
                UPDATE schema_migrations
                SET status = %s,
                    executed_at = NOW(),
                    execution_time_ms = %s,
                    error = NULL
                WHERE version = %s
            """,
                (MigrationStatus.COMPLETED.value, execution_time, migration.version),
            )

            self.executor.execute(
                """
                UPDATE migration_history
                SET completed_at = NOW(), success = TRUE
                WHERE version = %s AND completed_at IS NULL
            """,
                (migration.version,),
            )

        except Exception as e:
            logger.warning(f"Failed to record migration success: {e}")

    def _record_migration_failure(self, migration: Migration, error: str):
        """Record failed migration"""
        try:
            self.executor.execute(
                """
                UPDATE schema_migrations
                SET status = %s, error = %s
                WHERE version = %s
            """,
                (
                    MigrationStatus.FAILED.value,
                    error[:1000],  # Truncate long errors
                    migration.version,
                ),
            )

            self.executor.execute(
                """
                UPDATE migration_history
                SET completed_at = NOW(),
                    success = FALSE,
                    details = jsonb_build_object('error', %s)
                WHERE version = %s AND completed_at IS NULL
            """,
                (error, migration.version),
            )

        except Exception as e:
            logger.warning(f"Failed to record migration failure: {e}")

    def _record_migration_rollback(self, migration: Migration):
        """Record migration rollback"""
        try:
            self.executor.execute(
                """
                UPDATE schema_migrations
                SET status = %s
                WHERE version = %s
            """,
                (MigrationStatus.ROLLED_BACK.value, migration.version),
            )

            self.executor.execute(
                """
                INSERT INTO migration_history (version, action, completed_at, success)
                VALUES (%s, 'rollback', NOW(), TRUE)
            """,
                (migration.version,),
            )

        except Exception as e:
            logger.warning(f"Failed to record rollback: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get migration system status"""
        status = {
            "current_version": None,
            "pending_count": 0,
            "executed_count": 0,
            "failed_count": 0,
            "last_migration": None,
        }

        if not self.executor:
            return status

        try:
            # Get current version
            result = self.executor.query(
                """
                SELECT version, name, executed_at
                FROM schema_migrations
                WHERE status = 'completed'
                ORDER BY version DESC
                LIMIT 1
            """
            )

            if result:
                status["current_version"] = result[0]["version"]
                status["last_migration"] = {
                    "version": result[0]["version"],
                    "name": result[0]["name"],
                    "executed_at": result[0]["executed_at"],
                }

            # Get counts
            counts = self.executor.query(
                """
                SELECT status, COUNT(*) as count
                FROM schema_migrations
                GROUP BY status
            """
            )

            for row in counts:
                if row["status"] == MigrationStatus.COMPLETED.value:
                    status["executed_count"] = row["count"]
                elif row["status"] == MigrationStatus.FAILED.value:
                    status["failed_count"] = row["count"]

            # Count pending
            pending = self.get_pending_migrations()
            status["pending_count"] = len(pending)

        except Exception as e:
            logger.error(f"Failed to get status: {e}")

        return status
