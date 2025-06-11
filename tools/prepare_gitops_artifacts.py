#!/usr/bin/env python3
"""
Prepare GitOps artifacts for ArgoCD deployment
This script collects all team manifests and organizes them for GitOps
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List

import yaml


class GitOpsArtifactPreparer:
    def __init__(self, teams_dir: Path, mcps_dir: Path, gitops_dir: Path):
        self.teams_dir = teams_dir
        self.mcps_dir = mcps_dir
        self.gitops_dir = gitops_dir
        self.teams_manifests_dir = gitops_dir / "manifests" / "teams"
        self.mcps_manifests_dir = gitops_dir / "manifests" / "mcps"
        self.teams_manifests_dir.mkdir(parents=True, exist_ok=True)
        self.mcps_manifests_dir.mkdir(parents=True, exist_ok=True)

    def prepare_all_artifacts(self):
        """Collect all team and MCP manifests for GitOps deployment"""
        print("🚀 Preparing GitOps artifacts for ArgoCD...")

        # Prepare teams
        teams_collected = self._prepare_teams()

        # Prepare MCPs
        mcps_collected = self._prepare_mcps()

        # Generate master Kustomization
        self._generate_master_kustomization(teams_collected, mcps_collected)

        # Generate ArgoCD Applications
        self._generate_argocd_apps()

        print(f"\n✅ Collected manifests:")
        print(f"   - {len(teams_collected)} teams")
        print(f"   - {len(mcps_collected)} MCPs")
        print(f"📁 GitOps artifacts ready in: {self.gitops_dir}")
        print("\nNext steps:")
        print("1. Review the manifests in the gitops directory")
        print("2. Commit and push to your GitOps repository")
        print("3. Apply the ArgoCD applications")

    def _prepare_teams(self) -> List[str]:
        """Prepare team manifests"""
        print("\n📦 Processing Teams...")
        teams_collected = []

        # Scan teams directory
        for team_path in self.teams_dir.iterdir():
            if team_path.is_dir() and (team_path / "k8s").exists():
                team_name = team_path.name
                print(f"  📦 Processing {team_name}...")

                # Check if Docker image exists
                if not self._check_docker_image(f"{team_name}"):
                    print(f"    ⚠️  No Docker image found for {team_name}")
                    print(
                        f"       Run: cd {team_path} && python make-deployable-team.py"
                    )
                    print(f"       Then: docker build -t elf-automations/{team_name} .")
                    print(
                        f"       And: docker push <your-registry>/elf-automations/{team_name}"
                    )
                    continue

                # Copy K8s manifests
                self._copy_team_manifests(team_path, team_name)

                # Apply any patches
                self._apply_patches(team_path, team_name)

                teams_collected.append(team_name)

        return teams_collected

    def _prepare_mcps(self) -> List[str]:
        """Prepare MCP manifests"""
        print("\n🔧 Processing MCPs...")
        mcps_collected = []

        # Scan MCPs directory
        for mcp_path in self.mcps_dir.iterdir():
            if mcp_path.is_dir() and (mcp_path / "k8s").exists():
                mcp_name = mcp_path.name
                print(f"  🔧 Processing MCP: {mcp_name}...")

                # Check if Docker image exists
                if not self._check_docker_image(f"mcp-{mcp_name}"):
                    print(f"    ⚠️  No Docker image found for mcp-{mcp_name}")
                    print(f"       Run: cd {mcp_path}")
                    print(
                        f"       Then: docker build -t elf-automations/mcp-{mcp_name} ."
                    )
                    print(
                        f"       And: docker push <your-registry>/elf-automations/mcp-{mcp_name}"
                    )
                    continue

                # Copy K8s manifests
                self._copy_mcp_manifests(mcp_path, mcp_name)

                mcps_collected.append(mcp_name)

        return mcps_collected

    def _check_docker_image(self, team_name: str) -> bool:
        """Check if Docker image exists (simplified check)"""
        # In production, this would check your registry
        # For now, just check if Dockerfile exists
        dockerfile = self.teams_dir / team_name / "Dockerfile"
        return dockerfile.exists()

    def _copy_team_manifests(self, team_path: Path, team_name: str):
        """Copy and update team K8s manifests"""
        source_k8s = team_path / "k8s"
        dest_k8s = self.teams_manifests_dir / team_name
        dest_k8s.mkdir(exist_ok=True)

        for manifest_file in source_k8s.glob("*.yaml"):
            print(f"  📄 Copying {manifest_file.name}")

            # Read and potentially modify manifest
            with open(manifest_file) as f:
                manifest = yaml.safe_load(f)

            # Update image to use registry
            if manifest.get("kind") == "Deployment":
                self._update_image_registry(manifest)

            # Write to GitOps location
            dest_file = dest_k8s / manifest_file.name
            with open(dest_file, "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)

    def _update_image_registry(self, manifest: Dict):
        """Update image references to use proper registry"""
        # TODO: Get registry from environment or config
        registry = os.getenv("DOCKER_REGISTRY", "docker.io/your-org")

        if "spec" in manifest and "template" in manifest["spec"]:
            containers = manifest["spec"]["template"]["spec"].get("containers", [])
            for container in containers:
                if "image" in container:
                    # Update image to use full registry path
                    image = container["image"]
                    if not image.startswith(registry):
                        # Extract image name
                        if ":" in image:
                            name, tag = image.rsplit(":", 1)
                        else:
                            name, tag = image, "latest"

                        # Rebuild with registry
                        container["image"] = f"{registry}/{name}:{tag}"

    def _apply_patches(self, team_path: Path, team_name: str):
        """Apply any pending patches for this team"""
        patches_dir = team_path / "patches"
        if not patches_dir.exists():
            return

        applied_patches = []
        for patch_file in patches_dir.glob("*.yaml"):
            print(f"  🔧 Found patch: {patch_file.name}")
            # In a real implementation, this would apply the patch
            # For now, just note it needs manual application
            applied_patches.append(patch_file.name)

        if applied_patches:
            print(
                f"  ⚠️  Manual patch application needed for {len(applied_patches)} patches"
            )

    def _copy_mcp_manifests(self, mcp_path: Path, mcp_name: str):
        """Copy and update MCP K8s manifests"""
        source_k8s = mcp_path / "k8s"
        dest_k8s = self.mcps_manifests_dir / mcp_name
        dest_k8s.mkdir(exist_ok=True)

        for manifest_file in source_k8s.glob("*.yaml"):
            print(f"    📄 Copying {manifest_file.name}")

            # Read and potentially modify manifest
            with open(manifest_file) as f:
                manifest = yaml.safe_load(f)

            # Update image to use registry
            if manifest.get("kind") == "Deployment":
                self._update_image_registry(manifest)

            # Write to GitOps location
            dest_file = dest_k8s / manifest_file.name
            with open(dest_file, "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)

    def _generate_master_kustomization(self, teams: List[str], mcps: List[str]):
        """Generate master Kustomization files"""
        # Teams Kustomization
        teams_kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "namespace": "elf-automations",
            "resources": [],
        }

        for team in sorted(teams):
            teams_kustomization["resources"].extend(
                [
                    f"{team}/deployment.yaml",
                    f"{team}/service.yaml",
                    f"{team}/configmap.yaml",
                ]
            )

        teams_kust_file = self.teams_manifests_dir / "kustomization.yaml"
        with open(teams_kust_file, "w") as f:
            yaml.dump(teams_kustomization, f, default_flow_style=False)

        # MCPs Kustomization
        mcps_kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "namespace": "elf-automations",
            "resources": [],
        }

        for mcp in sorted(mcps):
            mcps_kustomization["resources"].extend(
                [
                    f"{mcp}/deployment.yaml",
                    f"{mcp}/service.yaml",
                    f"{mcp}/configmap.yaml",
                ]
            )

        mcps_kust_file = self.mcps_manifests_dir / "kustomization.yaml"
        with open(mcps_kust_file, "w") as f:
            yaml.dump(mcps_kustomization, f, default_flow_style=False)

        # Master Kustomization
        master_kustomization = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "namespace": "elf-automations",
            "resources": ["teams/", "mcps/"],
        }

        master_kust_file = self.gitops_dir / "manifests" / "kustomization.yaml"
        with open(master_kust_file, "w") as f:
            yaml.dump(master_kustomization, f, default_flow_style=False)

        print(f"\n📝 Generated Kustomizations: {len(teams)} teams, {len(mcps)} MCPs")

    def _generate_argocd_apps(self):
        """Generate ArgoCD Application manifests"""
        app_dir = self.gitops_dir / "applications"
        app_dir.mkdir(exist_ok=True)

        # Teams Application
        teams_app = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "elf-teams", "namespace": "argocd"},
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": os.getenv(
                        "GITOPS_REPO_URL", "https://github.com/your-org/gitops"
                    ),
                    "targetRevision": "HEAD",
                    "path": "manifests/teams",
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": "elf-automations",
                },
                "syncPolicy": {
                    "automated": {"prune": True, "selfHeal": True},
                    "syncOptions": ["CreateNamespace=true"],
                },
            },
        }

        teams_file = app_dir / "teams-app.yaml"
        with open(teams_file, "w") as f:
            yaml.dump(teams_app, f, default_flow_style=False)

        # MCPs Application
        mcps_app = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "elf-mcps", "namespace": "argocd"},
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": os.getenv(
                        "GITOPS_REPO_URL", "https://github.com/your-org/gitops"
                    ),
                    "targetRevision": "HEAD",
                    "path": "manifests/mcps",
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": "elf-automations",
                },
                "syncPolicy": {
                    "automated": {"prune": True, "selfHeal": True},
                    "syncOptions": ["CreateNamespace=true"],
                },
            },
        }

        mcps_file = app_dir / "mcps-app.yaml"
        with open(mcps_file, "w") as f:
            yaml.dump(mcps_app, f, default_flow_style=False)

        print("📱 Generated ArgoCD Application manifests for teams and MCPs")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Prepare GitOps artifacts for ArgoCD")
    parser.add_argument(
        "--teams-dir",
        type=Path,
        default=Path(__file__).parent.parent / "teams",
        help="Directory containing teams",
    )
    parser.add_argument(
        "--mcps-dir",
        type=Path,
        default=Path(__file__).parent.parent / "mcps",
        help="Directory containing MCPs",
    )
    parser.add_argument(
        "--gitops-dir",
        type=Path,
        default=Path(__file__).parent.parent / "gitops",
        help="Output directory for GitOps artifacts",
    )

    args = parser.parse_args()

    preparer = GitOpsArtifactPreparer(args.teams_dir, args.mcps_dir, args.gitops_dir)
    preparer.prepare_all_artifacts()


if __name__ == "__main__":
    main()
