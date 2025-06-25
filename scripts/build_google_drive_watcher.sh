#!/bin/bash

# Build script for google-drive-watcher MCP
# This prepares the Docker image for transfer to ArgoCD machine

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MCP_DIR="$PROJECT_ROOT/mcps/google-drive-watcher"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Google Drive Watcher MCP Build Script${NC}"
echo "====================================="

# Check if we're in the right place
if [ ! -d "$MCP_DIR" ]; then
    echo -e "${RED}✗${NC} google-drive-watcher directory not found at: $MCP_DIR"
    exit 1
fi

cd "$MCP_DIR"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}✗${NC} Dockerfile not found in $MCP_DIR"
    exit 1
fi

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}✗${NC} package.json not found - is this a Node.js project?"
    exit 1
fi

# Build the project first
echo -e "\n${BLUE}Step 1: Building TypeScript project...${NC}"
if [ -f "package-lock.json" ]; then
    npm ci
else
    npm install
fi

npm run build
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} TypeScript build successful"
else
    echo -e "${RED}✗${NC} TypeScript build failed"
    exit 1
fi

# Check if dist directory was created
if [ ! -d "dist" ]; then
    echo -e "${RED}✗${NC} Build did not create dist directory"
    exit 1
fi

# Build Docker image
echo -e "\n${BLUE}Step 2: Building Docker image...${NC}"
docker build -t elf-automations/google-drive-watcher:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Docker image built successfully"
else
    echo -e "${RED}✗${NC} Docker build failed"
    exit 1
fi

# Show image info
echo -e "\n${BLUE}Image Information:${NC}"
docker images elf-automations/google-drive-watcher:latest

# Create a list of images to transfer
echo -e "\n${BLUE}Creating image list for transfer...${NC}"
echo "elf-automations/google-drive-watcher:latest" > "$PROJECT_ROOT/images-to-transfer.txt"

echo -e "\n${GREEN}✓${NC} Build complete!"
echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Transfer the image to ArgoCD machine:"
echo "   ${YELLOW}./scripts/transfer-docker-images-ssh.sh${NC}"
echo ""
echo "2. Commit the k8s manifests:"
echo "   ${YELLOW}git add mcps/google-drive-watcher/k8s/${NC}"
echo "   ${YELLOW}git commit -m \"deploy: Add google-drive-watcher MCP\"${NC}"
echo "   ${YELLOW}git push${NC}"
echo ""
echo "3. ArgoCD will deploy the MCP to the elf-mcps namespace"