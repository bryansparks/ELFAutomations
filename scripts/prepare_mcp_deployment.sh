#!/bin/bash

# Prepare MCP deployment for GitOps
# This script sets up the k8s/mcps directory structure for ArgoCD

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}MCP Deployment Preparation Script${NC}"
echo "=================================="

# Create k8s/mcps directory if it doesn't exist
echo -e "\n${BLUE}Creating k8s/mcps directory structure...${NC}"
mkdir -p "$PROJECT_ROOT/k8s/mcps/google-drive-watcher"

# Copy google-drive-watcher manifests
echo -e "\n${BLUE}Copying google-drive-watcher manifests...${NC}"
if [ -d "$PROJECT_ROOT/mcps/google-drive-watcher/k8s" ]; then
    cp "$PROJECT_ROOT/mcps/google-drive-watcher/k8s/"*.yaml "$PROJECT_ROOT/k8s/mcps/google-drive-watcher/"
    echo -e "${GREEN}✓${NC} Copied manifests to k8s/mcps/google-drive-watcher/"
else
    echo -e "${RED}✗${NC} google-drive-watcher k8s manifests not found"
    exit 1
fi

# List copied files
echo -e "\n${BLUE}Files prepared for GitOps:${NC}"
ls -la "$PROJECT_ROOT/k8s/mcps/google-drive-watcher/"

# Create a README for the mcps directory
cat > "$PROJECT_ROOT/k8s/mcps/README.md" << EOF
# MCP Deployments

This directory contains Kubernetes manifests for MCP (Model Context Protocol) servers.

## Directory Structure
\`\`\`
k8s/mcps/
├── google-drive-watcher/   # Google Drive monitoring MCP
│   ├── configmap.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── README.md
\`\`\`

## Deployment
These manifests are automatically deployed by ArgoCD to the \`elf-mcps\` namespace.

## Adding New MCPs
1. Create a new subdirectory for your MCP
2. Add the Kubernetes manifests (deployment, service, configmap)
3. Commit and push - ArgoCD will automatically deploy

## Namespace
All MCPs are deployed to the \`elf-mcps\` namespace.
EOF

echo -e "${GREEN}✓${NC} Created README.md"

# Show what needs to be committed
echo -e "\n${BLUE}Files to add to Git:${NC}"
echo "  - k8s/argocd-apps/elf-mcps.yaml (ArgoCD Application)"
echo "  - k8s/mcps/google-drive-watcher/*.yaml (MCP manifests)"
echo "  - k8s/mcps/README.md"

echo -e "\n${BLUE}Git commands to run:${NC}"
echo -e "${YELLOW}git add k8s/argocd-apps/elf-mcps.yaml${NC}"
echo -e "${YELLOW}git add k8s/mcps/${NC}"
echo -e "${YELLOW}git commit -m \"feat: Add MCP GitOps deployment infrastructure${NC}"
echo -e "${YELLOW}${NC}"
echo -e "${YELLOW}- Create ArgoCD application for MCPs${NC}"
echo -e "${YELLOW}- Add google-drive-watcher MCP deployment${NC}"
echo -e "${YELLOW}- Establish k8s/mcps/ directory for MCP manifests\"${NC}"
echo -e "${YELLOW}git push${NC}"

echo -e "\n${GREEN}✓${NC} MCP deployment preparation complete!"