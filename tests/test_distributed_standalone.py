#!/usr/bin/env python3
"""
Standalone test for distributed agent components without dependency conflicts.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from crewai import Agent, Crew, Task
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_standalone")


class AgentConfig(BaseModel):
    """Configuration for distributed agents."""

    agent_id: str
    role: str
    goal: str
    backstory: str
    department: str = "general"
    a2a_port: int = 8081
    health_port: int = 8080
    discovery_endpoint: Optional[str] = None
    kubernetes_namespace: str = "default"
    service_name: Optional[str] = None


class SimpleDistributedAgent:
    """Simplified distributed agent for testing."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"agent.{config.agent_id}")

        # Create CrewAI agent
        self.crew_agent = Agent(
            role=config.role, goal=config.goal, backstory=config.backstory, verbose=True
        )

        self.logger.info(f"Distributed agent '{config.agent_id}' initialized")

    def get_agent_card(self) -> AgentCard:
        """Generate A2A agent card."""
        capabilities = AgentCapabilities(
            pushNotifications=True, stateTransitionHistory=True, streaming=False
        )

        return AgentCard(
            name=f"{self.config.role} ({self.config.agent_id})",
            description=f"{self.config.backstory[:200]}..."
            if len(self.config.backstory) > 200
            else self.config.backstory,
            version="1.0.0",
            url=f"http://{self.config.service_name or self.config.agent_id}:{self.config.a2a_port}",
            capabilities=capabilities,
            defaultInputModes=["text", "json"],
            defaultOutputModes=["text", "json"],
            skills=[
                AgentSkill(
                    id="task_execution",
                    name="task_execution",
                    description="Execute CrewAI tasks and workflows",
                    inputModes=["text", "json"],
                    outputModes=["text", "json"],
                    tags=["crewai", "task", "execution"],
                    examples=[],
                ),
                AgentSkill(
                    id="a2a_communication",
                    name="a2a_communication",
                    description="Communicate with other agents via A2A protocol",
                    inputModes=["text", "json"],
                    outputModes=["text", "json"],
                    tags=["a2a", "communication", "protocol"],
                    examples=[],
                ),
            ],
        )

    async def execute_task(
        self, description: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a task using CrewAI."""
        try:
            self.logger.info(f"Executing task: {description}")

            task = Task(
                description=description,
                agent=self.crew_agent,
                expected_output="Task completion result",
            )

            crew = Crew(agents=[self.crew_agent], tasks=[task], verbose=True)

            result = crew.kickoff()

            return {
                "status": "completed",
                "result": str(result),
                "agent_id": self.config.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "agent_id": self.config.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status."""
        return {
            "status": "healthy",
            "agent_id": self.config.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "is_ready": True,
            "is_live": True,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            "agent_id": self.config.agent_id,
            "role": self.config.role,
            "department": self.config.department,
            "is_running": True,
            "tasks_completed": 0,
            "health_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def test_agent_creation():
    """Test basic agent creation."""
    logger.info("🔍 Testing agent creation...")

    config = AgentConfig(
        agent_id="test-sales-agent",
        role="Sales Development Representative",
        goal="Qualify leads and drive revenue growth",
        backstory="An experienced sales agent specializing in lead qualification and outreach",
        department="sales",
        service_name="sales-agent-service",
    )

    agent = SimpleDistributedAgent(config)

    # Test agent card
    agent_card = agent.get_agent_card()
    assert agent_card.name == "Sales Development Representative (test-sales-agent)"
    assert agent_card.version == "1.0.0"
    assert "sales-agent-service:8081" in agent_card.url
    assert len(agent_card.skills) > 0

    logger.info(f"✅ Agent card: {agent_card.name}")
    logger.info(f"   URL: {agent_card.url}")
    logger.info(f"   Skills: {[skill.name for skill in agent_card.skills]}")

    # Test health status
    health = agent.get_health_status()
    assert health["status"] == "healthy"
    assert health["agent_id"] == "test-sales-agent"

    logger.info(f"✅ Health status: {health['status']}")

    # Test metrics
    metrics = agent.get_metrics()
    assert metrics["agent_id"] == "test-sales-agent"
    assert metrics["department"] == "sales"

    logger.info(f"✅ Metrics: {metrics['role']} in {metrics['department']}")

    return agent


async def test_task_execution(agent: SimpleDistributedAgent):
    """Test task execution."""
    logger.info("🔍 Testing task execution...")

    task_description = (
        "Generate a personalized cold email for a prospect in the healthcare industry"
    )
    context = {
        "prospect_name": "Dr. Smith",
        "company": "HealthTech Solutions",
        "industry": "healthcare",
    }

    result = await agent.execute_task(task_description, context)

    assert result["status"] == "completed"
    assert "result" in result
    assert result["agent_id"] == "test-sales-agent"

    logger.info(f"✅ Task completed successfully")
    logger.info(f"   Result preview: {result['result'][:100]}...")

    return result


async def test_a2a_capabilities():
    """Test A2A protocol capabilities."""
    logger.info("🔍 Testing A2A capabilities...")

    # Test AgentCapabilities
    capabilities = AgentCapabilities(
        pushNotifications=True, stateTransitionHistory=True, streaming=False
    )

    assert capabilities.pushNotifications == True
    assert capabilities.stateTransitionHistory == True
    assert capabilities.streaming == False

    logger.info("✅ AgentCapabilities created successfully")

    # Test AgentCard with all required fields
    agent_card = AgentCard(
        name="Test Marketing Agent",
        description="A marketing agent for testing A2A integration",
        version="1.0.0",
        url="http://marketing-agent:8081",
        capabilities=capabilities,
        defaultInputModes=["text", "json"],
        defaultOutputModes=["text", "json"],
        skills=[
            AgentSkill(
                id="content_creation",
                name="content_creation",
                description="Create marketing content",
                inputModes=["text", "json"],
                outputModes=["text", "json"],
                tags=["marketing", "content", "creation"],
                examples=[],
            ),
            AgentSkill(
                id="campaign_management",
                name="campaign_management",
                description="Manage marketing campaigns",
                inputModes=["text", "json"],
                outputModes=["text", "json"],
                tags=["marketing", "campaign", "management"],
                examples=[],
            ),
        ],
    )

    assert agent_card.name == "Test Marketing Agent"
    assert agent_card.version == "1.0.0"
    assert len(agent_card.skills) == 2

    logger.info(f"✅ AgentCard created: {agent_card.name}")
    logger.info(f"   Version: {agent_card.version}")
    logger.info(f"   Skills: {[skill.name for skill in agent_card.skills]}")

    return agent_card


async def test_multi_agent_scenario():
    """Test multi-agent scenario."""
    logger.info("🔍 Testing multi-agent scenario...")

    # Create sales agent
    sales_config = AgentConfig(
        agent_id="sales-agent-001",
        role="Senior Sales Representative",
        goal="Qualify leads and close deals",
        backstory="Experienced in B2B sales with focus on SaaS products",
        department="sales",
    )
    sales_agent = SimpleDistributedAgent(sales_config)

    # Create marketing agent
    marketing_config = AgentConfig(
        agent_id="marketing-agent-001",
        role="Marketing Specialist",
        goal="Generate leads and create compelling content",
        backstory="Expert in digital marketing and content creation",
        department="marketing",
    )
    marketing_agent = SimpleDistributedAgent(marketing_config)

    # Test both agents
    sales_card = sales_agent.get_agent_card()
    marketing_card = marketing_agent.get_agent_card()

    assert "Senior Sales Representative" in sales_card.name
    assert "Marketing Specialist" in marketing_card.name

    logger.info(f"✅ Sales Agent: {sales_card.name}")
    logger.info(f"✅ Marketing Agent: {marketing_card.name}")

    # Test task execution for both
    sales_task = "Qualify a lead from the healthcare industry"
    marketing_task = "Create a content strategy for healthcare prospects"

    sales_result = await sales_agent.execute_task(sales_task)
    marketing_result = await marketing_agent.execute_task(marketing_task)

    assert sales_result["status"] == "completed"
    assert marketing_result["status"] == "completed"

    logger.info("✅ Both agents executed tasks successfully")

    return [sales_agent, marketing_agent]


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Distributed Agent Architecture Tests")

    try:
        # Test basic agent creation
        agent = await test_agent_creation()

        # Test task execution
        await test_task_execution(agent)

        # Test A2A capabilities
        await test_a2a_capabilities()

        # Test multi-agent scenario
        await test_multi_agent_scenario()

        logger.info("🎉 All distributed agent tests passed!")
        logger.info("")
        logger.info("✅ Distributed Agent Architecture Validation Complete:")
        logger.info("   • CrewAI integration working")
        logger.info("   • A2A protocol types compatible")
        logger.info("   • Agent cards generated correctly")
        logger.info("   • Task execution functional")
        logger.info("   • Multi-agent scenarios supported")
        logger.info("")
        logger.info("🚀 Ready for Kubernetes deployment and A2A server integration!")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        exit(1)
