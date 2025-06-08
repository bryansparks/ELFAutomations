#!/bin/bash

echo "=== Loading Docker Image into OrbStack k3s ==="
echo

# Method 1: Direct import using k3s
echo "Method 1: Using k3s import..."
if command -v k3s &> /dev/null; then
    docker save ghcr.io/bryansparks/elfautomations-executive-team:latest | sudo k3s ctr images import -
else
    echo "k3s command not found, trying other methods..."
fi

# Method 2: Using crictl (if available)
echo
echo "Method 2: Using crictl..."
if command -v crictl &> /dev/null; then
    docker save ghcr.io/bryansparks/elfautomations-executive-team:latest | sudo crictl load
else
    echo "crictl not found, trying other methods..."
fi

# Method 3: OrbStack specific - just use the image directly
echo
echo "Method 3: OrbStack can use Docker images directly!"
echo "Let's update the deployment to use the local Docker image:"
kubectl patch deployment executive-team -n elf-teams -p '{"spec":{"template":{"spec":{"containers":[{"name":"executive-team","image":"ghcr.io/bryansparks/elfautomations-executive-team:latest","imagePullPolicy":"Never"}]}}}}'

echo
echo "Restarting the deployment..."
kubectl rollout restart deployment/executive-team -n elf-teams

echo
echo "Checking pod status..."
kubectl get pods -n elf-teams
