#!/usr/bin/env python3
"""
ElfAutomations.ai Control Center API
Provides comprehensive system data for the Control Center UI
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import structlog
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import Client, create_client

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from elf_automations.shared.monitoring.cost_monitor import CostMonitor
from elf_automations.shared.registry.client import TeamRegistryClient
from elf_automations.shared.utils.config import get_supabase_client

# Configure logging
logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ElfAutomations Control Center API",
    description="Comprehensive system data API for the Control Center UI",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients
supabase_client: Optional[Client] = None
team_registry: Optional[TeamRegistryClient] = None
cost_monitor: Optional[CostMonitor] = None

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []


# Response models
class SystemStatus(BaseModel):
    status: str
    health_score: int
    active_teams: int
    total_teams: int
    active_workflows: int
    system_load: float
    api_availability: Dict[str, bool]
    last_updated: datetime


class TeamInfo(BaseModel):
    id: str
    name: str
    display_name: str
    department: str
    placement: str
    status: str
    framework: str
    llm_provider: str
    llm_model: str
    member_count: int
    is_manager: bool = False
    reports_to: Optional[str] = None
    subordinate_teams: List[str] = []


class CostMetrics(BaseModel):
    today_cost: float
    today_budget: float
    today_percentage: float
    month_cost: float
    month_budget: float
    trend: str  # 'up', 'down', 'stable'
    top_teams: List[Dict[str, Any]]
    cost_by_model: Dict[str, float]
    hourly_costs: List[Dict[str, Any]]


class WorkflowStatus(BaseModel):
    id: str
    name: str
    status: str
    last_run: Optional[datetime]
    success_rate: float
    avg_duration: float
    executions_today: int


class Activity(BaseModel):
    id: str
    timestamp: datetime
    type: str  # 'team_created', 'workflow_executed', 'alert', etc
    title: str
    description: str
    severity: str  # 'info', 'warning', 'error'
    team: Optional[str] = None


class DashboardData(BaseModel):
    system_status: SystemStatus
    cost_metrics: CostMetrics
    teams: List[TeamInfo]
    workflows: List[WorkflowStatus]
    recent_activities: List[Activity]
    alerts: List[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    """Initialize clients on startup"""
    global supabase_client, team_registry, cost_monitor

    try:
        # Initialize Supabase client
        supabase_client = get_supabase_client()

        # Initialize team registry
        team_registry = TeamRegistryClient(supabase_client)

        # Initialize cost monitor
        cost_monitor = CostMonitor(supabase_client)

        logger.info("Control Center API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Control Center API: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/api/system/status", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status"""
    try:
        # Get team counts
        teams = await team_registry.get_all_teams()
        active_teams = [t for t in teams if t.get("status") == "active"]

        # Check API availability
        api_status = {
            "supabase": supabase_client is not None,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "n8n": await check_n8n_status(),
        }

        # Get workflow counts from N8N registry
        workflows = supabase_client.table("n8n_workflow_registry").select("*").execute()
        active_workflows = len([w for w in workflows.data if w.get("is_active")])

        # Calculate health score (0-100)
        health_score = calculate_health_score(
            len(active_teams), len(teams), api_status, active_workflows
        )

        return SystemStatus(
            status="operational" if health_score > 70 else "degraded",
            health_score=health_score,
            active_teams=len(active_teams),
            total_teams=len(teams),
            active_workflows=active_workflows,
            system_load=await get_system_load(),
            api_availability=api_status,
            last_updated=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/costs/metrics", response_model=CostMetrics)
async def get_cost_metrics():
    """Get comprehensive cost metrics"""
    try:
        # Get today's costs
        today = datetime.utcnow().date()
        today_usage = await cost_monitor.get_daily_usage("all", today)

        # Get monthly costs
        month_start = today.replace(day=1)
        monthly_costs = await cost_monitor.get_usage_between_dates(
            "all", month_start, today
        )

        # Get team budgets
        budgets = supabase_client.table("team_budgets").select("*").execute()
        daily_budget = sum(b.get("daily_budget", 10) for b in budgets.data)
        monthly_budget = daily_budget * 30  # Approximate

        # Get top spending teams
        top_teams = await cost_monitor.get_top_spending_teams(limit=5)

        # Get cost by model
        cost_by_model = await cost_monitor.get_cost_by_model(today)

        # Get hourly costs for trend
        hourly_costs = await cost_monitor.get_hourly_costs(today)

        # Determine trend
        yesterday = today - timedelta(days=1)
        yesterday_usage = await cost_monitor.get_daily_usage("all", yesterday)
        trend = determine_cost_trend(
            today_usage["total_cost"], yesterday_usage.get("total_cost", 0)
        )

        return CostMetrics(
            today_cost=float(today_usage.get("total_cost", 0)),
            today_budget=float(daily_budget),
            today_percentage=float(
                today_usage.get("total_cost", 0) / daily_budget * 100
            )
            if daily_budget > 0
            else 0,
            month_cost=float(monthly_costs.get("total_cost", 0)),
            month_budget=float(monthly_budget),
            trend=trend,
            top_teams=top_teams,
            cost_by_model=cost_by_model,
            hourly_costs=hourly_costs,
        )
    except Exception as e:
        logger.error(f"Error getting cost metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams", response_model=List[TeamInfo])
async def get_teams():
    """Get all teams with hierarchy information"""
    try:
        # Get teams from registry
        teams = await team_registry.get_all_teams()

        # Get relationships
        relationships = (
            supabase_client.table("team_relationships").select("*").execute()
        )

        # Get team members
        members = supabase_client.table("team_members").select("*").execute()

        # Build team info
        team_infos = []
        for team in teams:
            # Count members
            team_members = [m for m in members.data if m["team_id"] == team["id"]]

            # Find relationships
            reports_to = None
            subordinates = []
            for rel in relationships.data:
                if rel["child_team_id"] == team["id"]:
                    reports_to = rel["parent_entity_name"]
                elif (
                    rel["parent_entity_name"] == team["name"]
                    and rel["parent_entity_type"] == "team"
                ):
                    subordinates.append(rel["child_team_id"])

            # Get subordinate team names
            subordinate_names = [t["name"] for t in teams if t["id"] in subordinates]

            team_infos.append(
                TeamInfo(
                    id=team["id"],
                    name=team["name"],
                    display_name=team["display_name"],
                    department=team["department"],
                    placement=team["placement"],
                    status=team["status"],
                    framework=team["framework"],
                    llm_provider=team["llm_provider"],
                    llm_model=team["llm_model"],
                    member_count=len(team_members),
                    is_manager=any(m["is_manager"] for m in team_members),
                    reports_to=reports_to,
                    subordinate_teams=subordinate_names,
                )
            )

        return team_infos
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows", response_model=List[WorkflowStatus])
async def get_workflows():
    """Get workflow status from N8N registry"""
    try:
        # Get workflows from registry
        workflows = supabase_client.table("n8n_workflow_registry").select("*").execute()

        # Get execution history (if available)
        # For now, return mock data - would integrate with N8N API
        workflow_statuses = []
        for workflow in workflows.data:
            workflow_statuses.append(
                WorkflowStatus(
                    id=workflow["workflow_id"],
                    name=workflow["name"],
                    status="active" if workflow["is_active"] else "inactive",
                    last_run=workflow.get("updated_at"),
                    success_rate=95.0,  # Mock data
                    avg_duration=120.5,  # Mock data
                    executions_today=workflow.get("execution_count", 0),
                )
            )

        return workflow_statuses
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/activities", response_model=List[Activity])
async def get_recent_activities():
    """Get recent system activities"""
    try:
        activities = []

        # Get team audit log
        audit_logs = (
            supabase_client.table("team_audit_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        for log in audit_logs.data:
            activities.append(
                Activity(
                    id=log["id"],
                    timestamp=log["created_at"],
                    type="team_" + log["action"],
                    title=f"Team {log['action']}",
                    description=log.get("description", ""),
                    severity="info",
                    team=log.get("team_id"),
                )
            )

        # Get cost alerts
        alerts = (
            supabase_client.table("cost_alerts")
            .select("*")
            .order("timestamp", desc=True)
            .limit(5)
            .execute()
        )

        for alert in alerts.data:
            activities.append(
                Activity(
                    id=alert["id"],
                    timestamp=alert["timestamp"],
                    type="alert",
                    title=alert["message"],
                    description=f"Alert type: {alert['alert_type']}",
                    severity=alert["level"],
                    team=alert.get("team_name"),
                )
            )

        # Sort by timestamp
        activities.sort(key=lambda x: x.timestamp, reverse=True)

        return activities[:20]  # Return top 20
    except Exception as e:
        logger.error(f"Error getting activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data():
    """Get all dashboard data in one request"""
    try:
        # Parallel fetch all data
        system_status_task = get_system_status()
        cost_metrics_task = get_cost_metrics()
        teams_task = get_teams()
        workflows_task = get_workflows()
        activities_task = get_recent_activities()

        # Get alerts
        alerts = (
            supabase_client.table("cost_alerts")
            .select("*")
            .eq("acknowledged", False)
            .order("timestamp", desc=True)
            .limit(5)
            .execute()
        )

        # Wait for all tasks
        system_status = await system_status_task
        cost_metrics = await cost_metrics_task
        teams = await teams_task
        workflows = await workflows_task
        activities = await activities_task

        return DashboardData(
            system_status=system_status,
            cost_metrics=cost_metrics,
            teams=teams,
            workflows=workflows,
            recent_activities=activities,
            alerts=alerts.data,
        )
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Send updates every 5 seconds
            await asyncio.sleep(5)

            # Get latest data
            status = await get_system_status()
            await websocket.send_json(
                {
                    "type": "status_update",
                    "data": status.dict(),
                }
            )
    except WebSocketDisconnect:
        active_connections.remove(websocket)


# Helper functions
async def check_n8n_status() -> bool:
    """Check if N8N is accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5678/healthz", timeout=2.0)
            return response.status_code == 200
    except:
        return False


def calculate_health_score(
    active_teams: int,
    total_teams: int,
    api_status: Dict[str, bool],
    active_workflows: int,
) -> int:
    """Calculate system health score (0-100)"""
    score = 0

    # Team availability (40 points)
    if total_teams > 0:
        score += int((active_teams / total_teams) * 40)

    # API availability (40 points)
    available_apis = sum(1 for v in api_status.values() if v)
    score += int((available_apis / len(api_status)) * 40)

    # Workflow activity (20 points)
    if active_workflows > 0:
        score += min(20, active_workflows * 4)  # Max 20 points

    return score


async def get_system_load() -> float:
    """Get system load metric"""
    # Mock implementation - would check actual system metrics
    return 0.65


def determine_cost_trend(today_cost: float, yesterday_cost: float) -> str:
    """Determine cost trend"""
    if yesterday_cost == 0:
        return "stable"

    change = (today_cost - yesterday_cost) / yesterday_cost
    if change > 0.1:
        return "up"
    elif change < -0.1:
        return "down"
    else:
        return "stable"


if __name__ == "__main__":
    import uvicorn

    # Run the API server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
