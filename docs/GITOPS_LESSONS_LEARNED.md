# GitOps Lessons Learned

## What Went Wrong

1. **Kustomize Complexity**: The kustomization.yaml file added unnecessary complexity for simple deployments
2. **Resource Drift**: Old Kubernetes resources remained in the cluster when removed from Git
3. **Multi-document YAML**: Files with `---` separators caused issues with some tools
4. **Template Variables**: Unresolved variables like `${OPENAI_API_KEY}` in secrets.yaml caused failures
5. **Recursive Directory Scanning**: Can pick up unintended files or cause parsing errors

## What Worked

1. **Direct Path**: Pointing ArgoCD directly to specific YAML files (e.g., `combined.yaml`)
2. **Single File Manifests**: Combining related resources in one file with `---` separators
3. **Simple Sync Policies**: Starting with basic sync options before adding complexity
4. **Manual Sync First**: Testing with manual sync before enabling auto-sync

## Best Practices Going Forward

### 1. File Organization
```
k8s/
├── infrastructure/
│   └── <service>/
│       └── combined.yaml  # All resources for this service
├── teams/
│   └── combined.yaml      # Minimal shared resources
└── apps/
    └── <app-name>/
        └── combined.yaml  # All resources for this app
```

### 2. ArgoCD Application Template
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app-name>
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/bryansparks/ELFAutomations.git
    targetRevision: main
    path: k8s/<category>
    directory:
      include: '<specific-file>.yaml'  # Be explicit!
  destination:
    server: https://kubernetes.default.svc
    namespace: <target-namespace>
  syncPolicy:
    syncOptions:
    - CreateNamespace=true
    # Add these only after testing:
    # automated:
    #   prune: true
    #   selfHeal: true
```

### 3. Development Workflow

1. **Start Simple**: Create combined.yaml with all resources
2. **Test Locally**: `kubectl apply -f combined.yaml --dry-run=client`
3. **Deploy Manually First**: Create ArgoCD app without auto-sync
4. **Verify**: Ensure resources deploy correctly
5. **Enable Automation**: Add auto-sync and prune after verification

### 4. Debugging Checklist

When ArgoCD shows "Missing" or "Degraded":
- Check ArgoCD logs: `kubectl logs -n argocd deployment/argocd-repo-server`
- Verify Git access: `kubectl exec -n argocd deployment/argocd-repo-server -- git ls-remote <repo>`
- Test manifest generation locally
- Look for template variables that need resolution
- Check for YAML syntax errors

### 5. Resource Cleanup

Before major changes:
```bash
# Save current state
kubectl get all -n <namespace> -o yaml > backup.yaml

# Clean namespace
kubectl delete all --all -n <namespace>

# Let ArgoCD recreate from Git
kubectl patch application <app-name> -n argocd --type merge \
  -p '{"operation":{"sync":{"revision":"HEAD"}}}'
```

## Simplified Deployment Process

For new services going forward:

1. Create `k8s/apps/<name>/combined.yaml` with all resources
2. Create ArgoCD app pointing to that specific file
3. Test with manual sync
4. Enable auto-sync only after verification
5. Keep it simple - avoid Kustomize unless truly needed
