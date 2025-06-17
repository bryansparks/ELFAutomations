# DevOps Automation Team - Implementation Plan

## Quick Start Prototype

### Step 1: Create the DevOps Team Structure

```bash
# Create team with special capabilities
cd tools
python team_factory.py

# Inputs:
# Description: "DevOps automation team that creates new teams via GitHub PRs when capability gaps are identified"
# Framework: CrewAI
# Provider: OpenAI
# Department: infrastructure.automation
```

### Step 2: Add Special Tools

The DevOps team needs tools that aren't typical for other teams:

```python
# teams/devops-automation-team/tools/team_creation_tools.py

import subprocess
import json
from pathlib import Path
from github import Github
from typing import Dict, List

class TeamCreationTools:
    """Tools for automated team creation"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_PR_TOKEN")
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo("bryansparks/ELFAutomations")

    def create_team_specification(self, gap_analysis: Dict) -> Dict:
        """Generate team spec from capability gap"""

        return {
            "name": self._generate_team_name(gap_analysis),
            "description": gap_analysis["gap_description"],
            "framework": "CrewAI",  # Default, could be dynamic
            "llm_provider": "OpenAI",
            "department": self._determine_department(gap_analysis),
            "agents": self._determine_agents(gap_analysis),
            "skills": gap_analysis.get("required_skills", [])
        }

    def run_team_factory(self, spec: Dict) -> List[str]:
        """Run team factory with automated inputs"""

        # Save spec to temp file
        spec_file = Path("/tmp/team_spec.json")
        spec_file.write_text(json.dumps(spec))

        # Run team factory in non-interactive mode
        cmd = [
            "python",
            "/workspace/tools/team_factory.py",
            "--spec-file", str(spec_file),
            "--output-dir", "/tmp/generated_team"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Team factory failed: {result.stderr}")

        # Return list of generated files
        generated_files = []
        output_dir = Path("/tmp/generated_team")
        for file in output_dir.rglob("*"):
            if file.is_file():
                generated_files.append(str(file))

        return generated_files

    def create_pull_request(self, branch_name: str, files: Dict[str, str],
                          title: str, body: str) -> str:
        """Create PR with generated team files"""

        # Create branch
        base_branch = self.repo.get_branch("main")
        self.repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_branch.commit.sha
        )

        # Add files to branch
        for file_path, content in files.items():
            self.repo.create_file(
                path=file_path,
                message=f"Add {file_path}",
                content=content,
                branch=branch_name
            )

        # Create pull request
        pr = self.repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="main"
        )

        # Add labels
        pr.add_to_labels("automated", "new-team", "needs-review")

        return pr.html_url
```

### Step 3: Create Gap Detection Integration

```python
# teams/devops-automation-team/agents/gap_analyzer.py

from typing import Dict, Optional
from crewai import Agent

def gap_analyzer_agent():
    """Agent that monitors for capability gaps"""

    return Agent(
        role="Capability Gap Analyzer",
        goal="Monitor the system for capability gaps and recommend new teams",
        backstory="""You analyze requests and failures across the ElfAutomations
        system to identify when new capabilities are needed. You look for patterns
        like repeated failures, unhandled requests, or explicit capability requests.""",
        tools=[
            analyze_team_registry,
            check_failed_requests,
            analyze_project_requirements,
            estimate_team_cost
        ],
        verbose=True
    )

# Example gap detection
async def detect_capability_gaps():
    """Scan for gaps in current capabilities"""

    gaps = []

    # Check unassigned tasks requiring specific skills
    unassigned_tasks = await supabase.table('pm_tasks').select(
        '*, project:pm_projects(name)'
    ).eq('status', 'ready').is_('assigned_team', 'null').execute()

    # Group by required skills
    skill_gaps = {}
    for task in unassigned_tasks.data:
        skills = task.get('required_skills', [])
        for skill in skills:
            if skill not in skill_gaps:
                skill_gaps[skill] = []
            skill_gaps[skill].append(task)

    # Identify significant gaps
    for skill, tasks in skill_gaps.items():
        if len(tasks) >= 3:  # 3+ tasks need this skill
            gaps.append({
                "type": "skill_gap",
                "skill": skill,
                "task_count": len(tasks),
                "urgency": "high" if any(t['project']['priority'] == 'critical'
                                       for t in tasks) else "medium",
                "description": f"No team has {skill} capability, {len(tasks)} tasks blocked"
            })

    return gaps
```

### Step 4: Create the Orchestrator

```python
# teams/devops-automation-team/agents/automation_orchestrator.py

from typing import Dict
from crewai import Agent
from datetime import datetime

def automation_orchestrator_agent():
    """Manager agent that orchestrates team creation"""

    return Agent(
        role="DevOps Automation Orchestrator",
        goal="Coordinate the automated creation of new teams via GitHub PRs",
        backstory="""You are the manager of the DevOps automation team. When
        capability gaps are identified, you coordinate the creation of new teams
        by generating specifications, running automation tools, and creating
        pull requests for human review.""",
        tools=[
            create_team_specification,
            run_team_factory,
            create_pull_request,
            notify_humans,
            track_pr_status
        ],
        verbose=True,
        allow_delegation=True
    )

async def handle_gap(self, gap: Dict) -> Dict:
    """Handle identified capability gap"""

    # 1. Validate gap is significant
    if not self._is_gap_significant(gap):
        return {"status": "ignored", "reason": "Gap not significant"}

    # 2. Check if existing team can be enhanced
    existing_team = await self._find_similar_team(gap)
    if existing_team:
        return await self._enhance_existing_team(existing_team, gap)

    # 3. Create new team specification
    team_spec = await self.create_team_specification(gap)

    # 4. Estimate costs
    cost_estimate = await self.estimate_team_cost(team_spec)
    if cost_estimate["monthly_cost"] > 1000:  # $1000/month threshold
        return {"status": "requires_approval", "reason": "High cost team"}

    # 5. Create team via PR
    pr_url = await self.create_team_pr(team_spec, gap)

    # 6. Track the PR
    tracking_id = f"gap-{gap['id']}-team-{team_spec['name']}"
    await self.track_pr(pr_url, tracking_id)

    return {
        "status": "pr_created",
        "pr_url": pr_url,
        "tracking_id": tracking_id,
        "estimated_deployment": "2-4 hours after approval"
    }
```

### Step 5: Dockerfile with Dev Tools

```dockerfile
# teams/devops-automation-team/Dockerfile

FROM python:3.11-slim

# Install git and other dev tools
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install GitHub CLI for PR operations
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt update && apt install gh -y

# Copy team files
COPY . .

# Copy team/mcp factory tools
COPY --from=dev-tools /tools/team_factory.py /workspace/tools/
COPY --from=dev-tools /tools/mcp_factory.py /workspace/tools/

# Set up git config
RUN git config --global user.email "devops-team@elfautomations.ai" && \
    git config --global user.name "ElfAutomations DevOps Team"

CMD ["python", "crew.py"]
```

### Step 6: Minimal PR Creation Test

```python
# teams/devops-automation-team/test_pr_creation.py

#!/usr/bin/env python3
"""Test creating a PR for a new team"""

import os
from github import Github
from datetime import datetime

def test_pr_creation():
    """Test creating a simple PR"""

    # Setup
    token = os.getenv("GITHUB_PR_TOKEN")
    if not token:
        print("Error: GITHUB_PR_TOKEN not set")
        return

    g = Github(token)
    repo = g.get_repo("bryansparks/ELFAutomations")

    # Create branch
    branch_name = f"auto/test-team-{datetime.now():%Y%m%d-%H%M%S}"
    base = repo.get_branch("main")

    try:
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base.commit.sha
        )
        print(f"✓ Created branch: {branch_name}")

        # Add a simple file
        content = """# Test Team

This is an automated test of team creation.

## Purpose
Testing the DevOps automation workflow.
"""

        repo.create_file(
            path=f"teams/test-team-auto/README.md",
            message="Add test team README",
            content=content,
            branch=branch_name
        )
        print("✓ Added README file")

        # Create PR
        pr = repo.create_pull(
            title="[Test] Automated team creation",
            body="""## Automated Team Creation Test

This is a test PR created by the DevOps automation team.

**This PR can be closed without merging.**

### Testing:
- [x] Branch creation
- [x] File addition
- [x] PR creation
- [ ] Human review
""",
            head=branch_name,
            base="main"
        )

        pr.add_to_labels("test", "automated")
        print(f"✓ Created PR: {pr.html_url}")

        return pr.html_url

    except Exception as e:
        print(f"✗ Error: {e}")
        return None

if __name__ == "__main__":
    test_pr_creation()
```

## Deployment Strategy

### Phase 1: Local Testing
1. Create DevOps team locally
2. Test PR creation with limited token
3. Verify file generation works
4. Test notification system

### Phase 2: Staging Deployment
1. Deploy to K8s with restricted permissions
2. Test gap detection on historical data
3. Create test PRs (not merged)
4. Refine based on results

### Phase 3: Production Rollout
1. Enable for low-risk gaps only
2. Require human approval for all PRs
3. Monitor for 2 weeks
4. Gradually increase automation

## Key Constraints

1. **No Direct Git Push**: Only PRs, never direct commits
2. **Human Review Required**: All PRs need approval
3. **Rate Limited**: Max 5 teams per day
4. **Cost Awareness**: Estimate and report costs
5. **Audit Everything**: Full trail of decisions

## Success Metrics

- Time from gap identified to PR created: < 30 minutes
- PR quality (requires changes): < 20%
- False positive rate: < 10%
- Human review time: < 2 hours
- Successful deployments: > 90%

## Next Steps

1. Create minimal DevOps team
2. Set up GitHub token with PR permissions
3. Test PR creation workflow
4. Add gap detection logic
5. Deploy to staging environment
