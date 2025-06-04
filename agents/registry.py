"""
Agent Registry for ELF Automations

This module provides a centralized registry for managing all active agents
in the Virtual AI Company Platform.
"""

import asyncio
from typing import Dict, List, Optional, Set

import structlog

from .base import BaseAgent, AgentType

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """
    Centralized registry for managing all active agents.
    
    This class provides a singleton pattern for agent management,
    allowing agents to discover and communicate with each other.
    """
    
    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, BaseAgent] = {}
    _agents_by_department: Dict[str, Set[str]] = {}
    _agents_by_type: Dict[AgentType, Set[str]] = {}
    _lock = asyncio.Lock()
    
    def __new__(cls) -> 'AgentRegistry':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def register_agent(cls, agent: BaseAgent) -> None:
        """
        Register an agent with the registry.
        
        Args:
            agent: The agent to register
        """
        async with cls._lock:
            agent_id = agent.agent_id
            
            if agent_id in cls._agents:
                logger.warning("Agent already registered", agent_id=agent_id)
                return
            
            # Add to main registry
            cls._agents[agent_id] = agent
            
            # Add to department index
            if agent.department not in cls._agents_by_department:
                cls._agents_by_department[agent.department] = set()
            cls._agents_by_department[agent.department].add(agent_id)
            
            # Add to type index
            if agent.agent_type not in cls._agents_by_type:
                cls._agents_by_type[agent.agent_type] = set()
            cls._agents_by_type[agent.agent_type].add(agent_id)
            
            logger.info(
                "Agent registered",
                agent_id=agent_id,
                agent_name=agent.name,
                department=agent.department,
                agent_type=agent.agent_type.value,
                total_agents=len(cls._agents)
            )
    
    @classmethod
    async def unregister_agent(cls, agent_id: str) -> None:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        async with cls._lock:
            if agent_id not in cls._agents:
                logger.warning("Agent not found for unregistration", agent_id=agent_id)
                return
            
            agent = cls._agents[agent_id]
            
            # Remove from main registry
            del cls._agents[agent_id]
            
            # Remove from department index
            if agent.department in cls._agents_by_department:
                cls._agents_by_department[agent.department].discard(agent_id)
                if not cls._agents_by_department[agent.department]:
                    del cls._agents_by_department[agent.department]
            
            # Remove from type index
            if agent.agent_type in cls._agents_by_type:
                cls._agents_by_type[agent.agent_type].discard(agent_id)
                if not cls._agents_by_type[agent.agent_type]:
                    del cls._agents_by_type[agent.agent_type]
            
            logger.info(
                "Agent unregistered",
                agent_id=agent_id,
                agent_name=agent.name,
                total_agents=len(cls._agents)
            )
    
    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            The agent instance or None if not found
        """
        return cls._agents.get(agent_id)
    
    @classmethod
    def get_agents_by_department(cls, department: str) -> List[BaseAgent]:
        """
        Get all agents in a specific department.
        
        Args:
            department: Department name
            
        Returns:
            List of agents in the department
        """
        agent_ids = cls._agents_by_department.get(department, set())
        return [cls._agents[agent_id] for agent_id in agent_ids if agent_id in cls._agents]
    
    @classmethod
    def get_agents_by_type(cls, agent_type: AgentType) -> List[BaseAgent]:
        """
        Get all agents of a specific type.
        
        Args:
            agent_type: Type of agents to retrieve
            
        Returns:
            List of agents of the specified type
        """
        agent_ids = cls._agents_by_type.get(agent_type, set())
        return [cls._agents[agent_id] for agent_id in agent_ids if agent_id in cls._agents]
    
    @classmethod
    def get_all_agents(cls) -> List[BaseAgent]:
        """
        Get all registered agents.
        
        Returns:
            List of all registered agents
        """
        return list(cls._agents.values())
    
    @classmethod
    def find_agents(cls, **criteria) -> List[BaseAgent]:
        """
        Find agents matching specific criteria.
        
        Args:
            **criteria: Search criteria (department, agent_type, status, etc.)
            
        Returns:
            List of matching agents
        """
        matching_agents = []
        
        for agent in cls._agents.values():
            match = True
            
            # Check department
            if 'department' in criteria and agent.department != criteria['department']:
                match = False
            
            # Check agent type
            if 'agent_type' in criteria and agent.agent_type != criteria['agent_type']:
                match = False
            
            # Check status
            if 'status' in criteria and agent.state.status != criteria['status']:
                match = False
            
            # Check name pattern
            if 'name_contains' in criteria and criteria['name_contains'].lower() not in agent.name.lower():
                match = False
            
            if match:
                matching_agents.append(agent)
        
        return matching_agents
    
    @classmethod
    def get_department_head(cls, department: str) -> Optional[BaseAgent]:
        """
        Get the department head for a specific department.
        
        Args:
            department: Department name
            
        Returns:
            The department head agent or None if not found
        """
        department_agents = cls.get_agents_by_department(department)
        
        for agent in department_agents:
            if agent.agent_type == AgentType.DEPARTMENT_HEAD:
                return agent
        
        return None
    
    @classmethod
    def get_executive_agents(cls) -> List[BaseAgent]:
        """
        Get all executive-level agents.
        
        Returns:
            List of executive agents
        """
        return cls.get_agents_by_type(AgentType.EXECUTIVE)
    
    @classmethod
    def get_registry_stats(cls) -> Dict[str, any]:
        """
        Get statistics about the agent registry.
        
        Returns:
            Dictionary containing registry statistics
        """
        stats = {
            "total_agents": len(cls._agents),
            "departments": {},
            "agent_types": {},
            "active_agents": 0,
            "busy_agents": 0,
            "error_agents": 0
        }
        
        # Count by department
        for department, agent_ids in cls._agents_by_department.items():
            stats["departments"][department] = len(agent_ids)
        
        # Count by type
        for agent_type, agent_ids in cls._agents_by_type.items():
            stats["agent_types"][agent_type.value] = len(agent_ids)
        
        # Count by status
        for agent in cls._agents.values():
            if agent.state.status.value == "active":
                stats["active_agents"] += 1
            elif agent.state.status.value == "busy":
                stats["busy_agents"] += 1
            elif agent.state.status.value == "error":
                stats["error_agents"] += 1
        
        return stats
    
    @classmethod
    async def broadcast_message(cls, message_type: str, content: Dict[str, any], 
                               sender_id: str, department: Optional[str] = None,
                               agent_type: Optional[AgentType] = None) -> List[str]:
        """
        Broadcast a message to multiple agents.
        
        Args:
            message_type: Type of message to broadcast
            content: Message content
            sender_id: ID of the sending agent
            department: Optional department filter
            agent_type: Optional agent type filter
            
        Returns:
            List of message IDs sent
        """
        target_agents = []
        
        if department:
            target_agents = cls.get_agents_by_department(department)
        elif agent_type:
            target_agents = cls.get_agents_by_type(agent_type)
        else:
            target_agents = cls.get_all_agents()
        
        # Don't send to sender
        target_agents = [agent for agent in target_agents if agent.agent_id != sender_id]
        
        message_ids = []
        sender_agent = cls.get_agent(sender_id)
        
        if sender_agent:
            for target_agent in target_agents:
                try:
                    message_id = await sender_agent.send_message(
                        to_agent=target_agent.agent_id,
                        message_type=message_type,
                        content=content
                    )
                    message_ids.append(message_id)
                except Exception as e:
                    logger.error(
                        "Failed to send broadcast message",
                        sender_id=sender_id,
                        target_agent=target_agent.agent_id,
                        error=str(e)
                    )
        
        logger.info(
            "Broadcast message sent",
            message_type=message_type,
            sender_id=sender_id,
            target_count=len(target_agents),
            successful_sends=len(message_ids)
        )
        
        return message_ids
    
    @classmethod
    async def shutdown_all_agents(cls) -> None:
        """
        Shutdown all registered agents.
        """
        logger.info("Shutting down all agents", total_agents=len(cls._agents))
        
        # Create list of shutdown tasks
        shutdown_tasks = []
        for agent in cls._agents.values():
            shutdown_tasks.append(agent.stop())
        
        # Wait for all agents to shutdown
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        # Clear all registries
        cls._agents.clear()
        cls._agents_by_department.clear()
        cls._agents_by_type.clear()
        
        logger.info("All agents shutdown complete")
    
    @classmethod
    def list_agents(cls) -> List[Dict[str, any]]:
        """
        Get a list of all agents with their basic information.
        
        Returns:
            List of agent information dictionaries
        """
        return [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "type": agent.agent_type.value,
                "department": agent.department,
                "status": agent.state.status.value,
                "current_task": agent.state.current_task,
                "last_activity": agent.state.last_activity.isoformat(),
                "error_count": agent.state.error_count
            }
            for agent in cls._agents.values()
        ]
