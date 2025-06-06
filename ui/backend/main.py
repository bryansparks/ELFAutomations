"""
Agent Mesh UI Backend
FastAPI server providing CLI integration and real-time updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from k8s_client import get_k8s_client
from config_service import ConfigService, ConfigValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Mesh UI API",
    description="Backend API for Agent Mesh UI providing CLI integration and real-time updates",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_str = json.dumps(message, cls=DateTimeEncoder)
            for connection in self.active_connections.copy():
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    self.active_connections.remove(connection)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_str = json.dumps(message, cls=DateTimeEncoder)
            for connection in self.active_connections.copy():
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    self.active_connections.remove(connection)

manager = ConnectionManager()

# K8s API client service
class K8sAPIService:
    def __init__(self):
        self.k8s_client = get_k8s_client()

    async def get_agents_status(self) -> Dict[str, Any]:
        """Get current agent status from Kubernetes"""
        try:
            agents = await self.k8s_client.get_kagent_resources()
            return {
                "status": "success",
                "agents": agents,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_pods_status(self) -> Dict[str, Any]:
        """Get current pod status from Kubernetes"""
        try:
            pods = await self.k8s_client.get_pods_status()
            return {
                "status": "success",
                "pods": pods,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting pod status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_services_status(self) -> Dict[str, Any]:
        """Get current services status from Kubernetes"""
        try:
            services = await self.k8s_client.get_services_status()
            return {
                "status": "success",
                "services": services,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting services status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_deployments_status(self) -> Dict[str, Any]:
        """Get current deployments status from Kubernetes"""
        try:
            deployments = await self.k8s_client.get_deployments_status()
            return {
                "status": "success",
                "deployments": deployments,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting deployments status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Check K8s API connectivity
            k8s_healthy = await self.k8s_client.health_check()
            
            # Get resource counts
            agents = await self.k8s_client.get_kagent_resources()
            pods = await self.k8s_client.get_pods_status()
            services = await self.k8s_client.get_services_status()
            deployments = await self.k8s_client.get_deployments_status()
            
            # Calculate health metrics
            total_agents = len(agents)
            healthy_agents = len([a for a in agents if a.get("phase") == "Running"])
            
            total_pods = len(pods)
            running_pods = len([p for p in pods if p.get("status") == "Running"])
            
            total_deployments = len(deployments)
            ready_deployments = len([d for d in deployments if d.get("ready_replicas", 0) > 0])
            
            return {
                "status": "success",
                "system_health": {
                    "kubernetes_api": "healthy" if k8s_healthy else "unhealthy",
                    "agents": {
                        "total": total_agents,
                        "healthy": healthy_agents,
                        "health_percentage": (healthy_agents / total_agents * 100) if total_agents > 0 else 0
                    },
                    "pods": {
                        "total": total_pods,
                        "running": running_pods,
                        "health_percentage": (running_pods / total_pods * 100) if total_pods > 0 else 0
                    },
                    "deployments": {
                        "total": total_deployments,
                        "ready": ready_deployments,
                        "health_percentage": (ready_deployments / total_deployments * 100) if total_deployments > 0 else 0
                    },
                    "services": {
                        "total": len(services)
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

k8s_api_service = K8sAPIService()
config_service = ConfigService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "operational",
        "service": "Agent Mesh UI API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/agents/status")
async def get_agents_status():
    """Get current agent status from Kubernetes"""
    return await k8s_api_service.get_agents_status()

@app.get("/api/pods/status")
async def get_pods_status():
    """Get current pod status from Kubernetes"""
    return await k8s_api_service.get_pods_status()

@app.get("/api/services/status")
async def get_services_status():
    """Get current services status from Kubernetes"""
    return await k8s_api_service.get_services_status()

@app.get("/api/deployments/status")
async def get_deployments_status():
    """Get current deployments status from Kubernetes"""
    return await k8s_api_service.get_deployments_status()

@app.get("/api/system/health")
async def get_system_health():
    """Get overall system health status"""
    return await k8s_api_service.get_system_health()

# YAML Configuration Management API Endpoints

@app.get("/api/configs/summary")
async def get_config_summary():
    """Get summary of all configurations"""
    try:
        return config_service.get_config_summary()
    except Exception as e:
        logger.error(f"Error getting config summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/configs/departments")
async def get_departments():
    """Get list of all departments"""
    try:
        return {"departments": config_service.get_departments()}
    except Exception as e:
        logger.error(f"Error getting departments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent Configuration Endpoints

@app.get("/api/configs/agents")
async def list_agents():
    """List all agent configurations"""
    try:
        agents = config_service.list_agents()
        return {"agents": agents, "total": len(agents)}
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/configs/agents/{name}")
async def get_agent(name: str):
    """Get specific agent configuration"""
    try:
        agent = config_service.get_agent(name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent configuration '{name}' not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configs/agents")
async def create_agent(config: Dict[str, Any]):
    """Create new agent configuration"""
    try:
        result = config_service.create_agent(config)
        return {"message": "Agent configuration created successfully", "agent": result}
    except ConfigValidationError as e:
        logger.error(f"Validation error creating agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/configs/agents/{name}")
async def update_agent(name: str, config: Dict[str, Any]):
    """Update existing agent configuration"""
    try:
        result = config_service.update_agent(name, config)
        return {"message": "Agent configuration updated successfully", "agent": result}
    except ConfigValidationError as e:
        logger.error(f"Validation error updating agent {name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating agent {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/configs/agents/{name}")
async def delete_agent(name: str):
    """Delete agent configuration"""
    try:
        success = config_service.delete_agent(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent configuration '{name}' not found")
        return {"message": f"Agent configuration '{name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Crew Configuration Endpoints

@app.get("/api/configs/crews")
async def list_crews():
    """List all crew configurations"""
    try:
        crews = config_service.list_crews()
        return {"crews": crews, "total": len(crews)}
    except Exception as e:
        logger.error(f"Error listing crews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/configs/crews/{name}")
async def get_crew(name: str):
    """Get specific crew configuration"""
    try:
        crew = config_service.get_crew(name)
        if crew is None:
            raise HTTPException(status_code=404, detail=f"Crew configuration '{name}' not found")
        return crew
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting crew {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configs/crews")
async def create_crew(config: Dict[str, Any]):
    """Create new crew configuration"""
    try:
        result = config_service.create_crew(config)
        return {"message": "Crew configuration created successfully", "crew": result}
    except ConfigValidationError as e:
        logger.error(f"Validation error creating crew: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating crew: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/configs/crews/{name}")
async def update_crew(name: str, config: Dict[str, Any]):
    """Update existing crew configuration"""
    try:
        result = config_service.update_crew(name, config)
        return {"message": "Crew configuration updated successfully", "crew": result}
    except ConfigValidationError as e:
        logger.error(f"Validation error updating crew {name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating crew {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/configs/crews/{name}")
async def delete_crew(name: str):
    """Delete crew configuration"""
    try:
        success = config_service.delete_crew(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Crew configuration '{name}' not found")
        return {"message": f"Crew configuration '{name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting crew {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Template Endpoints

@app.get("/api/configs/templates/agent")
async def get_agent_template():
    """Get agent configuration template"""
    try:
        return config_service.get_agent_template()
    except Exception as e:
        logger.error(f"Error getting agent template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/configs/templates/crew")
async def get_crew_template():
    """Get crew configuration template"""
    try:
        return config_service.get_crew_template()
    except Exception as e:
        logger.error(f"Error getting crew template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            elif message.get("type") == "subscribe":
                # Handle subscription requests
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "subscription": message.get("subscription"),
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Background task for real-time monitoring
async def background_monitor():
    """Background task to monitor agents and pods and broadcast updates"""
    while True:
        try:
            # Get agent status
            agents_status = await k8s_api_service.get_agents_status()
            if agents_status["status"] == "success":
                await manager.broadcast_to_all({
                    "type": "agents_update",
                    "data": agents_status["agents"]
                })
            
            # Get pod status  
            pods_status = await k8s_api_service.get_pods_status()
            if pods_status["status"] == "success":
                await manager.broadcast_to_all({
                    "type": "pods_update", 
                    "data": pods_status["pods"]
                })
                
            # Get services status
            services_status = await k8s_api_service.get_services_status()
            if services_status["status"] == "success":
                await manager.broadcast_to_all({
                    "type": "services_update",
                    "data": services_status["services"]
                })
                
            # Get deployments status
            deployments_status = await k8s_api_service.get_deployments_status()
            if deployments_status["status"] == "success":
                await manager.broadcast_to_all({
                    "type": "deployments_update",
                    "data": deployments_status["deployments"]
                })
                
            # Get system health
            system_health = await k8s_api_service.get_system_health()
            if system_health["status"] == "success":
                await manager.broadcast_to_all({
                    "type": "system_health_update",
                    "data": system_health["system_health"]
                })
                
        except Exception as e:
            logger.error(f"Error in background monitor: {e}")
        
        # Wait 30 seconds before next update (reduced from 10s for better performance)
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    """Start background monitoring task"""
    logger.info("Starting Agent Mesh UI Backend")
    asyncio.create_task(background_monitor())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8847, log_level="info")
