# N8N AI Workflow Generator - Control Center Integration

## Overview

The N8N AI Workflow Generator is now integrated into the Elf Control Center, providing a seamless interface for creating complex workflows using natural language descriptions powered by Claude AI.

## Features

### 1. Natural Language Workflow Creation
- Describe workflows in plain English
- AI analyzes and generates appropriate n8n nodes
- Automatic configuration based on intent
- Pattern detection for common workflow types

### 2. Visual Workflow Preview
- Interactive node-based visualization using React Flow
- Color-coded nodes by type (triggers, actions, AI, etc.)
- Real-time preview as you refine descriptions
- Minimap for large workflows

### 3. AI Assistant Chat
- Interactive conversation with Claude to refine requirements
- Suggestions for improvements and edge cases
- Best practice recommendations
- Copy refined descriptions directly to the generator

### 4. Template Intelligence
- Automatic template matching
- Customization based on specific requirements
- Learn from successfully deployed workflows

## Architecture

### Frontend Components

#### WorkflowCreator (`/src/components/workflows/WorkflowCreator.tsx`)
- Main dialog component for workflow creation
- Three tabs: Describe, Preview, AI Chat
- Form for workflow metadata (name, team, category)
- Example descriptions to get started

#### WorkflowVisualizer (`/src/components/workflows/WorkflowVisualizer.tsx`)
- React Flow-based visualization
- Custom node components with icons
- Automatic layout from n8n JSON
- Interactive zoom, pan, and minimap

#### WorkflowChat (`/src/components/workflows/WorkflowChat.tsx`)
- Real-time chat with Claude AI
- Message history with timestamps
- Extract and use workflow descriptions
- Contextual suggestions

### Backend Integration

#### API Endpoints

1. **POST `/api/workflows/generate`**
   - Generates workflow from description
   - Uses `n8n_workflow_factory_v2.py`
   - Returns workflow JSON and metadata

2. **POST `/api/workflows/deploy`**
   - Saves workflow to registry
   - Prepares for n8n deployment
   - Returns workflow ID and status

3. **POST `/api/workflows/chat`**
   - Chat with AI assistant
   - Context-aware responses
   - Workflow creation guidance

### AI Integration

#### LLM Factory
- Supports OpenAI and Anthropic providers
- Automatic fallback on quota errors
- Configurable per team

#### Workflow Factory V2
- Enhanced pattern detection
- Template matching
- Service-specific node selection
- Intelligent parameter configuration

## Usage Guide

### Creating a Workflow

1. **Open Control Center**
   ```
   http://localhost:3002/workflows
   ```

2. **Click "Create Workflow"**
   - Opens the AI-powered creation dialog

3. **Describe Your Workflow**
   - Use natural language
   - Be specific about:
     - Triggers (webhook, schedule, event)
     - Data sources and formats
     - Processing steps
     - Conditions and logic
     - Output destinations

4. **Example Descriptions**
   ```
   "Every Monday at 9am, fetch sales data from Supabase,
   calculate weekly totals, and email a report to the sales team"

   "When a customer submits a support ticket via webhook,
   use AI to categorize by urgency, route to appropriate team
   based on category, and send acknowledgment email"

   "Monitor #alerts Slack channel, when a message contains 'URGENT',
   create a ticket in the system, notify on-call engineer via SMS,
   and post confirmation back to Slack"
   ```

5. **Use AI Assistant**
   - Switch to Chat tab for help
   - Ask about best practices
   - Get suggestions for improvements
   - Refine your description

6. **Preview Workflow**
   - Visual representation of nodes
   - Verify connections and logic
   - Check node configurations

7. **Deploy**
   - Click "Deploy to N8N"
   - Workflow saved to registry
   - Manual import to n8n required (for now)

### Node Type Mapping

| Description Keywords | Generated Node Type |
|---------------------|--------------------|
| "webhook", "HTTP POST" | Webhook trigger |
| "every", "schedule", "cron" | Schedule trigger |
| "email", "gmail" | Gmail/Email nodes |
| "slack", "message" | Slack integration |
| "database", "query" | PostgreSQL/Supabase |
| "if", "condition" | Switch/If nodes |
| "transform", "process" | Code/Function nodes |
| "AI", "analyze", "categorize" | OpenAI/Anthropic nodes |

### Best Practices

1. **Clear Trigger Definition**
   - Specify exact trigger type
   - Include frequency for schedules
   - Define webhook paths

2. **Data Flow Description**
   - Where data comes from
   - How it should be transformed
   - Where it should go

3. **Error Handling**
   - What happens on failure
   - Who should be notified
   - Retry logic needed

4. **Specific Services**
   - Name exact services (Gmail vs generic email)
   - Include authentication needs
   - Specify API endpoints

## Advanced Features

### Pattern Detection

The system automatically detects common patterns:

- **Email Management**: Triage, categorize, respond
- **Data Pipeline**: ETL operations
- **Approval Workflows**: Multi-step approvals
- **Report Generation**: Scheduled aggregation
- **Customer Support**: Multi-channel routing
- **Monitoring & Alerts**: Threshold-based notifications

### Custom Node Configuration

The AI intelligently configures nodes based on context:

```javascript
// Example: Email node configuration
{
  "operation": "send",
  "to": "{{$node['previous'].json['email']}}",
  "subject": "Support Ticket Received",
  "message": "We've received your request..."
}
```

### Workflow Optimization

The system suggests optimizations:

- Parallel processing where possible
- Efficient data transformations
- Proper error handling
- Resource-conscious scheduling

## Troubleshooting

### Common Issues

1. **"Failed to generate workflow"**
   - Check API is running: `http://localhost:8001/health`
   - Verify LLM credentials are configured
   - Check Supabase connection

2. **"Invalid workflow JSON"**
   - Try more specific description
   - Use AI chat for refinement
   - Check for unsupported node types

3. **"Deployment failed"**
   - Verify team exists in registry
   - Check Supabase permissions
   - Ensure workflow name is unique

### Debug Mode

Enable debug logging:
```python
export DEBUG=true
python run_control_center_api.py
```

## Future Enhancements

### Phase 2: Direct N8N Deployment
- API integration with n8n
- Automatic credential mapping
- One-click deployment

### Phase 3: Workflow Marketplace
- Share workflows between teams
- Community templates
- Rating and reviews

### Phase 4: Advanced AI Features
- Learn from execution history
- Proactive optimization suggestions
- Anomaly detection
- Auto-scaling recommendations

## API Reference

### Generate Workflow
```typescript
POST /api/workflows/generate
{
  "description": "Natural language description",
  "name": "Workflow name",
  "team": "team-name",
  "category": "automation"
}

Response:
{
  "workflow": { /* n8n JSON */ },
  "metadata": {
    "pattern": "detected-pattern",
    "trigger_type": "webhook",
    "services": { /* detected services */ }
  }
}
```

### Deploy Workflow
```typescript
POST /api/workflows/deploy
{
  "workflow": { /* n8n JSON */ },
  "metadata": { /* from generate */ }
}

Response:
{
  "success": true,
  "workflow_id": "uuid",
  "message": "Deployment status"
}
```

### Chat with Assistant
```typescript
POST /api/workflows/chat
{
  "messages": [
    {"role": "user", "content": "How do I..."}
  ],
  "currentDescription": "optional context",
  "context": "workflow_creation"
}

Response:
{
  "content": "Assistant response",
  "suggestions": ["Follow-up question 1", "..."]
}
```

## Security Considerations

1. **API Keys**: Stored securely via credential manager
2. **Workflow Validation**: Sanitized before deployment
3. **Team Isolation**: Workflows scoped to teams
4. **Audit Trail**: All actions logged

## Getting Started

1. Ensure all services are running:
   ```bash
   # Control Center API
   cd elf_automations/api
   python control_center.py

   # Control Center UI
   cd packages/templates/elf-control-center
   npm install
   npm run dev
   ```

2. Configure environment:
   ```bash
   # .env file
   OPENAI_API_KEY=your-key
   ANTHROPIC_API_KEY=your-key
   SUPABASE_URL=your-url
   SUPABASE_ANON_KEY=your-key
   ```

3. Open Control Center:
   ```
   http://localhost:3002
   ```

4. Navigate to Workflows page and start creating!

## Support

- **Documentation**: This guide and inline help
- **AI Assistant**: Built-in chat for guidance
- **Examples**: Pre-built descriptions to start from
- **Community**: Share workflows and get help
