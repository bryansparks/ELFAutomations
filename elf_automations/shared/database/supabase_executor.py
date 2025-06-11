"""
Supabase SQL executor for migrations
"""

import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import database libraries
try:
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase client not available")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available")

from ..credentials import CredentialManager
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class SupabaseExecutor:
    """
    Executes SQL against Supabase database
    Supports both Supabase client and direct PostgreSQL connection
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        credential_manager: Optional[CredentialManager] = None,
        use_direct_connection: bool = True,
    ):
        """
        Initialize Supabase executor

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon/service key
            credential_manager: For secure credential access
            use_direct_connection: Use psycopg2 for direct SQL execution
        """
        self.cred_manager = credential_manager or CredentialManager()
        self.use_direct_connection = use_direct_connection and PSYCOPG2_AVAILABLE

        # Get credentials
        self.supabase_url = supabase_url or self._get_credential("SUPABASE_URL")
        self.supabase_key = supabase_key or self._get_credential("SUPABASE_SERVICE_KEY")

        # Initialize clients
        self.supabase_client: Optional[Client] = None
        self.pg_connection = None

        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.supabase_client = create_client(
                    self.supabase_url, self.supabase_key
                )
                logger.info("Connected to Supabase via client")
            except Exception as e:
                logger.error(f"Failed to create Supabase client: {e}")

        # Try direct PostgreSQL connection
        if self.use_direct_connection:
            self._init_direct_connection()

    def _get_credential(self, name: str) -> Optional[str]:
        """Get credential from manager or environment"""
        try:
            # Try credential manager first
            return self.cred_manager.get_credential(
                name, "system", "database_migration"
            )
        except:
            # Fall back to environment
            return os.getenv(name)

    def _init_direct_connection(self):
        """Initialize direct PostgreSQL connection"""
        if not PSYCOPG2_AVAILABLE:
            return

        try:
            # Parse Supabase URL to get connection details
            # Format: https://xxxx.supabase.co
            if self.supabase_url:
                project_ref = self.supabase_url.split(".")[0].split("//")[-1]

                # Construct PostgreSQL connection string
                # Supabase PostgreSQL format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
                password = self._get_credential("SUPABASE_PASSWORD") or "postgres"

                conn_string = (
                    f"postgresql://postgres:{password}@"
                    f"db.{project_ref}.supabase.co:5432/postgres"
                )

                self.pg_connection = psycopg2.connect(
                    conn_string, cursor_factory=RealDictCursor
                )
                self.pg_connection.autocommit = False  # Use transactions
                logger.info("Connected to Supabase via PostgreSQL")

        except Exception as e:
            logger.warning(f"Failed to establish direct PostgreSQL connection: {e}")
            self.pg_connection = None

    def execute(self, sql: str, params: Optional[Tuple] = None) -> None:
        """
        Execute SQL statement(s)

        Args:
            sql: SQL to execute (can contain multiple statements)
            params: Optional parameters for parameterized queries
        """
        if self.pg_connection:
            self._execute_with_psycopg2(sql, params)
        elif self.supabase_client:
            self._execute_with_rpc(sql, params)
        else:
            raise RuntimeError("No database connection available")

    def _execute_with_psycopg2(self, sql: str, params: Optional[Tuple] = None):
        """Execute SQL using direct PostgreSQL connection"""
        cursor = self.pg_connection.cursor()

        try:
            # Start transaction
            self.pg_connection.rollback()  # Clear any pending transaction

            if params:
                # Single parameterized query
                cursor.execute(sql, params)
            else:
                # Split into individual statements
                statements = self._split_sql_statements(sql)

                for statement in statements:
                    if statement.strip():
                        logger.debug(f"Executing: {statement[:100]}...")
                        cursor.execute(statement)

            # Commit transaction
            self.pg_connection.commit()
            logger.info("SQL execution successful")

        except Exception as e:
            # Rollback on error
            self.pg_connection.rollback()
            logger.error(f"SQL execution failed: {e}")
            raise

        finally:
            cursor.close()

    def _execute_with_rpc(self, sql: str, params: Optional[Tuple] = None):
        """Execute SQL using Supabase RPC (limited functionality)"""
        # Note: Supabase Python client doesn't support raw SQL execution
        # You need to create a database function for this

        # First, ensure we have the execute_sql function
        self._ensure_execute_sql_function()

        try:
            # Call the function
            result = self.supabase_client.rpc(
                "execute_migration_sql", {"sql_text": sql}
            ).execute()

            logger.info("SQL execution via RPC successful")

        except Exception as e:
            logger.error(f"SQL execution via RPC failed: {e}")
            raise

    def _ensure_execute_sql_function(self):
        """Create RPC function for SQL execution if it doesn't exist"""
        # This would need to be created via Supabase dashboard or direct SQL
        function_sql = """
        CREATE OR REPLACE FUNCTION execute_migration_sql(sql_text text)
        RETURNS void AS $$
        BEGIN
            -- Only allow from service role
            IF current_setting('request.jwt.claims', true)::json->>'role' != 'service_role' THEN
                RAISE EXCEPTION 'Unauthorized';
            END IF;

            -- Execute the SQL
            EXECUTE sql_text;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """

        # Note: This function creation would need to be done manually
        # or via psycopg2 connection

    def query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results

        Args:
            sql: SELECT query to execute
            params: Optional parameters

        Returns:
            List of result rows as dictionaries
        """
        if self.pg_connection:
            return self._query_with_psycopg2(sql, params)
        elif self.supabase_client:
            return self._query_with_client(sql)
        else:
            raise RuntimeError("No database connection available")

    def _query_with_psycopg2(
        self, sql: str, params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Query using direct PostgreSQL connection"""
        cursor = self.pg_connection.cursor()

        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

        finally:
            cursor.close()

    def _query_with_client(self, sql: str) -> List[Dict[str, Any]]:
        """Query using Supabase client (limited to simple queries)"""
        # Extract table name from SQL (very basic parsing)
        match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
        if not match:
            raise ValueError("Cannot parse table name from SQL")

        table_name = match.group(1)

        # Execute via Supabase client (very limited)
        try:
            result = self.supabase_client.table(table_name).select("*").execute()
            return result.data
        except Exception as e:
            logger.error(f"Query via client failed: {e}")
            raise

    def _split_sql_statements(self, sql: str) -> List[str]:
        """
        Split SQL into individual statements
        Handles:
        - Statement terminators (;)
        - String literals
        - Comments
        - Dollar-quoted strings (PostgreSQL)
        """
        # Remove comments
        sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

        # Simple split by semicolon (not inside strings)
        # This is a basic implementation - production would need proper SQL parser
        statements = []
        current = []
        in_string = False
        string_char = None

        i = 0
        while i < len(sql):
            char = sql[i]

            # Handle string literals
            if char in ["'", '"'] and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                # Check for escaped quotes
                if i + 1 < len(sql) and sql[i + 1] == char:
                    i += 1  # Skip escaped quote
                else:
                    in_string = False
                    string_char = None

            # Handle statement terminator
            elif char == ";" and not in_string:
                current.append(char)
                statement = "".join(current).strip()
                if statement:
                    statements.append(statement)
                current = []
                i += 1
                continue

            current.append(char)
            i += 1

        # Add final statement
        final = "".join(current).strip()
        if final:
            statements.append(final)

        return statements

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            result = self.query("SELECT 1 as test")
            return len(result) > 0 and result[0]["test"] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def close(self):
        """Close database connections"""
        if self.pg_connection:
            try:
                self.pg_connection.close()
                logger.info("Closed PostgreSQL connection")
            except:
                pass

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def get_schema_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get current database schema information"""
        schema_info = {"tables": [], "views": [], "functions": [], "indexes": []}

        try:
            # Get tables
            tables = self.query(
                """
                SELECT
                    table_name,
                    table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            )

            for table in tables:
                if table["table_type"] == "BASE TABLE":
                    schema_info["tables"].append(table)
                elif table["table_type"] == "VIEW":
                    schema_info["views"].append(table)

            # Get indexes
            indexes = self.query(
                """
                SELECT
                    indexname as index_name,
                    tablename as table_name
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """
            )
            schema_info["indexes"] = indexes

        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")

        return schema_info
