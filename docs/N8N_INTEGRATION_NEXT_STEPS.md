# N8N Integration - Next Steps

## Current Status

✅ **Phase 1 Complete**:
- N8N Client SDK created and working
- Workflow registry tables in Supabase
- Management tools (CLI, test scripts)
- Test workflow registered in system

## Immediate Next Steps

### 1. Create N8N Workflow

1. Access n8n UI: `http://[your-node-ip]:30678`
   - Credentials: admin / elf-n8n-2024

2. Import the test workflow:
   - Click "Import from File"
   - Select `/examples/n8n_workflows/test-webhook-workflow.json`
   - Or create manually:
     - Add Webhook node (path: `/test`)
     - Add Set node (process data)
     - Add Respond to Webhook node

3. Save and activate the workflow

4. Note the workflow ID from the URL (e.g., `workflow/7` → ID is `7`)

### 2. Update Registry

```bash
# Update the test workflow with actual n8n ID
python scripts/update_test_workflow.py YOUR_WORKFLOW_ID
```

### 3. Test the Integration

```bash
# Run the test client
python scripts/test_n8n_client.py

# The workflow execution test should now work!
```

## Real-World Example: Marketing Data Pipeline

### 1. Create Marketing Workflow in N8N

Create a workflow that:
- Webhook trigger: `/marketing/competitor-analysis`
- HTTP Request node: Fetch competitor data
- Code node: Process and analyze data
- Postgres node: Store results
- Respond node: Return analysis

### 2. Register in System

```bash
python scripts/n8n_workflow_manager.py register competitor-analysis \
    --description "Analyze competitor social media and pricing" \
    --category data-pipeline \
    --team marketing-team \
    --workflow-id 8 \
    --trigger webhook \
    --webhook-url http://n8n.n8n.svc.cluster.local:5678/webhook/marketing/competitor-analysis \
    --input-schema '{"competitors": ["array"], "metrics": ["array"]}' \
    --output-schema '{"analysis": "object", "report_url": "string"}'
```

### 3. Use in Marketing Team

```python
# In marketing team code
from elf_automations.shared.n8n import N8NClient

async def analyze_competitors():
    async with N8NClient() as client:
        result = await client.execute_workflow(
            workflow_name="competitor-analysis",
            data={
                "competitors": ["CompanyA", "CompanyB"],
                "metrics": ["social_engagement", "pricing"]
            },
            team_name="marketing-team"
        )
        print(f"Analysis ready: {result.output_data['report_url']}")
```

## Phase 2 Preview: Workflow Factory

Coming next week:
- Automatic workflow generation from descriptions
- Pre-built workflow templates
- LLM-powered node configuration

Example:
```python
from tools.n8n_workflow_factory import N8NWorkflowFactory

factory = N8NWorkflowFactory()
workflow = factory.create_workflow(
    "Create a workflow that fetches Twitter mentions daily and sends a summary to Slack"
)
# Automatically generates and deploys the workflow!
```

## Common Workflow Patterns

### 1. Data Pipeline Pattern
- Trigger: Schedule or webhook
- Fetch: HTTP Request or Database query
- Transform: Code or Function nodes
- Store: Database or File
- Notify: Email or Slack

### 2. Integration Pattern
- Trigger: Webhook from System A
- Validate: IF node
- Transform: Set or Code node
- Send: HTTP Request to System B
- Log: Database write

### 3. Approval Pattern
- Trigger: Form submission
- Create: Approval request
- Wait: Wait node
- Route: Switch node based on approval
- Action: Execute approved action

## Tips for Success

1. **Start Simple**: Begin with basic webhook workflows
2. **Use Internal URLs**: Always use cluster-internal URLs
3. **Track Everything**: Log all executions for debugging
4. **Version Control**: Export workflows as JSON and commit
5. **Test Thoroughly**: Use the test client before production

## Monitoring & Debugging

### View Execution Stats
```bash
python scripts/n8n_workflow_manager.py stats
```

### Check Recent Executions
```python
async with N8NClient() as client:
    history = await client.get_execution_history(limit=20)
    for exec in history:
        print(f"{exec.workflow_name}: {exec.status.value} ({exec.duration}s)")
```

### Debug Failed Workflows
- Check n8n UI execution history
- Review error_message in workflow_executions table
- Verify webhook URLs are accessible
- Check input/output schema matches

## Support

- N8N Docs: https://docs.n8n.io
- ELF Integration Guide: `/docs/N8N_INTEGRATION_GUIDE.md`
- Report Issues: GitHub Issues
