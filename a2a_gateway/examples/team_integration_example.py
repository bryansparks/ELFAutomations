#!/usr/bin/env python3
"""
Example: How to integrate A2A Gateway with existing teams

This shows how to update a team's server to:
1. Register with the gateway on startup
2. Use gateway for inter-team communication
3. Unregister on shutdown
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import gateway client
from a2a_gateway.src.gateway_client import TeamAutoRegistration, GatewayClient

# Import A2A client with gateway support
from elf_automations.shared.a2a.client import A2AClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Team configuration
TEAM_CONFIG = {
    "team_id": "example-sales-team",
    "team_name": "Example Sales Team",
    "team_port": 8090,
    "capabilities": [
        "sales",
        "customer-engagement",
        "proposal-generation",
        "lead-qualification"
    ],
    "department": "sales"
}

# Global instances
auto_registration = None
a2a_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global auto_registration, a2a_client
    
    # Startup
    logger.info(f"Starting {TEAM_CONFIG['team_name']}...")
    
    # Initialize auto-registration
    auto_registration = TeamAutoRegistration(**TEAM_CONFIG)
    
    # Register with gateway
    registration_result = await auto_registration.register()
    if registration_result:
        logger.info(f"Successfully registered with A2A Gateway: {registration_result}")
    else:
        logger.warning("Failed to register with A2A Gateway - continuing without gateway")
    
    # Initialize A2A client with gateway support
    a2a_client = A2AClient(
        team_id=TEAM_CONFIG["team_id"],
        team_endpoint=f"http://localhost:{TEAM_CONFIG['team_port']}",
        use_gateway=True  # Enable gateway routing
    )
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {TEAM_CONFIG['team_name']}...")
    
    # Unregister from gateway
    if auto_registration:
        await auto_registration.unregister()
    
    # Close A2A client
    if a2a_client:
        await a2a_client.close()


# Create FastAPI app with lifespan
app = FastAPI(
    title=f"{TEAM_CONFIG['team_name']} API",
    description="Example team with A2A Gateway integration",
    version="1.0.0",
    lifespan=lifespan
)


class TaskRequest(BaseModel):
    """Incoming task request model"""
    from_agent: str
    to_agent: str
    task_type: str
    task_description: str
    context: Dict[str, Any] = {}
    timeout: int = 3600


class InterTeamRequest(BaseModel):
    """Request to send task to another team"""
    target_team: str = None
    task_description: str
    required_capabilities: list[str] = None
    context: Dict[str, Any] = {}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "team_name": TEAM_CONFIG["team_name"],
        "team_id": TEAM_CONFIG["team_id"],
        "gateway_enabled": a2a_client.use_gateway if a2a_client else False
    }


@app.post("/task")
async def handle_task(request: TaskRequest):
    """Handle incoming A2A task requests"""
    logger.info(f"Received task from {request.from_agent}: {request.task_description[:100]}...")
    
    try:
        # Simulate task processing
        result = f"Task completed by {TEAM_CONFIG['team_name']}: {request.task_description}"
        
        # Example: If task requires collaboration, use gateway to find help
        if "collaborate" in request.task_description.lower():
            # Use gateway to find a marketing team
            marketing_result = await a2a_client.send_task(
                target_team=None,  # Let gateway decide
                task_description="Create marketing content for this sales proposal",
                required_capabilities=["marketing", "content-creation"],
                context={"original_task": request.task_description}
            )
            
            result += f"\nCollaboration result: {marketing_result}"
        
        return {
            "status": "completed",
            "result": result,
            "team": TEAM_CONFIG["team_id"]
        }
        
    except Exception as e:
        logger.error(f"Error executing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/capabilities")
async def get_capabilities():
    """Return team capabilities"""
    return {
        "team_name": TEAM_CONFIG["team_name"],
        "team_id": TEAM_CONFIG["team_id"],
        "department": TEAM_CONFIG["department"],
        "capabilities": TEAM_CONFIG["capabilities"],
        "gateway_enabled": a2a_client.use_gateway if a2a_client else False
    }


@app.post("/collaborate")
async def collaborate_with_team(request: InterTeamRequest):
    """
    Example endpoint showing how to use gateway for inter-team collaboration
    """
    if not a2a_client:
        raise HTTPException(status_code=503, detail="A2A client not initialized")
    
    logger.info(f"Initiating collaboration: {request.task_description[:100]}...")
    
    try:
        # Use gateway to route task
        result = await a2a_client.send_task(
            target_team=request.target_team,
            task_description=request.task_description,
            required_capabilities=request.required_capabilities,
            context=request.context
        )
        
        return {
            "status": "success",
            "routed_to": result.get("routed_to", "unknown"),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Collaboration failed: {str(e)}")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/discover/{capability}")
async def discover_teams_by_capability(capability: str):
    """
    Discover other teams with specific capability
    """
    if not a2a_client:
        raise HTTPException(status_code=503, detail="A2A client not initialized")
    
    teams = await a2a_client.discover_teams(capability=capability)
    
    return {
        "capability": capability,
        "teams": teams,
        "count": len(teams)
    }


@app.get("/status")
async def get_status():
    """Get current team status"""
    # Could query gateway for our own status
    return {
        "status": "operational",
        "team_name": TEAM_CONFIG["team_name"],
        "team_id": TEAM_CONFIG["team_id"],
        "gateway_registered": auto_registration is not None,
        "active_tasks": 0,  # Would track in production
        "capabilities": TEAM_CONFIG["capabilities"]
    }


if __name__ == "__main__":
    # Run the server
    port = TEAM_CONFIG["team_port"]
    host = "0.0.0.0"
    
    logger.info(f"Starting {TEAM_CONFIG['team_name']} server on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")