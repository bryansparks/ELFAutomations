# Testing Guide: kagent + AgentGateway Integration

This guide provides step-by-step instructions for testing both components of your integration:

1. **kagent**: Kubernetes-native agent deployment with LangGraph agents
2. **AgentGateway**: MCP proxy for centralized tool access and observability

## Prerequisites

### Environment Variables
Create a `.env` file in the project root:

```bash
# Required for TypeScript MCP servers
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Required for Anthropic LLM
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional for Firecrawl testing
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### Get Firecrawl API Key (for testing)
1. Visit [https://www.firecrawl.dev/app/api-keys](https://www.firecrawl.dev/app/api-keys)
2. Create an account and get your API key
3. Add it to your `.env` file

## Phase 1: Testing AgentGateway + MCP Servers

### Step 1: Build and Start Services

```bash
# Build TypeScript MCP servers
cd mcp-servers-ts
npm install
npm run build
cd ..

# Start the full stack
docker-compose up -d

# Check service status
docker-compose ps
```

### Step 2: Verify AgentGateway Health

```bash
# Check AgentGateway is running
curl http://localhost:3000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-...","services":{"mcp_servers":...}}
```

### Step 3: Run MCP Integration Tests

```bash
# Run the comprehensive test suite
python tests/test_agentgateway_mcp.py

# Expected output:
# - AgentGateway health check passed
# - Lists available MCP servers (supabase, business-tools, firecrawl)
# - Tests each MCP server's tools
# - Validates communication flow
```

### Step 4: Manual MCP Testing

```bash
# List available MCP servers
curl http://localhost:3000/mcp/servers

# List tools for a specific server
curl http://localhost:3000/mcp/servers/supabase/tools

# Call an MCP tool
curl -X POST http://localhost:3000/mcp/servers/business-tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_weather",
    "arguments": {"location": "San Francisco, CA"}
  }'
```

### Expected Results - Phase 1

✅ **AgentGateway Running**: Health endpoint responds  
✅ **TypeScript MCP Servers**: Supabase and Business Tools accessible  
✅ **Public MCP Server**: Firecrawl website scraping works  
✅ **Tool Calls**: All MCP tools respond correctly  
✅ **Error Handling**: Graceful error responses for invalid calls  

## Phase 2: Testing kagent + LangGraph Agent

### Step 1: Build Agent Container

First, create a Dockerfile for the Chief AI Agent:

```bash
# Create the Dockerfile
cat > docker/chief-ai-agent.Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install -e .

# Copy agent code
COPY agents/ ./agents/
COPY . .

# Expose health check port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the kagent-wrapped agent
CMD ["python", "-m", "agents.executive.chief_ai_kagent"]
EOF

# Build the container
docker build -f docker/chief-ai-agent.Dockerfile -t elf-automations/chief-ai-agent:latest .
```

### Step 2: Test Agent Locally

```bash
# Run the agent locally (without K8s)
docker run --rm \
  -e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
  -e AGENTGATEWAY_URL=http://host.docker.internal:3000 \
  -e LOG_LEVEL=info \
  --name test-chief-ai-agent \
  elf-automations/chief-ai-agent:latest
```

### Step 3: Deploy to Kubernetes

```bash
# Create namespace if it doesn't exist
kubectl create namespace elf-automations --dry-run=client -o yaml | kubectl apply -f -

# Create required secrets
kubectl create secret generic anthropic-credentials \
  --from-literal=api-key=${ANTHROPIC_API_KEY} \
  -n elf-automations

# Deploy kagent controller
kubectl apply -f k8s/kagent/deployment.yaml

# Deploy the Chief AI Agent
kubectl apply -f k8s/kagent/chief-ai-agent.yaml

# Check deployments
kubectl get pods -n elf-automations
kubectl logs -f deployment/chief-ai-agent -n elf-automations
```

### Step 4: Test Agent Communication

```bash
# Check agent health
kubectl port-forward service/chief-ai-agent 8080:8080 -n elf-automations &
curl http://localhost:8080/health

# Check agent registration with kagent
kubectl get configmaps -n elf-automations | grep agent-chief-ai-agent-status

# View agent status
kubectl get configmap agent-chief-ai-agent-status -n elf-automations -o yaml
```

### Expected Results - Phase 2

✅ **Agent Container**: Builds and runs successfully  
✅ **kagent Integration**: Agent registers with kagent controller  
✅ **K8s Deployment**: Pod starts and stays healthy  
✅ **AgentGateway Communication**: Agent can reach MCP tools  
✅ **LangGraph Workflow**: Agent processes messages through workflow  
✅ **Health Monitoring**: Health checks and metrics working  

## Phase 3: End-to-End Integration Testing

### Step 1: Test Agent → AgentGateway → MCP Flow

```bash
# Send a test message to the agent
kubectl exec -it deployment/chief-ai-agent -n elf-automations -- \
  python -c "
import asyncio
from agents.executive.chief_ai_kagent import KAgentChiefAI

async def test():
    agent = KAgentChiefAI()
    await agent.start()
    
    # Test message that should trigger MCP tool usage
    response = await agent.process_message(
        'Get the current weather in San Francisco and search for recent news about AI'
    )
    print('Agent Response:', response)
    
    await agent.stop()

asyncio.run(test())
"
```

### Step 2: Monitor the Full Stack

```bash
# Monitor AgentGateway logs
docker-compose logs -f agentgateway

# Monitor agent logs
kubectl logs -f deployment/chief-ai-agent -n elf-automations

# Monitor kagent controller logs
kubectl logs -f deployment/kagent-controller -n elf-automations
```

### Expected Results - Phase 3

✅ **Message Processing**: Agent receives and processes messages  
✅ **Tool Discovery**: Agent discovers MCP tools via AgentGateway  
✅ **Tool Execution**: Agent successfully calls MCP tools  
✅ **Response Generation**: Agent generates responses using tool results  
✅ **Observability**: Full request tracing through the stack  

## Troubleshooting

### Common Issues

**AgentGateway not starting:**
```bash
# Check logs
docker-compose logs agentgateway

# Common fixes:
# 1. Ensure TypeScript MCP servers are built: npm run build
# 2. Check environment variables are set
# 3. Verify config/agentgateway/gateway.json is valid
```

**MCP servers not responding:**
```bash
# Test individual MCP servers
npx -y firecrawl-mcp  # Should start Firecrawl MCP server
node mcp-servers-ts/dist/supabase/server.js  # Test TypeScript server

# Check environment variables:
echo $SUPABASE_URL $SUPABASE_ANON_KEY $FIRECRAWL_API_KEY
```

**Agent not connecting to AgentGateway:**
```bash
# Check network connectivity
kubectl exec -it deployment/chief-ai-agent -n elf-automations -- \
  curl -v http://agentgateway:3000/health

# Verify service names and ports
kubectl get services -n elf-automations
```

**kagent controller issues:**
```bash
# Check CRDs are installed
kubectl get crd | grep kagent

# Check controller logs
kubectl logs -f deployment/kagent-controller -n elf-automations

# Verify RBAC permissions
kubectl auth can-i create agents --as=system:serviceaccount:elf-automations:kagent-controller
```

## Success Criteria

Your integration is working correctly when:

1. ✅ **AgentGateway serves as MCP proxy** with visibility into all tool calls
2. ✅ **TypeScript MCP servers** work alongside public MCP servers  
3. ✅ **kagent deploys agents** as Kubernetes-native resources
4. ✅ **LangGraph agents** can discover and use MCP tools via AgentGateway
5. ✅ **Full observability** through logs, metrics, and health checks
6. ✅ **Template established** for future agent and MCP server deployments

This validates your complete architecture:
**LangGraph Agents → kagent (K8s) → AgentGateway → MCP Servers → Tools/Services**
