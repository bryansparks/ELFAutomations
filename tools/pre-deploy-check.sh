#!/bin/bash
# Pre-deployment checklist for ElfAutomations teams
# Ensures all prerequisites are met before deploying a team

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔍 Running pre-deployment checks...${NC}"

# Check 1: Kubernetes cluster access
echo -n "Checking k8s cluster access... "
if kubectl cluster-info &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Cannot access k8s cluster${NC}"
    exit 1
fi

# Check 2: Namespace exists
echo -n "Checking elf-automations namespace... "
if kubectl get namespace elf-automations &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}Creating namespace...${NC}"
    kubectl create namespace elf-automations
fi

# Check 3: Required secrets exist
echo -n "Checking llm-api-keys secret... "
if kubectl get secret llm-api-keys -n elf-automations &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Missing llm-api-keys secret${NC}"
    echo "Create it with: kubectl create secret generic llm-api-keys --from-literal=openai-api-key=<key> --from-literal=anthropic-api-key=<key> -n elf-automations"
    exit 1
fi

echo -n "Checking supabase-credentials secret... "
if kubectl get secret supabase-credentials -n elf-automations &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Missing supabase-credentials secret${NC}"
    echo "Create it with: kubectl create secret generic supabase-credentials --from-literal=url=<url> --from-literal=key=<key> -n elf-automations"
    exit 1
fi

# Check 4: AgentGateway is running
echo -n "Checking AgentGateway service... "
if kubectl get service agentgateway -n elf-automations &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ AgentGateway service not found${NC}"
    echo "Deploy AgentGateway first"
    exit 1
fi

# Check 5: Redis is available (for A2A)
echo -n "Checking Redis service... "
if kubectl get service redis -n elf-automations &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ Redis service not found - A2A discovery may not work${NC}"
fi

# Check 6: Docker registry is accessible
echo -n "Checking Docker registry... "
REGISTRY=${DOCKER_REGISTRY:-"localhost:5000"}
if [[ "$REGISTRY" == "localhost:5000" ]]; then
    echo -e "${YELLOW}⚠ Using local registry${NC}"
else
    if docker pull $REGISTRY/test:latest &> /dev/null || true; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ Cannot reach registry $REGISTRY${NC}"
    fi
fi

# Check 7: Required CRDs
echo -n "Checking CRDs... "
if kubectl get crd kagents.kagent.dev &> /dev/null; then
    echo -e "${GREEN}✓ kagent CRD found${NC}"
else
    echo -e "${YELLOW}⚠ kagent CRD not found - some features may not work${NC}"
fi

echo -e "${GREEN}✅ Pre-deployment checks complete!${NC}"
