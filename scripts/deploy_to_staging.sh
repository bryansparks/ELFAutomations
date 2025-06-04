#!/bin/bash

# Deploy Virtual AI Company Platform to staging environment
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="virtual-ai-platform-staging"
KUBECTL_CONTEXT=${KUBECTL_CONTEXT:-minikube}
IMAGE_TAG=${IMAGE_TAG:-develop-latest}

echo -e "${BLUE}🚀 Deploying Virtual AI Company Platform to Staging${NC}"
echo "Namespace: $NAMESPACE"
echo "Context: $KUBECTL_CONTEXT"
echo "Image Tag: $IMAGE_TAG"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
if ! command_exists kubectl; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
    exit 1
fi

# Check if minikube is running
if [[ "$KUBECTL_CONTEXT" == "minikube" ]]; then
    if ! minikube status >/dev/null 2>&1; then
        echo -e "${RED}❌ Minikube is not running. Please start minikube.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Set kubectl context
echo -e "${YELLOW}🔧 Setting kubectl context to $KUBECTL_CONTEXT...${NC}"
kubectl config use-context "$KUBECTL_CONTEXT"

# Build Docker images locally
echo -e "${YELLOW}🏗️ Building Docker images...${NC}"

# Build web image
echo "Building web image..."
docker build -t "virtual-ai-web:$IMAGE_TAG" -f docker/web/Dockerfile .

# Build agents image
echo "Building agents image..."
docker build -t "virtual-ai-agents:$IMAGE_TAG" -f docker/agents/Dockerfile .

# Load images into minikube if using minikube
if [[ "$KUBECTL_CONTEXT" == "minikube" ]]; then
    echo -e "${YELLOW}📦 Loading images into minikube...${NC}"
    minikube image load "virtual-ai-web:$IMAGE_TAG"
    minikube image load "virtual-ai-agents:$IMAGE_TAG"
fi

# Create namespace
echo -e "${YELLOW}🏗️ Creating namespace and secrets...${NC}"
kubectl apply -f k8s/staging/namespace.yaml

# Update secrets with actual values if they exist in environment
if [[ -n "${SUPABASE_ANON_KEY:-}" ]]; then
    echo "Updating Supabase secrets..."
    kubectl patch secret supabase-secrets -n "$NAMESPACE" \
        --patch="{\"stringData\":{\"anon-key\":\"$SUPABASE_ANON_KEY\"}}"
fi

if [[ -n "${SUPABASE_PERSONAL_ACCESS_TOKEN:-}" ]]; then
    kubectl patch secret supabase-secrets -n "$NAMESPACE" \
        --patch="{\"stringData\":{\"personal-access-token\":\"$SUPABASE_PERSONAL_ACCESS_TOKEN\"}}"
fi

if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "Updating AI API secrets..."
    kubectl patch secret ai-api-secrets -n "$NAMESPACE" \
        --patch="{\"stringData\":{\"anthropic-key\":\"$ANTHROPIC_API_KEY\"}}"
fi

if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    kubectl patch secret ai-api-secrets -n "$NAMESPACE" \
        --patch="{\"stringData\":{\"openai-key\":\"$OPENAI_API_KEY\"}}"
fi

# Update image tags in manifests
echo -e "${YELLOW}🔄 Updating image tags in manifests...${NC}"
sed -i.bak "s|ghcr.io/bryansparks/elfautomations-web:develop-latest|virtual-ai-web:$IMAGE_TAG|g" k8s/staging/web-deployment.yaml
sed -i.bak "s|ghcr.io/bryansparks/elfautomations-agents:develop-latest|virtual-ai-agents:$IMAGE_TAG|g" k8s/staging/agents-deployment.yaml

# Deploy applications
echo -e "${YELLOW}🚀 Deploying applications...${NC}"
kubectl apply -f k8s/staging/web-deployment.yaml
kubectl apply -f k8s/staging/agents-deployment.yaml

# Restore original manifests
mv k8s/staging/web-deployment.yaml.bak k8s/staging/web-deployment.yaml
mv k8s/staging/agents-deployment.yaml.bak k8s/staging/agents-deployment.yaml

# Wait for deployments to be ready
echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/virtual-ai-web -n "$NAMESPACE"
kubectl wait --for=condition=available --timeout=300s deployment/virtual-ai-agents -n "$NAMESPACE"

# Get deployment status
echo -e "${YELLOW}📊 Deployment Status:${NC}"
kubectl get pods -n "$NAMESPACE"
kubectl get services -n "$NAMESPACE"

# Setup port forwarding for local access
echo -e "${YELLOW}🌐 Setting up port forwarding...${NC}"
echo "Web dashboard will be available at: http://localhost:8080"
echo "To access the dashboard, run:"
echo "kubectl port-forward -n $NAMESPACE service/virtual-ai-web-service 8080:80"

# Health check
echo -e "${YELLOW}🏥 Performing health check...${NC}"
WEB_POD=$(kubectl get pods -n "$NAMESPACE" -l app=virtual-ai-web -o jsonpath='{.items[0].metadata.name}')
if kubectl exec -n "$NAMESPACE" "$WEB_POD" -- curl -f http://localhost:8080/api/status >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️ Health check failed, but deployment may still be starting${NC}"
fi

echo
echo -e "${GREEN}🎉 Deployment to staging completed successfully!${NC}"
echo
echo "Next steps:"
echo "1. Run port forwarding: kubectl port-forward -n $NAMESPACE service/virtual-ai-web-service 8080:80"
echo "2. Open browser to: http://localhost:8080"
echo "3. Check logs: kubectl logs -n $NAMESPACE -l app=virtual-ai-web"
echo "4. Monitor agents: kubectl logs -n $NAMESPACE -l app=virtual-ai-agents"
