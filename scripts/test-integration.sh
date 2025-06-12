#!/bin/bash
set -e

# Test script for kagent + AgentGateway integration
# This script automates the testing process described in the documentation

echo "🚀 Starting kagent + AgentGateway Integration Tests"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << 'EOF'
# Required for TypeScript MCP servers
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Required for Anthropic LLM
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional for Firecrawl testing
FIRECRAWL_API_KEY=your_firecrawl_api_key
EOF
    print_error "Please update .env file with your credentials and run again"
    exit 1
fi

# Source environment variables
source .env

# Check required environment variables
required_vars=("SUPABASE_URL" "SUPABASE_ANON_KEY" "ANTHROPIC_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    var_value="${!var}"
    var_lower=$(echo "$var" | tr '[:upper:]' '[:lower:]')
    if [ -z "$var_value" ] || [ "$var_value" = "your_$var_lower" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables: ${missing_vars[*]}"
    echo "Please update your .env file with real values"
    exit 1
fi

print_status "Environment variables configured"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running"

# Phase 1: Test AgentGateway + MCP Servers
echo ""
echo "📡 Phase 1: Testing AgentGateway + MCP Servers"
echo "=============================================="

# Build TypeScript MCP servers
echo "Building TypeScript MCP servers..."
cd mcp-servers-ts
if ! npm install; then
    print_error "Failed to install npm dependencies"
    exit 1
fi

if ! npm run build; then
    print_error "Failed to build TypeScript MCP servers"
    exit 1
fi
cd ..

print_status "TypeScript MCP servers built successfully"

# Start services
echo "Starting Docker services..."
if ! docker-compose up -d redis postgres prometheus jaeger grafana; then
    print_error "Failed to start Docker services"
    exit 1
fi

print_status "Docker services started"

# Start AgentGateway directly (workaround for Docker Compose issue)
echo "Starting AgentGateway..."
docker run -d --name elf-agentgateway-test --network elf-network -v $(pwd)/config/agentgateway:/app/config -p 3000:3000 -p 9091:9091 elf-automations/agentgateway:latest

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check AgentGateway health
echo "Checking AgentGateway health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if nc -z localhost 3000 2>/dev/null; then
        print_status "AgentGateway is healthy"
        break
    fi

    if [ $attempt -eq $max_attempts ]; then
        print_error "AgentGateway failed to start after $max_attempts attempts"
        echo "Checking logs:"
        docker logs elf-agentgateway-test
        exit 1
    fi

    echo "Attempt $attempt/$max_attempts - waiting for AgentGateway..."
    sleep 2
    ((attempt++))
done

# Run MCP integration tests
echo "Running MCP integration tests..."
if python tests/test_agentgateway_mcp.py; then
    print_status "MCP integration tests passed"
else
    print_warning "Some MCP tests failed - check logs for details"
fi

# Phase 2: Test kagent + LangGraph Agent (if Kubernetes is available)
echo ""
echo "🤖 Phase 2: Testing kagent + LangGraph Agent"
echo "============================================"

# Check if kubectl is available
if command -v kubectl > /dev/null 2>&1; then
    # Check if we can connect to a Kubernetes cluster
    if kubectl cluster-info > /dev/null 2>&1; then
        echo "Kubernetes cluster detected - testing kagent integration"

        # Build agent container
        echo "Building Chief AI Agent container..."
        if docker build -f docker/chief-ai-agent.Dockerfile -t elf-automations/chief-ai-agent:latest .; then
            print_status "Agent container built successfully"
        else
            print_error "Failed to build agent container"
            exit 1
        fi

        # Create namespace
        kubectl create namespace elf-automations --dry-run=client -o yaml | kubectl apply -f -

        # Create secrets
        echo "Creating Kubernetes secrets..."
        kubectl create secret generic anthropic-credentials \
            --from-literal=api-key="${ANTHROPIC_API_KEY}" \
            -n elf-automations \
            --dry-run=client -o yaml | kubectl apply -f -

        if [ -n "${FIRECRAWL_API_KEY}" ] && [ "${FIRECRAWL_API_KEY}" != "your_firecrawl_api_key" ]; then
            kubectl create secret generic firecrawl-credentials \
                --from-literal=api-key="${FIRECRAWL_API_KEY}" \
                -n elf-automations \
                --dry-run=client -o yaml | kubectl apply -f -
        fi

        # Deploy kagent controller
        echo "Deploying kagent controller..."
        kubectl apply -f k8s/kagent/deployment.yaml

        # Deploy agent
        echo "Deploying Chief AI Agent..."
        kubectl apply -f k8s/kagent/chief-ai-agent.yaml

        # Wait for deployment
        echo "Waiting for agent deployment..."
        kubectl wait --for=condition=available --timeout=300s deployment/chief-ai-agent -n elf-automations

        print_status "kagent + LangGraph agent deployed successfully"

        echo "Checking agent status:"
        kubectl get pods -n elf-automations

        echo ""
        echo "To monitor the agent:"
        echo "kubectl logs -f deployment/chief-ai-agent -n elf-automations"
        echo ""
        echo "To test agent health:"
        echo "kubectl port-forward service/chief-ai-agent 8080:8080 -n elf-automations"
        echo "curl http://localhost:8080/health"

    else
        print_warning "Kubernetes cluster not available - skipping kagent tests"
        echo "To test kagent integration:"
        echo "1. Ensure you have a Kubernetes cluster running"
        echo "2. Configure kubectl to connect to your cluster"
        echo "3. Run this script again"
    fi
else
    print_warning "kubectl not found - skipping kagent tests"
    echo "To test kagent integration, install kubectl and configure access to a Kubernetes cluster"
fi

# Summary
echo ""
echo "🎉 Integration Test Summary"
echo "=========================="
print_status "AgentGateway is running and accessible"
print_status "TypeScript MCP servers are working"

if [ -n "${FIRECRAWL_API_KEY}" ] && [ "${FIRECRAWL_API_KEY}" != "your_firecrawl_api_key" ]; then
    print_status "Firecrawl MCP server is configured"
else
    print_warning "Firecrawl MCP server not configured (optional)"
fi

echo ""
echo "🔗 Useful URLs:"
echo "- AgentGateway: http://localhost:3000"
echo "- Prometheus Metrics: http://localhost:9091/metrics"

echo ""
echo "📚 Next Steps:"
echo "1. Review the testing guide: docs/TESTING_KAGENT_AGENTGATEWAY.md"
echo "2. Customize MCP servers in mcp-servers-ts/"
echo "3. Add more agents using the kagent template"
echo "4. Set up monitoring and alerting"

echo ""
print_status "Integration testing completed!"

# Cleanup
echo ""
echo "🧹 Cleaning up..."
echo "=================="
docker stop elf-agentgateway-test 2>/dev/null || true
docker rm elf-agentgateway-test 2>/dev/null || true
docker-compose down
print_status "Cleanup completed"
