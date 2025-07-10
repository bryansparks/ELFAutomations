#!/bin/bash

# Setup script for AgentGateway remote access
# This script configures various methods to access AgentGateway UI remotely

set -e

NAMESPACE="virtual-ai-platform"
DEPLOYMENT_HOST="192.168.6.5"
DEPLOYMENT_USER="bryan"

echo "AgentGateway Remote Access Setup"
echo "================================"
echo ""

# Function to check if kubectl is configured
check_kubectl() {
    if kubectl get nodes &>/dev/null; then
        echo "✓ kubectl is configured"
        return 0
    else
        echo "✗ kubectl not configured for remote cluster"
        return 1
    fi
}

# Option 1: SSH Tunnel
setup_ssh_tunnel() {
    echo "Setting up SSH tunnel..."
    echo "Run this command on your development machine:"
    echo ""
    echo "ssh -L 8080:localhost:8080 -L 9090:localhost:9090 $DEPLOYMENT_USER@$DEPLOYMENT_HOST \\"
    echo "  'kubectl port-forward service/agentgateway-service 8080:8080 -n $NAMESPACE & \\"
    echo "   kubectl port-forward service/agentgateway-metrics 9090:9090 -n $NAMESPACE'"
    echo ""
    echo "Then access:"
    echo "  - Admin UI: http://localhost:8080"
    echo "  - Metrics: http://localhost:9090"
}

# Option 2: Direct kubectl (if kubeconfig is set up)
setup_direct_kubectl() {
    echo "Setting up direct kubectl port-forward..."

    # Check if we can connect to the remote cluster
    if check_kubectl; then
        echo "Starting port-forward..."
        kubectl port-forward service/agentgateway-service 8080:8080 -n $NAMESPACE &
        PF1_PID=$!
        kubectl port-forward service/agentgateway-metrics 9090:9090 -n $NAMESPACE &
        PF2_PID=$!

        echo ""
        echo "Port forwarding started with PIDs: $PF1_PID, $PF2_PID"
        echo "Access:"
        echo "  - Admin UI: http://localhost:8080"
        echo "  - Metrics: http://localhost:9090"
        echo ""
        echo "Press Ctrl+C to stop port forwarding"

        # Wait for interrupt
        trap "kill $PF1_PID $PF2_PID; exit" INT
        wait
    else
        echo "Please configure kubectl to connect to the remote cluster first"
    fi
}

# Option 3: Setup Ingress
setup_ingress() {
    echo "Setting up Ingress for permanent access..."

    # Apply ingress configuration
    if check_kubectl; then
        kubectl apply -f k8s/base/agentgateway/ingress.yaml

        echo ""
        echo "Ingress created. Add these entries to your /etc/hosts file:"
        echo ""
        echo "$DEPLOYMENT_HOST agentgateway.elf.local"
        echo "$DEPLOYMENT_HOST agentgateway-metrics.elf.local"
        echo ""
        echo "Then access:"
        echo "  - Admin UI: http://agentgateway.elf.local"
        echo "  - Metrics: http://agentgateway-metrics.elf.local"
        echo ""
        echo "Default credentials: admin / agentgateway"
    else
        echo "Cannot apply ingress - kubectl not configured"
    fi
}

# Option 4: Create a persistent SSH config
setup_ssh_config() {
    echo "Setting up SSH config for easy access..."

    CONFIG_ENTRY="
Host agentgateway-tunnel
    HostName $DEPLOYMENT_HOST
    User $DEPLOYMENT_USER
    LocalForward 8080 localhost:8080
    LocalForward 9090 localhost:9090
    RemoteCommand kubectl port-forward service/agentgateway-service 8080:8080 -n $NAMESPACE & kubectl port-forward service/agentgateway-metrics 9090:9090 -n $NAMESPACE; bash
    RequestTTY yes
"

    echo "Add this to your ~/.ssh/config:"
    echo "$CONFIG_ENTRY"
    echo ""
    echo "Then connect with: ssh agentgateway-tunnel"
}

# Main menu
echo "Choose an option:"
echo "1) SSH Tunnel (temporary access)"
echo "2) Direct kubectl port-forward (requires kubeconfig)"
echo "3) Setup Ingress (permanent access)"
echo "4) Create SSH config entry"
echo "5) Show all options"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        setup_ssh_tunnel
        ;;
    2)
        setup_direct_kubectl
        ;;
    3)
        setup_ingress
        ;;
    4)
        setup_ssh_config
        ;;
    5)
        echo ""
        setup_ssh_tunnel
        echo ""
        echo "================================"
        echo ""
        setup_ssh_config
        echo ""
        echo "================================"
        echo ""
        setup_ingress
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
