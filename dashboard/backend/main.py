"""
ELF Automations Central Dashboard Backend

This FastAPI service aggregates data from all ELF systems and provides
a unified API for the dashboard frontend.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import Client, create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from elf_automations.shared.credentials import CredentialManager
from elf_automations.shared.infrastructure import HealthChecker
from elf_automations.shared.mcp import MCPDiscovery
from elf_automations.shared.monitoring import CostMonitor
from elf_automations.shared.n8n import N8NClient

# Import ELF modules
from elf_automations.shared.quota import QuotaManager


# Models
class TeamCreateRequest(BaseModel):
    name: str
    description: str
    framework: str = "CrewAI"
    llm_provider: str = "OpenAI"
    llm_model: str = "gpt-4"
    placement: str = ""


class WorkflowCreateRequest(BaseModel):
    name: str
    description: str
    owner_team: str
    category: str = "automation"


class DashboardStats(BaseModel):
    total_teams: int
    active_teams: int
    total_workflows: int
    workflows_today: int
    total_cost_today: float
    api_calls_today: int
    system_health: str
    active_mcps: int


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            for connection in self.active_connections.copy():
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")
                    self.active_connections.remove(connection)


# Dashboard service
class DashboardService:
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not configured")

        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Initialize other managers
        self.quota_manager = QuotaManager()
        self.cost_monitor = CostMonitor()
        self.health_checker = HealthChecker()
        self.n8n_client = None  # Initialized in lifespan
        self.mcp_discovery = MCPDiscovery()
        self.credential_manager = CredentialManager()

    async def get_dashboard_stats(self) -> DashboardStats:
        """Get overview statistics for dashboard"""
        try:
            # Get team stats
            teams_response = self.supabase.table("teams").select("*").execute()
            total_teams = len(teams_response.data)
            active_teams = len(
                [t for t in teams_response.data if t["status"] == "active"]
            )

            # Get workflow stats
            workflows_response = (
                self.supabase.table("n8n_workflows").select("*").execute()
            )
            total_workflows = len(workflows_response.data)

            # Get today's workflow executions
            today = datetime.now().strftime("%Y-%m-%d")
            today_executions = (
                self.supabase.table("workflow_executions")
                .select("*")
                .gte("started_at", f"{today}T00:00:00")
                .execute()
            )
            workflows_today = len(today_executions.data)

            # Get cost data
            cost_metrics = await self.cost_monitor.get_daily_cost(today)
            total_cost_today = cost_metrics.get("total_cost", 0.0)
            api_calls_today = cost_metrics.get("total_requests", 0)

            # Get system health
            health_results = await self.health_checker.check_all()
            system_health = (
                "healthy"
                if all(r.is_healthy for r in health_results.values())
                else "degraded"
            )

            # Get active MCPs
            mcps = await self.mcp_discovery.discover_all()
            active_mcps = len(mcps)

            return DashboardStats(
                total_teams=total_teams,
                active_teams=active_teams,
                total_workflows=total_workflows,
                workflows_today=workflows_today,
                total_cost_today=total_cost_today,
                api_calls_today=api_calls_today,
                system_health=system_health,
                active_mcps=active_mcps,
            )

        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams with their details"""
        try:
            # Get teams with member count
            teams_response = (
                self.supabase.table("team_composition").select("*").execute()
            )
            return teams_response.data
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_team_hierarchy(self) -> List[Dict[str, Any]]:
        """Get team hierarchy"""
        try:
            hierarchy_response = (
                self.supabase.table("team_hierarchy").select("*").execute()
            )
            return hierarchy_response.data
        except Exception as e:
            logger.error(f"Error getting team hierarchy: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows with stats"""
        try:
            workflows_response = (
                self.supabase.table("workflow_execution_stats").select("*").execute()
            )
            return workflows_response.data
        except Exception as e:
            logger.error(f"Error getting workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_cost_analytics(self) -> Dict[str, Any]:
        """Get detailed cost analytics"""
        try:
            # Get cost metrics for the last 7 days
            analytics = await self.cost_monitor.analyze_costs(self.quota_manager)

            # Get cost trends
            trends = await self.cost_monitor.get_cost_trends(days=7)

            # Get top spenders
            top_spenders = await self.cost_monitor.get_top_spenders(limit=5)

            return {
                "current_metrics": analytics,
                "trends": trends,
                "top_spenders": top_spenders,
                "alerts": self.cost_monitor.alerts[-10:],  # Last 10 alerts
            }
        except Exception as e:
            logger.error(f"Error getting cost analytics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            health_results = await self.health_checker.check_all()
            return {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "timestamp": result.timestamp.isoformat(),
                }
                for name, result in health_results.items()
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_mcps(self) -> List[Dict[str, Any]]:
        """Get all available MCPs"""
        try:
            mcps = await self.mcp_discovery.discover_all()
            return [
                {
                    "name": mcp.name,
                    "type": mcp.source_type,
                    "status": "active" if mcp.is_healthy else "unhealthy",
                    "tools": len(mcp.tools) if mcp.tools else 0,
                    "url": mcp.url,
                    "config": mcp.config,
                }
                for mcp in mcps
            ]
        except Exception as e:
            logger.error(f"Error getting MCPs: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_communication_logs(
        self, team: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent A2A communication logs"""
        try:
            # For now, read from log files
            logs_dir = Path("logs")
            logs = []

            if team:
                log_file = logs_dir / f"{team}_communications.log"
                if log_file.exists():
                    with open(log_file, "r") as f:
                        # Get last 100 lines
                        lines = f.readlines()[-100:]
                        for line in lines:
                            try:
                                # Parse log line
                                parts = line.strip().split(" - ", 3)
                                if len(parts) >= 4:
                                    logs.append(
                                        {
                                            "timestamp": parts[0],
                                            "team": parts[1],
                                            "level": parts[2],
                                            "message": parts[3],
                                        }
                                    )
                            except:
                                pass

            return logs
        except Exception as e:
            logger.error(f"Error getting communication logs: {e}")
            return []


# Create service instance
dashboard_service = DashboardService()
manager = ConnectionManager()


# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting ELF Dashboard Backend")

    # Initialize N8N client
    dashboard_service.n8n_client = N8NClient()

    # Start background tasks
    asyncio.create_task(real_time_updates())

    yield

    logger.info("Shutting down ELF Dashboard Backend")


# Create FastAPI app
app = FastAPI(
    title="ELF Automations Dashboard API",
    description="Central dashboard API for ELF Automations ecosystem",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Background task for real-time updates
async def real_time_updates():
    """Send real-time updates to connected clients"""
    while True:
        try:
            # Get current stats
            stats = await dashboard_service.get_dashboard_stats()

            # Broadcast to all connected clients
            await manager.broadcast(
                {
                    "type": "stats_update",
                    "data": stats.dict(),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Wait 5 seconds before next update
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error in real-time updates: {e}")
            await asyncio.sleep(10)  # Wait longer on error


# API Routes


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ELF Automations Dashboard API",
        "version": "1.0.0",
        "status": "online",
    }


@app.get("/api/stats", response_model=DashboardStats)
async def get_stats():
    """Get dashboard overview statistics"""
    return await dashboard_service.get_dashboard_stats()


@app.get("/api/teams")
async def get_teams():
    """Get all teams"""
    return await dashboard_service.get_teams()


@app.get("/api/teams/hierarchy")
async def get_team_hierarchy():
    """Get team hierarchy"""
    return await dashboard_service.get_team_hierarchy()


@app.post("/api/teams")
async def create_team(request: TeamCreateRequest):
    """Create a new team"""
    # TODO: Integrate with team factory
    return {"message": "Team creation not yet implemented", "data": request.dict()}


@app.get("/api/workflows")
async def get_workflows():
    """Get all workflows"""
    return await dashboard_service.get_workflows()


@app.post("/api/workflows")
async def create_workflow(request: WorkflowCreateRequest):
    """Create a new workflow"""
    # TODO: Integrate with N8N factory
    return {"message": "Workflow creation not yet implemented", "data": request.dict()}


@app.get("/api/costs")
async def get_cost_analytics():
    """Get cost analytics"""
    return await dashboard_service.get_cost_analytics()


@app.get("/api/health")
async def get_system_health():
    """Get system health status"""
    return await dashboard_service.get_system_health()


@app.get("/api/mcps")
async def get_mcps():
    """Get available MCPs"""
    return await dashboard_service.get_mcps()


@app.get("/api/communications")
async def get_communications(team: Optional[str] = None):
    """Get communication logs"""
    return await dashboard_service.get_communication_logs(team)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json(
                {"type": "echo", "data": data, "timestamp": datetime.now().isoformat()}
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.now().isoformat()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
