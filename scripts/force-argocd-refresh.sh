#!/bin/bash

echo "=== Forcing ArgoCD to Refresh ==="
echo

echo "1. Current app configuration:"
kubectl get application elf-teams -n argocd -o yaml | grep -A 5 "directory:"
echo

echo "2. Forcing hard refresh:"
kubectl patch application elf-teams -n argocd --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
echo

echo "3. Forcing sync:"
kubectl patch application elf-teams -n argocd --type merge -p '{"operation":{"sync":{"revision":"HEAD"}}}'
echo

echo "4. Waiting for sync..."
sleep 5
echo

echo "5. Checking sync status:"
kubectl get application elf-teams -n argocd
echo

echo "6. Checking what files ArgoCD sees in the repo:"
kubectl logs -n argocd deployment/argocd-repo-server | grep -A 10 "k8s/teams" | tail -20
echo

echo "7. Alternative: Delete and recreate the app:"
echo "If nothing works, run these commands:"
echo "kubectl delete application elf-teams -n argocd"
echo "Then rerun: bash scripts/setup-mac-mini-simple.sh"
