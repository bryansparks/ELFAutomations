#!/usr/bin/env python3
"""
Automated Team Factory

Modified version of team_factory.py that accepts JSON input for automated team creation.
Used by the DevOps automation team to create teams without human interaction.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# Import from original team_factory
sys.path.append(str(Path(__file__).parent))
from team_factory import TeamFactory, sanitize_team_name


class AutomatedTeamFactory(TeamFactory):
    """Extended TeamFactory for automated operation"""

    def __init__(self, spec_file: Path, output_dir: Path = None):
        super().__init__()
        self.spec_file = spec_file
        self.output_dir = output_dir or Path.cwd()
        self.spec = self._load_spec()

    def _load_spec(self) -> Dict:
        """Load team specification from JSON file"""
        with open(self.spec_file) as f:
            return json.load(f)

    def create_team_automated(self) -> Dict:
        """Create team from specification without prompts"""

        # Validate specification
        required_fields = [
            "name",
            "description",
            "framework",
            "llm_provider",
            "department",
        ]
        for field in required_fields:
            if field not in self.spec:
                raise ValueError(f"Missing required field: {field}")

        # Set team configuration
        self.team_name = sanitize_team_name(self.spec["name"])
        self.team_description = self.spec["description"]
        self.framework = self.spec["framework"]
        self.llm_provider = self.spec["llm_provider"]
        self.llm_model = self.spec.get(
            "llm_model", "gpt-4" if self.llm_provider == "OpenAI" else "claude-3-opus"
        )
        self.placement = self.spec["department"]

        # Set department
        if "." in self.placement:
            self.department = self.placement.split(".")[0]
        else:
            self.department = self.placement

        # Create team structure
        print(f"Creating team: {self.team_name}")
        print(f"Framework: {self.framework}")
        print(f"Department: {self.department}")
        print(f"Placement: {self.placement}")

        # Create directory structure
        team_dir = self.output_dir / "teams" / self.team_name
        self._create_directory_structure(team_dir)

        # Generate agents from spec or use AI
        if "agents" in self.spec and self.spec["agents"]:
            self.agents = self._convert_spec_agents(self.spec["agents"])
        else:
            # Use AI to generate agents
            self.agents = self._generate_agents()

        # Create all files
        self._create_all_files(team_dir)

        # Register with team registry (if available)
        try:
            self._register_team()
            print("✓ Registered in Team Registry")
        except Exception as e:
            print(f"Warning: Could not register team: {e}")

        # Return results
        return {
            "success": True,
            "team_name": self.team_name,
            "team_dir": str(team_dir),
            "agents": [agent["role"] for agent in self.agents],
            "framework": self.framework,
            "department": self.department,
        }

    def _convert_spec_agents(self, spec_agents: List[Dict]) -> List[Dict]:
        """Convert specification agents to internal format"""

        agents = []
        for spec_agent in spec_agents:
            agent = {
                "role": spec_agent["role"],
                "goal": spec_agent.get(
                    "goal", f"Excel at {spec_agent['role']} responsibilities"
                ),
                "backstory": spec_agent.get(
                    "backstory", spec_agent.get("description", "")
                ),
                "is_manager": spec_agent.get("is_manager", False),
                "tools": spec_agent.get("tools", []),
                "llm_config": {
                    "provider": self.llm_provider,
                    "model": self.llm_model,
                    "temperature": 0.7,
                },
            }
            agents.append(agent)

        return agents

    def generate_pr_files(self) -> Dict[str, str]:
        """Generate all files and return as dict for PR creation"""

        # Create team
        result = self.create_team_automated()

        if not result["success"]:
            raise Exception("Team creation failed")

        # Collect all generated files
        files = {}
        team_dir = Path(result["team_dir"])

        for file_path in team_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.output_dir)
                with open(file_path, "r") as f:
                    files[str(relative_path)] = f.read()

        # Add K8s deployment manifest
        k8s_manifest = self._generate_k8s_manifest()
        files[f"k8s/teams/{self.team_name}/deployment.yaml"] = k8s_manifest

        return files

    def _generate_k8s_manifest(self) -> str:
        """Generate Kubernetes deployment manifest"""

        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {self.team_name}
  namespace: elf-teams
  labels:
    app: {self.team_name}
    department: {self.department}
    created-by: devops-automation
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {self.team_name}
  template:
    metadata:
      labels:
        app: {self.team_name}
    spec:
      containers:
      - name: {self.team_name}
        image: elf-automations/{self.team_name}:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
        env:
        - name: TEAM_NAME
          value: "{self.team_name}"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-credentials
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: {self.team_name}
  namespace: elf-teams
spec:
  selector:
    app: {self.team_name}
  ports:
  - port: 80
    targetPort: 8000
"""


def main():
    parser = argparse.ArgumentParser(description="Automated Team Factory")
    parser.add_argument(
        "--spec-file", required=True, help="Path to team specification JSON"
    )
    parser.add_argument("--output-dir", help="Output directory (default: current dir)")
    parser.add_argument("--pr-mode", action="store_true", help="Generate files for PR")

    args = parser.parse_args()

    spec_file = Path(args.spec_file)
    if not spec_file.exists():
        print(f"Error: Spec file not found: {spec_file}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()

    factory = AutomatedTeamFactory(spec_file, output_dir)

    try:
        if args.pr_mode:
            # Generate files for PR
            files = factory.generate_pr_files()

            # Save to output directory
            pr_output = output_dir / "pr_files"
            pr_output.mkdir(exist_ok=True)

            # Write files manifest
            manifest_file = pr_output / "files_manifest.json"
            with open(manifest_file, "w") as f:
                json.dump(files, f, indent=2)

            print(f"\n✓ Generated {len(files)} files for PR")
            print(f"✓ Files manifest saved to: {manifest_file}")

        else:
            # Normal team creation
            result = factory.create_team_automated()

            print("\n✓ Team created successfully!")
            print(f"  Name: {result['team_name']}")
            print(f"  Location: {result['team_dir']}")
            print(f"  Agents: {', '.join(result['agents'])}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
