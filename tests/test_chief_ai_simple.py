#!/usr/bin/env python3
"""
Simple test for Chief AI Agent - isolating dependency issues.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_imports():
    """Test basic imports step by step."""
    try:
        logger.info("Testing basic Python imports...")
        
        # Test pydantic
        logger.info("Testing pydantic...")
        from pydantic import BaseModel, Field
        logger.info("✅ Pydantic imported")
        
        # Test CrewAI
        logger.info("Testing CrewAI...")
        from crewai import Agent, Task, Crew
        logger.info("✅ CrewAI imported")
        
        # Test A2A SDK (this might be the issue)
        logger.info("Testing A2A SDK...")
        try:
            from a2a.types import AgentCard, AgentCapabilities, AgentSkill
            from a2a.client import A2AClient
            from a2a.server import A2AServer
            logger.info("✅ A2A SDK imported")
        except ImportError as e:
            logger.warning(f"⚠️ A2A SDK not available: {e}")
            logger.info("Will create mock A2A classes for testing...")
            
            # Create mock A2A classes
            class AgentCard:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            
            class AgentCapabilities:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            
            class AgentSkill:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            
            # Make them available globally
            sys.modules['a2a'] = type('MockModule', (), {})()
            sys.modules['a2a.types'] = type('MockModule', (), {
                'AgentCard': AgentCard,
                'AgentCapabilities': AgentCapabilities, 
                'AgentSkill': AgentSkill
            })()
            sys.modules['a2a.client'] = type('MockModule', (), {'A2AClient': object})()
            sys.modules['a2a.server'] = type('MockModule', (), {'A2AServer': object})()
        
        # Test distributed agent base imports
        logger.info("Testing distributed agent base...")
        from agents.distributed.base.distributed_agent import AgentConfig
        logger.info("✅ AgentConfig imported")
        
        # Test Chief AI Agent
        logger.info("Testing Chief AI Agent...")
        from agents.distributed.examples.chief_ai_agent import ChiefAIAgent
        logger.info("✅ Chief AI Agent imported")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_creation():
    """Test creating the agent."""
    try:
        logger.info("Testing agent creation...")
        
        from agents.distributed.base.distributed_agent import AgentConfig
        from agents.distributed.examples.chief_ai_agent import ChiefAIAgent
        
        # Create simple config
        config = AgentConfig(
            agent_id="test-chief",
            role="CEO",
            goal="Test leadership",
            backstory="Test agent",
            department="executive"
        )
        
        # Create agent
        agent = ChiefAIAgent(config)
        logger.info(f"✅ Agent created: {agent.config.agent_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🔍 Running simple Chief AI Agent test...")
    
    success = True
    success &= test_basic_imports()
    success &= test_agent_creation()
    
    if success:
        logger.info("🎉 Simple test passed!")
    else:
        logger.error("❌ Simple test failed!")
    
    sys.exit(0 if success else 1)
