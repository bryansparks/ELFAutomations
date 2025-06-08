#!/bin/bash

echo "=== Mac Mini Deployment Status Check ==="
echo

echo "1. Checking if we're on the Mac Mini or Dev machine:"
hostname
echo

echo "2. Checking if OrbStack is installed:"
if command -v orb &> /dev/null; then
    echo "✓ OrbStack found"
    orb version
else
    echo "✗ OrbStack not found"
fi
echo

echo "3. Checking if k3s/kubernetes is running:"
if command -v kubectl &> /dev/null; then
    echo "✓ kubectl found"
    kubectl version --short 2>/dev/null || echo "✗ kubectl can't connect to cluster"
    echo
    echo "Cluster info:"
    kubectl cluster-info 2>/dev/null || echo "✗ No cluster found"
else
    echo "✗ kubectl not found"
fi
echo

echo "4. Checking if ArgoCD is installed:"
kubectl get namespace argocd 2>/dev/null && echo "✓ ArgoCD namespace exists" || echo "✗ ArgoCD namespace not found"
kubectl get pods -n argocd 2>/dev/null || echo "✗ No ArgoCD pods found"
echo

echo "5. Checking ArgoCD applications:"
kubectl get applications -n argocd 2>/dev/null || echo "✗ No ArgoCD applications found"
echo

echo "6. Checking if elf-teams namespace exists:"
kubectl get namespace elf-teams 2>/dev/null && echo "✓ elf-teams namespace exists" || echo "✗ elf-teams namespace not found"
echo

echo "7. Checking what's in our project directory:"
if [ -d "/Users/bryansparks/projects/ELFAutomations" ]; then
    echo "✓ Project directory exists"
    cd /Users/bryansparks/projects/ELFAutomations
    echo "Git status:"
    git status --short
    echo "Current branch:"
    git branch --show-current
    echo "K8s teams directory:"
    ls -la k8s/teams/ 2>/dev/null || echo "✗ k8s/teams directory not found"
else
    echo "✗ Project directory not found"
fi
