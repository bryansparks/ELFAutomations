# AgentGateway Configuration Plan

## Overview

This document outlines a comprehensive plan for configuring AgentGateway in the ElfAutomations system, covering both MCP management and potential A2A (Agent-to-Agent) protocol integration.

## Current State Analysis

### 1. AgentGateway Deployment
- **Location**: Running in `virtual-ai-platform` namespace
- **Current Config**: Minimal - only includes `@modelcontextprotocol/server-everything`
- **Endpoints**:
  - MCP Protocol: Port 3000 (SSE)
  - Admin UI: Port 8080
  - Metrics: Port 9090

### 2. Existing MCP Servers
Found but not all configured in AgentGateway:
- **supabase** (external npm package) ✓
- **team-registry** (TypeScript) ✓
- **business-tools** (Python) ✓
- **google-drive-watcher** (TypeScript) ✗
- **project-management** (TypeScript) ✗
- **memory-learning** (TypeScript) ✗
- **supabase** (internal TypeScript) ✗

### 3. A2A Architecture
- Each team runs its own A2A server (ports 8090, 8092, 8093)
- EventQueues for asynchronous message handling
- Direct peer-to-peer communication between teams
- Google's A2A protocol implementation

## Phase 1: Enhanced MCP Configuration

### 1.1 Complete MCP Server Registration

Create a comprehensive AgentGateway configuration that includes all MCP servers:

```json
{
  "type": "hybrid",
  "listeners": [
    {
      "name": "sse",
      "protocol": "MCP",
      "sse": {
        "address": "[::]",
        "port": 3000
      }
    },
    {
      "name": "admin",
      "protocol": "HTTP",
      "http": {
        "address": "[::]",
        "port": 8080
      }
    }
  ],
  "discovery": {
    "static": {
      "enabled": true,
      "configFile": "/config/static-mcps.json"
    },
    "kubernetes": {
      "enabled": true,
      "namespace": "elf-mcps",
      "labelSelector": "agentgateway.elfautomations.com/register=true"
    },
    "dynamic": {
      "enabled": true,
      "apiEndpoint": "/api/v1/mcps/register"
    }
  },
  "targets": {
    "mcp": [
      {
        "name": "supabase",
        "protocol": "stdio",
        "stdio": {
          "cmd": "npx",
          "args": ["-y", "@modelcontextprotocol/server-supabase"],
          "env": {
            "SUPABASE_URL": "${SUPABASE_URL}",
            "SUPABASE_ANON_KEY": "${SUPABASE_ANON_KEY}"
          }
        },
        "healthCheck": {
          "enabled": true,
          "interval": "30s",
          "timeout": "10s"
        }
      },
      {
        "name": "team-registry",
        "protocol": "stdio",
        "stdio": {
          "cmd": "node",
          "args": ["dist/server.js"],
          "cwd": "/mcp/typescript/servers/team-registry"
        }
      },
      {
        "name": "business-tools",
        "protocol": "stdio",
        "stdio": {
          "cmd": "python",
          "args": ["-m", "business_tools"],
          "cwd": "/mcp/python"
        }
      },
      {
        "name": "google-drive-watcher",
        "protocol": "stdio",
        "stdio": {
          "cmd": "node",
          "args": ["dist/index.js"],
          "cwd": "/mcps/google-drive-watcher"
        },
        "capabilities": {
          "authentication": "oauth2",
          "streaming": true
        }
      },
      {
        "name": "project-management",
        "protocol": "stdio",
        "stdio": {
          "cmd": "node",
          "args": ["dist/server.js"],
          "cwd": "/mcp/typescript/servers/project-management"
        }
      },
      {
        "name": "memory-learning",
        "protocol": "stdio",
        "stdio": {
          "cmd": "node",
          "args": ["dist/server.js"],
          "cwd": "/mcp/typescript/servers/memory-learning"
        }
      }
    ]
  },
  "routing": {
    "defaultPolicy": "allow",
    "rules": [
      {
        "source": "teams/*",
        "target": "mcp/*",
        "action": "allow"
      },
      {
        "source": "external/*",
        "target": "mcp/supabase",
        "action": "deny"
      }
    ]
  },
  "monitoring": {
    "metrics": {
      "enabled": true,
      "port": 9090,
      "path": "/metrics"
    },
    "tracing": {
      "enabled": true,
      "exporter": "otlp",
      "endpoint": "http://jaeger:4317"
    },
    "logging": {
      "level": "info",
      "format": "json",
      "outputs": ["stdout", "file"]
    }
  }
}
```

### 1.2 Security & Access Control

Add comprehensive security configuration:

```yaml
security:
  authentication:
    enabled: true
    providers:
      - type: "bearer"
        validation:
          endpoint: "http://auth-service/validate"
      - type: "mtls"
        caFile: "/certs/ca.crt"
  
  authorization:
    enabled: true
    policies:
      - name: "team-access"
        subjects: ["team:*"]
        resources: ["mcp:*"]
        actions: ["call"]
      - name: "admin-access"
        subjects: ["role:admin"]
        resources: ["*"]
        actions: ["*"]
  
  rateLimiting:
    enabled: true
    default: "100/minute"
    overrides:
      - subject: "team:executive"
        limit: "1000/minute"
      - resource: "mcp:supabase"
        limit: "50/minute"
```

## Phase 2: A2A Protocol Integration

### 2.1 AgentGateway as A2A Router

Extend AgentGateway to manage inter-team A2A communication:

```json
{
  "protocols": {
    "mcp": {
      "listeners": [/* existing MCP config */]
    },
    "a2a": {
      "enabled": true,
      "listeners": [
        {
          "name": "a2a-gateway",
          "protocol": "HTTP",
          "http": {
            "address": "[::]",
            "port": 8000
          }
        }
      ],
      "routing": {
        "mode": "intelligent",
        "discovery": {
          "wellKnown": true,
          "registry": "http://team-registry:8080",
          "cache": {
            "ttl": "5m"
          }
        }
      }
    }
  }
}
```

### 2.2 A2A Benefits Through AgentGateway

1. **Centralized Monitoring**
   - Track all inter-team communications
   - Message flow visualization
   - Performance metrics per team interaction

2. **Access Control**
   - Team-to-team communication policies
   - Rate limiting between teams
   - Audit logging of all interactions

3. **Message Enhancement**
   - Automatic correlation IDs
   - Request/response tracing
   - Error handling and retry logic

4. **Load Balancing**
   - Distribute requests across team replicas
   - Circuit breaking for failed teams
   - Graceful degradation

### 2.3 A2A Integration Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Marketing     │────▶│   AgentGateway   │────▶│     Sales       │
│     Team        │     │  (A2A Router)    │     │     Team        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ├── Discovery
                               ├── Routing
                               ├── Auth/Authz
                               ├── Monitoring
                               └── Load Balancing
```

## Phase 3: Implementation Steps

### 3.1 Immediate Actions (MCP Configuration)

1. **Update AgentGateway ConfigMap**
   ```bash
   # Create enhanced configuration
   cat > /config/agentgateway/config-enhanced.json << EOF
   {/* enhanced config from above */}
   EOF
   
   # Update kustomization
   cd k8s/base/agentgateway
   # Edit kustomization.yaml to use config-enhanced.json
   ```

2. **Deploy Missing MCPs**
   ```bash
   # Deploy google-drive-watcher
   cd mcps/google-drive-watcher
   docker build -t elf-automations/google-drive-watcher:latest .
   kubectl apply -k k8s/
   ```

3. **Test MCP Discovery**
   ```bash
   # List all discovered MCPs
   python scripts/register_mcp_dynamic.py list
   
   # Test each MCP
   python scripts/test_mcp_connectivity.py --all
   ```

### 3.2 A2A Integration (Next Phase)

1. **Extend AgentGateway**
   - Fork AgentGateway repository
   - Add A2A protocol support
   - Implement team discovery via well-known URIs

2. **Update Team Templates**
   - Modify team factory to register with AgentGateway
   - Add A2A client configuration for gateway routing
   - Update logging to include gateway metadata

3. **Create A2A Policies**
   - Define team communication rules
   - Set up rate limits per team pair
   - Configure monitoring dashboards

## Phase 4: Monitoring & Observability

### 4.1 Metrics to Track

**MCP Metrics:**
- Tool call count by MCP
- Response times per tool
- Error rates by MCP
- Active connections

**A2A Metrics:**
- Inter-team message count
- Message latency by team pair
- Error rates between teams
- Queue depths per team

### 4.2 Dashboards

Create Grafana dashboards for:
1. MCP Performance Overview
2. Team Communication Matrix
3. Error Analysis Dashboard
4. Resource Usage by Component

## Benefits Summary

### For MCP Management
- ✅ Centralized configuration and discovery
- ✅ Unified access control and rate limiting
- ✅ Comprehensive monitoring and metrics
- ✅ Dynamic MCP registration without restarts

### For A2A Communication
- ✅ Centralized routing and load balancing
- ✅ Communication policies and governance
- ✅ End-to-end message tracing
- ✅ Resilience through circuit breaking

## Next Steps

1. **Immediate** (Week 1):
   - Update AgentGateway configuration with all MCPs
   - Deploy missing MCP servers
   - Test end-to-end MCP access through gateway

2. **Short-term** (Week 2-3):
   - Design A2A integration architecture
   - Create proof-of-concept A2A routing
   - Test with executive team communications

3. **Medium-term** (Month 2):
   - Full A2A integration deployment
   - Comprehensive monitoring setup
   - Performance optimization

## Conclusion

AgentGateway can serve as a powerful central hub for both MCP management and A2A communication in the ElfAutomations system. The phased approach allows immediate improvements to MCP configuration while planning for sophisticated inter-team communication management.