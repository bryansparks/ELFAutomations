# Google A2A Protocol Integration Guide
## Virtual AI Company Platform - Real A2A Implementation

**Version:** 1.0
**Purpose:** Integration guide for Google's official A2A (Agent-to-Agent) protocol
**Target:** Windsurf AI Assistant for implementation

---

## Google A2A Protocol Sources

### Official Repository
**Primary Source:** https://github.com/google-research/a2a
**Documentation:** https://a2a.dev (if available) or README in repository
**License:** Apache 2.0 (verify in repository)

### Repository Structure
```
google-research/a2a/
├── python/                 # Python A2A client and server
│   ├── a2a/               # Core A2A Python package
│   ├── examples/          # Python implementation examples
│   └── setup.py           # Python package setup
├── typescript/            # TypeScript A2A implementation
│   ├── src/a2a/          # Core A2A TypeScript package
│   ├── examples/         # TypeScript examples
│   └── package.json      # NPM package configuration
├── proto/                 # Protocol buffer definitions
│   └── a2a.proto         # A2A message schemas
├── docs/                  # Documentation and specifications
└── examples/              # Cross-language examples
```

---

## Installation and Setup Instructions

### For Python Components (CrewAI Agents)

#### Add to requirements.txt
```txt
# Google A2A Protocol - Official Implementation
git+https://github.com/google-research/a2a.git@main#subdirectory=python

# Supporting dependencies (verify versions in A2A requirements)
grpcio>=1.50.0
protobuf>=4.21.0
asyncio-grpc>=1.0.0
```

#### Installation Commands for Windsurf
```bash
# Navigate to project root
cd /path/to/virtual-ai-company

# Install A2A Python package
pip install git+https://github.com/google-research/a2a.git@main#subdirectory=python

# Verify installation
python -c "import a2a; print(f'A2A version: {a2a.__version__}')"
```

### For TypeScript Components (Infrastructure Services)

#### Add to package.json
```json
{
  "dependencies": {
    "@google-research/a2a": "git+https://github.com/google-research/a2a.git#subdirectory=typescript",
    "@grpc/grpc-js": "^1.8.0",
    "@grpc/proto-loader": "^0.7.0"
  }
}
```

#### Installation Commands for Windsurf
```bash
# Navigate to TypeScript service directory
cd infrastructure/a2a-services

# Install A2A TypeScript package
npm install git+https://github.com/google-research/a2a.git#subdirectory=typescript

# Verify installation
node -e "const a2a = require('@google-research/a2a'); console.log('A2A loaded successfully');"
```

---

## Integration Architecture

### Project Structure with Real A2A
```
virtual-ai-company/
├── agents/                          # CrewAI agents with A2A integration
│   ├── base/
│   │   ├── crew_a2a_agent.py       # Base agent using real A2A client
│   │   └── a2a_wrapper.py          # Wrapper for Google A2A Python client
│   ├── sales/
│   │   ├── sdr_agent.py            # SDR agent with A2A communication
│   │   └── sales_manager_agent.py  # Sales manager with A2A coordination
│   └── marketing/
│       ├── content_creator_agent.py
│       └── marketing_manager_agent.py
├── infrastructure/
│   ├── a2a-services/               # A2A infrastructure using TypeScript
│   │   ├── message-router/         # Using Google A2A message routing
│   │   ├── service-discovery/      # Using Google A2A discovery
│   │   └── context-store/          # A2A context management
│   └── kubernetes/
│       ├── a2a-infrastructure.yaml # K8s manifests for A2A services
│       └── agent-deployments/      # kagent CRDs with A2A configuration
├── mcp-servers/                    # MCP servers (unchanged)
└── requirements.txt                # Updated with A2A dependencies
```

---

## Implementation Examples

### Python Agent with Real A2A Integration

#### Base Agent Using Google A2A Client
```python
# agents/base/crew_a2a_agent.py
from crewai import Agent, Task, Crew
from a2a import A2AClient, A2AMessage, A2AConfig  # Google's official A2A
from a2a.discovery import ServiceDiscovery
from a2a.transport import GRPCTransport
import asyncio
from typing import Dict, Any, Optional

class CrewAIA2AAgent:
    def __init__(
        self,
        agent_id: str,
        role: str,
        backstory: str,
        a2a_config: A2AConfig
    ):
        self.agent_id = agent_id

        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role=role,
            backstory=backstory,
            verbose=True,
            allow_delegation=False  # A2A handles delegation
        )

        # Initialize Google A2A client
        self.a2a_client = A2AClient(
            agent_id=agent_id,
            config=a2a_config,
            transport=GRPCTransport()  # Use Google's gRPC transport
        )

        # Service discovery for finding other agents
        self.service_discovery = ServiceDiscovery(a2a_config)

    async def start(self):
        """Start A2A client and register with discovery service"""
        await self.a2a_client.start()
        await self.service_discovery.register_agent(
            agent_id=self.agent_id,
            capabilities=self.get_capabilities(),
            metadata=self.get_metadata()
        )

    async def stop(self):
        """Gracefully shutdown A2A client"""
        await self.service_discovery.unregister_agent(self.agent_id)
        await self.a2a_client.stop()

    async def send_message(
        self,
        target_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> A2AMessage:
        """Send message using Google A2A protocol"""

        # Create A2A message using Google's message format
        a2a_message = A2AMessage(
            sender_id=self.agent_id,
            recipient_id=target_agent,
            message_type=message_type,
            payload=payload,
            context=context or {},
            correlation_id=self.a2a_client.generate_correlation_id()
        )

        # Send via Google A2A client
        response = await self.a2a_client.send_message(a2a_message)
        return response

    async def handle_incoming_message(self, message: A2AMessage) -> A2AMessage:
        """Handle incoming A2A messages"""

        # Extract message details
        message_type = message.message_type
        payload = message.payload
        sender = message.sender_id

        # Process based on message type
        if message_type == "task_delegation":
            result = await self.handle_task_delegation(payload)
        elif message_type == "information_request":
            result = await self.handle_information_request(payload)
        elif message_type == "status_update":
            result = await self.handle_status_update(payload)
        else:
            result = {"error": f"Unknown message type: {message_type}"}

        # Create response using Google A2A format
        response = A2AMessage(
            sender_id=self.agent_id,
            recipient_id=sender,
            message_type=f"{message_type}_response",
            payload=result,
            correlation_id=message.correlation_id
        )

        return response

    def get_capabilities(self) -> list[str]:
        """Override in subclasses to define agent capabilities"""
        return ["base_agent"]

    def get_metadata(self) -> Dict[str, Any]:
        """Agent metadata for service discovery"""
        return {
            "department": self.get_department(),
            "agent_type": self.get_agent_type(),
            "version": "1.0.0",
            "framework": "crewai"
        }
```

#### Sales Agent Implementation with Real A2A
```python
# agents/sales/sdr_agent.py
from agents.base.crew_a2a_agent import CrewAIA2AAgent
from a2a import A2AConfig, A2AMessage
from crewai import Task
import os

class SDRAgent(CrewAIA2AAgent):
    def __init__(self):
        # A2A configuration from environment
        a2a_config = A2AConfig(
            discovery_endpoint=os.getenv("A2A_DISCOVERY_ENDPOINT"),
            message_router_endpoint=os.getenv("A2A_MESSAGE_ROUTER"),
            agent_port=int(os.getenv("A2A_AGENT_PORT", "8080"))
        )

        super().__init__(
            agent_id="sdr-agent",
            role="Sales Development Representative",
            backstory="""You are an experienced SDR focused on qualifying
            inbound leads and conducting initial outreach. You coordinate
            with marketing for lead sources and sales reps for handoffs.""",
            a2a_config=a2a_config
        )

    async def handle_task_delegation(self, payload: dict) -> dict:
        """Handle task delegation from other agents"""
        task_type = payload.get("task_type")

        if task_type == "qualify_lead":
            return await self.qualify_lead(payload["lead_data"])
        elif task_type == "initial_outreach":
            return await self.conduct_outreach(payload["prospect_data"])
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def qualify_lead(self, lead_data: dict) -> dict:
        """Qualify lead using CrewAI + notify sales rep via A2A"""

        # Use CrewAI for lead qualification
        qualification_task = Task(
            description=f"""
            Qualify this lead based on BANT criteria:
            Lead Data: {lead_data}

            Assess:
            - Budget: Can they afford our solution?
            - Authority: Are they a decision maker?
            - Need: Do they have a clear need for our product?
            - Timeline: When are they looking to implement?

            Provide a qualification score (0-1) and detailed assessment.
            """
        )

        crew = Crew(agents=[self.crew_agent], tasks=[qualification_task])
        result = crew.kickoff()

        # Parse CrewAI result
        qualification_result = {
            "qualified": result.score > 0.7,
            "score": result.score,
            "assessment": result.assessment,
            "next_steps": result.recommended_actions,
            "lead_id": lead_data.get("lead_id")
        }

        # If qualified, notify sales rep via Google A2A
        if qualification_result["qualified"]:
            await self.send_message(
                target_agent="sales-rep-agent",
                message_type="qualified_lead_handoff",
                payload={
                    "lead": qualification_result,
                    "qualification_details": result.detailed_assessment,
                    "recommended_approach": result.recommended_approach
                },
                context={
                    "workflow": "lead_qualification",
                    "priority": "high" if result.score > 0.9 else "normal"
                }
            )

        return qualification_result

    def get_capabilities(self) -> list[str]:
        return [
            "lead_qualification",
            "initial_outreach",
            "lead_scoring",
            "prospect_research"
        ]

    def get_department(self) -> str:
        return "sales"

    def get_agent_type(self) -> str:
        return "sdr"
```

### TypeScript A2A Infrastructure Services

#### Message Router Using Google A2A
```typescript
// infrastructure/a2a-services/message-router/router.ts
import { A2AMessageRouter, A2AConfig, A2AMessage } from '@google-research/a2a';
import { ServiceDiscovery } from '@google-research/a2a/discovery';
import express from 'express';

class A2AMessageRouterService {
    private router: A2AMessageRouter;
    private discovery: ServiceDiscovery;
    private app: express.Application;

    constructor(config: A2AConfig) {
        // Initialize Google A2A message router
        this.router = new A2AMessageRouter(config);
        this.discovery = new ServiceDiscovery(config);
        this.app = express();
        this.setupRoutes();
    }

    async start(port: number = 8080): Promise<void> {
        // Start Google A2A components
        await this.router.start();
        await this.discovery.start();

        // Start HTTP server for health checks
        this.app.listen(port, () => {
            console.log(`A2A Message Router running on port ${port}`);
        });
    }

    private setupRoutes(): void {
        // Health check for Kubernetes
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                router_status: this.router.getStatus(),
                discovery_status: this.discovery.getStatus()
            });
        });

        // Metrics endpoint
        this.app.get('/metrics', (req, res) => {
            res.json(this.router.getMetrics());
        });
    }

    async routeMessage(message: A2AMessage): Promise<void> {
        // Use Google A2A routing logic
        await this.router.routeMessage(message);
    }

    async stop(): Promise<void> {
        await this.router.stop();
        await this.discovery.stop();
    }
}

// Start the service
const config = new A2AConfig({
    discoveryEndpoint: process.env.A2A_DISCOVERY_ENDPOINT,
    messagePort: parseInt(process.env.A2A_MESSAGE_PORT || '8080'),
    grpcPort: parseInt(process.env.A2A_GRPC_PORT || '50051')
});

const routerService = new A2AMessageRouterService(config);
routerService.start().catch(console.error);
```

---

## Kubernetes Integration with Real A2A

### A2A Infrastructure Deployment
```yaml
# infrastructure/kubernetes/a2a-infrastructure.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: a2a-message-router
  namespace: a2a-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: a2a-message-router
  template:
    metadata:
      labels:
        app: a2a-message-router
    spec:
      containers:
      - name: message-router
        image: "elfautomations/a2a-message-router:v1.0.0"
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 50051
          name: grpc
        env:
        - name: A2A_DISCOVERY_ENDPOINT
          value: "a2a-discovery:8080"
        - name: A2A_GRPC_PORT
          value: "50051"
        - name: A2A_MESSAGE_PORT
          value: "8080"
        # Add Google A2A specific configuration
        - name: A2A_CONFIG_PATH
          value: "/etc/a2a/config.yaml"
        volumeMounts:
        - name: a2a-config
          mountPath: /etc/a2a
      volumes:
      - name: a2a-config
        configMap:
          name: a2a-config

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: a2a-config
  namespace: a2a-system
data:
  config.yaml: |
    # Google A2A configuration
    discovery:
      endpoint: "a2a-discovery:8080"
      refresh_interval: 30s

    transport:
      grpc:
        port: 50051
        tls_enabled: true

    routing:
      strategy: "round_robin"
      retry_policy:
        max_attempts: 3
        backoff: "exponential"

    context:
      storage: "redis"
      redis_url: "redis://redis-cluster:6379"
```

### Agent Deployment with Real A2A Configuration
```yaml
# agents/kubernetes/sdr-agent.yaml
apiVersion: kagent.dev/v1
kind: Agent
metadata:
  name: sdr-agent
  namespace: sales-department
spec:
  systemPrompt: |
    You are a Sales Development Representative using Google A2A protocol
    for coordination with marketing and sales teams.

  image: "elfautomations/sdr-agent:v1.0.0"
  replicas: 5

  # A2A configuration via environment variables
  env:
    - name: A2A_AGENT_ID
      value: "sdr-agent"
    - name: A2A_DISCOVERY_ENDPOINT
      value: "a2a-discovery.a2a-system:8080"
    - name: A2A_MESSAGE_ROUTER
      value: "a2a-message-router.a2a-system:50051"
    - name: A2A_AGENT_PORT
      value: "8080"
    - name: A2A_CONFIG_PATH
      value: "/etc/a2a/agent-config.yaml"

  # Mount A2A configuration
  volumeMounts:
    - name: a2a-agent-config
      mountPath: /etc/a2a

  volumes:
    - name: a2a-agent-config
      configMap:
        name: a2a-agent-config

  tools:
    - name: crm-qualification-tools
    - name: lead-scoring-tools
```

---

## Next Steps for Windsurf

### 1. Clone and Examine A2A Repository
```bash
# First, examine the official A2A implementation
git clone https://github.com/google-research/a2a.git
cd a2a

# Study the structure and examples
ls -la python/examples/
ls -la typescript/examples/
cat README.md
```

### 2. Update Project Dependencies
```bash
# Update requirements.txt with real A2A
echo "git+https://github.com/google-research/a2a.git@main#subdirectory=python" >> requirements.txt

# Update package.json for TypeScript services
cd infrastructure/a2a-services
npm install git+https://github.com/google-research/a2a.git#subdirectory=typescript
```

### 3. Implement Real A2A Integration
- Start with **TASK-005-REVISED** but use Google's A2A implementation
- Replace custom A2A client with Google's official Python client
- Use Google's TypeScript components for infrastructure services
- Follow Google's A2A message schemas and patterns

### 4. Configuration Management
- Study Google A2A configuration patterns from their examples
- Implement Kubernetes ConfigMaps for A2A service configuration
- Set up proper environment variables for agent A2A integration

**The key benefit: You get Google's proven, production-ready A2A implementation instead of building your own!** This saves significant development time and gives you a robust, well-tested communication protocol for your distributed agents.

Ready to integrate real Google A2A! 🚀
