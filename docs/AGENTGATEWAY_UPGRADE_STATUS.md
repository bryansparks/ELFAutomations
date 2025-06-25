# AgentGateway Upgrade Status

## Completed Actions

### 1. Configuration Updates
- ✅ Updated `/k8s/base/agentgateway/kustomization.yaml` to use `mcp-config.json`
- ✅ Fixed team-registry path in `mcp-config.json` (was `/mcp-servers-ts`, now `/mcp/typescript/servers/team-registry/server.js`)
- ✅ Added google-drive-watcher to `mcp-config.json`

### 2. MCP Server Readiness Assessment
| MCP Server | Status | Notes |
|------------|--------|-------|
| supabase | ✅ Ready | External npm package |
| team-registry | ⚠️ Path Fixed | Path corrected in config |
| business-tools | ❌ Not Ready | No deployment infrastructure |
| google-drive-watcher | ✅ Ready | Full k8s manifests available |
| project-management | ❌ Not Ready | No Dockerfile or k8s manifests |
| memory-learning | ❌ Not Ready | No Dockerfile or k8s manifests |

### 3. Files Modified for GitOps
```bash
# Modified files to commit:
k8s/base/agentgateway/kustomization.yaml
config/agentgateway/mcp-config.json
```

## Next Steps for GitOps Deployment

### 1. Commit and Push Changes
```bash
git add k8s/base/agentgateway/kustomization.yaml
git add config/agentgateway/mcp-config.json
git commit -m "feat: Upgrade AgentGateway with enhanced MCP configuration

- Switch to mcp-config.json for enhanced features
- Add google-drive-watcher MCP server
- Fix team-registry path to correct location
- Enable health checks and observability"
git push
```

### 2. Deploy google-drive-watcher MCP
Since google-drive-watcher has full k8s manifests:
```bash
# Add to git for ArgoCD
git add mcps/google-drive-watcher/k8s/
git commit -m "feat: Add google-drive-watcher MCP deployment"
git push
```

### 3. Monitor ArgoCD Deployment
After pushing, ArgoCD will:
1. Update AgentGateway ConfigMap with new configuration
2. Restart AgentGateway pods to load new config
3. Deploy google-drive-watcher to `elf-mcps` namespace

## Docker Images Required

⚠️ **Important**: The following Docker images need to be built and transferred to the ArgoCD machine:

1. **google-drive-watcher**:
   ```bash
   cd mcps/google-drive-watcher
   docker build -t elf-automations/google-drive-watcher:latest .
   ```

2. **AgentGateway** (if custom image is used)

Use the transfer script after building:
```bash
./scripts/transfer-docker-images-ssh.sh
```

## Configuration Notes

### MCP Servers Currently Configured:
1. **supabase** - Supabase data access
2. **team-registry** - Team management (path fixed)
3. **business-tools** - Business operations (needs deployment work)
4. **google-drive-watcher** - Google Drive monitoring (ready to deploy)

### Features Enabled:
- Health checks (30s intervals)
- Prometheus metrics (port 9090)
- JSON logging
- Jaeger tracing
- RBAC with team roles
- Rate limiting (100/min default)

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| team-registry path incorrect | Path updated but needs testing |
| business-tools not deployable | Keep in config but may fail to start |
| Missing environment variables | Ensure secrets are configured in k8s |

## Future Work

### Phase 1: Fix Remaining MCPs
- Create proper deployment infrastructure for business-tools
- Build and containerize project-management and memory-learning

### Phase 2: A2A Integration
- Design A2A routing through AgentGateway
- Implement team discovery mechanisms
- Add inter-team communication policies

## Validation Steps (Post-Deployment)

Once ArgoCD deploys the changes:

1. Check AgentGateway logs for MCP loading
2. Verify google-drive-watcher pod starts in `elf-mcps` namespace
3. Test MCP connectivity through AgentGateway
4. Monitor metrics endpoint for MCP call statistics