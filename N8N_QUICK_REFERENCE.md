# N8N Integration Quick Reference

## Essential Commands

```bash
# Check workflow registry
python scripts/n8n_workflow_manager.py list

# Register new workflow
python scripts/n8n_workflow_manager.py register [name] \
  --description "desc" --category automation --team my-team \
  --workflow-id 7 --trigger webhook \
  --webhook-url http://n8n.n8n.svc.cluster.local:5678/webhook/[path]

# Update test workflow
python scripts/update_test_workflow.py [workflow-id]

# Test integration
python scripts/test_n8n_integration.py
```

## Python SDK Usage

```python
from elf_automations.shared.n8n import N8NClient

# Execute workflow
async with N8NClient() as client:
    result = await client.execute_workflow(
        workflow_name="test-webhook-workflow",
        data={"message": "Hello"},
        team_name="my-team"
    )
    print(result.output_data)

# List workflows
workflows = await client.list_workflows(owner_team="my-team")

# Get execution history
history = await client.get_execution_history(limit=10)
```

## Workflow Categories
- `data-pipeline` - ETL and data processing
- `integration` - System-to-system
- `automation` - General automation
- `notification` - Alerts and notifications
- `approval` - Approval workflows

## URLs
- **N8N UI**: http://[node-ip]:30678 (admin/elf-n8n-2024)
- **Internal webhook**: http://n8n.n8n.svc.cluster.local:5678/webhook/[path]

## Troubleshooting
- Workflow not found? Check: `python scripts/n8n_workflow_manager.py list`
- Execution failed? Check n8n UI execution history
- Can't connect? Verify SUPABASE_URL and SUPABASE_ANON_KEY in .env