#!/bin/bash
# Force sync the infrastructure ArgoCD application

echo "🔄 Forcing sync of infrastructure app..."

# Get current sync status
echo "Current status:"
kubectl get app -n argocd elf-infrastructure

# Force sync
echo ""
echo "Triggering sync..."
kubectl patch app elf-infrastructure -n argocd --type merge -p '{"operation": {"initiatedBy": {"username": "admin"},"sync": {"revision": "HEAD"}}}'

# Wait a moment
sleep 5

# Check status again
echo ""
echo "New status:"
kubectl get app -n argocd elf-infrastructure

# Watch the sync progress
echo ""
echo "Watching sync progress (press Ctrl+C to stop):"
kubectl get app -n argocd elf-infrastructure -w