"""
A2A Gateway Client

Client library for teams to register with and use the A2A Gateway.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GatewayClient:
    """Client for interacting with the A2A Gateway"""
    
    def __init__(
        self,
        gateway_url: Optional[str] = None,
        registration_token: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize gateway client
        
        Args:
            gateway_url: URL of the A2A Gateway (default: from env or localhost)
            registration_token: Token for team registration (default: from env)
            timeout: HTTP timeout in seconds
        """
        self.gateway_url = gateway_url or os.getenv("A2A_GATEWAY_URL", "http://localhost:8080")
        self.registration_token = registration_token or os.getenv("GATEWAY_REGISTRATION_TOKEN", "")
        self.timeout = timeout
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        # Remove trailing slash from gateway URL
        self.gateway_url = self.gateway_url.rstrip("/")
        
    async def register_team(
        self,
        team_id: str,
        team_name: str,
        endpoint: str,
        capabilities: List[str],
        department: str,
        framework: str = "CrewAI",
        health_endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a team with the gateway
        
        Args:
            team_id: Unique team identifier
            team_name: Human-readable team name
            endpoint: Team's A2A endpoint URL
            capabilities: List of team capabilities
            department: Team department
            framework: AI framework used (default: CrewAI)
            health_endpoint: Custom health check endpoint
            metadata: Additional team metadata
            
        Returns:
            Registration response from gateway
        """
        logger.info(f"Registering team {team_id} with gateway at {self.gateway_url}")
        
        headers = {}
        if self.registration_token:
            headers["Authorization"] = f"Bearer {self.registration_token}"
        
        payload = {
            "team_id": team_id,
            "team_name": team_name,
            "endpoint": endpoint,
            "capabilities": capabilities,
            "department": department,
            "framework": framework,
            "metadata": metadata or {}
        }
        
        if health_endpoint:
            payload["health_endpoint"] = health_endpoint
        
        try:
            response = await self.http_client.post(
                f"{self.gateway_url}/register",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully registered team {team_id} with gateway")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to register team {team_id}: {e}")
            raise
    
    async def unregister_team(self, team_id: str) -> Dict[str, Any]:
        """
        Unregister a team from the gateway
        
        Args:
            team_id: Team identifier to unregister
            
        Returns:
            Unregistration response
        """
        logger.info(f"Unregistering team {team_id} from gateway")
        
        headers = {}
        if self.registration_token:
            headers["Authorization"] = f"Bearer {self.registration_token}"
        
        try:
            response = await self.http_client.delete(
                f"{self.gateway_url}/teams/{team_id}",
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully unregistered team {team_id}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to unregister team {team_id}: {e}")
            raise
    
    async def route_task(
        self,
        from_team: str,
        task_description: str,
        to_team: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 3600
    ) -> Dict[str, Any]:
        """
        Route a task through the gateway
        
        Args:
            from_team: Requesting team ID
            task_description: Description of the task
            to_team: Target team ID (optional, will route by capability if not specified)
            required_capabilities: Required capabilities for task execution
            context: Additional task context
            timeout: Task timeout in seconds
            
        Returns:
            Task execution result
        """
        logger.info(f"Routing task from {from_team}: {task_description[:50]}...")
        
        payload = {
            "from_team": from_team,
            "task_description": task_description,
            "context": context or {},
            "timeout": timeout
        }
        
        if to_team:
            payload["to_team"] = to_team
            
        if required_capabilities:
            payload["required_capabilities"] = required_capabilities
        
        try:
            response = await self.http_client.post(
                f"{self.gateway_url}/route",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Task routed successfully to {result.get('routed_to', 'unknown')}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to route task: {e}")
            raise
    
    async def discover_teams(
        self,
        capability: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available teams
        
        Args:
            capability: Filter by specific capability
            
        Returns:
            List of team information
        """
        params = {}
        if capability:
            params["capability"] = capability
        
        try:
            response = await self.http_client.get(
                f"{self.gateway_url}/teams",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to discover teams: {e}")
            raise
    
    async def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a specific team
        
        Args:
            team_id: Team identifier
            
        Returns:
            Team status information
        """
        try:
            response = await self.http_client.get(
                f"{self.gateway_url}/teams/{team_id}"
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get team status: {e}")
            raise
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get all available capabilities in the system
        
        Returns:
            Capability information
        """
        try:
            response = await self.http_client.get(
                f"{self.gateway_url}/capabilities"
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get capabilities: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get gateway statistics
        
        Returns:
            Gateway and team statistics
        """
        try:
            response = await self.http_client.get(
                f"{self.gateway_url}/stats"
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get statistics: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if gateway is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.http_client.get(
                f"{self.gateway_url}/health",
                timeout=5.0
            )
            return response.status_code == 200
            
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class TeamAutoRegistration:
    """
    Helper class for automatic team registration on startup
    """
    
    def __init__(
        self,
        team_id: str,
        team_name: str,
        team_port: int,
        capabilities: List[str],
        department: str,
        framework: str = "CrewAI",
        gateway_url: Optional[str] = None,
        registration_token: Optional[str] = None
    ):
        """
        Initialize auto-registration helper
        
        Args:
            team_id: Team identifier
            team_name: Team name
            team_port: Port the team server is running on
            capabilities: Team capabilities
            department: Team department
            framework: AI framework
            gateway_url: Gateway URL (optional)
            registration_token: Registration token (optional)
        """
        self.team_id = team_id
        self.team_name = team_name
        self.team_port = team_port
        self.capabilities = capabilities
        self.department = department
        self.framework = framework
        self.gateway_url = gateway_url
        self.registration_token = registration_token
        
        # Determine team endpoint
        self.team_endpoint = self._determine_endpoint()
        
    def _determine_endpoint(self) -> str:
        """Determine the team's endpoint URL"""
        # In Kubernetes, use service name
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            return f"http://{self.team_id}:{self.team_port}"
        # Otherwise use localhost
        else:
            return f"http://localhost:{self.team_port}"
    
    async def register(self) -> Optional[Dict[str, Any]]:
        """
        Register the team with the gateway
        
        Returns:
            Registration result or None if disabled
        """
        # Check if auto-registration is disabled
        if os.getenv("DISABLE_GATEWAY_REGISTRATION", "false").lower() == "true":
            logger.info("Gateway registration disabled by environment variable")
            return None
        
        async with GatewayClient(
            gateway_url=self.gateway_url,
            registration_token=self.registration_token
        ) as client:
            
            # Wait for gateway to be available
            max_retries = 10
            for i in range(max_retries):
                if await client.health_check():
                    break
                    
                logger.info(f"Waiting for gateway... ({i+1}/{max_retries})")
                await asyncio.sleep(5)
            else:
                logger.warning("Gateway not available, skipping registration")
                return None
            
            # Register team
            try:
                result = await client.register_team(
                    team_id=self.team_id,
                    team_name=self.team_name,
                    endpoint=self.team_endpoint,
                    capabilities=self.capabilities,
                    department=self.department,
                    framework=self.framework,
                    metadata={
                        "registered_at": datetime.now().isoformat(),
                        "auto_registered": True
                    }
                )
                
                logger.info(f"Team {self.team_id} successfully registered with gateway")
                return result
                
            except Exception as e:
                logger.error(f"Failed to register team: {e}")
                # Don't fail startup if registration fails
                return None
    
    async def unregister(self):
        """Unregister the team from the gateway"""
        async with GatewayClient(
            gateway_url=self.gateway_url,
            registration_token=self.registration_token
        ) as client:
            try:
                await client.unregister_team(self.team_id)
                logger.info(f"Team {self.team_id} unregistered from gateway")
            except Exception as e:
                logger.error(f"Failed to unregister team: {e}")


# Example usage for teams
async def example_team_startup():
    """Example of how teams should register on startup"""
    
    # Create auto-registration helper
    auto_reg = TeamAutoRegistration(
        team_id="sales-team",
        team_name="Sales Team",
        team_port=8090,
        capabilities=[
            "sales",
            "customer-engagement", 
            "proposal-generation",
            "lead-qualification"
        ],
        department="sales"
    )
    
    # Register on startup
    await auto_reg.register()
    
    # ... team runs ...
    
    # Unregister on shutdown
    await auto_reg.unregister()


if __name__ == "__main__":
    # Test the client
    asyncio.run(example_team_startup())