# AgentGateway Remote Access Guide

## Overview
AgentGateway's admin UI runs on the deployment machine (Mac Mini with OrbStack at 192.168.6.5), but you need to access it from your development MacBook. This guide provides multiple solutions.

## Available Ports
- **8080**: Admin UI (management, metrics, access control)
- **3000**: MCP Protocol endpoint (for agents)
- **9090**: Prometheus metrics endpoint

## Access Methods

### 1. SSH Tunnel (Quickest)
For immediate access without any configuration:

```bash
# On your development MacBook
ssh -L 8080:localhost:8080 bryan@192.168.6.5 \
  "kubectl port-forward service/agentgateway-service 8080:8080 -n virtual-ai-platform"

# Access at: http://localhost:8080
```

### 2. Persistent SSH Config
Add to `~/.ssh/config` for easy repeated access:

```
Host agentgateway
    HostName 192.168.6.5
    User bryan
    LocalForward 8080 localhost:8080
    LocalForward 9090 localhost:9090
    RemoteCommand kubectl port-forward service/agentgateway-service 8080:8080 -n virtual-ai-platform & kubectl port-forward service/agentgateway-metrics 9090:9090 -n virtual-ai-platform; bash
    RequestTTY yes
```

Then simply: `ssh agentgateway`

### 3. Kubernetes Ingress (GitOps-Managed)
For production-ready access with proper DNS:

1. Apply the ingress configuration:
   ```bash
   git add k8s/base/agentgateway/ingress.yaml
   git commit -m "Add AgentGateway ingress for remote UI access"
   git push
   ```

2. Add to `/etc/hosts` on your development machine:
   ```
   192.168.6.5 agentgateway.elf.local
   192.168.6.5 agentgateway-metrics.elf.local
   ```

3. Access:
   - Admin UI: http://agentgateway.elf.local
   - Metrics: http://agentgateway-metrics.elf.local
   - Default auth: admin / agentgateway

### 4. Remote kubectl (Advanced)
If you copy the kubeconfig from the Mac Mini:

```bash
# On Mac Mini
kubectl config view --raw > kubeconfig.yaml

# On development machine
export KUBECONFIG=~/kubeconfig.yaml
kubectl port-forward service/agentgateway-service 8080:8080 -n virtual-ai-platform
```

## What You Can Do in the UI

### Access Control Management
- View and modify RBAC policies
- Create API keys for teams
- Set rate limits per team
- Configure allowed MCP servers per team

### Metrics & Analytics
- Request/response metrics per team
- MCP server health status
- Performance analytics
- Error tracking and debugging

### MCP Server Management
- Register new MCP servers
- Update server configurations
- View server health status
- Test MCP connections

### Credential Management
- Configure secure credential storage
- Set environment variables for MCPs
- Manage credential rotation

## Security Considerations

1. **Authentication**: The UI requires bearer token authentication
2. **Basic Auth**: Ingress adds HTTP basic auth layer
3. **Network**: Consider VPN for production access
4. **Audit**: All changes are logged

## Automation Script

Use the provided setup script for guided configuration:

```bash
./scripts/setup_agentgateway_remote_access.sh
```

Options:
1. SSH Tunnel setup
2. Direct kubectl (if configured)
3. Ingress deployment
4. SSH config creation

## Best Practices

1. **Development**: Use SSH tunnel for quick access
2. **Testing**: Use ingress with hosts file
3. **Production**: Use proper DNS with HTTPS/TLS
4. **GitOps**: Commit ingress changes for persistence

## Troubleshooting

### Can't connect via SSH tunnel
- Verify SSH access: `ssh bryan@192.168.6.5`
- Check pod status: `kubectl get pods -n virtual-ai-platform`

### Ingress not working
- Verify ingress controller: `kubectl get pods -n ingress-nginx`
- Check ingress status: `kubectl describe ingress -n virtual-ai-platform`

### UI shows authentication error
- AgentGateway uses bearer tokens
- Check configmap for authentication settings
- Verify credentials in environment

## Integration with GitOps

Since your AgentGateway runs on the deployment machine:

1. **Configuration changes** made in UI are persisted to ConfigMaps
2. **Export configurations** from UI and commit to Git
3. **ArgoCD** will sync changes automatically
4. **Metrics/Analytics** are real-time from production

This approach gives you full management capabilities while maintaining GitOps principles.
