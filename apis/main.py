"""
Main API Server for ELF Automations

This module provides the main REST API server for the Virtual AI Company Platform.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import structlog
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel
from starlette.responses import Response

from agents.base import AgentConfig, AgentType
from agents.executive.chief_ai_agent import ChiefAIAgent
from agents.registry import AgentRegistry
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
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "api_requests_total", "Total API requests", ["method", "endpoint"]
)
REQUEST_DURATION = Histogram("api_request_duration_seconds", "API request duration")
AGENT_OPERATIONS = Counter(
    "agent_operations_total", "Total agent operations", ["operation", "agent_type"]
)

# Global state
chief_agent: Optional[ChiefAIAgent] = None
business_tools_server: Optional[BusinessToolsServer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global chief_agent, business_tools_server

    logger.info("Starting ELF Automations API server")

    try:
        # Initialize Chief AI Agent
        chief_agent = ChiefAIAgent()
        await chief_agent.start()
        logger.info("Chief AI Agent started")

        # Initialize Business Tools MCP Server
        database_url = os.getenv("DATABASE_URL")
        business_tools_server = BusinessToolsServer(database_url)
        await business_tools_server.start()
        logger.info("Business Tools MCP Server started")

        # Start background tasks
        asyncio.create_task(chief_agent.start_performance_monitoring())

        yield

    except Exception as e:
        logger.error("Error during startup", error=str(e))
        raise
    finally:
        # Cleanup
        logger.info("Shutting down ELF Automations API server")

        if chief_agent:
            await chief_agent.stop()

        if business_tools_server:
            await business_tools_server.stop()

        await AgentRegistry.shutdown_all_agents()


# Create FastAPI app
app = FastAPI(
    title="ELF Automations API",
    description="Virtual AI Company Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class AgentCreateRequest(BaseModel):
    name: str
    agent_type: AgentType
    department: str
    config: Optional[AgentConfig] = None


class TaskCreateRequest(BaseModel):
    agent_id: str
    task_type: str
    description: Optional[str] = None
    context: Optional[Dict] = None


class MessageRequest(BaseModel):
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict
    priority: int = 3


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    REQUEST_COUNT.labels(method="GET", endpoint="/health").inc()

    return {"status": "healthy", "service": "elf-automations-api", "version": "0.1.0"}


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Agent management endpoints
@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    REQUEST_COUNT.labels(method="GET", endpoint="/agents").inc()

    agents = AgentRegistry.list_agents()
    return {"agents": agents, "count": len(agents)}


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent by ID."""
    REQUEST_COUNT.labels(method="GET", endpoint="/agents/{agent_id}").inc()

    agent = AgentRegistry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent.get_status()


@app.get("/agents/department/{department}")
async def get_agents_by_department(department: str):
    """Get agents by department."""
    REQUEST_COUNT.labels(method="GET", endpoint="/agents/department/{department}").inc()

    agents = AgentRegistry.get_agents_by_department(department)
    return {
        "department": department,
        "agents": [agent.get_status() for agent in agents],
        "count": len(agents),
    }


@app.get("/agents/type/{agent_type}")
async def get_agents_by_type(agent_type: AgentType):
    """Get agents by type."""
    REQUEST_COUNT.labels(method="GET", endpoint="/agents/type/{agent_type}").inc()

    agents = AgentRegistry.get_agents_by_type(agent_type)
    return {
        "agent_type": agent_type.value,
        "agents": [agent.get_status() for agent in agents],
        "count": len(agents),
    }


@app.post("/agents/{agent_id}/tasks")
async def create_task(agent_id: str, task_request: TaskCreateRequest):
    """Create a task for an agent."""
    REQUEST_COUNT.labels(method="POST", endpoint="/agents/{agent_id}/tasks").inc()
    AGENT_OPERATIONS.labels(operation="create_task", agent_type="unknown").inc()

    agent = AgentRegistry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    task = {
        "type": task_request.task_type,
        "description": task_request.description,
        "context": task_request.context or {},
    }

    try:
        result = await agent.execute_task(task)
        return {"task_id": task.get("id"), "agent_id": agent_id, "result": result}
    except Exception as e:
        logger.error("Task execution failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@app.post("/agents/{agent_id}/messages")
async def send_message(agent_id: str, message_request: MessageRequest):
    """Send a message to an agent."""
    REQUEST_COUNT.labels(method="POST", endpoint="/agents/{agent_id}/messages").inc()
    AGENT_OPERATIONS.labels(operation="send_message", agent_type="unknown").inc()

    from_agent = AgentRegistry.get_agent(message_request.from_agent)
    if not from_agent:
        raise HTTPException(status_code=404, detail="From agent not found")

    to_agent = AgentRegistry.get_agent(message_request.to_agent)
    if not to_agent:
        raise HTTPException(status_code=404, detail="To agent not found")

    try:
        message_id = await from_agent.send_message(
            to_agent=message_request.to_agent,
            message_type=message_request.message_type,
            content=message_request.content,
            priority=message_request.priority,
        )

        return {
            "message_id": message_id,
            "from_agent": message_request.from_agent,
            "to_agent": message_request.to_agent,
            "status": "sent",
        }
    except Exception as e:
        logger.error("Message sending failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Message sending failed: {str(e)}")


# Registry management endpoints
@app.get("/registry/stats")
async def get_registry_stats():
    """Get agent registry statistics."""
    REQUEST_COUNT.labels(method="GET", endpoint="/registry/stats").inc()

    return AgentRegistry.get_registry_stats()


@app.post("/registry/broadcast")
async def broadcast_message(
    message_type: str,
    content: Dict,
    sender_id: str,
    department: Optional[str] = None,
    agent_type: Optional[AgentType] = None,
):
    """Broadcast a message to multiple agents."""
    REQUEST_COUNT.labels(method="POST", endpoint="/registry/broadcast").inc()
    AGENT_OPERATIONS.labels(operation="broadcast_message", agent_type="all").inc()

    try:
        message_ids = await AgentRegistry.broadcast_message(
            message_type=message_type,
            content=content,
            sender_id=sender_id,
            department=department,
            agent_type=agent_type,
        )

        return {
            "message_type": message_type,
            "sender_id": sender_id,
            "message_ids": message_ids,
            "count": len(message_ids),
        }
    except Exception as e:
        logger.error("Broadcast failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")


# Chief AI Agent endpoints
@app.get("/chief")
async def get_chief_status():
    """Get Chief AI Agent status."""
    REQUEST_COUNT.labels(method="GET", endpoint="/chief").inc()

    if not chief_agent:
        raise HTTPException(status_code=503, detail="Chief AI Agent not available")

    return chief_agent.get_status()


@app.post("/chief/strategic-planning")
async def trigger_strategic_planning(
    context: Optional[Dict] = None, time_horizon: str = "quarterly"
):
    """Trigger strategic planning by the Chief AI Agent."""
    REQUEST_COUNT.labels(method="POST", endpoint="/chief/strategic-planning").inc()
    AGENT_OPERATIONS.labels(
        operation="strategic_planning", agent_type="executive"
    ).inc()

    if not chief_agent:
        raise HTTPException(status_code=503, detail="Chief AI Agent not available")

    task = {
        "type": "strategic_planning",
        "context": context or {},
        "time_horizon": time_horizon,
    }

    try:
        result = await chief_agent.execute_task(task)
        return result
    except Exception as e:
        logger.error("Strategic planning failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Strategic planning failed: {str(e)}"
        )


@app.post("/chief/performance-review")
async def trigger_performance_review():
    """Trigger performance review by the Chief AI Agent."""
    REQUEST_COUNT.labels(method="POST", endpoint="/chief/performance-review").inc()
    AGENT_OPERATIONS.labels(
        operation="performance_review", agent_type="executive"
    ).inc()

    if not chief_agent:
        raise HTTPException(status_code=503, detail="Chief AI Agent not available")

    task = {"type": "performance_review", "context": {"manual_trigger": True}}

    try:
        result = await chief_agent.execute_task(task)
        return result
    except Exception as e:
        logger.error("Performance review failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Performance review failed: {str(e)}"
        )


# MCP Server endpoints
@app.get("/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools."""
    REQUEST_COUNT.labels(method="GET", endpoint="/mcp/tools").inc()

    if not business_tools_server:
        raise HTTPException(
            status_code=503, detail="Business Tools MCP Server not available"
        )

    tools = business_tools_server.get_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in tools
        ],
        "count": len(tools),
    }


@app.post("/mcp/tools/{tool_name}")
async def call_mcp_tool(tool_name: str, arguments: Dict):
    """Call an MCP tool."""
    REQUEST_COUNT.labels(method="POST", endpoint="/mcp/tools/{tool_name}").inc()

    if not business_tools_server:
        raise HTTPException(
            status_code=503, detail="Business Tools MCP Server not available"
        )

    try:
        result = await business_tools_server.call_tool(tool_name, arguments)
        return result
    except Exception as e:
        logger.error("MCP tool call failed", tool_name=tool_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Tool call failed: {str(e)}")


@app.get("/mcp/resources")
async def list_mcp_resources():
    """List available MCP resources."""
    REQUEST_COUNT.labels(method="GET", endpoint="/mcp/resources").inc()

    if not business_tools_server:
        raise HTTPException(
            status_code=503, detail="Business Tools MCP Server not available"
        )

    resources = business_tools_server.get_resources()
    return {
        "resources": [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mime_type,
            }
            for resource in resources
        ],
        "count": len(resources),
    }


def main():
    """Main function for running the API server."""
    import os

    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")

    # Run the server
    uvicorn.run(
        "apis.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False,  # Set to True for development
    )


if __name__ == "__main__":
    main()
