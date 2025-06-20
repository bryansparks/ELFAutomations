# N8N Workflow Factory Guide

## Overview

The N8N Workflow Factory provides a friction-less approach to creating workflows at scale, combining AI-powered generation with pre-built templates to enable hundreds of business automation workflows.

## Architecture

```
Natural Language → AI Analysis → Template Matching → Workflow Generation → N8N Import
                                         ↓
                                  Custom Generation
```

## Three-Tier Strategy

### 1. AI-Powered Generation
- Describe workflows in plain English
- AI analyzes and generates appropriate nodes
- Automatic configuration based on intent

### 2. Template Library
- Pre-built patterns for common operations
- Industry-tested configurations
- Customizable parameters

### 3. N8N Visual Builder
- Complex one-off workflows
- Visual debugging
- Fine-tuning generated workflows

## Quick Start

### Basic Usage

```bash
# Generate from description
python tools/n8n_workflow_factory_v2.py create \
  "Every Monday, fetch sales data and email report to team" \
  --name "Weekly Sales Report" \
  --team sales-team \
  --category automation

# List available templates
python tools/n8n_workflow_factory_v2.py list-templates

# Show specific template
python tools/n8n_workflow_factory_v2.py show-template data-pipeline etl
```

### Python API

```python
from tools.n8n_workflow_factory_v2 import EnhancedWorkflowFactory

factory = EnhancedWorkflowFactory()

# Generate workflow
workflow = await factory.create_workflow(
    description="When customer submits support ticket, categorize by urgency, "
                "route to appropriate team, and send acknowledgment email",
    name="Support Ticket Router",
    team="support-team",
    category="automation"
)

# Access the n8n JSON
n8n_json = workflow['workflow']
```

## Template Categories

### Data Pipeline Templates
- **ETL**: Extract, Transform, Load operations
- **Reporting**: Scheduled data aggregation and distribution
- **Data Sync**: Keep systems synchronized

### Integration Templates
- **CRM Sync**: Bi-directional CRM updates
- **API Gateway**: Multi-system orchestration
- **Event Broadcasting**: Publish/subscribe patterns

### Approval Templates
- **Multi-Step**: Hierarchical approval chains
- **Parallel Approval**: Multiple approvers
- **Conditional Routing**: Dynamic approval paths

### Automation Templates
- **Report Generator**: Scheduled reports with multiple outputs
- **Alert System**: Threshold monitoring and notifications
- **Task Automation**: Repetitive task workflows

## Workflow Patterns

### 1. Webhook → Process → Respond
```
Trigger: External system webhook
Process: Transform/validate data
Respond: Return success/failure
```

### 2. Schedule → Fetch → Store
```
Trigger: Cron schedule
Fetch: Pull from APIs/databases
Store: Save processed results
```

### 3. Event → Route → Notify
```
Trigger: System event
Route: Conditional logic
Notify: Multiple channels
```

## Advanced Features

### Intelligent Node Selection

The factory analyzes your description to select appropriate nodes:

- **"fetch data"** → HTTP Request node
- **"save to database"** → PostgreSQL node
- **"send to Slack"** → Slack node
- **"wait for approval"** → Wait node
- **"if amount > 1000"** → Switch node

### Automatic Configuration

Based on context, the factory configures:
- Webhook paths
- Schedule intervals
- Authentication methods
- Error handling

### Template Customization

Templates are customized based on your requirements:
```python
# Original template has daily schedule
"Every Monday at 9am, fetch sales data..."
# Factory updates to weekly Monday schedule
```

## Best Practices

### 1. Clear Descriptions

**Good**: "Every hour, check inventory levels below 100 units and create reorder request"

**Better**: "Every hour, query products table for items where quantity < 100, create purchase_orders record with supplier_id and quantity needed, then notify procurement team on Slack"

### 2. Specify Triggers

- **Schedule**: "Every Monday at 9am", "Daily at midnight", "Every 30 minutes"
- **Webhook**: "When customer signs up", "On order placement"
- **Manual**: "Manually triggered report"

### 3. Include Conditions

- "If amount exceeds $1000, escalate to manager"
- "Only process records created today"
- "Skip if customer is inactive"

### 4. Define Outputs

- "Send report to #sales Slack channel"
- "Email summary to executives"
- "Update status in database"

## Scaling to Hundreds of Workflows

### Organization by Function

```
/workflows
  /sales
    - lead-scoring.json
    - daily-pipeline-report.json
    - commission-calculator.json
  /finance
    - invoice-processing.json
    - expense-approval.json
    - budget-alerts.json
  /operations
    - inventory-check.json
    - supplier-sync.json
    - quality-alerts.json
```

### Naming Conventions

- `[department]-[function]-[frequency]`
- Examples:
  - `sales-leads-daily`
  - `finance-invoices-webhook`
  - `ops-inventory-hourly`

### Version Control

All workflows stored as JSON in Git:
- Track changes
- Review before deployment
- Rollback capability
- Team collaboration

## Deployment Process

### 1. Generate Workflow
```bash
python tools/n8n_workflow_factory_v2.py create \
  "Your workflow description" \
  --name "Workflow Name" \
  --team your-team \
  --output workflows/your-workflow.json
```

### 2. Review JSON
- Check node configuration
- Verify connections
- Update placeholders

### 3. Import to n8n
- Use n8n UI import
- Or API deployment (future)

### 4. Configure Credentials
- Database connections
- API keys
- Webhook URLs

### 5. Test & Activate
- Run test execution
- Verify outputs
- Enable workflow

## Monitoring & Optimization

### Track Performance
```python
from elf_automations.shared.n8n import N8NClient

async with N8NClient() as client:
    stats = await client.get_execution_history(
        workflow_name="your-workflow"
    )
```

### Identify Patterns
- Common failures
- Performance bottlenecks
- Usage patterns

### Iterate & Improve
- Update templates
- Refine AI prompts
- Optimize node configuration

## ROI Calculation

### Time Savings
- Manual process: 2 hours/week
- Automated: 5 minutes/week
- Savings: 1.92 hours/week

### Cost Savings
- 100 workflows × 1.92 hours × $50/hour = $9,600/week
- Annual savings: ~$500,000

### Efficiency Gains
- 24/7 operation
- Consistent execution
- Error reduction
- Audit trail

## Troubleshooting

### Common Issues

1. **Template Not Matched**
   - Add more specific keywords
   - Use `--force-custom` flag

2. **Invalid JSON**
   - Check for syntax errors
   - Validate in n8n import

3. **Missing Nodes**
   - Update description with operations
   - Manually add in n8n

### Debug Mode

```bash
# See AI analysis
python tools/n8n_workflow_factory_v2.py create \
  "description" --debug

# Force custom generation
python tools/n8n_workflow_factory_v2.py create \
  "description" --force-custom
```

## Future Enhancements

### Phase 3: Self-Service Portal
- Web interface for business users
- Approval workflow for production
- Template marketplace

### Phase 4: Advanced AI
- Learn from existing workflows
- Suggest optimizations
- Auto-generate from tickets

## Support

- Factory Issues: Create GitHub issue
- n8n Issues: Check n8n documentation
- Template Requests: Submit PR with new template