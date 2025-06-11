"""
Automated deployment pipeline for teams and infrastructure

Handles:
- Team deployment workflow
- Health verification
- Rollback on failure
- Status tracking and notifications
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .docker_manager import DockerImage, DockerManager
from .health_checker import HealthChecker

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status"""

    PENDING = "pending"
    BUILDING = "building"
    PUSHING = "pushing"
    DEPLOYING = "deploying"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentStage(Enum):
    """Deployment pipeline stages"""

    PRE_BUILD = "pre_build"
    BUILD = "build"
    TEST = "test"
    PUSH = "push"
    DEPLOY = "deploy"
    VERIFY = "verify"
    POST_DEPLOY = "post_deploy"


@dataclass
class DeploymentContext:
    """Context for a deployment"""

    team_name: str
    team_path: Path
    image_name: str
    image_tag: str
    namespace: str = "elf-teams"
    status: DeploymentStatus = DeploymentStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DeploymentPipeline:
    """Automated deployment pipeline"""

    def __init__(
        self,
        docker_manager: DockerManager,
        health_checker: Optional[HealthChecker] = None,
        k8s_context: str = "docker-desktop",
        argocd_repo: Optional[str] = None,
    ):
        """
        Initialize deployment pipeline

        Args:
            docker_manager: Docker manager instance
            health_checker: Health checker instance
            k8s_context: Kubernetes context name
            argocd_repo: ArgoCD Git repository URL
        """
        self.docker = docker_manager
        self.health_checker = health_checker
        self.k8s_context = k8s_context
        self.argocd_repo = (
            argocd_repo or "https://github.com/bryansparks/ELFAutomations.git"
        )

        # Stage hooks
        self._stage_hooks: Dict[DeploymentStage, List[Callable]] = {
            stage: [] for stage in DeploymentStage
        }

    def add_stage_hook(self, stage: DeploymentStage, hook: Callable):
        """Add a hook to run at a specific stage"""
        self._stage_hooks[stage].append(hook)

    async def deploy_team(
        self,
        team_name: str,
        team_path: Optional[Path] = None,
        auto_rollback: bool = True,
    ) -> DeploymentContext:
        """
        Deploy a team through the full pipeline

        Args:
            team_name: Name of the team
            team_path: Path to team directory
            auto_rollback: Whether to rollback on failure

        Returns:
            DeploymentContext with results
        """
        if not team_path:
            team_path = Path("teams") / team_name

        if not team_path.exists():
            raise ValueError(f"Team path not found: {team_path}")

        # Create deployment context
        context = DeploymentContext(
            team_name=team_name,
            team_path=team_path,
            image_name=f"elf-automations/{team_name}",
            image_tag=datetime.now().strftime("%Y%m%d-%H%M%S"),
            started_at=datetime.now(),
        )

        try:
            # Run through pipeline stages
            await self._run_stage(DeploymentStage.PRE_BUILD, context)
            await self._build_stage(context)
            await self._test_stage(context)
            await self._push_stage(context)
            await self._deploy_stage(context)
            await self._verify_stage(context)
            await self._run_stage(DeploymentStage.POST_DEPLOY, context)

            # Success!
            context.status = DeploymentStatus.COMPLETED
            context.completed_at = datetime.now()
            logger.info(f"Successfully deployed {team_name}")

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            context.status = DeploymentStatus.FAILED
            context.error = str(e)
            context.completed_at = datetime.now()

            if auto_rollback:
                await self._rollback(context)

        return context

    async def _run_stage(self, stage: DeploymentStage, context: DeploymentContext):
        """Run hooks for a stage"""
        for hook in self._stage_hooks[stage]:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(context)
                else:
                    hook(context)
            except Exception as e:
                logger.error(f"Hook failed in {stage.value}: {e}")
                raise

    async def _build_stage(self, context: DeploymentContext):
        """Build Docker image"""
        logger.info(f"Building image for {context.team_name}")
        context.status = DeploymentStatus.BUILDING

        await self._run_stage(DeploymentStage.BUILD, context)

        # Check for make-deployable-team.py
        make_script = context.team_path / "make-deployable-team.py"
        if make_script.exists():
            logger.info("Running make-deployable-team.py")
            result = subprocess.run(
                ["python", str(make_script)],
                cwd=str(context.team_path),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise Exception(f"make-deployable-team.py failed: {result.stderr}")

        # Build Docker image
        image = self.docker.build_image(
            path=str(context.team_path),
            image_name=context.image_name,
            tag=context.image_tag,
            push_to_registry=False,  # We'll push in next stage
        )

        if not image:
            raise Exception("Failed to build Docker image")

        context.metadata["docker_image"] = image.full_name
        logger.info(f"Built image: {image.full_name}")

    async def _test_stage(self, context: DeploymentContext):
        """Run tests on built image"""
        logger.info(f"Testing {context.team_name}")

        await self._run_stage(DeploymentStage.TEST, context)

        # Run container briefly to ensure it starts
        test_cmd = [
            "docker",
            "run",
            "--rm",
            "--name",
            f"{context.team_name}-test",
            context.metadata["docker_image"],
            "python",
            "-c",
            "print('Health check passed')",
        ]

        try:
            result = subprocess.run(
                test_cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                raise Exception(f"Container test failed: {result.stderr}")
            logger.info("Container test passed")
        except subprocess.TimeoutExpired:
            raise Exception("Container test timed out")

    async def _push_stage(self, context: DeploymentContext):
        """Push image to registry"""
        logger.info(f"Pushing image for {context.team_name}")
        context.status = DeploymentStatus.PUSHING

        await self._run_stage(DeploymentStage.PUSH, context)

        # Push to local registry
        image = DockerImage(name=context.image_name, tag=context.image_tag)

        registry_image = self.docker.push_to_registry(image)
        if not registry_image:
            raise Exception("Failed to push to registry")

        context.metadata["registry_image"] = registry_image.full_name

        # If remote host configured, transfer image
        if self.docker.remote_host:
            from .docker_manager import ImageTransfer

            transfer = ImageTransfer(self.docker)
            if not transfer.transfer_image(image):
                raise Exception("Failed to transfer image to remote host")

    async def _deploy_stage(self, context: DeploymentContext):
        """Deploy to Kubernetes"""
        logger.info(f"Deploying {context.team_name} to Kubernetes")
        context.status = DeploymentStatus.DEPLOYING

        await self._run_stage(DeploymentStage.DEPLOY, context)

        # Update K8s manifest with new image tag
        manifest_path = context.team_path / "k8s" / "deployment.yaml"
        if not manifest_path.exists():
            raise Exception(f"K8s manifest not found: {manifest_path}")

        # Read and update manifest
        manifest_content = manifest_path.read_text()
        updated_manifest = manifest_content.replace(
            f"{context.image_name}:latest", f"{context.metadata['registry_image']}"
        )

        # Apply to cluster
        apply_cmd = [
            "kubectl",
            "apply",
            "--context",
            self.k8s_context,
            "-n",
            context.namespace,
            "-f",
            "-",
        ]

        result = subprocess.run(
            apply_cmd, input=updated_manifest, text=True, capture_output=True
        )

        if result.returncode != 0:
            raise Exception(f"kubectl apply failed: {result.stderr}")

        logger.info("Kubernetes manifest applied")

        # Wait for deployment to be ready
        await self._wait_for_deployment(context)

    async def _wait_for_deployment(
        self, context: DeploymentContext, timeout: int = 300
    ):
        """Wait for deployment to be ready"""
        logger.info(f"Waiting for {context.team_name} deployment to be ready...")

        wait_cmd = [
            "kubectl",
            "wait",
            "--context",
            self.k8s_context,
            "-n",
            context.namespace,
            "--for=condition=available",
            "--timeout",
            f"{timeout}s",
            f"deployment/{context.team_name}",
        ]

        result = subprocess.run(wait_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Deployment not ready: {result.stderr}")

        logger.info("Deployment is ready")

    async def _verify_stage(self, context: DeploymentContext):
        """Verify deployment health"""
        logger.info(f"Verifying {context.team_name} deployment")
        context.status = DeploymentStatus.VERIFYING

        await self._run_stage(DeploymentStage.VERIFY, context)

        if self.health_checker:
            # Get pod name
            get_pod_cmd = [
                "kubectl",
                "get",
                "pods",
                "--context",
                self.k8s_context,
                "-n",
                context.namespace,
                "-l",
                f"app={context.team_name}",
                "-o",
                "jsonpath={.items[0].metadata.name}",
            ]

            result = subprocess.run(get_pod_cmd, capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout:
                raise Exception("Failed to get pod name")

            pod_name = result.stdout.strip()

            # Check health endpoint
            health_endpoint = f"http://{pod_name}:8000/health"
            health_status = await self.health_checker.check_endpoint(
                health_endpoint, namespace=context.namespace
            )

            if not health_status["healthy"]:
                raise Exception(f"Health check failed: {health_status.get('error')}")

            logger.info("Health verification passed")
        else:
            logger.warning("No health checker configured, skipping verification")

    async def _rollback(self, context: DeploymentContext):
        """Rollback a failed deployment"""
        logger.warning(f"Rolling back deployment for {context.team_name}")

        try:
            # Get previous revision
            rollback_cmd = [
                "kubectl",
                "rollout",
                "undo",
                "--context",
                self.k8s_context,
                "-n",
                context.namespace,
                f"deployment/{context.team_name}",
            ]

            result = subprocess.run(rollback_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                context.status = DeploymentStatus.ROLLED_BACK
                logger.info("Rollback completed successfully")
            else:
                logger.error(f"Rollback failed: {result.stderr}")

        except Exception as e:
            logger.error(f"Error during rollback: {e}")

    async def deploy_multiple_teams(
        self, team_names: List[str], parallel: bool = False
    ) -> Dict[str, DeploymentContext]:
        """
        Deploy multiple teams

        Args:
            team_names: List of team names to deploy
            parallel: Whether to deploy in parallel

        Returns:
            Dict of team_name -> DeploymentContext
        """
        results = {}

        if parallel:
            # Deploy in parallel
            tasks = [self.deploy_team(team_name) for team_name in team_names]

            contexts = await asyncio.gather(*tasks, return_exceptions=True)

            for team_name, context in zip(team_names, contexts):
                if isinstance(context, Exception):
                    # Create failed context
                    results[team_name] = DeploymentContext(
                        team_name=team_name,
                        team_path=Path("teams") / team_name,
                        image_name=f"elf-automations/{team_name}",
                        image_tag="failed",
                        status=DeploymentStatus.FAILED,
                        error=str(context),
                    )
                else:
                    results[team_name] = context
        else:
            # Deploy sequentially
            for team_name in team_names:
                try:
                    context = await self.deploy_team(team_name)
                    results[team_name] = context
                except Exception as e:
                    logger.error(f"Failed to deploy {team_name}: {e}")
                    results[team_name] = DeploymentContext(
                        team_name=team_name,
                        team_path=Path("teams") / team_name,
                        image_name=f"elf-automations/{team_name}",
                        image_tag="failed",
                        status=DeploymentStatus.FAILED,
                        error=str(e),
                    )

        return results

    def get_deployment_report(
        self, contexts: Dict[str, DeploymentContext]
    ) -> Dict[str, Any]:
        """Generate deployment report"""
        report = {
            "total": len(contexts),
            "successful": 0,
            "failed": 0,
            "rolled_back": 0,
            "teams": {},
        }

        for team_name, context in contexts.items():
            if context.status == DeploymentStatus.COMPLETED:
                report["successful"] += 1
            elif context.status == DeploymentStatus.FAILED:
                report["failed"] += 1
            elif context.status == DeploymentStatus.ROLLED_BACK:
                report["rolled_back"] += 1

            duration = None
            if context.started_at and context.completed_at:
                duration = (context.completed_at - context.started_at).total_seconds()

            report["teams"][team_name] = {
                "status": context.status.value,
                "duration_seconds": duration,
                "error": context.error,
                "image": context.metadata.get("docker_image"),
            }

        return report
