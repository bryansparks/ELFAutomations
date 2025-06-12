# DevOps Team Workflow Example

## Scenario: Data Visualization Gap

The system has identified that multiple projects need data visualization capabilities, but no current team has these skills.

## Step-by-Step Workflow

### 1. Gap Detection (Automatic)

```python
# Gap detected by monitoring unassigned tasks
gap = {
    "id": "gap-2025-01-22-viz",
    "type": "skill_gap",
    "required_skills": ["data-visualization", "d3.js", "react", "charts"],
    "affected_tasks": 8,
    "affected_projects": ["customer-analytics", "sales-dashboard", "metrics-platform"],
    "urgency": "high",
    "business_impact": "Cannot deliver visual analytics to stakeholders"
}
```

### 2. DevOps Team Receives Request

The DevOps automation team's gap analyzer detects this pattern and triggers team creation:

```python
# A2A message to DevOps team
message = {
    "type": "capability_gap_alert",
    "from": "project-management-system",
    "to": "devops-automation-team",
    "gap": gap,
    "recommendation": "create_new_team"
}
```

### 3. Team Specification Generation

The DevOps team analyzes the gap and generates a team specification:

```json
{
  "name": "data-visualization-team",
  "description": "Specialized team for creating interactive data visualizations and dashboards",
  "department": "engineering.frontend",
  "framework": "CrewAI",
  "llm_provider": "OpenAI",
  "llm_model": "gpt-4",
  "agents": [
    {
      "role": "Visualization Architect",
      "description": "Designs data visualization strategies and architectures",
      "is_manager": true,
      "skills": ["architecture", "data-viz", "d3.js"]
    },
    {
      "role": "Frontend Developer",
      "description": "Implements interactive visualizations using React and D3.js",
      "skills": ["react", "d3.js", "typescript"]
    },
    {
      "role": "UX Designer",
      "description": "Ensures visualizations are intuitive and user-friendly",
      "skills": ["ux-design", "accessibility", "user-research"]
    },
    {
      "role": "Data Engineer",
      "description": "Optimizes data pipelines for visualization performance",
      "skills": ["data-engineering", "sql", "performance"]
    }
  ],
  "estimated_monthly_cost": 200
}
```

### 4. Automated File Generation

The DevOps team runs the automated team factory:

```bash
# Inside the DevOps pod
python /workspace/tools/team_factory_automated.py \
  --spec-file /tmp/data-viz-team-spec.json \
  --output-dir /tmp/generated \
  --pr-mode
```

This generates:
- `teams/data-visualization-team/README.md`
- `teams/data-visualization-team/agents/*.py` (4 agent files)
- `teams/data-visualization-team/crew.py`
- `teams/data-visualization-team/Dockerfile`
- `teams/data-visualization-team/requirements.txt`
- `teams/data-visualization-team/config/team_config.yaml`
- `k8s/teams/data-visualization-team/deployment.yaml`

### 5. Pull Request Creation

The DevOps team creates a PR via GitHub API:

```python
# Branch name
branch = "auto/team-data-visualization-20250122-1430"

# PR title
title = "[Automated] Add data-visualization-team - 8 tasks blocked"

# PR body (see below)
```

### 6. Pull Request Content

```markdown
## Automated Team Creation Request

### 🚨 Capability Gap Detected
- **Gap ID**: gap-2025-01-22-viz
- **Type**: Skill Gap
- **Impact**: 8 tasks blocked across 3 projects
- **Skills Needed**: data-visualization, d3.js, react, charts

### 📊 Affected Projects
1. **customer-analytics** - Cannot create customer insight dashboards
2. **sales-dashboard** - Blocked on interactive sales visualizations
3. **metrics-platform** - Need real-time metric displays

### 👥 Proposed Team: data-visualization-team
- **Department**: engineering.frontend
- **Purpose**: Specialized team for creating interactive data visualizations
- **Framework**: CrewAI
- **Agents**: 4 (1 manager, 3 specialists)

### 🤖 Team Composition
| Role | Responsibilities | Key Skills |
|------|-----------------|------------|
| Visualization Architect (Manager) | Design viz strategies, coordinate team | architecture, data-viz, d3.js |
| Frontend Developer | Implement interactive visualizations | react, d3.js, typescript |
| UX Designer | Ensure intuitive, accessible designs | ux-design, accessibility |
| Data Engineer | Optimize data for visualization | data-engineering, sql, performance |

### 💰 Cost Estimate
- **LLM Usage**: ~$150/month (GPT-4)
- **Infrastructure**: ~$50/month (1 pod, 0.5 CPU, 1GB RAM)
- **Total**: ~$200/month

### 📁 Files Generated
All files were auto-generated using team templates:
- ✅ Team structure follows standard patterns
- ✅ Includes health/readiness endpoints
- ✅ A2A integration for manager agent
- ✅ Proper error handling and logging

### 🔍 Review Checklist
Please verify:
- [ ] No existing team can handle data visualization
- [ ] Team composition matches the need
- [ ] Cost is acceptable for the value provided
- [ ] Integration points with blocked projects are clear
- [ ] Security review (no special permissions needed)

### 🤝 Next Steps After Approval
1. Docker image will be built automatically
2. Team deploys via ArgoCD (ETA: 15 minutes)
3. Team Registry updated with new team
4. Team begins claiming visualization tasks
5. Blocked projects can resume progress

### 📈 Success Metrics
- Unblock 8 tasks within 24 hours
- Deliver first visualization within 1 week
- All 3 projects have working dashboards within 2 weeks

---
**Automation Details**
- Created by: `devops-automation-team`
- Timestamp: `2025-01-22T14:30:00Z`
- Tracking ID: `gap-2025-01-22-viz`
- Urgency: `HIGH` (3 projects blocked)

⚠️ **Human Review Required**: This PR was automatically generated. Please review the team composition and approve if appropriate.
```

### 7. Human Review Process

1. **Notification sent to**:
   - Slack: #team-creation-requests
   - Email: platform-team@elfautomations.com
   - Dashboard: Pending reviews widget

2. **Review SLA**: 2 hours for high-urgency requests

3. **Reviewer checks**:
   - Is the gap real?
   - Is the team composition appropriate?
   - Are there security concerns?
   - Is the cost justified?

### 8. Post-Approval Automation

Once approved and merged:

```bash
# ArgoCD detects new team in k8s/teams/
# Automatically:
1. Builds Docker image
2. Deploys to cluster
3. Updates Team Registry
4. Notifies project teams
```

### 9. Team Activation

Within 30 minutes of merge:

```python
# New team starts operating
data_viz_team = Team("data-visualization-team")

# Check for available work
tasks = await data_viz_team.find_available_work(
    skills=["data-visualization", "d3.js"]
)

# Start claiming tasks
for task in tasks[:3]:  # Start with 3 tasks
    await data_viz_team.claim_task(task.id)
```

### 10. Feedback Loop

The DevOps team monitors:
- Was the team successfully deployed?
- Did it start claiming appropriate tasks?
- Are projects unblocked?
- Is the team performing as expected?

## Benefits Demonstrated

1. **Speed**: From gap detection to PR in ~30 minutes
2. **Quality**: Consistent team structure and documentation
3. **Oversight**: Humans review but don't manually create
4. **Traceability**: Complete audit trail
5. **Adaptability**: System responds to real needs

## Security Boundaries

- DevOps team can only create PRs, not merge
- Limited to specific file paths (teams/*, k8s/teams/*)
- Cannot modify existing teams
- All actions logged and auditable
- Cost estimates prevent runaway spending

This workflow enables autonomous growth while maintaining control!
