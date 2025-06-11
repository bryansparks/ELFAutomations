#!/usr/bin/env python3
"""
Crew CLI - Tool for creating and managing teams in ElfAutomations
"""

import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class CrewCLI:
    """CLI tool for managing crews/teams in ElfAutomations"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.crews_dir = self.project_root / "agent-configs" / "crews"
        self.k8s_dir = self.project_root / "k8s" / "agents"

    def create_team(
        self,
        team_name: str,
        department: str,
        agents: List[str],
        description: str = "",
        namespace: str = "elf-automations",
    ) -> Dict:
        """Create a new team configuration"""

        # Ensure directories exist
        self.crews_dir.mkdir(parents=True, exist_ok=True)

        # Create team configuration
        team_config = {
            "apiVersion": "kagent.dev/v1alpha1",
            "kind": "Team",
            "metadata": {
                "name": team_name,
                "namespace": namespace,
                "labels": {
                    "agent-type": "distributed-crewai",
                    "app": "elf-automations",
                    "component": "team",
                    "department": department,
                    "version": "v1.0.0",
                },
            },
            "spec": {
                "description": description,
                "maxTurns": 10,
                "modelConfig": "default-model-config",
                "participants": agents,
                "roundRobinTeamConfig": {},
                "terminationCondition": {"maxMessageTermination": {"maxMessages": 20}},
            },
        }

        # Save team configuration
        team_file = self.crews_dir / f"{team_name}.yaml"
        with open(team_file, "w") as f:
            yaml.dump(team_config, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Created team configuration: {team_file}")
        return team_config

    def create_executive_team(self) -> Dict:
        """Create the Executive Team configuration"""
        print("🚀 Creating Executive Team...")

        # For now, just the chief-ai-agent for "hello world" test
        team_config = self.create_team(
            team_name="executive-team",
            department="executive",
            agents=["chief-ai-agent"],
            description="Executive leadership team responsible for strategic direction and company-wide coordination",
        )

        print("✅ Executive Team created successfully!")
        print(f"   - Team: executive-team")
        print(f"   - Agents: chief-ai-agent")
        print(f"   - Location: {self.crews_dir}/executive-team.yaml")

        return team_config

    def list_teams(self):
        """List all existing teams"""
        print("\n📋 Existing Teams:")
        if self.crews_dir.exists():
            for team_file in self.crews_dir.glob("*.yaml"):
                with open(team_file, "r") as f:
                    config = yaml.safe_load(f)
                    name = config["metadata"]["name"]
                    department = config["metadata"]["labels"].get(
                        "department", "unknown"
                    )
                    agents = config["spec"].get("participants", [])
                    print(f"   - {name} ({department}): {', '.join(agents)}")
        else:
            print("   No teams found.")


def main():
    parser = argparse.ArgumentParser(description="ElfAutomations Crew CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new team")
    create_parser.add_argument(
        "--executive", action="store_true", help="Create the Executive Team"
    )
    create_parser.add_argument("--name", help="Team name")
    create_parser.add_argument("--department", help="Department name")
    create_parser.add_argument("--agents", nargs="+", help="List of agents")
    create_parser.add_argument("--description", default="", help="Team description")

    # List command
    list_parser = subparsers.add_parser("list", help="List all teams")

    args = parser.parse_args()

    cli = CrewCLI()

    if args.command == "create":
        if args.executive:
            cli.create_executive_team()
        elif args.name and args.department and args.agents:
            cli.create_team(
                team_name=args.name,
                department=args.department,
                agents=args.agents,
                description=args.description,
            )
        else:
            create_parser.print_help()
    elif args.command == "list":
        cli.list_teams()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
