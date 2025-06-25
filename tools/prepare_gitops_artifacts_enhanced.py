#!/usr/bin/env python3
"""
Enhanced GitOps Artifact Preparer with MCP Support
This version includes:
1. MCP ConfigMap collection with AgentGateway labels
2. Dynamic AgentGateway configuration updates
3. Proper namespace handling for MCPs
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml
from rich.console import Console
from rich.table import Table

console = Console()


class EnhancedGitOpsArtifactPreparer:
    def __init__(self, teams_dir: Path, mcps_dir: Path, gitops_dir: Path):
        self.teams_dir = teams_dir
        self.mcps_dir = mcps_dir
        self.gitops_dir = gitops_dir
        self.teams_manifests_dir = gitops_dir / "manifests" / "teams"
        self.mcps_manifests_dir = gitops_dir / "manifests" / "mcps"
        self.agentgateway_dir = gitops_dir / "manifests" / "agentgateway"

        # Create directories
        self.teams_manifests_dir.mkdir(parents=True, exist_ok=True)
        self.mcps_manifests_dir.mkdir(parents=True, exist_ok=True)
        self.agentgateway_dir.mkdir(parents=True, exist_ok=True)

        # Track discovered MCPs for AgentGateway config update
        self.discovered_mcps = []

    def prepare_all_artifacts(self):
        """Collect all team and MCP manifests for GitOps deployment"""
        console.print("[bold cyan]🚀 Enhanced GitOps Artifact Preparation[/bold cyan]\n")

        # Prepare teams
        teams_collected = self._prepare_teams()

        # Prepare MCPs with AgentGateway integration
        mcps_collected = self._prepare_mcps()

        # Update AgentGateway configuration
        self._update_agentgateway_config()

        # Generate master Kustomization
        self._generate_master_kustomization(teams_collected, mcps_collected)

        # Generate ArgoCD Applications
        self._generate_argocd_apps()

        # Show summary
        self._show_summary(teams_collected, mcps_collected)

    def _prepare_teams(self) -> List[str]:
        """Prepare team manifests (unchanged from original)"""
        console.print("[yellow]📦 Processing Teams...[/yellow]")
        teams_collected = []

        for team_path in self.teams_dir.iterdir():
            if team_path.is_dir() and (team_path / "k8s").exists():
                team_name = team_path.name
                console.print(f"  📦 Processing {team_name}...")

                # Check if Docker image exists
                if not self._check_docker_image(f"{team_name}"):
                    console.print(f"    ⚠️  No Docker image found for {team_name}")
                    continue

                # Copy K8s manifests
                self._copy_team_manifests(team_path, team_name)

                # Apply any patches
                self._apply_patches(team_path, team_name)

                teams_collected.append(team_name)

        return teams_collected

    def _prepare_mcps(self) -> List[str]:
        """Prepare MCP manifests with AgentGateway integration"""
        console.print(
            "\n[yellow]🔧 Processing MCPs with AgentGateway Integration...[/yellow]"
        )
        mcps_collected = []

        for mcp_path in self.mcps_dir.iterdir():
            if mcp_path.is_dir() and (mcp_path / "k8s").exists():
                mcp_name = mcp_path.name
                console.print(f"  🔧 Processing MCP: {mcp_name}...")

                # Check for manifest.yaml
                manifest_path = mcp_path / "manifest.yaml"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = yaml.safe_load(f)

                    # Extract MCP metadata for AgentGateway
                    self.discovered_mcps.append(
                        {"name": mcp_name, "manifest": manifest, "path": mcp_path}
                    )

                # Check if Docker image exists
                if not self._check_docker_image(f"mcp-{mcp_name}"):
                    console.print(f"    ⚠️  No Docker image found for mcp-{mcp_name}")
                    continue

                # Copy and enhance K8s manifests
                self._copy_mcp_manifests(mcp_path, mcp_name)

                mcps_collected.append(mcp_name)

        return mcps_collected

    def _copy_mcp_manifests(self, mcp_path: Path, mcp_name: str):
        """Copy and enhance MCP K8s manifests"""
        source_k8s = mcp_path / "k8s"
        dest_k8s = self.mcps_manifests_dir / mcp_name
        dest_k8s.mkdir(exist_ok=True)

        for manifest_file in source_k8s.glob("*.yaml"):
            console.print(f"    📄 Processing {manifest_file.name}")

            with open(manifest_file) as f:
                manifest = yaml.safe_load(f)

            # Enhance ConfigMap with AgentGateway registration label
            if manifest.get("kind") == "ConfigMap":
                self._enhance_mcp_configmap(manifest, mcp_path)

            # Update image references
            if manifest.get("kind") == "Deployment":
                self._update_image_registry(manifest)
                # Ensure proper namespace
                manifest["metadata"]["namespace"] = "elf-mcps"

            # Update Service namespace
            if manifest.get("kind") == "Service":
                manifest["metadata"]["namespace"] = "elf-mcps"

            # Write enhanced manifest
            dest_file = dest_k8s / manifest_file.name
            with open(dest_file, "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)

    def _enhance_mcp_configmap(self, configmap: Dict, mcp_path: Path):
        """Enhance MCP ConfigMap with AgentGateway registration"""
        # Add registration label
        if "labels" not in configmap["metadata"]:
            configmap["metadata"]["labels"] = {}

        configmap["metadata"]["labels"][
            "agentgateway.elfautomations.com/register"
        ] = "true"
        configmap["metadata"]["namespace"] = "elf-mcps"

        # Check for agentgateway-config.json
        agentgateway_config_path = mcp_path / "agentgateway-config.json"
        if agentgateway_config_path.exists():
            with open(agentgateway_config_path) as f:
                gateway_config = json.load(f)

            # Add to ConfigMap data
            if "data" not in configmap:
                configmap["data"] = {}

            configmap["data"]["agentgateway-config.json"] = json.dumps(
                gateway_config, indent=2
            )

            console.print("    ✅ Added AgentGateway registration config")

    def _update_agentgateway_config(self):
        """Update AgentGateway configuration with discovered MCPs"""
        console.print("\n[yellow]🔗 Updating AgentGateway Configuration...[/yellow]")

        # Load existing AgentGateway config
        agentgateway_config_path = (
            self.gitops_dir.parent / "k8s" / "base" / "agentgateway" / "configmap.yaml"
        )

        if not agentgateway_config_path.exists():
            console.print(
                "  ⚠️  AgentGateway ConfigMap not found, creating dynamic config..."
            )
            self._create_dynamic_agentgateway_config()
            return

        # Read existing config
        with open(agentgateway_config_path) as f:
            configmap = yaml.safe_load(f)

        config_json = json.loads(configmap["data"]["config.json"])

        # Track existing MCPs
        existing_mcps = {
            mcp["name"] for mcp in config_json.get("targets", {}).get("mcp", [])
        }

        # Add discovered MCPs
        new_mcps = []
        for mcp_info in self.discovered_mcps:
            mcp_name = mcp_info["name"]
            if mcp_name in existing_mcps:
                console.print(f"  ℹ️  MCP '{mcp_name}' already registered")
                continue

            manifest = mcp_info["manifest"]
            spec = manifest.get("spec", {})
            runtime = spec.get("runtime", {})

            # Create MCP entry
            mcp_entry = {
                "name": mcp_name,
                runtime.get("type", "stdio"): {
                    "cmd": runtime.get("command", "node"),
                    "args": runtime.get("args", []),
                    "env": runtime.get("env", {}),
                    "working_directory": runtime.get("workingDirectory", "/app"),
                },
                "health_check": spec.get(
                    "healthCheck", {"enabled": True, "interval": "30s", "timeout": "5s"}
                ),
            }

            new_mcps.append(mcp_entry)
            console.print(f"  ✅ Added MCP '{mcp_name}' to AgentGateway config")

        if new_mcps:
            # Add new MCPs to config
            if "targets" not in config_json:
                config_json["targets"] = {}
            if "mcp" not in config_json["targets"]:
                config_json["targets"]["mcp"] = []

            config_json["targets"]["mcp"].extend(new_mcps)

            # Update ConfigMap
            configmap["data"]["config.json"] = json.dumps(config_json, indent=2)

            # Save updated ConfigMap
            dest_path = self.agentgateway_dir / "configmap.yaml"
            with open(dest_path, "w") as f:
                yaml.dump(configmap, f, default_flow_style=False)

            console.print(f"\n  💾 Saved updated AgentGateway config to {dest_path}")

    def _create_dynamic_agentgateway_config(self):
        """Create dynamic AgentGateway configuration"""
        # Create a minimal AgentGateway config that relies on dynamic discovery
        config = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "agentgateway-dynamic-config",
                "namespace": "elf-automations",
                "labels": {"app": "agentgateway", "component": "config"},
            },
            "data": {
                "config.json": json.dumps(
                    {
                        "type": "dynamic",
                        "discovery": {
                            "enabled": True,
                            "sources": [
                                {
                                    "type": "kubernetes",
                                    "namespace": "elf-mcps",
                                    "labelSelector": "agentgateway.elfautomations.com/register=true",
                                },
                                {"type": "api", "endpoint": "/api/mcp/register"},
                            ],
                        },
                        "listeners": [
                            {
                                "name": "mcp-sse",
                                "protocol": "MCP",
                                "sse": {"address": "[::]", "port": 3000},
                            },
                            {
                                "name": "admin",
                                "protocol": "HTTP",
                                "http": {"address": "[::]", "port": 8080},
                            },
                        ],
                        "observability": {
                            "metrics": {"prometheus": {"enabled": True, "port": 9090}}
                        },
                    },
                    indent=2,
                )
            },
        }

        dest_path = self.agentgateway_dir / "dynamic-configmap.yaml"
        with open(dest_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        console.print(f"  ✅ Created dynamic AgentGateway config at {dest_path}")

    def _check_docker_image(self, image_name: str) -> bool:
        """Check if Docker image exists"""
        # In production, this would check your registry
        # For now, just check if Dockerfile exists
        dockerfile_paths = [
            self.teams_dir / image_name / "Dockerfile",
            self.mcps_dir / image_name.replace("mcp-", "") / "Dockerfile",
        ]

        return any(path.exists() for path in dockerfile_paths)

    def _copy_team_manifests(self, team_path: Path, team_name: str):
        """Copy team manifests (unchanged)"""
        source_k8s = team_path / "k8s"
        dest_k8s = self.teams_manifests_dir / team_name
        dest_k8s.mkdir(exist_ok=True)

        for manifest_file in source_k8s.glob("*.yaml"):
            console.print(f"  📄 Copying {manifest_file.name}")

            with open(manifest_file) as f:
                manifest = yaml.safe_load(f)

            if manifest.get("kind") == "Deployment":
                self._update_image_registry(manifest)

            dest_file = dest_k8s / manifest_file.name
            with open(dest_file, "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)

    def _update_image_registry(self, manifest: Dict):
        """Update image references to use proper registry"""
        registry = os.getenv("DOCKER_REGISTRY", "")

        if "spec" in manifest and "template" in manifest["spec"]:
            containers = manifest["spec"]["template"]["spec"].get("containers", [])
            for container in containers:
                if "image" in container and registry:
                    image = container["image"]
                    if not image.startswith(registry):
                        if ":" in image:
                            name, tag = image.rsplit(":", 1)
                        else:
                            name, tag = image, "latest"
                        container["image"] = f"{registry}/{name}:{tag}"

    def _apply_patches(self, team_path: Path, team_name: str):
        """Apply any pending patches for this team"""
        patches_dir = team_path / "patches"
        if not patches_dir.exists():
            return

        applied_patches = []
        for patch_file in patches_dir.glob("*.yaml"):
            console.print(f"  🔧 Found patch: {patch_file.name}")
            applied_patches.append(patch_file.name)

        if applied_patches:
            console.print(
                f"  ⚠️  Manual patch application needed for {len(applied_patches)} patches"
            )

    def _generate_master_kustomization(self, teams: List[str], mcps: List[str]):
        """Generate Kustomization files"""
        # Teams Kustomization
        if teams:
            teams_kustomization = {
                "apiVersion": "kustomize.config.k8s.io/v1beta1",
                "kind": "Kustomization",
                "namespace": "elf-automations",
                "resources": [],
            }

            for team in sorted(teams):
                team_dir = self.teams_manifests_dir / team
                for file in team_dir.glob("*.yaml"):
                    teams_kustomization["resources"].append(f"{team}/{file.name}")

            with open(self.teams_manifests_dir / "kustomization.yaml", "w") as f:
                yaml.dump(teams_kustomization, f, default_flow_style=False)

        # MCPs Kustomization
        if mcps:
            mcps_kustomization = {
                "apiVersion": "kustomize.config.k8s.io/v1beta1",
                "kind": "Kustomization",
                "namespace": "elf-mcps",
                "resources": [],
            }

            for mcp in sorted(mcps):
                mcp_dir = self.mcps_manifests_dir / mcp
                for file in mcp_dir.glob("*.yaml"):
                    mcps_kustomization["resources"].append(f"{mcp}/{file.name}")

            with open(self.mcps_manifests_dir / "kustomization.yaml", "w") as f:
                yaml.dump(mcps_kustomization, f, default_flow_style=False)

        # Master Kustomization
        master_kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "resources": [],
        }

        if teams:
            master_kustomization["resources"].append("teams/")
        if mcps:
            master_kustomization["resources"].append("mcps/")
        if self.agentgateway_dir.exists():
            master_kustomization["resources"].append("agentgateway/")

        with open(self.gitops_dir / "manifests" / "kustomization.yaml", "w") as f:
            yaml.dump(master_kustomization, f, default_flow_style=False)

    def _generate_argocd_apps(self):
        """Generate ArgoCD Application manifests"""
        apps_dir = self.gitops_dir / "argocd-apps"
        apps_dir.mkdir(exist_ok=True)

        # ELF Platform App
        platform_app = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "elf-platform", "namespace": "argocd"},
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": "https://github.com/bryansparks/ELFAutomations.git",
                    "targetRevision": "main",
                    "path": "gitops/manifests",
                },
                "destination": {"server": "https://kubernetes.default.svc"},
                "syncPolicy": {"automated": {"prune": True, "selfHeal": True}},
            },
        }

        with open(apps_dir / "elf-platform.yaml", "w") as f:
            yaml.dump(platform_app, f, default_flow_style=False)

    def _show_summary(self, teams: List[str], mcps: List[str]):
        """Show deployment summary"""
        console.print(
            f"\n[bold green]✅ GitOps Artifacts Prepared Successfully![/bold green]"
        )

        # Summary table
        table = Table(title="Deployment Summary")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Items", style="yellow")

        if teams:
            table.add_row(
                "Teams",
                str(len(teams)),
                ", ".join(teams[:3]) + ("..." if len(teams) > 3 else ""),
            )

        if mcps:
            table.add_row(
                "MCPs",
                str(len(mcps)),
                ", ".join(mcps[:3]) + ("..." if len(mcps) > 3 else ""),
            )

        if self.discovered_mcps:
            registered = [m["name"] for m in self.discovered_mcps]
            table.add_row(
                "AgentGateway MCPs",
                str(len(registered)),
                ", ".join(registered[:3]) + ("..." if len(registered) > 3 else ""),
            )

        console.print(table)

        # Next steps
        console.print("\n[bold cyan]Next Steps:[/bold cyan]")
        console.print("1. Review the manifests in the gitops directory")
        console.print("2. Commit and push to your GitOps repository:")
        console.print("   git add gitops/")
        console.print(
            "   git commit -m 'Update platform manifests with MCP integration'"
        )
        console.print("   git push")
        console.print("3. ArgoCD will automatically sync the changes")
        console.print(
            "\n[yellow]MCPs will be auto-discovered by AgentGateway via:[/yellow]"
        )
        console.print(
            "  • ConfigMap labels (agentgateway.elfautomations.com/register=true)"
        )
        console.print("  • Dynamic discovery in elf-mcps namespace")
        console.print("  • Runtime registration API")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced GitOps artifact preparation with MCP support"
    )
    parser.add_argument(
        "--teams-dir", type=Path, default=Path("teams"), help="Teams directory"
    )
    parser.add_argument(
        "--mcps-dir", type=Path, default=Path("mcps"), help="MCPs directory"
    )
    parser.add_argument(
        "--gitops-dir",
        type=Path,
        default=Path("gitops"),
        help="GitOps output directory",
    )

    args = parser.parse_args()

    preparer = EnhancedGitOpsArtifactPreparer(
        args.teams_dir, args.mcps_dir, args.gitops_dir
    )

    preparer.prepare_all_artifacts()


if __name__ == "__main__":
    main()
