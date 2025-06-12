# Workflow Engine - Real-World Example

## Scenario: AI Model Update Workflow

A new AI model needs to be evaluated, tested, and deployed across all teams. This requires coordination between multiple teams with dependencies, approvals, and rollback capabilities.

## The Workflow Definition

```yaml
name: ai-model-update
version: 1
description: Coordinate AI model updates across all teams
timeout: 72h

inputs:
  - name: model_info
    type: object
    schema:
      provider: string      # OpenAI, Anthropic
      model: string        # gpt-4-turbo, claude-3-opus
      reason: string       # Why updating
      urgency: string      # low, medium, high

outputs:
  - name: deployment_report
  - name: rollback_plan

# Workflow begins
steps:
  # Phase 1: Assessment
  - id: initial_assessment
    type: task
    team: engineering-team
    action: assess_model_compatibility
    inputs:
      model: ${inputs.model_info}
    outputs:
      compatibility_report: report
      estimated_cost_increase: cost_delta
    timeout: 2h

  # Phase 2: Cost approval if needed
  - id: check_cost_increase
    type: condition
    condition: ${steps.initial_assessment.outputs.cost_delta > 500}
    if_true:
      - id: cost_approval
        type: approval
        approvers:
          - team: executive-team
            role: cfo
        message: |
          Model update will increase monthly costs by $${steps.initial_assessment.outputs.cost_delta}.
          Current model: ${inputs.model_info.current_model}
          New model: ${inputs.model_info.model}
        timeout: 24h
        on_timeout: reject

  # Phase 3: Parallel testing
  - id: test_teams
    type: parallel
    continue_on: partial_success  # Continue even if some teams fail
    steps:
      - id: test_engineering
        type: task
        team: engineering-team
        action: test_model_performance
        inputs:
          model: ${inputs.model_info.model}
          test_suite: engineering_tasks

      - id: test_marketing
        type: task
        team: marketing-team
        action: test_content_quality
        inputs:
          model: ${inputs.model_info.model}
          test_cases: marketing_scenarios

      - id: test_sales
        type: task
        team: sales-team
        action: test_customer_interactions
        inputs:
          model: ${inputs.model_info.model}
          sample_conversations: true

  # Phase 4: Analyze test results
  - id: analyze_results
    type: task
    team: qa-team
    action: consolidate_test_results
    inputs:
      test_results:
        engineering: ${steps.test_engineering.outputs}
        marketing: ${steps.test_marketing.outputs}
        sales: ${steps.test_sales.outputs}
    outputs:
      recommendation: recommendation  # proceed, abort, partial
      risk_assessment: risks

  # Phase 5: Decision gate
  - id: deployment_decision
    type: condition
    condition: ${steps.analyze_results.outputs.recommendation == 'proceed'}
    if_true:
      steps:
        - id: create_rollback_plan
          type: task
          team: devops-automation-team
          action: prepare_rollback
          inputs:
            current_state: ${workflow.initial_state}
            target_state: ${inputs.model_info}
          outputs:
            rollback_plan: plan

        - id: staged_rollout
          type: sequence
          steps:
            # Stage 1: Dev teams
            - id: update_dev_teams
              type: parallel
              steps:
                - team: engineering-team
                  action: update_model_config
                - team: qa-team
                  action: update_model_config

            # Monitor for 2 hours
            - id: monitor_stage1
              type: task
              team: operations-team
              action: monitor_system_health
              inputs:
                duration: 2h
                alert_threshold: any_errors

            # Stage 2: Customer-facing teams
            - id: update_production_teams
              type: parallel
              steps:
                - team: sales-team
                  action: update_model_config
                - team: support-team
                  action: update_model_config
                - team: marketing-team
                  action: update_model_config

            # Final monitoring
            - id: monitor_stage2
              type: task
              team: operations-team
              action: monitor_system_health
              inputs:
                duration: 4h
                metrics: [response_time, error_rate, cost]

    if_false:
      steps:
        - id: document_rejection
          type: task
          team: engineering-team
          action: document_test_failures
          inputs:
            test_results: ${steps.analyze_results.outputs}
            model_info: ${inputs.model_info}

  # Phase 6: Final report
  - id: final_report
    type: task
    team: analytics-team
    action: generate_deployment_report
    inputs:
      workflow_history: ${workflow.history}
      model_info: ${inputs.model_info}
      final_status: ${workflow.status}
    outputs:
      report: deployment_report

# Error handling
error_handlers:
  - error_type: team_timeout
    action: retry
    max_attempts: 2
    then: escalate

  - error_type: test_failure
    action: custom
    handler:
      - id: emergency_rollback
        type: task
        team: devops-automation-team
        action: execute_rollback
        inputs:
          plan: ${steps.create_rollback_plan.outputs.plan}

  - error_type: critical_error
    action: notify
    recipients:
      - operations-team
      - executive-team
```

## Execution Walkthrough

### Starting the Workflow

```python
# Triggered by engineering team identifying new model
workflow_client = WorkflowMCPClient()

instance_id = await workflow_client.start_workflow(
    workflow_name="ai-model-update",
    inputs={
        "model_info": {
            "provider": "OpenAI",
            "current_model": "gpt-4",
            "model": "gpt-4-turbo",
            "reason": "Improved performance and cost efficiency",
            "urgency": "medium"
        }
    }
)

print(f"Started workflow: {instance_id}")
# Output: Started workflow: wf-2025-01-22-model-update-001
```

### Workflow Execution Log

```
[2025-01-22 10:00:00] Workflow started: ai-model-update
[2025-01-22 10:00:01] Step 'initial_assessment' assigned to engineering-team
[2025-01-22 10:15:32] engineering-team claimed task
[2025-01-22 10:45:12] Step 'initial_assessment' completed
  - Output: compatibility_report = "Compatible with minor config changes"
  - Output: cost_delta = 650

[2025-01-22 10:45:13] Condition 'check_cost_increase' evaluated: true (650 > 500)
[2025-01-22 10:45:14] Step 'cost_approval' waiting for CFO approval
[2025-01-22 11:30:22] CFO approved cost increase
[2025-01-22 11:30:23] Starting parallel step 'test_teams'
  - test_engineering assigned to engineering-team
  - test_marketing assigned to marketing-team
  - test_sales assigned to sales-team

[2025-01-22 12:00:00] test_engineering completed: PASS (performance +15%)
[2025-01-22 12:10:00] test_marketing completed: PASS (quality score 9.2/10)
[2025-01-22 12:05:00] test_sales completed: PARTIAL (2 failed scenarios)

[2025-01-22 12:10:01] Step 'analyze_results' assigned to qa-team
[2025-01-22 12:25:00] Step 'analyze_results' completed
  - Output: recommendation = "proceed"
  - Output: risks = ["Sales team needs retraining on 2 scenarios"]

[2025-01-22 12:25:01] Condition 'deployment_decision' evaluated: true
[2025-01-22 12:25:02] Step 'create_rollback_plan' assigned to devops-automation-team
[2025-01-22 12:30:00] Rollback plan created

[2025-01-22 12:30:01] Starting staged rollout
[2025-01-22 12:30:02] Stage 1: Updating dev teams
  - engineering-team: model updated
  - qa-team: model updated

[2025-01-22 12:30:30] Monitoring stage 1 for 2 hours
[2025-01-22 14:30:30] Stage 1 monitoring complete: No errors detected

[2025-01-22 14:30:31] Stage 2: Updating production teams
  - sales-team: model updated
  - support-team: model updated
  - marketing-team: model updated

[2025-01-22 14:31:00] Monitoring stage 2 for 4 hours
[2025-01-22 18:31:00] Stage 2 monitoring complete: All metrics normal

[2025-01-22 18:31:01] Step 'final_report' assigned to analytics-team
[2025-01-22 18:45:00] Final report generated
[2025-01-22 18:45:01] Workflow completed successfully
```

### Team Perspective: Engineering Team

```python
# In engineering team's agent
class EngineeringTeamAgent:
    async def check_workflow_tasks(self):
        """Check for workflow tasks"""

        tasks = await self.workflow_client.get_team_tasks("engineering-team")
        # Returns: [
        #   {
        #     "id": "task-001",
        #     "workflow_instance": "wf-2025-01-22-model-update-001",
        #     "action": "assess_model_compatibility",
        #     "input_data": {"provider": "OpenAI", "model": "gpt-4-turbo", ...},
        #     "deadline": "2025-01-22T12:00:00Z"
        #   }
        # ]

        for task in tasks:
            if task.action == "assess_model_compatibility":
                # Claim the task
                await self.workflow_client.claim_task(task.id, "engineering-team")

                # Perform assessment
                report = await self.assess_model_compatibility(task.input_data)

                # Return results to workflow
                await self.workflow_client.complete_task(
                    task.id,
                    output={
                        "compatibility_report": report.summary,
                        "cost_delta": report.estimated_cost_increase
                    }
                )
```

### Monitoring Dashboard View

```
┌─────────────────────────────────────────────────────────────┐
│                AI Model Update Workflow                      │
│                Instance: wf-2025-01-22-model-update-001     │
├─────────────────────────────────────────────────────────────┤
│ Status: RUNNING                                             │
│ Started: 2 hours ago                                        │
│ Progress: ███████████████░░░░░ 75%                        │
├─────────────────────────────────────────────────────────────┤
│ Steps:                                                      │
│ ✓ initial_assessment      (45 min)    engineering-team     │
│ ✓ cost_approval          (45 min)    CFO                   │
│ ✓ test_teams            (40 min)    [parallel]            │
│   ├─ ✓ test_engineering             engineering-team       │
│   ├─ ✓ test_marketing               marketing-team         │
│   └─ ⚠ test_sales                  sales-team (2 issues)  │
│ ✓ analyze_results        (15 min)    qa-team              │
│ ✓ create_rollback_plan   (5 min)     devops-team          │
│ ▶ staged_rollout         (running)   [sequence]            │
│   ├─ ✓ update_dev_teams             [complete]            │
│   ├─ ✓ monitor_stage1               operations-team       │
│   ├─ ✓ update_production_teams      [complete]            │
│   └─ ▶ monitor_stage2               operations-team (2h left) │
│ ⏸ final_report          (waiting)    analytics-team        │
├─────────────────────────────────────────────────────────────┤
│ Alerts: None                                                │
│ Est. Completion: 2 hours                                    │
└─────────────────────────────────────────────────────────────┘
```

### Database State During Execution

```sql
-- Current workflow instance
SELECT * FROM workflow_instances WHERE id = 'wf-2025-01-22-model-update-001';

-- Result:
{
  "id": "wf-2025-01-22-model-update-001",
  "workflow_definition_id": "ai-model-update-v1",
  "status": "running",
  "current_step": "monitor_stage2",
  "context": {
    "model_info": {
      "provider": "OpenAI",
      "model": "gpt-4-turbo",
      ...
    },
    "steps": {
      "initial_assessment": {
        "outputs": {
          "compatibility_report": "Compatible with minor config changes",
          "cost_delta": 650
        }
      },
      ...
    }
  },
  "started_at": "2025-01-22 10:00:00",
  "completed_at": null
}

-- Active team tasks
SELECT * FROM workflow_team_tasks
WHERE instance_id = 'wf-2025-01-22-model-update-001'
AND status = 'pending';

-- Result: Currently empty (all tasks claimed/completed)
```

## Benefits Demonstrated

1. **Complex Coordination**: 6 teams working together seamlessly
2. **Conditional Logic**: Cost approval only when needed
3. **Parallel Execution**: Testing happens simultaneously
4. **Staged Rollout**: Reduces risk with gradual deployment
5. **Error Handling**: Rollback plan ready if needed
6. **Full Visibility**: Every step tracked and auditable
7. **Asynchronous**: Teams work at their own pace

## Key Insights

### For Simple Tasks
- Direct A2A messages work fine
- No need for workflow overhead

### For Complex Processes
- Workflow engine provides structure
- Dependencies are explicit
- Error handling is robust
- Progress is visible

### Integration Pattern
- Teams poll for workflow tasks
- Claim tasks they can handle
- Complete with outputs
- Workflow engine orchestrates

This example shows how the workflow engine enables sophisticated multi-team coordination that would be impossible with simple A2A messages!
