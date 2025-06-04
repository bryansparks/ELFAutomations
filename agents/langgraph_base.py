"""
LangGraph-based Agent Infrastructure Foundation

This module provides the foundational LangGraph-based agent infrastructure
for TASK-005, establishing the pattern for all future agents in the
Virtual AI Company Platform.

Key Technologies:
- LangGraph: Stateful, graph-based agent workflows
- kagent: Kubernetes-native agent deployment
- MCP: Model Context Protocol for tool integration
- agentgateway.dev: Centralized MCP access gateway
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Annotated

import aiohttp
import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field, ConfigDict

logger = structlog.get_logger(__name__)


class AgentLifecycleState(str, Enum):
    """Agent lifecycle states for kagent integration."""
    
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DESTROYED = "destroyed"


class MCPToolCall(BaseModel):
    """Represents an MCP tool call through agentgateway."""
    
    model_config = ConfigDict(extra='forbid')
    
    tool_name: str = Field(description="Name of the MCP tool")
    server_name: str = Field(description="MCP server name")
    arguments: Dict[str, Any] = Field(description="Tool arguments")
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentGatewayClient:
    """Client for communicating with local AgentGateway for MCP access."""
    
    def __init__(self, gateway_url: str, agent_id: str, api_key: Optional[str] = None):
        self.gateway_url = gateway_url.rstrip('/')
        self.agent_id = agent_id
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logger.bind(agent_id=agent_id, gateway_url=gateway_url)
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            "User-Agent": f"ELF-Agent/{self.agent_id}",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools through the gateway."""
        try:
            # Use MCP protocol to list tools
            mcp_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list",
                "params": {}
            }
            
            async with self.session.post(
                f"{self.gateway_url}/mcp",
                json=mcp_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]
                    self.logger.info("Retrieved available tools", tool_count=len(tools))
                    return tools
                else:
                    self.logger.warning("No tools found in response", response=data)
                    return []
                    
        except Exception as e:
            self.logger.error("Failed to list available tools", error=str(e))
            return []
    
    async def call_mcp_tool(self, tool_call: MCPToolCall) -> Dict[str, Any]:
        """Call an MCP tool through the AgentGateway using MCP protocol."""
        mcp_request = {
            "jsonrpc": "2.0",
            "id": tool_call.call_id,
            "method": "tools/call",
            "params": {
                "name": f"{tool_call.server_name}/{tool_call.tool_name}",
                "arguments": tool_call.arguments
            }
        }
        
        try:
            async with self.session.post(
                f"{self.gateway_url}/mcp",
                json=mcp_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if "result" in result:
                    self.logger.info(
                        "MCP tool call successful",
                        tool_name=tool_call.tool_name,
                        server_name=tool_call.server_name,
                        call_id=tool_call.call_id
                    )
                    return result["result"]
                elif "error" in result:
                    error_msg = result["error"].get("message", "Unknown MCP error")
                    self.logger.error(
                        "MCP tool call error",
                        tool_name=tool_call.tool_name,
                        server_name=tool_call.server_name,
                        call_id=tool_call.call_id,
                        error=error_msg
                    )
                    raise Exception(f"MCP Error: {error_msg}")
                else:
                    raise Exception(f"Unexpected MCP response: {result}")
                
        except Exception as e:
            self.logger.error(
                "MCP tool call failed",
                tool_name=tool_call.tool_name,
                server_name=tool_call.server_name,
                call_id=tool_call.call_id,
                error=str(e)
            )
            raise


class LangGraphAgentState(TypedDict):
    """State structure for LangGraph agent workflows."""
    
    messages: Annotated[List[BaseMessage], add_messages]
    agent_id: str
    current_task: Optional[str]
    task_context: Dict[str, Any]
    available_tools: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    error_count: int
    last_activity: datetime
    metadata: Dict[str, Any]


class KAgentHealthCheck(BaseModel):
    """Health check data for kagent integration."""
    
    model_config = ConfigDict(extra='forbid')
    
    agent_id: str
    status: AgentLifecycleState
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    message_queue_size: int = Field(default=0)
    active_tasks: int = Field(default=0)
    error_count: int = Field(default=0)
    uptime_seconds: float = Field(default=0.0)
    memory_usage_mb: float = Field(default=0.0)
    cpu_usage_percent: float = Field(default=0.0)


class LangGraphBaseAgent(ABC):
    """
    LangGraph-based foundational agent class for TASK-005.
    
    This establishes the pattern for all future agents using:
    - LangGraph for stateful workflows
    - kagent for Kubernetes deployment
    - MCP via agentgateway.dev for tool access
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        department: str,
        system_prompt: str,
        gateway_url: str = "http://agentgateway-service:3000",
        gateway_api_key: str = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.department = department
        self.system_prompt = system_prompt
        self._state = AgentLifecycleState.CREATED
        self.start_time = None
        self.error_count = 0
        
        # Initialize structured logger
        self.logger = structlog.get_logger().bind(
            agent_id=agent_id,
            agent_name=name,
            department=department
        )
        
        # Initialize AgentGateway client for MCP access
        self.gateway_client = AgentGatewayClient(
            agent_id=agent_id,
            gateway_url=gateway_url,
            api_key=gateway_api_key
        )
        
        # Initialize LLM
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.1,
            max_tokens=4000
        )
        
        # LangGraph components
        self.graph: Optional[StateGraph] = None
        self.checkpointer = MemorySaver()
        self.compiled_graph = None
        
        # Initialize the agent workflow graph
        self._initialize_graph()
        
        self.logger.info("LangGraph agent initialized")
    
    def _initialize_graph(self):
        """Initialize the LangGraph workflow."""
        # Create the state graph
        workflow = StateGraph(LangGraphAgentState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("load_tools", self._load_tools_node)
        workflow.add_node("process_task", self._process_task_node)
        workflow.add_node("execute_tools", self._execute_tools_node)
        workflow.add_node("respond", self._respond_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges
        workflow.add_edge("initialize", "load_tools")
        workflow.add_edge("load_tools", "process_task")
        workflow.add_conditional_edges(
            "process_task",
            self._should_use_tools,
            {
                "use_tools": "execute_tools",
                "respond": "respond",
                "error": "error_handler"
            }
        )
        workflow.add_edge("execute_tools", "respond")
        workflow.add_edge("respond", END)
        workflow.add_edge("error_handler", END)
        
        # Compile the graph
        self.graph = workflow
        self.compiled_graph = workflow.compile(checkpointer=self.checkpointer)
        
        self.logger.info("LangGraph workflow initialized")
    
    async def _initialize_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """Initialize the agent for a new task."""
        self.logger.info("Initializing agent for new task")
        
        state["agent_id"] = self.agent_id
        state["last_activity"] = datetime.utcnow()
        state["tool_results"] = {}
        state["metadata"] = state.get("metadata", {})
        
        return state
    
    async def _load_tools_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """Load available MCP tools through agentgateway."""
        self.logger.info("Loading available MCP tools")
        
        try:
            async with self.gateway_client as gateway:
                tools = await gateway.list_available_tools()
                state["available_tools"] = tools
                
                self.logger.info("Loaded MCP tools", tool_count=len(tools))
                
        except Exception as e:
            self.logger.error("Failed to load MCP tools", error=str(e))
            state["available_tools"] = []
            state["error_count"] = state.get("error_count", 0) + 1
        
        return state
    
    async def _process_task_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """Process the current task using LLM reasoning."""
        messages = state.get("messages", [])
        
        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            system_msg = SystemMessage(content=self.system_prompt)
            messages.insert(0, system_msg)
        
        try:
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Add response to messages
            if isinstance(response, AIMessage):
                messages.append(response)
            else:
                messages.append(AIMessage(content=str(response)))
            
            state["messages"] = messages
            state["last_activity"] = datetime.utcnow()
            
            self.logger.info("Task processed by LLM")
            
        except Exception as e:
            self.logger.error("LLM processing failed", error=str(e))
            state["error_count"] = state.get("error_count", 0) + 1
            
            # Add error message
            error_msg = AIMessage(content=f"Error processing task: {str(e)}")
            messages.append(error_msg)
            state["messages"] = messages
        
        return state
    
    def _should_use_tools(self, state: LangGraphAgentState) -> str:
        """Determine if tools should be used based on the current state."""
        messages = state.get("messages", [])
        error_count = state.get("error_count", 0)
        
        # Check for errors
        if error_count > 3:
            return "error"
        
        # Check if the last message indicates tool usage is needed
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                content = last_message.content.lower()
                # Simple heuristic - look for tool-related keywords
                if any(keyword in content for keyword in ["tool", "search", "database", "api", "call"]):
                    return "use_tools"
        
        return "respond"
    
    async def _execute_tools_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """Execute MCP tools through agentgateway."""
        self.logger.info("Executing MCP tools")
        
        # This is a placeholder for tool execution logic
        # In a real implementation, this would parse the LLM response
        # to identify which tools to call and with what parameters
        
        try:
            # Example tool call (this would be dynamic based on LLM output)
            async with self.gateway_client as gateway:
                # Placeholder tool call
                tool_call = MCPToolCall(
                    tool_name="example_tool",
                    server_name="business_tools",
                    arguments={"query": "test"}
                )
                
                # This would only execute if the LLM actually requested a tool
                # result = await gateway.call_mcp_tool(tool_call)
                # state["tool_results"][tool_call.call_id] = result
                
                self.logger.info("Tool execution completed")
                
        except Exception as e:
            self.logger.error("Tool execution failed", error=str(e))
            state["error_count"] = state.get("error_count", 0) + 1
        
        return state
    
    async def _respond_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """Generate final response."""
        self.logger.info("Generating final response")
        
        # Update last activity
        state["last_activity"] = datetime.utcnow()
        
        return state
    
    async def _error_handler_node(self, state: LangGraphAgentState) -> LangGraphAgentState:
        """Handle errors in the workflow."""
        error_count = state.get("error_count", 0)
        
        self.logger.error("Error handler activated", error_count=error_count)
        
        # Add error message to conversation
        messages = state.get("messages", [])
        error_msg = AIMessage(
            content=f"I encountered an error while processing your request. Error count: {error_count}"
        )
        messages.append(error_msg)
        state["messages"] = messages
        
        return state
    
    async def process_message(self, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a message through the LangGraph workflow."""
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "agent_id": self.agent_id,
            "current_task": None,
            "task_context": {},
            "available_tools": [],
            "tool_results": {},
            "error_count": 0,
            "last_activity": datetime.utcnow(),
            "metadata": {}
        }
        
        try:
            # Run the workflow
            config = {"configurable": {"thread_id": thread_id}}
            result = await self.compiled_graph.ainvoke(initial_state, config)
            
            self.logger.info("Message processed successfully", thread_id=thread_id)
            return result
            
        except Exception as e:
            self.logger.error("Message processing failed", error=str(e), thread_id=thread_id)
            self.error_count += 1
            raise
    
    async def start(self) -> None:
        """Start the agent (kagent lifecycle)."""
        self._state = AgentLifecycleState.STARTING
        self.start_time = datetime.utcnow()
        self.logger.info("Starting agent")
        
        try:
            # Perform startup tasks
            await self._startup_tasks()
            
            self._state = AgentLifecycleState.RUNNING
            self.logger.info("Agent started successfully")
            
        except Exception as e:
            self._state = AgentLifecycleState.ERROR
            self.logger.error("Agent startup failed", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the agent (kagent lifecycle)."""
        self._state = AgentLifecycleState.STOPPING
        self.logger.info("Stopping agent")
        
        try:
            # Perform shutdown tasks
            await self._shutdown_tasks()
            
            self._state = AgentLifecycleState.STOPPED
            self.logger.info("Agent stopped successfully")
            
        except Exception as e:
            self._state = AgentLifecycleState.ERROR
            self.logger.error("Agent shutdown failed", error=str(e))
            raise
    
    async def destroy(self) -> None:
        """Destroy the agent (kagent lifecycle)."""
        self.logger.info("Destroying agent")
        
        try:
            if self._state == AgentLifecycleState.RUNNING:
                await self.stop()
            
            # Cleanup resources
            await self._cleanup_resources()
            
            self._state = AgentLifecycleState.DESTROYED
            self.logger.info("Agent destroyed successfully")
            
        except Exception as e:
            self._state = AgentLifecycleState.ERROR
            self.logger.error("Agent destruction failed", error=str(e))
            raise
    
    @property
    def state(self) -> AgentLifecycleState:
        """Get the current agent state."""
        return self._state
    
    @state.setter
    def state(self, value: AgentLifecycleState) -> None:
        """Set the agent state."""
        self._state = value
    
    def get_health_check(self) -> KAgentHealthCheck:
        """Get health check data for kagent monitoring."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        
        return KAgentHealthCheck(
            agent_id=self.agent_id,
            status=self._state,
            error_count=self.error_count,
            uptime_seconds=uptime
        )
    
    @abstractmethod
    async def _startup_tasks(self) -> None:
        """Implement agent-specific startup tasks."""
        pass
    
    @abstractmethod
    async def _shutdown_tasks(self) -> None:
        """Implement agent-specific shutdown tasks."""
        pass
    
    @abstractmethod
    async def _cleanup_resources(self) -> None:
        """Implement agent-specific resource cleanup."""
        pass
    
    def __repr__(self) -> str:
        return f"LangGraphBaseAgent(id={self.agent_id}, name={self.name}, state={self._state.value})"
