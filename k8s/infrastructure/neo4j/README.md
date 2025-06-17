# Neo4j GraphDB for ElfAutomations

This directory contains Kubernetes manifests for deploying Neo4j as the graph database for ElfAutomations' multi-tenant RAG system.

## Components

- **namespace.yaml**: Creates the `elf-infrastructure` namespace
- **secret.yaml**: Contains Neo4j credentials (⚠️ Change in production!)
- **configmap.yaml**: Neo4j configuration with multi-tenant support
- **persistent-volume-claim.yaml**: Storage for data and logs
- **deployment.yaml**: Neo4j deployment with resource limits
- **service.yaml**: ClusterIP and NodePort services for access
- **kustomization.yaml**: Kustomize configuration for easy deployment

## Deployment

### Quick Deploy
```bash
# From project root
./scripts/deploy_neo4j.sh

# Or manually
kubectl apply -k k8s/infrastructure/neo4j/
```

### Verify Deployment
```bash
# Check pods
kubectl get pods -n elf-infrastructure

# Check services
kubectl get svc -n elf-infrastructure

# View logs
kubectl logs -n elf-infrastructure deployment/neo4j
```

## Access

### From Outside Cluster (Development)
- Browser UI: `http://<node-ip>:30474`
- Bolt Connection: `bolt://<node-ip>:30687`
- Default credentials: `neo4j / elfautomations2025`

### From Inside Cluster
- Service DNS: `neo4j.elf-infrastructure.svc.cluster.local`
- Bolt port: 7687
- HTTP port: 7474

## Configuration

### Resource Limits
Currently configured for development:
- Memory: 2Gi request, 4Gi limit
- CPU: 1 core request, 2 core limit
- Heap: 2GB max
- Page Cache: 1GB

Adjust in `deployment.yaml` for production.

### Storage
- Data: 10Gi PVC
- Logs: 2Gi PVC
- Storage class: `local-path` (default for K3s)

## Multi-Tenant Features

Neo4j is configured with:
- Multi-database support enabled
- Label-based tenant isolation
- Full-text search enabled
- APOC procedures for advanced operations

## Testing

Test the deployment:
```bash
python scripts/test_neo4j_connection.py \
  --uri bolt://localhost:30687 \
  --username neo4j \
  --password elfautomations2025
```

## Security Notes

⚠️ **IMPORTANT**:
1. Change default password immediately in production
2. Update the secret.yaml with strong credentials
3. Consider using external secrets management
4. Enable SSL/TLS for Bolt connections in production

## Integration with RAG

Neo4j will be used for:
- Storing document relationships
- Entity graphs (people, organizations, concepts)
- Multi-tenant data isolation via labels
- Graph-based retrieval for RAG queries

## Troubleshooting

### Pod Won't Start
```bash
# Check events
kubectl describe pod -n elf-infrastructure -l app=neo4j

# Check PVC binding
kubectl get pvc -n elf-infrastructure
```

### Can't Connect
```bash
# Check service endpoints
kubectl get endpoints -n elf-infrastructure neo4j

# Test from inside cluster
kubectl run -it --rm debug --image=neo4j:5.15 --restart=Never -- cypher-shell -a bolt://neo4j:7687
```

### Performance Issues
- Increase heap size in deployment.yaml
- Add more CPU/memory resources
- Check disk I/O on the node

## Next Steps

1. Deploy using `./scripts/deploy_neo4j.sh`
2. Verify with `./scripts/test_neo4j_connection.py`
3. Create GraphDB MCP using `python tools/mcp_factory.py`
4. Integrate with RAG team for document processing
