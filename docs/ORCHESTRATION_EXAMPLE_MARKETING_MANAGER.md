# Orchestration in Action: Marketing Manager Example

## Scenario

The CEO sends a request to the Marketing Manager:

> "We need to launch a comprehensive awareness campaign for our new AI-powered analytics feature. This should include content creation, social media, email campaigns, webinars, and coordination with sales for lead handoff. We want to track ROI carefully. This is high priority - we're announcing at the conference in 3 weeks."

## How the Marketing Manager Processes This

### Step 1: Initial Analysis

The Marketing Manager's enhanced prompt includes the orchestration framework, so they immediately begin analyzing:

```python
# Marketing Manager's Internal Process
orchestration_advisor = OrchestrationAdvisor()

decision = orchestration_advisor.analyze_request(
    request=ceo_request,
    context={
        "team_id": "marketing-team",
        "available_sub_teams": ["content-team", "social-media-team", "email-team", "events-team"],
        "current_workload": "moderate",
        "deadline": "3 weeks"
    }
)
```

### Step 2: Complexity Assessment

The advisor analyzes the request:

```yaml
Complexity Factors:
  estimated_hours: 120  # 3 weeks, multiple deliverables
  team_count: 6  # marketing + sub-teams + sales
  skill_count: 8  # writing, design, video, social, email, analytics, events, sales
  dependency_type: complex  # content must be created before distribution
  approval_count: 2  # CEO approval on messaging, sales approval on handoff process
  error_impact: high  # conference announcement is public commitment
  visibility_required: high  # CEO priority, public announcement
  has_conditional_logic: true  # lead scoring determines sales handoff
  requires_parallel_execution: true  # multiple channels simultaneously
```

### Step 3: Decision Output

```yaml
Decision: workflow_engine
Confidence: 0.95

Reasoning:
  - "6 teams required - complex coordination needed"
  - "High error impact requires robust error handling of workflow engine"
  - "Parallel execution required - workflow engine recommended"
  - "Conditional logic present - workflow engine provides best support"
  - "Matches 'product_launch' pattern - typically handled with this approach"

Key Considerations:
  - "Requires coordination across marketing, content, social, email, events, sales"
  - "Has formal approval gates"
  - "Needs staged rollout capability"
  - "High visibility to executives"
```

### Step 4: Workflow Decomposition

The advisor provides a suggested workflow structure:

```yaml
workflow_name: ai-analytics-feature-awareness-campaign
estimated_duration: 120 hours (3 weeks)

phases:
  - name: Strategy & Planning
    type: sequential
    steps:
      - marketing-manager: Define campaign strategy and key messages
      - marketing-manager: Get CEO approval on messaging
      - marketing-manager: Create content calendar and channel plan

  - name: Content Creation
    type: parallel
    steps:
      - content-team: Create blog posts and whitepapers
      - content-team: Develop webinar content and slides
      - social-media-team: Create social media assets
      - email-team: Design email templates and sequences
      - events-team: Prepare conference materials

  - name: Review & Refinement
    type: sequential
    steps:
      - marketing-manager: Review all content
      - marketing-manager: Get final CEO approval
      - sales-team: Review and approve lead handoff process

  - name: Campaign Launch
    type: parallel
    steps:
      - content-team: Publish blog posts
      - social-media-team: Launch social campaign
      - email-team: Begin email sequence
      - events-team: Schedule and promote webinars

  - name: Lead Management
    type: conditional
    condition: lead_score > 70
    if_true:
      - sales-team: High-value lead handoff
    if_false:
      - email-team: Nurture sequence

  - name: Monitoring & Optimization
    type: continuous
    steps:
      - analytics-team: Track campaign metrics
      - marketing-manager: Daily performance review
      - all-teams: Optimize based on data
```

### Step 5: Marketing Manager's Actions

Based on the analysis, the Marketing Manager:

```python
# 1. Creates the workflow
workflow_instance = await workflow_client.start_workflow(
    workflow_name="product-awareness-campaign",
    inputs={
        "product": "AI-powered analytics",
        "deadline": "2025-02-12",  # Conference date
        "budget": 50000,
        "success_metrics": {
            "leads_generated": 500,
            "webinar_attendees": 200,
            "social_engagement": 10000
        }
    }
)

# 2. Communicates the plan
await a2a_client.send_message(
    to="ceo",
    message={
        "type": "campaign_plan_created",
        "workflow_id": workflow_instance,
        "approach": "workflow_engine",
        "reasoning": decision.reasoning,
        "timeline": "3 weeks with parallel execution",
        "first_approval_needed": "Campaign messaging by EOD tomorrow"
    }
)

# 3. Monitors execution
# The workflow engine now handles:
# - Task assignment to sub-teams
# - Dependency management
# - Progress tracking
# - Error handling
# - Conditional lead routing
```

## Alternative Scenarios

### Scenario A: Simple Request

CEO: "Write a blog post about our new feature"

**Analysis Result**:
- Decision: `direct_delegation`
- Reasoning: "Task estimated at 2.0 hours - suitable for direct handling"
- Action: Marketing Manager delegates directly to content team

### Scenario B: Medium Complexity

CEO: "Create a customer case study with testimonials and ROI data"

**Analysis Result**:
- Decision: `project_management`
- Reasoning: "Linear dependencies can be managed with project tracking"
- Action: Marketing Manager creates project with tasks for interview, writing, design, approval

## Key Insights

### What Made This Work

1. **Clear Decision Framework**: The manager didn't guess - they had clear criteria
2. **Pattern Recognition**: Previous product launches provided a template
3. **Appropriate Tool Selection**: Workflow engine handled the complexity perfectly
4. **Decomposition Skills**: Complex request became manageable phases

### Benefits Realized

1. **CEO Confidence**: Clear plan with reasoning builds trust
2. **Team Clarity**: Everyone knows their role and dependencies
3. **Risk Mitigation**: Error handling and approvals built in
4. **Progress Visibility**: Real-time tracking without constant check-ins
5. **Optimal Resource Use**: Parallel execution saves time

### Learning Loop

After the campaign:
```python
# Record outcome for future learning
await orchestration_advisor.record_outcome(
    decision_id=decision.id,
    outcome={
        "success": True,
        "actual_duration": 118,  # Slightly under estimate
        "team_satisfaction": 0.9,
        "rework_needed": False,
        "key_learning": "Parallel content creation worked well"
    }
)
```

This feeds back into the system, making future decisions even better.

## Conclusion

By embedding orchestration intelligence into manager agents, we transform them from simple delegators into sophisticated conductors who:
- Know when to use each tool
- Can justify their decisions
- Learn from experience
- Maximize team effectiveness

This is how we ensure the powerful capabilities we build actually get used appropriately!
