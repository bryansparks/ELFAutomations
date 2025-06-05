# Technology Stack & Architecture - REVISED
## Virtual AI Company Platform - Distributed Agent Architecture

**Version:** 2.0 - Major Architecture Revision  
**Architecture Owner:** Engineering Team  
**Previous Version:** Replaced LangGraph monolithic approach with distributed agent architecture

---

## Technology Stack Overview

### Core Technologies

#### 1. **CrewAI Agent Framework**
**Purpose**: Individual agent implementation with role-based specialization  
**Version**: 0.70.0+  
**Key Features**: Role-based agents, task delegation, simple coordination patterns  
**Documentation**: https://docs.crewai.com/  

**Why CrewAI for Distributed Architecture:**
- Lightweight agent framework perfect for containerization
- Role-based agent design maps naturally to organizational structure
- Simple API that integrates well with A2A communication
- Easy to deploy individual agents as Kubernetes services

#### 2. **A2A (Agent-to-Agent) Communication Protocol**
**Purpose**: Rich inter-agent communication with context sharing  
**Implementation**: Google's Agent-to-Agent protocol + custom message queues  
**Key Features**: Service discovery, context preservation, async/sync messaging  
**Documentation**: https://github.com/google/a2a-protocol  

**A2A Integration Benefits:**
- Solves CrewAI's traditional inter-agent communication limitations
- Enables complex multi-agent workflows across distributed agents
- Provides conversation context sharing and persistence
- Supports both synchronous and asynchronous communication patterns

#### 3. **kagent - Kubernetes Agent Management**
**Purpose**: One CRD per agent type for independent lifecycle management  
**Version**: Latest stable  
**Key Features**: Individual agent scaling, per-agent monitoring, independent deployment  
**Documentation**: https://kagent.dev/docs  

**Distributed Agent Benefits:**
- Each agent type gets its own kagent CRD and scaling policy
- True Kubernetes-native deployment and management
- Per-agent metrics and resource utilization tracking
- Independent updates and rollbacks per agent type

#### 4. **Model Context Protocol (MCP)**
**Purpose**: Standardized tool interfaces (unchanged from previous architecture)  
**Version**: 1.0+  
**Implementation**: TypeScript MCP servers as independent microservices  
**Documentation**: https://modelcontextprotocol.io/  

#### 5. **AgentGateway**
**Purpose**: Secure, governed access to MCP servers (unchanged from previous architecture)  
**Implementation**: High-availability proxy layer with policy enforcement  
**Key Features**: Authentication, authorization, audit logging, rate limiting  

#### 6. **Kubernetes**
**Purpose**: Container orchestration with true microservice benefits for agents  
**Version**: 1.28+  
**Key Features**: Per-agent scaling, individual monitoring, independent deployment  
**Documentation**: https://kubernetes.io/docs/  

---

## Programming Languages & Frameworks

### Primary Languages
```yaml
Python:
  version: "3.11+"
  purpose: "CrewAI agent development, A2A integration, kagent integration"
  key_libraries:
    - crewai>=0.70.0
    - a2a-client>=1.0.0  # Custom A2A client library
    - fastapi>=0.104.0
    - pydantic>=2.0.0
    - asyncio (built-in)
    - kubernetes>=29.0.0

TypeScript:
  version: "Node.js 18+ / TypeScript 5+"
  purpose: "MCP server development (unchanged)"
  key_libraries:
    - "@modelcontextprotocol/sdk"
    - express
    - socket.io

Go:
  version: "1.21+"
  purpose: "A2A message routing, high-performance communication services"
  key_libraries:
    - gin-gonic/gin
    - gorilla/websocket
    - kubernetes/client-go
```

### Development Frameworks
```yaml
CrewAI_Framework:
  purpose: "Individual agent implementation"
  features: ["Role-based agents", "Task delegation", "Simple coordination"]
  benefits: ["Lightweight", "Container-friendly", "Easy A2A integration"]

A2A_Communication:
  purpose: "Inter-agent messaging and coordination"
  features: ["Service discovery", "Context preservation", "Message routing"]
  benefits: ["Rich communication", "Distributed workflows", "Fault tolerance"]

FastAPI:
  purpose: "Agent HTTP APIs, health checks, A2A endpoints"
  features: ["Auto-documentation", "Type validation", "Async support"]

Pydantic:
  purpose: "Data validation, agent configuration, message schemas"
  features: ["Runtime validation", "JSON schema", "Type safety"]
```

---

## Agent Implementation Architecture

### Individual Agent Structure

#### Base Agent Implementation
```python
from crewai import Agent, Task, Crew
from a2a_client import A2AClient
from fastapi import FastAPI
import asyncio

class DistributedCrewAIAgent:
    def __init__(self, agent_id: str, role: str, backstory: str):
        self.agent_id = agent_id
        self.crew_agent = Agent(
            role=role,
            backstory=backstory,
            verbose=True,
            allow_delegation=False  # Delegation handled via A2A
        )
        self.a2a_client = A2AClient(agent_id)
        self.app = FastAPI()
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.post("/task")
        async def handle_task(self, task_request: TaskRequest):
            """Handle direct task assignment"""
            result = await self.process_task(task_request)
            return {"result": result, "agent_id": self.agent_id}
            
        @self.app.post("/a2a/message")
        async def handle_a2a_message(self, message: A2AMessage):
            """Handle A2A communication from other agents"""
            response = await self.process_a2a_message(message)
            return response
            
        @self.app.get("/health")
        async def health_check(self):
            """Kubernetes health check"""
            return {"status": "healthy", "agent_id": self.agent_id}
            
    async def send_to_agent(self, target_agent: str, message: dict, context: dict = None):
        """Send message to another agent via A2A"""
        return await self.a2a_client.send_message(
            target_agent=target_agent,
            message=message,
            context=context,
            sender_id=self.agent_id
        )
        
    async def process_task(self, task_request: TaskRequest):
        """Process task using CrewAI + A2A coordination"""
        crew = Crew(
            agents=[self.crew_agent],
            tasks=[Task(description=task_request.description)],
            verbose=True
        )
        result = crew.kickoff()
        
        # Use A2A for any needed coordination
        if task_request.requires_coordination:
            await self.coordinate_with_other_agents(result)
            
        return result
```

#### Department-Specific Agent Examples

**Sales Development Representative Agent:**
```python
class SDRAgent(DistributedCrewAIAgent):
    def __init__(self):
        super().__init__(
            agent_id="sdr-agent",
            role="Sales Development Representative",
            backstory="""You are an experienced SDR focused on qualifying inbound leads 
            and conducting initial outreach. You work closely with marketing to understand 
            lead sources and with sales reps to ensure smooth handoffs."""
        )
        
    async def process_task(self, task_request: TaskRequest):
        if task_request.task_type == "qualify_lead":
            return await self.qualify_lead(task_request.lead_data)
        elif task_request.task_type == "outreach":
            return await self.conduct_outreach(task_request.prospect_data)
            
    async def qualify_lead(self, lead_data):
        # Use CrewAI for lead qualification
        qualification_task = Task(
            description=f"Qualify this lead: {lead_data}. Assess fit, budget, authority, need, timeline."
        )
        crew = Crew(agents=[self.crew_agent], tasks=[qualification_task])
        result = crew.kickoff()
        
        # If qualified, notify sales rep via A2A
        if result.qualified:
            await self.send_to_agent(
                target_agent="sales-rep-agent",
                message={
                    "type": "qualified_lead_handoff",
                    "lead": result.lead_details,
                    "qualification_score": result.score,
                    "next_steps": result.recommended_actions
                }
            )
            
        return result

class MarketingContentCreatorAgent(DistributedCrewAIAgent):
    def __init__(self):
        super().__init__(
            agent_id="content-creator-agent",
            role="Marketing Content Creator",
            backstory="""You are a skilled content creator specializing in B2B marketing 
            content. You work with marketing managers on content strategy and with social 
            media agents for content distribution."""
        )
        
    async def process_task(self, task_request: TaskRequest):
        if task_request.task_type == "create_blog_post":
            return await self.create_blog_post(task_request.brief)
        elif task_request.task_type == "create_social_content":
            return await self.create_social_content(task_request.campaign_data)
            
    async def create_blog_post(self, content_brief):
        # Use CrewAI for content creation
        content_task = Task(
            description=f"Create a blog post based on this brief: {content_brief}"
        )
        crew = Crew(agents=[self.crew_agent], tasks=[content_task])
        result = crew.kickoff()
        
        # Notify social media agent for distribution via A2A
        await self.send_to_agent(
            target_agent="social-media-agent",
            message={
                "type": "content_ready_for_distribution",
                "content": result.blog_post,
                "distribution_channels": ["linkedin", "twitter"],
                "target_audience": content_brief.target_audience
            }
        )
        
        return result
```

---

## A2A Communication Architecture

### Message Queue Infrastructure
```yaml
A2A_Core_Components:
  Message_Router:
    technology: "Apache Kafka / Redis Streams"
    purpose: "Route messages between agents"
    features: ["Message persistence", "Delivery guarantees", "Scalability"]
    
  Service_Discovery:
    technology: "Kubernetes DNS + Custom registry"
    purpose: "Agent discovery and capability advertisement"
    features: ["Dynamic registration", "Health checking", "Load balancing"]
    
  Context_Store:
    technology: "Redis with persistence"
    purpose: "Shared conversation context and agent memory"
    features: ["Fast access", "TTL support", "Clustering"]
    
  Message_Schema:
    technology: "Pydantic models + JSON Schema"
    purpose: "Type-safe message validation"
    features: ["Runtime validation", "Auto-documentation", "Versioning"]
```

### A2A Client Library
```python
class A2AClient:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.message_router = MessageRouter()
        self.service_discovery = ServiceDiscovery()
        self.context_store = ContextStore()
        
    async def send_message(
        self, 
        target_agent: str, 
        message: dict, 
        context: dict = None,
        message_type: str = "request"
    ) -> A2AResponse:
        """Send message to target agent with context"""
        
        # Discover target agent
        target_info = await self.service_discovery.find_agent(target_agent)
        if not target_info:
            raise AgentNotFoundError(f"Agent {target_agent} not found")
            
        # Prepare message with context
        full_message = A2AMessage(
            from_agent=self.agent_id,
            to_agent=target_agent,
            message_type=message_type,
            payload=message,
            context=context or {},
            timestamp=datetime.utcnow(),
            correlation_id=str(uuid.uuid4())
        )
        
        # Store context for conversation continuity
        if context:
            await self.context_store.update_conversation_context(
                conversation_id=f"{self.agent_id}-{target_agent}",
                context=context
            )
            
        # Route message
        response = await self.message_router.send_message(full_message)
        return response
        
    async def register_agent(self, capabilities: List[str], health_endpoint: str):
        """Register agent with service discovery"""
        await self.service_discovery.register_agent(
            agent_id=self.agent_id,
            capabilities=capabilities,
            health_endpoint=health_endpoint,
            metadata={
                "department": self.get_department(),
                "agent_type": self.get_agent_type(),
                "version": self.get_version()
            }
        )
```

### Message Types and Schemas
```python
from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any
from datetime import datetime

class A2AMessage(BaseModel):
    from_agent: str
    to_agent: str
    message_type: Literal["request", "response", "notification", "delegation"]
    payload: Dict[str, Any]
    context: Dict[str, Any] = {}
    timestamp: datetime
    correlation_id: str
    priority: Literal["low", "normal", "high", "urgent"] = "normal"

class TaskDelegationMessage(BaseModel):
    task_type: str
    task_description: str
    deadline: Optional[datetime] = None
    priority: str = "normal"
    required_capabilities: List[str] = []
    context: Dict[str, Any] = {}

class InformationRequestMessage(BaseModel):
    request_type: str
    questions: List[str]
    context: Dict[str, Any] = {}
    urgency: str = "normal"

class StatusUpdateMessage(BaseModel):
    update_type: str
    status: str
    metrics: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
```

---

## Kubernetes Deployment Architecture

### Per-Agent kagent CRDs

#### Sales Development Representative Deployment
```yaml
apiVersion: kagent.dev/v1
kind: Agent
metadata:
  name: sdr-agent
  namespace: sales-department
  labels:
    department: sales
    agent-type: sdr
    role: lead-qualification
spec:
  systemPrompt: |
    You are a Sales Development Representative (SDR) focused on qualifying 
    inbound leads and conducting initial outreach. You work with marketing 
    teams to understand lead sources and coordinate with sales representatives 
    for smooth handoffs of qualified prospects.
    
  # CrewAI + A2A agent container
  image: "elfautomations/sdr-agent:v1.0.0"
  
  # High-volume agent scaling
  replicas: 5
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 15
    targetCPUUtilization: 70
    customMetrics:
      - name: "leads_in_queue"
        targetValue: "10"
      - name: "qualification_rate"
        targetValue: "0.8"
  
  # Resource allocation optimized for qualification workload
  resources:
    requests:
      memory: "256Mi"
      cpu: "200m"
    limits:
      memory: "512Mi"
      cpu: "400m"
      
  # A2A communication configuration
  env:
    - name: A2A_AGENT_ID
      value: "sdr-agent"
    - name: A2A_DISCOVERY_ENDPOINT
      value: "http://a2a-discovery:8080"
    - name: A2A_MESSAGE_ROUTER
      value: "kafka://kafka-cluster:9092"
    - name: DEPARTMENT
      value: "sales"
      
  # MCP tools for lead qualification
  tools:
    - name: crm-qualification-tools
    - name: lead-scoring-tools
    - name: email-outreach-tools
    
  # Health checks specific to agent functionality
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
    
  readinessProbe:
    httpGet:
      path: /ready
      port: 8080
    initialDelaySeconds: 10
    periodSeconds: 5

---
apiVersion: kagent.dev/v1
kind: Agent
metadata:
  name: content-creator-agent
  namespace: marketing-department
  labels:
    department: marketing
    agent-type: content-creator
    role: content-generation
spec:
  systemPrompt: |
    You are a Marketing Content Creator specializing in B2B content creation.
    You create blog posts, whitepapers, social media content, and marketing 
    materials. You collaborate with marketing managers on strategy and social 
    media agents for content distribution.
    
  image: "elfautomations/content-creator-agent:v1.0.0"
  
  # Content creation scaling - less frequent but resource intensive
  replicas: 2
  autoscaling:
    enabled: true
    minReplicas: 1
    maxReplicas: 5
    targetCPUUtilization: 80
    customMetrics:
      - name: "content_requests_queue"
        targetValue: "5"
        
  # Higher resource allocation for content generation
  resources:
    requests:
      memory: "512Mi"
      cpu: "400m"
    limits:
      memory: "1Gi"
      cpu: "800m"
      
  env:
    - name: A2A_AGENT_ID
      value: "content-creator-agent"
    - name: A2A_DISCOVERY_ENDPOINT
      value: "http://a2a-discovery:8080"
    - name: DEPARTMENT
      value: "marketing"
      
  tools:
    - name: content-generation-tools
    - name: seo-optimization-tools
    - name: brand-guidelines-tools
```

### A2A Infrastructure Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: a2a-message-router
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
        env:
        - name: KAFKA_BROKERS
          value: "kafka-cluster:9092"
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: a2a-service-discovery
spec:
  replicas: 2
  selector:
    matchLabels:
      app: a2a-service-discovery
  template:
    metadata:
      labels:
        app: a2a-service-discovery
    spec:
      containers:
      - name: service-discovery
        image: "elfautomations/a2a-service-discovery:v1.0.0"
        ports:
        - containerPort: 8080
        env:
        - name: KUBERNETES_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
```

---

## Monitoring & Observability

### Per-Agent Metrics
```yaml
Agent_Specific_Metrics:
  Resource_Metrics:
    - cpu_utilization_per_agent_type
    - memory_usage_per_agent_type
    - request_response_time_per_agent
    - task_completion_rate_per_agent
    
  Business_Metrics:
    - leads_qualified_per_sdr_agent
    - content_pieces_created_per_content_agent
    - support_tickets_resolved_per_support_agent
    - sales_conversions_per_sales_agent
    
  A2A_Communication_Metrics:
    - message_latency_between_agents
    - message_success_rate_per_agent_pair
    - conversation_context_preservation_rate
    - inter_department_coordination_success

Kubernetes_Native_Metrics:
  - pod_scaling_events_per_agent_type
  - resource_efficiency_per_agent
  - deployment_success_rate_per_agent
  - health_check_success_rate_per_agent
```

### Monitoring Stack Integration
```yaml
Prometheus_Configuration:
  scrape_configs:
    - job_name: 'sdr-agents'
      kubernetes_sd_configs:
        - role: pod
          namespaces:
            names: ['sales-department']
      relabel_configs:
        - source_labels: [__meta_kubernetes_pod_label_agent_type]
          target_label: agent_type
          
    - job_name: 'content-creator-agents'
      kubernetes_sd_configs:
        - role: pod
          namespaces:
            names: ['marketing-department']
            
Grafana_Dashboards:
  - sales_department_dashboard:
      panels:
        - sdr_agent_performance
        - sales_rep_agent_metrics
        - lead_conversion_funnel
        
  - marketing_department_dashboard:
      panels:
        - content_creation_velocity
        - social_media_engagement
        - campaign_performance
        
  - a2a_communication_dashboard:
      panels:
        - inter_agent_message_flow
        - communication_latency_heatmap
        - context_preservation_metrics
```

---

## Development Workflow

### Individual Agent Development
```python
# Development structure for individual agents
agents/
├── base/
│   ├── distributed_crew_agent.py    # Base agent class
│   ├── a2a_client.py                # A2A communication client
│   └── health_checks.py             # Kubernetes health checks
├── sales/
│   ├── sdr_agent.py                 # SDR agent implementation
│   ├── sales_rep_agent.py           # Sales rep agent
│   └── sales_manager_agent.py       # Sales manager agent
├── marketing/
│   ├── content_creator_agent.py     # Content creator
│   ├── social_media_agent.py        # Social media manager
│   └── marketing_manager_agent.py   # Marketing manager
└── tests/
    ├── unit/                        # Unit tests per agent
    ├── integration/                 # A2A integration tests
    └── e2e/                         # End-to-end workflow tests
```

### Container Build Process
```dockerfile
# Multi-stage build for individual agents
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Security: non-root user
RUN useradd --create-home --shell /bin/bash agent
USER agent
WORKDIR /home/agent

# Copy dependencies and agent code
COPY --from=builder /root/.local /home/agent/.local
COPY --chown=agent:agent agents/base/ ./base/
COPY --chown=agent:agent agents/sales/sdr_agent.py ./agent.py

# Health check for Kubernetes
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Environment variables for A2A
ENV A2A_AGENT_ID=sdr-agent
ENV PORT=8080

EXPOSE 8080
CMD ["python", "agent.py"]
```

---

## Migration Strategy

### From LangGraph Monolithic to Distributed Agents

#### Phase 1: Infrastructure Preparation
- Deploy A2A communication infrastructure
- Update kagent CRDs for individual agent deployment
- Prepare CrewAI agent base classes

#### Phase 2: Agent-by-Agent Migration
- Start with simple agents (SDR, Content Creator)
- Implement A2A communication patterns
- Validate independent scaling and monitoring

#### Phase 3: Complex Workflow Migration
- Migrate manager-level agents with coordination responsibilities
- Implement cross-department A2A workflows
- Optimize resource allocation per agent type

#### Phase 4: Production Optimization
- Fine-tune scaling policies per agent type
- Optimize A2A communication performance
- Implement advanced monitoring and alerting

This distributed agent architecture provides true Kubernetes-native deployment with granular scaling, detailed observability, and independent agent lifecycle management while enabling sophisticated multi-agent coordination through A2A communication.
