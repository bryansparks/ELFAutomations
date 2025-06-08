#!/bin/bash

echo "=== Recreating ArgoCD Application ==="
echo

echo "1. Deleting existing app:"
kubectl delete application elf-teams -n argocd
echo

echo "2. Creating new app with correct configuration:"
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

echo
echo "3. Waiting for app to be created..."
sleep 5

echo
echo "4. Triggering initial sync:"
kubectl patch application elf-teams -n argocd --type merge -p '{"operation":{"sync":{}}}'

echo
echo "5. Checking application status:"
sleep 5
kubectl get application elf-teams -n argocd

echo
echo "6. Checking resources:"
kubectl get application elf-teams -n argocd -o jsonpath='{.status.resources[*].name}' | tr ' ' '\n'
