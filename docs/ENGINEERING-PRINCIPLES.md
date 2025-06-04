# Engineering Principles & Guidelines
## Virtual AI Company Platform

**Version:** 1.0  
**Date:** June 2025  
**Owner:** Engineering Team  

---

## Core Engineering Principles

### 1. **Agent-First Architecture**
Every system component should be designed with autonomous AI agents as the primary users, not humans. This means APIs, interfaces, and workflows should prioritize machine-readable formats, standardized protocols, and predictable behaviors that agents can reliably interact with.

**Implementation Guidelines:**
- Design APIs with consistent, machine-parseable responses
- Use structured data formats (JSON Schema, OpenAPI) for all interfaces
- Implement deterministic behaviors with clear error handling
- Prioritize async/await patterns for non-blocking agent interactions

### 2. **Hierarchical Scalability**
The system must scale both horizontally (more agents) and vertically (more complex agent hierarchies) without architectural changes. Each layer of the organizational hierarchy should be independently scalable.

**Implementation Guidelines:**
- Use Kubernetes CRDs for declarative agent scaling
- Implement resource quotas and limits at department levels
- Design stateless agent services with external state management
- Use event-driven architecture for cross-departmental communication

### 3. **Protocol Standardization**
All agent-to-tool and agent-to-agent communications must use standardized protocols to ensure interoperability, maintainability, and extensibility.

**Implementation Guidelines:**
- Implement MCP for all tool integrations
- Use OpenAPI specifications for internal APIs
- Standardize message formats using JSON Schema
- Implement versioning strategies for protocol evolution

### 4. **Observable Autonomous Operations**
Since agents operate autonomously, comprehensive observability is critical for understanding system behavior, debugging issues, and optimizing performance.

**Implementation Guidelines:**
- Implement distributed tracing for all multi-agent workflows
- Log all agent decisions with context and reasoning
- Create business-level metrics alongside technical metrics
- Build real-time dashboards for both technical and business stakeholders

### 5. **Fault-Tolerant Workflows**
Agent workflows must be resilient to individual agent failures, external service outages, and partial system degradation while maintaining business continuity.

**Implementation Guidelines:**
- Implement circuit breakers for external service calls
- Use exponential backoff with jitter for retries
- Design workflows with graceful degradation modes
- Implement automatic failover and recovery mechanisms

---

## Development Standards

### Code Organization

#### Project Structure
```
project-root/
├── agents/                 # Agent definitions and workflows
│   ├── executive/         # Executive layer agents
│   ├── departments/       # Department-specific agents
│   └── individual/        # Individual contributor agents
├── mcp-servers/           # Custom MCP server implementations
│   ├── business-tools/    # Business-specific tools
│   ├── integrations/      # Third-party integrations
│   └── utilities/         # Common utility tools
├── k8s/                   # Kubernetes manifests
│   ├── base/              # Base configurations
│   ├── overlays/          # Environment-specific overlays
│   └── operators/         # Custom operators
├── workflows/             # LangGraph workflow definitions
│   ├── cross-department/  # Inter-department workflows
│   └── department/        # Department-specific workflows
├── apis/                  # REST/GraphQL API implementations
├── tests/                 # Test suites
├── docs/                  # Documentation
└── tools/                 # Development and deployment tools
```

#### Naming Conventions
```yaml
Agents:
  Classes: "PascalCase with Agent suffix (e.g., SalesManagerAgent)"
  Instances: "kebab-case in k8s (e.g., sales-manager-agent)"
  Files: "snake_case.py (e.g., sales_manager_agent.py)"

Workflows:
  LangGraph: "snake_case (e.g., lead_qualification_workflow)"
  Files: "snake_case.py (e.g., lead_qualification.py)"

MCP Servers:
  Classes: "PascalCase with Server suffix (e.g., CRMServer)"
  Executables: "kebab-case (e.g., crm-server)"

APIs:
  Endpoints: "kebab-case (/api/v1/agent-status)"
  Functions: "snake_case (get_agent_status)"
```

### Code Quality Standards

#### Python Code Standards
```python
# Type hints are mandatory for all functions
from typing import Dict, List, Optional, Union
import asyncio
from dataclasses import dataclass
from pydantic import BaseModel, Field

# Use Pydantic for all data models
class AgentConfig(BaseModel):
    name: str = Field(..., description="Agent name")
    department: str = Field(..., description="Department assignment")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    
class AgentResponse(BaseModel):
    agent_id: str
    status: str
    message: Optional[str] = None
    
# Async-first for all agent operations
async def create_agent(config: AgentConfig) -> AgentResponse:
    """Create a new agent instance with the given configuration."""
    try:
        # Implementation here
        return AgentResponse(
            agent_id=f"{config.department}-{config.name}",
            status="created",
            message="Agent successfully created"
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise

# Use structured logging
import structlog
logger = structlog.get_logger()

# Error handling with context
class AgentError(Exception):
    def __init__(self, message: str, agent_id: str, context: Dict = None):
        self.message = message
        self.agent_id = agent_id
        self.context = context or {}
        super().__init__(f"Agent {agent_id}: {message}")
```

#### Documentation Standards
```python
def process_customer_inquiry(
    inquiry: CustomerInquiry,
    assigned_agent: str,
    priority: int = 1
) -> InquiryResponse:
    """Process a customer inquiry through the appropriate agent workflow.
    
    This function routes customer inquiries to the correct department agent
    based on inquiry type and current workload distribution.
    
    Args:
        inquiry: Customer inquiry containing message, contact info, and metadata
        assigned_agent: Agent ID to handle the inquiry
        priority: Inquiry priority (1=low, 5=critical)
        
    Returns:
        InquiryResponse containing status, agent assignment, and estimated resolution time
        
    Raises:
        AgentNotFoundError: When assigned agent is not available
        WorkflowTimeoutError: When inquiry processing exceeds timeout
        
    Examples:
        >>> inquiry = CustomerInquiry(message="Need help with billing", type="support")
        >>> response = process_customer_inquiry(inquiry, "support-agent-1")
        >>> print(response.status)
        "assigned"
    """
```

### Testing Standards

#### Test Structure
```python
# tests/agents/test_sales_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from agents.sales import SalesAgent
from mcp_servers.crm import CRMServer

class TestSalesAgent:
    @pytest.fixture
    async def sales_agent(self):
        """Create a sales agent for testing."""
        mock_crm = AsyncMock(spec=CRMServer)
        agent = SalesAgent(
            name="test-sales-agent",
            tools=["crm", "email"],
            crm_server=mock_crm
        )
        return agent
    
    @pytest.mark.asyncio
    async def test_qualify_lead_success(self, sales_agent):
        """Test successful lead qualification workflow."""
        # Given
        lead_data = {
            "name": "John Doe",
            "company": "Test Corp",
            "email": "john@testcorp.com"
        }
        
        # When
        result = await sales_agent.qualify_lead(lead_data)
        
        # Then
        assert result.status == "qualified"
        assert result.score > 0.7
        sales_agent.crm_server.create_lead.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_qualify_lead_insufficient_data(self, sales_agent):
        """Test lead qualification with insufficient data."""
        # Given
        incomplete_lead = {"name": "John Doe"}
        
        # When/Then
        with pytest.raises(ValueError, match="Missing required lead information"):
            await sales_agent.qualify_lead(incomplete_lead)

# Integration tests
class TestSalesWorkflow:
    @pytest.mark.integration
    async def test_end_to_end_lead_processing(self):
        """Test complete lead processing from marketing to sales."""
        # Given: A lead from marketing
        # When: Processing through sales workflow
        # Then: Lead is properly qualified and assigned
        pass
```

#### Test Categories
```yaml
Unit Tests:
  scope: "Individual agent methods and functions"
  coverage: "95% minimum code coverage"
  speed: "< 100ms per test"
  isolation: "Mocked external dependencies"

Integration Tests:
  scope: "Agent-to-agent and agent-to-tool interactions"
  coverage: "Critical business workflows"
  speed: "< 5 seconds per test"
  environment: "Local test environment with real services"

End-to-End Tests:
  scope: "Complete business processes across departments"
  coverage: "Primary user journeys"
  speed: "< 30 seconds per test"
  environment: "Staging environment with production-like data"

Performance Tests:
  scope: "Scalability and resource utilization"
  metrics: "Response time, throughput, resource usage"
  benchmarks: "100 agents, 1000 tasks/minute"
  tools: "Locust, K6, custom load generators"
```

### Configuration Management

#### Environment Configuration
```yaml
# config/base/config.yaml
agents:
  default_model: "claude-3-5-sonnet-20241022"
  max_concurrent_tasks: 10
  timeout_seconds: 30
  retry_attempts: 3

departments:
  sales:
    agent_count: 5
    tools: ["crm", "email", "calendar"]
    budget_limits:
      api_calls_per_hour: 1000
      
  marketing:
    agent_count: 3
    tools: ["social_media", "analytics", "content"]
    budget_limits:
      api_calls_per_hour: 500

# config/environments/production.yaml
observability:
  logging_level: "INFO"
  metrics_enabled: true
  tracing_enabled: true
  
security:
  require_tls: true
  api_rate_limiting: true
  audit_logging: true
```

#### Secrets Management
```yaml
# Never commit secrets to version control
# Use Kubernetes secrets or external secret management

apiVersion: v1
kind: Secret
metadata:
  name: ai-model-api-keys
type: Opaque
data:
  anthropic-api-key: <base64-encoded-key>
  openai-api-key: <base64-encoded-key>
---
# Reference secrets in agent configurations
apiVersion: kagent.dev/v1
kind: Agent
metadata:
  name: sales-agent
spec:
  model:
    apiKeyRef:
      secretName: ai-model-api-keys
      key: anthropic-api-key
```

### Deployment Standards

#### Container Standards
```dockerfile
# Multi-stage builds for optimization
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Security: run as non-root user
RUN useradd --create-home --shell /bin/bash agent
USER agent
WORKDIR /home/agent

# Copy dependencies and code
COPY --from=builder /root/.local /home/agent/.local
COPY --chown=agent:agent . .

# Health checks
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python health_check.py

# Labels for metadata
LABEL org.opencontainers.image.source="https://github.com/company/ai-company"
LABEL org.opencontainers.image.description="Virtual AI Company Agent"
LABEL org.opencontainers.image.version="1.0.0"

CMD ["python", "-m", "agents.main"]
```

#### Kubernetes Deployment Standards
```yaml
# Resource limits and requests are mandatory
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# Security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false

# Probes for health monitoring
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
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Performance Guidelines

#### Response Time Requirements
```yaml
Agent_Response_Times:
  simple_tasks: "< 2 seconds"
  complex_reasoning: "< 10 seconds"
  cross_department_coordination: "< 15 seconds"
  
API_Response_Times:
  health_checks: "< 100ms"
  agent_status: "< 500ms"
  workflow_initiation: "< 1 second"
  
Database_Operations:
  reads: "< 100ms"
  writes: "< 200ms"
  complex_queries: "< 1 second"
```

#### Resource Optimization
```python
# Use connection pooling for external services
from aiohttp import ClientSession, TCPConnector

class OptimizedMCPServer:
    def __init__(self):
        connector = TCPConnector(limit=100, limit_per_host=30)
        self.session = ClientSession(connector=connector)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

# Implement caching for expensive operations
from functools import lru_cache
import asyncio

class AgentMemory:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = {}
    
    async def get_with_ttl(self, key: str, ttl: int = 300):
        """Get cached value with time-to-live."""
        if key in self._cache:
            if time.time() - self._cache_ttl[key] < ttl:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._cache_ttl[key]
        return None
```

### Security Guidelines

#### Authentication & Authorization
```python
# JWT token validation
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_agent_token(token: str = Depends(security)):
    """Verify agent JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        agent_id = payload.get("agent_id")
        if agent_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return agent_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Role-based access control
class AgentPermissions:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.roles = self._get_agent_roles(agent_id)
    
    def can_access_department(self, department: str) -> bool:
        """Check if agent can access department resources."""
        return department in self.roles or "admin" in self.roles
```

#### Data Protection
```python
# Encrypt sensitive data
from cryptography.fernet import Fernet

class SecureAgentData:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_agent_memory(self, data: dict) -> bytes:
        """Encrypt agent memory data."""
        json_data = json.dumps(data).encode()
        return self.cipher.encrypt(json_data)
    
    def decrypt_agent_memory(self, encrypted_data: bytes) -> dict:
        """Decrypt agent memory data."""
        decrypted_data = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
```

### Error Handling & Monitoring

#### Structured Error Handling
```python
import structlog
from enum import Enum

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentException(Exception):
    def __init__(
        self, 
        message: str, 
        agent_id: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: dict = None
    ):
        self.message = message
        self.agent_id = agent_id
        self.severity = severity
        self.context = context or {}
        
        # Log the error with structured data
        logger = structlog.get_logger()
        logger.error(
            "Agent error occurred",
            agent_id=agent_id,
            error_message=message,
            severity=severity.value,
            context=context,
            error_type=self.__class__.__name__
        )
        
        super().__init__(message)

# Circuit breaker pattern for external services
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time < self.timeout:
                raise CircuitBreakerOpenError("Circuit breaker is open")
            else:
                self.state = "half-open"
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise e
```

These engineering principles ensure the Virtual AI Company Platform is built with enterprise-grade reliability, maintainability, and scalability while supporting the unique requirements of autonomous AI agent operations.
