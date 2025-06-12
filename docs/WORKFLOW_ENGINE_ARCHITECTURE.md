# Workflow Engine Architecture for Multi-Team Orchestration

**Date**: January 22, 2025
**Status**: Design Proposal

## Overview

A workflow engine that enables complex, multi-team processes to run autonomously by orchestrating team interactions through declarative workflows.

## Problem Statement

Currently:
- Teams work in isolation or with simple A2A messages
- No way to define complex multi-step processes
- No branching logic or parallel execution
- Error handling is ad-hoc
- No visibility into process state

## Proposed Solution: Workflow Orchestration MCP

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Workflow Engine MCP                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Workflow   │  │   Execution  │  │    State      │  │
│  │  Parser     │  │   Engine     │  │   Manager     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │
    ┌─────────────────────┴────────────────────────┐
    │                                               │
┌───▼────────┐  ┌────────────────┐  ┌─────────────▼──┐
│   Team A   │  │    Team B      │  │    Team C      │
│ (via A2A)  │  │   (via A2A)    │  │   (via A2A)    │
└────────────┘  └────────────────┘  └────────────────┘
```

## Database Schema

```sql
-- Workflow definitions
CREATE TABLE workflow_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    definition JSONB NOT NULL, -- The workflow DSL
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active', -- active, deprecated, testing
    tags TEXT[],
    UNIQUE(name, version)
);

-- Workflow instances (running workflows)
CREATE TABLE workflow_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id UUID REFERENCES workflow_definitions(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- running, completed, failed, cancelled, paused
    current_step VARCHAR(255),
    context JSONB DEFAULT '{}', -- Workflow variables/state
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_details JSONB,
    parent_instance_id UUID REFERENCES workflow_instances(id), -- For sub-workflows
    triggered_by VARCHAR(255), -- team_id or user_id
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
);

-- Step executions
CREATE TABLE workflow_step_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID REFERENCES workflow_instances(id) ON DELETE CASCADE,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(50) NOT NULL, -- task, parallel, condition, loop, subworkflow
    status VARCHAR(50) NOT NULL, -- pending, running, completed, failed, skipped
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    assigned_team VARCHAR(255),
    input_data JSONB,
    output_data JSONB,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    INDEX idx_instance_status (instance_id, status)
);

-- Team task queue (tasks assigned by workflows)
CREATE TABLE workflow_team_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID REFERENCES workflow_instances(id),
    step_execution_id UUID REFERENCES workflow_step_executions(id),
    team_id VARCHAR(255) NOT NULL,
    task_type VARCHAR(255) NOT NULL,
    priority INTEGER DEFAULT 5,
    deadline TIMESTAMP WITH TIME ZONE,
    input_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, claimed, in_progress, completed, failed
    claimed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    output_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_team_status (team_id, status),
    INDEX idx_priority_created (priority DESC, created_at)
);

-- Workflow triggers/events
CREATE TABLE workflow_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id UUID REFERENCES workflow_definitions(id),
    trigger_type VARCHAR(50) NOT NULL, -- event, schedule, manual, webhook
    trigger_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow audit log
CREATE TABLE workflow_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID REFERENCES workflow_instances(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    details JSONB NOT NULL,
    team_id VARCHAR(255),
    INDEX idx_instance_time (instance_id, timestamp)
);
```

## Workflow Definition Language (DSL)

### YAML-based DSL Example

```yaml
name: customer-onboarding
version: 1
description: Complete customer onboarding process
timeout: 7d  # 7 days max

inputs:
  - name: customer_data
    type: object
    required: true
  - name: urgency
    type: string
    default: normal

outputs:
  - name: customer_id
  - name: onboarding_report

steps:
  # Step 1: Validate customer data
  - id: validate_data
    type: task
    team: compliance-team
    action: validate_customer_data
    inputs:
      data: ${inputs.customer_data}
    timeout: 1h
    on_failure: retry
    retry:
      attempts: 3
      backoff: exponential

  # Step 2: Parallel account setup
  - id: setup_accounts
    type: parallel
    steps:
      - id: create_billing
        type: task
        team: finance-team
        action: create_billing_account
        inputs:
          customer: ${inputs.customer_data}

      - id: create_technical
        type: task
        team: engineering-team
        action: provision_technical_account
        inputs:
          customer: ${inputs.customer_data}

      - id: create_support
        type: task
        team: support-team
        action: setup_support_portal
        inputs:
          customer: ${inputs.customer_data}

  # Step 3: Conditional premium setup
  - id: check_premium
    type: condition
    condition: ${inputs.customer_data.tier == 'premium'}
    if_true:
      - id: premium_setup
        type: task
        team: premium-services-team
        action: configure_premium_features
        inputs:
          customer_id: ${steps.create_technical.outputs.account_id}

  # Step 4: Send notifications
  - id: notify_complete
    type: parallel
    steps:
      - id: email_customer
        type: task
        team: marketing-team
        action: send_welcome_email
        inputs:
          email: ${inputs.customer_data.email}
          account_id: ${steps.create_technical.outputs.account_id}

      - id: notify_sales
        type: task
        team: sales-team
        action: update_crm
        inputs:
          customer_id: ${steps.create_billing.outputs.customer_id}
          status: onboarded

  # Step 5: Generate report
  - id: final_report
    type: task
    team: analytics-team
    action: generate_onboarding_report
    inputs:
      customer_id: ${steps.create_billing.outputs.customer_id}
      steps_completed: ${workflow.completed_steps}
    outputs:
      report: onboarding_report

error_handlers:
  - error_type: timeout
    action: notify
    team: operations-team

  - error_type: validation_failed
    action: escalate
    team: compliance-team
```

### Advanced Features

#### 1. Loops
```yaml
- id: process_items
  type: loop
  items: ${inputs.order_items}
  as: item
  steps:
    - id: validate_item
      type: task
      team: inventory-team
      action: check_availability
      inputs:
        item: ${item}
```

#### 2. Sub-workflows
```yaml
- id: run_sub_process
  type: subworkflow
  workflow: order-fulfillment
  version: 2
  inputs:
    order_id: ${inputs.order_id}
```

#### 3. Human Approval Gates
```yaml
- id: approval_gate
  type: approval
  approvers:
    - team: executive-team
      role: cfo
  timeout: 24h
  message: "Approve discount over $10,000"
```

## MCP Implementation

### Core Tools

```typescript
interface WorkflowTools {
  // Definition management
  create_workflow(definition: WorkflowDefinition): WorkflowId;
  update_workflow(id: WorkflowId, definition: WorkflowDefinition): void;
  list_workflows(filters?: WorkflowFilters): WorkflowDefinition[];

  // Instance management
  start_workflow(workflow_name: string, inputs: any): InstanceId;
  pause_workflow(instance_id: InstanceId): void;
  resume_workflow(instance_id: InstanceId): void;
  cancel_workflow(instance_id: InstanceId): void;

  // Status and monitoring
  get_instance_status(instance_id: InstanceId): InstanceStatus;
  get_instance_history(instance_id: InstanceId): StepExecution[];
  list_active_instances(filters?: InstanceFilters): WorkflowInstance[];

  // Team integration
  get_team_tasks(team_id: string): WorkflowTask[];
  claim_task(task_id: TaskId, team_id: string): Task;
  complete_task(task_id: TaskId, output: any): void;
  fail_task(task_id: TaskId, error: any): void;

  // Analytics
  get_workflow_metrics(workflow_name: string): WorkflowMetrics;
  get_bottlenecks(timeframe: string): BottleneckAnalysis[];
}
```

## Execution Engine

### State Machine Approach

```python
class WorkflowExecutor:
    """Core workflow execution engine"""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.instance = self.load_instance()
        self.definition = self.load_definition()
        self.context = WorkflowContext(self.instance.context)

    async def execute(self):
        """Main execution loop"""

        try:
            while not self.is_complete():
                # Get next steps to execute
                next_steps = self.get_next_steps()

                if not next_steps:
                    await self.wait_for_events()
                    continue

                # Execute steps (potentially in parallel)
                await self.execute_steps(next_steps)

                # Update workflow state
                self.update_state()

                # Check for completion
                if self.check_completion():
                    await self.complete_workflow()

        except Exception as e:
            await self.handle_error(e)

    async def execute_steps(self, steps: List[Step]):
        """Execute workflow steps"""

        tasks = []
        for step in steps:
            if step.type == 'task':
                task = self.execute_task_step(step)
            elif step.type == 'parallel':
                task = self.execute_parallel_step(step)
            elif step.type == 'condition':
                task = self.execute_condition_step(step)
            elif step.type == 'loop':
                task = self.execute_loop_step(step)
            else:
                raise ValueError(f"Unknown step type: {step.type}")

            tasks.append(task)

        # Wait for all steps to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results
        for step, result in zip(steps, results):
            if isinstance(result, Exception):
                await self.handle_step_error(step, result)
            else:
                await self.handle_step_success(step, result)
```

## Team Integration Pattern

### How Teams Interact with Workflows

```python
# In each team's agent code
class WorkflowAwareAgent:
    """Mixin for workflow integration"""

    def __init__(self):
        self.workflow_client = WorkflowMCPClient()

    async def check_workflow_tasks(self):
        """Periodically check for workflow tasks"""

        tasks = await self.workflow_client.get_team_tasks(self.team_id)

        for task in tasks:
            if self.can_handle_task(task):
                # Claim the task
                claimed = await self.workflow_client.claim_task(
                    task.id,
                    self.team_id
                )

                if claimed:
                    await self.execute_workflow_task(claimed)

    async def execute_workflow_task(self, task: WorkflowTask):
        """Execute a task from a workflow"""

        try:
            # Execute based on task type
            if task.task_type == 'validate_customer_data':
                result = await self.validate_customer_data(task.input_data)
            elif task.task_type == 'create_account':
                result = await self.create_account(task.input_data)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            # Report success
            await self.workflow_client.complete_task(task.id, result)

        except Exception as e:
            # Report failure
            await self.workflow_client.fail_task(task.id, str(e))
```

## Example Workflows

### 1. Product Launch Workflow
```yaml
name: product-launch
steps:
  - parallel:
    - marketing-team: create_launch_campaign
    - engineering-team: prepare_deployment
    - support-team: create_documentation
  - executive-team: final_approval
  - parallel:
    - marketing-team: execute_campaign
    - engineering-team: deploy_product
  - analytics-team: monitor_launch_metrics
```

### 2. Incident Response Workflow
```yaml
name: incident-response
inputs:
  severity: critical
steps:
  - ops-team: assess_incident
  - condition: ${severity == 'critical'}
    if_true:
      - executive-team: notify_leadership
  - parallel:
    - engineering-team: investigate_root_cause
    - support-team: communicate_with_customers
  - engineering-team: implement_fix
  - qa-team: verify_fix
  - ops-team: close_incident
```

### 3. Customer Complaint Resolution
```yaml
name: complaint-resolution
steps:
  - support-team: categorize_complaint
  - condition: ${category == 'technical'}
    if_true:
      - engineering-team: investigate_issue
    if_false:
      - customer-success-team: handle_complaint
  - loop:
    condition: ${!customer_satisfied}
    steps:
      - support-team: propose_resolution
      - approval: customer_approval
  - finance-team: process_compensation
  - analytics-team: update_metrics
```

## Monitoring and Visualization

### Workflow Dashboard
```
┌─────────────────────────────────────────────┐
│         Active Workflows Dashboard          │
├─────────────────────────────────────────────┤
│ Running: 24  Completed: 156  Failed: 3     │
├─────────────────────────────────────────────┤
│ customer-onboarding-001  ████████░░ 80%    │
│   └─ Current: setup_accounts (parallel)     │
│                                             │
│ product-launch-002       ████░░░░░░ 40%    │
│   └─ Waiting: executive approval            │
│                                             │
│ incident-response-003    ██████████ 100%   │
│   └─ Completed in 45 minutes                │
└─────────────────────────────────────────────┘
```

## Benefits

1. **Complex Orchestration**: Handle multi-team processes with ease
2. **Visibility**: Complete view of process state and history
3. **Error Handling**: Robust retry and fallback mechanisms
4. **Parallelism**: Execute independent steps simultaneously
5. **Flexibility**: Conditional logic and dynamic routing
6. **Reusability**: Define once, run many times
7. **Analytics**: Identify bottlenecks and optimize

## Implementation Roadmap

### Phase 1: Core Engine (Week 1-2)
- Workflow definition parser
- Basic execution engine
- Database schema implementation
- Simple task assignment

### Phase 2: Team Integration (Week 3-4)
- MCP server implementation
- Team task queue
- Workflow-aware agent mixin
- Basic monitoring

### Phase 3: Advanced Features (Week 5-6)
- Parallel execution
- Conditional logic
- Loop support
- Sub-workflows

### Phase 4: Production Features (Week 7-8)
- Error handling strategies
- Retry mechanisms
- Monitoring dashboard
- Performance optimization

## Conclusion

This workflow engine would increase autonomy by 5-6% by enabling complex business processes to run without human coordination. Teams would work together seamlessly on multi-step processes, with full visibility and control.
