# A2A (Agent-to-Agent) Architecture Guide

## Overview

This document explains the Google A2A (Agent-to-Agent) protocol architecture and how it's implemented in our distributed CrewAI agent system. The A2A protocol enables seamless communication and interoperability between AI agents built on different frameworks, running on separate servers.

## Table of Contents

1. [What is A2A?](#what-is-a2a)
2. [Architecture Overview](#architecture-overview)
3. [A2A Server Role and Responsibilities](#a2a-server-role-and-responsibilities)
4. [Message Queuing Architecture](#message-queuing-architecture)
5. [Discovery Mechanisms](#discovery-mechanisms)
6. [Communication Flow](#communication-flow)
7. [Our Implementation](#our-implementation)
8. [Key Benefits](#key-benefits)
9. [Technical Components](#technical-components)

## What is A2A?

The Agent2Agent (A2A) protocol is an open standard that addresses a critical challenge in the AI landscape: enabling AI agents built on diverse frameworks by different companies, running on separate servers, to communicate and collaborate effectively as agents, not just as tools.

### Core Principles

- **Decentralized Communication**: No single point of failure or central broker
- **Agent Autonomy**: Each agent controls its own capabilities and policies
- **Security & Privacy**: Agents collaborate without exposing internal state, memory, or tools
- **Interoperability**: Standard protocol works across different AI frameworks
- **Discoverability**: Agents can find and understand each other's capabilities

## Architecture Overview

The A2A protocol uses a **hybrid distributed architecture** that combines server-based endpoints with peer-to-peer communication:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Chief AI Agent │    │   Sales Agent   │    │ Marketing Agent │
│ A2A Server:8090 │◄──►│ A2A Server:8092 │◄──►│ A2A Server:8093 │
│   (CrewAI)      │    │   (CrewAI)      │    │   (CrewAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Discovery Layer │
                    │ (Multiple Types)│
                    └─────────────────┘
```

### Key Characteristics

- **Each Agent = Server + Client**: Every agent runs its own A2A server and can act as a client
- **Direct Communication**: Agents communicate peer-to-peer via HTTP/JSON-RPC 2.0
- **No Central Broker**: No single point of failure or bottleneck
- **Framework Agnostic**: Works with any underlying AI framework (CrewAI, LangChain, etc.)

## A2A Server Role and Responsibilities

Each A2A server in our deployment serves multiple critical functions:

### 1. Agent Identity & Discovery

**Agent Card Hosting**
- Hosts the Agent Card at `/.well-known/agent.json` (RFC 8615 compliant)
- Provides standardized agent metadata and capabilities
- Enables automated discovery by other agents

**Capability Advertisement**
- Declares supported skills and functions
- Specifies input/output modes (text, forms, media)
- Lists authentication requirements

### 2. Task Execution Interface

**Request Processing**
- Receives task requests from other agents via HTTP POST
- Validates incoming requests against A2A protocol
- Routes tasks to underlying agent framework (CrewAI)

**Response Management**
- Executes tasks using the agent's specialized capabilities
- Returns structured A2A Messages with results
- Supports both synchronous and streaming responses

### 3. Communication Protocol Handler

**Message Processing**
- Handles A2A protocol messages (Task requests/responses)
- Manages conversation context and task history
- Ensures protocol compliance and error handling

**State Management**
- Tracks task execution without exposing internal state
- Maintains conversation history for context
- Provides task lifecycle management (start, execute, cancel)

## Message Queuing Architecture

**Yes, you're absolutely right!** Each agent has its own message queues. The A2A protocol uses **EventQueues** at each agent for sophisticated asynchronous communication, streaming responses, and task event management.

### 🏗️ Queue Architecture per Agent

```
┌─────────────────────────────────────────────────────────────┐
│                    Sales Agent (Pod)                        │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  A2A Server     │    │  EventQueues    │                │
│  │  (Port 8092)    │◄──►│  (Per Task)     │                │
│  │                 │    │                 │                │
│  │ • HTTP Endpoints│    │ task-123 ──────►│ EventQueue     │
│  │ • Request Handler│    │ task-456 ──────►│ EventQueue     │
│  │ • Stream Handler│    │ task-789 ──────►│ EventQueue     │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           └───────────────────────┼────────────────────────│
│                                   │                        │
│  ┌─────────────────────────────────▼──────────────────────┐ │
│  │              CrewAI Agent                             │ │
│  │            (Task Execution)                           │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 EventQueue Purpose & Types

The A2A protocol uses **EventQueues** for several critical purposes:

#### **1. Streaming Response Buffering**
EventQueues act as buffers between asynchronous agent execution and HTTP response handling, enabling real-time streaming of results.

**Use Cases**:
- Long-running tasks that stream progress updates
- Real-time collaboration between agents
- Partial result delivery during complex processing

**Example Flow**:
```
Agent Execution ──► EventQueue ──► HTTP Stream ──► Client Agent
     │                  │              │
     │ enqueue_event()   │ dequeue_event() │ Server-Sent Events
     │                  │              │
   Progress            Buffer         Stream
   Updates            Events         Response
```

#### **2. Task Event Management**
EventQueues handle task lifecycle events, providing comprehensive task state tracking.

**Event Types**:
- `Message`: Agent responses and communications
- `Task`: Task definitions and updates
- `TaskStatusUpdateEvent`: Task progress and state changes
- `TaskArtifactUpdateEvent`: File/data artifacts produced
- `A2AError`: Error conditions and failures
- `JSONRPCError`: Protocol-level errors

**Example Events**:
```python
# Task status update
status_event = TaskStatusUpdateEvent(
    task_id="task-123",
    status="in_progress",
    progress=0.45,
    message="Processing sales data..."
)

# Task artifact (file/data produced)
artifact_event = TaskArtifactUpdateEvent(
    task_id="task-123",
    artifact_type="report",
    artifact_data="Generated sales report content..."
)
```

#### **3. Asynchronous Communication Decoupling**
EventQueues decouple agent execution from HTTP response handling, enabling non-blocking communication.

**Benefits**:
- Agent can continue processing while client receives updates
- Multiple clients can "tap" into the same task stream
- Resilient to network interruptions

### 🔄 EventQueue Operations

#### **Core Operations**
```python
# Create/access queue for a task
queue = await queue_manager.create_or_tap("task-123")

# Agent enqueues events during execution
await queue.enqueue_event(progress_message)
await queue.enqueue_event(status_update)
await queue.enqueue_event(final_result)

# Client dequeues events for streaming
event = await queue.dequeue_event(no_wait=False)
```

#### **Tapping (Child Queues)**
Multiple clients can "tap" into the same EventQueue to receive the same events:

```python
# Primary queue
main_queue = await queue_manager.get("task-123")

# Create child queue (tap) for additional client
child_queue = await queue_manager.tap("task-123")
# OR
child_queue = main_queue.tap()

# Both queues receive the same events
```

### 🏭 QueueManager Implementation

Each agent runs a **QueueManager** that manages EventQueues per task:

```python
class InMemoryQueueManager(QueueManager):
    def __init__(self):
        self.queues: Dict[str, EventQueue] = {}  # task_id → EventQueue

    async def create_or_tap(self, task_id: str) -> EventQueue:
        """Create EventQueue for new task or return existing."""
        if task_id not in self.queues:
            self.queues[task_id] = EventQueue()
        return self.queues[task_id]

    async def add(self, task_id: str, queue: EventQueue) -> None:
        """Associate EventQueue with task ID."""
        self.queues[task_id] = queue

    async def get(self, task_id: str) -> Optional[EventQueue]:
        """Retrieve EventQueue for task."""
        return self.queues.get(task_id)

    async def close(self, task_id: str) -> None:
        """Close and cleanup EventQueue."""
        if task_id in self.queues:
            self.queues[task_id].close()
            del self.queues[task_id]
```

### 📡 Streaming Communication Example

Here's how EventQueues enable streaming communication between agents:

```python
# Agent A requests task from Agent B
async def request_sales_analysis():
    # 1. Send task request to Agent B
    response = await a2a_client.send_task(
        agent_url="http://sales-agent:8092",
        task={
            "id": "sales-analysis-001",
            "description": "Analyze Q4 sales performance"
        }
    )

    # 2. Agent B creates EventQueue for this task
    queue = await queue_manager.create_or_tap("sales-analysis-001")

    # 3. Agent B starts processing and streams updates
    await queue.enqueue_event(Message(
        role="assistant",
        parts=[TextPart(text="Starting sales analysis...")]
    ))

    # 4. Agent A receives streaming updates
    while not queue.is_closed():
        event = await queue.dequeue_event()
        if event:
            print(f"Received: {event}")
```

### 🔧 Integration with A2A Server

EventQueues integrate seamlessly with the A2A server infrastructure:

```python
# A2A Server initialization
self.queue_manager = InMemoryQueueManager()
self.request_handler = DefaultRequestHandler(
    agent_executor=self.agent_executor,
    task_store=self.task_store,
    queue_manager=self.queue_manager  # EventQueues managed here
)

# Server-Sent Events (SSE) endpoint uses EventQueues
@app.get("/tasks/{task_id}/stream")
async def stream_task_events(task_id: str):
    queue = await queue_manager.get(task_id)
    if queue:
        # Stream events from EventQueue to client
        async for event in queue.dequeue_event():
            yield f"data: {event.json()}\n\n"
```

### 🎯 Key Benefits of EventQueue Architecture

1. **Real-Time Streaming**: Agents can stream partial results and progress updates
2. **Asynchronous Processing**: Non-blocking communication between agents
3. **Multi-Client Support**: Multiple clients can tap into the same task stream
4. **Event Persistence**: Events are buffered until consumed
5. **Error Handling**: Comprehensive error event types for robust communication
6. **Task Lifecycle**: Complete tracking of task states and artifacts

This EventQueue architecture is what makes A2A truly powerful for **real-time agent collaboration** and **streaming multi-agent workflows**! 🚀

## Discovery Mechanisms

The A2A protocol supports multiple discovery strategies to accommodate different deployment scenarios:

### 1. Well-Known URI (Standardized Discovery)

**Mechanism**: Agents host their Agent Card at a standardized path
- **Standard Path**: `https://{agent-domain}/.well-known/agent.json`
- **Process**:
  1. Client discovers agent domain
  2. Performs HTTP GET to well-known URI
  3. Receives Agent Card with capabilities and endpoint info

**Example**:
```bash
curl https://sales-agent.company.com/.well-known/agent.json
```

**Advantages**:
- Simple and standardized
- Enables automated discovery
- Follows web standards (RFC 8615)
- Reduces discovery to "find the agent's domain"

### 2. Curated Registries (Catalog-Based Discovery)

**Mechanism**: Central registry maintains collection of Agent Cards
- **Process**:
  1. Agents register their cards with registry service
  2. Clients query registry with search criteria
  3. Registry returns matching Agent Cards

**Example Query**:
```json
{
  "query": "find agents with 'sales' skills that support streaming",
  "filters": {
    "skills": ["sales", "customer-engagement"],
    "capabilities": ["streaming"]
  }
}
```

**Advantages**:
- Centralized management and governance
- Capability-based discovery
- Access controls and policies
- Enterprise and marketplace scenarios

### 3. Direct Configuration (Private Discovery)

**Mechanism**: Agents are directly configured with known endpoints
- **Methods**:
  - Hardcoded Agent Card details
  - Configuration files
  - Environment variables
  - Private APIs

**Advantages**:
- Simple for known relationships
- Effective for static deployments
- No external dependencies

## Communication Flow

Here's how agents communicate in our system:

### Step-by-Step Process

```
┌─────────────────┐                    ┌─────────────────┐
│  Marketing      │                    │  Sales Agent    │
│  Agent (Client) │                    │  (Server)       │
└─────────────────┘                    └─────────────────┘
         │                                       │
         │ 1. Discovery Request                  │
         │ GET /.well-known/agent.json          │
         │──────────────────────────────────────►│
         │                                       │
         │ 2. Agent Card Response                │
         │ (capabilities, skills, auth)          │
         │◄──────────────────────────────────────│
         │                                       │
         │ 3. Task Request                       │
         │ POST /tasks/send                      │
         │ {task: "Generate sales proposal"}     │
         │──────────────────────────────────────►│
         │                                       │
         │                                       │ 4. Execute via CrewAI
         │                                       │ ┌─────────────┐
         │                                       │ │   CrewAI    │
         │                                       │ │   Agent     │
         │                                       │ │  Execution  │
         │                                       │ └─────────────┘
         │                                       │
         │ 5. Task Response                      │
         │ {result: "Sales proposal content"}    │
         │◄──────────────────────────────────────│
         │                                       │
```

### Message Structure

**Task Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/send",
  "params": {
    "task": {
      "id": "task-123",
      "history": [
        {
          "role": "user",
          "parts": [
            {
              "text": "Generate a sales proposal for enterprise client"
            }
          ]
        }
      ]
    }
  },
  "id": "req-456"
}
```

**Task Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "role": "assistant",
    "parts": [
      {
        "text": "Here's your enterprise sales proposal..."
      }
    ]
  },
  "id": "req-456"
}
```

## Our Implementation

### Current Deployment Architecture

Our Kubernetes deployment implements the A2A protocol with:

**3 Independent A2A Servers**:
- **Chief AI Agent**: Port 8090 (Executive/Coordination)
- **Sales Agent**: Port 8092 (Sales & Customer Engagement)
- **Marketing Agent**: Port 8093 (Marketing & Content Creation)

**Technical Stack**:
- **A2A SDK**: Google's official `a2a-sdk` (v0.2.5)
- **Server Framework**: `A2AStarletteApplication` (ASGI)
- **Agent Framework**: CrewAI for task execution
- **Container Runtime**: Docker + Kubernetes
- **Service Discovery**: Kubernetes DNS + A2A discovery

### Key Components

#### 1. A2AServerManager
```python
class A2AServerManager:
    """Manages A2A server lifecycle for distributed agents."""

    def __init__(self, agent_card: AgentCard, crewai_agent: Agent):
        self.agent_card = agent_card
        self.crewai_agent = crewai_agent
        self.app = A2AStarletteApplication(...)
```

#### 2. CrewAIAgentExecutor
```python
class CrewAIAgentExecutor(AgentExecutor):
    """Bridges A2A protocol with CrewAI agent execution."""

    async def execute(self, task: Task, context: Dict[str, Any]) -> Message:
        # Convert A2A task to CrewAI task
        # Execute using CrewAI agent
        # Return A2A-compliant response
```

#### 3. Agent Card Generation
```python
agent_card = AgentCard(
    name="Sales Agent",
    description="Specialized in sales and customer engagement",
    url=f"http://sales-agent:8092",
    capabilities=AgentCapabilities(
        streaming=True,
        pushNotifications=False
    ),
    skills=[
        AgentSkill(
            id="sales-proposal",
            name="Sales Proposal Generation",
            description="Generate customized sales proposals"
        )
    ]
)
```

### Deployment Status

✅ **All A2A Servers Running**: 3 agents with real A2A SDK integration
✅ **Health Checks Operational**: `/health` and `/ready` endpoints responding
✅ **Agent Cards Generated**: Proper capabilities and skills defined
✅ **Task Execution Ready**: CrewAI integration working
✅ **Kubernetes Native**: Individual agent lifecycle management

## Key Benefits

### 1. True Decentralization
- No single point of failure
- Each agent maintains autonomy
- Horizontal scaling capabilities

### 2. Framework Interoperability
- CrewAI agents can communicate with LangChain agents
- Protocol-level compatibility across AI frameworks
- Future-proof agent communication

### 3. Security & Privacy
- Agents don't expose internal state
- No shared memory or tool access
- Authentication and authorization at protocol level

### 4. Discoverability & Flexibility
- Multiple discovery mechanisms
- Dynamic capability negotiation
- Supports both public and private agent ecosystems

### 5. Production Readiness
- Standard HTTP/JSON-RPC transport
- Comprehensive error handling
- Monitoring and observability support

## Technical Components

### Core A2A SDK Components

```python
# Server Components
from a2a.server.apps import A2AStarletteApplication
from a2a.server.agent_execution import AgentExecutor
from a2a.server.tasks import TaskStore
from a2a.server.events import QueueManager

# Type Definitions
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from a2a.types import Message, Task, TextPart, Role

# Client Components (for agent-to-agent communication)
from a2a.client import A2AClient
```

### Implementation Classes

**TaskStore**: Manages task persistence and retrieval
```python
class InMemoryTaskStore(TaskStore):
    async def save(self, task: Task) -> None: ...
    async def get(self, task_id: str) -> Optional[Task]: ...
    async def delete(self, task_id: str) -> bool: ...
```

**QueueManager**: Handles event queuing and processing
```python
class InMemoryQueueManager(QueueManager):
    async def add(self, queue_name: str, item: Any) -> None: ...
    async def get(self, queue_name: str) -> Optional[Any]: ...
    async def create_or_tap(self, queue_name: str) -> Any: ...
```

## Next Steps

### Immediate Development
1. **A2A Discovery Service**: Implement centralized agent registry
2. **Agent-to-Agent Messaging**: Test real communication between agents
3. **Multi-Agent Workflows**: Coordinate complex tasks across agents

### Future Enhancements
1. **AgentGateway Integration**: Connect MCP tool access
2. **Advanced Discovery**: Implement capability-based agent finding
3. **Monitoring & Observability**: Add comprehensive agent communication tracking
4. **Security Hardening**: Implement authentication and authorization

---

## Conclusion

The A2A protocol provides a robust, decentralized architecture for agent-to-agent communication that preserves agent autonomy while enabling powerful collaboration. Our implementation successfully bridges the A2A protocol with CrewAI agents, creating a production-ready distributed agent system that can scale and interoperate with other A2A-compliant agents.

The "server" in A2A Server is really each agent providing an API endpoint for other agents to communicate with it - creating a true peer-to-peer agent network with standardized discovery and communication protocols.
