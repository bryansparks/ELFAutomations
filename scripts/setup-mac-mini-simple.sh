#!/bin/bash
set -e

echo "=== Simplified Mac Mini Setup for ELF Automations ==="
echo
echo "This script will:"
echo "1. Install OrbStack (if needed)"
echo "2. Enable Kubernetes in OrbStack"
echo "3. Install ArgoCD"
echo "4. Configure ArgoCD to watch our GitHub repo"
echo "5. Deploy the Executive team"
echo
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 1. Check/Install OrbStack
echo "→ Checking OrbStack..."
if ! command -v orb &> /dev/null; then
    echo "Installing OrbStack..."
    brew install --cask orbstack
else
    echo "✓ OrbStack already installed"
fi

# 2. Start OrbStack and enable Kubernetes
echo "→ Starting OrbStack..."
open -a OrbStack
sleep 5

echo "→ Enabling Kubernetes in OrbStack..."
# OrbStack has k8s built-in, just needs to be enabled via the UI
echo "Please ensure Kubernetes is enabled in OrbStack preferences!"
echo "Press any key when Kubernetes is enabled..."
read -n 1

# 3. Wait for Kubernetes to be ready
echo "→ Waiting for Kubernetes to be ready..."
until kubectl cluster-info &> /dev/null; do
    echo -n "."
    sleep 2
done
echo " Ready!"

# 4. Install ArgoCD
echo "→ Installing ArgoCD..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "→ Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# 5. Get ArgoCD admin password
echo "→ Getting ArgoCD admin password..."
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "ArgoCD admin password: $ARGOCD_PASSWORD"
echo "(Save this password!)"

# 6. Create our application in ArgoCD
echo "→ Creating ArgoCD application..."
cat <<EOF | kubectl apply -f -
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
  destination:
    server: https://kubernetes.default.svc
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF

# 7. Create secrets with placeholder values
echo "→ Creating namespace and secrets..."
kubectl create namespace elf-teams --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: llm-api-keys
  namespace: elf-teams
type: Opaque
stringData:
  OPENAI_API_KEY: "your-openai-api-key-here"
  ANTHROPIC_API_KEY: "your-anthropic-api-key-here"
EOF

echo
echo "=== Setup Complete! ==="
echo
echo "ArgoCD UI: http://localhost:8080"
echo "Username: admin"
echo "Password: $ARGOCD_PASSWORD"
echo
echo "To access ArgoCD UI:"
echo "kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo
echo "IMPORTANT: Update the API keys in the secret:"
echo "kubectl edit secret llm-api-keys -n elf-teams"
echo
echo "ArgoCD will sync the Executive team from GitHub within 3 minutes."
