#!/bin/bash

echo "=== ArgoCD Application Details ==="
echo

echo "1. Application Details:"
kubectl get application elf-teams -n argocd -o yaml | grep -A 20 "status:" | grep -E "(message|sync:|health:|resources:)" || echo "Could not get app details"
echo

echo "2. What resources ArgoCD thinks should exist:"
kubectl get application elf-teams -n argocd -o jsonpath='{.status.resources[*].name}' | tr ' ' '\n'
echo
echo

echo "3. Check what's actually deployed:"
kubectl get all -n elf-teams
echo

echo "4. Describe the deployment (if it exists):"
kubectl describe deployment executive-team -n elf-teams 2>/dev/null || echo "No deployment found"
echo

echo "5. Check if namespace has the manifests:"
kubectl get configmap,service,deployment,serviceaccount,role,rolebinding -n elf-teams
echo

echo "6. Force ArgoCD sync:"
echo "Run this to force sync: kubectl patch application elf-teams -n argocd --type merge -p '{\"operation\":{\"sync\":{}}}'"
