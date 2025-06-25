#!/usr/bin/env python3
"""
A2A Gateway Server

Central routing and discovery service for team-to-team communication
using the Google A2A protocol.

Features:
- Team registration and discovery
- Intelligent routing based on capabilities
- Health monitoring and circuit breaking
- Request/response logging
- Load balancing across team instances
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Supabase for persistent storage
from supabase import create_client, Client

# A2A types
from a2a.types import AgentCard, Task, Message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TeamRegistration(BaseModel):
    """Team registration request"""
    team_id: str
    team_name: str
    endpoint: str
    capabilities: List[str]
    department: str
    framework: str = "CrewAI"
    health_endpoint: Optional[str] = None
    metadata: Dict[str, Any] = {}


class TaskRouteRequest(BaseModel):
    """Task routing request"""
    from_team: str
    to_team: Optional[str] = None  # If None, route by capability
    task_description: str
    required_capabilities: Optional[List[str]] = None
    context: Dict[str, Any] = {}
    timeout: int = 3600


class TeamHealth(BaseModel):
    """Team health status"""
    team_id: str
    status: str  # healthy, unhealthy, degraded
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    success_count: int = 0


class TeamInstance:
    """Represents a registered team with health tracking"""
    
    def __init__(self, registration: TeamRegistration):
        self.team_id = registration.team_id
        self.team_name = registration.team_name
        self.endpoint = registration.endpoint
        self.capabilities = set(registration.capabilities)
        self.department = registration.department
        self.framework = registration.framework
        self.health_endpoint = registration.health_endpoint or f"{registration.endpoint}/health"
        self.metadata = registration.metadata
        
        # Health tracking
        self.status = "healthy"
        self.last_health_check = datetime.now()
        self.consecutive_failures = 0
        self.error_count = 0
        self.success_count = 0
        self.total_response_time = 0.0
        
        # Circuit breaker
        self.circuit_open = False
        self.circuit_opened_at: Optional[datetime] = None
        
    @property
    def is_available(self) -> bool:
        """Check if team is available for routing"""
        if self.circuit_open:
            # Check if circuit should be closed
            if self.circuit_opened_at and \
               datetime.now() - self.circuit_opened_at > timedelta(minutes=5):
                self.circuit_open = False
                self.circuit_opened_at = None
                logger.info(f"Circuit breaker closed for {self.team_id}")
        
        return self.status == "healthy" and not self.circuit_open
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        total_requests = self.success_count + self.error_count
        if total_requests == 0:
            return 0.0
        return self.total_response_time / total_requests
    
    def record_success(self, response_time: float):
        """Record successful request"""
        self.success_count += 1
        self.total_response_time += response_time
        self.consecutive_failures = 0
        
    def record_failure(self):
        """Record failed request"""
        self.error_count += 1
        self.consecutive_failures += 1
        
        # Open circuit breaker after 3 consecutive failures
        if self.consecutive_failures >= 3 and not self.circuit_open:
            self.circuit_open = True
            self.circuit_opened_at = datetime.now()
            logger.warning(f"Circuit breaker opened for {self.team_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "endpoint": self.endpoint,
            "capabilities": list(self.capabilities),
            "department": self.department,
            "framework": self.framework,
            "status": self.status,
            "is_available": self.is_available,
            "health": {
                "last_check": self.last_health_check.isoformat(),
                "error_count": self.error_count,
                "success_count": self.success_count,
                "average_response_time_ms": round(self.average_response_time, 2),
                "circuit_breaker_open": self.circuit_open
            },
            "metadata": self.metadata
        }


class A2AGateway:
    """Main gateway implementation"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        # Team registry
        self.teams: Dict[str, TeamInstance] = {}
        self.capability_index: Dict[str, Set[str]] = {}  # capability -> team_ids
        
        # HTTP client for team communication
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Supabase client for persistence
        self.supabase: Optional[Client] = None
        if supabase_url and supabase_key:
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("Connected to Supabase for persistent storage")
        
        # Background tasks
        self.health_check_task: Optional[asyncio.Task] = None
        
    async def startup(self):
        """Initialize gateway on startup"""
        logger.info("Starting A2A Gateway...")
        
        # Load teams from Supabase if available
        if self.supabase:
            await self._load_teams_from_storage()
        
        # Start health monitoring
        self.health_check_task = asyncio.create_task(self._health_monitor())
        
        logger.info("A2A Gateway started successfully")
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        logger.info("Shutting down A2A Gateway...")
        
        # Cancel background tasks
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Close HTTP client
        await self.http_client.aclose()
        
        logger.info("A2A Gateway shutdown complete")
    
    async def register_team(self, registration: TeamRegistration) -> Dict[str, Any]:
        """Register a team with the gateway"""
        logger.info(f"Registering team: {registration.team_id}")
        
        # Create team instance
        team = TeamInstance(registration)
        
        # Add to registry
        self.teams[registration.team_id] = team
        
        # Update capability index
        for capability in registration.capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = set()
            self.capability_index[capability].add(registration.team_id)
        
        # Persist to Supabase
        if self.supabase:
            try:
                self.supabase.table("a2a_teams").upsert({
                    "team_id": registration.team_id,
                    "team_name": registration.team_name,
                    "endpoint": registration.endpoint,
                    "capabilities": registration.capabilities,
                    "department": registration.department,
                    "framework": registration.framework,
                    "metadata": registration.metadata,
                    "registered_at": datetime.now().isoformat()
                }).execute()
            except Exception as e:
                logger.error(f"Failed to persist team registration: {e}")
        
        # Perform initial health check
        await self._check_team_health(team)
        
        return {
            "status": "registered",
            "team_id": registration.team_id,
            "gateway_endpoint": os.getenv("GATEWAY_URL", "http://localhost:8080")
        }
    
    async def unregister_team(self, team_id: str) -> Dict[str, Any]:
        """Unregister a team from the gateway"""
        logger.info(f"Unregistering team: {team_id}")
        
        if team_id not in self.teams:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        
        team = self.teams[team_id]
        
        # Remove from capability index
        for capability in team.capabilities:
            if capability in self.capability_index:
                self.capability_index[capability].discard(team_id)
                if not self.capability_index[capability]:
                    del self.capability_index[capability]
        
        # Remove from registry
        del self.teams[team_id]
        
        # Remove from Supabase
        if self.supabase:
            try:
                self.supabase.table("a2a_teams").delete().eq("team_id", team_id).execute()
            except Exception as e:
                logger.error(f"Failed to remove team from storage: {e}")
        
        return {"status": "unregistered", "team_id": team_id}
    
    async def route_task(self, request: TaskRouteRequest) -> Dict[str, Any]:
        """Route a task to appropriate team"""
        logger.info(f"Routing task from {request.from_team}: {request.task_description[:50]}...")
        
        # Find target team
        target_team = await self._find_target_team(request)
        if not target_team:
            raise HTTPException(
                status_code=503,
                detail="No available teams found for this task"
            )
        
        # Record routing decision
        if self.supabase:
            try:
                self.supabase.table("a2a_routing_log").insert({
                    "from_team": request.from_team,
                    "to_team": target_team.team_id,
                    "task_description": request.task_description[:500],
                    "required_capabilities": request.required_capabilities,
                    "routed_at": datetime.now().isoformat()
                }).execute()
            except Exception as e:
                logger.error(f"Failed to log routing decision: {e}")
        
        # Forward request to target team
        start_time = datetime.now()
        try:
            response = await self.http_client.post(
                f"{target_team.endpoint}/task",
                json={
                    "from_agent": request.from_team,
                    "to_agent": target_team.team_id,
                    "task_type": "routed_task",
                    "task_description": request.task_description,
                    "context": request.context,
                    "timeout": request.timeout
                },
                timeout=request.timeout
            )
            
            response.raise_for_status()
            
            # Record success
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            target_team.record_success(response_time)
            
            result = response.json()
            result["routed_to"] = target_team.team_id
            result["routing_time_ms"] = round(response_time, 2)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to route task to {target_team.team_id}: {e}")
            target_team.record_failure()
            
            # Try another team if available
            if request.to_team is None:  # Only retry if not targeting specific team
                request.required_capabilities = request.required_capabilities or []
                request.required_capabilities.append(f"not:{target_team.team_id}")
                return await self.route_task(request)
            
            raise HTTPException(
                status_code=502,
                detail=f"Failed to execute task on team {target_team.team_id}: {str(e)}"
            )
    
    async def get_teams(self, capability: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of registered teams"""
        if capability:
            # Filter by capability
            team_ids = self.capability_index.get(capability, set())
            teams = [self.teams[tid].to_dict() for tid in team_ids if tid in self.teams]
        else:
            # All teams
            teams = [team.to_dict() for team in self.teams.values()]
        
        return teams
    
    async def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """Get detailed status of a team"""
        if team_id not in self.teams:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        
        return self.teams[team_id].to_dict()
    
    async def _find_target_team(self, request: TaskRouteRequest) -> Optional[TeamInstance]:
        """Find best team for routing"""
        candidates: List[TeamInstance] = []
        
        if request.to_team:
            # Specific team requested
            if request.to_team in self.teams and self.teams[request.to_team].is_available:
                return self.teams[request.to_team]
            return None
        
        # Find by capabilities
        if request.required_capabilities:
            # Find teams with ALL required capabilities
            matching_teams = None
            for capability in request.required_capabilities:
                if capability.startswith("not:"):
                    # Exclude specific team
                    continue
                    
                teams_with_cap = self.capability_index.get(capability, set())
                if matching_teams is None:
                    matching_teams = teams_with_cap.copy()
                else:
                    matching_teams &= teams_with_cap
            
            if matching_teams:
                for team_id in matching_teams:
                    if team_id in self.teams and self.teams[team_id].is_available:
                        # Exclude teams marked with "not:"
                        if any(cap == f"not:{team_id}" for cap in request.required_capabilities):
                            continue
                        candidates.append(self.teams[team_id])
        
        # If no capability match, try to infer from task description
        if not candidates:
            task_lower = request.task_description.lower()
            
            # Simple keyword matching (can be enhanced with NLP)
            keyword_capabilities = {
                "sales": ["sales", "customer-engagement", "proposal-generation"],
                "marketing": ["marketing", "content-creation", "campaign-management"],
                "technical": ["technical", "architecture", "development"],
                "product": ["product-management", "feature-planning", "roadmap"],
                "support": ["customer-support", "issue-resolution", "help-desk"]
            }
            
            for keyword, caps in keyword_capabilities.items():
                if keyword in task_lower:
                    for cap in caps:
                        if cap in self.capability_index:
                            for team_id in self.capability_index[cap]:
                                if team_id in self.teams and self.teams[team_id].is_available:
                                    candidates.append(self.teams[team_id])
        
        if not candidates:
            return None
        
        # Select team with best performance (lowest average response time)
        return min(candidates, key=lambda t: t.average_response_time)
    
    async def _check_team_health(self, team: TeamInstance):
        """Check health of a single team"""
        try:
            start_time = datetime.now()
            response = await self.http_client.get(
                team.health_endpoint,
                timeout=5.0
            )
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                team.status = "healthy"
                team.consecutive_failures = 0
            else:
                team.status = "degraded"
                
            team.last_health_check = datetime.now()
            
        except Exception as e:
            logger.warning(f"Health check failed for {team.team_id}: {e}")
            team.status = "unhealthy"
            team.consecutive_failures += 1
            team.last_health_check = datetime.now()
    
    async def _health_monitor(self):
        """Background task to monitor team health"""
        while True:
            try:
                # Check health of all teams
                for team in self.teams.values():
                    # Check if health check is needed (every 30 seconds)
                    if datetime.now() - team.last_health_check > timedelta(seconds=30):
                        await self._check_team_health(team)
                
                # Wait before next round
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(10)
    
    async def _load_teams_from_storage(self):
        """Load team registrations from Supabase"""
        try:
            result = self.supabase.table("a2a_teams").select("*").execute()
            
            for record in result.data:
                registration = TeamRegistration(
                    team_id=record["team_id"],
                    team_name=record["team_name"],
                    endpoint=record["endpoint"],
                    capabilities=record["capabilities"],
                    department=record["department"],
                    framework=record.get("framework", "CrewAI"),
                    metadata=record.get("metadata", {})
                )
                
                team = TeamInstance(registration)
                self.teams[registration.team_id] = team
                
                # Rebuild capability index
                for capability in registration.capabilities:
                    if capability not in self.capability_index:
                        self.capability_index[capability] = set()
                    self.capability_index[capability].add(registration.team_id)
            
            logger.info(f"Loaded {len(self.teams)} teams from storage")
            
        except Exception as e:
            logger.error(f"Failed to load teams from storage: {e}")


# Create gateway instance
gateway = A2AGateway(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_ANON_KEY")
)

# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await gateway.startup()
    yield
    # Shutdown
    await gateway.shutdown()

app = FastAPI(
    title="A2A Gateway",
    description="Central routing and discovery service for team-to-team A2A communication",
    version="1.0.0",
    lifespan=lifespan
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Gateway health check"""
    return {
        "status": "healthy",
        "service": "a2a-gateway",
        "timestamp": datetime.now().isoformat(),
        "registered_teams": len(gateway.teams),
        "total_capabilities": len(gateway.capability_index)
    }


# Team registration endpoints
@app.post("/register")
async def register_team(registration: TeamRegistration):
    """Register a team with the gateway"""
    return await gateway.register_team(registration)


@app.delete("/teams/{team_id}")
async def unregister_team(team_id: str):
    """Unregister a team from the gateway"""
    return await gateway.unregister_team(team_id)


# Discovery endpoints
@app.get("/teams")
async def list_teams(capability: Optional[str] = None):
    """List registered teams, optionally filtered by capability"""
    return await gateway.get_teams(capability)


@app.get("/teams/{team_id}")
async def get_team_status(team_id: str):
    """Get detailed status of a specific team"""
    return await gateway.get_team_status(team_id)


@app.get("/capabilities")
async def list_capabilities():
    """List all available capabilities"""
    return {
        "capabilities": list(gateway.capability_index.keys()),
        "capability_count": len(gateway.capability_index),
        "team_capabilities": {
            cap: list(teams) for cap, teams in gateway.capability_index.items()
        }
    }


# Task routing endpoint
@app.post("/route")
async def route_task(request: TaskRouteRequest):
    """Route a task to appropriate team"""
    return await gateway.route_task(request)


# Proxy endpoint for direct team communication (with logging)
@app.post("/proxy/{team_id}/task")
async def proxy_task(team_id: str, request: Request):
    """Proxy a task request to specific team (with logging and monitoring)"""
    if team_id not in gateway.teams:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    
    team = gateway.teams[team_id]
    if not team.is_available:
        raise HTTPException(status_code=503, detail=f"Team {team_id} is not available")
    
    # Forward request
    body = await request.json()
    
    try:
        start_time = datetime.now()
        response = await gateway.http_client.post(
            f"{team.endpoint}/task",
            json=body,
            timeout=body.get("timeout", 3600)
        )
        
        response.raise_for_status()
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        team.record_success(response_time)
        
        return response.json()
        
    except Exception as e:
        team.record_failure()
        raise HTTPException(status_code=502, detail=str(e))


# Gateway statistics
@app.get("/stats")
async def get_statistics():
    """Get gateway statistics"""
    total_requests = sum(t.success_count + t.error_count for t in gateway.teams.values())
    total_successes = sum(t.success_count for t in gateway.teams.values())
    total_errors = sum(t.error_count for t in gateway.teams.values())
    
    return {
        "gateway_stats": {
            "registered_teams": len(gateway.teams),
            "healthy_teams": len([t for t in gateway.teams.values() if t.status == "healthy"]),
            "total_capabilities": len(gateway.capability_index),
            "total_requests": total_requests,
            "total_successes": total_successes,
            "total_errors": total_errors,
            "success_rate": round(total_successes / total_requests * 100, 2) if total_requests > 0 else 0
        },
        "team_stats": [
            {
                "team_id": team.team_id,
                "status": team.status,
                "requests": team.success_count + team.error_count,
                "success_rate": round(team.success_count / (team.success_count + team.error_count) * 100, 2) 
                    if (team.success_count + team.error_count) > 0 else 0,
                "avg_response_time_ms": round(team.average_response_time, 2)
            }
            for team in gateway.teams.values()
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting A2A Gateway on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")