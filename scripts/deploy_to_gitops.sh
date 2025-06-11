#!/bin/bash
#
# Deploy to GitOps - Complete workflow to get artifacts to ArgoCD
#
# This script:
# 1. Builds and pushes Docker images
# 2. Updates manifest with correct image references
# 3. Prepares GitOps artifacts
# 4. Shows how to push to GitOps repo

set -e

# Configuration
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"docker.io/your-org"}
GITOPS_REPO=${GITOPS_REPO:-"git@github.com:your-org/gitops-repo.git"}
GITOPS_BRANCH=${GITOPS_BRANCH:-"main"}

echo "🚀 ElfAutomations GitOps Deployment"
echo "=================================="
echo "Docker Registry: $DOCKER_REGISTRY"
echo "GitOps Repo: $GITOPS_REPO"
echo ""

# Step 1: Build and push Docker images for teams
echo "📦 Step 1: Building Docker images..."
echo ""

# Executive Team
if [ -d "teams/executive-team" ]; then
    echo "Building executive-team..."
    cd teams/executive-team

    # Make deployable
    python make-deployable-team.py

    # Build image
    docker build -t $DOCKER_REGISTRY/elf-automations/executive-team:latest .

    # Push image (uncomment when ready)
    # docker push $DOCKER_REGISTRY/elf-automations/executive-team:latest

    cd ../..
fi

# Add more teams here as they're created
# for team in teams/*; do
#     if [ -d "$team" ]; then
#         # Build and push each team
#     fi
# done

# Step 2: Update image references in manifests
echo ""
echo "📝 Step 2: Updating image references..."
export DOCKER_REGISTRY  # Make available to Python script

# Step 3: Prepare GitOps artifacts
echo ""
echo "🔧 Step 3: Preparing GitOps artifacts..."
python tools/prepare_gitops_artifacts.py

# Step 4: Show GitOps directory structure
echo ""
echo "📂 GitOps directory structure:"
tree gitops/ -I '__pycache__'

# Step 5: Instructions for GitOps repo
echo ""
echo "📤 Step 4: Push to GitOps Repository"
echo "===================================="
echo ""
echo "Option A: If you have a separate GitOps repository:"
echo "  1. Clone your GitOps repo:"
echo "     git clone $GITOPS_REPO /tmp/gitops-repo"
echo ""
echo "  2. Copy artifacts:"
echo "     cp -r gitops/* /tmp/gitops-repo/"
echo ""
echo "  3. Commit and push:"
echo "     cd /tmp/gitops-repo"
echo "     git add ."
echo "     git commit -m 'Deploy ElfAutomations teams'"
echo "     git push origin $GITOPS_BRANCH"
echo ""
echo "Option B: If using this repository for GitOps:"
echo "  1. Commit the gitops directory:"
echo "     git add gitops/"
echo "     git commit -m 'Update GitOps manifests'"
echo "     git push origin main"
echo ""

# Step 6: Apply ArgoCD applications
echo "🚀 Step 5: Deploy with ArgoCD"
echo "============================="
echo ""
echo "On your ArgoCD machine:"
echo ""
echo "1. Apply the ArgoCD applications:"
echo "   kubectl apply -f gitops/applications/"
echo ""
echo "2. Or use ArgoCD CLI:"
echo "   argocd app create elf-teams --file gitops/applications/teams-app.yaml"
echo "   argocd app sync elf-teams"
echo ""
echo "3. Monitor deployment:"
echo "   argocd app list"
echo "   argocd app get elf-teams"
echo ""

# Step 7: Verify deployment
echo "✅ Step 6: Verify Deployment"
echo "==========================="
echo ""
echo "Check pods are running:"
echo "  kubectl get pods -n elf-automations"
echo ""
echo "Check services:"
echo "  kubectl get svc -n elf-automations"
echo ""
echo "Test A2A discovery:"
echo "  kubectl logs deployment/agentgateway -n elf-automations | grep 'Discovered'"
echo ""

echo "🎉 GitOps preparation complete!"
echo ""
echo "⚠️  Important Notes:"
echo "- Ensure your K8s cluster can pull from $DOCKER_REGISTRY"
echo "- ArgoCD must have access to your GitOps repository"
echo "- Update DOCKER_REGISTRY env var to your actual registry"
