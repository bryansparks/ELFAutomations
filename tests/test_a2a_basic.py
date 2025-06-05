#!/usr/bin/env python3
"""
Basic test for A2A SDK integration without dependency conflicts.
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_a2a")

async def test_a2a_import():
    """Test basic A2A SDK import and functionality."""
    try:
        # Test A2A imports
        from a2a.types import AgentCard, AgentCapabilities
        logger.info("✅ A2A SDK imported successfully")
        
        # Test AgentCard creation with proper structure
        capabilities = AgentCapabilities(
            pushNotifications=False,
            stateTransitionHistory=False,
            streaming=False
        )
        
        agent_card = AgentCard(
            name="Test Agent",
            description="A test agent for validation",
            version="1.0.0",
            url="http://localhost:8081",
            capabilities=capabilities,
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[]
        )
        
        logger.info(f"✅ AgentCard created: {agent_card.name}")
        
        # Test CrewAI import
        from crewai import Agent, Task, Crew
        logger.info("✅ CrewAI imported successfully")
        
        # Create a simple CrewAI agent
        test_agent = Agent(
            role="Test Agent",
            goal="Test CrewAI functionality",
            backstory="A simple test agent",
            verbose=True
        )
        
        logger.info(f"✅ CrewAI Agent created: {test_agent.role}")
        
        # Test task creation
        test_task = Task(
            description="Say hello world",
            agent=test_agent,
            expected_output="A greeting message"
        )
        
        logger.info(f"✅ CrewAI Task created: {test_task.description}")
        
        # Create crew
        crew = Crew(
            agents=[test_agent],
            tasks=[test_task],
            verbose=True
        )
        
        logger.info("✅ CrewAI Crew created successfully")
        
        # Execute the task
        logger.info("🚀 Executing test task...")
        result = crew.kickoff()
        
        logger.info(f"✅ Task completed: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_a2a_import())
    if success:
        print("🎉 A2A and CrewAI integration test passed!")
    else:
        print("❌ A2A and CrewAI integration test failed!")
        exit(1)
