# K8s Structure Fix Summary

## Problem
There is a nested directory structure at `infrastructure/k8s/k8s/` that needs to be fixed.

## Solution
Move all contents from `infrastructure/k8s/k8s/` up one level to `infrastructure/k8s/`.

## Directories to be moved:

### Data Stores
- `data-stores/qdrant/` - Contains Qdrant vector database deployment files

### Infrastructure Components
- `infrastructure/neo4j/` - Neo4j graph database deployment
- `infrastructure/minio/` - MinIO object storage deployment

### Core Components
- `agentgateway/` - Agent Gateway deployment
- `agents/` - Agent deployments
- `apps/` - Application deployments (includes n8n)
- `argocd-apps/` - ArgoCD application definitions
- `base/` - Base Kubernetes configurations
- `kagent/` - Kagent-related deployments
- `mcps/` - MCP server deployments
- `n8n/` - n8n workflow automation deployment
- `operators/` - Kubernetes operators
- `overlays/` - Kustomize overlays
- `production/` - Production-specific configurations
- `staging/` - Staging-specific configurations
- `teams/` - Team deployments

## Final Structure
After the fix, the structure will be:
```
infrastructure/k8s/
├── agentgateway/
├── agents/
├── apps/
├── argocd-apps/
├── base/
├── data-stores/
│   └── qdrant/
├── infrastructure/
│   ├── minio/
│   └── neo4j/
├── kagent/
├── mcps/
├── n8n/
├── operators/
├── overlays/
├── production/
├── staging/
└── teams/
```

## How to execute the fix

1. Make the script executable:
   ```bash
   chmod +x /Users/bryansparks/projects/ELFAutomations/FIX_NESTED_K8S.sh
   ```

2. Run the script:
   ```bash
   /Users/bryansparks/projects/ELFAutomations/FIX_NESTED_K8S.sh
   ```

The script will:
- Move all directories from `infrastructure/k8s/k8s/` to `infrastructure/k8s/`
- Remove the empty `k8s` directory
- Display the final structure
