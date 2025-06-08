#!/bin/bash

# Complete setup script for a new M-series Mac to run ELF Automations
# This script is idempotent - safe to run multiple times

set -e

echo "=== ELF Automations Complete Mac Setup ==="
echo "This script will set up a new Mac to run the ELF Automations platform"
echo "It's safe to run multiple times - existing installations will be skipped"
echo
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Install Homebrew (if not installed)
echo -e "\n${YELLOW}→ Checking Homebrew...${NC}"
if ! command_exists brew; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH for M-series Macs
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo -e "${GREEN}✓ Homebrew already installed${NC}"
fi

# 2. Install Git (if not installed)
echo -e "\n${YELLOW}→ Checking Git...${NC}"
if ! command_exists git; then
    echo "Installing Git..."
    brew install git
else
    echo -e "${GREEN}✓ Git already installed${NC}"
fi

# 3. Install Docker/OrbStack
echo -e "\n${YELLOW}→ Checking OrbStack...${NC}"
if ! command_exists orb; then
    echo "Installing OrbStack (better Docker for Mac)..."
    brew install --cask orbstack
    echo "Starting OrbStack..."
    open -a OrbStack
    echo "Waiting for OrbStack to initialize..."
    sleep 10
else
    echo -e "${GREEN}✓ OrbStack already installed${NC}"
    # Ensure it's running
    if ! pgrep -x "OrbStack" > /dev/null; then
        echo "Starting OrbStack..."
        open -a OrbStack
        sleep 5
    fi
fi

# 4. Enable Kubernetes in OrbStack
echo -e "\n${YELLOW}→ Enabling Kubernetes in OrbStack...${NC}"
echo "Please ensure Kubernetes is enabled in OrbStack preferences!"
echo "Open OrbStack → Settings → Kubernetes → Enable Kubernetes"
echo "Press any key when Kubernetes is enabled..."
read -n 1

# 5. Install kubectl (if not installed)
echo -e "\n${YELLOW}→ Checking kubectl...${NC}"
if ! command_exists kubectl; then
    echo "Installing kubectl..."
    brew install kubectl
else
    echo -e "${GREEN}✓ kubectl already installed${NC}"
fi

# 6. Wait for Kubernetes to be ready
echo -e "\n${YELLOW}→ Waiting for Kubernetes to be ready...${NC}"
until kubectl cluster-info &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e "\n${GREEN}✓ Kubernetes is ready${NC}"

# 7. Clone the repository
echo -e "\n${YELLOW}→ Setting up ELF Automations repository...${NC}"
REPO_DIR="$HOME/projects/ELFAutomations"
if [ ! -d "$REPO_DIR" ]; then
    echo "Cloning repository..."
    mkdir -p "$HOME/projects"
    cd "$HOME/projects"
    git clone https://github.com/bryansparks/ELFAutomations.git
    cd ELFAutomations
else
    echo -e "${GREEN}✓ Repository already exists${NC}"
    cd "$REPO_DIR"
    echo "Pulling latest changes..."
    git pull origin main
fi

# 8. Install ArgoCD
echo -e "\n${YELLOW}→ Installing ArgoCD...${NC}"
if kubectl get namespace argocd &> /dev/null; then
    echo -e "${GREEN}✓ ArgoCD namespace already exists${NC}"
else
    echo "Creating ArgoCD namespace..."
    kubectl create namespace argocd
fi

echo "Installing/Updating ArgoCD..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# 9. Get ArgoCD admin password
echo -e "\n${YELLOW}→ ArgoCD Credentials:${NC}"
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "Username: admin"
echo "Password: $ARGOCD_PASSWORD"
echo "(Save this password!)"

# 10. Create ArgoCD application with correct settings
echo -e "\n${YELLOW}→ Creating ArgoCD application...${NC}"
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: elf-teams
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/bryansparks/ELFAutomations.git
    targetRevision: main
    path: k8s/teams
    directory:
      recurse: true
      include: '{*.yaml,**/*.yaml}'
  destination:
    server: https://kubernetes.default.svc
    namespace: elf-teams
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF

# 11. Build the Docker image
echo -e "\n${YELLOW}→ Building Executive Team Docker image...${NC}"
cd "$REPO_DIR"
if docker images | grep -q "ghcr.io/bryansparks/elfautomations-executive-team"; then
    echo -e "${GREEN}✓ Docker image already exists${NC}"
else
    echo "Building Docker image..."
    bash scripts/build-executive-team.sh
fi

# 12. Wait for initial sync
echo -e "\n${YELLOW}→ Waiting for ArgoCD to sync...${NC}"
sleep 10

# 13. Force a sync to ensure everything is up to date
echo "Triggering ArgoCD sync..."
kubectl patch application elf-teams -n argocd --type merge -p '{"operation":{"sync":{}}}'

# 14. Check deployment status
echo -e "\n${YELLOW}→ Checking deployment status...${NC}"
sleep 5
kubectl get pods -n elf-teams

# 15. Print summary
echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo
echo "ArgoCD UI: http://localhost:8080"
echo "Username: admin"
echo "Password: $ARGOCD_PASSWORD"
echo
echo "To access ArgoCD UI:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo
echo "To check Executive team status:"
echo "  kubectl get pods -n elf-teams"
echo
echo "To test the Executive team API:"
echo "  kubectl port-forward -n elf-teams svc/executive-team 8090:8090"
echo "  curl http://localhost:8090/"
echo
echo "IMPORTANT: Remember to add real API keys:"
echo "  kubectl edit secret llm-api-keys -n elf-teams"
echo
echo "Your GitOps pipeline is ready! Any changes pushed to GitHub will auto-deploy."

# Save credentials to file
echo -e "\nSaving credentials to ~/elf-credentials.txt"
cat > ~/elf-credentials.txt <<EOF
ELF Automations Credentials
Generated: $(date)

ArgoCD:
  URL: http://localhost:8080
  Username: admin
  Password: $ARGOCD_PASSWORD

Quick Commands:
  ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443
  Check pods: kubectl get pods -n elf-teams
  Test API: kubectl port-forward -n elf-teams svc/executive-team 8090:8090

Repository: https://github.com/bryansparks/ELFAutomations
Local path: $REPO_DIR
EOF

echo -e "${GREEN}✓ Credentials saved to ~/elf-credentials.txt${NC}"
