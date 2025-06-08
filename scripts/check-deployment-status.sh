#!/bin/bash

echo "=== ELF Teams Deployment Status ==="
echo

echo "1. ArgoCD Application Status:"
kubectl get application elf-teams -n argocd
echo

echo "2. Executive Team Pods:"
kubectl get pods -n elf-teams
echo

echo "3. Executive Team Services:"
kubectl get services -n elf-teams
echo

echo "4. Secrets Status:"
kubectl get secrets -n elf-teams
echo

echo "5. Recent Events:"
kubectl get events -n elf-teams --sort-by='.lastTimestamp' | tail -10
echo

echo "6. If Executive team pod exists, check logs:"
POD=$(kubectl get pods -n elf-teams -l app=executive-team -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ ! -z "$POD" ]; then
    echo "Logs from $POD:"
    kubectl logs -n elf-teams $POD --tail=20
else
    echo "No executive team pod found"
fi

echo
echo "=== Quick Actions ==="
echo "Access ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "Get ArgoCD password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
echo "Edit API keys: kubectl edit secret llm-api-keys -n elf-teams"
