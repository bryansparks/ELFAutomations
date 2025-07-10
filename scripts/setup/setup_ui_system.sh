#!/bin/bash

# ELF UI System Setup Script

echo "🎨 Setting up ELF UI Design System..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the project root by looking for Python project files
if [ ! -f "pyproject.toml" ] && [ ! -f "README.md" ]; then
    echo "❌ Error: Must run from project root"
    exit 1
fi

# Create workspace package.json if it doesn't exist
if [ ! -f "package.json" ]; then
    echo -e "${BLUE}Creating workspace package.json...${NC}"
    cat > package.json << EOF
{
  "name": "elf-automations",
  "private": true,
  "workspaces": [
    "packages/*",
    "dashboard",
    "packages/templates/*"
  ],
  "scripts": {
    "dev:ui": "cd packages/ui && npm run dev",
    "build:ui": "cd packages/ui && npm run build",
    "dev:control-center": "cd packages/templates/elf-control-center && npm run dev",
    "storybook": "cd packages/ui && npm run storybook"
  },
  "devDependencies": {
    "prettier": "^3.2.5"
  }
}
EOF
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}⚠️  npm is not installed. Please install Node.js and npm first.${NC}"
    echo "Visit https://nodejs.org/ to download and install Node.js"
    exit 1
fi

# Install dependencies for UI package
echo -e "${BLUE}Installing UI package dependencies...${NC}"
if [ -d "packages/ui" ]; then
    cd packages/ui
    npm install
    cd ../..
else
    echo -e "${YELLOW}Warning: packages/ui directory not found${NC}"
fi

# Install dependencies for CLI
echo -e "${BLUE}Installing CLI dependencies...${NC}"
if [ -d "packages/cli" ]; then
    cd packages/cli
    npm install
    npm run build || echo -e "${YELLOW}Warning: CLI build failed${NC}"
    cd ../..
else
    echo -e "${YELLOW}Warning: packages/cli directory not found${NC}"
fi

# Install dependencies for ELF Control Center template
echo -e "${BLUE}Installing ELF Control Center dependencies...${NC}"
if [ -d "packages/templates/elf-control-center" ]; then
    cd packages/templates/elf-control-center
    npm install
    cd ../../..
else
    echo -e "${YELLOW}Warning: packages/templates/elf-control-center directory not found${NC}"
fi

# Create symlink for global CLI usage (may require sudo)
echo -e "${BLUE}Setting up global CLI command...${NC}"
if [ -d "packages/cli" ]; then
    cd packages/cli
    echo -e "${YELLOW}Note: npm link may require sudo permissions${NC}"
    npm link || echo -e "${YELLOW}Warning: Could not create global link. You may need to run: cd packages/cli && sudo npm link${NC}"
    cd ../..
fi

# Build UI package
echo -e "${BLUE}Building UI package...${NC}"
if [ -d "packages/ui" ]; then
    cd packages/ui
    npm run build || echo -e "${YELLOW}Warning: UI build failed${NC}"
    cd ../..
fi

# Success message
echo -e "${GREEN}✅ ELF UI System setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Start the UI development server:"
echo "   ${BLUE}npm run dev:ui${NC}"
echo ""
echo "2. Start Storybook to view components:"
echo "   ${BLUE}npm run storybook${NC}"
echo ""
echo "3. Start the ELF Control Center:"
echo "   ${BLUE}npm run dev:control-center${NC}"
echo ""
echo "4. Create a new app with the CLI:"
echo "   ${BLUE}elf-ui create my-app --template=dashboard${NC}"
echo ""
echo "5. View the documentation:"
echo "   ${BLUE}cat docs/ELF_UI_DESIGN_SYSTEM.md${NC}"
