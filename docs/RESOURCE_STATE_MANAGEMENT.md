# Resource State Management System

## Overview

The Resource State Management System provides unified lifecycle tracking for all ElfAutomations resources: N8N workflows, MCP servers/clients, and Teams. It addresses the challenge of tracking resources through their transient states from creation to production deployment.

## Key Concepts

### Resource States

Every resource progresses through a defined set of states:

1. **Created** - Resource exists in codebase but not registered in system
2. **Registered** - Resource is known to the system (in Supabase)
3. **Building** - Docker image or deployment artifact being created
4. **Built** - Build artifacts ready
5. **Deploying** - Being deployed to Kubernetes
6. **Deployed** - Running in K8s but not yet active
7. **Active** - Fully operational and callable
8. **Inactive** - Deployed but disabled
9. **Failed** - Deployment or validation failed
10. **Archived** - Retained for history but not deployable

### Resource-Specific States

#### N8N Workflows
- **validating** - Workflow being validated for API keys, node compatibility
- **validated** - Passed all validation checks
- **failed_validation** - Validation failed

#### MCP Servers
- **health_checking** - Running health checks
- **available** - Health checks passed, ready for connections

#### Teams
- **awaiting_dependencies** - Waiting for required resources
- **scaling** - Scaling operations in progress

## Architecture

### Database Schema

```sql
-- Core Tables
resource_states         -- Current state of each resource
state_transitions      -- History of all state changes
mcp_registry          -- Registry of MCP servers and clients
deployment_requirements -- Requirements before activation

-- Views
resource_state_overview     -- Summary by type and state
resources_awaiting_action   -- Resources needing attention
mcp_deployment_status      -- MCP-specific deployment view
workflow_deployment_pipeline -- Workflow-specific view
```

### State Management Framework

Located in `/elf_automations/shared/state_manager/`:

```python
# Core components
StateMachine           # Generic state machine implementation
ResourceStateManager   # Base class for resource managers
WorkflowStateManager   # N8N workflow state management
MCPStateManager       # MCP server/client management
TeamStateManager      # Team state management
StateTracker          # Query and monitoring utilities
```

### Control Center UI

The Resources page (`http://localhost:3003/resources`) provides:

- **Overview Cards** - Summary by resource type
- **Awaiting Action** - Resources requiring intervention
- **Resource List** - Searchable/filterable list with state badges
- **State History** - View transition history for any resource

## Usage Examples

### 1. Workflow Lifecycle

```python
from elf_automations.shared.state_manager import WorkflowStateManager
from supabase import create_client

# Initialize
supabase = create_client(url, key)
workflow_mgr = WorkflowStateManager(supabase)

# Register a new workflow
success, error = workflow_mgr.register_workflow(
    workflow_id="uuid-here",
    workflow_name="Email Parser",
    owner_team="marketing-team",
    transitioned_by="user@example.com"
)

# Start validation
success, error = workflow_mgr.start_validation(
    workflow_id="uuid-here",
    workflow_name="Email Parser",
    validator="validation-service"
)

# Complete validation
success, error = workflow_mgr.complete_validation(
    workflow_id="uuid-here",
    workflow_name="Email Parser",
    success=True,
    validation_report={"errors": [], "warnings": []},
    validator="validation-service"
)

# Deploy to N8N
success, error = workflow_mgr.deploy_workflow(
    workflow_id="uuid-here",
    workflow_name="Email Parser",
    n8n_id="n8n-workflow-id",
    deployer="deployment-service"
)

# Activate
success, error = workflow_mgr.activate_workflow(
    workflow_id="uuid-here",
    workflow_name="Email Parser",
    activator="admin@example.com"
)
```

### 2. MCP Server Lifecycle

```python
from elf_automations.shared.state_manager import MCPStateManager

mcp_mgr = MCPStateManager(supabase)

# Register MCP
success, error = mcp_mgr.register_mcp(
    mcp_id="uuid-here",
    mcp_name="team-registry",
    mcp_type="server",
    category="data-access",
    registrar="mcp-factory"
)

# Build Docker image
success, error = mcp_mgr.build_image(
    mcp_id="uuid-here",
    mcp_name="team-registry",
    builder="ci-system"
)

# Complete build
success, error = mcp_mgr.complete_build(
    mcp_id="uuid-here",
    mcp_name="team-registry",
    success=True,
    image_tag="team-registry:v1.0",
    builder="ci-system"
)

# Health check
success, error = mcp_mgr.health_check(
    mcp_id="uuid-here",
    mcp_name="team-registry",
    checker="k8s-operator"
)
```

### 3. Querying Resource States

```python
from elf_automations.shared.state_manager import StateTracker

tracker = StateTracker(supabase)

# Get overview
overview = tracker.get_resource_overview()
# Returns: {'workflow': {'active': 5, 'deployed': 3}, 'mcp_server': {...}}

# Get resources awaiting action
awaiting = tracker.get_resources_awaiting_action()
# Returns list of resources in states like 'created', 'failed', etc.

# Get failed resources
failed = tracker.get_failed_resources()

# Get specific resource details
details = tracker.get_resource_details('workflow', 'workflow-uuid')

# Search resources
results = tracker.search_resources(
    query="email",
    resource_type="workflow",
    states=["active", "deployed"]
)

# Get deployment readiness
readiness = tracker.get_deployment_readiness()
# Shows resources ready to move to next stage
```

## State Transitions

### Workflow State Machine

```
created → registered → validating → validated → deploying → deployed → active
                          ↓                                      ↓         ↓
                   failed_validation                          inactive  archived
```

### MCP State Machine

```
created → registered → building → built → deploying → deployed → health_checking → available → active
                          ↓                    ↓                        ↓                           ↓
                        failed              failed                   failed                    inactive
```

### Team State Machine

```
created → registered → building → built → deploying → deployed → active
                                                           ↓         ↓
                                              awaiting_dependencies  scaling
```

## API Endpoints

### GET /api/resources
Get all resources with optional filters:
- `?type=workflow|mcp_server|team`
- `?state=active|deployed|failed`
- `?search=keyword`

### GET /api/resources/overview
Get summary counts by resource type and state

### GET /api/resources/awaiting-action
Get resources that need attention (failed, awaiting dependencies, etc.)

### GET /api/resources/[id]/transitions
Get state transition history for a specific resource

### POST /api/resources/[id]/transition
Trigger a state transition (requires appropriate permissions)

## Deployment Requirements

Resources can have requirements that must be satisfied before activation:

```python
# Add a requirement
workflow_mgr.add_deployment_requirement(
    resource_id="workflow-uuid",
    requirement_type="credential",
    requirement_name="OPENAI_API_KEY",
    details={"description": "OpenAI API key for LLM calls"}
)

# Update requirement status
workflow_mgr.update_requirement_status(
    resource_id="workflow-uuid",
    requirement_name="OPENAI_API_KEY",
    status="satisfied",
    details={"verified_at": "2024-01-20T10:00:00Z"}
)

# Check all requirements
req_status = workflow_mgr.check_deployment_requirements("workflow-uuid")
# Returns: {
#   "all_satisfied": false,
#   "pending_count": 2,
#   "failed_count": 0,
#   "requirements": [...]
# }
```

## Integration Points

### 1. Team Factory
When creating teams, automatically register them:
```python
# In team_factory.py
team_mgr.register_team(team_id, team_name, department, framework, "team-factory")
```

### 2. MCP Factory
Register MCPs during creation:
```python
# In mcp_factory.py
mcp_mgr.register_mcp(mcp_id, mcp_name, "server", category, "mcp-factory")
```

### 3. Workflow Import
Track imported workflows:
```python
# In workflow import API
workflow_mgr.register_workflow(workflow.id, workflow.name, owner_team, "import-api")
```

### 4. GitOps Pipeline
Update states during deployment:
```python
# In deployment scripts
if deployment_successful:
    resource_mgr.transition_state(id, name, "deployed", "Deployment complete", "gitops")
```

### 5. K8s Operator (Future)
Sync K8s deployment status back to Supabase:
```python
# In K8s operator
if pod.status.phase == "Running":
    resource_mgr.transition_state(id, name, "active", "Pod running", "k8s-operator")
```

## Best Practices

1. **Always provide meaningful transition reasons** - These appear in the UI and help with debugging

2. **Use appropriate transitioned_by values** - Use service names for automated transitions, user emails for manual ones

3. **Check requirements before transitions** - Don't move to active state without verifying requirements

4. **Handle transition failures gracefully** - Always check the success/error tuple returned

5. **Keep metadata lightweight** - Store only essential information in state_metadata

6. **Use views for complex queries** - The provided views are optimized for common queries

## Troubleshooting

### Resource stuck in a state
1. Check state transition history in UI or via API
2. Look for failed requirements
3. Check the state_reason field for clues
4. Use manual transition if needed (with caution)

### State transition failing
1. Verify the transition is allowed in the state machine
2. Check required metadata is provided
3. Look for validation errors in response
4. Ensure proper permissions

### Missing resources in overview
1. Ensure resource is registered in resource_states table
2. Check resource_type matches expected values
3. Verify views are created properly
4. Refresh materialized views if used

## Future Enhancements

1. **Automated State Transitions** - K8s operator to sync deployment status
2. **State-based Triggers** - Webhook notifications on state changes
3. **Bulk Operations** - Transition multiple resources at once
4. **State Machine Versioning** - Handle state machine evolution
5. **Custom State Machines** - Allow resource-specific state definitions
6. **Integration with CI/CD** - Automatic progression through states
7. **State-based Access Control** - Permissions based on resource state

## Summary

The Resource State Management System provides:
- ✅ Unified tracking across all resource types
- ✅ Clear visibility into resource lifecycle
- ✅ Audit trail for compliance
- ✅ Integration points for automation
- ✅ Extensible architecture for new resource types

This system transforms resource management from a black box into a transparent, manageable process with clear visibility at every stage.
