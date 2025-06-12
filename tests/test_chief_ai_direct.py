#!/usr/bin/env python3
"""
Direct test for Chief AI Agent - bypassing old LangChain imports.
"""

import logging
import os
import sys

# Add the project root to Python path
sys.path.insert(0, "/Users/bryansparks/projects/ELFAutomations")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_direct_imports():
    """Test direct imports without going through agents.__init__.py"""
    try:
        logger.info("Testing direct imports...")

        # Test pydantic
        from pydantic import BaseModel, Field

        logger.info("✅ Pydantic imported")

        # Test CrewAI
        from crewai import Agent, Crew, Task

        logger.info("✅ CrewAI imported")

        # Import directly from the distributed agent file
        logger.info("Testing direct distributed agent import...")
        sys.path.insert(
            0, "/Users/bryansparks/projects/ELFAutomations/agents/distributed/base"
        )
        from distributed_agent import AgentConfig, DistributedCrewAIAgent

        logger.info("✅ DistributedCrewAIAgent imported directly")

        return AgentConfig, DistributedCrewAIAgent

    except Exception as e:
        logger.error(f"❌ Direct import failed: {e}")
        import traceback

        traceback.print_exc()
        return None, None


def test_chief_ai_direct():
    """Test Chief AI Agent with direct imports."""
    try:
        logger.info("Testing Chief AI Agent direct import...")

        # Import the Chief AI Agent directly
        sys.path.insert(
            0, "/Users/bryansparks/projects/ELFAutomations/agents/distributed/examples"
        )

        # We need to create a minimal version first
        logger.info("Creating minimal Chief AI Agent test...")

        # Test basic CrewAI agent creation
        from crewai import Agent

        test_agent = Agent(
            role="Test CEO",
            goal="Test executive functions",
            backstory="A test executive agent",
            verbose=True,
        )

        logger.info(f"✅ CrewAI Agent created: {test_agent.role}")

        return test_agent

    except Exception as e:
        logger.error(f"❌ Chief AI direct test failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_crewai_task_execution():
    """Test CrewAI task execution."""
    try:
        logger.info("Testing CrewAI task execution...")

        from crewai import Agent, Crew, Task

        # Create a simple agent
        executive_agent = Agent(
            role="Chief Executive Officer",
            goal="Provide strategic leadership and make executive decisions",
            backstory="An experienced executive leader with strategic planning expertise",
            verbose=True,
            allow_delegation=False,
        )

        # Create a simple task
        strategic_task = Task(
            description="Analyze the current business situation and provide 3 strategic recommendations for growth",
            agent=executive_agent,
            expected_output="A list of 3 strategic recommendations with brief explanations",
        )

        # Create crew and execute
        executive_crew = Crew(
            agents=[executive_agent], tasks=[strategic_task], verbose=True
        )

        logger.info("Executing CrewAI task...")
        result = executive_crew.kickoff()

        logger.info("✅ CrewAI task execution successful")
        logger.info(f"Result preview: {str(result)[:100]}...")

        return result

    except Exception as e:
        logger.error(f"❌ CrewAI task execution failed: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    logger.info("🔍 Running direct Chief AI Agent test...")

    success = True

    # Test 1: Direct imports
    AgentConfig, DistributedCrewAIAgent = test_direct_imports()
    if AgentConfig is None:
        success = False

    # Test 2: Chief AI direct
    chief_agent = test_chief_ai_direct()
    if chief_agent is None:
        success = False

    # Test 3: CrewAI task execution
    task_result = test_crewai_task_execution()
    if task_result is None:
        success = False

    if success:
        logger.info("🎉 Direct test passed! CrewAI is working.")
        logger.info("✅ Ready to proceed with Chief AI Agent implementation")
    else:
        logger.error("❌ Direct test failed!")

    sys.exit(0 if success else 1)
