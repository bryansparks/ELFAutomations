#!/bin/bash

# Force clean elf-teams namespace
# This script removes all resources and lets ArgoCD recreate minimal config

set -e

echo "🧹 Force cleaning elf-teams namespace..."
echo "⚠️  This will delete all resources in elf-teams namespace!"
echo ""

# Show what will be deleted
echo "Current resources in elf-teams:"
kubectl get all -n elf-teams
echo ""

read -p "Are you sure you want to delete everything? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "🗑️  Deleting all resources in elf-teams namespace..."

# Delete all deployments, services, pods, etc
kubectl delete all --all -n elf-teams --grace-period=0 --force 2>/dev/null || true

# Delete any remaining resources
kubectl delete configmaps --all -n elf-teams 2>/dev/null || true
kubectl delete secrets --all -n elf-teams 2>/dev/null || true
kubectl delete serviceaccounts --all -n elf-teams 2>/dev/null || true
kubectl delete roles --all -n elf-teams 2>/dev/null || true
kubectl delete rolebindings --all -n elf-teams 2>/dev/null || true

echo "✅ All resources deleted"
echo ""

# Force ArgoCD to sync
echo "🔄 Forcing ArgoCD to sync..."
kubectl patch application elf-teams -n argocd --type merge \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'

sleep 2

kubectl patch application elf-teams -n argocd --type merge \
  -p '{"operation":{"sync":{"prune":true,"revision":"HEAD","syncOptions":["Replace=true"]}}}'

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Monitoring sync status:"
echo "kubectl get applications elf-teams -n argocd -w"
echo ""
echo "📋 Check namespace contents:"
echo "kubectl get all -n elf-teams"
