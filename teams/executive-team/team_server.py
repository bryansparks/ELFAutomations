#!/usr/bin/env python3
"""
Team Server - Runs the CrewAI team with A2A protocol endpoint
"""

import asyncio
import logging
import os
from typing import Any, Dict

import uvicorn

# Import the team
from crew import ExecutiveTeamCrew
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Import A2A server components
from agents.distributed.a2a.server import A2AServer

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="executive-team API")

# Initialize the crew
crew_instance = None


@app.on_event("startup")
async def startup_event():
    """Initialize the crew on startup"""
    global crew_instance
    logger.info("Initializing executive-team...")
    crew_instance = ExecutiveTeamCrew()
    logger.info("Team initialized successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "team": "executive-team"}


@app.get("/capabilities")
async def get_capabilities():
    """Get team capabilities"""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Team not initialized")

    return crew_instance.get_team_status()


@app.post("/task")
async def execute_task(request: Dict[str, Any]):
    """Execute a task with the team via A2A protocol"""
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Team not initialized")

    try:
        task_description = request.get("description", "")
        context = request.get("context", {})

        # Execute the task
        result = crew_instance.execute_task(task_description, context)

        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the server
    port = int(os.getenv("PORT", "8090"))
    uvicorn.run(app, host="0.0.0.0", port=port)
