#!/bin/bash

echo "=== Starting ELF Automations After Reboot ==="
echo

# 1. Check if OrbStack is running
echo "1. Checking OrbStack..."
if ! pgrep -x "OrbStack" > /dev/null; then
    echo "Starting OrbStack..."
    open -a OrbStack
    echo "Waiting for OrbStack to initialize..."
    sleep 10
else
    echo "✓ OrbStack is already running"
fi

# 2. Wait for Kubernetes to be ready
echo
echo "2. Waiting for Kubernetes to be ready..."
until kubectl cluster-info &> /dev/null; do
    echo -n "."
    sleep 2
done
echo
echo "✓ Kubernetes is ready"

# 3. Check ArgoCD status
echo
echo "3. Checking ArgoCD status..."
kubectl get pods -n argocd | grep -E "NAME|argocd"
echo

# 4. Check Executive team status
echo "4. Checking Executive team status..."
kubectl get pods -n elf-teams
echo

# 5. Get ArgoCD password (in case you need it)
echo "5. ArgoCD Credentials:"
echo "Username: admin"
echo -n "Password: "
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "Password secret not found"
echo
echo

# 6. Quick health check
echo "6. Quick health check..."
if kubectl get pods -n elf-teams | grep -q "Running"; then
    echo "✓ Executive team is running"
else
    echo "⚠ Executive team is not running. Checking events..."
    kubectl get events -n elf-teams --sort-by='.lastTimestamp' | tail -5
fi

echo
echo "=== Quick Commands ==="
echo "Access ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "Test Executive API: kubectl port-forward -n elf-teams svc/executive-team 8090:8090"
echo "Check all pods: kubectl get pods --all-namespaces"
echo "Watch team pods: kubectl get pods -n elf-teams -w"
