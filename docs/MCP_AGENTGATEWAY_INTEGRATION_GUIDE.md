# MCP AgentGateway Integration Guide

## Overview

This guide describes the complete integration between MCPs (Model Context Protocol servers) and AgentGateway in the ELF Automations system. The integration provides three key capabilities:

1. **Automatic Registration** - MCPs are automatically accessible through AgentGateway
2. **GitOps Integration** - All MCPs are deployed via GitOps with proper manifests
3. **Dynamic Registration** - MCPs can be added at runtime without redeployment

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│     Teams       │────▶│   AgentGateway   │────▶│      MCPs       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                           │
                               ▼                           ▼
                        ┌──────────────┐          ┌──────────────┐
                        │  Discovery   │          │  ConfigMaps  │
                        │   Sources    │          │  (labeled)   │
                        └──────────────┘          └──────────────┘
```

## MCP Creation with AgentGateway Integration

### Using Enhanced MCP Factory

The enhanced MCP factory automatically creates all necessary files for AgentGateway integration:

```bash
cd tools
python mcp_factory_enhanced.py
```

This creates:
- `mcps/{name}/manifest.yaml` - MCP metadata and specification
- `mcps/{name}/agentgateway-config.json` - Runtime configuration
- `mcps/{name}/k8s/configmap.yaml` - With registration label
- `mcps/{name}/k8s/deployment.yaml` - Kubernetes deployment
- `mcps/{name}/k8s/service.yaml` - Kubernetes service
- `mcps/{name}/Dockerfile` - Container definition

### Key Files Generated

#### 1. Manifest.yaml
```yaml
apiVersion: mcp.elfautomations.com/v1
kind: MCPServer
metadata:
  name: my-mcp
  namespace: elf-mcps
spec:
  displayName: "My MCP"
  protocol: stdio
  runtime:
    command: node
    args: ["dist/server.js"]
  tools:
    - name: query
      description: "Query data"
  healthCheck:
    enabled: true
    interval: 30s
```

#### 2. ConfigMap with Registration Label
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-mcp-config
  namespace: elf-mcps
  labels:
    agentgateway.elfautomations.com/register: "true"  # Critical label
data:
  agentgateway-config.json: |
    {
      "name": "my-mcp",
      "protocol": "stdio",
      "runtime": {...},
      "tools": [...]
    }
```

## Discovery Mechanisms

### 1. ConfigMap Label Discovery (Primary)
AgentGateway automatically discovers MCPs with the label:
```yaml
agentgateway.elfautomations.com/register: "true"
```

### 2. Static Configuration (Fallback)
MCPs can be added to AgentGateway's main ConfigMap:
```yaml
# k8s/base/agentgateway/configmap.yaml
targets:
  mcp:
    - name: my-mcp
      stdio:
        cmd: node
        args: ["dist/server.js"]
```

### 3. Dynamic API Registration (Runtime)
```bash
# Register MCP at runtime
python scripts/register_mcp_dynamic.py register --file mcps/my-mcp/manifest.yaml

# Or interactively
python scripts/register_mcp_dynamic.py register --interactive
```

## GitOps Deployment Flow

### 1. Build and Prepare
```bash
# Build Docker image
cd mcps/my-mcp
docker build -t elf-automations/my-mcp:latest .

# Prepare GitOps artifacts
cd ../..
python tools/prepare_gitops_artifacts_enhanced.py
```

### 2. Deploy via GitOps
```bash
# Commit and push
git add mcps/ gitops/
git commit -m "Add new MCP with AgentGateway integration"
git push

# ArgoCD will automatically:
# 1. Deploy the MCP to elf-mcps namespace
# 2. Create ConfigMap with registration label
# 3. AgentGateway discovers and registers the MCP
```

### 3. Verify Deployment
```bash
# Check MCP pod
kubectl get pods -n elf-mcps -l app=my-mcp

# Check AgentGateway logs
kubectl logs -n elf-automations deployment/agentgateway | grep my-mcp

# List registered MCPs
python scripts/register_mcp_dynamic.py list
```

## Using MCPs from Teams

### Python Client
```python
from elf_automations.shared.mcp import MCPClient

# Client automatically routes through AgentGateway
client = MCPClient(team_id="my-team")

# Call MCP tool
result = await client.call_tool(
    server="my-mcp",
    tool="query",
    arguments={"table": "users"}
)

# Or use convenience method
result = await client.my_mcp("query", table="users")
```

### Direct HTTP (for testing)
```bash
# Via AgentGateway
curl -X POST http://agentgateway:3000/mcp/my-mcp/tools/query \
  -H "Authorization: Bearer $TEAM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"table": "users"}'
```

## Dynamic Registration

### Register New MCP Without Deployment
```bash
# 1. Create registration file
cat > /tmp/new-mcp.json << EOF
{
  "name": "external-api",
  "protocol": "http",
  "runtime": {
    "url": "https://api.example.com/mcp"
  },
  "tools": [
    {
      "name": "search",
      "description": "Search external API"
    }
  ]
}
EOF

# 2. Register with AgentGateway
python scripts/register_mcp_dynamic.py register --file /tmp/new-mcp.json

# 3. MCP is immediately available
python -c "
from elf_automations.shared.mcp import MCPClient
client = MCPClient()
result = await client.call_tool('external-api', 'search', {'query': 'test'})
print(result)
"
```

### Unregister MCP
```bash
python scripts/register_mcp_dynamic.py unregister external-api
```

## Best Practices

### 1. Namespace Organization
- **Teams**: `elf-automations` namespace
- **MCPs**: `elf-mcps` namespace
- **AgentGateway**: `elf-automations` namespace

### 2. Naming Conventions
- MCP names: `kebab-case` (e.g., `document-processor`)
- Tool names: `snake_case` (e.g., `process_document`)
- ConfigMap: `{mcp-name}-config`

### 3. Security
- All MCP access goes through AgentGateway
- Teams authenticate with bearer tokens
- MCPs never exposed directly
- Credentials injected by AgentGateway

### 4. Health Checks
- Always define a health check tool
- Use lightweight operations
- 30-second intervals recommended

## Troubleshooting

### MCP Not Discovered
1. Check ConfigMap has label: `agentgateway.elfautomations.com/register=true`
2. Verify namespace is `elf-mcps`
3. Check AgentGateway logs: `kubectl logs -n elf-automations deployment/agentgateway`

### Registration Failed
1. Verify AgentGateway is running
2. Check authentication token
3. Validate MCP configuration JSON
4. Review AgentGateway API logs

### Tool Calls Failing
1. Check MCP pod is running
2. Verify health checks passing
3. Review MCP logs: `kubectl logs -n elf-mcps -l app=my-mcp`
4. Test with `register_mcp_dynamic.py test my-mcp`

## Advanced Features

### Rate Limiting
Configure in manifest.yaml:
```yaml
rateLimiting:
  enabled: true
  rules:
    - category: "data"
      rate: "100/minute"
    - category: "admin"
      rate: "10/hour"
```

### Tool Categories
Organize tools by function:
```yaml
categories:
  data:
    displayName: "Data Operations"
    tools: ["query", "insert", "update"]
  admin:
    displayName: "Administration"
    tools: ["configure", "reset"]
```

### Multi-Protocol Support
```yaml
# HTTP MCP
protocol: http
runtime:
  url: "http://my-service:8080"

# SSE MCP
protocol: sse
runtime:
  url: "http://streaming-service:8080/events"
```

## Migration Guide

### From Static to Dynamic MCPs
1. Extract MCP config from AgentGateway ConfigMap
2. Create manifest.yaml with metadata
3. Generate k8s manifests with registration label
4. Deploy via GitOps
5. Remove from static config

### From Direct Access to AgentGateway
1. Update client code to use MCPClient
2. Remove direct MCP URLs
3. Add authentication tokens
4. Update error handling for gateway responses

## Conclusion

The MCP-AgentGateway integration provides a robust, scalable, and secure way to manage MCP servers in the ELF Automations ecosystem. The combination of automatic discovery, GitOps deployment, and dynamic registration ensures maximum flexibility while maintaining security and governance.
