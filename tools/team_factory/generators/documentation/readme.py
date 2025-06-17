"""
README generator for teams.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ...models import TeamSpecification
from ..base import BaseGenerator


class ReadmeGenerator(BaseGenerator):
    """Generates README documentation for teams."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate README documentation.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        team_dir = Path(team_spec.name)
        readme_path = team_dir / "README.md"

        # Generate README content
        readme_content = self._generate_readme_content(team_spec)

        # Write file
        with open(readme_path, "w") as f:
            f.write(readme_content)

        return {"generated_files": [str(readme_path)], "errors": []}

    def _generate_readme_content(self, team_spec: TeamSpecification) -> str:
        """Generate README content."""
        # Process type based on team size
        process_type = "Hierarchical" if len(team_spec.members) >= 5 else "Sequential"

        # Team member table
        member_rows = []
        for member in team_spec.members:
            role_marker = " (Manager)" if member.is_manager else ""
            responsibilities = ", ".join(member.responsibilities[:3])
            member_rows.append(
                f"| {member.role}{role_marker} | {member.personality} | {responsibilities} |"
            )

        members_table = "\n".join(member_rows)

        # Sub-teams section if applicable
        sub_teams_section = ""
        if team_spec.sub_team_recommendations:
            sub_team_items = []
            for sub in team_spec.sub_team_recommendations:
                sub_team_items.append(
                    f"- **{sub.name}** ({sub.size} members): {sub.purpose}"
                )
            sub_teams_section = f"""
## Recommended Sub-Teams

As the team grows, consider creating these specialized sub-teams:

{chr(10).join(sub_team_items)}
"""

        return f"""# {team_spec.name.replace("-", " ").title()}

## Overview

**Purpose**: {team_spec.purpose}

**Framework**: {team_spec.framework}
**Department**: {team_spec.department}
**Reports To**: {team_spec.reporting_to}
**Created**: {datetime.now().strftime("%Y-%m-%d")}

## Team Composition

| Role | Personality | Key Responsibilities |
|------|-------------|----------------------|
{members_table}

**Team Size**: {len(team_spec.members)} members
**Process Type**: {process_type}

## Technical Details

### LLM Configuration
- **Provider**: {team_spec.llm_provider}
- **Model**: {team_spec.llm_model}
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
   ```

3. **Run the team**:
   ```bash
   python team_server.py
   ```

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t {team_spec.name} .
   ```

2. **Run locally**:
   ```bash
   docker run -p 8000:8000 \\
     -e OPENAI_API_KEY=$OPENAI_API_KEY \\
     {team_spec.name}
   ```

### Kubernetes Deployment

1. **Apply the manifest**:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

2. **Check status**:
   ```bash
   kubectl get pods -n elf-teams -l app={team_spec.name}
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /task` - Submit task via A2A protocol
- `GET /capabilities` - List team capabilities
- `GET /status` - Current team status

## Team Communication

### Internal (Within Team)
- Natural language communication between agents
- Personality-driven interactions
- Logged to `logs/{team_spec.name}_communications.log`

### External (Between Teams)
- A2A protocol through manager agent only
- Structured task requests and responses
- Logged to `logs/{team_spec.name}_a2a.log`

## Memory & Learning

The team uses Qdrant for memory storage and implements:
- Experience storage and retrieval
- Pattern recognition from past tasks
- Continuous improvement through reflection
- Performance insights generation
{sub_teams_section}
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
curl -X POST http://localhost:8000/task \\
  -H "Content-Type: application/json" \\
  -d '{{"from_agent": "test", "to_agent": "{team_spec.name}-manager",
       "task_type": "request", "task_description": "Test task"}}'
```

## Troubleshooting

1. **LLM Quota Errors**: Check daily limits in `config/llm_config.yaml`
2. **Memory Connection**: Verify Qdrant service is accessible
3. **A2A Communication**: Check AgentGateway service status
4. **Deployment Issues**: Review pod logs with `kubectl logs`

---

Generated by Team Factory | Framework: {team_spec.framework} | LLM: {team_spec.llm_provider}
"""
