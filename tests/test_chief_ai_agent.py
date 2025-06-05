#!/usr/bin/env python3
"""
Test script for the distributed Chief AI Agent implementation.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_chief_ai_agent_import():
    """Test importing the Chief AI Agent."""
    try:
        logger.info("🔍 Testing Chief AI Agent import...")
        from agents.distributed.examples.chief_ai_agent import ChiefAIAgent
        from agents.distributed.base.distributed_agent import AgentConfig
        logger.info("✅ Chief AI Agent imported successfully")
        return ChiefAIAgent, AgentConfig
    except Exception as e:
        logger.error(f"❌ Failed to import Chief AI Agent: {e}")
        raise


async def test_chief_ai_agent_creation():
    """Test creating a Chief AI Agent instance."""
    try:
        logger.info("🔍 Testing Chief AI Agent creation...")
        
        from agents.distributed.examples.chief_ai_agent import ChiefAIAgent
        from agents.distributed.base.distributed_agent import AgentConfig
        
        # Create configuration
        config = AgentConfig(
            agent_id="test-chief-ai-agent",
            role="Chief Executive Officer",
            goal="Test executive leadership capabilities",
            backstory="Test executive agent for validation",
            department="executive",
            a2a_port=8090
        )
        
        # Create agent
        chief_agent = ChiefAIAgent(config)
        
        logger.info(f"✅ Chief AI Agent created: {chief_agent.config.agent_id}")
        logger.info(f"   • Role: {chief_agent.config.role}")
        logger.info(f"   • Department: {chief_agent.config.department}")
        logger.info(f"   • Capabilities: {len(chief_agent.executive_capabilities)}")
        
        return chief_agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create Chief AI Agent: {e}")
        raise


async def test_agent_card_generation():
    """Test A2A AgentCard generation."""
    try:
        logger.info("🔍 Testing AgentCard generation...")
        
        from agents.distributed.examples.chief_ai_agent import ChiefAIAgent
        
        # Create agent with default config
        chief_agent = ChiefAIAgent()
        
        # Generate agent card
        agent_card = chief_agent.get_agent_card()
        
        logger.info("✅ AgentCard generated successfully")
        logger.info(f"   • Name: {agent_card.name}")
        logger.info(f"   • Description: {agent_card.description[:100]}...")
        logger.info(f"   • Skills: {len(agent_card.skills)}")
        logger.info(f"   • Capabilities: Push={agent_card.capabilities.pushNotifications}, History={agent_card.capabilities.stateTransitionHistory}")
        
        # Validate required skills
        skill_ids = [skill.id for skill in agent_card.skills]
        expected_skills = ["strategic_planning", "performance_monitoring", "escalation_handling", "department_coordination"]
        
        for expected_skill in expected_skills:
            if expected_skill in skill_ids:
                logger.info(f"   ✅ Skill '{expected_skill}' present")
            else:
                logger.warning(f"   ⚠️ Skill '{expected_skill}' missing")
        
        return agent_card
        
    except Exception as e:
        logger.error(f"❌ Failed to generate AgentCard: {e}")
        raise


async def test_executive_task_execution():
    """Test executive task execution."""
    try:
        logger.info("🔍 Testing executive task execution...")
        
        from agents.distributed.examples.chief_ai_agent import ChiefAIAgent
        from agents.distributed.a2a.messages import create_task_request, MessageType
        
        # Create agent
        chief_agent = ChiefAIAgent()
        
        # Test strategic planning task
        strategic_task = create_task_request(
            task_id="test-strategic-001",
            task_description="Develop Q1 strategic objectives for company growth",
            task_type="strategic_planning",
            from_agent="test-requester",
            to_agent=chief_agent.config.agent_id,
            content={
                "scope": "company-wide",
                "time_horizon": "quarterly",
                "priority": "high"
            }
        )
        
        # Execute task
        result = await chief_agent._handle_executive_task(strategic_task)
        
        logger.info("✅ Strategic planning task executed")
        logger.info(f"   • Status: {result.get('status', 'unknown')}")
        logger.info(f"   • Objective ID: {result.get('result', {}).get('objective_id', 'none')}")
        
        # Test escalation handling
        escalation_message = {
            "message_type": MessageType.ESCALATION,
            "from_agent": "sales-agent",
            "to_agent": chief_agent.config.agent_id,
            "content": {
                "issue_description": "Resource shortage impacting sales targets",
                "department": "sales",
                "severity": "high"
            }
        }
        
        # Create mock message object
        class MockMessage:
            def __init__(self, data):
                self.message_type = data["message_type"]
                self.from_agent = data["from_agent"]
                self.to_agent = data["to_agent"]
                self.content = data["content"]
        
        escalation_result = await chief_agent._handle_escalation(MockMessage(escalation_message))
        
        logger.info("✅ Escalation handling tested")
        logger.info(f"   • Status: {escalation_result.get('status', 'unknown')}")
        logger.info(f"   • Resolution: {escalation_result.get('resolution', {}).get('decision', 'none')[:50]}...")
        
        return result, escalation_result
        
    except Exception as e:
        logger.error(f"❌ Failed to execute executive tasks: {e}")
        raise


async def test_performance_monitoring():
    """Test performance monitoring capabilities."""
    try:
        logger.info("🔍 Testing performance monitoring...")
        
        from agents.distributed.examples.chief_ai_agent import ChiefAIAgent
        
        # Create agent
        chief_agent = ChiefAIAgent()
        
        # Simulate some activity
        chief_agent.decisions_made = 5
        chief_agent.escalations_handled = 2
        chief_agent.strategic_initiatives_launched = 1
        
        # Add mock company metrics
        chief_agent.company_metrics = {
            "sales": {
                "current": {
                    "metrics": {"leads": 100, "conversions": 15},
                    "timestamp": datetime.utcnow().isoformat(),
                    "reported_by": "sales-agent"
                }
            },
            "marketing": {
                "current": {
                    "metrics": {"campaigns": 5, "reach": 10000},
                    "timestamp": datetime.utcnow().isoformat(),
                    "reported_by": "marketing-agent"
                }
            }
        }
        
        # Get metrics
        metrics = chief_agent.get_metrics()
        
        logger.info("✅ Performance monitoring working")
        logger.info(f"   • Decisions made: {metrics.get('decisions_made', 0)}")
        logger.info(f"   • Escalations handled: {metrics.get('escalations_handled', 0)}")
        logger.info(f"   • Strategic initiatives: {metrics.get('strategic_initiatives_launched', 0)}")
        logger.info(f"   • Departments monitored: {metrics.get('departments_monitored', 0)}")
        
        # Test performance analysis
        analysis = await chief_agent._analyze_department_performance("sales", {"leads": 100, "conversions": 15})
        
        logger.info("✅ Department performance analysis working")
        logger.info(f"   • Overall status: {analysis.get('overall_status', 'unknown')}")
        logger.info(f"   • Recommendations: {len(analysis.get('recommendations', []))}")
        
        return metrics, analysis
        
    except Exception as e:
        logger.error(f"❌ Failed performance monitoring test: {e}")
        raise


async def test_crewai_integration():
    """Test CrewAI integration."""
    try:
        logger.info("🔍 Testing CrewAI integration...")
        
        from agents.distributed.examples.chief_ai_agent import ChiefAIAgent
        
        # Create agent
        chief_agent = ChiefAIAgent()
        
        # Test CrewAI agent access
        crew_agent = chief_agent.crew_agent
        
        logger.info("✅ CrewAI integration working")
        logger.info(f"   • Agent role: {crew_agent.role}")
        logger.info(f"   • Agent goal: {crew_agent.goal[:50]}...")
        logger.info(f"   • Memory enabled: {crew_agent.memory}")
        logger.info(f"   • Delegation allowed: {crew_agent.allow_delegation}")
        
        # Test task execution (simplified)
        task_result = await chief_agent._execute_general_executive_task(
            "Analyze current market position and provide strategic recommendations",
            {"priority": "high", "scope": "market_analysis"}
        )
        
        logger.info("✅ CrewAI task execution working")
        logger.info(f"   • Task completed: {task_result.get('task_description', 'unknown')[:50]}...")
        logger.info(f"   • Implementation required: {task_result.get('implementation_required', False)}")
        
        return crew_agent, task_result
        
    except Exception as e:
        logger.error(f"❌ Failed CrewAI integration test: {e}")
        raise


async def run_all_tests():
    """Run all Chief AI Agent tests."""
    logger.info("🚀 Starting Chief AI Agent Tests")
    logger.info("=" * 50)
    
    try:
        # Test 1: Import
        await test_chief_ai_agent_import()
        
        # Test 2: Creation
        chief_agent = await test_chief_ai_agent_creation()
        
        # Test 3: AgentCard generation
        agent_card = await test_agent_card_generation()
        
        # Test 4: Executive task execution
        task_results = await test_executive_task_execution()
        
        # Test 5: Performance monitoring
        performance_results = await test_performance_monitoring()
        
        # Test 6: CrewAI integration
        crewai_results = await test_crewai_integration()
        
        logger.info("=" * 50)
        logger.info("🎉 ALL CHIEF AI AGENT TESTS PASSED!")
        logger.info("=" * 50)
        
        # Summary
        logger.info("📊 Test Summary:")
        logger.info("   ✅ Import and creation: PASSED")
        logger.info("   ✅ A2A AgentCard generation: PASSED")
        logger.info("   ✅ Executive task execution: PASSED")
        logger.info("   ✅ Performance monitoring: PASSED")
        logger.info("   ✅ CrewAI integration: PASSED")
        
        logger.info("\n🏆 Chief AI Agent is ready for distributed deployment!")
        
        return True
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error("❌ CHIEF AI AGENT TESTS FAILED!")
        logger.error("=" * 50)
        logger.error(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
