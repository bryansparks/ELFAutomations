#!/bin/bash

# Cleanup shadow ArgoCD applications
# These are apps that were manually created but aren't in our GitOps flow

echo "🧹 Cleaning up shadow ArgoCD applications..."

# List all current applications
echo "Current ArgoCD applications:"
kubectl get applications -n argocd

echo ""
echo "Expected applications (from GitOps):"
echo "  - elf-infrastructure (Neo4j)"
echo "  - elf-teams-direct (minimal teams)"
echo "  - n8n (workflow automation)"

echo ""
echo "Shadow applications to remove:"

# Check for known shadow apps
SHADOW_APPS=(
  "elf-teams"          # Old version
  "elf-teams-simple"   # Troubleshooting remnant
  "n8n-workflow"       # Old n8n name
)

for app in "${SHADOW_APPS[@]}"; do
  if kubectl get application "$app" -n argocd &> /dev/null; then
    echo "  - $app (FOUND - will delete)"
    kubectl delete application "$app" -n argocd
  fi
done

echo ""
echo "✅ Cleanup complete. Final state:"
kubectl get applications -n argocd
