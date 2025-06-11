#!/bin/bash
# Complete pipeline: Create and deploy a team from natural language description
# This orchestrates the entire process from team creation to k3s deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ElfAutomations Team Creation & Deployment Pipeline${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

# Step 1: Run pre-deployment checks
echo -e "${YELLOW}📋 Step 1: Running pre-deployment checks...${NC}"
./tools/pre-deploy-check.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Pre-deployment checks failed. Please fix issues before continuing.${NC}"
    exit 1
fi

# Step 2: Create team using team factory
echo -e "\n${YELLOW}🏭 Step 2: Creating team with Team Factory...${NC}"
cd tools
python team_factory.py
cd ..

# Step 3: Get the newly created team directory
echo -e "\n${YELLOW}📁 Step 3: Locating newly created team...${NC}"
echo -n "Enter the team name (as created, e.g., marketing-team): "
read TEAM_NAME
TEAM_DIR="teams/$TEAM_NAME"

if [ ! -d "$TEAM_DIR" ]; then
    echo -e "${RED}Error: Team directory $TEAM_DIR not found${NC}"
    exit 1
fi

echo -e "${GREEN}Found team at: $TEAM_DIR${NC}"

# Step 4: Deploy the team
echo -e "\n${YELLOW}🚀 Step 4: Deploying team to k3s...${NC}"
./tools/deploy-team.sh $TEAM_DIR

# Step 5: Verify deployment
echo -e "\n${YELLOW}✅ Step 5: Verifying deployment...${NC}"
kubectl get pods -n elf-automations -l app=$TEAM_NAME
kubectl get services -n elf-automations -l app=$TEAM_NAME

# Step 6: Register with AgentGateway (if applicable)
echo -e "\n${YELLOW}🔗 Step 6: Registering with AgentGateway...${NC}"
# This would call a script to register the team with AgentGateway
# For now, just show the registration info
echo -e "${GREEN}Team $TEAM_NAME is ready for AgentGateway registration${NC}"
echo -e "AgentGateway will discover the team via its /capabilities endpoint"

# Step 7: Test A2A communication
echo -e "\n${YELLOW}🧪 Step 7: Testing A2A communication...${NC}"
kubectl run test-a2a --rm -i --tty --image=curlimages/curl --restart=Never -- \
    curl -X GET http://$TEAM_NAME-service.elf-automations.svc.cluster.local:8080/health || true

echo -e "\n${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Team creation and deployment complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "\n${BLUE}Next steps:${NC}"
echo -e "1. Monitor logs: ${YELLOW}kubectl logs -f deployment/$TEAM_NAME -n elf-automations${NC}"
echo -e "2. Check A2A discovery: ${YELLOW}kubectl logs deployment/agentgateway -n elf-automations | grep $TEAM_NAME${NC}"
echo -e "3. Send test task via executive team or API"
echo -e "\n${BLUE}Useful commands:${NC}"
echo -e "- Scale team: ${YELLOW}kubectl scale deployment/$TEAM_NAME --replicas=2 -n elf-automations${NC}"
echo -e "- Update team: ${YELLOW}kubectl rollout restart deployment/$TEAM_NAME -n elf-automations${NC}"
echo -e "- Delete team: ${YELLOW}kubectl delete -f $TEAM_DIR/k8s/deployment.yaml${NC}"
