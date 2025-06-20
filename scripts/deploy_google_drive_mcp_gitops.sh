#!/bin/bash
#
# Deploy Google Drive MCP via GitOps
# This script prepares the MCP for ArgoCD deployment
#

set -e

echo "🚀 Deploying Google Drive MCP via GitOps"
echo "========================================"

# Check if Docker image exists
if docker image inspect "elf-automations/google-drive-watcher:latest" >/dev/null 2>&1; then
    echo "✅ Docker image found: elf-automations/google-drive-watcher:latest"
else
    echo "❌ Docker image not found! Building..."
    cd mcps/google-drive-watcher
    docker build -t elf-automations/google-drive-watcher:latest .
    cd ../..
fi

# Transfer image to ArgoCD machine
echo ""
echo "📦 Transferring Docker image to ArgoCD machine..."
./scripts/transfer-docker-images-ssh.sh

# Prepare GitOps artifacts
echo ""
echo "📋 Preparing GitOps artifacts..."
cd tools
python prepare_gitops_artifacts.py
cd ..

# Show next steps
echo ""
echo "✅ Google Drive MCP prepared for GitOps deployment!"
echo ""
echo "Next steps:"
echo "1. Review the generated manifests in gitops/"
echo "2. Commit and push to GitHub:"
echo "   cd gitops"
echo "   git add ."
echo "   git commit -m 'Deploy Google Drive MCP'"
echo "   git push origin main"
echo ""
echo "3. ArgoCD will automatically:"
echo "   - Detect the changes"
echo "   - Deploy the MCP to Kubernetes"
echo "   - Start monitoring Google Drive folders"
echo ""
echo "4. After deployment, set up OAuth for tenants:"
echo "   kubectl exec -it -n elf-mcps deployment/google-drive-watcher -- node dist/server.js get_auth_url"
echo ""
echo "5. Monitor the deployment:"
echo "   kubectl logs -n elf-mcps -l app=google-drive-watcher -f"