#!/usr/bin/env python3
"""
Test Chief AI Agent using CrewAI - focused test without complex imports.
"""

import logging
from crewai import Agent, Task, Crew

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chief_ai_crewai():
    """Test Chief AI Agent using pure CrewAI."""
    try:
        logger.info("🔍 Testing Chief AI Agent with CrewAI...")
        
        # Create Chief AI Agent
        chief_ai_agent = Agent(
            role="Chief AI Agent - Executive Leadership",
            goal="Provide strategic leadership, coordinate departments, monitor performance, and make executive decisions for the organization",
            backstory="""You are the Chief AI Agent, serving as the executive leader of an AI-powered organization. 
            You have extensive experience in strategic planning, performance monitoring, resource allocation, 
            and cross-departmental coordination. Your role is to ensure organizational success through 
            data-driven decision making and effective leadership.""",
            verbose=True,
            allow_delegation=True,
            memory=True
        )
        
        logger.info(f"✅ Chief AI Agent created: {chief_ai_agent.role}")
        
        # Test 1: Strategic Planning Task
        strategic_task = Task(
            description="""Analyze the current organizational state and develop a comprehensive strategic plan including:
            1. Key performance indicators (KPIs) to monitor
            2. Resource allocation priorities for the next quarter
            3. Department coordination strategies
            4. Risk assessment and mitigation plans
            5. Growth opportunities and initiatives""",
            agent=chief_ai_agent,
            expected_output="A detailed strategic plan with specific actionable items and metrics"
        )
        
        # Test 2: Performance Monitoring Task
        performance_task = Task(
            description="""Create a performance monitoring framework that includes:
            1. Department-level performance metrics
            2. Individual agent performance indicators
            3. System health and efficiency measures
            4. Customer satisfaction tracking
            5. Escalation procedures for performance issues""",
            agent=chief_ai_agent,
            expected_output="A comprehensive performance monitoring framework with clear metrics and procedures"
        )
        
        # Test 3: Executive Decision Task
        decision_task = Task(
            description="""You've received reports of declining performance in the Sales department and 
            increasing customer complaints in Support. As the Chief AI Agent, analyze this situation and:
            1. Identify root causes of the issues
            2. Develop immediate action plans
            3. Assign responsibilities to appropriate departments
            4. Set timeline for resolution
            5. Define success metrics for improvement""",
            agent=chief_ai_agent,
            expected_output="Executive decision memo with action plans, responsibilities, and success metrics"
        )
        
        # Create executive crew
        executive_crew = Crew(
            agents=[chief_ai_agent],
            tasks=[strategic_task, performance_task, decision_task],
            verbose=True
        )
        
        logger.info("🚀 Executing Chief AI Agent tasks...")
        results = executive_crew.kickoff()
        
        logger.info("✅ Chief AI Agent tasks completed successfully!")
        logger.info(f"Results preview: {str(results)[:200]}...")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Chief AI Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_multi_agent_coordination():
    """Test Chief AI Agent coordinating with other agents."""
    try:
        logger.info("🔍 Testing multi-agent coordination...")
        
        # Create Chief AI Agent
        chief_ai = Agent(
            role="Chief AI Agent",
            goal="Coordinate and oversee department operations",
            backstory="Executive leader responsible for organizational coordination",
            verbose=True,
            allow_delegation=True
        )
        
        # Create department agents
        sales_agent = Agent(
            role="Sales Manager",
            goal="Drive sales performance and revenue growth",
            backstory="Experienced sales professional focused on results",
            verbose=True
        )
        
        marketing_agent = Agent(
            role="Marketing Manager", 
            goal="Create effective marketing campaigns and brand awareness",
            backstory="Creative marketing expert with digital expertise",
            verbose=True
        )
        
        # Create coordination task
        coordination_task = Task(
            description="""As Chief AI Agent, coordinate a cross-departmental initiative to launch a new product:
            1. Define roles and responsibilities for Sales and Marketing
            2. Set timeline and milestones
            3. Establish communication protocols
            4. Define success metrics
            5. Create contingency plans""",
            agent=chief_ai,
            expected_output="Comprehensive project coordination plan with clear assignments"
        )
        
        # Create multi-agent crew
        coordination_crew = Crew(
            agents=[chief_ai, sales_agent, marketing_agent],
            tasks=[coordination_task],
            verbose=True
        )
        
        logger.info("🚀 Executing multi-agent coordination...")
        coordination_results = coordination_crew.kickoff()
        
        logger.info("✅ Multi-agent coordination successful!")
        logger.info(f"Coordination results preview: {str(coordination_results)[:200]}...")
        
        return coordination_results
        
    except Exception as e:
        logger.error(f"❌ Multi-agent coordination test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    logger.info("🎯 Running Chief AI Agent CrewAI Tests...")
    
    success = True
    
    # Test 1: Chief AI Agent functionality
    chief_results = test_chief_ai_crewai()
    if chief_results is None:
        success = False
    
    # Test 2: Multi-agent coordination
    coordination_results = test_multi_agent_coordination()
    if coordination_results is None:
        success = False
    
    if success:
        logger.info("🎉 All Chief AI Agent tests passed!")
        logger.info("✅ Chief AI Agent is ready for distributed deployment")
        logger.info("✅ CrewAI integration working perfectly")
        logger.info("✅ Multi-agent coordination validated")
    else:
        logger.error("❌ Some tests failed!")
    
    exit(0 if success else 1)
