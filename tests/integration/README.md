# Distributed Agent Architecture - Integration Test Suite

This comprehensive test framework validates the complete distributed agent architecture, ensuring all components work correctly together in production-like environments.

## Architecture Overview

The test suite validates this distributed agent architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Kubernetes     │    │     kagent      │    │   Individual    │
│  Foundation     │───►│   Controller    │───►│    Agents       │
│  (minikube)     │    │   (CRDs)        │    │  (CrewAI+A2A)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         │              ┌─────────────────┐             │
         └─────────────►│ AgentGateway    │◄────────────┘
                        │  (MCP Proxy)    │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   MCP Servers   │
                        │ (Tools/Services)│
                        └─────────────────┘
```

## Test Suites

### 1. 🏗️ Kubernetes Foundation (`test_k8s_foundation.py`)

Validates the underlying Kubernetes infrastructure:

- **Cluster Connectivity**: minikube status and kubectl access
- **Docker Availability**: Docker daemon running and accessible
- **Namespace Management**: `elf-automations` namespace creation
- **RBAC Permissions**: Service accounts and role bindings
- **CRD Installation**: kagent Custom Resource Definitions
- **Controller Status**: kagent controller pod health
- **Resource Quotas**: Memory, CPU, and storage limits

### 2. 🚀 Agent Deployment (`test_agent_deployment.py`)

Tests agent deployment and lifecycle management:

- **Docker Images**: Agent container images available
- **Secrets Configuration**: OpenAI API keys and credentials
- **Chief AI Agent**: Executive leadership agent deployment
- **Pod Health**: Kubernetes health and readiness probes
- **API Endpoints**: Agent HTTP endpoints accessibility
- **CrewAI Tasks**: Task execution and completion
- **Scaling**: Agent replica management
- **Lifecycle**: Startup, shutdown, and restart handling

### 3. 🔄 A2A Communication (`test_a2a_communication.py`)

Validates Google A2A protocol integration:

- **SDK Availability**: A2A Python SDK imports and setup
- **AgentCard Generation**: Proper agent metadata structure
- **Agent Capabilities**: Skills, modes, and capabilities config
- **A2A Server**: Agent-to-agent communication server
- **Registration**: Agent discovery and registration
- **Task Store**: Task persistence and management
- **Queue Manager**: Event queuing and streaming
- **Messaging**: Inter-agent communication
- **Workflows**: Multi-agent coordination
- **Event Streaming**: Real-time agent collaboration

### 4. 🌐 AgentGateway + MCP (`test_agentgateway_mcp.py`)

Tests MCP server integration and tool access:

- **Docker Image**: AgentGateway container build and config
- **Configuration**: Gateway setup and validation
- **Deployment**: Kubernetes deployment and services
- **Health Checks**: Gateway connectivity and status
- **MCP Discovery**: MCP server registration and discovery
- **Proxy Functionality**: Request routing and response handling
- **Agent Integration**: Agent access to MCP tools
- **Tool Execution**: End-to-end tool invocation
- **Multiple Servers**: Multi-MCP server support
- **Error Handling**: Resilience and failure recovery

## Quick Start

### Run All Tests

```bash
# Run complete integration test suite
./run_integration_tests.py

# Or with Python
python3 run_integration_tests.py
```

### Run Specific Test Suite

```bash
# Kubernetes foundation only
./run_integration_tests.py --suite k8s

# Agent deployment only
./run_integration_tests.py --suite agents

# A2A communication only
./run_integration_tests.py --suite a2a

# AgentGateway + MCP only
./run_integration_tests.py --suite gateway
```

### Get Test Suite Information

```bash
./run_integration_tests.py --info
```

## Prerequisites

### Required Infrastructure

1. **minikube** - Local Kubernetes cluster
   ```bash
   minikube start
   ```

2. **Docker** - Container runtime
   ```bash
   docker --version
   ```

3. **kubectl** - Kubernetes CLI
   ```bash
   kubectl cluster-info
   ```

### Required Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install A2A SDK (when available)
pip install a2a-sdk
```

### Docker Images

The following Docker images must be available:

- `elf-automations/distributed-agent:latest`
- `elf-automations/chief-ai-agent:latest`
- `elf-automations/agentgateway:latest`

Build them with:
```bash
# Build distributed agent image
docker build -t elf-automations/distributed-agent:latest .

# Build AgentGateway image
cd third-party/agentgateway
docker build -t elf-automations/agentgateway:latest .
```

## Test Output

The test framework provides clear, colorful output with:

- ✅ **PASSED** - Test completed successfully
- ❌ **FAILED** - Test failed with error details
- ⏳ **RUNNING** - Test currently executing
- ⏱️ **Duration** - Execution time for each test
- 📊 **Summary** - Overall results and statistics

Example output:
```
🧪 Kubernetes Foundation Tests
  ✅ Cluster Connectivity                    (2.1s)
  ✅ Docker Availability                     (0.8s)
  ✅ Namespace Creation                      (1.2s)
  ❌ RBAC Permissions                        (0.5s) - ServiceAccount not found

📊 Results: 3 passed, 1 failed, 4 total (4.6s)
```

## Test Configuration

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for agent testing
- `KUBECONFIG` - Kubernetes configuration (optional)

### Kubernetes Namespace

All tests run in the `elf-automations` namespace, which is created automatically.

### Test Timeouts

- Pod startup: 120 seconds
- HTTP endpoints: 30 seconds
- Command execution: 60 seconds
- Port forwarding: 10 seconds

## Troubleshooting

### Common Issues

1. **minikube not running**
   ```bash
   minikube start
   ```

2. **Docker images not found**
   ```bash
   docker images | grep elf-automations
   # Build missing images
   ```

3. **kubectl access denied**
   ```bash
   kubectl config current-context
   kubectl cluster-info
   ```

4. **Namespace issues**
   ```bash
   kubectl create namespace elf-automations
   ```

### Debug Mode

For detailed debugging, check individual test logs:

```bash
# Check pod logs
kubectl logs -n elf-automations -l app=chief-ai-agent

# Check controller logs
kubectl logs -n elf-automations -l app=kagent-controller

# Check service status
kubectl get all -n elf-automations
```

## CI/CD Integration

The test suite is designed for CI/CD integration:

```yaml
# GitHub Actions example
- name: Run Integration Tests
  run: |
    minikube start
    ./run_integration_tests.py

# Exit codes:
# 0 - All tests passed
# 1 - Some tests failed
# 130 - Tests interrupted
```

## Contributing

When adding new tests:

1. Follow the `TestSuite` base class pattern
2. Use async/await for all operations
3. Include proper cleanup in test methods
4. Add descriptive test names and error messages
5. Update this README with new test descriptions

## Architecture Benefits Validated

This test suite validates the key benefits of our distributed agent architecture:

- ✅ **Native Kubernetes Integration** - Each agent as independent pod
- ✅ **Standardized Communication** - A2A protocol between agents
- ✅ **Real-time Collaboration** - EventQueues for streaming workflows
- ✅ **Production Readiness** - Monitoring, scaling, health checks
- ✅ **Framework Flexibility** - CrewAI + A2A + MCP integration
- ✅ **Granular Observability** - Per-agent metrics and lifecycle
- ✅ **Independent Scaling** - Right-sized resources per agent type
- ✅ **Failure Isolation** - Agent failures don't cascade

This represents a breakthrough pattern for scalable agent mesh applications that can be applied across a wide array of distributed AI systems.
