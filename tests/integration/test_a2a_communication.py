#!/usr/bin/env python3
"""
A2A Communication Test Suite
Tests Google A2A protocol integration and agent-to-agent communication.
"""

import asyncio
import json
import time
from typing import List, Dict
import httpx

from .test_runner import (TestSuite, TestResult, TestStatus, run_command, 
                         check_http_endpoint, wait_for_condition)


class A2ACommunicationTestSuite(TestSuite):
    """Test suite for A2A protocol communication."""
    
    def __init__(self):
        super().__init__("A2A Communication Protocol")
        self.test_namespace = "elf-automations"
        self.test_agents = []
        
    async def run_tests(self) -> List[TestResult]:
        """Run all A2A communication tests."""
        tests = [
            self.test_a2a_sdk_availability,
            self.test_agent_card_generation,
            self.test_agent_capabilities_definition,
            self.test_a2a_server_startup,
            self.test_agent_registration,
            self.test_task_store_operations,
            self.test_queue_manager_operations,
            self.test_agent_to_agent_messaging,
            self.test_multi_agent_workflow,
            self.test_event_streaming
        ]
        
        for test in tests:
            start_time = time.time()
            try:
                await test()
                duration = time.time() - start_time
                self.add_result(
                    test.__name__.replace('test_', '').replace('_', ' ').title(),
                    TestStatus.PASSED,
                    duration
                )
            except Exception as e:
                duration = time.time() - start_time
                self.add_result(
                    test.__name__.replace('test_', '').replace('_', ' ').title(),
                    TestStatus.FAILED,
                    duration,
                    str(e)
                )
                
        return self.results
        
    async def test_a2a_sdk_availability(self):
        """Test A2A SDK is available and importable."""
        # Test that we can import A2A SDK components
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from a2a.client import A2AClient
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill
    from a2a.server.apps import A2AStarletteApplication
    print("SUCCESS: A2A SDK imports successful")
except ImportError as e:
    print(f"FAILED: A2A SDK import failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"A2A SDK not available: {stderr}")
            
    async def test_agent_card_generation(self):
        """Test AgentCard generation with proper structure."""
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill
    
    # Create test agent card
    capabilities = AgentCapabilities(
        pushNotifications=True,
        stateTransitionHistory=True,
        streaming=True
    )
    
    skill = AgentSkill(
        id="test-skill",
        name="Test Skill",
        description="A test skill",
        inputModes=["text"],
        outputModes=["text"],
        tags=["test"],
        examples=[]
    )
    
    card = AgentCard(
        agent_id="test-agent",
        name="Test Agent",
        description="A test agent",
        version="1.0.0",
        url="http://localhost:8090",
        capabilities=capabilities,
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill]
    )
    
    print(f"SUCCESS: AgentCard created with ID: {card.agent_id}")
    
except Exception as e:
    print(f"FAILED: AgentCard generation failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"AgentCard generation failed: {stderr}")
            
    async def test_agent_capabilities_definition(self):
        """Test agent capabilities are properly defined."""
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from agents.distributed.a2a.client import A2AClientManager
    from agents.distributed.distributed_agent import DistributedAgent
    
    # Create test agent
    agent = DistributedAgent(
        agent_id="test-capabilities-agent",
        role="Test Agent",
        goal="Test agent capabilities",
        backstory="A test agent for capability testing",
        department="test"
    )
    
    # Get agent card
    card = agent.get_agent_card()
    
    # Verify capabilities
    if not card.capabilities:
        raise Exception("Agent capabilities not defined")
        
    if not card.skills:
        raise Exception("Agent skills not defined")
        
    print(f"SUCCESS: Agent capabilities defined - {len(card.skills)} skills")
    
except Exception as e:
    print(f"FAILED: Agent capabilities test failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"Agent capabilities test failed: {stderr}")
            
    async def test_a2a_server_startup(self):
        """Test A2A server can start up properly."""
        # Deploy a test A2A server
        deployment_yaml = f'''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: a2a-server-test
  namespace: {self.test_namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: a2a-server-test
  template:
    metadata:
      labels:
        app: a2a-server-test
    spec:
      containers:
      - name: a2a-server
        image: elf-automations/distributed-agent:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8090
          name: a2a-server
        env:
        - name: AGENT_ID
          value: "a2a-test-agent"
        - name: AGENT_ROLE
          value: "A2A Test Agent"
        - name: A2A_SERVER_PORT
          value: "8090"
        command: ["python3", "-c"]
        args:
        - |
          import asyncio
          import sys
          sys.path.append("/app")
          
          from agents.distributed.a2a.server import InMemoryTaskStore, InMemoryQueueManager
          from agents.distributed.distributed_agent import CrewAIAgentExecutor
          from a2a.server.apps import A2AStarletteApplication
          import uvicorn
          
          async def main():
              task_store = InMemoryTaskStore()
              queue_manager = InMemoryQueueManager()
              executor = CrewAIAgentExecutor("a2a-test-agent", "A2A Test Agent", "Test A2A server", "Test agent for A2A server testing", "test")
              
              app = A2AStarletteApplication(
                  task_store=task_store,
                  queue_manager=queue_manager,
                  executor=executor
              )
              
              config = uvicorn.Config(app, host="0.0.0.0", port=8090, log_level="info")
              server = uvicorn.Server(config)
              await server.serve()
          
          asyncio.run(main())
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: a2a-server-test-service
  namespace: {self.test_namespace}
spec:
  selector:
    app: a2a-server-test
  ports:
  - name: a2a-server
    port: 8090
    targetPort: 8090
'''
        
        # Apply deployment
        process = await asyncio.create_subprocess_exec(
            'kubectl', 'apply', '-f', '-',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(deployment_yaml.encode())
        
        if process.returncode != 0:
            raise Exception(f"Failed to deploy A2A server: {stderr.decode()}")
            
        self.test_agents.append("a2a-server-test")
        
        # Wait for pod to be running
        async def pod_running():
            success, stdout, stderr = await run_command([
                'kubectl', 'get', 'pods', '-n', self.test_namespace,
                '-l', 'app=a2a-server-test', '-o', 'jsonpath={.items[0].status.phase}'
            ])
            return success and stdout.strip() == 'Running'
            
        if not await wait_for_condition(pod_running, timeout=120):
            raise Exception("A2A server pod not running within timeout")
            
    async def test_agent_registration(self):
        """Test agent registration with A2A protocol."""
        # This test would verify that agents can register with a discovery service
        # For now, we'll test the registration logic locally
        
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from agents.distributed.a2a.client import A2AClientManager
    from agents.distributed.distributed_agent import DistributedAgent
    
    # Create test agent
    agent = DistributedAgent(
        agent_id="registration-test-agent",
        role="Registration Test Agent",
        goal="Test agent registration",
        backstory="A test agent for registration testing",
        department="test"
    )
    
    # Test registration process
    client_manager = A2AClientManager()
    
    # Register agent (this will use mock implementation)
    success = client_manager.register_agent(agent.get_agent_card())
    
    if not success:
        raise Exception("Agent registration failed")
        
    print("SUCCESS: Agent registration completed")
    
except Exception as e:
    print(f"FAILED: Agent registration test failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"Agent registration test failed: {stderr}")
            
    async def test_task_store_operations(self):
        """Test task store operations."""
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from agents.distributed.a2a.server import InMemoryTaskStore
    import asyncio
    
    async def test_task_store():
        store = InMemoryTaskStore()
        
        # Test save operation
        task_data = {"task_id": "test-123", "status": "running", "data": "test"}
        await store.save("test-123", task_data)
        
        # Test get operation
        retrieved = await store.get("test-123")
        if retrieved != task_data:
            raise Exception("Task store get operation failed")
            
        # Test delete operation
        await store.delete("test-123")
        
        # Verify deletion
        deleted = await store.get("test-123")
        if deleted is not None:
            raise Exception("Task store delete operation failed")
            
        print("SUCCESS: Task store operations completed")
    
    asyncio.run(test_task_store())
    
except Exception as e:
    print(f"FAILED: Task store test failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"Task store test failed: {stderr}")
            
    async def test_queue_manager_operations(self):
        """Test queue manager operations."""
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from agents.distributed.a2a.server import InMemoryQueueManager
    import asyncio
    
    async def test_queue_manager():
        manager = InMemoryQueueManager()
        
        # Test create_or_tap operation
        queue = await manager.create_or_tap("test-queue")
        if queue is None:
            raise Exception("Queue creation failed")
            
        # Test enqueue operation
        test_event = {"event_type": "test", "data": "test_data"}
        await queue.enqueue_event(test_event)
        
        # Test dequeue operation
        retrieved_event = await queue.dequeue_event(no_wait=True)
        if retrieved_event != test_event:
            raise Exception("Queue dequeue operation failed")
            
        # Test tap operation
        main_queue = await manager.create_or_tap("main-queue")
        child_queue = main_queue.tap()
        if child_queue is None:
            raise Exception("Queue tap operation failed")
            
        print("SUCCESS: Queue manager operations completed")
    
    asyncio.run(test_queue_manager())
    
except Exception as e:
    print(f"FAILED: Queue manager test failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"Queue manager test failed: {stderr}")
            
    async def test_agent_to_agent_messaging(self):
        """Test direct agent-to-agent messaging."""
        # This would test actual A2A messaging between agents
        # For now, we'll test the messaging infrastructure
        
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from agents.distributed.a2a.messages import (
        TaskStatusUpdateEvent, TaskArtifactUpdateEvent, TaskProgressEvent
    )
    
    # Test message creation
    status_event = TaskStatusUpdateEvent(
        task_id="test-task",
        status="running",
        timestamp="2024-01-01T00:00:00Z"
    )
    
    artifact_event = TaskArtifactUpdateEvent(
        task_id="test-task",
        artifact_type="result",
        artifact_data={"result": "test result"},
        timestamp="2024-01-01T00:00:00Z"
    )
    
    progress_event = TaskProgressEvent(
        task_id="test-task",
        progress=50,
        message="Task 50% complete",
        timestamp="2024-01-01T00:00:00Z"
    )
    
    # Verify message structure
    if not status_event.task_id:
        raise Exception("TaskStatusUpdateEvent creation failed")
        
    if not artifact_event.artifact_data:
        raise Exception("TaskArtifactUpdateEvent creation failed")
        
    if progress_event.progress != 50:
        raise Exception("TaskProgressEvent creation failed")
        
    print("SUCCESS: A2A messaging infrastructure validated")
    
except Exception as e:
    print(f"FAILED: A2A messaging test failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"A2A messaging test failed: {stderr}")
            
    async def test_multi_agent_workflow(self):
        """Test multi-agent workflow coordination."""
        # This would test a workflow involving multiple agents
        # For now, we'll test the workflow infrastructure
        
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from agents.distributed.distributed_agent import DistributedAgent
    
    # Create multiple test agents
    chief_agent = DistributedAgent(
        agent_id="chief-workflow-test",
        role="Chief Executive Officer",
        goal="Coordinate multi-agent workflow",
        backstory="Executive agent for workflow coordination",
        department="executive"
    )
    
    sales_agent = DistributedAgent(
        agent_id="sales-workflow-test",
        role="Sales Manager",
        goal="Handle sales tasks in workflow",
        backstory="Sales agent for workflow testing",
        department="sales"
    )
    
    marketing_agent = DistributedAgent(
        agent_id="marketing-workflow-test",
        role="Marketing Manager",
        goal="Handle marketing tasks in workflow",
        backstory="Marketing agent for workflow testing",
        department="marketing"
    )
    
    # Verify agents can be created and have proper capabilities
    agents = [chief_agent, sales_agent, marketing_agent]
    
    for agent in agents:
        card = agent.get_agent_card()
        if not card.capabilities:
            raise Exception(f"Agent {agent.agent_id} missing capabilities")
        if not card.skills:
            raise Exception(f"Agent {agent.agent_id} missing skills")
            
    print(f"SUCCESS: Multi-agent workflow with {len(agents)} agents validated")
    
except Exception as e:
    print(f"FAILED: Multi-agent workflow test failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"Multi-agent workflow test failed: {stderr}")
            
    async def test_event_streaming(self):
        """Test event streaming capabilities."""
        # Test Server-Sent Events (SSE) streaming
        test_script = '''
import sys
sys.path.append("/Users/bryansparks/projects/ELFAutomations")

try:
    from agents.distributed.a2a.server import InMemoryQueueManager
    from agents.distributed.a2a.messages import TaskProgressEvent
    import asyncio
    
    async def test_streaming():
        manager = InMemoryQueueManager()
        queue = await manager.create_or_tap("streaming-test")
        
        # Simulate streaming events
        events = [
            TaskProgressEvent(
                task_id="streaming-test",
                progress=25,
                message="Task 25% complete",
                timestamp="2024-01-01T00:00:00Z"
            ),
            TaskProgressEvent(
                task_id="streaming-test",
                progress=50,
                message="Task 50% complete",
                timestamp="2024-01-01T00:00:01Z"
            ),
            TaskProgressEvent(
                task_id="streaming-test",
                progress=100,
                message="Task complete",
                timestamp="2024-01-01T00:00:02Z"
            )
        ]
        
        # Enqueue events
        for event in events:
            await queue.enqueue_event(event.dict())
            
        # Dequeue and verify events
        received_events = []
        for _ in range(len(events)):
            event = await queue.dequeue_event(no_wait=True)
            if event:
                received_events.append(event)
                
        if len(received_events) != len(events):
            raise Exception(f"Expected {len(events)} events, got {len(received_events)}")
            
        print("SUCCESS: Event streaming validated")
    
    asyncio.run(test_streaming())
    
except Exception as e:
    print(f"FAILED: Event streaming test failed: {e}")
    sys.exit(1)
'''
        
        success, stdout, stderr = await run_command([
            'python3', '-c', test_script
        ])
        
        if not success or 'SUCCESS' not in stdout:
            raise Exception(f"Event streaming test failed: {stderr}")
            
    async def cleanup_test_resources(self):
        """Clean up test resources."""
        for agent in self.test_agents:
            await run_command([
                'kubectl', 'delete', 'deployment', agent, '-n', self.test_namespace
            ])
            await run_command([
                'kubectl', 'delete', 'service', f'{agent}-service', '-n', self.test_namespace
            ])


# Standalone test runner for this suite
async def main():
    """Run A2A communication tests standalone."""
    from .test_runner import TestRunner
    
    runner = TestRunner()
    runner.add_suite(A2ACommunicationTestSuite())
    
    success = await runner.run_all_tests()
    return success


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
