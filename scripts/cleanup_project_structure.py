#!/usr/bin/env python3
"""
Comprehensive project structure cleanup script for ELFAutomations.
This script reorganizes the project into a clean, maintainable structure.
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class ProjectCleaner:
    def __init__(self, project_root, dry_run=False):
        self.root = Path(project_root)
        self.dry_run = dry_run
        self.moved_files = []
        self.errors = []

    def log(self, message, level="INFO"):
        print(f"[{level}] {message}")

    def create_directory(self, path):
        """Create directory if it doesn't exist."""
        dir_path = self.root / path
        if not dir_path.exists():
            if self.dry_run:
                self.log(f"Would create: {path}")
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log(f"Created: {path}")

    def move_file(self, src, dest):
        """Move file from src to dest."""
        src_path = self.root / src
        dest_path = self.root / dest

        if src_path.exists():
            if dest_path.is_dir():
                dest_path = dest_path / src_path.name

            if self.dry_run:
                self.log(f"Would move: {src} → {dest}")
            else:
                try:
                    shutil.move(str(src_path), str(dest_path))
                    self.log(f"Moved: {src} → {dest}")
                    self.moved_files.append((str(src), str(dest)))
                except Exception as e:
                    self.errors.append(f"Failed to move {src}: {str(e)}")

    def create_directory_structure(self):
        """Create the new organized directory structure."""
        directories = [
            # Source code
            "src",
            "src/elf_automations",
            "src/teams",
            "src/mcps",
            # Infrastructure
            "infrastructure",
            "infrastructure/k8s",
            "infrastructure/docker",
            "infrastructure/terraform",
            # Scripts (organized)
            "scripts/setup",
            "scripts/deployment",
            "scripts/testing",
            "scripts/utilities",
            "scripts/demos",
            "scripts/analysis",
            # Database
            "database",
            "database/schemas",
            "database/migrations",
            "database/seeds",
            "database/backups",
            # Documentation
            "docs/architecture",
            "docs/guides",
            "docs/api",
            "docs/sessions",
            "docs/planning",
            "docs/decisions",
            # Tests
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            # Archive
            "archive",
            "archive/old_scripts",
            "archive/old_docs",
            "archive/deprecated",
            # Examples
            "examples/workflows",
            "examples/configs",
            "examples/teams",
        ]

        self.log("Creating directory structure...")
        for directory in directories:
            self.create_directory(directory)

    def organize_scripts(self):
        """Organize scripts into subdirectories."""
        if not (self.root / "scripts").exists():
            return

        script_patterns = {
            "setup": ["setup_*.py", "setup_*.sh", "install_*.py", "init_*.py"],
            "testing": ["test_*.py", "test_*.sh", "*_test.py", "check_*.py"],
            "deployment": ["deploy_*.py", "deploy_*.sh", "transfer_*.sh", "push_*.sh"],
            "utilities": ["*_manager.py", "*_helper.py", "fix_*.py", "update_*.py"],
            "demos": ["demo_*.py", "demo_*.sh", "example_*.py"],
            "analysis": ["analyze_*.py", "*_analyzer.py", "*_report.py"],
        }

        self.log("Organizing scripts...")
        for category, patterns in script_patterns.items():
            for pattern in patterns:
                for file in (self.root / "scripts").glob(pattern):
                    if file.is_file():
                        self.move_file(
                            f"scripts/{file.name}", f"scripts/{category}/{file.name}"
                        )

    def organize_sql_files(self):
        """Organize SQL files into database directory."""
        self.log("Organizing SQL files...")

        # Move root SQL files
        for sql_file in self.root.glob("*.sql"):
            self.move_file(sql_file.name, "database/schemas/")

        # Organize sql/ directory if it exists
        if (self.root / "sql").exists():
            for sql_file in (self.root / "sql").glob("*.sql"):
                if "create_" in sql_file.name:
                    self.move_file(f"sql/{sql_file.name}", "database/schemas/")
                elif "migrate" in sql_file.name or "migration" in sql_file.name:
                    self.move_file(f"sql/{sql_file.name}", "database/migrations/")
                elif "seed" in sql_file.name:
                    self.move_file(f"sql/{sql_file.name}", "database/seeds/")
                else:
                    self.move_file(f"sql/{sql_file.name}", "database/")

    def organize_documentation(self):
        """Organize documentation files."""
        self.log("Organizing documentation...")

        doc_mappings = {
            # Session notes
            "SESSION*.md": "docs/sessions/",
            "*_SESSION.md": "docs/sessions/",
            # Planning docs
            "AUTONOMY_*.md": "docs/planning/",
            "*_PLAN.md": "docs/planning/",
            "*_ROADMAP.md": "docs/planning/",
            # Guides
            "*_GUIDE.md": "docs/guides/",
            "*_REFERENCE.md": "docs/guides/",
            "*_INTEGRATION_*.md": "docs/guides/",
            # Memory/session files
            "*_MEMORY.md": "docs/sessions/",
            "*_STATUS.md": "docs/sessions/",
            # Architecture
            "*_DESIGN.md": "docs/architecture/",
            "*_ARCHITECTURE.md": "docs/architecture/",
        }

        for pattern, dest in doc_mappings.items():
            for file in self.root.glob(pattern):
                if file.is_file():
                    self.move_file(file.name, dest)

    def move_source_code(self):
        """Move source code to src/ directory."""
        self.log("Organizing source code...")

        # Move elf_automations if it's in root
        if (self.root / "elf_automations").exists():
            self.move_file("elf_automations", "src/elf_automations")

        # Move teams
        if (self.root / "teams").exists():
            self.move_file("teams", "src/teams")

        # Consolidate MCP servers
        mcp_dirs = ["mcps", "mcp-servers", "mcp_servers", "mcp-servers-ts"]
        for mcp_dir in mcp_dirs:
            if (self.root / mcp_dir).exists():
                # Move contents, not the directory itself
                for item in (self.root / mcp_dir).iterdir():
                    self.move_file(f"{mcp_dir}/{item.name}", f"src/mcps/{item.name}")

    def archive_old_files(self):
        """Move old/backup files to archive."""
        self.log("Archiving old files...")

        patterns = [
            "*_backup*",
            "*_old*",
            "*.bak",
            "*_deprecated*",
            "OLD_*",
            "BACKUP_*",
        ]

        for pattern in patterns:
            for file in self.root.glob(pattern):
                if file.is_file():
                    self.move_file(file.name, "archive/")

    def update_gitignore(self):
        """Update .gitignore with new patterns."""
        if self.dry_run:
            self.log("Would update .gitignore")
            return

        gitignore_additions = """
# Archive directory
archive/

# Backup files
*.bak
*_backup*
*_old*

# Database backups
database/backups/

# Local test files
test_local_*
"""

        gitignore_path = self.root / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "a") as f:
                f.write(gitignore_additions)
            self.log("Updated .gitignore")

    def create_migration_log(self):
        """Create a log of all moved files."""
        if self.dry_run or not self.moved_files:
            return

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "files_moved": len(self.moved_files),
            "errors": self.errors,
            "migrations": self.moved_files,
        }

        log_path = self.root / "migration_log.json"
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)
        self.log(f"Created migration log: migration_log.json")

    def run_cleanup(self):
        """Run the complete cleanup process."""
        self.log(f"Starting project cleanup {'(DRY RUN)' if self.dry_run else ''}...")

        # Create new structure
        self.create_directory_structure()

        # Organize different file types
        self.organize_scripts()
        self.organize_sql_files()
        self.organize_documentation()
        self.move_source_code()
        self.archive_old_files()

        # Move infrastructure
        if (self.root / "k8s").exists():
            self.move_file("k8s", "infrastructure/k8s")

        # Update configurations
        self.update_gitignore()
        self.create_migration_log()

        # Report results
        self.log(f"\nCleanup complete! Moved {len(self.moved_files)} files.")
        if self.errors:
            self.log(f"Errors encountered: {len(self.errors)}")
            for error in self.errors:
                self.log(error, "ERROR")

        self.log("\nNext steps:")
        self.log("1. Review the changes")
        self.log("2. Update import paths in Python files")
        self.log("3. Update script references in docs")
        self.log("4. Run tests to ensure everything works")
        self.log("5. Commit changes in logical groups")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up ELFAutomations project structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory (default: current directory)",
    )

    args = parser.parse_args()

    cleaner = ProjectCleaner(args.root, args.dry_run)
    cleaner.run_cleanup()


if __name__ == "__main__":
    main()
