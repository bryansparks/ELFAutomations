#!/bin/bash

# n8n Deployment Script for ElfAutomations
# This script deploys n8n to the k3s cluster with all necessary configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="elf-teams"
N8N_DIR="k8s/n8n"
N8N_HOST="n8n.elf-automations.local"

echo -e "${GREEN}ElfAutomations n8n Deployment Script${NC}"
echo "===================================="

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}kubectl not found. Please install kubectl.${NC}"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}Cannot connect to Kubernetes cluster. Please check your kubeconfig.${NC}"
        exit 1
    fi
    
    # Check namespace
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        echo -e "${YELLOW}Creating namespace $NAMESPACE...${NC}"
        kubectl create namespace $NAMESPACE
    fi
    
    # Check for existing n8n deployment
    if kubectl get deployment n8n -n $NAMESPACE &> /dev/null; then
        echo -e "${YELLOW}n8n deployment already exists. Would you like to update it? (y/n)${NC}"
        read -r response
        if [[ "$response" != "y" ]]; then
            echo "Exiting..."
            exit 0
        fi
    fi
    
    echo -e "${GREEN}Prerequisites check passed!${NC}"
}

# Function to configure secrets
configure_secrets() {
    echo -e "\n${YELLOW}Configuring secrets...${NC}"
    
    # Check if secrets already exist
    if kubectl get secret n8n-secrets -n $NAMESPACE &> /dev/null; then
        echo -e "${YELLOW}n8n-secrets already exists. Would you like to update it? (y/n)${NC}"
        read -r response
        if [[ "$response" != "y" ]]; then
            return
        fi
        kubectl delete secret n8n-secrets -n $NAMESPACE
    fi
    
    # Prompt for passwords
    echo -n "Enter n8n admin password: "
    read -s N8N_PASSWORD
    echo
    
    echo -n "Enter PostgreSQL password for n8n_user: "
    read -s POSTGRES_PASSWORD
    echo
    
    # Create secret
    kubectl create secret generic n8n-secrets \
        --namespace=$NAMESPACE \
        --from-literal=basic-auth-password="$N8N_PASSWORD" \
        --from-literal=postgres-password="$POSTGRES_PASSWORD"
    
    echo -e "${GREEN}Secrets configured successfully!${NC}"
}

# Function to deploy n8n
deploy_n8n() {
    echo -e "\n${YELLOW}Deploying n8n...${NC}"
    
    # Change to project root
    cd "$(dirname "$0")/.."
    
    # Apply kustomization
    kubectl apply -k $N8N_DIR
    
    echo -e "${GREEN}n8n deployment initiated!${NC}"
}

# Function to wait for deployment
wait_for_deployment() {
    echo -e "\n${YELLOW}Waiting for n8n to be ready...${NC}"
    
    # Wait for deployment rollout
    kubectl rollout status deployment/n8n -n $NAMESPACE --timeout=300s
    
    # Get pod status
    echo -e "\n${YELLOW}Pod status:${NC}"
    kubectl get pods -n $NAMESPACE -l app=n8n
    
    echo -e "${GREEN}n8n is ready!${NC}"
}

# Function to display access information
display_access_info() {
    echo -e "\n${GREEN}=== n8n Deployment Complete ===${NC}"
    echo -e "\nAccess n8n at: ${GREEN}http://$N8N_HOST${NC}"
    echo -e "Username: ${GREEN}admin${NC}"
    echo -e "Password: ${GREEN}[the password you entered]${NC}"
    
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo "1. Add '$N8N_HOST' to your /etc/hosts file pointing to your ingress IP"
    echo "2. Access n8n and complete the setup wizard"
    echo "3. Import workflow templates from the examples"
    echo "4. Create the n8n-interface team for A2A communication"
    
    echo -e "\n${YELLOW}Useful commands:${NC}"
    echo "- View logs: kubectl logs -n $NAMESPACE -l app=n8n -f"
    echo "- Port forward: kubectl port-forward -n $NAMESPACE svc/n8n 5678:5678"
    echo "- Check ingress: kubectl get ingress -n $NAMESPACE"
}

# Function to check deployment health
check_health() {
    echo -e "\n${YELLOW}Checking n8n health...${NC}"
    
    # Get pod name
    POD=$(kubectl get pod -n $NAMESPACE -l app=n8n -o jsonpath="{.items[0].metadata.name}")
    
    if [ -z "$POD" ]; then
        echo -e "${RED}No n8n pod found!${NC}"
        return 1
    fi
    
    # Check if pod is ready
    if kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' | grep -q "True"; then
        echo -e "${GREEN}n8n pod is healthy!${NC}"
        
        # Try to curl the health endpoint via port-forward
        echo -e "${YELLOW}Testing n8n API health...${NC}"
        kubectl port-forward -n $NAMESPACE $POD 5678:5678 &> /dev/null &
        PF_PID=$!
        sleep 3
        
        if curl -s http://localhost:5678/healthz &> /dev/null; then
            echo -e "${GREEN}n8n API is responding!${NC}"
        else
            echo -e "${YELLOW}n8n API not accessible via port-forward (this is normal if n8n is still initializing)${NC}"
        fi
        
        kill $PF_PID 2> /dev/null || true
    else
        echo -e "${RED}n8n pod is not ready. Check logs with: kubectl logs -n $NAMESPACE $POD${NC}"
    fi
}

# Main execution
main() {
    check_prerequisites
    configure_secrets
    deploy_n8n
    wait_for_deployment
    check_health
    display_access_info
}

# Run main function
main