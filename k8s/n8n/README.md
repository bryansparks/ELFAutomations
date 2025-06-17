# n8n Deployment for ElfAutomations

This directory contains the Kubernetes manifests for deploying n8n as part of the ElfAutomations Business Operating System.

## Overview

n8n serves as the automation layer in our three-layer architecture:
- **AI Teams**: Reasoning and strategy
- **MCPs**: Tools and data access
- **n8n**: Workflow automation and scheduling

## Prerequisites

1. K3s cluster with `elf-teams` namespace
2. PostgreSQL instance for n8n backend storage
3. NGINX Ingress Controller
4. DNS entry for `n8n.elf-automations.local`

## Configuration

### 1. Update Secrets

Before deploying, update the passwords in `secrets.yaml`:

```bash
# Generate secure passwords
echo -n "your-strong-password" | base64

# Edit secrets.yaml with the base64 values
vi secrets.yaml
```

### 2. Database Setup

Create the n8n database and user in PostgreSQL:

```sql
CREATE DATABASE n8n;
CREATE USER n8n_user WITH ENCRYPTED PASSWORD 'your-postgres-password';
GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n_user;
```

### 3. DNS Configuration

Add to your `/etc/hosts` or DNS server:
```
192.168.6.5  n8n.elf-automations.local
```

## Deployment

Deploy all resources using Kustomize:

```bash
# Deploy n8n
kubectl apply -k .

# Verify deployment
kubectl get pods -n elf-teams -l app=n8n
kubectl get pvc -n elf-teams -l app=n8n
kubectl get ingress -n elf-teams -l app=n8n
```

## Initial Setup

1. Access n8n at http://n8n.elf-automations.local
2. Login with username: `admin` and the password from secrets
3. Create initial workflows for:
   - Team health monitoring
   - Metric collection
   - Scheduled reports
   - Cross-team coordination

## Integration with ElfAutomations

### 1. Team Integration

Teams can trigger n8n workflows via the n8n-interface team:

```python
# Example: Trigger workflow from AI team
await a2a_client.send_task({
    "to": "n8n-interface-team",
    "task": "execute_workflow",
    "workflow_id": "customer_onboarding",
    "data": {
        "customer_id": "12345",
        "plan": "premium"
    }
})
```

### 2. MCP Integration

n8n can use MCPs for data access:
- Use HTTP Request nodes to call MCP endpoints
- Configure authentication in n8n credentials
- Access via AgentGateway for proper routing

### 3. Webhook Integration

n8n webhooks are accessible at:
```
http://n8n.elf-automations.local/webhook/[webhook-id]
```

## Monitoring

Check n8n health:
```bash
# Pod status
kubectl logs -n elf-teams -l app=n8n

# Storage usage
kubectl exec -n elf-teams -l app=n8n -- df -h

# Database connections
kubectl exec -n elf-teams -l app=n8n -- psql -U n8n_user -d n8n -c "SELECT count(*) FROM pg_stat_activity;"
```

## Troubleshooting

### Pod not starting
- Check secrets are properly configured
- Verify PostgreSQL is accessible
- Check PVC binding: `kubectl describe pvc -n elf-teams`

### Cannot access UI
- Verify ingress is configured: `kubectl get ingress -n elf-teams`
- Check DNS resolution: `nslookup n8n.elf-automations.local`
- Test service directly: `kubectl port-forward -n elf-teams svc/n8n 5678:5678`

### Workflow execution issues
- Check n8n logs: `kubectl logs -n elf-teams -l app=n8n`
- Verify resource limits aren't being hit
- Check database connectivity

## Backup and Recovery

### Backup workflows
```bash
# Export all workflows
kubectl exec -n elf-teams -l app=n8n -- n8n export:workflow --all --output=/tmp/workflows.json
kubectl cp elf-teams/$(kubectl get pod -n elf-teams -l app=n8n -o name | cut -d/ -f2):/tmp/workflows.json ./workflows-backup.json
```

### Backup database
```bash
# Backup n8n database
kubectl exec -n elf-teams postgres-pod -- pg_dump -U n8n_user n8n > n8n-backup.sql
```

## Next Steps

1. Create n8n-interface team for A2A communication
2. Import workflow templates from 1000+ examples
3. Set up workflow engineering team
4. Implement intelligent request routing
5. Create workflow pattern library

## Resources

- [n8n Documentation](https://docs.n8n.io)
- [ElfAutomations Layer Selection Framework](/docs/LAYER_SELECTION_FRAMEWORK.md)
- [Post-n8n Architecture](/docs/POST_N8N_ARCHITECTURE.md)