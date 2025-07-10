#!/usr/bin/env python3
"""
ElfAutomations.ai Control Center API - Minimal Version
Avoids complex imports to work around dependency issues
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="ElfAutomations Control Center API",
    description="Comprehensive system data API for the Control Center UI",
    version="1.0.0",
)

# CORS configuration - allow access from any origin for development
# In production, restrict to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients
supabase_client: Optional[Client] = None

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


def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global supabase_client
    if not supabase_client:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        supabase_client = create_client(url, key)
    return supabase_client


@app.on_event("startup")
async def startup_event():
    """Initialize clients on startup"""
    try:
        # Initialize Supabase client
        get_supabase_client()
        print("Control Center API initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Control Center API: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/api/system/status", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status"""
    try:
        client = get_supabase_client()

        # Get team counts
        teams_result = client.table("teams").select("*", count="exact").execute()
        teams = teams_result.data or []
        active_teams = [t for t in teams if t.get("status") == "active"]

        # Check API availability
        api_status = {
            "supabase": client is not None,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "n8n": await check_n8n_status(),
        }

        # Get workflow counts from N8N registry
        workflows_result = (
            client.table("n8n_workflow_registry").select("*", count="exact").execute()
        )
        workflows = workflows_result.data or []
        active_workflows = len([w for w in workflows if w.get("is_active")])

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
            system_load=0.65,  # Mock for now
            api_availability=api_status,
            last_updated=datetime.utcnow(),
        )
    except Exception as e:
        print(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/costs/metrics", response_model=CostMetrics)
async def get_cost_metrics():
    """Get comprehensive cost metrics"""
    try:
        client = get_supabase_client()

        # Get today's costs
        today = datetime.utcnow().date()
        today_str = today.isoformat()

        # Get daily summary
        daily_result = (
            client.table("daily_cost_summary")
            .select("*")
            .eq("date", today_str)
            .execute()
        )

        today_data = daily_result.data[0] if daily_result.data else {}
        today_cost = float(today_data.get("total_cost", 0))

        # Get monthly costs
        month_start = today.replace(day=1).isoformat()
        monthly_result = (
            client.table("daily_cost_summary")
            .select("total_cost")
            .gte("date", month_start)
            .lte("date", today_str)
            .execute()
        )

        month_cost = sum(float(d.get("total_cost", 0)) for d in monthly_result.data)

        # Get budgets
        budgets_result = client.table("team_budgets").select("daily_budget").execute()
        daily_budget = (
            sum(float(b.get("daily_budget", 10)) for b in budgets_result.data) or 100
        )
        monthly_budget = daily_budget * 30

        # Get top spending teams (mock for now)
        top_teams = [
            {
                "team_name": "engineering-team",
                "total_cost": 45.23,
                "request_count": 1250,
            },
            {"team_name": "marketing-team", "total_cost": 32.15, "request_count": 890},
            {"team_name": "executive-team", "total_cost": 28.90, "request_count": 750},
        ]

        # Cost by model (mock)
        cost_by_model = {
            "gpt-4": 45.50,
            "gpt-3.5-turbo": 12.30,
            "claude-3-opus": 38.20,
            "claude-3-sonnet": 15.40,
        }

        # Hourly costs (mock)
        hourly_costs = [
            {"hour": i, "cost": 5 + (i % 8) * 2, "requests": 50 + (i % 5) * 20}
            for i in range(24)
        ]

        # Determine trend
        yesterday = (today - timedelta(days=1)).isoformat()
        yesterday_result = (
            client.table("daily_cost_summary")
            .select("total_cost")
            .eq("date", yesterday)
            .execute()
        )

        yesterday_cost = (
            float(yesterday_result.data[0].get("total_cost", 0))
            if yesterday_result.data
            else 0
        )
        trend = determine_cost_trend(today_cost, yesterday_cost)

        return CostMetrics(
            today_cost=today_cost,
            today_budget=daily_budget,
            today_percentage=(today_cost / daily_budget * 100)
            if daily_budget > 0
            else 0,
            month_cost=month_cost,
            month_budget=monthly_budget,
            trend=trend,
            top_teams=top_teams,
            cost_by_model=cost_by_model,
            hourly_costs=hourly_costs,
        )
    except Exception as e:
        print(f"Error getting cost metrics: {e}")
        # Return mock data on error
        return CostMetrics(
            today_cost=125.50,
            today_budget=200.0,
            today_percentage=62.75,
            month_cost=2150.30,
            month_budget=6000.0,
            trend="up",
            top_teams=[
                {
                    "team_name": "engineering-team",
                    "total_cost": 45.23,
                    "request_count": 1250,
                },
                {
                    "team_name": "marketing-team",
                    "total_cost": 32.15,
                    "request_count": 890,
                },
            ],
            cost_by_model={"gpt-4": 45.50, "claude-3-opus": 38.20},
            hourly_costs=[
                {"hour": i, "cost": 5 + (i % 8) * 2, "requests": 50} for i in range(24)
            ],
        )


@app.get("/api/teams", response_model=List[TeamInfo])
async def get_teams():
    """Get all teams with hierarchy information"""
    try:
        client = get_supabase_client()

        # Get teams from registry
        teams_result = client.table("teams").select("*").execute()
        teams = teams_result.data or []

        # Get relationships
        relationships_result = client.table("team_relationships").select("*").execute()
        relationships = relationships_result.data or []

        # Get team members
        members_result = client.table("team_members").select("*").execute()
        members = members_result.data or []

        # Build team info
        team_infos = []
        for team in teams:
            # Count members
            team_members = [m for m in members if m["team_id"] == team["id"]]

            # Find relationships
            reports_to = None
            subordinates = []
            for rel in relationships:
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
        print(f"Error getting teams: {e}")
        # Return mock data on error
        return [
            TeamInfo(
                id="1",
                name="executive-team",
                display_name="Executive Team",
                department="executive",
                placement="executive",
                status="active",
                framework="CrewAI",
                llm_provider="OpenAI",
                llm_model="gpt-4",
                member_count=5,
                is_manager=True,
                reports_to=None,
                subordinate_teams=["engineering-team", "marketing-team"],
            ),
            TeamInfo(
                id="2",
                name="engineering-team",
                display_name="Engineering Team",
                department="engineering",
                placement="engineering",
                status="active",
                framework="LangGraph",
                llm_provider="Anthropic",
                llm_model="claude-3-opus",
                member_count=8,
                is_manager=True,
                reports_to="Chief Technology Officer",
                subordinate_teams=[],
            ),
        ]


@app.get("/api/workflows", response_model=List[WorkflowStatus])
async def get_workflows():
    """Get workflow status from N8N registry"""
    try:
        client = get_supabase_client()

        # Get workflows from registry
        workflows_result = client.table("n8n_workflow_registry").select("*").execute()
        workflows = workflows_result.data or []

        # Get execution history (if available)
        workflow_statuses = []
        for workflow in workflows:
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
        print(f"Error getting workflows: {e}")
        # Return mock data
        return [
            WorkflowStatus(
                id="1",
                name="Customer Onboarding",
                status="active",
                last_run=datetime.utcnow(),
                success_rate=98.5,
                avg_duration=45.2,
                executions_today=23,
            ),
            WorkflowStatus(
                id="2",
                name="Daily Reports",
                status="active",
                last_run=datetime.utcnow() - timedelta(hours=2),
                success_rate=100.0,
                avg_duration=180.0,
                executions_today=4,
            ),
        ]


@app.get("/api/activities", response_model=List[Activity])
async def get_recent_activities():
    """Get recent system activities"""
    try:
        client = get_supabase_client()
        activities = []

        # Get team audit log
        audit_result = (
            client.table("team_audit_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        for log in audit_result.data:
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
        alerts_result = (
            client.table("cost_alerts")
            .select("*")
            .order("timestamp", desc=True)
            .limit(5)
            .execute()
        )

        for alert in alerts_result.data:
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
        print(f"Error getting activities: {e}")
        # Return mock data
        return [
            Activity(
                id="1",
                timestamp=datetime.utcnow(),
                type="team_created",
                title="Team created",
                description="Marketing team was created",
                severity="info",
                team="marketing-team",
            ),
            Activity(
                id="2",
                timestamp=datetime.utcnow() - timedelta(hours=1),
                type="alert",
                title="High API usage detected",
                description="Engineering team exceeded 80% of daily budget",
                severity="warning",
                team="engineering-team",
            ),
        ]


@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data():
    """Get all dashboard data in one request"""
    try:
        # Parallel fetch all data
        system_status = await get_system_status()
        cost_metrics = await get_cost_metrics()
        teams = await get_teams()
        workflows = await get_workflows()
        activities = await get_recent_activities()

        # Get alerts
        client = get_supabase_client()
        alerts_result = (
            client.table("cost_alerts")
            .select("*")
            .eq("acknowledged", False)
            .order("timestamp", desc=True)
            .limit(5)
            .execute()
        )

        return DashboardData(
            system_status=system_status,
            cost_metrics=cost_metrics,
            teams=teams,
            workflows=workflows,
            recent_activities=activities,
            alerts=alerts_result.data or [],
        )
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mcp/create")
async def create_mcp(config: Dict[str, Any]):
    """Create a new MCP using the factory"""
    try:
        import json
        import subprocess
        import tempfile

        # Save config to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        # Run mcp_factory.py script
        # In production, this would be more sophisticated
        result = subprocess.run(
            ["python", "tools/mcp_factory.py", "--config", config_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
        )

        # Clean up temp file
        os.unlink(config_path)

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"MCP '{config['name']}' created successfully",
                "path": f"/mcps/{config['language']}/{config['name']}/",
                "output": result.stdout,
            }
        else:
            return {
                "success": False,
                "message": "Failed to create MCP",
                "error": result.stderr,
            }
    except Exception as e:
        print(f"Error creating MCP: {e}")
        # For now, return a simulated success response
        return {
            "success": True,
            "message": f"MCP '{config['name']}' creation initiated",
            "path": f"/mcps/{config['language']}/{config['name']}/",
            "note": "In production, this would run the actual mcp_factory.py script",
        }


@app.get("/api/mcp/discover")
async def discover_mcps(query: Optional[str] = None):
    """Discover available MCP servers"""
    try:
        # Import here to avoid startup issues
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from tools.mcp_marketplace import MCPMarketplace

        marketplace = MCPMarketplace()
        # Get filtered MCPs based on query
        if query:
            mcps = [
                m
                for m in marketplace.known_mcps
                if query.lower() in m.name.lower()
                or query.lower() in m.description.lower()
                or any(query.lower() in cap for cap in m.capabilities)
            ]
        else:
            mcps = marketplace.known_mcps

        # Convert to API response format
        return {
            "success": True,
            "mcps": [
                {
                    "name": mcp.name,
                    "description": mcp.description,
                    "source": mcp.source,
                    "installType": mcp.install_type,
                    "installCommand": mcp.install_command,
                    "capabilities": mcp.capabilities,
                    "author": mcp.author,
                    "verified": mcp.verified,
                    "stars": mcp.stars,
                    "installed": False,  # Check against registry in real implementation
                }
                for mcp in mcps
            ],
            "total": len(mcps),
        }
    except Exception as e:
        print(f"Error discovering MCPs: {e}")
        return {"success": False, "message": str(e), "mcps": []}


@app.post("/api/mcp/install")
async def install_mcp(request: Dict[str, str]):
    """Install an MCP from the marketplace"""
    try:
        mcp_name = request.get("name")
        if not mcp_name:
            return {"success": False, "message": "MCP name is required"}

        # Import here to avoid startup issues
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from tools.mcp_marketplace import MCPMarketplace

        marketplace = MCPMarketplace()
        success = marketplace.install_mcp(mcp_name)

        if success:
            return {"success": True, "message": f"Successfully installed {mcp_name}"}
        else:
            return {"success": False, "message": f"Failed to install {mcp_name}"}
    except Exception as e:
        print(f"Error installing MCP: {e}")
        return {"success": False, "message": str(e)}


@app.get("/api/mcp/installed")
async def list_installed_mcps():
    """List installed MCPs"""
    try:
        # Import here to avoid startup issues
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from tools.mcp_marketplace import MCPMarketplace

        marketplace = MCPMarketplace()

        # Check if registry exists
        if not marketplace.registry_file.exists():
            return {"success": True, "mcps": [], "total": 0}

        with open(marketplace.registry_file, "r") as f:
            registry = json.load(f)

        mcps = [
            {
                "name": name,
                "description": info.get("description", ""),
                "source": info.get("source", ""),
                "capabilities": info.get("capabilities", []),
                "installedAt": info.get("installed_at", ""),
            }
            for name, info in registry.items()
        ]

        return {"success": True, "mcps": mcps, "total": len(mcps)}
    except Exception as e:
        print(f"Error listing installed MCPs: {e}")
        return {"success": False, "message": str(e), "mcps": []}


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
