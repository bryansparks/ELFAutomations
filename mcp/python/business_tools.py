"""
Business Tools MCP Server for ELF Automations

This module provides business-specific tools through the MCP protocol,
including customer management, lead tracking, and task management.
"""

import asyncio
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Sequence

import asyncpg
import structlog
from dotenv import load_dotenv

from .base import BaseMCPServer, MCPResource, MCPTool

logger = structlog.get_logger(__name__)

# Try to import Supabase client
try:
    from supabase import Client as SupabaseClient
    from supabase import create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    SupabaseClient = None


class BusinessToolsServer(BaseMCPServer):
    """
    Business Tools MCP Server

    Provides business-focused tools for customer management, lead tracking,
    task management, and business metrics. Supports both PostgreSQL and Supabase.
    """

    def __init__(self):
        super().__init__("business-tools", "Business management and analytics tools")
        self.db_pool: Optional[asyncpg.Pool] = None
        self.supabase_client: Optional[SupabaseClient] = None
        self.use_supabase = False

        # Load environment variables
        load_dotenv()

        # Determine which database to use
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
        postgres_url = os.getenv("DATABASE_URL")

        if supabase_url and supabase_key and SUPABASE_AVAILABLE:
            self.use_supabase = True
            self.logger.info("Using Supabase as database backend")
        elif postgres_url:
            self.use_supabase = False
            self.logger.info("Using PostgreSQL as database backend")
        else:
            self.logger.warning(
                "No database configuration found - some features may be limited"
            )

    async def start(self):
        """Start the MCP server and initialize database connections."""
        await super().start()

        if self.use_supabase:
            await self._init_supabase()
        else:
            await self._init_postgres()

    async def _init_supabase(self):
        """Initialize Supabase client."""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

            if not supabase_url or not supabase_key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_ANON_KEY/SUPABASE_KEY are required"
                )

            self.supabase_client = create_client(supabase_url, supabase_key)

            # Test connection
            result = (
                self.supabase_client.table("customers").select("id").limit(1).execute()
            )
            self.logger.info("Supabase connection established successfully")

        except Exception as e:
            self.logger.error("Failed to initialize Supabase client", error=str(e))
            self.supabase_client = None

    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool."""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                self.logger.warning("DATABASE_URL not set - database features disabled")
                return

            self.db_pool = await asyncpg.create_pool(
                database_url, min_size=1, max_size=10, command_timeout=30
            )

            # Test connection
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self.logger.info("PostgreSQL connection pool established")

        except Exception as e:
            self.logger.error("Failed to initialize PostgreSQL pool", error=str(e))
            self.db_pool = None

    async def stop(self):
        """Stop the MCP server and cleanup connections."""
        if self.db_pool:
            await self.db_pool.close()
            self.db_pool = None

        # Supabase client doesn't need explicit cleanup
        self.supabase_client = None

        await super().stop()

    async def _execute_query(
        self, query: str, params: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Execute a database query using the appropriate backend."""
        if self.use_supabase and self.supabase_client:
            return await self._execute_supabase_query(query, params)
        elif self.db_pool:
            return await self._execute_postgres_query(query, params)
        else:
            raise RuntimeError("No database connection available")

    async def _execute_supabase_query(
        self, query: str, params: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Execute query using Supabase client."""
        try:
            # For Supabase, we need to use the PostgREST API instead of raw SQL
            # This is a simplified approach - in practice, you'd use Supabase's query builder

            # Parse simple queries and convert to Supabase operations
            query_lower = query.lower().strip()

            if query_lower.startswith("select"):
                # Extract table name from SELECT query (simplified)
                if "from customers" in query_lower:
                    result = (
                        self.supabase_client.table("customers").select("*").execute()
                    )
                    return result.data
                elif "from leads" in query_lower:
                    result = self.supabase_client.table("leads").select("*").execute()
                    return result.data
                elif "from tasks" in query_lower:
                    result = self.supabase_client.table("tasks").select("*").execute()
                    return result.data
                elif "from business_metrics" in query_lower:
                    result = (
                        self.supabase_client.table("business_metrics")
                        .select("*")
                        .execute()
                    )
                    return result.data
                else:
                    # Fallback for unknown queries
                    self.logger.warning("Unsupported query for Supabase", query=query)
                    return []
            else:
                # For non-SELECT queries, we'd need more sophisticated parsing
                self.logger.warning(
                    "Non-SELECT queries not yet supported for Supabase", query=query
                )
                return []

        except Exception as e:
            self.logger.error("Supabase query failed", query=query, error=str(e))
            return []

    async def _execute_postgres_query(
        self, query: str, params: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """Execute query using PostgreSQL connection."""
        try:
            async with self.db_pool.acquire() as conn:
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)

                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error("PostgreSQL query failed", query=query, error=str(e))
            return []

    async def _insert_record(
        self, table: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Insert a record using the appropriate backend."""
        if self.use_supabase and self.supabase_client:
            try:
                result = self.supabase_client.table(table).insert(data).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                self.logger.error("Supabase insert failed", table=table, error=str(e))
                return None
        elif self.db_pool:
            try:
                columns = list(data.keys())
                values = list(data.values())
                placeholders = ", ".join(f"${i+1}" for i in range(len(values)))

                query = f"""
                INSERT INTO {table} ({", ".join(columns)})
                VALUES ({placeholders})
                RETURNING *
                """

                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(query, *values)
                    return dict(row) if row else None
            except Exception as e:
                self.logger.error("PostgreSQL insert failed", table=table, error=str(e))
                return None
        else:
            raise RuntimeError("No database connection available")

    async def _update_record(
        self, table: str, record_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a record using the appropriate backend."""
        if self.use_supabase and self.supabase_client:
            try:
                result = (
                    self.supabase_client.table(table)
                    .update(data)
                    .eq("id", record_id)
                    .execute()
                )
                return result.data[0] if result.data else None
            except Exception as e:
                self.logger.error("Supabase update failed", table=table, error=str(e))
                return None
        elif self.db_pool:
            try:
                set_clauses = [f"{col} = ${i+2}" for i, col in enumerate(data.keys())]
                query = f"""
                UPDATE {table}
                SET {", ".join(set_clauses)}
                WHERE id = $1
                RETURNING *
                """

                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(query, record_id, *data.values())
                    return dict(row) if row else None
            except Exception as e:
                self.logger.error("PostgreSQL update failed", table=table, error=str(e))
                return None
        else:
            raise RuntimeError("No database connection available")

    def _register_tools(self) -> None:
        """Register all business tools."""

        # Customer management tools
        self.register_tool(
            MCPTool(
                name="create_customer",
                description="Create a new customer record",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Customer name"},
                        "email": {"type": "string", "description": "Customer email"},
                        "phone": {"type": "string", "description": "Customer phone"},
                        "company": {
                            "type": "string",
                            "description": "Customer company",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional customer data",
                        },
                    },
                    "required": ["name", "email"],
                },
            )
        )

        self.register_tool(
            MCPTool(
                name="get_customer",
                description="Retrieve customer information by ID or email",
                parameters={
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer UUID",
                        },
                        "email": {"type": "string", "description": "Customer email"},
                    },
                    "oneOf": [{"required": ["customer_id"]}, {"required": ["email"]}],
                },
            )
        )

        self.register_tool(
            MCPTool(
                name="update_customer",
                description="Update customer information",
                parameters={
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer UUID",
                        },
                        "name": {"type": "string", "description": "Customer name"},
                        "email": {"type": "string", "description": "Customer email"},
                        "phone": {"type": "string", "description": "Customer phone"},
                        "company": {
                            "type": "string",
                            "description": "Customer company",
                        },
                        "status": {"type": "string", "description": "Customer status"},
                        "metadata": {
                            "type": "object",
                            "description": "Additional customer data",
                        },
                    },
                    "required": ["customer_id"],
                },
            )
        )

        # Lead management tools
        self.register_tool(
            MCPTool(
                name="create_lead",
                description="Create a new lead",
                parameters={
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Associated customer UUID",
                        },
                        "source": {"type": "string", "description": "Lead source"},
                        "score": {
                            "type": "integer",
                            "description": "Lead score (0-100)",
                        },
                        "assigned_agent_id": {
                            "type": "string",
                            "description": "Assigned agent UUID",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional lead data",
                        },
                    },
                    "required": ["customer_id", "source"],
                },
            )
        )

        self.register_tool(
            MCPTool(
                name="update_lead_score",
                description="Update lead scoring based on activities",
                parameters={
                    "type": "object",
                    "properties": {
                        "lead_id": {"type": "string", "description": "Lead UUID"},
                        "score_change": {
                            "type": "integer",
                            "description": "Score change (+/-)",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for score change",
                        },
                    },
                    "required": ["lead_id", "score_change"],
                },
            )
        )

        self.register_tool(
            MCPTool(
                name="get_leads",
                description="Get leads with optional filtering",
                parameters={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Lead status filter",
                        },
                        "assigned_agent_id": {
                            "type": "string",
                            "description": "Assigned agent filter",
                        },
                        "min_score": {
                            "type": "integer",
                            "description": "Minimum score filter",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results",
                            "default": 50,
                        },
                    },
                },
            )
        )

        # Task management tools
        self.register_tool(
            MCPTool(
                name="create_task",
                description="Create a new task",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "description": {
                            "type": "string",
                            "description": "Task description",
                        },
                        "type": {"type": "string", "description": "Task type"},
                        "priority": {
                            "type": "integer",
                            "description": "Priority (1-5)",
                            "default": 3,
                        },
                        "assigned_agent_id": {
                            "type": "string",
                            "description": "Assigned agent UUID",
                        },
                        "created_by_agent_id": {
                            "type": "string",
                            "description": "Creating agent UUID",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date (ISO format)",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional task data",
                        },
                    },
                    "required": ["title", "created_by_agent_id"],
                },
            )
        )

        self.register_tool(
            MCPTool(
                name="update_task_status",
                description="Update task status",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task UUID"},
                        "status": {"type": "string", "description": "New status"},
                        "completion_notes": {
                            "type": "string",
                            "description": "Completion notes",
                        },
                    },
                    "required": ["task_id", "status"],
                },
            )
        )

        self.register_tool(
            MCPTool(
                name="get_tasks",
                description="Get tasks with optional filtering",
                parameters={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Task status filter",
                        },
                        "assigned_agent_id": {
                            "type": "string",
                            "description": "Assigned agent filter",
                        },
                        "created_by_agent_id": {
                            "type": "string",
                            "description": "Creator agent filter",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Priority filter",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results",
                            "default": 50,
                        },
                    },
                },
            )
        )

        # Business metrics tools
        self.register_tool(
            MCPTool(
                name="get_business_metrics",
                description="Get business performance metrics",
                parameters={
                    "type": "object",
                    "properties": {
                        "metric_type": {
                            "type": "string",
                            "description": "Type of metrics to retrieve",
                        },
                        "time_period": {
                            "type": "string",
                            "description": "Time period (day, week, month)",
                        },
                        "department": {
                            "type": "string",
                            "description": "Department filter",
                        },
                    },
                },
            )
        )

    def _register_resources(self) -> None:
        """Register business resources."""

        self.register_resource(
            MCPResource(
                uri="business://customers",
                name="Customers Database",
                description="Customer records and information",
                mime_type="application/json",
            )
        )

        self.register_resource(
            MCPResource(
                uri="business://leads",
                name="Leads Database",
                description="Lead tracking and scoring data",
                mime_type="application/json",
            )
        )

        self.register_resource(
            MCPResource(
                uri="business://tasks",
                name="Tasks Database",
                description="Task management and tracking",
                mime_type="application/json",
            )
        )

        self.register_resource(
            MCPResource(
                uri="business://metrics",
                name="Business Metrics",
                description="Business performance metrics and KPIs",
                mime_type="application/json",
            )
        )

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a business tool."""
        self.logger.info("Calling business tool", tool_name=tool_name)

        # Route to appropriate handler
        if tool_name == "create_customer":
            return await self._create_customer(arguments)
        elif tool_name == "get_customer":
            return await self._get_customer(arguments)
        elif tool_name == "update_customer":
            return await self._update_customer(arguments)
        elif tool_name == "create_lead":
            return await self._create_lead(arguments)
        elif tool_name == "update_lead_score":
            return await self._update_lead_score(arguments)
        elif tool_name == "get_leads":
            return await self._get_leads(arguments)
        elif tool_name == "create_task":
            return await self._create_task(arguments)
        elif tool_name == "update_task_status":
            return await self._update_task_status(arguments)
        elif tool_name == "get_tasks":
            return await self._get_tasks(arguments)
        elif tool_name == "get_business_metrics":
            return await self._get_business_metrics(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a business resource."""
        self.logger.info("Reading business resource", uri=uri)

        if uri == "business://customers":
            return await self._read_customers_resource()
        elif uri == "business://leads":
            return await self._read_leads_resource()
        elif uri == "business://tasks":
            return await self._read_tasks_resource()
        elif uri == "business://metrics":
            return await self._read_metrics_resource()
        else:
            raise ValueError(f"Unknown resource: {uri}")

    # Customer management implementations
    async def _create_customer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        customer_id = str(uuid.uuid4())

        if self.use_supabase and self.supabase_client:
            data = {
                "id": customer_id,
                "name": args["name"],
                "email": args["email"],
                "phone": args.get("phone"),
                "company": args.get("company"),
                "metadata": json.dumps(args.get("metadata", {})),
            }
            result = await self._insert_record("customers", data)
            if result:
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "message": f"Customer {args['name']} created successfully",
                }
            else:
                return {"error": "Failed to create customer"}
        else:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO business.customers (id, name, email, phone, company, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    customer_id,
                    args["name"],
                    args["email"],
                    args.get("phone"),
                    args.get("company"),
                    json.dumps(args.get("metadata", {})),
                )

            return {
                "success": True,
                "customer_id": customer_id,
                "message": f"Customer {args['name']} created successfully",
            }

    async def _get_customer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get customer information."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        if self.use_supabase and self.supabase_client:
            if "customer_id" in args:
                result = (
                    self.supabase_client.table("customers")
                    .select("*")
                    .eq("id", args["customer_id"])
                    .execute()
                )
                if result.data:
                    return {"success": True, "customer": result.data[0]}
                else:
                    return {"success": False, "message": "Customer not found"}
            else:
                result = (
                    self.supabase_client.table("customers")
                    .select("*")
                    .eq("email", args["email"])
                    .execute()
                )
                if result.data:
                    return {"success": True, "customer": result.data[0]}
                else:
                    return {"success": False, "message": "Customer not found"}
        else:
            async with self.db_pool.acquire() as conn:
                if "customer_id" in args:
                    row = await conn.fetchrow(
                        "SELECT * FROM business.customers WHERE id = $1",
                        args["customer_id"],
                    )
                else:
                    row = await conn.fetchrow(
                        "SELECT * FROM business.customers WHERE email = $1",
                        args["email"],
                    )

                if row:
                    return {"success": True, "customer": dict(row)}
                else:
                    return {"success": False, "message": "Customer not found"}

    async def _update_customer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer information."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        if self.use_supabase and self.supabase_client:
            data = {
                "name": args.get("name"),
                "email": args.get("email"),
                "phone": args.get("phone"),
                "company": args.get("company"),
                "status": args.get("status"),
                "metadata": json.dumps(args.get("metadata", {})),
            }
            result = await self._update_record("customers", args["customer_id"], data)
            if result:
                return {"success": True, "message": "Customer updated successfully"}
            else:
                return {"error": "Failed to update customer"}
        else:
            # Build update query dynamically
            update_fields = []
            values = []
            param_count = 1

            for field in ["name", "email", "phone", "company", "status"]:
                if field in args:
                    update_fields.append(f"{field} = ${param_count}")
                    values.append(args[field])
                    param_count += 1

            if "metadata" in args:
                update_fields.append(f"metadata = ${param_count}")
                values.append(json.dumps(args["metadata"]))
                param_count += 1

            if not update_fields:
                return {"error": "No fields to update"}

            values.append(args["customer_id"])

            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    f"""
                    UPDATE business.customers
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE id = ${param_count}
                """,
                    *values,
                )

                if result == "UPDATE 1":
                    return {"success": True, "message": "Customer updated successfully"}
                else:
                    return {"success": False, "message": "Customer not found"}

    # Lead management implementations
    async def _create_lead(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lead."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        lead_id = str(uuid.uuid4())

        if self.use_supabase and self.supabase_client:
            data = {
                "id": lead_id,
                "customer_id": args["customer_id"],
                "source": args["source"],
                "score": args.get("score", 0),
                "assigned_agent_id": args.get("assigned_agent_id"),
                "metadata": json.dumps(args.get("metadata", {})),
            }
            result = await self._insert_record("leads", data)
            if result:
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "message": "Lead created successfully",
                }
            else:
                return {"error": "Failed to create lead"}
        else:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO business.leads (id, customer_id, source, score, assigned_agent_id, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    lead_id,
                    args["customer_id"],
                    args["source"],
                    args.get("score", 0),
                    args.get("assigned_agent_id"),
                    json.dumps(args.get("metadata", {})),
                )

            return {
                "success": True,
                "lead_id": lead_id,
                "message": "Lead created successfully",
            }

    async def _update_lead_score(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update lead score."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        if self.use_supabase and self.supabase_client:
            data = {"score": args["score_change"]}
            result = await self._update_record("leads", args["lead_id"], data)
            if result:
                return {
                    "success": True,
                    "new_score": result["score"],
                    "message": f"Lead score updated by {args['score_change']}",
                }
            else:
                return {"error": "Failed to update lead score"}
        else:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE business.leads
                    SET score = GREATEST(0, LEAST(100, score + $1)), updated_at = NOW()
                    WHERE id = $2
                """,
                    args["score_change"],
                    args["lead_id"],
                )

                if result == "UPDATE 1":
                    # Get updated score
                    row = await conn.fetchrow(
                        "SELECT score FROM business.leads WHERE id = $1",
                        args["lead_id"],
                    )

                    return {
                        "success": True,
                        "new_score": row["score"] if row else None,
                        "message": f"Lead score updated by {args['score_change']}",
                    }
                else:
                    return {"success": False, "message": "Lead not found"}

    async def _get_leads(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get leads with filtering."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        if self.use_supabase and self.supabase_client:
            query = self.supabase_client.table("leads").select("*")
            if "status" in args:
                query = query.eq("status", args["status"])
            if "assigned_agent_id" in args:
                query = query.eq("assigned_agent_id", args["assigned_agent_id"])
            if "min_score" in args:
                query = query.gte("score", args["min_score"])
            result = query.execute()
            return {"success": True, "leads": result.data, "count": len(result.data)}
        else:
            # Build query with filters
            where_conditions = []
            values = []
            param_count = 1

            if "status" in args:
                where_conditions.append(f"status = ${param_count}")
                values.append(args["status"])
                param_count += 1

            if "assigned_agent_id" in args:
                where_conditions.append(f"assigned_agent_id = ${param_count}")
                values.append(args["assigned_agent_id"])
                param_count += 1

            if "min_score" in args:
                where_conditions.append(f"score >= ${param_count}")
                values.append(args["min_score"])
                param_count += 1

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )
            limit = args.get("limit", 50)

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT * FROM business.leads
                    {where_clause}
                    ORDER BY score DESC, created_at DESC
                    LIMIT {limit}
                """,
                    *values,
                )

                return {
                    "success": True,
                    "leads": [dict(row) for row in rows],
                    "count": len(rows),
                }

    # Task management implementations
    async def _create_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        task_id = str(uuid.uuid4())
        due_date = None
        if "due_date" in args:
            try:
                due_date = datetime.fromisoformat(args["due_date"])
            except ValueError:
                return {"error": "Invalid due_date format"}

        if self.use_supabase and self.supabase_client:
            data = {
                "id": task_id,
                "title": args["title"],
                "description": args.get("description"),
                "type": args.get("type"),
                "priority": args.get("priority", 3),
                "assigned_agent_id": args.get("assigned_agent_id"),
                "created_by_agent_id": args["created_by_agent_id"],
                "due_date": due_date,
                "metadata": json.dumps(args.get("metadata", {})),
            }
            result = await self._insert_record("tasks", data)
            if result:
                return {
                    "success": True,
                    "task_id": task_id,
                    "message": f"Task '{args['title']}' created successfully",
                }
            else:
                return {"error": "Failed to create task"}
        else:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO business.tasks
                    (id, title, description, type, priority, assigned_agent_id, created_by_agent_id, due_date, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    task_id,
                    args["title"],
                    args.get("description"),
                    args.get("type"),
                    args.get("priority", 3),
                    args.get("assigned_agent_id"),
                    args["created_by_agent_id"],
                    due_date,
                    json.dumps(args.get("metadata", {})),
                )

            return {
                "success": True,
                "task_id": task_id,
                "message": f"Task '{args['title']}' created successfully",
            }

    async def _update_task_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update task status."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        completed_at = None
        if args["status"] == "completed":
            completed_at = datetime.utcnow()

        if self.use_supabase and self.supabase_client:
            data = {"status": args["status"], "completed_at": completed_at}
            result = await self._update_record("tasks", args["task_id"], data)
            if result:
                return {
                    "success": True,
                    "message": f"Task status updated to {args['status']}",
                }
            else:
                return {"error": "Failed to update task status"}
        else:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE business.tasks
                    SET status = $1, completed_at = $2, updated_at = NOW()
                    WHERE id = $3
                """,
                    args["status"],
                    completed_at,
                    args["task_id"],
                )

                if result == "UPDATE 1":
                    return {
                        "success": True,
                        "message": f"Task status updated to {args['status']}",
                    }
                else:
                    return {"success": False, "message": "Task not found"}

    async def _get_tasks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get tasks with filtering."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        if self.use_supabase and self.supabase_client:
            query = self.supabase_client.table("tasks").select("*")
            if "status" in args:
                query = query.eq("status", args["status"])
            if "assigned_agent_id" in args:
                query = query.eq("assigned_agent_id", args["assigned_agent_id"])
            if "created_by_agent_id" in args:
                query = query.eq("created_by_agent_id", args["created_by_agent_id"])
            if "priority" in args:
                query = query.eq("priority", args["priority"])
            result = query.execute()
            return {"success": True, "tasks": result.data, "count": len(result.data)}
        else:
            # Build query with filters
            where_conditions = []
            values = []
            param_count = 1

            for field in [
                "status",
                "assigned_agent_id",
                "created_by_agent_id",
                "priority",
            ]:
                if field in args:
                    where_conditions.append(f"{field} = ${param_count}")
                    values.append(args[field])
                    param_count += 1

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )
            limit = args.get("limit", 50)

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT * FROM business.tasks
                    {where_clause}
                    ORDER BY priority ASC, created_at DESC
                    LIMIT {limit}
                """,
                    *values,
                )

                return {
                    "success": True,
                    "tasks": [dict(row) for row in rows],
                    "count": len(rows),
                }

    async def _get_business_metrics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get business metrics."""
        if not self.db_pool and not self.supabase_client:
            return {"error": "Database not available"}

        # This is a simplified implementation
        # In production, this would calculate real metrics
        if self.use_supabase and self.supabase_client:
            result = (
                self.supabase_client.table("business_metrics").select("*").execute()
            )
            if result.data:
                return {"success": True, "metrics": result.data[0]}
            else:
                return {"success": False, "message": "No business metrics found"}
        else:
            async with self.db_pool.acquire() as conn:
                customer_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM business.customers"
                )
                lead_count = await conn.fetchval("SELECT COUNT(*) FROM business.leads")
                task_count = await conn.fetchval("SELECT COUNT(*) FROM business.tasks")
                completed_tasks = await conn.fetchval(
                    "SELECT COUNT(*) FROM business.tasks WHERE status = 'completed'"
                )

            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "customers": {
                    "total": customer_count,
                    "active": customer_count,  # Simplified
                },
                "leads": {"total": lead_count, "conversion_rate": 0.15},  # Mock data
                "tasks": {
                    "total": task_count,
                    "completed": completed_tasks,
                    "completion_rate": completed_tasks / task_count
                    if task_count > 0
                    else 0,
                },
            }

            return {"success": True, "metrics": metrics}

    # Resource readers
    async def _read_customers_resource(self) -> Dict[str, Any]:
        """Read customers resource."""
        return {
            "type": "text",
            "text": json.dumps(
                {
                    "resource": "customers",
                    "description": "Customer management system",
                    "available_tools": [
                        "create_customer",
                        "get_customer",
                        "update_customer",
                    ],
                },
                indent=2,
            ),
        }

    async def _read_leads_resource(self) -> Dict[str, Any]:
        """Read leads resource."""
        return {
            "type": "text",
            "text": json.dumps(
                {
                    "resource": "leads",
                    "description": "Lead tracking and scoring system",
                    "available_tools": [
                        "create_lead",
                        "update_lead_score",
                        "get_leads",
                    ],
                },
                indent=2,
            ),
        }

    async def _read_tasks_resource(self) -> Dict[str, Any]:
        """Read tasks resource."""
        return {
            "type": "text",
            "text": json.dumps(
                {
                    "resource": "tasks",
                    "description": "Task management system",
                    "available_tools": [
                        "create_task",
                        "update_task_status",
                        "get_tasks",
                    ],
                },
                indent=2,
            ),
        }

    async def _read_metrics_resource(self) -> Dict[str, Any]:
        """Read metrics resource."""
        return {
            "type": "text",
            "text": json.dumps(
                {
                    "resource": "metrics",
                    "description": "Business performance metrics",
                    "available_tools": ["get_business_metrics"],
                },
                indent=2,
            ),
        }
