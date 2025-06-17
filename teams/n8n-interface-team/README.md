# n8n-interface-team

## Overview

**Purpose**: Enable seamless integration between AI teams and n8n automation workflows

**Framework**: CrewAI
**Department**: infrastructure
**Reports To**: None
**Created**: 2025-06-14

This team acts as the bridge between AI teams and n8n workflows. When an AI team needs to execute a workflow, they send an A2A request to this team. The team validates the request, triggers the n8n workflow, monitors its execution, handles any errors, and returns the results back to the requesting team. All executions are tracked in Supabase for audit and analytics purposes.

## Team Composition

| Role | Personality | Key Responsibilities |
|------|-------------|----------------------|
| Manager with A2A (Manager) | strategic-thinker | Receives workflow execution requests from other teams via A2A protocol, Delegates tasks to appropriate team members based on request type, Monitors overall team performance and workflow execution metrics |
| Validation Specialist | detail-oriented | Validates incoming workflow requests against schema definitions, Ensures all required parameters are present and properly formatted, Checks authorization and permissions for workflow execution |
| Monitoring Specialist | analytical | Monitors n8n workflow executions in real-time, Updates Supabase with execution status and progress, Tracks execution metrics and performance data |
| Resilience Engineer | problem-solver | Manages workflow execution failures and implements retry logic, Categorizes errors and determines appropriate recovery strategies, Maintains error logs and patterns for continuous improvement |
| Registry Specialist | methodical | Maintains up-to-date workflow registry in Supabase, Synchronizes workflow definitions with n8n instance, Tracks workflow versions and deprecation status |

**Team Size**: 5 members
**Process Type**: Hierarchical

## Technical Details

### LLM Configuration
- **Provider**: OpenAI
- **Model**: gpt-4
- **Fallback**: Enabled (automatic failover chain)

### Infrastructure
- **Container**: Docker multi-stage build
- **Orchestration**: Kubernetes (namespace: elf-teams)
- **API**: FastAPI with A2A protocol support
- **Memory**: Qdrant vector database
- **Registry**: Supabase team registry

## Getting Started

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export OPENAI_API_KEY=your-key  # or ANTHROPIC_API_KEY
   export SUPABASE_URL=your-url
   export SUPABASE_KEY=your-key
   export N8N_BASE_URL=http://localhost:5678  # Your n8n instance
   ```

3. **Run the team**:
   ```bash
   python team_server.py
   ```

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t n8n-interface-team .
   ```

2. **Run locally**:
   ```bash
   docker run -p 8000:8000 \
     -e OPENAI_API_KEY=$OPENAI_API_KEY \
     n8n-interface-team
   ```

### Kubernetes Deployment

1. **Apply the manifest**:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

2. **Check status**:
   ```bash
   kubectl get pods -n elf-teams -l app=n8n-interface-team
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /task` - Submit task via A2A protocol
- `GET /capabilities` - List team capabilities
- `GET /status` - Current team status

## n8n Integration

### Available n8n Tools

The team has access to specialized n8n integration tools:

- `trigger_n8n_workflow` - Trigger a workflow via webhook
- `check_workflow_execution_status` - Check status of running workflows
- `list_available_workflows` - List all registered workflows
- `validate_workflow_input` - Validate input against workflow schema
- `update_workflow_registry` - Update workflow definitions
- `record_workflow_error` - Track and analyze errors

### Workflow Request Format

When sending a workflow execution request via A2A:

```json
{
  "task": "execute_workflow",
  "workflow_id": "workflow-123",
  "webhook_path": "data-processing",
  "payload": {
    "input_data": "...",
    "parameters": {}
  },
  "success_criteria": {
    "timeout": 300,
    "expected_output": "processed_data"
  }
}
```

### Database Schema

The team uses the following Supabase tables:

- `workflow_registry` - Catalog of available workflows
- `workflow_executions` - Track all workflow runs
- `workflow_errors` - Detailed error tracking
- `workflow_metrics` - Performance metrics

## Team Communication

### Internal (Within Team)
- Natural language communication between agents
- Personality-driven interactions
- Logged to `logs/n8n-interface-team_communications.log`

### External (Between Teams)
- A2A protocol through manager agent only
- Structured task requests and responses
- Logged to `logs/n8n-interface-team_a2a.log`

## Memory & Learning

The team uses Qdrant for memory storage and implements:
- Experience storage and retrieval
- Pattern recognition from past tasks
- Continuous improvement through reflection
- Performance insights generation

## Monitoring

- Prometheus metrics on port 9090
- Structured JSON logging
- Health checks every 30 seconds
- Cost and quota tracking

## Development

### Adding New Capabilities

1. Update agent responsibilities in `agents/`
2. Add new tools in `tools/`
3. Update team configuration in `config/team_config.yaml`
4. Rebuild and redeploy

### Testing

```bash
# Run health check
curl http://localhost:8000/health

# Submit a task
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"from_agent": "test", "to_agent": "n8n-interface-team-manager",
       "task_type": "request", "task_description": "Test task"}'
```

## Troubleshooting

1. **LLM Quota Errors**: Check daily limits in `config/llm_config.yaml`
2. **Memory Connection**: Verify Qdrant service is accessible
3. **A2A Communication**: Check AgentGateway service status
4. **Deployment Issues**: Review pod logs with `kubectl logs`
5. **n8n Connection**: Verify N8N_BASE_URL and webhook endpoints
6. **Workflow Errors**: Check workflow_errors table in Supabase

---

Generated by Team Factory | Framework: CrewAI | LLM: OpenAI
