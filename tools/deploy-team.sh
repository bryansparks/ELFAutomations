#!/bin/bash
# Deploy Team to K3s Infrastructure
# This script handles the complete deployment pipeline for a team

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if team directory is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No team directory specified${NC}"
    echo "Usage: $0 <team-directory>"
    echo "Example: $0 teams/executive-team"
    exit 1
fi

TEAM_DIR=$1
TEAM_NAME=$(basename $TEAM_DIR)

# Validate team directory exists
if [ ! -d "$TEAM_DIR" ]; then
    echo -e "${RED}Error: Team directory $TEAM_DIR does not exist${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Deploying team: $TEAM_NAME${NC}"

# Step 1: Generate deployable artifacts
echo -e "${YELLOW}Step 1: Generating deployable artifacts...${NC}"
cd $TEAM_DIR
if [ -f "make-deployable-team.py" ]; then
    python make-deployable-team.py
else
    echo -e "${RED}Error: make-deployable-team.py not found${NC}"
    exit 1
fi

# Step 2: Build Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
REGISTRY=${DOCKER_REGISTRY:-"localhost:5000"}
IMAGE_TAG="$REGISTRY/elf-automations/$TEAM_NAME:latest"

docker build -t $IMAGE_TAG .

# Step 3: Push to registry (if not localhost)
if [ "$REGISTRY" != "localhost:5000" ]; then
    echo -e "${YELLOW}Step 3: Pushing to registry...${NC}"
    docker push $IMAGE_TAG
else
    echo -e "${YELLOW}Step 3: Using local registry, push skipped${NC}"
fi

# Step 4: Update k8s manifest with correct image
echo -e "${YELLOW}Step 4: Updating k8s manifest...${NC}"
sed -i "s|elf-automations/$TEAM_NAME:latest|$IMAGE_TAG|g" k8s/deployment.yaml

# Step 5: Apply k8s manifests
echo -e "${YELLOW}Step 5: Applying k8s manifests...${NC}"
kubectl apply -f k8s/deployment.yaml

# Step 6: Wait for deployment to be ready
echo -e "${YELLOW}Step 6: Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/$TEAM_NAME -n elf-automations

# Step 7: Verify deployment
echo -e "${YELLOW}Step 7: Verifying deployment...${NC}"
POD_NAME=$(kubectl get pods -n elf-automations -l app=$TEAM_NAME -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD_NAME -n elf-automations --tail=20

# Step 8: Check health endpoint
echo -e "${YELLOW}Step 8: Checking health endpoint...${NC}"
SERVICE_URL=$(kubectl get svc $TEAM_NAME-service -n elf-automations -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$SERVICE_URL" ]; then
    # For local k3s, use port-forward
    kubectl port-forward -n elf-automations svc/$TEAM_NAME-service 8080:8080 &
    PF_PID=$!
    sleep 2
    curl -s http://localhost:8080/health || echo -e "${RED}Health check failed${NC}"
    kill $PF_PID
else
    curl -s http://$SERVICE_URL:8080/health || echo -e "${RED}Health check failed${NC}"
fi

echo -e "${GREEN}✅ Team $TEAM_NAME deployed successfully!${NC}"
echo -e "${GREEN}📊 View logs: kubectl logs -f deployment/$TEAM_NAME -n elf-automations${NC}"
echo -e "${GREEN}🔍 Check status: kubectl get pods -n elf-automations -l app=$TEAM_NAME${NC}"
