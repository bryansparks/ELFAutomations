#!/bin/bash

# Enable auto-sync for all our applications
# This makes GitOps truly automatic!

echo "🚀 Enabling auto-sync for GitOps applications..."

# Enable auto-sync for elf-infrastructure (Neo4j)
echo "Updating elf-infrastructure..."
kubectl patch application elf-infrastructure -n argocd --type merge -p '{
  "spec": {
    "syncPolicy": {
      "automated": {
        "prune": true,
        "selfHeal": true
      }
    }
  }
}'

# Enable auto-sync for elf-teams-direct
echo "Updating elf-teams-direct..."
kubectl patch application elf-teams-direct -n argocd --type merge -p '{
  "spec": {
    "syncPolicy": {
      "automated": {
        "prune": true,
        "selfHeal": true
      }
    }
  }
}'

# Enable auto-sync for n8n
echo "Updating n8n..."
kubectl patch application n8n -n argocd --type merge -p '{
  "spec": {
    "syncPolicy": {
      "automated": {
        "prune": true,
        "selfHeal": true
      }
    }
  }
}'

echo ""
echo "✅ Auto-sync enabled! From now on:"
echo "  - Git push = Automatic deployment"
echo "  - No manual syncing required"
echo "  - ArgoCD checks for changes every 3 minutes"
echo ""
echo "Current sync status:"
kubectl get applications -n argocd