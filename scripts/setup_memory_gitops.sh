#!/bin/bash
# Setup Memory System for GitOps deployment

echo "Memory & Learning System - GitOps Setup"
echo "======================================"
echo ""

# Step 1: Setup Supabase schema (runs locally)
echo "Step 1: Creating Supabase schema..."
python scripts/setup_memory_system.py --skip-k8s

if [ $? -ne 0 ]; then
    echo "❌ Failed to create Supabase schema"
    exit 1
fi

echo "✅ Supabase schema created"
echo ""

# Step 2: Prepare Qdrant for GitOps
echo "Step 2: Preparing Qdrant manifests for ArgoCD..."

# Check if Qdrant manifests exist
if [ -d "k8s/data-stores/qdrant" ]; then
    echo "✅ Qdrant manifests found at k8s/data-stores/qdrant/"
    echo ""
    echo "Files to be deployed by ArgoCD:"
    ls -la k8s/data-stores/qdrant/
else
    echo "❌ Qdrant manifests not found!"
    exit 1
fi

echo ""
echo "Step 3: GitOps Deployment Instructions"
echo "--------------------------------------"
echo "1. Commit and push the Qdrant manifests:"
echo "   git add k8s/data-stores/qdrant/"
echo "   git commit -m 'feat: Add Qdrant vector database for memory system'"
echo "   git push"
echo ""
echo "2. ArgoCD will automatically deploy Qdrant to your K3s cluster"
echo ""
echo "3. After deployment, verify on the K3s machine:"
echo "   ssh bryan@192.168.6.5"
echo "   kubectl get pods -n elf-automations -l app=qdrant"
echo "   kubectl get svc -n elf-automations qdrant"
echo ""
echo "4. For local development, you can port-forward from K3s:"
echo "   ssh -L 6333:localhost:6333 bryan@192.168.6.5 \\"
echo "     'kubectl port-forward -n elf-automations svc/qdrant 6333:6333'"
echo ""
echo "======================================"
echo "✅ GitOps setup complete!"
echo ""
echo "Next steps:"
echo "- Commit and push Qdrant manifests"
echo "- Wait for ArgoCD deployment"
echo "- Build Memory & Learning MCP server"
echo "- Create RAG free-agent team"