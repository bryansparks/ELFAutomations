#!/usr/bin/env python3
"""
Enhanced Make Deployable Team Script
Updates existing teams to support WebSocket chat interfaces
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from supabase import Client, create_client

    from tools.team_factory.generators.infrastructure.fastapi_server import (
        FastAPIServerGenerator,
    )
    from tools.team_factory.models import TeamMember, TeamSpecification
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to run from the project root and install dependencies")
    sys.exit(1)


class TeamEnhancer:
    """Enhances existing teams with chat capabilities."""

    def __init__(self):
        """Initialize with Supabase client."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.server_generator = FastAPIServerGenerator()

    def get_team_info(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Fetch team info from Supabase."""
        try:
            result = (
                self.supabase.table("teams")
                .select("*")
                .eq("name", team_name)
                .single()
                .execute()
            )
            return result.data if result.data else None
        except Exception as e:
            print(f"Error fetching team info: {e}")
            return None

    def load_team_spec(self, team_dir: Path) -> Optional[TeamSpecification]:
        """Load team specification from existing team directory."""
        # Try to load from team_config.yaml
        config_file = team_dir / "config" / "team_config.yaml"
        if config_file.exists():
            import yaml

            with open(config_file) as f:
                config = yaml.safe_load(f)

            # Convert to TeamSpecification
            team_spec = TeamSpecification(
                name=config.get("team_name", team_dir.name),
                department=config.get("department", "general"),
                purpose=config.get("purpose", "Team purpose"),
                framework=config.get("framework", "CrewAI"),
                llm_provider=config.get("llm_provider", "openai"),
                llm_model=config.get("llm_model", "gpt-4"),
                members=[],  # Will populate from agents
            )

            # Load members from agents directory
            agents_dir = team_dir / "agents"
            if agents_dir.exists():
                for agent_file in agents_dir.glob("*.py"):
                    if agent_file.name == "__init__.py":
                        continue

                    # Extract agent info from file
                    agent_name = agent_file.stem
                    with open(agent_file) as f:
                        content = f.read()

                    # Simple extraction of role from file content
                    if 'role="' in content:
                        role_start = content.find('role="') + 6
                        role_end = content.find('"', role_start)
                        role = content[role_start:role_end]
                    else:
                        role = agent_name.replace("_", " ").title()

                    # Check if manager
                    is_manager = any(
                        term in role.lower()
                        for term in ["manager", "lead", "head", "director"]
                    )

                    team_spec.members.append(
                        TeamMember(name=agent_name, role=role, is_manager=is_manager)
                    )

            return team_spec

        return None

    def enhance_team(self, team_path: str, enable_chat: bool = None) -> bool:
        """
        Enhance a team with chat capabilities.

        Args:
            team_path: Path to the team directory
            enable_chat: Override chat enablement (if None, checks Supabase)

        Returns:
            True if successful, False otherwise
        """
        team_dir = Path(team_path).resolve()
        if not team_dir.exists():
            print(f"Team directory not found: {team_dir}")
            return False

        team_name = team_dir.name
        print(f"Enhancing team: {team_name}")

        # Get team info from Supabase
        team_info = self.get_team_info(team_name)

        # Load team specification
        team_spec = self.load_team_spec(team_dir)
        if not team_spec:
            print(f"Could not load team specification for {team_name}")
            return False

        # Update chat settings
        if enable_chat is not None:
            team_spec.enable_chat_interface = enable_chat
            team_spec.is_top_level = True  # Typically chat-enabled teams are top-level
        elif team_info:
            team_spec.enable_chat_interface = team_info.get(
                "enable_chat_interface", False
            )
            team_spec.is_top_level = team_info.get("is_top_level", False)
            team_spec.chat_config = team_info.get("chat_config", {})

        if not team_spec.enable_chat_interface:
            print(f"Chat interface not enabled for {team_name}")
            return False

        print(f"Chat interface enabled for {team_name}")

        # Backup existing team_server.py
        server_path = team_dir / "team_server.py"
        if server_path.exists():
            backup_path = team_dir / "team_server.py.backup"
            print(f"Backing up existing server to {backup_path}")
            import shutil

            shutil.copy(server_path, backup_path)

        # Generate new server with chat support
        print("Generating WebSocket-enabled server...")
        os.chdir(team_dir.parent)  # Change to teams directory
        result = self.server_generator.generate(team_spec)

        if result.get("errors"):
            print(f"Errors during generation: {result['errors']}")
            return False

        # Update requirements.txt if needed
        requirements_path = team_dir / "requirements.txt"
        if requirements_path.exists():
            with open(requirements_path, "r") as f:
                requirements = f.read()

            # Add WebSocket dependencies if not present
            new_deps = []
            if "websockets" not in requirements:
                new_deps.append("websockets>=10.0")
            if "python-jwt" not in requirements and "PyJWT" not in requirements:
                new_deps.append("PyJWT>=2.8.0")

            if new_deps:
                print(f"Adding dependencies: {', '.join(new_deps)}")
                with open(requirements_path, "a") as f:
                    f.write("\n" + "\n".join(new_deps) + "\n")

        # Update Kubernetes deployment if needed
        k8s_path = team_dir / "k8s" / "deployment.yaml"
        if k8s_path.exists():
            print("Updating Kubernetes deployment for WebSocket support...")
            import yaml

            with open(k8s_path, "r") as f:
                k8s_config = yaml.safe_load(f)

            # Find the deployment
            for doc in k8s_config if isinstance(k8s_config, list) else [k8s_config]:
                if doc and doc.get("kind") == "Deployment":
                    # Add WebSocket annotations
                    annotations = (
                        doc.get("spec", {})
                        .get("template", {})
                        .get("metadata", {})
                        .get("annotations", {})
                    )
                    annotations[
                        "nginx.ingress.kubernetes.io/proxy-read-timeout"
                    ] = "3600"
                    annotations[
                        "nginx.ingress.kubernetes.io/proxy-send-timeout"
                    ] = "3600"

                    if "metadata" not in doc["spec"]["template"]:
                        doc["spec"]["template"]["metadata"] = {}
                    if "annotations" not in doc["spec"]["template"]["metadata"]:
                        doc["spec"]["template"]["metadata"]["annotations"] = {}
                    doc["spec"]["template"]["metadata"]["annotations"].update(
                        annotations
                    )

                    # Add JWT_SECRET_KEY env var if not present
                    containers = (
                        doc.get("spec", {})
                        .get("template", {})
                        .get("spec", {})
                        .get("containers", [])
                    )
                    for container in containers:
                        env_vars = container.get("env", [])
                        if not any(e.get("name") == "JWT_SECRET_KEY" for e in env_vars):
                            env_vars.append(
                                {
                                    "name": "JWT_SECRET_KEY",
                                    "valueFrom": {
                                        "secretKeyRef": {
                                            "name": f"{team_name}-secrets",
                                            "key": "jwt-secret-key",
                                        }
                                    },
                                }
                            )
                            container["env"] = env_vars

            with open(k8s_path, "w") as f:
                yaml.dump(k8s_config, f, default_flow_style=False)

        print(f"✅ Successfully enhanced {team_name} with WebSocket chat support!")
        print("\nNext steps:")
        print(f"1. Review the updated team_server.py")
        print(f"2. Test locally: cd {team_dir} && python team_server.py")
        print(f"3. Rebuild Docker image: docker build -t {team_name} .")
        print(f"4. Deploy to Kubernetes")

        return True

    def enhance_all_top_level_teams(self) -> Dict[str, bool]:
        """Enhance all top-level teams with chat support."""
        # Query all top-level teams with chat enabled
        try:
            result = (
                self.supabase.table("teams")
                .select("name, enable_chat_interface")
                .eq("is_top_level", True)
                .eq("enable_chat_interface", True)
                .execute()
            )

            teams = result.data if result.data else []
            results = {}

            for team in teams:
                team_name = team["name"]
                # Look for team directory
                team_paths = [
                    PROJECT_ROOT / "teams" / team_name,
                    PROJECT_ROOT / "src" / "teams" / "teams" / team_name,
                ]

                team_dir = None
                for path in team_paths:
                    if path.exists():
                        team_dir = path
                        break

                if team_dir:
                    print(f"\n{'='*60}")
                    success = self.enhance_team(str(team_dir))
                    results[team_name] = success
                else:
                    print(f"Team directory not found for {team_name}")
                    results[team_name] = False

            return results

        except Exception as e:
            print(f"Error querying teams: {e}")
            return {}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhance teams with WebSocket chat support"
    )
    parser.add_argument("team_path", nargs="?", help="Path to team directory")
    parser.add_argument(
        "--all", action="store_true", help="Enhance all top-level teams"
    )
    parser.add_argument(
        "--enable-chat", action="store_true", help="Force enable chat interface"
    )
    parser.add_argument(
        "--disable-chat", action="store_true", help="Force disable chat interface"
    )

    args = parser.parse_args()

    enhancer = TeamEnhancer()

    if args.all:
        print("Enhancing all top-level teams with chat support...")
        results = enhancer.enhance_all_top_level_teams()

        print(f"\n{'='*60}")
        print("Summary:")
        for team, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {team}")

    elif args.team_path:
        enable_chat = None
        if args.enable_chat:
            enable_chat = True
        elif args.disable_chat:
            enable_chat = False

        success = enhancer.enhance_team(args.team_path, enable_chat)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
