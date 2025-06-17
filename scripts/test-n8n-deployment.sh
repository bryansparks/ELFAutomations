#!/bin/bash

# Test script for n8n deployment in ElfAutomations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

NAMESPACE="elf-teams"

echo -e "${GREEN}n8n Deployment Test Suite${NC}"
echo "========================="

# Test 1: Check if deployment exists
echo -e "\n${YELLOW}Test 1: Checking deployment...${NC}"
if kubectl get deployment n8n -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ Deployment exists${NC}"
    kubectl get deployment n8n -n $NAMESPACE
else
    echo -e "${RED}✗ Deployment not found${NC}"
    exit 1
fi

# Test 2: Check if pods are running
echo -e "\n${YELLOW}Test 2: Checking pods...${NC}"
POD_COUNT=$(kubectl get pods -n $NAMESPACE -l app=n8n --no-headers | wc -l)
if [ "$POD_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✓ Pod count is correct${NC}"
    kubectl get pods -n $NAMESPACE -l app=n8n
else
    echo -e "${RED}✗ Expected 1 pod, found $POD_COUNT${NC}"
    exit 1
fi

# Test 3: Check pod status
echo -e "\n${YELLOW}Test 3: Checking pod status...${NC}"
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=n8n -o jsonpath="{.items[0].metadata.name}")
POD_STATUS=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath="{.status.phase}")
if [ "$POD_STATUS" = "Running" ]; then
    echo -e "${GREEN}✓ Pod is running${NC}"
else
    echo -e "${RED}✗ Pod status is $POD_STATUS${NC}"
    kubectl describe pod $POD_NAME -n $NAMESPACE
    exit 1
fi

# Test 4: Check PVCs
echo -e "\n${YELLOW}Test 4: Checking persistent volume claims...${NC}"
PVC_COUNT=$(kubectl get pvc -n $NAMESPACE -l app=n8n --no-headers | wc -l)
if [ "$PVC_COUNT" -eq 2 ]; then
    echo -e "${GREEN}✓ Both PVCs exist${NC}"
    kubectl get pvc -n $NAMESPACE -l app=n8n
else
    echo -e "${RED}✗ Expected 2 PVCs, found $PVC_COUNT${NC}"
    exit 1
fi

# Test 5: Check service
echo -e "\n${YELLOW}Test 5: Checking service...${NC}"
if kubectl get service n8n -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ Service exists${NC}"
    kubectl get service n8n -n $NAMESPACE
else
    echo -e "${RED}✗ Service not found${NC}"
    exit 1
fi

# Test 6: Check ingress
echo -e "\n${YELLOW}Test 6: Checking ingress...${NC}"
if kubectl get ingress n8n -n $NAMESPACE &> /dev/null; then
    echo -e "${GREEN}✓ Ingress exists${NC}"
    kubectl get ingress n8n -n $NAMESPACE
else
    echo -e "${RED}✗ Ingress not found${NC}"
    exit 1
fi

# Test 7: Check container logs
echo -e "\n${YELLOW}Test 7: Checking container logs for errors...${NC}"
ERROR_COUNT=$(kubectl logs $POD_NAME -n $NAMESPACE --tail=50 | grep -i error | wc -l || true)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No errors in recent logs${NC}"
else
    echo -e "${YELLOW}⚠ Found $ERROR_COUNT error messages in logs${NC}"
    echo "Recent errors:"
    kubectl logs $POD_NAME -n $NAMESPACE --tail=50 | grep -i error || true
fi

# Test 8: Port forward test
echo -e "\n${YELLOW}Test 8: Testing n8n API via port-forward...${NC}"
kubectl port-forward -n $NAMESPACE pod/$POD_NAME 5678:5678 &> /dev/null &
PF_PID=$!
sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/healthz | grep -q "200"; then
    echo -e "${GREEN}✓ n8n API is responding (HTTP 200)${NC}"
else
    echo -e "${YELLOW}⚠ n8n API returned non-200 status${NC}"
fi

kill $PF_PID 2> /dev/null || true

# Test 9: Check resource usage
echo -e "\n${YELLOW}Test 9: Checking resource usage...${NC}"
kubectl top pod $POD_NAME -n $NAMESPACE || echo -e "${YELLOW}Note: kubectl top requires metrics-server${NC}"

# Summary
echo -e "\n${GREEN}=== Test Summary ===${NC}"
echo -e "${GREEN}All basic deployment tests passed!${NC}"
echo -e "\n${YELLOW}Manual verification steps:${NC}"
echo "1. Access n8n UI at http://n8n.elf-automations.local"
echo "2. Login with admin credentials"
echo "3. Create a test workflow"
echo "4. Execute the test workflow"
echo "5. Verify webhook functionality"

echo -e "\n${YELLOW}Integration test commands:${NC}"
echo "# Test webhook endpoint:"
echo "curl -X POST http://n8n.elf-automations.local/webhook-test/test-webhook"
echo ""
echo "# Test from another pod:"
echo "kubectl run test-curl --image=curlimages/curl -n $NAMESPACE --rm -it -- curl http://n8n:5678/healthz"