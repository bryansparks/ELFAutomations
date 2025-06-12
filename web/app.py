#!/usr/bin/env python3
"""
Virtual AI Company Platform - Web Dashboard

A Flask-based web interface to monitor and interact with the Virtual AI Company Platform.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import structlog
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Import our components
sys.path.append(str(Path(__file__).parent.parent))

from agents.executive.chief_ai_agent import ChiefAIAgent
from mcp_servers.business_tools import BusinessToolsServer

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "flask_requests_total", "Total Flask requests", ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram("flask_request_duration_seconds", "Flask request duration")
ACTIVE_CONNECTIONS = Gauge("flask_active_connections", "Active Flask connections")
BUSINESS_METRICS = Gauge(
    "business_metrics", "Business metrics from Supabase", ["metric_type"]
)
AGENT_TASK_COUNT = Counter(
    "agent_tasks_total", "Total agent tasks submitted", ["task_type", "status"]
)
AGENT_TASK_DURATION = Histogram(
    "agent_task_duration_seconds", "Agent task execution duration"
)

# Load environment
load_dotenv(Path(__file__).parent.parent / ".env")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Global business tools instance
business_tools = None


@app.before_request
def before_request():
    request.start_time = time.time()
    ACTIVE_CONNECTIONS.inc()


@app.after_request
def after_request(response):
    ACTIVE_CONNECTIONS.dec()

    # Record request metrics
    duration = time.time() - request.start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or "unknown",
        status=response.status_code,
    ).inc()

    return response


@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


async def get_business_tools():
    """Get or initialize business tools."""
    global business_tools
    if business_tools is None:
        business_tools = BusinessToolsServer()
        await business_tools.start()
    return business_tools


@app.route("/")
def dashboard():
    """Main dashboard page."""
    return render_template("dashboard.html")


@app.route("/api/status")
def api_status():
    """Get system status."""
    try:
        # Check Supabase connection
        supabase_status = {
            "url": os.getenv("SUPABASE_URL", "Not configured"),
            "connected": bool(
                os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY")
            ),
            "project_id": os.getenv("SUPABASE_PROJECT_ID", "Not configured"),
        }

        # Check environment
        env_status = {
            "supabase_configured": bool(os.getenv("SUPABASE_URL")),
            "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        }

        return jsonify(
            {
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "supabase": supabase_status,
                "environment": env_status,
                "services": {
                    "business_tools": "operational",
                    "ai_agents": "operational",
                    "database": "operational",
                },
            }
        )
    except Exception as e:
        logger.error("Status check failed", error=str(e))
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/metrics")
def api_metrics():
    """Get business metrics from database."""

    async def _get_metrics():
        try:
            tools = await get_business_tools()

            if not tools.supabase_client:
                return {"error": "Supabase not connected"}

            # Get counts from each table
            customers_result = (
                tools.supabase_client.table("customers")
                .select("*", count="exact")
                .execute()
            )
            leads_result = (
                tools.supabase_client.table("leads")
                .select("*", count="exact")
                .execute()
            )
            tasks_result = (
                tools.supabase_client.table("tasks")
                .select("*", count="exact")
                .execute()
            )
            business_metrics_result = (
                tools.supabase_client.table("business_metrics")
                .select("*", count="exact")
                .execute()
            )
            agent_activities_result = (
                tools.supabase_client.table("agent_activities")
                .select("*", count="exact")
                .execute()
            )

            # Get lead quality metrics
            high_quality_leads = (
                tools.supabase_client.table("leads")
                .select("*", count="exact")
                .gte("score", 80)
                .execute()
            )
            all_leads = tools.supabase_client.table("leads").select("score").execute()

            # Calculate average lead score
            lead_scores = [
                lead["score"] for lead in all_leads.data if lead["score"] is not None
            ]
            avg_lead_score = sum(lead_scores) / len(lead_scores) if lead_scores else 0

            # Get task completion metrics
            completed_tasks = (
                tools.supabase_client.table("tasks")
                .select("*", count="exact")
                .eq("status", "completed")
                .execute()
            )
            pending_tasks = (
                tools.supabase_client.table("tasks")
                .select("*", count="exact")
                .eq("status", "pending")
                .execute()
            )

            total_tasks = tasks_result.count
            completed_count = completed_tasks.count
            completion_rate = (
                (completed_count / total_tasks * 100) if total_tasks > 0 else 0
            )

            metrics = {
                "customers_count": customers_result.count,
                "leads_count": leads_result.count,
                "tasks_count": total_tasks,
                "business_metrics_count": business_metrics_result.count,
                "agent_activities_count": agent_activities_result.count,
                "high_quality_leads": high_quality_leads.count,
                "average_lead_score": avg_lead_score,
                "lead_quality_rate": (
                    high_quality_leads.count / leads_result.count * 100
                )
                if leads_result.count > 0
                else 0,
                "completed_tasks": completed_count,
                "pending_tasks": pending_tasks.count,
                "task_completion_rate": completion_rate,
            }

            # Update Prometheus business metrics
            BUSINESS_METRICS.labels(metric_type="customers").set(customers_result.count)
            BUSINESS_METRICS.labels(metric_type="leads").set(leads_result.count)
            BUSINESS_METRICS.labels(metric_type="high_quality_leads").set(
                high_quality_leads.count
            )
            BUSINESS_METRICS.labels(metric_type="tasks_total").set(total_tasks)
            BUSINESS_METRICS.labels(metric_type="tasks_completed").set(completed_count)
            BUSINESS_METRICS.labels(metric_type="task_completion_rate").set(
                completion_rate
            )
            BUSINESS_METRICS.labels(metric_type="average_lead_score").set(
                avg_lead_score
            )

            return metrics

        except Exception as e:
            logger.error("Failed to fetch metrics", error=str(e))
            return {"error": str(e)}

    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_get_metrics())
        return jsonify(result)
    finally:
        loop.close()


@app.route("/api/agents")
def api_agents():
    """Get agent information."""
    agents = [
        {
            "id": "chief-ai-agent",
            "name": "Chief AI Agent",
            "type": "executive",
            "department": "executive",
            "status": "active",
            "last_activity": datetime.now().isoformat(),
        }
    ]

    return jsonify({"agents": agents})


@app.route("/api/agents/analyze", methods=["POST"])
def api_agent_analyze():
    """Request AI agent analysis."""

    async def _run_analysis():
        try:
            data = request.get_json()
            prompt = data.get("prompt", "Provide a business status analysis.")

            # Initialize Chief AI Agent
            chief_agent = ChiefAIAgent()

            # Run analysis
            result = await chief_agent.think(prompt)

            return {
                "analysis": result,
                "timestamp": datetime.now().isoformat(),
                "agent": "chief-ai-agent",
            }

        except Exception as e:
            logger.error("Agent analysis failed", error=str(e))
            return {"error": str(e)}

    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run_analysis())
        return jsonify(result)
    finally:
        loop.close()


@app.route("/api/agent/task", methods=["POST"])
def api_agent_task():
    """Submit a task to the Chief AI Agent."""
    start_time = time.time()
    task_type = "unknown"
    status = "failed"

    try:
        # Get task data from request
        data = request.get_json()
        if not data:
            AGENT_TASK_COUNT.labels(task_type="unknown", status="failed").inc()
            return jsonify({"error": "No JSON data provided"}), 400

        description = data.get("description", "").strip()
        task_type = data.get("type", "general_executive")
        priority = data.get("priority", "medium")

        if not description:
            AGENT_TASK_COUNT.labels(task_type=task_type, status="failed").inc()
            return jsonify({"error": "Task description is required"}), 400

        logger.info("Received agent task", task_type=task_type, priority=priority)

        # Create task object
        task = {
            "description": description,
            "type": task_type,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        }

        # Execute task using Chief AI Agent
        async def _execute_task():
            try:
                # Initialize agent if needed
                if not hasattr(api_agent_task, "_agent"):
                    from agents.executive.chief_ai_agent import ChiefAIAgent

                    api_agent_task._agent = ChiefAIAgent()

                # Execute the task
                result = await api_agent_task._agent._execute_task_impl(task)
                return result

            except Exception as e:
                logger.error("Task execution failed", error=str(e), task_type=task_type)
                raise e

        # Run the async task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_execute_task())
            status = "success"

            # Record successful task metrics
            duration = time.time() - start_time
            AGENT_TASK_COUNT.labels(task_type=task_type, status="success").inc()
            AGENT_TASK_DURATION.observe(duration)

            logger.info(
                "Task completed successfully", task_type=task_type, duration=duration
            )

            return jsonify(
                {
                    "status": "success",
                    "task": task,
                    "result": result,
                    "execution_time": duration,
                }
            )

        except Exception as e:
            status = "failed"
            duration = time.time() - start_time
            AGENT_TASK_COUNT.labels(task_type=task_type, status="failed").inc()
            AGENT_TASK_DURATION.observe(duration)

            logger.error(
                "Task execution failed",
                error=str(e),
                task_type=task_type,
                duration=duration,
            )
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": str(e),
                        "task": task,
                        "execution_time": duration,
                    }
                ),
                500,
            )
        finally:
            loop.close()

    except Exception as e:
        duration = time.time() - start_time
        AGENT_TASK_COUNT.labels(task_type=task_type, status="failed").inc()
        AGENT_TASK_DURATION.observe(duration)

        logger.error("Request processing failed", error=str(e))
        return (
            jsonify({"status": "error", "error": str(e), "execution_time": duration}),
            500,
        )


@app.route("/api/database/tables")
def api_database_tables():
    """Get database table information."""

    async def _get_tables():
        try:
            tools = await get_business_tools()

            if not tools.supabase_client:
                return {"error": "Supabase not connected"}

            tables_info = []
            tables = [
                "customers",
                "leads",
                "tasks",
                "business_metrics",
                "agent_activities",
            ]

            for table in tables:
                try:
                    # Get count
                    count_result = (
                        tools.supabase_client.table(table)
                        .select("id", count="exact")
                        .execute()
                    )
                    count = count_result.count if count_result.count is not None else 0

                    # Get sample data
                    sample_result = (
                        tools.supabase_client.table(table)
                        .select("*")
                        .limit(3)
                        .execute()
                    )
                    sample_data = sample_result.data if sample_result.data else []

                    tables_info.append(
                        {"name": table, "count": count, "sample_data": sample_data}
                    )

                except Exception as e:
                    logger.warning(
                        f"Failed to get info for table {table}", error=str(e)
                    )
                    tables_info.append(
                        {"name": table, "count": 0, "sample_data": [], "error": str(e)}
                    )

            return {"tables": tables_info}

        except Exception as e:
            logger.error("Database tables query failed", error=str(e))
            return {"error": str(e)}

    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_get_tables())
        return jsonify(result)
    finally:
        loop.close()


if __name__ == "__main__":
    logger.info("Starting Virtual AI Company Platform Dashboard")
    logger.info(f"Supabase URL: {os.getenv('SUPABASE_URL', 'Not configured')}")

    # Run Flask app
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        debug=os.getenv("FLASK_DEBUG", "False").lower() == "true",
    )
