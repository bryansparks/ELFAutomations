# Current Deployment Inventory (June 17, 2025)

## What's Actually Deployed (via ArgoCD)

### 1. **elf-infrastructure** (Synced, Healthy)
- **Path**: `k8s/infrastructure/`
- **Contains**: Neo4j graph database
- **Namespace**: `elf-infrastructure`
- **Resources**:
  - Neo4j deployment with 2 PVCs (data + logs)
  - ConfigMap with Neo4j configuration
  - Secret with credentials
  - 2 Services (internal ClusterIP + external NodePort)
  - Access: Port 30474 (browser), 30687 (bolt)

### 2. **elf-teams-direct** (Synced, Healthy)
- **Path**: `k8s/teams/combined.yaml`
- **Namespace**: `elf-teams`
- **Resources**:
  - Namespace
  - Minimal ConfigMap placeholder
  - NO active team deployments (cleaned up)

### 3. **n8n** (Should be Synced, Healthy)
- **Path**: `k8s/apps/n8n/combined.yaml`
- **Namespace**: `n8n`
- **Resources**:
  - Namespace
  - Deployment (n8n workflow automation)
  - Secret with credentials
  - PVC for data persistence
  - 2 Services (internal + NodePort 30678)
  - Test ConfigMap (auto-deployed)

## What's in the Repository (But NOT Deployed)

### Old/Legacy Configurations:
- `k8s/agentgateway/` - Old agent gateway setup
- `k8s/base/` - Complex Kustomize base configurations
- `k8s/kagent/` - Kagent CRDs and deployments
- `k8s/data-stores/qdrant/` - Vector database (not deployed)
- `k8s/n8n/` - Old n8n configuration (replaced by apps/n8n)
- `k8s/production/`, `k8s/staging/` - Environment overlays
- `k8s/teams/executive*/` - Archived team deployments

### Simplified Active Paths:
```
k8s/
├── apps/
│   └── n8n/
│       └── combined.yaml          ✅ DEPLOYED
├── infrastructure/
│   └── neo4j/                     ✅ DEPLOYED
│       ├── deployment.yaml
│       ├── configmap.yaml
│       ├── service.yaml
│       └── ...
└── teams/
    └── combined.yaml              ✅ DEPLOYED (minimal)
```

## ArgoCD Applications

| App Name | Source Path | Target Namespace | Auto-Sync | Status |
|----------|-------------|------------------|-----------|---------|
| elf-infrastructure | k8s/infrastructure | elf-infrastructure | Enabled* | Healthy |
| elf-teams-direct | k8s/teams/combined.yaml | elf-teams | Enabled* | Healthy |
| n8n | k8s/apps/n8n/combined.yaml | n8n | Enabled* | Healthy |

*Auto-sync enabled if you ran `enable-auto-sync.sh`

## Access Points

### Neo4j (Graph Database)
- Internal: `neo4j.elf-infrastructure.svc.cluster.local:7687`
- External: `<node-ip>:30474` (browser), `<node-ip>:30687` (bolt)
- Credentials: neo4j / elf-automation-2024

### n8n (Workflow Automation)
- Internal: `n8n.n8n.svc.cluster.local:5678`
- External: `<node-ip>:30678`
- Credentials: admin / elf-n8n-2024

## What Should Be on Deployment Machine

```bash
# Check deployed applications
kubectl get applications -n argocd

# Should show:
# - elf-infrastructure (Neo4j)
# - elf-teams-direct (minimal placeholder)
# - n8n (workflow automation)

# Check namespaces
kubectl get namespaces | grep -E "(elf-|n8n)"

# Should show:
# - elf-infrastructure
# - elf-teams
# - n8n

# Check running pods
kubectl get pods -A | grep -E "(neo4j|n8n|elf-)"

# Should show:
# - neo4j pod in elf-infrastructure (Running)
# - n8n pod in n8n namespace (Running)
# - No pods in elf-teams (minimal setup)
```

## Clean Architecture Going Forward

1. **Use `k8s/apps/`** for new applications
2. **Use `k8s/infrastructure/`** for shared services
3. **Keep `k8s/teams/`** minimal until teams are developed
4. **Ignore/archive** all the old complex configurations
5. **Single `combined.yaml`** per service/app
6. **Direct ArgoCD references** to specific files

## Next Steps

1. Consider archiving old unused k8s configurations
2. Document which paths are deprecated
3. Continue using the simplified structure
4. Add new services under `k8s/apps/<service-name>/combined.yaml`
