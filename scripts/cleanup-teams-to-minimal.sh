#!/bin/bash

# Cleanup elf-teams to minimal configuration
# This script archives old team configurations and sets up a minimal deployment

set -e

echo "🧹 Cleaning up elf-teams to minimal configuration..."

# Create archive directory
ARCHIVE_DIR="k8s/teams-archive-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

# Archive existing team deployments
echo "📦 Archiving existing team configurations to $ARCHIVE_DIR..."
mv k8s/teams/executive-team "$ARCHIVE_DIR/" 2>/dev/null || true
mv k8s/teams/executive "$ARCHIVE_DIR/" 2>/dev/null || true
mv k8s/teams/marketing "$ARCHIVE_DIR/" 2>/dev/null || true
mv k8s/teams/sales "$ARCHIVE_DIR/" 2>/dev/null || true
mv k8s/teams/secrets.yaml.backup "$ARCHIVE_DIR/" 2>/dev/null || true

# Keep only essential files
echo "✅ Keeping essential files:"
echo "  - namespace.yaml"
echo "  - secrets.yaml (if exists)"

# Create a minimal placeholder deployment
cat > k8s/teams/minimal-placeholder.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: teams-config
  namespace: elf-teams
  labels:
    app: elf-teams
    component: configuration
data:
  status: |
    # ELF Teams - Minimal Configuration
    # This is a placeholder for the teams namespace
    # Teams will be deployed here as they are developed
    mode: development
    teams:
      - n8n (workflow automation)
      - neo4j (in elf-infrastructure namespace)
EOF

# Create a minimal kustomization file
cat > k8s/teams/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: elf-teams

resources:
  - namespace.yaml
  - minimal-placeholder.yaml

# Only include secrets if it exists
# - secrets.yaml
EOF

# Check if secrets.yaml exists and add it to kustomization
if [ -f "k8s/teams/secrets.yaml" ]; then
    echo "  - secrets.yaml" >> k8s/teams/kustomization.yaml
fi

echo ""
echo "📋 Summary of changes:"
echo "  - Archived old team deployments to: $ARCHIVE_DIR"
echo "  - Created minimal placeholder configuration"
echo "  - Updated kustomization.yaml"
echo ""
echo "🚀 Next steps:"
echo "1. Review the changes:"
echo "   git status"
echo ""
echo "2. Commit and push to trigger GitOps sync:"
echo "   git add -A"
echo "   git commit -m 'refactor: Minimize elf-teams to essential configuration'"
echo "   git push origin main"
echo ""
echo "3. On deployment machine, the elf-teams app should auto-sync"
echo "   kubectl get applications -n argocd -w"
echo ""
echo "4. To restore old configurations later:"
echo "   cp -r $ARCHIVE_DIR/* k8s/teams/"
