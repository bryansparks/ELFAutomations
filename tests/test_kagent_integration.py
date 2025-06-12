#!/usr/bin/env python3
"""
Test kagent integration with distributed CrewAI agents.
This script validates that our distributed agents can be deployed via kagent CRDs.
"""

import asyncio
import logging
import subprocess
import time
from pathlib import Path

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_kagent")


def check_minikube_status():
    """Check if minikube is running."""
    try:
        result = subprocess.run(["minikube", "status"], capture_output=True, text=True)
        return "Running" in result.stdout
    except Exception as e:
        logger.error(f"Failed to check minikube status: {e}")
        return False


def check_kagent_controller():
    """Check if kagent controller is running."""
    try:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "pods",
                "-n",
                "kagent-system",
                "-l",
                "app=kagent-controller",
            ],
            capture_output=True,
            text=True,
        )
        return "Running" in result.stdout
    except Exception as e:
        logger.error(f"Failed to check kagent controller: {e}")
        return False


def apply_kagent_crd(manifest_path: str):
    """Apply kagent CRD manifest."""
    try:
        result = subprocess.run(
            ["kubectl", "apply", "-f", manifest_path], capture_output=True, text=True
        )

        if result.returncode == 0:
            logger.info(f"✅ Applied kagent CRD: {manifest_path}")
            return True
        else:
            logger.error(f"❌ Failed to apply CRD: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to apply kagent CRD: {e}")
        return False


def check_agent_status(agent_name: str, namespace: str = "elf-automations"):
    """Check the status of a deployed agent."""
    try:
        # Check Agent CRD status
        result = subprocess.run(
            ["kubectl", "get", "agent", agent_name, "-n", namespace, "-o", "yaml"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            agent_yaml = yaml.safe_load(result.stdout)
            status = agent_yaml.get("status", {})

            logger.info(f"Agent {agent_name} status:")
            logger.info(f"  Accepted: {status.get('accepted', 'Unknown')}")
            logger.info(f"  Reason: {status.get('reason', 'Unknown')}")

            # Check if pods are running
            pod_result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-n",
                    namespace,
                    "-l",
                    f"app={agent_name}",
                    "-o",
                    "wide",
                ],
                capture_output=True,
                text=True,
            )

            if pod_result.returncode == 0:
                logger.info(f"Pods for {agent_name}:")
                logger.info(pod_result.stdout)

            return status.get("accepted", False)
        else:
            logger.error(f"Failed to get agent status: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Failed to check agent status: {e}")
        return False


def create_namespace(namespace: str):
    """Create namespace if it doesn't exist."""
    try:
        result = subprocess.run(
            ["kubectl", "create", "namespace", namespace],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info(f"✅ Created namespace: {namespace}")
        elif "already exists" in result.stderr:
            logger.info(f"✅ Namespace {namespace} already exists")
        else:
            logger.error(f"❌ Failed to create namespace: {result.stderr}")
            return False

        return True
    except Exception as e:
        logger.error(f"Failed to create namespace: {e}")
        return False


async def test_kagent_integration():
    """Test kagent integration with distributed agents."""
    logger.info("🚀 Testing kagent integration with distributed agents")

    # Check prerequisites
    logger.info("🔍 Checking prerequisites...")

    if not check_minikube_status():
        logger.error("❌ Minikube is not running. Please start minikube first.")
        return False

    logger.info("✅ Minikube is running")

    if not check_kagent_controller():
        logger.warning(
            "⚠️  kagent controller not found. This is expected if not deployed yet."
        )
    else:
        logger.info("✅ kagent controller is running")

    # Create namespace
    if not create_namespace("elf-automations"):
        return False

    # Test kagent CRD application
    logger.info("🔍 Testing kagent CRD application...")

    manifest_path = "/Users/bryansparks/projects/ELFAutomations/agents/distributed/k8s/sales-agent-kagent.yaml"

    if not Path(manifest_path).exists():
        logger.error(f"❌ Manifest file not found: {manifest_path}")
        return False

    # Apply the CRD
    if not apply_kagent_crd(manifest_path):
        return False

    # Wait a bit for processing
    logger.info("⏳ Waiting for agent processing...")
    await asyncio.sleep(10)

    # Check agent status
    logger.info("🔍 Checking agent status...")
    agent_accepted = check_agent_status("sales-agent", "elf-automations")

    if agent_accepted:
        logger.info("✅ Sales agent accepted by kagent controller")
    else:
        logger.warning("⚠️  Sales agent not yet accepted (this may be normal)")

    # Check for any error events
    logger.info("🔍 Checking for events...")
    try:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "events",
                "-n",
                "elf-automations",
                "--sort-by=.metadata.creationTimestamp",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("Recent events:")
            logger.info(result.stdout)
    except Exception as e:
        logger.warning(f"Could not fetch events: {e}")

    return True


async def test_docker_build():
    """Test building the distributed agent Docker image."""
    logger.info("🔍 Testing Docker image build...")

    dockerfile_path = (
        "/Users/bryansparks/projects/ELFAutomations/agents/distributed/Dockerfile"
    )

    if not Path(dockerfile_path).exists():
        logger.error(f"❌ Dockerfile not found: {dockerfile_path}")
        return False

    try:
        # Build the Docker image
        logger.info("🔨 Building Docker image...")
        result = subprocess.run(
            [
                "docker",
                "build",
                "-t",
                "elf-automations/sales-agent:latest",
                "-f",
                dockerfile_path,
                "/Users/bryansparks/projects/ELFAutomations/agents/distributed",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("✅ Docker image built successfully")

            # Load into minikube
            logger.info("📦 Loading image into minikube...")
            load_result = subprocess.run(
                ["minikube", "image", "load", "elf-automations/sales-agent:latest"],
                capture_output=True,
                text=True,
            )

            if load_result.returncode == 0:
                logger.info("✅ Image loaded into minikube")
                return True
            else:
                logger.error(f"❌ Failed to load image: {load_result.stderr}")
                return False
        else:
            logger.error(f"❌ Docker build failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Failed to build Docker image: {e}")
        return False


async def main():
    """Run all integration tests."""
    logger.info("🚀 Starting kagent Integration Tests")

    try:
        # Test Docker build first
        docker_success = await test_docker_build()
        if not docker_success:
            logger.warning("⚠️  Docker build failed, but continuing with CRD tests...")

        # Test kagent integration
        kagent_success = await test_kagent_integration()

        if kagent_success:
            logger.info("🎉 kagent integration tests completed!")
            logger.info("")
            logger.info("✅ Integration Test Results:")
            logger.info("   • kagent CRD manifest applied successfully")
            logger.info("   • Namespace created")
            logger.info("   • Agent resource deployed")
            if docker_success:
                logger.info("   • Docker image built and loaded")
            logger.info("")
            logger.info("🚀 Next Steps:")
            logger.info("   • Deploy kagent controller if not already running")
            logger.info("   • Monitor agent reconciliation")
            logger.info("   • Test A2A communication between agents")
            logger.info("   • Integrate with AgentGateway for MCP access")

            return True
        else:
            logger.error("❌ kagent integration tests failed")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        exit(1)
