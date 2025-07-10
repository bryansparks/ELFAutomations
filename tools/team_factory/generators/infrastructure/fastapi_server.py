"""
FastAPI server generator for team A2A endpoints.
"""

from pathlib import Path
from typing import Any, Dict

from ...models import TeamSpecification
from ..base import BaseGenerator


class FastAPIServerGenerator(BaseGenerator):
    """Generates FastAPI server wrapper for teams."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate FastAPI server.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        team_dir = Path(team_spec.name)
        server_path = team_dir / "team_server.py"

        # Generate server content
        server_content = self._generate_server_content(team_spec)

        # Write file
        with open(server_path, "w") as f:
            f.write(server_content)

        return {"generated_files": [str(server_path)], "errors": []}

    def _generate_server_content(self, team_spec: TeamSpecification) -> str:
        """Generate team server content."""
        orchestrator_import = (
            "from crew import get_orchestrator"
            if team_spec.framework == "CrewAI"
            else "from workflows.team_workflow import get_workflow"
        )
        orchestrator_var = (
            "orchestrator" if team_spec.framework == "CrewAI" else "workflow"
        )

        # Add chat imports if enabled
        chat_imports = ""
        if team_spec.enable_chat_interface:
            chat_imports = """
from fastapi import WebSocket, WebSocketDisconnect
from elf_automations.shared.auth.jwt_handler import require_websocket_auth, get_jwt_handler
from elf_automations.shared.chat import ConversationManager
import json"""

        # Generate chat endpoint if enabled
        chat_endpoint = ""
        chat_initialization = ""

        if team_spec.enable_chat_interface:
            manager_member = team_spec.manager
            manager_name = manager_member.name if manager_member else "Manager"
            manager_role = manager_member.role if manager_member else "Team Manager"

            chat_initialization = f"""
# Initialize conversation manager for chat interface
conversation_manager = None
jwt_handler = None

@app.on_event("startup")
async def startup_event():
    global conversation_manager, jwt_handler

    # Initialize JWT handler
    jwt_handler = get_jwt_handler()

    # Initialize conversation manager
    if {orchestrator_var}:
        manager_agent = {orchestrator_var}.manager if hasattr({orchestrator_var}, 'manager') else None
        conversation_manager = ConversationManager(
            team_agent=manager_agent,
            team_name="{team_spec.name}",
            manager_name="{manager_name}",
            manager_role="{manager_role}",
            chat_config={repr(team_spec.chat_config)}
        )
        logger.info("Chat interface initialized")
"""

            chat_endpoint = f"""
@app.websocket("/chat")
@require_websocket_auth(jwt_handler)
async def chat_endpoint(websocket: WebSocket):
    \"\"\"WebSocket endpoint for team chat interface.\"\"\"
    await websocket.accept()

    # Get user info from JWT
    user_id = websocket.state.user_id
    team_id = websocket.state.team_id
    session_id = websocket.state.session_id or None

    # Verify team access
    if team_id != "{team_spec.name}":
        await websocket.close(code=1008, reason="Invalid team access")
        return

    # Start or resume session
    if not session_id:
        session_id, greeting = await conversation_manager.start_session(
            user_id=user_id,
            initial_context={{"source": "websocket", "team_id": team_id}}
        )

        # Send greeting
        await websocket.send_json({{
            "type": "greeting",
            "session_id": session_id,
            "message": greeting,
            "manager": "{manager_name}",
            "team": "{team_spec.name}"
        }})

    try:
        while True:
            # Receive message from user
            data = await websocket.receive_json()

            if data.get("type") == "end_session":
                # End the session
                summary = await conversation_manager.end_session(
                    session_id,
                    reason="user_ended"
                )
                await websocket.send_json({{
                    "type": "session_ended",
                    "summary": summary
                }})
                break

            # Process chat message
            user_message = data.get("message", "")
            if not user_message:
                continue

            # Send thinking indicator
            await websocket.send_json({{
                "type": "status",
                "status": "thinking"
            }})

            # Process with conversation manager
            response = await conversation_manager.process_message(
                session_id=session_id,
                user_message=user_message,
                context=data.get("context", {{}})
            )

            # Send response
            await websocket.send_json({{
                "type": "message",
                "content": response["response"],
                "thinking_time": response["thinking_time"],
                "ready_to_delegate": response["ready_to_delegate"],
                "metadata": {{
                    "message_count": response["message_count"],
                    "total_tokens": response["total_tokens"]
                }}
            }})

            # If ready to delegate, send delegation preview
            if response["ready_to_delegate"]:
                delegation_spec = conversation_manager.prepare_delegation(session_id)
                if delegation_spec:
                    await websocket.send_json({{
                        "type": "delegation_preview",
                        "delegation": delegation_spec,
                        "requires_confirmation": True
                    }})

    except WebSocketDisconnect:
        logger.info(f"Chat session disconnected for user {{user_id}}")
        # Clean up session
        await conversation_manager.end_session(session_id, reason="disconnected")
    except Exception as e:
        logger.error(f"Chat error: {{str(e)}}")
        await websocket.close(code=1011, reason="Internal error")


@app.post("/chat/delegation/confirm")
async def confirm_delegation(
    session_id: str,
    confirmed: bool,
    modifications: Optional[Dict[str, Any]] = None
):
    \"\"\"Confirm or reject a delegation after chat session.\"\"\"
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Chat interface not initialized")

    if not confirmed:
        return {{"status": "delegation_cancelled"}}

    # Get delegation spec
    delegation_spec = conversation_manager.prepare_delegation(session_id)
    if not delegation_spec:
        raise HTTPException(status_code=404, detail="No delegation found for session")

    # Apply modifications if any
    if modifications:
        delegation_spec.update(modifications)

    # Create A2A task from delegation
    # This would integrate with your existing task execution
    task_request = TaskRequestModel(
        from_agent="chat_interface",
        to_agent="{manager_name}",
        task_type="delegated_from_chat",
        task_description=delegation_spec.get("description", ""),
        context=delegation_spec
    )

    # Execute through normal task flow
    response = await execute_task(task_request)

    # End chat session
    await conversation_manager.end_session(session_id, reason="delegation_complete")

    return {{
        "status": "delegation_confirmed",
        "task_id": response.get("task_id"),
        "delegation": delegation_spec
    }}
"""

        return f'''#!/usr/bin/env python3
"""
Team Server - Runs the {team_spec.framework} team with A2A protocol endpoint
Generated by Team Factory
"""

import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import uvicorn

# Team imports
{orchestrator_import}
from agents.distributed.a2a.server import A2AServer
from agents.distributed.a2a.messages import TaskRequest, TaskResponse{chat_imports}


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="{team_spec.name} Team API",
    description="A2A-enabled {team_spec.framework} team for {team_spec.purpose}",
    version="1.0.0"
)

# Initialize team orchestrator
{orchestrator_var} = None
a2a_server = None{chat_initialization}


class TaskRequestModel(BaseModel):
    """Model for incoming task requests"""
    from_agent: str
    to_agent: str
    task_type: str
    task_description: str
    context: Dict[str, Any] = {{}}
    timeout: int = 3600  # Default 1 hour


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    team_name: str = "{team_spec.name}"
    framework: str = "{team_spec.framework}"
    department: str = "{team_spec.department}"
    timestamp: str
    agents: List[str] = {[m.role for m in team_spec.members]}


@app.on_event("startup")
async def startup_event():
    """Initialize team on startup"""
    global {orchestrator_var}, a2a_server

    logger.info("Starting {team_spec.name} team server...")

    # Initialize orchestrator
    {orchestrator_var} = get_{orchestrator_var}()
    logger.info("Team orchestrator initialized")

    # Initialize A2A server
    a2a_server = A2AServer(
        agent_id="{team_spec.name}-manager",
        capabilities=[
            "{team_spec.purpose}",
            "Task execution",
            "Status reporting",
            "Team coordination"
        ]
    )
    await a2a_server.start()
    logger.info("A2A server initialized")

    logger.info("{team_spec.name} team server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global a2a_server

    logger.info("Shutting down {team_spec.name} team server...")

    if a2a_server:
        await a2a_server.stop()

    logger.info("Shutdown complete")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/task")
async def handle_task(request: TaskRequestModel):
    """Handle incoming A2A task requests"""
    logger.info(f"Received task from {{request.from_agent}}: {{request.task_description[:100]}}...")

    try:
        # Create task request
        task_request = TaskRequest(
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            task_type=request.task_type,
            task_description=request.task_description,
            context=request.context,
            timeout=request.timeout
        )

        # Execute task using orchestrator
        if "{team_spec.framework}" == "CrewAI":
            result = {orchestrator_var}.run(
                task_description=request.task_description,
                context=request.context
            )
        else:
            # LangGraph async execution
            result = await {orchestrator_var}.run(
                objective=request.task_description,
                context=request.context
            )

        # Create response
        response = TaskResponse(
            request_id=task_request.request_id,
            from_agent=request.to_agent,
            to_agent=request.from_agent,
            status="completed",
            result=str(result),
            context={{
                "execution_time": datetime.utcnow().isoformat(),
                "team_name": "{team_spec.name}"
            }}
        )

        logger.info(f"Task completed successfully for {{request.from_agent}}")
        return response.dict()

    except Exception as e:
        logger.error(f"Error executing task: {{str(e)}}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/capabilities")
async def get_capabilities():
    """Return team capabilities"""
    return {{
        "team_name": "{team_spec.name}",
        "department": "{team_spec.department}",
        "framework": "{team_spec.framework}",
        "purpose": "{team_spec.purpose}",
        "agents": [
            {{
                "role": agent,
                "is_manager": agent == "{next((m.role for m in team_spec.members if m.is_manager), 'Manager')}"
            }}
            for agent in {[m.role for m in team_spec.members]}
        ],
        "capabilities": [
            "{team_spec.purpose}",
            "Task execution via {team_spec.framework}",
            "A2A protocol support",
            "Status reporting",
            "Health monitoring"{f',\n            "Chat interface for interactive task delegation"' if team_spec.enable_chat_interface else ''}
        ]
    }}


@app.get("/status")
async def get_status():
    """Get current team status"""
    return {{
        "status": "operational",
        "team_name": "{team_spec.name}",
        "active_tasks": 0,  # Would track actual tasks in production
        "last_activity": datetime.utcnow().isoformat(),
        "agents_status": {{
            agent: "ready" for agent in {[m.role for m in team_spec.members]}
        }}
    }}
{chat_endpoint}

if __name__ == "__main__":
    # Run the server
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting server on {{host}}:{{port}}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
'''
