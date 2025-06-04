"""
Demo Agent Implementation using LangGraph Foundation

This demonstrates the TASK-005 pattern for all future agents:
- LangGraph for stateful workflows
- kagent for Kubernetes deployment
- MCP via agentgateway.dev for tool access
"""

import asyncio
from typing import Dict, Any

from agents.langgraph_base import LangGraphBaseAgent


class DemoAgent(LangGraphBaseAgent):
    """
    Demonstration agent implementing the TASK-005 foundational pattern.
    
    This agent serves as a reference implementation showing how all future
    agents should be structured using the established technology stack.
    """
    
    def __init__(
        self,
        agent_id: str = "demo-agent-001",
        name: str = "Demo Agent",
        department: str = "demonstration",
        gateway_url: str = "https://agentgateway.dev",
        gateway_api_key: str = None
    ):
        system_prompt = """You are a demonstration AI agent for the Virtual AI Company Platform.

Your role is to showcase the foundational agent architecture using:
- LangGraph for stateful, graph-based workflows
- kagent for Kubernetes-native deployment
- MCP (Model Context Protocol) for standardized tool integration
- agentgateway.dev for centralized tool access

You can help with:
1. Demonstrating agent capabilities
2. Testing the infrastructure
3. Validating the technology stack
4. Providing examples for future agent development

Always be helpful, clear, and demonstrate best practices for agent behavior.
When you need to use tools, explain what you're doing and why.
"""
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            department=department,
            system_prompt=system_prompt,
            gateway_url=gateway_url,
            gateway_api_key=gateway_api_key
        )
    
    async def _startup_tasks(self) -> None:
        """Demo agent startup tasks."""
        self.logger.info("Demo agent performing startup tasks")
        
        # Simulate startup initialization
        await asyncio.sleep(0.1)
        
        # Log available capabilities
        self.logger.info(
            "Demo agent capabilities initialized",
            capabilities=[
                "LangGraph workflow demonstration",
                "MCP tool integration via agentgateway",
                "kagent lifecycle management",
                "Infrastructure testing"
            ]
        )
    
    async def _shutdown_tasks(self) -> None:
        """Demo agent shutdown tasks."""
        self.logger.info("Demo agent performing shutdown tasks")
        
        # Simulate graceful shutdown
        await asyncio.sleep(0.1)
        
        self.logger.info("Demo agent shutdown tasks completed")
    
    async def _cleanup_resources(self) -> None:
        """Demo agent resource cleanup."""
        self.logger.info("Demo agent cleaning up resources")
        
        # Cleanup any demo-specific resources
        await asyncio.sleep(0.1)
        
        self.logger.info("Demo agent resource cleanup completed")
    
    async def demonstrate_workflow(self, task_description: str) -> Dict[str, Any]:
        """
        Demonstrate the LangGraph workflow with a specific task.
        
        Args:
            task_description: Description of the task to demonstrate
            
        Returns:
            Workflow execution result
        """
        self.logger.info("Demonstrating workflow", task=task_description)
        
        try:
            # Process the task through the LangGraph workflow
            result = await self.process_message(
                f"Please demonstrate: {task_description}"
            )
            
            self.logger.info("Workflow demonstration completed successfully")
            return result
            
        except Exception as e:
            self.logger.error("Workflow demonstration failed", error=str(e))
            raise
    
    async def test_mcp_integration(self) -> Dict[str, Any]:
        """
        Test MCP integration through agentgateway.
        
        Returns:
            Test results
        """
        self.logger.info("Testing MCP integration through agentgateway")
        
        try:
            result = await self.process_message(
                "Please test the MCP tool integration by listing available tools and demonstrating a tool call."
            )
            
            self.logger.info("MCP integration test completed")
            return result
            
        except Exception as e:
            self.logger.error("MCP integration test failed", error=str(e))
            raise
    
    async def validate_infrastructure(self) -> Dict[str, Any]:
        """
        Validate the complete infrastructure stack.
        
        Returns:
            Validation results
        """
        self.logger.info("Validating infrastructure stack")
        
        validation_results = {
            "langgraph_workflow": False,
            "mcp_connectivity": False,
            "agentgateway_access": False,
            "kagent_lifecycle": False,
            "overall_status": "unknown"
        }
        
        try:
            # Test LangGraph workflow
            workflow_result = await self.process_message(
                "Validate that the LangGraph workflow is functioning correctly."
            )
            validation_results["langgraph_workflow"] = True
            
            # Test MCP connectivity (this would be more comprehensive in practice)
            mcp_result = await self.test_mcp_integration()
            validation_results["mcp_connectivity"] = True
            validation_results["agentgateway_access"] = True
            
            # Test kagent lifecycle
            health_check = self.get_health_check()
            validation_results["kagent_lifecycle"] = health_check.status.value in ["running", "created"]
            
            # Overall status
            all_tests_passed = all(validation_results[key] for key in validation_results if key != "overall_status")
            validation_results["overall_status"] = "passed" if all_tests_passed else "failed"
            
            self.logger.info("Infrastructure validation completed", results=validation_results)
            return validation_results
            
        except Exception as e:
            self.logger.error("Infrastructure validation failed", error=str(e))
            validation_results["overall_status"] = "error"
            return validation_results


# Factory function for creating demo agents
def create_demo_agent(
    agent_id: str = None,
    gateway_url: str = "https://agentgateway.dev",
    gateway_api_key: str = None
) -> DemoAgent:
    """
    Factory function for creating demo agents.
    
    Args:
        agent_id: Unique identifier for the agent
        gateway_url: URL for the agentgateway service
        gateway_api_key: API key for agentgateway authentication
        
    Returns:
        Configured DemoAgent instance
    """
    if not agent_id:
        import uuid
        agent_id = f"demo-agent-{str(uuid.uuid4())[:8]}"
    
    return DemoAgent(
        agent_id=agent_id,
        gateway_url=gateway_url,
        gateway_api_key=gateway_api_key
    )


# Example usage and testing
async def main():
    """Example usage of the demo agent."""
    print("🚀 TASK-005 Demo Agent - LangGraph Foundation")
    print("=" * 50)
    
    # Create demo agent
    agent = create_demo_agent()
    
    try:
        # Start the agent
        await agent.start()
        print(f"✅ Agent started: {agent}")
        
        # Demonstrate workflow
        print("\n📋 Testing LangGraph Workflow:")
        workflow_result = await agent.demonstrate_workflow(
            "Show how the LangGraph workflow processes a simple business query"
        )
        print(f"Workflow result: {len(workflow_result.get('messages', []))} messages processed")
        
        # Test MCP integration
        print("\n🔧 Testing MCP Integration:")
        mcp_result = await agent.test_mcp_integration()
        print(f"MCP test result: {len(mcp_result.get('available_tools', []))} tools available")
        
        # Validate infrastructure
        print("\n🏗️ Validating Infrastructure:")
        validation = await agent.validate_infrastructure()
        print(f"Validation status: {validation['overall_status']}")
        for component, status in validation.items():
            if component != "overall_status":
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {component}: {status}")
        
        # Get health check
        print("\n💚 Health Check:")
        health = agent.get_health_check()
        print(f"  Agent ID: {health.agent_id}")
        print(f"  Status: {health.status.value}")
        print(f"  Uptime: {health.uptime_seconds:.1f}s")
        print(f"  Errors: {health.error_count}")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
    
    finally:
        # Stop the agent
        await agent.stop()
        print(f"\n🛑 Agent stopped: {agent}")


if __name__ == "__main__":
    asyncio.run(main())
