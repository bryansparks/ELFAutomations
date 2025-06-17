#!/bin/bash

# Create N8n ArgoCD Application
# This script creates an ArgoCD application for n8n workflow automation

set -e

echo "Creating n8n ArgoCD Application..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if ArgoCD namespace exists
if ! kubectl get namespace argocd &> /dev/null; then
    echo "ArgoCD namespace not found. Please install ArgoCD first."
    exit 1
fi

# Create the n8n application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: n8n-workflow
  namespace: argocd
  labels:
    app.kubernetes.io/name: n8n
    app.kubernetes.io/part-of: elf-automations
spec:
  project: default
  source:
    repoURL: https://github.com/bryansparks/ELFAutomations.git
    targetRevision: main
    path: k8s/n8n
  destination:
    server: https://kubernetes.default.svc
    namespace: elf-teams
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
EOF

echo "✅ n8n ArgoCD Application created!"
echo ""
echo "To check status:"
echo "  kubectl get application n8n-workflow -n argocd"
echo ""
echo "To force sync:"
echo "  kubectl patch application n8n-workflow -n argocd --type merge -p '{\"operation\":{\"sync\":{\"revision\":\"HEAD\"}}}'"
echo ""
echo "To access n8n UI (after deployment):"
echo "  kubectl port-forward -n elf-teams svc/n8n 5678:5678"
echo "  Then open http://localhost:5678"
echo ""
echo "Default credentials (from secrets.yaml):"
echo "  Username: admin"
echo "  Password: elf-n8n-2024"
