#!/bin/bash
# Quick setup script for Google Drive Watcher MCP

echo "🚀 Google Drive Watcher MCP Setup"
echo "================================"

# Check if we're in the right directory
if [ ! -f "mcps/google-drive-watcher/package.json" ]; then
    echo "❌ Please run this script from the ELFAutomations root directory"
    exit 1
fi

# Check for required environment variables
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "❌ Missing Google OAuth credentials"
    echo "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file"
    echo ""
    echo "To get these credentials:"
    echo "1. Go to https://console.cloud.google.com"
    echo "2. Create a project and enable Google Drive API"
    echo "3. Create OAuth 2.0 credentials"
    echo "4. Add to your .env file"
    exit 1
fi

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "❌ Missing Supabase credentials"
    echo "Please set SUPABASE_URL and SUPABASE_KEY in your .env file"
    exit 1
fi

echo "✅ Environment variables detected"

# Build the MCP
echo ""
echo "📦 Building Google Drive Watcher MCP..."
cd mcps/google-drive-watcher

# Install dependencies
echo "Installing dependencies..."
npm install

# Build TypeScript
echo "Building TypeScript..."
npm run build

# Build Docker image
echo ""
echo "🐳 Building Docker image..."
docker build -t elf-automations/google-drive-watcher:latest .

echo ""
echo "✅ Build complete!"

# Option to deploy
echo ""
read -p "Deploy to Kubernetes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating namespace..."
    kubectl create namespace elf-mcps 2>/dev/null || true

    echo "Creating secrets..."
    kubectl create secret generic google-oauth-credentials \
        --from-literal=client_id=$GOOGLE_CLIENT_ID \
        --from-literal=client_secret=$GOOGLE_CLIENT_SECRET \
        -n elf-mcps \
        --dry-run=client -o yaml | kubectl apply -f -

    kubectl create secret generic supabase-credentials \
        --from-literal=url=$SUPABASE_URL \
        --from-literal=service_key=$SUPABASE_KEY \
        -n elf-mcps \
        --dry-run=client -o yaml | kubectl apply -f -

    echo "Deploying MCP..."
    kubectl apply -f k8s/deployment.yaml

    echo ""
    echo "✅ Deployed to Kubernetes!"
    echo ""
    echo "Check status with:"
    echo "kubectl get pods -n elf-mcps"
else
    echo ""
    echo "To deploy later, run:"
    echo "kubectl apply -f mcps/google-drive-watcher/k8s/deployment.yaml"
fi

cd ../..

echo ""
echo "📝 Next steps:"
echo "1. Set up OAuth for each tenant: python scripts/setup_google_oauth.py"
echo "2. Create folder structure in Google Drive:"
echo "   /elf-drops/"
echo "   ├── core/"
echo "   ├── acme-corp/"
echo "   └── globex-inc/"
echo "3. Add folders to monitoring"
echo ""
echo "🎉 Google Drive Watcher MCP is ready!"
