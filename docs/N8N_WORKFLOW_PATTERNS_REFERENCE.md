# N8N Workflow Patterns Reference Guide

## Table of Contents
1. [Overview](#overview)
2. [Pattern Categories](#pattern-categories)
3. [Authentication Requirements](#authentication-requirements)
4. [Pattern Details](#pattern-details)
5. [Service Configuration](#service-configuration)
6. [Implementation Examples](#implementation-examples)
7. [Troubleshooting](#troubleshooting)

## Overview

The N8N Workflow Pattern system provides intelligent workflow generation based on common business patterns. Each pattern includes predefined inputs, processing logic, storage, and outputs that can be customized based on your specific needs.

## Pattern Categories

### 1. **Input-Process-Output Pattern**
**Use Case**: Basic data flow operations
- Receive data from an API or webhook
- Process/transform the data
- Send to destination

**Example**: "Receive order data, calculate tax, store in database"

### 2. **Email Management Pattern**
**Use Case**: Email triage and automation
- Monitor email accounts (Gmail, IMAP)
- AI-powered categorization
- Routing to appropriate teams
- Auto-responses

**Example**: "Monitor support@company.com, categorize emails, create tickets for urgent ones"

### 3. **SMS Communication Pattern**
**Use Case**: Two-way SMS messaging
- Receive SMS via Twilio webhook
- Process and analyze content
- Route or auto-respond
- Track conversations

**Example**: "Customer SMS support with automated FAQ responses"

### 4. **Approval Workflow Pattern**
**Use Case**: Multi-level approval processes
- Request submission
- Routing based on criteria
- Escalation chains
- Notification at each step

**Example**: "Purchase orders over $5000 need VP approval"

### 5. **Data Pipeline Pattern**
**Use Case**: ETL operations
- Extract from multiple sources
- Transform and validate
- Load to destination
- Error handling

**Example**: "Sync Salesforce leads to internal database nightly"

### 6. **Report Generation Pattern**
**Use Case**: Automated reporting
- Scheduled data collection
- Aggregation and analysis
- Multi-format output
- Distribution

**Example**: "Weekly sales dashboard sent to executives"

### 7. **Customer Support Pattern**
**Use Case**: Unified support system
- Monitor multiple channels
- Centralized ticketing
- Smart routing
- SLA tracking

**Example**: "Monitor email, SMS, and Slack for support requests"

### 8. **Data Collection Pattern**
**Use Case**: Form and survey processing
- Webhook reception
- Data validation
- Storage in multiple systems
- Confirmation sending

**Example**: "Process website contact forms and add to CRM"

## Authentication Requirements

### Gmail
```yaml
Required:
  - OAuth2 Client ID
  - OAuth2 Client Secret
  - Redirect URI: http://localhost:5678/rest/oauth2-credential/callback
Setup:
  1. Enable Gmail API in Google Cloud Console
  2. Create OAuth2 credentials
  3. Add authorized redirect URIs
  4. Configure in n8n credentials
```

### Twilio
```yaml
Required:
  - Account SID
  - Auth Token
  - Phone Number (for sending)
  - Webhook URL (for receiving)
Setup:
  1. Create Twilio account
  2. Purchase phone number
  3. Configure webhook URL in Twilio console
  4. Add credentials to n8n
```

### Slack
```yaml
Required:
  - OAuth Access Token
  - Bot Token (for posting)
  - Webhook URL (optional)
Setup:
  1. Create Slack App
  2. Add OAuth scopes (chat:write, channels:read)
  3. Install to workspace
  4. Copy tokens to n8n
```

### Google Sheets/Docs
```yaml
Required:
  - OAuth2 Client ID
  - OAuth2 Client Secret
  - API Scopes
Setup:
  1. Enable Google Sheets/Docs API
  2. Create service account or OAuth2 credentials
  3. Share sheets/docs with service account email
  4. Configure in n8n
```

### Supabase
```yaml
Required:
  - Project URL
  - Service Role Key (or Anon Key)
  - Table permissions
Setup:
  1. Create Supabase project
  2. Copy URL and keys from settings
  3. Configure RLS policies if needed
  4. Add to n8n credentials
```

### OpenAI/Anthropic
```yaml
Required:
  - API Key
  - Organization ID (OpenAI)
Setup:
  1. Create account
  2. Generate API key
  3. Set usage limits
  4. Configure in n8n
```

### MCP (Model Context Protocol)
```yaml
Required:
  - MCP Server URL
  - Authentication (varies by server)
Setup:
  1. Deploy MCP server
  2. Configure authentication
  3. Add as n8n credential
  4. Map tools in workflow
```

## Pattern Details

### Email Management Pattern

**Nodes Generated**:
1. **Email Trigger** (Gmail/IMAP)
   - Polls for new emails
   - Filters by label/folder
   - Extracts metadata

2. **AI Categorization** (OpenAI/Anthropic)
   - Analyzes content
   - Determines urgency
   - Suggests routing

3. **Data Storage** (Supabase)
   - Tracks all emails
   - Stores categorization
   - Enables reporting

4. **Routing Logic** (Switch)
   - Routes by category
   - Handles priorities
   - Manages escalations

5. **Notifications** (Slack/Email)
   - Alerts teams
   - Provides summaries
   - Includes actions

**Configuration Options**:
```json
{
  "email_provider": "gmail",
  "ai_model": "gpt-4",
  "storage": "supabase",
  "notification_channels": ["slack", "email"],
  "categories": ["support", "sales", "urgent"],
  "auto_response": true
}
```

### SMS Communication Pattern

**Nodes Generated**:
1. **Webhook Receiver** (Twilio)
   - Receives SMS
   - Extracts metadata
   - Validates source

2. **Customer Lookup** (Database)
   - Checks history
   - Gets preferences
   - Identifies VIPs

3. **AI Analysis** (OpenAI)
   - Sentiment analysis
   - Intent detection
   - Response generation

4. **Response Router** (If/Switch)
   - Auto-respond vs human
   - Priority routing
   - Escalation logic

5. **Message Sender** (Twilio)
   - Sends responses
   - Tracks delivery
   - Handles errors

**Configuration Options**:
```json
{
  "sms_provider": "twilio",
  "auto_response_enabled": true,
  "sentiment_analysis": true,
  "support_hours": "9-5 EST",
  "escalation_keywords": ["urgent", "emergency"]
}
```

### Report Generation Pattern

**Nodes Generated**:
1. **Schedule Trigger**
   - Cron expression
   - Time zone handling
   - Holiday awareness

2. **Data Collection** (Multiple sources)
   - Database queries
   - API calls
   - File reads

3. **Data Processing** (Code)
   - Aggregation
   - Calculations
   - Formatting

4. **Report Creation**
   - Google Sheets
   - Google Docs
   - PDF generation

5. **Distribution**
   - Email with attachments
   - Slack summaries
   - Dashboard updates

**Configuration Options**:
```json
{
  "schedule": "0 9 * * 1",
  "data_sources": ["supabase", "google_sheets"],
  "output_formats": ["sheets", "docs", "pdf"],
  "recipients": {
    "email": ["executives@company.com"],
    "slack": ["#weekly-reports"]
  }
}
```

## Service Configuration

### Team-Based Preferences

```python
# Marketing Team Configuration
marketing_config = {
    "email_provider": "gmail",
    "sms_provider": "twilio",
    "storage": "supabase",
    "spreadsheets": "google_sheets",
    "ai_provider": "openai",
    "notification_priority": {
        "high": ["slack", "sms"],
        "medium": ["slack", "email"],
        "low": ["email"]
    }
}

# Engineering Team Configuration
engineering_config = {
    "email_provider": "smtp",
    "storage": "postgres",
    "ai_provider": "anthropic",
    "mcp_servers": ["github", "jira"],
    "notification_priority": {
        "high": ["pagerduty", "slack"],
        "medium": ["slack"],
        "low": ["email"]
    }
}
```

### Global Defaults

```yaml
Workflow Settings:
  - Save execution data: true
  - Retry on failure: 3 times
  - Timeout: 300 seconds
  - Error workflow: "error-handler"

Rate Limiting:
  - Max executions: 100/hour
  - Concurrent executions: 5

Data Handling:
  - Batch size: 100
  - Parallel processing: true
```

## Implementation Examples

### Example 1: Customer Email Triage

```bash
python tools/n8n_workflow_factory_v2.py create \
  "Monitor support@company.com Gmail, use AI to categorize customer emails by urgency and topic, store in Supabase, and notify the right team in Slack" \
  --name "Customer Email Triage" \
  --team support \
  --use-pattern
```

**Generated Workflow**:
- Pattern: Email Management
- Input: Gmail (support@company.com)
- AI: GPT-4 for categorization
- Storage: Supabase (emails table)
- Output: Slack (#support-urgent, #support-general)

### Example 2: SMS Order Updates

```bash
python tools/n8n_workflow_factory_v2.py create \
  "Send SMS updates via Twilio when orders change status in our database, include tracking info" \
  --name "Order Status SMS" \
  --team operations \
  --use-pattern
```

**Generated Workflow**:
- Pattern: SMS Communication
- Trigger: Database change (orders table)
- Processing: Format message with tracking
- Output: Twilio SMS
- Storage: Message log in Supabase

### Example 3: Weekly Performance Dashboard

```bash
python tools/n8n_workflow_factory_v2.py create \
  "Every Monday at 9am, pull performance metrics from Supabase, create Google Sheets report with charts, generate executive summary in Google Docs, and email to leadership" \
  --name "Weekly Performance Dashboard" \
  --team analytics \
  --use-pattern
```

**Generated Workflow**:
- Pattern: Report Generation
- Trigger: Weekly schedule (Monday 9am)
- Data: Supabase queries
- Processing: Aggregation and charts
- Output: Google Sheets + Docs + Gmail

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify credentials in n8n
   - Check API quotas/limits
   - Ensure proper scopes/permissions

2. **Pattern Not Detected**
   - Use more specific keywords
   - Manually specify pattern
   - Check pattern detection logic

3. **Service Not Available**
   - Verify team configuration
   - Check service restrictions
   - Ensure MCP server is running

4. **Workflow Errors**
   - Check error workflow logs
   - Verify data formats
   - Test individual nodes

### Debug Mode

```bash
# Enable verbose logging
export N8N_LOG_LEVEL=debug

# Test pattern detection
python examples/pattern_workflow_demo.py --test-detection

# Generate with debug output
python tools/n8n_workflow_factory_v2.py create \
  "your description" \
  --name "Test" \
  --team test \
  --use-pattern \
  --debug
```

### Getting Help

1. Check generated workflow JSON for issues
2. Verify all required credentials are configured
3. Test individual services separately
4. Review n8n execution logs
5. Check pattern matching in logs

## Next Steps

1. **Configure Credentials**: Set up all required service credentials in n8n
2. **Test Patterns**: Run pattern detection tests with your use cases
3. **Customize Patterns**: Extend patterns for your specific needs
4. **Set Team Preferences**: Configure service preferences per team
5. **Deploy Workflows**: Import generated workflows into n8n and activate

Remember: The pattern system generates the workflow structure, but you'll need to configure credentials and test each workflow before production use.
