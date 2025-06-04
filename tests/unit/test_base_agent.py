"""
Unit tests for BaseAgent class
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.base import BaseAgent, AgentConfig, AgentType, AgentStatus


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent for testing."""
    
    async def _execute_task_impl(self, task):
        """Simple test task implementation."""
        return {"status": "completed", "result": f"Task {task.get('id', 'unknown')} completed"}


@pytest.fixture
def agent_config():
    """Create a test agent configuration."""
    return AgentConfig(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0.1,
        tools=["test_tool"],
        department_access=["test_department"]
    )


@pytest.fixture
def test_agent(agent_config):
    """Create a test agent instance."""
    return TestAgent(
        agent_id="test-agent-001",
        name="Test Agent",
        agent_type=AgentType.INDIVIDUAL,
        department="test_department",
        config=agent_config
    )


class TestBaseAgent:
    """Test cases for BaseAgent class."""
    
    def test_agent_initialization(self, test_agent, agent_config):
        """Test agent initialization."""
        assert test_agent.agent_id == "test-agent-001"
        assert test_agent.name == "Test Agent"
        assert test_agent.agent_type == AgentType.INDIVIDUAL
        assert test_agent.department == "test_department"
        assert test_agent.config == agent_config
        assert test_agent.state.agent_id == "test-agent-001"
        assert test_agent.state.status == AgentStatus.INACTIVE
    
    def test_agent_config_validation(self):
        """Test agent configuration validation."""
        # Test valid model
        config = AgentConfig(model="claude-3-5-sonnet-20241022")
        assert config.model == "claude-3-5-sonnet-20241022"
        
        # Test invalid model
        with pytest.raises(ValueError):
            AgentConfig(model="invalid-model")
    
    @pytest.mark.asyncio
    async def test_agent_start_stop(self, test_agent):
        """Test agent start and stop functionality."""
        # Test start
        with patch('agents.registry.AgentRegistry.register_agent') as mock_register:
            await test_agent.start()
            assert test_agent.state.status == AgentStatus.ACTIVE
            mock_register.assert_called_once_with(test_agent)
        
        # Test stop
        with patch('agents.registry.AgentRegistry.unregister_agent') as mock_unregister:
            await test_agent.stop()
            assert test_agent.state.status == AgentStatus.INACTIVE
            mock_unregister.assert_called_once_with(test_agent.agent_id)
    
    @pytest.mark.asyncio
    async def test_task_execution(self, test_agent):
        """Test task execution."""
        task = {
            "id": "test-task-001",
            "type": "test_task",
            "description": "Test task"
        }
        
        result = await test_agent.execute_task(task)
        
        assert result["status"] == "completed"
        assert "test-task-001" in result["result"]
        assert test_agent.state.status == AgentStatus.ACTIVE
        assert test_agent.state.current_task is None
        assert test_agent.state.error_count == 0
    
    @pytest.mark.asyncio
    async def test_task_execution_error(self, test_agent):
        """Test task execution with error."""
        # Mock the implementation to raise an error
        with patch.object(test_agent, '_execute_task_impl', side_effect=Exception("Test error")):
            task = {"id": "error-task", "type": "error_task"}
            
            with pytest.raises(Exception):
                await test_agent.execute_task(task)
            
            assert test_agent.state.status == AgentStatus.ERROR
            assert test_agent.state.error_count == 1
    
    @pytest.mark.asyncio
    async def test_message_sending(self, test_agent):
        """Test message sending functionality."""
        with patch.object(test_agent, '_deliver_message') as mock_deliver:
            message_id = await test_agent.send_message(
                to_agent="target-agent",
                message_type="test_message",
                content={"data": "test"}
            )
            
            assert message_id is not None
            mock_deliver.assert_called_once()
            
            # Check the message structure
            call_args = mock_deliver.call_args[0][0]
            assert call_args.from_agent == test_agent.agent_id
            assert call_args.to_agent == "target-agent"
            assert call_args.message_type == "test_message"
            assert call_args.content == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_message_receiving(self, test_agent):
        """Test message receiving functionality."""
        from agents.base import AgentMessage
        
        message = AgentMessage(
            from_agent="sender-agent",
            to_agent=test_agent.agent_id,
            message_type="test_message",
            content={"data": "test"}
        )
        
        # Receive the message
        await test_agent._receive_message(message)
        
        # Check that message is in queue
        assert not test_agent._message_queue.empty()
        
        # Process messages
        with patch.object(test_agent, '_handle_message') as mock_handle:
            await test_agent.process_messages()
            mock_handle.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_llm_interaction(self, test_agent):
        """Test LLM interaction."""
        with patch('agents.base.ChatAnthropic') as mock_llm_class:
            mock_llm_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Test response"
            mock_llm_instance.ainvoke.return_value = mock_response
            mock_llm_class.return_value = mock_llm_instance
            
            # Reinitialize the agent to use the mocked LLM
            test_agent.llm = mock_llm_instance
            
            response = await test_agent.think("Test prompt")
            
            assert response == "Test response"
            mock_llm_instance.ainvoke.assert_called_once()
    
    def test_agent_status(self, test_agent):
        """Test agent status reporting."""
        status = test_agent.get_status()
        
        assert status["agent_id"] == test_agent.agent_id
        assert status["name"] == test_agent.name
        assert status["type"] == test_agent.agent_type.value
        assert status["department"] == test_agent.department
        assert status["status"] == test_agent.state.status.value
        assert "last_activity" in status
        assert "error_count" in status
    
    def test_agent_repr(self, test_agent):
        """Test agent string representation."""
        repr_str = repr(test_agent)
        assert "TestAgent" in repr_str
        assert test_agent.agent_id in repr_str
        assert test_agent.name in repr_str
        assert test_agent.department in repr_str


@pytest.mark.asyncio
async def test_agent_config_defaults():
    """Test agent configuration defaults."""
    config = AgentConfig()
    
    assert config.model == "claude-3-5-sonnet-20241022"
    assert config.max_tokens == 4000
    assert config.temperature == 0.1
    assert config.timeout_seconds == 60
    assert config.max_retries == 3
    assert config.tools == []
    assert config.department_access == []
    assert config.escalation_threshold == 3


@pytest.mark.asyncio
async def test_agent_config_validation_edge_cases():
    """Test agent configuration validation edge cases."""
    # Test max_tokens bounds
    with pytest.raises(ValueError):
        AgentConfig(max_tokens=50)  # Too low
    
    with pytest.raises(ValueError):
        AgentConfig(max_tokens=10000)  # Too high
    
    # Test temperature bounds
    with pytest.raises(ValueError):
        AgentConfig(temperature=-0.1)  # Too low
    
    with pytest.raises(ValueError):
        AgentConfig(temperature=2.1)  # Too high
