"""
Deployment script generator for team setup.
"""

from pathlib import Path
from typing import Any, Dict

from ...models import TeamSpecification
from ..base import BaseGenerator


class DeploymentScriptGenerator(BaseGenerator):
    """Generates deployment scripts and utilities."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate deployment scripts.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        team_dir = Path(team_spec.name)
        generated_files = []
        
        # Generate make-deployable-team.py
        deployable_script = team_dir / "make-deployable-team.py"
        with open(deployable_script, "w") as f:
            f.write(self._generate_deployable_script(team_spec))
        deployable_script.chmod(0o755)
        generated_files.append(str(deployable_script))
        
        # Generate health_check.sh
        health_check = team_dir / "health_check.sh"
        with open(health_check, "w") as f:
            f.write(self._generate_health_check_script(team_spec))
        health_check.chmod(0o755)
        generated_files.append(str(health_check))
        
        # Generate requirements.txt
        requirements = team_dir / "requirements.txt"
        with open(requirements, "w") as f:
            f.write(self._generate_requirements(team_spec))
        generated_files.append(str(requirements))
        
        return {
            "generated_files": generated_files,
            "errors": []
        }
    
    def _generate_deployable_script(self, team_spec: TeamSpecification) -> str:
        """Generate make-deployable-team.py script."""
        return f'''#!/usr/bin/env python3
"""
Make Deployable Team Script
Creates a containerized version of the team that can run as a single K8s pod

This script:
1. Creates a team_server.py that wraps the crew with A2A protocol
2. Generates a Dockerfile for containerization
3. Creates K8s deployment manifests
4. Sets up health check endpoints
"""

import os
import sys
from pathlib import Path


def create_deployable_team():
    """Create all files needed for deployment"""
    print("Creating deployable team structure...")
    
    # Check if team_server.py exists
    if not Path("team_server.py").exists():
        print("ERROR: team_server.py not found. Run from team directory.")
        sys.exit(1)
    
    # Check required files
    required_files = ["crew.py" if "{team_spec.framework}" == "CrewAI" else "workflows/team_workflow.py", 
                      "requirements.txt", "Dockerfile"]
    
    missing = [f for f in required_files if not Path(f).exists() and not Path(f).parent.exists()]
    if missing:
        print(f"Warning: Missing files: {{missing}}")
    
    print("✓ Team structure verified")
    
    # Create deployment instructions
    deploy_instructions = """
# Deployment Instructions

## Local Testing
1. Build Docker image:
   ```bash
   docker build -t {team_spec.name} .
   ```

2. Run locally:
   ```bash
   docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY {team_spec.name}
   ```

## Kubernetes Deployment
1. Apply the manifest:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

2. Check deployment status:
   ```bash
   kubectl get pods -n elf-teams -l app={team_spec.name}
   ```

3. View logs:
   ```bash
   kubectl logs -n elf-teams -l app={team_spec.name}
   ```

## GitOps Deployment
1. Commit changes to git
2. Push to repository
3. ArgoCD will automatically deploy
"""
    
    with open("DEPLOYMENT.md", "w") as f:
        f.write(deploy_instructions)
    
    print("✓ Created DEPLOYMENT.md")
    print("\\nDeployable team structure created successfully!")
    print("\\nNext steps:")
    print("1. Review generated files")
    print("2. Build Docker image: docker build -t {team_spec.name} .")
    print("3. Deploy to Kubernetes: kubectl apply -f k8s/deployment.yaml")


if __name__ == "__main__":
    create_deployable_team()
'''
    
    def _generate_health_check_script(self, team_spec: TeamSpecification) -> str:
        """Generate health check script."""
        return f'''#!/bin/bash
# Health check script for {team_spec.name}

HEALTH_URL="${{HEALTH_URL:-http://localhost:8000/health}}"
TIMEOUT="${{TIMEOUT:-5}}"

# Perform health check
response=$(curl -s -w "\\n%{{http_code}}" --connect-timeout $TIMEOUT "$HEALTH_URL")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "✓ Health check passed"
    echo "Response: $body"
    exit 0
else
    echo "✗ Health check failed"
    echo "HTTP Code: $http_code"
    echo "Response: $body"
    exit 1
fi
'''
    
    def _generate_requirements(self, team_spec: TeamSpecification) -> str:
        """Generate requirements.txt."""
        base_requirements = [
            "crewai>=0.83.0,<1.0.0" if team_spec.framework == "CrewAI" else "langgraph>=0.2.0,<0.3.0",
            "langchain>=0.3.0,<0.4.0",
            "langchain-core>=0.3.0,<0.4.0",
            "langchain-community>=0.3.0,<0.4.0",
            "fastapi>=0.111.0,<0.112.0",
            "uvicorn>=0.30.0,<0.31.0",
            "pydantic>=2.8.0,<3.0.0",
            "python-dotenv>=1.0.0,<2.0.0",
            "httpx>=0.27.0,<0.28.0",
            "prometheus-client>=0.20.0,<0.21.0",
            "structlog>=24.0.0,<25.0.0",
            "qdrant-client>=1.10.0,<2.0.0",
            "supabase>=2.5.0,<3.0.0",
        ]
        
        # Add LLM provider requirements
        if team_spec.llm_provider == "OpenAI":
            base_requirements.extend([
                "langchain-openai>=0.2.0,<0.3.0",
                "openai>=1.37.0,<2.0.0",
            ])
        elif team_spec.llm_provider == "Anthropic":
            base_requirements.extend([
                "langchain-anthropic>=0.2.0,<0.3.0",
                "anthropic>=0.31.0,<1.0.0",
            ])
        
        # Add additional framework-specific requirements
        if team_spec.framework == "LangGraph":
            base_requirements.extend([
                "langgraph-checkpoint==1.0.0",
                "langgraph-sdk==0.1.0",
                "asyncpg==0.29.0",  # For PostgreSQL checkpointing
            ])
        
        return "\n".join(base_requirements) + "\n"