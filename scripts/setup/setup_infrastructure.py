#!/usr/bin/env python3
"""
Master infrastructure setup script

Orchestrates the complete infrastructure setup for ElfAutomations:
1. Environment validation
2. Docker setup (registry, image management)
3. Kubernetes setup (cluster, namespaces, RBAC)
4. Database setup (Supabase schemas, migrations)
5. Monitoring setup (Grafana, Prometheus)
6. ArgoCD setup (GitOps deployment)
7. Health verification
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elf_automations.shared.infrastructure import (
    DatabaseManager,
    DockerManager,
    HealthChecker,
    ImageTransfer,
    InfrastructureHealth,
    MigrationRunner,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()


class InfrastructureSetup:
    """Master infrastructure setup orchestrator"""

    def __init__(
        self,
        skip_docker: bool = False,
        skip_k8s: bool = False,
        skip_db: bool = False,
        remote_host: Optional[str] = None,
        remote_user: Optional[str] = None,
    ):
        """
        Initialize infrastructure setup

        Args:
            skip_docker: Skip Docker setup
            skip_k8s: Skip Kubernetes setup
            skip_db: Skip database setup
            remote_host: Remote host for Docker transfers
            remote_user: SSH user for remote host
        """
        self.skip_docker = skip_docker
        self.skip_k8s = skip_k8s
        self.skip_db = skip_db

        # Initialize managers
        self.docker_manager = (
            DockerManager(remote_host=remote_host, remote_user=remote_user)
            if not skip_docker
            else None
        )

        self.db_manager = DatabaseManager() if not skip_db else None
        self.health_checker = HealthChecker()

        self.results = {}

    async def run(self) -> Dict[str, Any]:
        """Run complete infrastructure setup"""
        console.print(
            Panel.fit(
                "[bold blue]ElfAutomations Infrastructure Setup[/bold blue]\n"
                "Setting up complete infrastructure stack",
                border_style="blue",
            )
        )

        # Phase 1: Environment validation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Validating environment...", total=None)
            self.results["environment"] = await self._validate_environment()
            progress.update(task, completed=True)

        if not self.results["environment"]["valid"]:
            console.print("[red]Environment validation failed![/red]")
            return self.results

        # Phase 2: Docker setup
        if not self.skip_docker:
            console.print("\n[bold]Phase 2: Docker Setup[/bold]")
            self.results["docker"] = await self._setup_docker()

        # Phase 3: Kubernetes setup
        if not self.skip_k8s:
            console.print("\n[bold]Phase 3: Kubernetes Setup[/bold]")
            self.results["kubernetes"] = await self._setup_kubernetes()

        # Phase 4: Database setup
        if not self.skip_db:
            console.print("\n[bold]Phase 4: Database Setup[/bold]")
            self.results["database"] = await self._setup_database()

        # Phase 5: Monitoring setup
        console.print("\n[bold]Phase 5: Monitoring Setup[/bold]")
        self.results["monitoring"] = await self._setup_monitoring()

        # Phase 6: ArgoCD setup
        console.print("\n[bold]Phase 6: ArgoCD Setup[/bold]")
        self.results["argocd"] = await self._setup_argocd()

        # Phase 7: Health verification
        console.print("\n[bold]Phase 7: Health Verification[/bold]")
        self.results["health"] = await self._verify_health()

        # Display summary
        self._display_summary()

        return self.results

    async def _validate_environment(self) -> Dict[str, Any]:
        """Validate environment and dependencies"""
        validation = {"valid": True, "checks": {}, "missing": []}

        # Check required tools
        required_tools = [
            ("docker", ["docker", "--version"]),
            ("kubectl", ["kubectl", "version", "--client"]),
            ("python", ["python", "--version"]),
            ("git", ["git", "--version"]),
        ]

        for tool_name, cmd in required_tools:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                validation["checks"][tool_name] = result.returncode == 0
                if result.returncode != 0:
                    validation["valid"] = False
                    validation["missing"].append(tool_name)
            except FileNotFoundError:
                validation["checks"][tool_name] = False
                validation["valid"] = False
                validation["missing"].append(tool_name)

        # Check environment variables
        required_env = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        if not self.skip_db:
            required_env.extend(["SUPABASE_URL", "SUPABASE_KEY"])

        for env_var in required_env:
            if os.getenv(env_var):
                validation["checks"][env_var] = True
            else:
                validation["checks"][env_var] = False
                validation["valid"] = False
                validation["missing"].append(f"Environment variable: {env_var}")

        return validation

    async def _setup_docker(self) -> Dict[str, Any]:
        """Setup Docker and local registry"""
        result = {"registry_setup": False, "images_built": 0, "errors": []}

        if not self.docker_manager:
            return result

        # Setup local registry
        with console.status("Setting up Docker registry..."):
            try:
                if self.docker_manager.setup_local_registry():
                    result["registry_setup"] = True
                    console.print("✅ Docker registry running on localhost:5000")
                else:
                    result["errors"].append("Failed to setup registry")
                    console.print("❌ Failed to setup Docker registry")
            except Exception as e:
                result["errors"].append(str(e))
                console.print(f"❌ Docker setup error: {e}")

        # Setup remote registry access if configured
        if self.docker_manager.remote_host:
            with console.status("Configuring remote Docker access..."):
                try:
                    transfer = ImageTransfer(self.docker_manager)
                    if transfer.setup_remote_registry_access():
                        console.print(
                            f"✅ Remote Docker configured at {self.docker_manager.remote_host}"
                        )
                    else:
                        result["errors"].append("Failed to configure remote Docker")
                except Exception as e:
                    result["errors"].append(str(e))

        return result

    async def _setup_kubernetes(self) -> Dict[str, Any]:
        """Setup Kubernetes cluster and resources"""
        result = {"cluster_ready": False, "namespaces_created": [], "errors": []}

        # Check cluster
        with console.status("Checking Kubernetes cluster..."):
            try:
                cmd = ["kubectl", "cluster-info"]
                subprocess.run(cmd, check=True, capture_output=True)
                result["cluster_ready"] = True
                console.print("✅ Kubernetes cluster is ready")
            except subprocess.CalledProcessError as e:
                result["errors"].append("Kubernetes cluster not accessible")
                console.print("❌ Kubernetes cluster not ready")
                return result

        # Create namespaces
        namespaces = ["elf-teams", "elf-monitoring", "argocd"]

        for namespace in namespaces:
            try:
                cmd = ["kubectl", "create", "namespace", namespace]
                subprocess.run(cmd, check=True, capture_output=True)
                result["namespaces_created"].append(namespace)
                console.print(f"✅ Created namespace: {namespace}")
            except subprocess.CalledProcessError:
                # Namespace might already exist
                console.print(f"ℹ️  Namespace {namespace} already exists")

        # Apply base manifests
        base_manifests = Path("k8s/base")
        if base_manifests.exists():
            with console.status("Applying base Kubernetes manifests..."):
                try:
                    cmd = ["kubectl", "apply", "-f", str(base_manifests)]
                    subprocess.run(cmd, check=True, capture_output=True)
                    console.print("✅ Base manifests applied")
                except subprocess.CalledProcessError as e:
                    result["errors"].append(f"Failed to apply base manifests: {e}")

        return result

    async def _setup_database(self) -> Dict[str, Any]:
        """Setup database schemas and migrations"""
        result = {
            "connected": False,
            "migrations_run": 0,
            "schemas_healthy": False,
            "errors": [],
        }

        if not self.db_manager:
            return result

        # Check connection
        with console.status("Connecting to database..."):
            if self.db_manager.client:
                result["connected"] = True
                console.print("✅ Connected to Supabase")
            else:
                result["errors"].append("Failed to connect to database")
                console.print("❌ Failed to connect to database")
                return result

        # Run migrations
        with console.status("Running database migrations..."):
            try:
                runner = MigrationRunner(self.db_manager)
                migration_results = runner.setup_all_schemas()

                result["migrations_run"] = migration_results["migrations"]["executed"]
                result["schemas_healthy"] = migration_results["success"]

                console.print(f"✅ Ran {result['migrations_run']} migrations")

                # Show migration details
                if migration_results["migrations"]["migrations"]:
                    table = Table(title="Migration Results")
                    table.add_column("Migration", style="cyan")
                    table.add_column("Status", style="green")

                    for m in migration_results["migrations"]["migrations"]:
                        table.add_row(m["name"], m["status"])

                    console.print(table)

            except Exception as e:
                result["errors"].append(str(e))
                console.print(f"❌ Migration error: {e}")

        return result

    async def _setup_monitoring(self) -> Dict[str, Any]:
        """Setup monitoring stack"""
        result = {"prometheus_deployed": False, "grafana_deployed": False, "errors": []}

        # Deploy monitoring stack
        monitoring_path = Path("k8s/base/prometheus.yaml")
        if monitoring_path.exists():
            try:
                cmd = [
                    "kubectl",
                    "apply",
                    "-f",
                    str(monitoring_path),
                    "-n",
                    "elf-monitoring",
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                result["prometheus_deployed"] = True
                console.print("✅ Prometheus deployed")
            except subprocess.CalledProcessError as e:
                result["errors"].append(f"Failed to deploy Prometheus: {e}")

        grafana_path = Path("k8s/base/grafana.yaml")
        if grafana_path.exists():
            try:
                cmd = [
                    "kubectl",
                    "apply",
                    "-f",
                    str(grafana_path),
                    "-n",
                    "elf-monitoring",
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                result["grafana_deployed"] = True
                console.print("✅ Grafana deployed")
            except subprocess.CalledProcessError as e:
                result["errors"].append(f"Failed to deploy Grafana: {e}")

        return result

    async def _setup_argocd(self) -> Dict[str, Any]:
        """Setup ArgoCD for GitOps"""
        result = {"installed": False, "configured": False, "errors": []}

        # Check if ArgoCD is installed
        with console.status("Checking ArgoCD installation..."):
            try:
                cmd = ["kubectl", "get", "deployment", "argocd-server", "-n", "argocd"]
                subprocess.run(cmd, check=True, capture_output=True)
                result["installed"] = True
                console.print("✅ ArgoCD is installed")
            except subprocess.CalledProcessError:
                # Install ArgoCD
                console.print("📦 Installing ArgoCD...")
                try:
                    cmd = [
                        "kubectl",
                        "apply",
                        "-n",
                        "argocd",
                        "-f",
                        "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml",
                    ]
                    subprocess.run(cmd, check=True, capture_output=True)
                    result["installed"] = True
                    console.print("✅ ArgoCD installed")
                except subprocess.CalledProcessError as e:
                    result["errors"].append(f"Failed to install ArgoCD: {e}")
                    return result

        # Wait for ArgoCD to be ready
        with console.status("Waiting for ArgoCD to be ready..."):
            try:
                cmd = [
                    "kubectl",
                    "wait",
                    "--for=condition=available",
                    "--timeout=300s",
                    "deployment/argocd-server",
                    "-n",
                    "argocd",
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                console.print("✅ ArgoCD is ready")
            except subprocess.CalledProcessError:
                result["errors"].append("ArgoCD failed to become ready")

        return result

    async def _verify_health(self) -> Dict[str, Any]:
        """Verify overall infrastructure health"""
        async with self.health_checker as checker:
            infra_health = InfrastructureHealth(checker)
            report = await infra_health.get_health_report()

            # Display health status
            table = Table(title="Infrastructure Health")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Message")

            for component, details in report["components"].items():
                status = details["status"]
                style = (
                    "green"
                    if status == "healthy"
                    else "yellow"
                    if status == "degraded"
                    else "red"
                )
                table.add_row(
                    component.title(),
                    f"[{style}]{status.upper()}[/{style}]",
                    details["message"],
                )

            console.print(table)

            return report

    def _display_summary(self):
        """Display setup summary"""
        console.print("\n")
        console.print(
            Panel.fit("[bold]Infrastructure Setup Summary[/bold]", border_style="green")
        )

        # Create summary table
        table = Table()
        table.add_column("Component", style="cyan")
        table.add_column("Status")
        table.add_column("Details")

        # Environment
        env_status = "✅ Valid" if self.results["environment"]["valid"] else "❌ Invalid"
        table.add_row(
            "Environment",
            env_status,
            f"{len(self.results['environment']['missing'])} missing",
        )

        # Docker
        if "docker" in self.results:
            docker_status = (
                "✅ Ready" if self.results["docker"]["registry_setup"] else "❌ Failed"
            )
            table.add_row("Docker", docker_status, "Registry on :5000")

        # Kubernetes
        if "kubernetes" in self.results:
            k8s_status = (
                "✅ Ready" if self.results["kubernetes"]["cluster_ready"] else "❌ Failed"
            )
            ns_count = len(self.results["kubernetes"]["namespaces_created"])
            table.add_row("Kubernetes", k8s_status, f"{ns_count} namespaces")

        # Database
        if "database" in self.results:
            db_status = (
                "✅ Ready" if self.results["database"]["schemas_healthy"] else "❌ Failed"
            )
            migrations = self.results["database"]["migrations_run"]
            table.add_row("Database", db_status, f"{migrations} migrations")

        # Monitoring
        if "monitoring" in self.results:
            mon_ready = (
                self.results["monitoring"]["prometheus_deployed"]
                and self.results["monitoring"]["grafana_deployed"]
            )
            mon_status = "✅ Ready" if mon_ready else "⚠️ Partial"
            table.add_row("Monitoring", mon_status, "Prometheus + Grafana")

        # ArgoCD
        if "argocd" in self.results:
            argo_status = (
                "✅ Ready" if self.results["argocd"]["installed"] else "❌ Failed"
            )
            table.add_row("ArgoCD", argo_status, "GitOps ready")

        console.print(table)

        # Next steps
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Deploy teams: python scripts/deploy_teams.py")
        console.print(
            "2. Access ArgoCD: kubectl port-forward svc/argocd-server -n argocd 8080:443"
        )
        console.print(
            "3. Access Grafana: kubectl port-forward svc/grafana -n elf-monitoring 3000:80"
        )
        console.print("4. Monitor health: python scripts/monitor_infrastructure.py")


@click.command()
@click.option("--skip-docker", is_flag=True, help="Skip Docker setup")
@click.option("--skip-k8s", is_flag=True, help="Skip Kubernetes setup")
@click.option("--skip-db", is_flag=True, help="Skip database setup")
@click.option("--remote-host", help="Remote host for Docker transfers")
@click.option("--remote-user", default="bryan", help="SSH user for remote host")
@click.option("--fix-transfer", is_flag=True, help="Fix the corrupted transfer script")
def main(skip_docker, skip_k8s, skip_db, remote_host, remote_user, fix_transfer):
    """Master infrastructure setup for ElfAutomations"""

    if fix_transfer:
        # Fix the corrupted transfer script
        fix_transfer_script()
        return

    # Run setup
    setup = InfrastructureSetup(
        skip_docker=skip_docker,
        skip_k8s=skip_k8s,
        skip_db=skip_db,
        remote_host=remote_host,
        remote_user=remote_user,
    )

    asyncio.run(setup.run())


def fix_transfer_script():
    """Fix the corrupted transfer-docker-images-ssh.sh script"""
    script_path = Path("scripts/transfer-docker-images-ssh.sh")

    console.print("[bold]Fixing corrupted transfer script...[/bold]")

    correct_content = """#!/bin/bash

# Transfer Docker images to remote machine via SSH
# This script handles the manual transfer of Docker images when no registry is available

REMOTE_HOST="${1:-192.168.6.5}"
REMOTE_USER="${2:-bryan}"
IMAGE_FILTER="${3:-elf-automations}"

echo "🚀 Docker Image Transfer Script"
echo "==============================="
echo "Remote Host: $REMOTE_USER@$REMOTE_HOST"
echo "Image Filter: $IMAGE_FILTER"
echo ""

# Check SSH connectivity
echo "🔍 Checking SSH connection..."
if ! ssh -q "$REMOTE_USER@$REMOTE_HOST" exit; then
    echo "❌ Cannot connect to $REMOTE_USER@$REMOTE_HOST"
    echo "Please ensure:"
    echo "1. The remote host is reachable"
    echo "2. SSH keys are configured"
    echo "3. The user has Docker access on remote"
    exit 1
fi
echo "✅ SSH connection successful"

# Get list of images to transfer
echo ""
echo "🔍 Finding images to transfer..."
IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "$IMAGE_FILTER")

if [ -z "$IMAGES" ]; then
    echo "❌ No images found matching filter: $IMAGE_FILTER"
    exit 1
fi

echo "📦 Found images:"
echo "$IMAGES" | nl

# Transfer each image
TOTAL=$(echo "$IMAGES" | wc -l | xargs)
COUNT=0

for IMAGE in $IMAGES; do
    COUNT=$((COUNT + 1))
    echo ""
    echo "[$COUNT/$TOTAL] Transferring $IMAGE..."

    # Create temporary file name
    TEMP_FILE="/tmp/$(echo $IMAGE | tr '/:' '_').tar.gz"

    # Save and compress image
    echo "  📦 Saving and compressing..."
    if ! docker save "$IMAGE" | gzip > "$TEMP_FILE"; then
        echo "  ❌ Failed to save image"
        continue
    fi

    # Get file size
    SIZE=$(ls -lh "$TEMP_FILE" | awk '{print $5}')
    echo "  📊 Compressed size: $SIZE"

    # Transfer to remote
    echo "  📤 Transferring to remote..."
    if ! scp -q "$TEMP_FILE" "$REMOTE_USER@$REMOTE_HOST:$TEMP_FILE"; then
        echo "  ❌ Failed to transfer"
        rm -f "$TEMP_FILE"
        continue
    fi

    # Load on remote
    echo "  📥 Loading on remote..."
    if ! ssh "$REMOTE_USER@$REMOTE_HOST" "gunzip -c $TEMP_FILE | docker load && rm -f $TEMP_FILE"; then
        echo "  ❌ Failed to load on remote"
    else
        echo "  ✅ Successfully transferred $IMAGE"
    fi

    # Cleanup local temp file
    rm -f "$TEMP_FILE"
done

echo ""
echo "✅ Transfer complete!"
echo ""
echo "📋 To verify on remote host:"
echo "   ssh $REMOTE_USER@$REMOTE_HOST docker images | grep $IMAGE_FILTER"
"""

    # Write the fixed script
    script_path.write_text(correct_content)
    script_path.chmod(0o755)

    console.print(f"✅ Fixed transfer script at {script_path}")
    console.print("\nYou can now run:")
    console.print(
        f"  ./scripts/transfer-docker-images-ssh.sh [remote-host] [remote-user] [image-filter]"
    )


if __name__ == "__main__":
    main()
