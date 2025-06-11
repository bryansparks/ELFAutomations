"""
Schema validation for database migrations
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Schema validation result"""

    level: ValidationLevel
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

    def __str__(self):
        location = f" (line {self.line_number})" if self.line_number else ""
        suggestion = f"\n  Suggestion: {self.suggestion}" if self.suggestion else ""
        return f"[{self.level.value.upper()}]{location}: {self.message}{suggestion}"


class SchemaValidator:
    """
    Validates SQL schema definitions and migrations
    """

    # Reserved words that shouldn't be used as identifiers
    RESERVED_WORDS = {
        "user",
        "order",
        "group",
        "table",
        "column",
        "select",
        "insert",
        "update",
        "delete",
        "from",
        "where",
        "join",
        "union",
        "having",
    }

    # Recommended conventions
    NAMING_PATTERNS = {
        "table": r"^[a-z][a-z0-9_]*$",
        "column": r"^[a-z][a-z0-9_]*$",
        "index": r"^idx_[a-z0-9_]+$",
        "constraint": r"^[a-z]+_[a-z0-9_]+$",
        "function": r"^[a-z][a-z0-9_]*$",
    }

    def __init__(self):
        """Initialize validator"""
        self.results: List[ValidationResult] = []

    def validate_migration(self, sql_content: str) -> List[ValidationResult]:
        """
        Validate a migration SQL file

        Args:
            sql_content: SQL content to validate

        Returns:
            List of validation results
        """
        self.results = []

        # Split into lines for line number tracking
        lines = sql_content.split("\n")

        # Run various validations
        self._validate_syntax(lines)
        self._validate_naming_conventions(lines)
        self._validate_data_types(lines)
        self._validate_indexes(lines)
        self._validate_constraints(lines)
        self._validate_best_practices(lines)

        return self.results

    def _validate_syntax(self, lines: List[str]):
        """Basic SQL syntax validation"""

        # Check for common syntax errors
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("--"):
                continue

            # Check for missing semicolons (simplified)
            if any(keyword in line.upper() for keyword in ["CREATE", "ALTER", "DROP"]):
                # Look for statement end
                found_semicolon = False
                for j in range(i - 1, len(lines)):
                    if ";" in lines[j]:
                        found_semicolon = True
                        break
                    if j > i + 20:  # Don't look too far
                        break

                if not found_semicolon:
                    self.results.append(
                        ValidationResult(
                            level=ValidationLevel.WARNING,
                            message="Statement might be missing semicolon",
                            line_number=i,
                            suggestion="Ensure all SQL statements end with ;",
                        )
                    )

    def _validate_naming_conventions(self, lines: List[str]):
        """Validate naming conventions"""

        sql_text = "\n".join(lines)

        # Check table names
        table_matches = re.findall(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", sql_text, re.IGNORECASE
        )

        for table_name in table_matches:
            # Check pattern
            if not re.match(self.NAMING_PATTERNS["table"], table_name):
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Table name '{table_name}' doesn't follow naming convention",
                        suggestion="Use lowercase with underscores (e.g., user_profiles)",
                    )
                )

            # Check reserved words
            if table_name.lower() in self.RESERVED_WORDS:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Table name '{table_name}' is a reserved word",
                        suggestion=f"Consider renaming to '{table_name}_table' or similar",
                    )
                )

            # Check length
            if len(table_name) > 63:  # PostgreSQL limit
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Table name '{table_name}' exceeds 63 character limit",
                        suggestion="Use a shorter table name",
                    )
                )

    def _validate_data_types(self, lines: List[str]):
        """Validate data type usage"""

        sql_text = "\n".join(lines)

        # Check for deprecated or problematic data types
        problematic_types = {
            "CHAR": "Use VARCHAR or TEXT instead of CHAR",
            "FLOAT": "Use NUMERIC or DOUBLE PRECISION for better precision",
            "REAL": "Use NUMERIC or DOUBLE PRECISION for better precision",
            "SERIAL": "Use IDENTITY columns or gen_random_uuid() for PostgreSQL 10+",
        }

        for dtype, suggestion in problematic_types.items():
            if re.search(rf"\b{dtype}\b", sql_text, re.IGNORECASE):
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Consider avoiding {dtype} data type",
                        suggestion=suggestion,
                    )
                )

        # Check for missing NOT NULL on important columns
        column_defs = re.findall(
            r"(\w+)\s+(VARCHAR|TEXT|INTEGER|BIGINT|UUID|TIMESTAMP)",
            sql_text,
            re.IGNORECASE,
        )

        for col_name, col_type in column_defs:
            if col_name.lower() in ["name", "email", "username"]:
                # Check if NOT NULL is specified
                pattern = rf"{col_name}\s+{col_type}[^,\n]*"
                match = re.search(pattern, sql_text, re.IGNORECASE)
                if match and "NOT NULL" not in match.group().upper():
                    self.results.append(
                        ValidationResult(
                            level=ValidationLevel.WARNING,
                            message=f"Column '{col_name}' should probably be NOT NULL",
                            suggestion="Add NOT NULL constraint for data integrity",
                        )
                    )

    def _validate_indexes(self, lines: List[str]):
        """Validate index definitions"""

        sql_text = "\n".join(lines)

        # Find CREATE INDEX statements
        index_matches = re.findall(
            r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)\s*\(([^)]+)\)",
            sql_text,
            re.IGNORECASE,
        )

        for index_name, table_name, columns in index_matches:
            # Check naming convention
            if not re.match(self.NAMING_PATTERNS["index"], index_name):
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Index name '{index_name}' doesn't follow convention",
                        suggestion=f"Use format: idx_{table_name}_{columns.replace(', ', '_')}",
                    )
                )

            # Check for duplicate indexes (simplified)
            column_list = [c.strip() for c in columns.split(",")]
            if len(column_list) > 5:
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"Index '{index_name}' has many columns ({len(column_list)})",
                        suggestion="Consider if all columns are necessary for the index",
                    )
                )

    def _validate_constraints(self, lines: List[str]):
        """Validate constraints"""

        sql_text = "\n".join(lines)

        # Check for primary keys
        table_matches = re.findall(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\);",
            sql_text,
            re.IGNORECASE | re.DOTALL,
        )

        for table_name, table_def in table_matches:
            # Check for primary key
            if "PRIMARY KEY" not in table_def.upper():
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Table '{table_name}' missing PRIMARY KEY",
                        suggestion="Add a primary key constraint for data integrity",
                    )
                )

            # Check for created_at/updated_at patterns
            if "created_at" in table_def.lower():
                if (
                    "DEFAULT NOW()" not in table_def
                    and "DEFAULT CURRENT_TIMESTAMP" not in table_def
                ):
                    self.results.append(
                        ValidationResult(
                            level=ValidationLevel.WARNING,
                            message=f"Table '{table_name}' created_at should have DEFAULT NOW()",
                            suggestion="Add DEFAULT NOW() to created_at column",
                        )
                    )

    def _validate_best_practices(self, lines: List[str]):
        """Validate against best practices"""

        sql_text = "\n".join(lines)

        # Check for CASCADE deletes
        if "ON DELETE CASCADE" in sql_text.upper():
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.WARNING,
                    message="Using ON DELETE CASCADE can lead to unintended data loss",
                    suggestion="Consider using ON DELETE RESTRICT or SET NULL instead",
                )
            )

        # Check for missing IF EXISTS/IF NOT EXISTS
        create_without_exists = re.findall(
            r"CREATE\s+(?!.*IF\s+NOT\s+EXISTS)(TABLE|INDEX|VIEW)\s+(\w+)",
            sql_text,
            re.IGNORECASE,
        )

        for obj_type, obj_name in create_without_exists:
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.INFO,
                    message=f"CREATE {obj_type} {obj_name} without IF NOT EXISTS",
                    suggestion="Add IF NOT EXISTS for idempotent migrations",
                )
            )

        # Check for hardcoded values that should be parameters
        hardcoded_emails = re.findall(r"'[^']+@[^']+\.[^']+'", sql_text)
        if hardcoded_emails:
            self.results.append(
                ValidationResult(
                    level=ValidationLevel.WARNING,
                    message="Found hardcoded email addresses",
                    suggestion="Consider using parameters or configuration instead",
                )
            )

        # Check for missing indexes on foreign keys
        foreign_keys = re.findall(
            r"FOREIGN\s+KEY\s*\((\w+)\)\s+REFERENCES", sql_text, re.IGNORECASE
        )

        for fk_column in foreign_keys:
            # Simple check - look for index on this column
            if (
                f"({fk_column})" not in sql_text
                or f"idx_{fk_column}" not in sql_text.lower()
            ):
                self.results.append(
                    ValidationResult(
                        level=ValidationLevel.INFO,
                        message=f"Foreign key column '{fk_column}' might benefit from an index",
                        suggestion=f"Consider adding: CREATE INDEX idx_table_{fk_column} ON table({fk_column})",
                    )
                )

    def get_summary(self) -> Dict[str, int]:
        """Get validation summary"""
        summary = {"errors": 0, "warnings": 0, "info": 0, "total": len(self.results)}

        for result in self.results:
            if result.level == ValidationLevel.ERROR:
                summary["errors"] += 1
            elif result.level == ValidationLevel.WARNING:
                summary["warnings"] += 1
            elif result.level == ValidationLevel.INFO:
                summary["info"] += 1

        return summary

    def has_errors(self) -> bool:
        """Check if validation found any errors"""
        return any(r.level == ValidationLevel.ERROR for r in self.results)

    def print_results(self):
        """Print validation results"""
        if not self.results:
            logger.info("✓ No validation issues found")
            return

        # Group by level
        for level in ValidationLevel:
            level_results = [r for r in self.results if r.level == level]
            if level_results:
                logger.info(f"\n{level.value.upper()}S ({len(level_results)}):")
                for result in level_results:
                    print(f"  {result}")

        # Summary
        summary = self.get_summary()
        logger.info(
            f"\nValidation complete: "
            f"{summary['errors']} errors, "
            f"{summary['warnings']} warnings, "
            f"{summary['info']} info"
        )
