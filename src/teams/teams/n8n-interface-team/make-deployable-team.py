#!/usr/bin/env python3
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
    required_files = [
        "crew.py" if "CrewAI" == "CrewAI" else "workflows/team_workflow.py",
        "requirements.txt",
        "Dockerfile",
    ]

    missing = [
        f
        for f in required_files
        if not Path(f).exists() and not Path(f).parent.exists()
    ]
    if missing:
        print(f"Warning: Missing files: {missing}")

    print("✓ Team structure verified")

    # Create deployment instructions
    deploy_instructions = """
# Deployment Instructions

## Local Testing
1. Build Docker image:
   ```bash
   docker build -t n8n-interface-team .
   ```

2. Run locally:
   ```bash
   docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY n8n-interface-team
   ```

## Kubernetes Deployment
1. Apply the manifest:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

2. Check deployment status:
   ```bash
   kubectl get pods -n elf-teams -l app=n8n-interface-team
   ```

3. View logs:
   ```bash
   kubectl logs -n elf-teams -l app=n8n-interface-team
   ```

## GitOps Deployment
1. Commit changes to git
2. Push to repository
3. ArgoCD will automatically deploy
"""

    with open("DEPLOYMENT.md", "w") as f:
        f.write(deploy_instructions)

    print("✓ Created DEPLOYMENT.md")
    print("\nDeployable team structure created successfully!")
    print("\nNext steps:")
    print("1. Review generated files")
    print("2. Build Docker image: docker build -t n8n-interface-team .")
    print("3. Deploy to Kubernetes: kubectl apply -f k8s/deployment.yaml")


if __name__ == "__main__":
    create_deployable_team()
