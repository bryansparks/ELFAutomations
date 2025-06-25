# Telemetry and Registry Guide

## Overview

This guide explains the lightweight telemetry and unified registry system for ElfAutomations. The system provides:

1. **Unified Telemetry**: Fire-and-forget logging for MCP, A2A, and N8N communications
2. **Unified Registry**: Single source of truth for all entities (Teams, MCPs, Workflows)
3. **State Tracking**: Current state and health of all registered entities

## Architecture

### Telemetry Flow
```
Teams/MCPs/Workflows
        ↓ (fire-and-forget)
Communication Telemetry
        ↓
    Supabase
        ↓
  Control Center UI
```

### Registry Structure
```
Unified Registry
├── Teams (from team factory)
├── MCP Servers (from MCP factory)
├── N8N Workflows (from webhook events)
└── Other Services (future)
```

## Setup

### 1. Run Setup Script
```bash
cd scripts
python setup_telemetry_and_registry.py
```

This creates:
- `communication_telemetry` table
- `unified_registry` table
- Supporting views and functions

### 2. Environment Variables
Ensure these are set:
```bash
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
```

## Integration Guide

### A2A Teams - Telemetry Integration

#### Option 1: Use Enhanced Client (Recommended)
```python
from elf_automations.shared.a2a.telemetry_client import create_a2a_client

# Creates client with telemetry enabled by default
client = create_a2a_client(
    team_id="marketing-team",
    enable_telemetry=True  # Default
)

# All operations are automatically tracked
result = await client.send_task(
    target_team="sales-team",
    task_description="Generate proposal"
)
```

#### Option 2: Minimal Changes to Existing Code
If teams already use the standard A2A client, just update the import:

```python
# Old:
from elf_automations.shared.a2a.client import A2AClient

# New:
from elf_automations.shared.a2a.telemetry_client import A2AClientWithTelemetry as A2AClient
```

### AgentGateway - MCP Telemetry

Add telemetry to AgentGateway's MCP handlers:

```python
from elf_automations.shared.telemetry import telemetry_client

# In your MCP handler
async def handle_mcp_request(request):
    start_time = telemetry_client.start_timer()
    
    try:
        # Existing MCP logic...
        result = await call_mcp_tool(...)
        
        # Record success
        await telemetry_client.record_mcp(
            source_id=request.team_id,
            mcp_name=request.mcp_server,
            tool_name=request.tool,
            status="success",
            duration_ms=telemetry_client.calculate_duration_ms(start_time),
            tokens_used=result.get("tokens_used"),
            correlation_id=request.correlation_id
        )
        
        return result
        
    except Exception as e:
        # Record error
        await telemetry_client.record_mcp(
            source_id=request.team_id,
            mcp_name=request.mcp_server,
            tool_name=request.tool,
            status="error",
            duration_ms=telemetry_client.calculate_duration_ms(start_time),
            error_message=str(e),
            correlation_id=request.correlation_id
        )
        raise
```

### N8N Workflow Registration

#### Manual Registration
```python
from n8n.workflow_registration import N8NWorkflowRegistry

registry = N8NWorkflowRegistry()

# Register a workflow
registry.register_workflow(
    workflow_id="wf_001",
    workflow_name="Customer Onboarding",
    description="Automated customer onboarding process",
    tags=["customer", "automation"],
    nodes=[
        {"type": "webhook", "name": "Start"},
        {"type": "http", "name": "Create Account"},
        {"type": "email", "name": "Send Welcome"}
    ]
)

# Update workflow state
registry.update_workflow_state(
    workflow_id="wf_001",
    state="active",
    health_status="healthy"
)
```

#### Webhook Auto-Registration
Set up an N8N webhook to auto-register workflows:

```python
from n8n.workflow_registration import N8NWorkflowRegistry, N8NWebhookHandler

registry = N8NWorkflowRegistry()
handler = N8NWebhookHandler(registry)

# In your webhook endpoint
@app.post("/n8n/webhook")
async def handle_n8n_event(event: dict):
    result = await handler.handle_workflow_event(event)
    return result
```

### Entity Registration

Register any entity in the unified registry:

```python
# Using SQL function
await supabase.rpc("register_entity", {
    "p_entity_id": "my-service-001",
    "p_entity_type": "service",
    "p_entity_name": "My Custom Service",
    "p_registered_by": "manual",
    "p_capabilities": ["data-processing", "api-access"],
    "p_endpoint_url": "http://my-service:8080"
}).execute()

# Update state
await supabase.rpc("update_entity_state", {
    "p_entity_id": "my-service-001",
    "p_entity_type": "service",
    "p_new_state": "active",
    "p_health_status": "healthy"
}).execute()
```

## Telemetry Queries

### Real-time Communication Metrics
```sql
-- Last 5 minutes of activity
SELECT * FROM system_health_overview;

-- Communication patterns
SELECT * FROM communication_patterns
ORDER BY total_calls DESC;

-- Top communication pairs
SELECT * FROM top_communication_pairs;
```

### Entity State Overview
```sql
-- System state summary
SELECT * FROM system_entity_state;

-- Entity hierarchy
SELECT * FROM entity_hierarchy;

-- Registration gaps
SELECT * FROM check_registration_gaps();
```

### Custom Queries for Control Center

#### Communication Matrix
```sql
SELECT 
    source_id,
    target_id,
    protocol,
    COUNT(*) as calls,
    AVG(duration_ms) as avg_ms,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors
FROM communication_telemetry
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY source_id, target_id, protocol;
```

#### Entity Health Dashboard
```sql
SELECT 
    entity_type,
    entity_name,
    current_state,
    health_status,
    last_activity,
    EXTRACT(EPOCH FROM (NOW() - last_activity)) as seconds_since_activity
FROM unified_registry
WHERE current_state != 'deleted'
ORDER BY health_status, last_activity DESC;
```

## Best Practices

### 1. Telemetry
- **Fire and Forget**: Never let telemetry errors break your application
- **Lightweight**: Only track essential metrics
- **Correlation IDs**: Use for tracing related operations

### 2. Registration
- **Auto-Register**: Use factories and webhooks when possible
- **State Updates**: Keep entity states current
- **Health Checks**: Regular health status updates

### 3. Performance
- **Batch Operations**: Group telemetry writes when possible
- **Materialized Views**: Use for dashboard queries
- **Indexes**: Already created on key columns

## Monitoring

### Key Metrics to Track
1. **Request Volume**: Calls per minute by protocol
2. **Error Rates**: Percentage of failed operations
3. **Latency**: P50, P95, P99 response times
4. **Entity Health**: Percentage of healthy entities

### Alerts to Configure
1. Error rate > 5% for any protocol
2. No activity from an entity for > 1 hour
3. Average latency > 1000ms
4. Entity in unhealthy state for > 10 minutes

## Troubleshooting

### No Telemetry Data
1. Check Supabase credentials are set
2. Verify telemetry is enabled in client
3. Check Supabase logs for errors

### Missing Entities
1. Run `check_registration_gaps()` function
2. Verify factories are using registration
3. Check webhook integration for N8N

### Performance Issues
1. Refresh materialized views regularly
2. Use time-based queries (last hour, day)
3. Consider archiving old telemetry

## Future Enhancements

1. **Grafana Dashboards**: Pre-built dashboards for common views
2. **Anomaly Detection**: ML-based unusual pattern detection
3. **Cost Attribution**: Link telemetry to cost monitoring
4. **SLA Tracking**: Service level agreement monitoring