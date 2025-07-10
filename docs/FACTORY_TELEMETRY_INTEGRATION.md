# Factory Telemetry Integration Guide

## Overview

This guide explains how to integrate the telemetry patches into the three factory files to enable automatic telemetry tracking and entity registration.

## Integration Steps

### 1. Team Factory (`tools/team_factory.py`)

Since `team_factory.py` is a backward compatibility wrapper, add the patch import to the main script:

```python
#!/usr/bin/env python3
"""
Backward compatibility wrapper for team_factory.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Also add project root for elf_automations imports
project_root = Path(__file__).parent.parent
if project_root.exists():
    sys.path.insert(0, str(project_root))

# Import and apply telemetry patch
try:
    from team_factory_telemetry_patch import patch_team_factory
    patch_team_factory()
except ImportError:
    print("Warning: Telemetry patch not available")

# Rest of the existing code...
```

### 2. MCP Server Factory (`tools/mcp_server_factory.py`)

Add the telemetry patch import near the top of the file:

```python
#!/usr/bin/env python3
"""
MCP Server Factory - Creates SDK-Compliant MCP Servers
"""

# Existing imports...

# Import and apply telemetry patch
try:
    from mcp_server_factory_telemetry_patch import patch_mcp_server_factory
    patch_mcp_server_factory()
except ImportError:
    print("Warning: MCP telemetry patch not available")

# Rest of the existing code...
```

### 3. N8N Workflow Factory V3 (`tools/n8n_workflow_factory_v3.py`)

Add the telemetry patch import after the initial imports:

```python
#!/usr/bin/env python3
"""
N8N Workflow Factory V3
"""

# Existing imports...

# Import and apply telemetry patch
try:
    from n8n_workflow_factory_v3_telemetry_patch import patch_n8n_workflow_factory
    patch_n8n_workflow_factory()
except ImportError:
    print("Warning: N8N telemetry patch not available")

# Rest of the existing code...
```

## What the Patches Provide

### Team Factory Telemetry
- Tracks team creation operations
- Records team metadata (framework, LLM provider, agent count)
- Automatically registers teams in unified registry
- Updates team state (created, active, etc.)
- Tracks errors during team creation

### MCP Server Factory Telemetry
- Tracks MCP server creation and deployment
- Records server capabilities (tools, resources)
- Automatically registers servers in unified registry
- Tracks deployment state changes
- Provides tool usage telemetry decorators

### N8N Workflow Factory V3 Telemetry
- Tracks AI workflow creation
- Records workflow patterns and AI configurations
- Extracts and registers workflow capabilities
- Links workflows to parent teams
- Includes telemetry nodes in generated workflows

## Telemetry Data Flow

```
Factory Operation
      ↓
Telemetry Client (fire-and-forget)
      ↓
Supabase Tables:
├── communication_telemetry (operation tracking)
└── unified_registry (entity registration)
      ↓
Control Center UI
```

## Benefits

1. **Complete Visibility**: All entity creation is tracked
2. **No Registration Gaps**: Automatic registration ensures no "holes"
3. **Performance Metrics**: Track creation times and success rates
4. **Error Tracking**: Capture and analyze failures
5. **Capability Discovery**: Know what each entity can do
6. **Relationship Mapping**: Track parent-child relationships

## Testing the Integration

After adding the patches, test each factory:

```bash
# Test team factory
cd tools
python team_factory.py

# Test MCP server factory
python mcp_server_factory.py create \
  --name test-server \
  --display-name "Test Server" \
  --description "Test MCP server with telemetry"

# Test N8N workflow factory
python n8n_workflow_factory_v3.py create-ai \
  "Create a workflow that monitors Slack and responds with AI" \
  --name "AI Slack Monitor" \
  --team "support-team"
```

## Verifying Telemetry

Check that telemetry is working:

```sql
-- Check recent factory operations
SELECT * FROM communication_telemetry
WHERE workflow_id IN ('team-factory', 'mcp-factory', 'n8n-factory-v3')
ORDER BY timestamp DESC
LIMIT 20;

-- Check registered entities
SELECT * FROM unified_registry
WHERE registered_by IN ('team_factory', 'mcp_server_factory', 'n8n_workflow_factory_v3')
ORDER BY created_at DESC;

-- Check for registration gaps
SELECT * FROM check_registration_gaps();
```

## Troubleshooting

### Telemetry Not Recording
1. Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set
2. Verify telemetry tables exist (run setup script)
3. Check factory console output for warnings

### Registration Failures
1. Look for "Warning: Could not register" messages
2. Check Supabase connection
3. Verify RPC functions exist

### Import Errors
1. Ensure patch files are in same directory as factories
2. Check Python path includes project root
3. Verify `elf_automations` package is accessible

## Next Steps

1. **Deploy Updated Factories**: Ensure all team members use updated versions
2. **Monitor Metrics**: Set up dashboards for factory usage
3. **Alert on Failures**: Configure alerts for high error rates
4. **Regular Audits**: Run registration gap checks weekly
