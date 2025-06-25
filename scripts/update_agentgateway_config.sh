#!/bin/bash

# Update AgentGateway Configuration Script
# This script helps update the AgentGateway configuration for GitOps deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config/agentgateway"
K8S_DIR="$PROJECT_ROOT/k8s/base/agentgateway"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}AgentGateway Configuration Update Script${NC}"
echo "========================================"

# Check if mcp-config.json exists
if [ -f "$CONFIG_DIR/mcp-config.json" ]; then
    echo -e "${GREEN}✓${NC} Found enhanced MCP configuration at: $CONFIG_DIR/mcp-config.json"
    
    # Show current MCP servers
    echo -e "\n${BLUE}Current MCP servers configured:${NC}"
    jq -r '.targets.mcp[].name' "$CONFIG_DIR/mcp-config.json" | while read -r mcp; do
        echo "  - $mcp"
    done
else
    echo -e "${YELLOW}!${NC} Enhanced MCP configuration not found at: $CONFIG_DIR/mcp-config.json"
    echo "  Using basic configuration from: $CONFIG_DIR/config.json"
fi

# Update kustomization to use mcp-config.json
echo -e "\n${BLUE}Updating kustomization.yaml to use enhanced config...${NC}"

# Check if we need to update the kustomization
if grep -q "config.json=.*config.json" "$K8S_DIR/kustomization.yaml"; then
    echo "Current configuration file: config.json"
    echo "Would you like to switch to mcp-config.json? (y/n)"
    read -r response
    
    if [[ "$response" == "y" ]]; then
        # Backup current kustomization
        cp "$K8S_DIR/kustomization.yaml" "$K8S_DIR/kustomization.yaml.bak"
        
        # Update to use mcp-config.json
        sed -i '' 's|config.json=.*config.json|config.json=../../../config/agentgateway/mcp-config.json|' "$K8S_DIR/kustomization.yaml"
        
        echo -e "${GREEN}✓${NC} Updated kustomization.yaml to use mcp-config.json"
    fi
else
    echo -e "${GREEN}✓${NC} Already using enhanced configuration"
fi

# Show next steps
echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Review the configuration:"
echo "   cat $CONFIG_DIR/mcp-config.json"
echo ""
echo "2. Commit changes to Git:"
echo "   git add $K8S_DIR/kustomization.yaml"
echo "   git add $CONFIG_DIR/mcp-config.json"
echo "   git commit -m \"Update AgentGateway with enhanced MCP configuration\""
echo "   git push"
echo ""
echo "3. ArgoCD will automatically deploy the changes"
echo ""
echo "4. Monitor the deployment:"
echo "   kubectl logs -n virtual-ai-platform deployment/agentgateway -f"

# Additional info about missing MCPs
echo -e "\n${YELLOW}Note: The following MCPs may need to be deployed:${NC}"
echo "- google-drive-watcher (check: mcps/google-drive-watcher/)"
echo "- project-management (check: mcp/typescript/servers/project-management/)"
echo "- memory-learning (check: mcp/typescript/servers/memory-learning/)"

echo -e "\n${GREEN}✓${NC} Configuration update preparation complete!"