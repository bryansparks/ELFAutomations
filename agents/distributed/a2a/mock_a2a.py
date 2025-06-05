"""
Mock A2A SDK classes for testing until the real A2A SDK is available.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class AgentCapabilities:
    """Mock A2A AgentCapabilities."""
    pushNotifications: bool = True
    stateTransitionHistory: bool = True
    streaming: bool = True


@dataclass 
class AgentSkill:
    """Mock A2A AgentSkill."""
    id: str
    name: str
    description: str
    inputModes: List[str]
    outputModes: List[str]
    tags: List[str]
    examples: List[str]


@dataclass
class AgentCard:
    """Mock A2A AgentCard."""
    agent_id: str
    name: str
    description: str
    version: str
    url: str
    capabilities: AgentCapabilities
    defaultInputModes: List[str]
    defaultOutputModes: List[str]
    skills: List[AgentSkill]


class MessageType(str, Enum):
    """Mock message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


@dataclass
class A2AMessage:
    """Mock A2A Message."""
    message_type: MessageType
    sender_id: str
    recipient_id: str
    content: Dict[str, Any]
    message_id: Optional[str] = None


class A2AClient:
    """Mock A2A Client."""
    
    def __init__(self, agent_id: str, discovery_endpoint: Optional[str] = None):
        self.agent_id = agent_id
        self.discovery_endpoint = discovery_endpoint
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Mock send message."""
        return {"status": "sent", "message_id": "mock-123"}
    
    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Mock register agent."""
        return True


class A2AClientManager:
    """Mock A2A Client Manager for discovery service."""
    
    def __init__(self, discovery_endpoint: str = None):
        self.discovery_endpoint = discovery_endpoint
        self.registered_agents = {}
    
    async def register_agent(self, agent_card: AgentCard) -> Dict[str, Any]:
        """Mock register agent with discovery service."""
        self.registered_agents[agent_card.agent_id] = agent_card
        return {
            "status": "registered",
            "agent_id": agent_card.agent_id,
            "endpoint": self.discovery_endpoint
        }
    
    async def unregister_agent(self, agent_id: str) -> Dict[str, Any]:
        """Mock unregister agent from discovery service."""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
        return {
            "status": "unregistered",
            "agent_id": agent_id
        }
    
    async def discover_agents(self, capabilities: List[str] = None) -> List[AgentCard]:
        """Mock discover agents by capabilities."""
        agents = list(self.registered_agents.values())
        if capabilities:
            # Filter by capabilities (mock implementation)
            filtered_agents = []
            for agent in agents:
                if any(cap.name in capabilities for cap in agent.capabilities.skills):
                    filtered_agents.append(agent)
            return filtered_agents
        return agents


class A2AServer:
    """Mock A2A Server."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.is_running = False
    
    async def start(self):
        """Mock start server."""
        self.is_running = True
    
    async def stop(self):
        """Mock stop server."""
        self.is_running = False
    
    def add_message_handler(self, handler):
        """Mock add message handler."""
        pass


class A2AServer:
    """Mock A2A Server."""
    
    def __init__(self, agent_id: str, host: str = "0.0.0.0", port: int = 8090):
        self.agent_id = agent_id
        self.host = host
        self.port = port
        self.running = False
    
    async def start(self):
        """Mock start server."""
        self.running = True
        return {"status": "started", "host": self.host, "port": self.port}
    
    async def stop(self):
        """Mock stop server."""
        self.running = False
        return {"status": "stopped"}

    async def broadcast_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Mock broadcast message."""
        return {"status": "broadcast", "recipients": []}
