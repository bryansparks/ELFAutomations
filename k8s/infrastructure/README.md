# ElfAutomations Infrastructure

This directory contains all infrastructure components for ElfAutomations, managed via GitOps with ArgoCD.

## Structure

```
k8s/infrastructure/
├── kustomization.yaml      # Parent kustomization
├── neo4j/                  # Graph database
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ...
├── qdrant/                 # Vector database (future)
├── monitoring/             # Prometheus/Grafana (future)
└── logging/                # ELK or Loki (future)
```

## Deployment

All infrastructure is deployed via ArgoCD:

1. **Initial Setup** (one time only):
   ```bash
   # On ArgoCD machine
   ./scripts/create-infrastructure-argocd-app.sh
   ```

2. **Adding New Components**:
   - Add manifests under appropriate subdirectory
   - Update this parent `kustomization.yaml`
   - Commit and push
   - ArgoCD will auto-deploy

## Current Components

### Neo4j (Graph Database)
- **Purpose**: Multi-tenant graph storage for RAG
- **Access**: NodePort 30474 (UI), 30687 (Bolt)
- **Namespace**: elf-infrastructure

## Planned Components

### Qdrant (Vector Database)
- **Purpose**: Semantic search and embeddings
- **Status**: To be added

### Monitoring Stack
- **Purpose**: Prometheus + Grafana for metrics
- **Status**: Planned

### Logging Stack
- **Purpose**: Centralized logging
- **Status**: Planned

## GitOps Workflow

1. Make changes in this directory
2. Commit and push to GitHub
3. ArgoCD automatically syncs within 3 minutes
4. Check status: `kubectl get app -n argocd elf-infrastructure`

## Best Practices

1. **Namespace Isolation**: Each component uses appropriate namespace
2. **Resource Limits**: All deployments have resource requests/limits
3. **Persistent Storage**: Use PVCs for stateful components
4. **Security**: Use secrets for credentials (consider external secret management)
5. **Labels**: Consistent labeling for resource management

## Troubleshooting

### Check ArgoCD Sync Status
```bash
kubectl get app -n argocd elf-infrastructure
kubectl describe app -n argocd elf-infrastructure
```

### View ArgoCD Logs
```bash
kubectl logs -n argocd deployment/argocd-server
```

### Force Sync
```bash
argocd app sync elf-infrastructure
```

## Adding New Infrastructure

1. Create new directory under `/k8s/infrastructure/`
2. Add Kubernetes manifests
3. Create `kustomization.yaml` in that directory
4. Update parent `kustomization.yaml` to include it
5. Commit, push, and ArgoCD handles the rest
