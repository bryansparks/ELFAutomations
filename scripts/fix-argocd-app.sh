#!/bin/bash

echo "=== Checking ArgoCD Application Configuration ==="
echo

echo "1. Current ArgoCD app source path:"
kubectl get application elf-teams -n argocd -o jsonpath='{.spec.source.path}'
echo
echo

echo "2. Let's see what ArgoCD app looks like:"
kubectl get application elf-teams -n argocd -o yaml | grep -A 10 "source:"
echo

echo "3. Checking what's in our GitHub repo k8s/teams directory:"
echo "Go to: https://github.com/bryansparks/ELFAutomations/tree/main/k8s/teams"
echo "You should see:"
echo "  - namespace.yaml"
echo "  - secrets.yaml"
echo "  - executive/ (directory with deployment.yaml, service.yaml, etc.)"
echo

echo "4. To fix, we need to update the ArgoCD app to recurse into subdirectories:"
cat << 'EOF'

kubectl apply -f - <<YAML
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
      recurse: true  # This tells ArgoCD to look in subdirectories
  destination:
    server: https://kubernetes.default.svc
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
YAML

EOF
