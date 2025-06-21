# Google Drive MCP - AgentGateway Integration

## Overview

The Google Drive MCP has been configured to follow ElfAutomations conventions for MCP creation and AgentGateway integration. All MCPs (internal and external) are accessed through AgentGateway for centralized management.

## Key Files Created/Updated

### 1. AgentGateway Configuration
- **`/mcps/google-drive-watcher/agentgateway-config.json`** - Defines MCP metadata, tools, and categories
- **`/mcps/google-drive-watcher/manifest.yaml`** - Kubernetes-style manifest for MCP registration
- **`/config/agentgateway/mcp-config-with-google-drive.json`** - Updated AgentGateway config including Google Drive MCP

### 2. Kubernetes Manifests
- **`/mcps/google-drive-watcher/k8s/deployment.yaml`** - Main deployment with ConfigMap mount
- **`/mcps/google-drive-watcher/k8s/service.yaml`** - ClusterIP service
- **`/mcps/google-drive-watcher/k8s/configmap.yaml`** - AgentGateway registration config with label

### 3. Key Updates
- Added `agentgateway.elfautomations.com/register: "true"` label to ConfigMap
- Mounted agentgateway-config.json in the deployment
- Split monolithic deployment.yaml into separate files for GitOps
- Added tool categories and rate limiting configuration

## AgentGateway Integration Points

### 1. Discovery
The MCP is discoverable through:
- **ConfigMap Label**: `agentgateway.elfautomations.com/register: "true"`
- **Namespace**: `elf-mcps`
- **Protocol**: stdio (via Node.js)

### 2. Tool Categories
Tools are organized into logical categories:
- **authentication** - OAuth management
- **folder-management** - Watch folder operations
- **document-operations** - File operations
- **rag-integration** - RAG pipeline integration
- **monitoring** - Change detection

### 3. Health Checking
- Uses `list_watch_folders` tool for health checks
- 30-second intervals with 5-second timeout
- Integrated with Kubernetes probes

### 4. Rate Limiting
- Authentication: 10 requests/hour
- Document operations: 100 requests/minute
- Prevents API quota exhaustion

## Deployment via GitOps

### Updated Deployment Process
```bash
# 1. Build and tag image
cd mcps/google-drive-watcher
docker build -t elf-automations/google-drive-watcher:latest .

# 2. Transfer to ArgoCD machine
./scripts/deploy_google_drive_mcp_gitops.sh

# 3. Commit GitOps changes
cd gitops
git add .
git commit -m "Deploy Google Drive MCP with AgentGateway integration"
git push origin main
```

### Post-Deployment Verification
```bash
# Check AgentGateway registration
kubectl logs -n elf-automations deployment/agentgateway | grep google-drive

# Verify ConfigMap
kubectl get configmap -n elf-mcps google-drive-watcher-config -o yaml

# Test via AgentGateway
curl -X POST http://agentgateway:3000/mcp/google-drive-watcher/tools/list_watch_folders
```

## Using the MCP via AgentGateway

### Python Client Example
```python
from elf_automations.shared.mcp import MCPClient

# Client automatically routes through AgentGateway
client = MCPClient()

# Authenticate
auth_url = await client.call_tool(
    "google-drive-watcher",
    "get_auth_url"
)

# Add watch folder
result = await client.call_tool(
    "google-drive-watcher",
    "add_watch_folder",
    {
        "folderId": "1abc123def456ghi",
        "tenantName": "acme_corp"
    }
)
```

### Direct AgentGateway API
```bash
# List available tools
curl http://agentgateway:8080/api/v1/mcps/google-drive-watcher/tools

# Execute tool
curl -X POST http://agentgateway:3000/mcp/google-drive-watcher/tools/start_monitoring \
  -H "Content-Type: application/json" \
  -d '{"intervalSeconds": 300}'
```

## Security Considerations

1. **Credential Injection**: AgentGateway injects credentials from environment/secrets
2. **RBAC**: Role-based access control for tool execution
3. **Rate Limiting**: Prevents abuse and API quota exhaustion
4. **Audit Logging**: All MCP calls are logged through AgentGateway

## Monitoring & Observability

1. **Prometheus Metrics**: Available at `:9090/metrics`
2. **Jaeger Tracing**: Distributed tracing for MCP calls
3. **Structured Logging**: JSON format for log aggregation

## Next Steps

1. Deploy via GitOps pipeline
2. Configure OAuth for each tenant
3. Set up monitoring dashboards
4. Create RAG processor team to handle queued documents

## Troubleshooting

### MCP Not Appearing in AgentGateway
1. Check ConfigMap has correct label
2. Verify namespace is correct
3. Check AgentGateway logs for discovery errors

### Tool Execution Failures
1. Verify credentials are injected
2. Check rate limiting hasn't been exceeded
3. Review AgentGateway logs for routing errors
