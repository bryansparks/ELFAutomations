# N8N Workflow Patterns Guide

## Overview

The enhanced N8N workflow factory now includes intelligent pattern detection and service selection. This guide explains how to use the new pattern-based workflow generation system.

## Design Patterns

### 1. Input-Process-Output Pattern
Basic pattern for receiving data, processing it, and sending to destination.
- **Use cases**: API integrations, data transformations, simple automations
- **Example**: "Receive webhook data, validate it, and store in database"

### 2. Email Management Pattern
Monitor and manage email communications with AI categorization.
- **Services**: Gmail, IMAP, SMTP
- **Storage**: Supabase for tracking
- **Features**: AI categorization, routing, auto-responses
- **Example**: "Monitor Gmail for customer emails, categorize with AI, route to teams"

### 3. SMS Communication Pattern
Handle SMS messaging with Twilio or MCP integrations.
- **Services**: Twilio, MCP SMS providers
- **Features**: Two-way messaging, routing, auto-responses
- **Example**: "Receive customer texts, analyze sentiment, route to support"

### 4. Approval Workflow Pattern
Multi-level approval processes with escalation.
- **Channels**: Slack, Email notifications
- **Features**: Timeout handling, escalation chains
- **Example**: "Expense approval with manager and director escalation"

### 5. Data Pipeline Pattern
ETL operations for data processing.
- **Sources**: APIs, Databases, Spreadsheets
- **Features**: Batch processing, error handling
- **Example**: "Extract sales data, transform it, load to data warehouse"

### 6. Report Generation Pattern
Automated report creation and distribution.
- **Schedule**: Cron-based triggers
- **Outputs**: Email, Google Docs, Slack
- **Example**: "Weekly sales report with charts sent to executives"

### 7. Customer Support Pattern
Unified support across multiple channels.
- **Channels**: Email, SMS, Slack
- **Features**: AI triage, ticket creation, routing
- **Example**: "Monitor all channels for support requests and create tickets"

### 8. Data Collection Pattern
Form and survey data collection workflows.
- **Sources**: Webhooks, Google Forms
- **Storage**: Supabase, Google Sheets
- **Example**: "Collect lead forms and sync to CRM"

## Service Configuration

### Default Services by Team

**Marketing Team:**
- Email: Gmail
- SMS: Twilio
- Storage: Supabase
- Spreadsheets: Google Sheets
- Chat: Slack
- AI: OpenAI GPT-4

**Engineering Team:**
- Email: SMTP
- Storage: PostgreSQL
- Chat: Slack
- AI: Anthropic Claude
- MCP: GitHub, Jira, Datadog

### Notification Priorities

**High Priority**: Slack + SMS + Email
**Medium Priority**: Slack + Email
**Low Priority**: Email only
**Errors**: Slack + Email (+ PagerDuty for engineering)

## Usage Examples

### CLI with Pattern Detection

```bash
# Generate workflow using pattern detection
python tools/n8n_workflow_factory_v2.py create \
  "Monitor Gmail for orders and create invoices in Google Sheets" \
  --name "Order Invoice Automation" \
  --team marketing \
  --use-pattern

# Generate without patterns (uses templates or custom)
python tools/n8n_workflow_factory_v2.py create \
  "Custom workflow description" \
  --name "Custom Workflow" \
  --team engineering
```

### Python API

```python
from elf_automations.shared.n8n.patterns import detect_pattern
from elf_automations.shared.n8n.config import WorkflowConfig
from tools.n8n_workflow_factory_v2 import EnhancedWorkflowFactory

# Configure team preferences
config = WorkflowConfig()
config.global_preferences.email_provider = "gmail"
config.global_preferences.sms_provider = "twilio"

# Create factory for team
factory = EnhancedWorkflowFactory(team_name="marketing")

# Generate with pattern detection
result = await factory.create_pattern_workflow(
    description="Monitor emails and route to support",
    name="Email Router",
    team="marketing",
    category="support"
)
```

### Pattern Detection Examples

| Description | Detected Pattern | Services Used |
|------------|-----------------|---------------|
| "Monitor email inbox" | Email Management | Gmail, Supabase, Slack |
| "Send SMS notifications" | SMS Communication | Twilio, Supabase |
| "Approve purchase orders" | Approval Workflow | Slack, Email, Supabase |
| "Weekly sales report" | Report Generation | Supabase, Google Sheets/Docs |
| "ETL customer data" | Data Pipeline | API, PostgreSQL |

## MCP Integration

The system supports MCP (Model Context Protocol) tools for extended functionality:

### When to Use MCP
- When native n8n nodes don't exist for a service
- For specialized integrations (e.g., custom SMS providers)
- When you need advanced tool capabilities

### Example MCP Services
- SMS providers beyond Twilio
- Specialized databases
- Custom authentication systems
- Industry-specific tools

### Configuration
```python
preferences = ServicePreferences(
    mcp_enabled=True,
    preferred_mcp_servers=["sms-gateway", "custom-crm"]
)
```

## Best Practices

1. **Use Patterns for Common Workflows**
   - Faster generation
   - Consistent structure
   - Built-in best practices

2. **Configure Team Preferences**
   - Set default services per team
   - Define notification rules
   - Specify restricted services

3. **Leverage AI Processing**
   - Email/SMS categorization
   - Sentiment analysis
   - Content generation

4. **Design for Reliability**
   - Error handling nodes
   - Retry logic
   - Notification on failures

5. **Optimize for Performance**
   - Batch processing where possible
   - Parallel execution
   - Rate limiting

## Workflow Structure

Generated workflows follow this structure:
```
Input Nodes → Processing/AI → Storage → Output/Notifications
     ↓                ↓           ↓              ↓
Error Handler → Error Storage → Error Notifications
```

## Adding Custom Patterns

To add a new pattern, extend `WorkflowPatterns`:

```python
@staticmethod
def my_custom_pattern() -> WorkflowPattern:
    return WorkflowPattern(
        name="my_custom",
        description="My custom pattern",
        inputs=[InputSource.WEBHOOK],
        storage=[StorageType.SUPABASE],
        outputs=[OutputChannel.SLACK],
        requires_ai=True
    )
```

## Testing Patterns

Run the demo script to test pattern detection:

```bash
# Show all patterns
python examples/pattern_workflow_demo.py --show-patterns

# Test pattern detection
python examples/pattern_workflow_demo.py --test-detection

# Generate example workflows
python examples/pattern_workflow_demo.py --generate
```

## Next Steps

1. Configure team preferences in `WorkflowConfig`
2. Test pattern detection with your use cases
3. Generate workflows using `--use-pattern` flag
4. Customize patterns for your specific needs
5. Set up MCP servers for extended functionality
