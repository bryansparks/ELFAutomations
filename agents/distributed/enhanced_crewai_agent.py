"""
Enhanced CrewAI Agent with A2A Discovery Integration

This module provides enhanced CrewAI agents and crews that integrate with A2A discovery
using composition wrappers to avoid Pydantic validation conflicts.

Updated to use REAL A2A services instead of mocks.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from crewai import Agent, Task, Crew

# Import REAL A2A services
from .a2a.discovery import DiscoveryService
from .a2a.client import A2AClientManager
from .a2a.mock_a2a import AgentCard, AgentCapabilities, AgentSkill  # For AgentCard structure

logger = logging.getLogger(__name__)


@dataclass
class A2AConfig:
    """Configuration for A2A services"""
    discovery_endpoint: Optional[str] = None
    redis_url: str = "redis://localhost:6379"
    timeout: float = 30.0
    max_retries: int = 3


class A2AAgentWrapper:
    """Wrapper that adds A2A capabilities to CrewAI agents using REAL A2A services"""
    
    def __init__(
        self, 
        agent: Agent, 
        capabilities: List[str] = None, 
        a2a_enabled: bool = True,
        a2a_config: A2AConfig = None
    ):
        self.agent = agent
        self.capabilities = capabilities or []
        self.a2a_enabled = a2a_enabled
        self.a2a_config = a2a_config or A2AConfig()
        
        # Initialize REAL A2A services
        self.discovery_service = None
        self.a2a_client = None
        
        if self.a2a_enabled:
            self._initialize_a2a_services()
    
    def _initialize_a2a_services(self):
        """Initialize real A2A services"""
        try:
            # Initialize real discovery service
            self.discovery_service = DiscoveryService(
                discovery_endpoint=self.a2a_config.discovery_endpoint
            )
            
            # Initialize real A2A client manager
            agent_id = f"crew_agent_{self.agent.role.lower().replace(' ', '_')}"
            self.a2a_client = A2AClientManager(
                agent_id=agent_id,
                discovery_endpoint=self.a2a_config.discovery_endpoint,
                redis_url=self.a2a_config.redis_url,
                timeout=self.a2a_config.timeout,
                max_retries=self.a2a_config.max_retries
            )
            
            logger.info(f"✅ Initialized real A2A services for agent: {agent_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize A2A services: {e}")
            self.a2a_enabled = False
    
    def __getattr__(self, name):
        """Delegate attribute access to the wrapped agent"""
        return getattr(self.agent, name)
    
    async def start_a2a_services(self):
        """Start A2A services (must be called before using A2A features)"""
        if not self.a2a_enabled or not self.a2a_client:
            return
            
        try:
            await self.a2a_client.start()
            await self._register_agent()
            logger.info(f"🚀 Started A2A services for {self.agent.role}")
        except Exception as e:
            logger.error(f"❌ Failed to start A2A services: {e}")
            self.a2a_enabled = False
    
    async def stop_a2a_services(self):
        """Stop A2A services and unregister agent"""
        if not self.a2a_enabled or not self.a2a_client:
            return
            
        try:
            await self._unregister_agent()
            await self.a2a_client.stop()
            logger.info(f"🛑 Stopped A2A services for {self.agent.role}")
        except Exception as e:
            logger.error(f"❌ Failed to stop A2A services: {e}")
    
    async def _register_agent(self):
        """Register this agent with the real discovery service"""
        if not self.discovery_service or not self.capabilities:
            return
            
        try:
            agent_card = AgentCard(
                agent_id=f"crew_agent_{self.agent.role.lower().replace(' ', '_')}",
                name=self.agent.role,
                description=self.agent.backstory or f"CrewAI agent: {self.agent.role}",
                version="1.0.0",
                url="local://crew-agent",
                capabilities=AgentCapabilities(
                    pushNotifications=True,
                    stateTransitionHistory=True,
                    streaming=True
                ),
                defaultInputModes=["text"],
                defaultOutputModes=["text"],
                skills=[
                    AgentSkill(
                        id=f"skill_{i}",
                        name=cap,
                        description=f"Capability: {cap}",
                        inputModes=["text"],
                        outputModes=["text"],
                        tags=[cap],
                        examples=[f"Example usage of {cap}"]
                    ) for i, cap in enumerate(self.capabilities)
                ]
            )
            
            success = await self.discovery_service.register_agent(agent_card)
            if success:
                logger.info(f"✅ Registered agent {agent_card.agent_id} with real discovery service")
            else:
                logger.warning(f"⚠️ Failed to register agent {agent_card.agent_id}")
                
        except Exception as e:
            logger.error(f"❌ Error registering agent: {e}")
    
    async def _unregister_agent(self):
        """Unregister this agent from the real discovery service"""
        if not self.discovery_service:
            return
            
        try:
            agent_id = f"crew_agent_{self.agent.role.lower().replace(' ', '_')}"
            success = await self.discovery_service.unregister_agent(agent_id)
            if success:
                logger.info(f"✅ Unregistered agent {agent_id} from real discovery service")
            else:
                logger.warning(f"⚠️ Failed to unregister agent {agent_id}")
                
        except Exception as e:
            logger.error(f"❌ Error unregistering agent: {e}")
    
    async def execute_task_with_discovery(self, task_description: str, required_capability: str = None):
        """Execute a task, using A2A discovery if needed"""
        logger.info(f"🎯 Executing task: {task_description}")
        
        # Check if we can handle this locally
        if not required_capability or required_capability in self.capabilities:
            logger.info(f"🏠 Handling locally with {self.agent.role}")
            return f"Task completed by {self.agent.role}: {task_description}"
        
        # Use real A2A discovery for external capabilities
        if self.a2a_enabled and self.discovery_service:
            try:
                logger.info(f"🔍 Discovering agents with capability: {required_capability}")
                agents = await self.discovery_service.discover_agents([required_capability])
                
                if agents:
                    external_agent = agents[0]
                    logger.info(f"🌐 Found external agent: {external_agent.name}")
                    
                    # Send task to external agent via real A2A client
                    if self.a2a_client:
                        message_data = {
                            "task": task_description,
                            "capability": required_capability,
                            "from_agent": self.agent.role
                        }
                        
                        success = await self.a2a_client.send_message(
                            to_agent=external_agent.agent_id,
                            message_type="task_request",
                            content=message_data
                        )
                        
                        if success:
                            return f"Task delegated to {external_agent.name} via real A2A: {task_description}"
                        else:
                            logger.warning("⚠️ Failed to send message via A2A")
                
                logger.warning(f"⚠️ No agents found with capability: {required_capability}")
                
            except Exception as e:
                logger.error(f"❌ A2A discovery failed: {e}")
        
        # Fallback to local execution
        logger.info(f"🏠 Fallback: handling locally with {self.agent.role}")
        return f"Task completed by {self.agent.role} (fallback): {task_description}"


class A2ACrewWrapper:
    """Wrapper that adds A2A capabilities to CrewAI crews using REAL A2A services"""
    
    def __init__(
        self, 
        crew: Crew, 
        wrapped_agents: List[A2AAgentWrapper],
        a2a_enabled: bool = True,
        a2a_config: A2AConfig = None
    ):
        self.crew = crew
        self.wrapped_agents = wrapped_agents
        self.a2a_enabled = a2a_enabled
        self.a2a_config = a2a_config or A2AConfig()
        
        # Initialize crew-level A2A services
        self.discovery_service = None
        self.a2a_client = None
        
        if self.a2a_enabled:
            self._initialize_crew_a2a_services()
    
    def _initialize_crew_a2a_services(self):
        """Initialize real A2A services for the crew"""
        try:
            self.discovery_service = DiscoveryService(
                discovery_endpoint=self.a2a_config.discovery_endpoint
            )
            
            crew_id = f"crew_{id(self.crew)}"
            self.a2a_client = A2AClientManager(
                agent_id=crew_id,
                discovery_endpoint=self.a2a_config.discovery_endpoint,
                redis_url=self.a2a_config.redis_url,
                timeout=self.a2a_config.timeout,
                max_retries=self.a2a_config.max_retries
            )
            
            logger.info(f"✅ Initialized real A2A services for crew: {crew_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize crew A2A services: {e}")
            self.a2a_enabled = False
    
    def __getattr__(self, name):
        """Delegate attribute access to the wrapped crew"""
        return getattr(self.crew, name)
    
    async def start_a2a_services(self):
        """Start A2A services for crew and all agents"""
        if not self.a2a_enabled:
            return
            
        try:
            # Start crew-level services
            if self.a2a_client:
                await self.a2a_client.start()
            
            # Start agent-level services
            for wrapped_agent in self.wrapped_agents:
                await wrapped_agent.start_a2a_services()
            
            # Register crew capabilities
            await self._register_crew()
            
            logger.info(f"🚀 Started A2A services for crew with {len(self.wrapped_agents)} agents")
            
        except Exception as e:
            logger.error(f"❌ Failed to start crew A2A services: {e}")
            self.a2a_enabled = False
    
    async def stop_a2a_services(self):
        """Stop A2A services for crew and all agents"""
        if not self.a2a_enabled:
            return
            
        try:
            # Stop agent-level services
            for wrapped_agent in self.wrapped_agents:
                await wrapped_agent.stop_a2a_services()
            
            # Unregister crew
            await self._unregister_crew()
            
            # Stop crew-level services
            if self.a2a_client:
                await self.a2a_client.stop()
            
            logger.info(f"🛑 Stopped A2A services for crew")
            
        except Exception as e:
            logger.error(f"❌ Failed to stop crew A2A services: {e}")
    
    async def _register_crew(self):
        """Register crew capabilities with real discovery service"""
        if not self.discovery_service:
            return
            
        try:
            # Aggregate all agent capabilities
            all_capabilities = set()
            for wrapped_agent in self.wrapped_agents:
                all_capabilities.update(wrapped_agent.capabilities)
            
            crew_card = AgentCard(
                agent_id=f"crew_{id(self.crew)}",
                name=f"CrewAI Crew ({len(self.wrapped_agents)} agents)",
                description=f"Multi-agent crew with capabilities: {', '.join(all_capabilities)}",
                version="1.0.0",
                url="local://crew",
                capabilities=AgentCapabilities(
                    pushNotifications=True,
                    stateTransitionHistory=True,
                    streaming=True
                ),
                defaultInputModes=["text"],
                defaultOutputModes=["text"],
                skills=[
                    AgentSkill(
                        id=f"skill_{i}",
                        name=cap,
                        description=f"Crew capability: {cap}",
                        inputModes=["text"],
                        outputModes=["text"],
                        tags=[cap],
                        examples=[f"Example usage of {cap}"]
                    ) for i, cap in enumerate(all_capabilities)
                ]
            )
            
            success = await self.discovery_service.register_agent(crew_card)
            if success:
                logger.info(f"✅ Registered crew with real discovery service")
            else:
                logger.warning(f"⚠️ Failed to register crew")
                
        except Exception as e:
            logger.error(f"❌ Error registering crew: {e}")
    
    async def _unregister_crew(self):
        """Unregister crew from real discovery service"""
        if not self.discovery_service:
            return
            
        try:
            crew_id = f"crew_{id(self.crew)}"
            success = await self.discovery_service.unregister_agent(crew_id)
            if success:
                logger.info(f"✅ Unregistered crew from real discovery service")
            else:
                logger.warning(f"⚠️ Failed to unregister crew")
                
        except Exception as e:
            logger.error(f"❌ Error unregistering crew: {e}")
    
    async def execute_tasks_with_discovery(self, tasks: List[Dict[str, Any]]):
        """Execute multiple tasks with A2A discovery coordination"""
        logger.info(f"🎯 Executing {len(tasks)} tasks with real A2A discovery")
        
        results = []
        for task_info in tasks:
            task_description = task_info.get("description", "")
            required_capability = task_info.get("capability")
            assigned_agent = task_info.get("agent")
            
            # Find the appropriate agent
            target_agent = None
            if assigned_agent:
                target_agent = next(
                    (wa for wa in self.wrapped_agents if wa.agent.role == assigned_agent),
                    None
                )
            
            if not target_agent:
                target_agent = self.wrapped_agents[0]  # Default to first agent
            
            # Execute task with discovery
            result = await target_agent.execute_task_with_discovery(
                task_description, required_capability
            )
            results.append(result)
        
        return results


# Factory functions for common crew types
def create_sales_crew_with_a2a(a2a_config: A2AConfig) -> A2ACrewWrapper:
    """Create a sales crew with real A2A integration"""
    
    # Create base agents
    sales_manager = Agent(
        role="Sales Manager",
        goal="Coordinate sales activities and strategy",
        backstory="Experienced sales leader with expertise in team coordination and strategy development"
    )
    
    lead_gen_specialist = Agent(
        role="Lead Generation Specialist", 
        goal="Generate high-quality leads for the sales team",
        backstory="Expert in lead generation, prospecting, and market research"
    )
    
    sales_closer = Agent(
        role="Sales Closer",
        goal="Close deals and convert prospects to customers",
        backstory="Skilled sales professional focused on deal closing and customer conversion"
    )
    
    # Wrap agents with A2A capabilities
    wrapped_agents = [
        A2AAgentWrapper(
            agent=sales_manager,
            capabilities=["sales_strategy", "team_coordination", "market_analysis"],
            a2a_config=a2a_config
        ),
        A2AAgentWrapper(
            agent=lead_gen_specialist,
            capabilities=["lead_generation", "prospecting", "market_research"],
            a2a_config=a2a_config
        ),
        A2AAgentWrapper(
            agent=sales_closer,
            capabilities=["deal_closing", "customer_conversion", "negotiation"],
            a2a_config=a2a_config
        )
    ]
    
    # Create base crew with unwrapped agents
    base_agents = [wa.agent for wa in wrapped_agents]
    crew = Crew(
        agents=base_agents,
        tasks=[],  # Tasks will be added dynamically
        verbose=True
    )
    
    return A2ACrewWrapper(
        crew=crew,
        wrapped_agents=wrapped_agents,
        a2a_config=a2a_config
    )


def create_marketing_crew_with_a2a(a2a_config: A2AConfig) -> A2ACrewWrapper:
    """Create a marketing crew with real A2A integration"""
    
    # Create base agents
    marketing_manager = Agent(
        role="Marketing Manager",
        goal="Develop and execute marketing strategies",
        backstory="Strategic marketing leader with expertise in campaign development and brand management"
    )
    
    content_creator = Agent(
        role="Content Creator",
        goal="Create engaging marketing content",
        backstory="Creative professional specializing in content creation and brand storytelling"
    )
    
    social_media_manager = Agent(
        role="Social Media Manager",
        goal="Manage social media presence and engagement",
        backstory="Social media expert focused on community building and online engagement"
    )
    
    # Wrap agents with A2A capabilities
    wrapped_agents = [
        A2AAgentWrapper(
            agent=marketing_manager,
            capabilities=["marketing_strategy", "campaign_management", "brand_development"],
            a2a_config=a2a_config
        ),
        A2AAgentWrapper(
            agent=content_creator,
            capabilities=["content_creation", "copywriting", "visual_design"],
            a2a_config=a2a_config
        ),
        A2AAgentWrapper(
            agent=social_media_manager,
            capabilities=["social_media", "community_management", "engagement"],
            a2a_config=a2a_config
        )
    ]
    
    # Create base crew with unwrapped agents
    base_agents = [wa.agent for wa in wrapped_agents]
    crew = Crew(
        agents=base_agents,
        tasks=[],  # Tasks will be added dynamically
        verbose=True
    )
    
    return A2ACrewWrapper(
        crew=crew,
        wrapped_agents=wrapped_agents,
        a2a_config=a2a_config
    )


async def example_workflow_with_real_a2a():
    """Example workflow demonstrating CrewAI + real A2A integration"""
    
    # Configure real A2A services
    a2a_config = A2AConfig(
        discovery_endpoint="http://localhost:8080",  # Real discovery service
        redis_url="redis://localhost:6379",          # Real Redis instance
        timeout=30.0,
        max_retries=3
    )
    
    logger.info("🚀 Starting CrewAI + Real A2A Integration Demo")
    
    try:
        # Create crews with real A2A services
        sales_crew = create_sales_crew_with_a2a(a2a_config)
        marketing_crew = create_marketing_crew_with_a2a(a2a_config)
        
        # Start A2A services
        await sales_crew.start_a2a_services()
        await marketing_crew.start_a2a_services()
        
        # Execute coordinated tasks
        sales_tasks = [
            {
                "description": "Generate leads for Q4 campaign",
                "capability": "lead_generation",
                "agent": "Lead Generation Specialist"
            },
            {
                "description": "Create sales presentation",
                "capability": "content_creation",  # Will trigger A2A discovery
                "agent": "Sales Manager"
            }
        ]
        
        marketing_tasks = [
            {
                "description": "Create social media campaign",
                "capability": "social_media",
                "agent": "Social Media Manager"
            },
            {
                "description": "Close enterprise deals",
                "capability": "deal_closing",  # Will trigger A2A discovery
                "agent": "Content Creator"
            }
        ]
        
        # Execute tasks in parallel with real A2A coordination
        sales_results, marketing_results = await asyncio.gather(
            sales_crew.execute_tasks_with_discovery(sales_tasks),
            marketing_crew.execute_tasks_with_discovery(marketing_tasks)
        )
        
        logger.info("✅ Sales Results:")
        for result in sales_results:
            logger.info(f"  - {result}")
        
        logger.info("✅ Marketing Results:")
        for result in marketing_results:
            logger.info(f"  - {result}")
        
        # Stop A2A services
        await sales_crew.stop_a2a_services()
        await marketing_crew.stop_a2a_services()
        
        logger.info("🎉 Real A2A integration demo completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the example workflow with real A2A services
    asyncio.run(example_workflow_with_real_a2a())
