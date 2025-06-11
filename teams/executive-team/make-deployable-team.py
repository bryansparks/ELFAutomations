#!/usr/bin/env python3
"""
Make Deployable Team Script
Creates a containerized version of the team that can run as a single K8s pod

This script:
1. Creates a team_server.py that wraps the crew with A2A protocol
2. Generates a Dockerfile for containerization
3. Creates requirements.txt with all dependencies
4. Prepares the team for GitOps deployment
"""

import os
import shutil
from pathlib import Path


def create_deployable_team():
    """Create a deployable version of the team"""
    team_dir = Path(__file__).parent

    print("🚀 Creating deployable team package...")

    # Create team_server.py - the main entry point
    create_team_server(team_dir)

    # Create Dockerfile
    create_dockerfile(team_dir)

    # Create requirements.txt
    create_requirements(team_dir)

    # Create a simple health check endpoint
    create_health_check(team_dir)

    print("✅ Team is ready for containerization!")
    print("📦 Next steps:")
    print("   1. Build: docker build -t elf-automations/executive-team .")
    print("   2. Push to registry accessible by your K8s cluster")
    print("   3. Update k8s/deployment.yaml with correct image")
    print("   4. Commit to GitOps repo for ArgoCD")


def create_team_server(team_dir: Path):
    """Create the main server that runs the team"""
    server_content = """#!/usr/bin/env python3
\"\"\"
Team Server - Runs the CrewAI team with A2A protocol endpoint
\"\"\"

import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any

# Import the team
from crew import ExecutiveTeamCrew

# Import A2A server components
from agents.distributed.a2a.server import A2AServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="executive-team API")

# Initialize the crew
crew_instance = None

@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize the crew on startup\"\"\"
    global crew_instance
    logger.info("Initializing executive-team...")
    crew_instance = ExecutiveTeamCrew()
    logger.info("Team initialized successfully")

@app.get("/health")
async def health_check():
    \"\"\"Health check endpoint\"\"\"
    return {"status": "healthy", "team": "executive-team"}

@app.get("/capabilities")
async def get_capabilities():
    \"\"\"Get team capabilities\"\"\"
    if not crew_instance:
        raise HTTPException(status_code=503, detail="Team not initialized")

    return crew_instance.get_team_status()

@app.post("/task")
async def execute_task(request: Dict[str, Any]):
    \"\"\"Execute a task with the team via A2A protocol\"\"\"
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
"""

    server_file = team_dir / "team_server.py"
    with open(server_file, "w") as f:
        f.write(server_content)
    os.chmod(server_file, 0o755)


def create_dockerfile(team_dir: Path):
    """Create Dockerfile for the team"""
    dockerfile_content = """FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy team files
COPY . .

# Create logs directory
RUN mkdir -p /logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8090

# Expose port
EXPOSE 8090

# Run the server
CMD ["python", "team_server.py"]
"""

    dockerfile = team_dir / "Dockerfile"
    with open(dockerfile, "w") as f:
        f.write(dockerfile_content)


def create_requirements(team_dir: Path):
    """Create requirements.txt with all dependencies"""
    requirements_content = """# Core dependencies
crewai>=0.70.0
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0

# Server dependencies
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# A2A dependencies
redis>=5.0.0
aioredis>=2.0.0

# Utilities
python-dotenv>=1.0.0
PyYAML>=6.0
"""

    requirements_file = team_dir / "requirements.txt"
    with open(requirements_file, "w") as f:
        f.write(requirements_content)


def create_health_check(team_dir: Path):
    """Create a simple health check script"""
    health_check_content = """#!/bin/bash
# Simple health check for K8s
curl -f http://localhost:8090/health || exit 1
"""

    health_check = team_dir / "health_check.sh"
    with open(health_check, "w") as f:
        f.write(health_check_content)
    os.chmod(health_check, 0o755)


if __name__ == "__main__":
    create_deployable_team()
