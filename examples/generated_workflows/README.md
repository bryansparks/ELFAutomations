# Pre-Generated N8N Workflows

This directory contains a comprehensive set of pre-generated n8n workflows organized by category. These workflows can be imported directly into n8n or customized using the n8n workflow factory.

## 📁 Directory Structure

```
generated_workflows/
├── marketing/           # Marketing automation workflows
├── sales/              # Sales process automation
├── daily_weekly/       # Recurring task automation
├── email_management/   # Email handling workflows
└── *.json             # Legacy workflows from previous sessions
```

## 🎯 Marketing Workflows

### 1. Social Media Monitor (`marketing/social_media_monitor.json`)
- **Schedule**: Every 15 minutes
- **Features**:
  - Fetches social media mentions across platforms
  - Performs sentiment analysis on mentions
  - Stores all mentions in database
  - Sends Slack alerts for negative sentiment
- **Use Case**: Brand monitoring and reputation management

### 2. Campaign Performance Tracker (`marketing/campaign_performance_tracker.json`)
- **Schedule**: Daily at 9:00 AM
- **Features**:
  - Retrieves active campaign data
  - Fetches analytics metrics (impressions, clicks, ROI)
  - Calculates performance metrics (CTR, CPA, conversion rates)
  - Generates HTML reports
  - Alerts on underperforming campaigns
- **Use Case**: Marketing campaign optimization

### 3. Lead Scoring Automation (`marketing/lead_scoring_automation.json`)
- **Trigger**: Webhook on new lead submission
- **Features**:
  - Validates lead data
  - Enriches with third-party data (Clearbit)
  - Calculates lead score based on multiple factors
  - Routes leads based on score (A/B/C grades)
  - Integrates with CRM and email marketing
- **Use Case**: Sales qualification and prioritization

## 💼 Sales Workflows

### 1. Deal Pipeline Automation (`sales/deal_pipeline_automation.json`)
- **Trigger**: Webhook on deal stage change
- **Features**:
  - Routes actions based on deal stage
  - Creates stage-specific tasks
  - Generates proposals automatically
  - Alerts managers for negotiation stage
  - Processes won/lost deals
  - Analyzes lost deal reasons
- **Use Case**: Sales process standardization

### 2. Quote Generation Workflow (`sales/quote_generation_workflow.json`)
- **Trigger**: Webhook on quote request
- **Features**:
  - Validates quote request data
  - Retrieves customer information and pricing
  - Calculates volume discounts and margins
  - Checks approval requirements
  - Generates PDF quotes
  - Sends quotes via email
  - Creates follow-up tasks
- **Use Case**: Automated quotation process

## 📅 Daily/Weekly Task Workflows

### 1. Daily Standup Automation (`daily_weekly/daily_standup_automation.json`)
- **Schedule**: Weekdays at 8:45 AM
- **Features**:
  - Sends standup reminders to team members
  - Collects standup responses
  - Identifies missing updates
  - Formats and posts team summaries
  - Generates participation metrics
  - Sends manager reports
- **Use Case**: Remote team coordination

### 2. Weekly Report Generator (`daily_weekly/weekly_report_generator.json`)
- **Schedule**: Fridays at 2:00 PM
- **Features**:
  - Aggregates weekly KPIs
  - Analyzes project status
  - Measures team performance
  - Generates AI insights using GPT-4
  - Creates PDF reports
  - Distributes to executives
  - Creates follow-up tasks in JIRA
- **Use Case**: Executive reporting and planning

## 📧 Email Management Workflows

### 1. Email Triage Automation (`email_management/email_triage_automation.json`)
- **Trigger**: IMAP email monitoring
- **Features**:
  - Extracts email metadata
  - Checks sender history
  - AI-powered categorization (GPT-3.5)
  - Routes emails by category
  - Creates support tickets
  - Updates CRM contacts
  - Applies Gmail labels
- **Use Case**: Inbox zero and email organization

### 2. Auto Response System (`email_management/auto_response_system.json`)
- **Trigger**: Webhook on email receipt
- **Features**:
  - Validates incoming emails
  - Checks auto-response rules
  - Prevents duplicate responses
  - Generates personalized responses
  - Respects business hours
  - Creates support tickets
  - Logs all interactions
- **Use Case**: Customer service automation

## 🚀 Quick Start

### Importing Workflows

1. Open your n8n instance
2. Go to Workflows → Import
3. Select the JSON file you want to import
4. Review and adjust credentials
5. Activate the workflow

### Using the Workflow Factory

Generate custom workflows from natural language:

```bash
cd tools
python n8n_workflow_factory.py "Your workflow description" \
  --name "Workflow Name" \
  --team "your-team" \
  --category "automation"
```

## 🔧 Customization Tips

### Common Modifications

1. **Change Schedule Timing**:
   - Look for `scheduleTrigger` nodes
   - Modify `interval`, `atHour`, `atMinute` parameters

2. **Update Notification Channels**:
   - Find Slack nodes
   - Change `channel` parameter to your channel

3. **Modify Database Tables**:
   - Look for PostgreSQL nodes
   - Update `table` and `columns` parameters

4. **Adjust API Endpoints**:
   - Find HTTP Request nodes
   - Update `url` parameters

### Environment Variables

Most workflows expect these credentials:
- PostgreSQL database
- Slack OAuth2
- Email SMTP/IMAP
- API keys (OpenAI, Clearbit, etc.)

## 📋 Workflow Categories

### Data Pipeline
- Schedule-based data fetching
- ETL processes
- Data synchronization

### Integration
- API integrations
- Third-party service connections
- Webhook handlers

### Automation
- Business process automation
- Repetitive task handling
- Rule-based actions

### Notification
- Alert systems
- Status updates
- Report distribution

### Approval
- Multi-step approval processes
- Escalation workflows
- Audit trails

## 🤝 Contributing

To add new workflows:

1. Use the n8n workflow factory
2. Test thoroughly in n8n
3. Export as JSON
4. Place in appropriate category folder
5. Update this README

## 📚 Resources

- [N8N Documentation](https://docs.n8n.io/)
- [Workflow Factory Guide](/tools/README.md)
- [Team Architecture](/docs/Agent Design Pattern V2.md)
