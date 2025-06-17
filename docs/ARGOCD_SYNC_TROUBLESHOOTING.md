# ArgoCD Sync Troubleshooting Guide

## Common Sync Issues and Solutions

### 1. Repository Not Accessible
**Symptoms:**
- "Repository not accessible" errors
- "Failed to fetch" messages

**Solutions:**
```bash
# Check Git connectivity from repo-server pod
REPO_SERVER=$(kubectl get pods -n argocd -l app.kubernetes.io/component=repo-server -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n argocd $REPO_SERVER -- git ls-remote https://github.com/bryansparks/ELFAutomations.git HEAD

# Clear repository cache
kubectl exec -n argocd $REPO_SERVER -- rm -rf /tmp/git@github.com:bryansparks:ELFAutomations*
```

### 2. Out of Sync - Won't Update
**Symptoms:**
- Application shows "OutOfSync" but won't sync
- Changes in Git not reflected in cluster

**Solutions:**
```bash
# Force refresh (re-reads from Git)
kubectl patch application elf-teams -n argocd --type merge \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"true"}}}'

# Manual sync with prune
kubectl patch application elf-teams -n argocd --type merge \
  -p '{"operation":{"sync":{"prune":true,"revision":"HEAD"}}}'
```

### 3. Stuck in Progressing State
**Symptoms:**
- Application stuck in "Progressing" state
- Sync operation never completes

**Solutions:**
```bash
# Check detailed status
kubectl describe application elf-teams -n argocd

# Force terminate sync operation
kubectl patch application elf-teams -n argocd --type merge \
  -p '{"operation":null}'

# Delete and recreate application
kubectl delete application elf-teams -n argocd
# Then recreate using the script
```

### 4. Image Pull Errors (Local Images)
**Symptoms:**
- "ErrImagePull" or "ImagePullBackOff"
- Using local Docker images with imagePullPolicy: Never

**Solutions:**
```bash
# On deployment machine, check if images exist
docker images | grep elf-automations

# If missing, transfer from dev machine:
# On dev machine:
./scripts/transfer-docker-images-ssh.sh

# Verify on deployment machine:
docker images | grep elf-automations
```

### 5. Namespace Issues
**Symptoms:**
- "namespace not found" errors
- Resources failing to create

**Solutions:**
```bash
# Ensure syncOptions includes CreateNamespace
kubectl edit application elf-teams -n argocd
# Add under spec.syncPolicy.syncOptions:
# - CreateNamespace=true

# Manually create namespace if needed
kubectl create namespace elf-teams
kubectl create namespace elf-infrastructure
```

## Quick Reset Commands

### Soft Reset (Refresh from Git)
```bash
# For teams
kubectl patch application elf-teams -n argocd --type merge \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"true"}}}'

# For infrastructure  
kubectl patch application elf-infrastructure -n argocd --type merge \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"true"}}}'
```

### Hard Reset (Delete and Recreate)
```bash
# Delete applications
kubectl delete application elf-teams elf-infrastructure -n argocd

# Recreate
kubectl apply -f scripts/argocd-apps/elf-teams.yaml
kubectl apply -f scripts/argocd-apps/elf-infrastructure.yaml
```

### Nuclear Reset (Complete ArgoCD Reset)
```bash
# WARNING: This will delete all ArgoCD data!
# 1. Export application definitions first
kubectl get applications -n argocd -o yaml > argocd-apps-backup.yaml

# 2. Delete ArgoCD namespace
kubectl delete namespace argocd

# 3. Reinstall ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 4. Restore applications
kubectl apply -f argocd-apps-backup.yaml
```

## Using the Reset Script

We've created `scripts/reset-argocd-sync.sh` that automates these troubleshooting steps:

```bash
# On deployment machine
cd /path/to/ELFAutomations
./scripts/reset-argocd-sync.sh

# Options:
# 1 - Quick diagnosis
# 2 - Force refresh all
# 3 - Hard refresh (clear cache)
# 4 - Reset specific app
# 5 - Reset all apps
# 6 - Check Git connectivity
# 7 - Full system reset
```

## Monitoring Sync Status

### Watch sync status in real-time
```bash
watch -n 2 "kubectl get applications -n argocd"
```

### Get detailed sync status
```bash
kubectl get application elf-teams -n argocd -o jsonpath='{.status.sync}' | jq
```

### Check ArgoCD logs
```bash
# Application controller logs
kubectl logs -n argocd -l app.kubernetes.io/component=application-controller --tail=100

# Repo server logs  
kubectl logs -n argocd -l app.kubernetes.io/component=repo-server --tail=100
```

## Prevention Tips

1. **Always commit and push changes** before expecting sync
2. **Check image availability** when using local images
3. **Monitor ArgoCD health** regularly
4. **Use proper sync policies** (automated with prune and self-heal)
5. **Keep ArgoCD updated** to latest stable version

## Emergency Contacts

- ArgoCD Slack: #argo-cd on CNCF Slack
- GitHub Issues: https://github.com/argoproj/argo-cd/issues
- Documentation: https://argo-cd.readthedocs.io/