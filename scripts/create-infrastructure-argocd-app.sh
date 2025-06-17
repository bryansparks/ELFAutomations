#!/bin/bash
# Create ArgoCD application for infrastructure components

echo "Creating ArgoCD app for infrastructure..."

kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: elf-infrastructure
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/bryansparks/ELFAutomations.git
    targetRevision: HEAD
    path: k8s/infrastructure
  destination:
    server: https://kubernetes.default.svc
    namespace: elf-infrastructure
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF

echo "✅ ArgoCD infrastructure app created"
echo "Check status with: kubectl get app -n argocd elf-infrastructure"
