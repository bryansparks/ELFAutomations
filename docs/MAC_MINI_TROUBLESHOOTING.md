# Mac Mini Setup Troubleshooting Guide

## Quick Status Check

Run this on your Mac Mini:
```bash
bash scripts/check-mac-mini-status.sh
```

## Common Issues & Solutions

### 1. OrbStack Issues

**Problem**: OrbStack not starting
```bash
# Restart OrbStack
killall OrbStack || true
open -a OrbStack
```

**Problem**: Kubernetes not enabled
- Open OrbStack app
- Go to Preferences
- Check "Enable Kubernetes"
- Wait 2-3 minutes for it to start

### 2. Kubernetes Connection Issues

**Problem**: kubectl can't connect
```bash
# Check if kubernetes is running in OrbStack
orb status

# Get kubeconfig
mkdir -p ~/.kube
orb kubeconfig > ~/.kube/config
```

### 3. ArgoCD Issues

**Problem**: ArgoCD not installing
```bash
# Clean install ArgoCD
kubectl delete namespace argocd --ignore-not-found
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**Problem**: Can't access ArgoCD UI
```bash
# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 4. Application Sync Issues

**Problem**: ArgoCD app not syncing
```bash
# Check app status
kubectl get application elf-teams -n argocd

# Force sync
kubectl patch application elf-teams -n argocd --type merge -p '{"operation": {"sync": {}}}'

# Check events
kubectl describe application elf-teams -n argocd
```

**Problem**: Namespace not created
```bash
kubectl create namespace elf-teams
```

**Problem**: Secrets missing
```bash
# Create placeholder secrets
kubectl apply -f k8s/teams/secrets.yaml

# Edit to add real keys
kubectl edit secret llm-api-keys -n elf-teams
```

### 5. GitHub Connection Issues

**Problem**: ArgoCD can't reach GitHub
```bash
# Check if the repo is public
# If private, you need to add repo credentials in ArgoCD

# Add repo (if private)
argocd repo add https://github.com/bryansparks/ELFAutomations.git \
  --username YOUR_GITHUB_USERNAME \
  --password YOUR_GITHUB_TOKEN
```

## Reset Everything

If all else fails, here's how to start fresh:

```bash
# 1. Delete ArgoCD
kubectl delete namespace argocd --ignore-not-found

# 2. Delete our app namespace
kubectl delete namespace elf-teams --ignore-not-found

# 3. Reset OrbStack Kubernetes
# In OrbStack app: Settings → Kubernetes → Reset Kubernetes

# 4. Run the simple setup script
bash scripts/setup-mac-mini-simple.sh
```

## Manual Step-by-Step

If the script fails, here's the manual process:

1. **Install OrbStack**
   ```bash
   brew install --cask orbstack
   open -a OrbStack
   # Enable Kubernetes in preferences
   ```

2. **Install ArgoCD**
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

3. **Wait for ArgoCD**
   ```bash
   kubectl get pods -n argocd -w
   # Wait until all pods are Running
   ```

4. **Create ArgoCD App**
   ```bash
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
     destination:
       server: https://kubernetes.default.svc
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
   EOF
   ```

5. **Create Secrets**
   ```bash
   kubectl create namespace elf-teams
   kubectl apply -f k8s/teams/secrets.yaml
   kubectl edit secret llm-api-keys -n elf-teams
   # Add your real API keys
   ```

## Verify Deployment

Once everything is set up:

```bash
# Check ArgoCD app status
kubectl get application elf-teams -n argocd

# Check if pods are running
kubectl get pods -n elf-teams

# Check logs
kubectl logs -n elf-teams -l app=executive-team

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open http://localhost:8080
```
