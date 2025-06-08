#!/bin/bash

echo "=== Diagnosing ArgoCD Degraded Status ==="
echo

echo "1. Current application status:"
kubectl get application elf-teams -n argocd -o jsonpath='{.status.health.status}' && echo
kubectl get application elf-teams -n argocd -o jsonpath='{.status.health.message}' && echo
echo

echo "2. Checking all resources in elf-teams namespace:"
kubectl get all -n elf-teams
echo

echo "3. Looking for unhealthy resources:"
kubectl get application elf-teams -n argocd -o json | jq -r '.status.resources[] | select(.health.status != "Healthy") | "\(.kind)/\(.name): \(.health.status) - \(.health.message)"'
echo

echo "4. Checking for multiple ReplicaSets (common cause):"
kubectl get replicasets -n elf-teams
echo

echo "5. Checking events for errors:"
kubectl get events -n elf-teams --sort-by='.lastTimestamp' | tail -10
echo

echo "=== Quick Fixes ==="
echo

echo "Fix 1: Delete old/stuck pods:"
echo "kubectl get pods -n elf-teams --no-headers | grep -E 'ImagePullBackOff|ErrImagePull|Error|Terminating' | awk '{print \$1}' | xargs -r kubectl delete pod -n elf-teams"
echo

echo "Fix 2: Clean up old ReplicaSets:"
echo "kubectl delete replicaset -n elf-teams --field-selector metadata.name!=\$(kubectl get deployment executive-team -n elf-teams -o jsonpath='{.status.newReplicaSet}')"
echo

echo "Fix 3: Force sync in ArgoCD:"
echo "kubectl patch application elf-teams -n argocd --type merge -p '{\"operation\":{\"sync\":{\"prune\":true}}}'"
echo

echo "Fix 4: If still degraded, refresh ArgoCD's view:"
echo "In the ArgoCD UI, click the 'Refresh' button (circular arrow icon)"
