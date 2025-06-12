#!/usr/bin/env python3
"""
Agent Deployment Test Suite
Tests kagent + CrewAI agent deployment and lifecycle management.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List

from .test_runner import (
    TestResult,
    TestStatus,
    TestSuite,
    check_http_endpoint,
    run_command,
    wait_for_condition,
)


class AgentDeploymentTestSuite(TestSuite):
    """Test suite for agent deployment via kagent."""

    def __init__(self):
        super().__init__("Agent Deployment (kagent + CrewAI)")
        self.test_namespace = "elf-automations"
        self.deployed_agents = []

    async def run_tests(self) -> List[TestResult]:
        """Run all agent deployment tests."""
        tests = [
            self.test_docker_images_available,
            self.test_namespace_preparation,
            self.test_secrets_configuration,
            self.test_chief_ai_agent_deployment,
            self.test_agent_pod_health,
            self.test_agent_api_endpoints,
            self.test_crewai_task_execution,
            self.test_agent_scaling,
            self.test_agent_lifecycle_management,
        ]

        for test in tests:
            start_time = time.time()
            try:
                await test()
                duration = time.time() - start_time
                self.add_result(
                    test.__name__.replace("test_", "").replace("_", " ").title(),
                    TestStatus.PASSED,
                    duration,
                )
            except Exception as e:
                duration = time.time() - start_time
                self.add_result(
                    test.__name__.replace("test_", "").replace("_", " ").title(),
                    TestStatus.FAILED,
                    duration,
                    str(e),
                )

        # Cleanup
        await self.cleanup_test_resources()
        return self.results

    async def test_docker_images_available(self):
        """Test required Docker images are available."""
        required_images = [
            "elf-automations/distributed-agent:latest",
            "elf-automations/chief-ai-agent:latest",
        ]

        for image in required_images:
            # Check if image exists locally
            success, stdout, stderr = await run_command(
                ["docker", "images", image, "--format", "table"]
            )

            if not success or image.split(":")[0] not in stdout:
                # Try to build the image if Dockerfile exists
                dockerfile_paths = [
                    Path("agents/distributed/Dockerfile"),
                    Path("agents/distributed/docker/Dockerfile"),
                ]

                dockerfile_found = False
                for dockerfile_path in dockerfile_paths:
                    if dockerfile_path.exists():
                        success, stdout, stderr = await run_command(
                            [
                                "docker",
                                "build",
                                "-t",
                                image,
                                "-f",
                                str(dockerfile_path),
                                ".",
                            ],
                            timeout=300,
                        )  # 5 minute timeout for build

                        if not success:
                            raise Exception(f"Failed to build image {image}: {stderr}")
                        dockerfile_found = True
                        break

                if not dockerfile_found:
                    raise Exception(
                        f"Image {image} not available and no Dockerfile found"
                    )

    async def test_namespace_preparation(self):
        """Test namespace is prepared for agent deployment."""
        # Create namespace if it doesn't exist
        success, stdout, stderr = await run_command(
            ["kubectl", "create", "namespace", self.test_namespace]
        )

        # If namespace already exists, that's fine
        if not success and "already exists" not in stderr:
            raise Exception(f"Failed to create namespace: {stderr}")

        # Verify namespace is active
        success, stdout, stderr = await run_command(
            ["kubectl", "get", "namespace", self.test_namespace]
        )
        if not success:
            raise Exception(f"Namespace {self.test_namespace} not accessible")

        if "Active" not in stdout:
            raise Exception(f"Namespace {self.test_namespace} not in Active state")

    async def test_secrets_configuration(self):
        """Test required secrets are configured."""
        # Check if OpenAI API key secret exists
        success, stdout, stderr = await run_command(
            ["kubectl", "get", "secret", "openai-api-key", "-n", self.test_namespace]
        )

        if not success:
            # Create a test secret (this should be configured properly in production)
            success, stdout, stderr = await run_command(
                [
                    "kubectl",
                    "create",
                    "secret",
                    "generic",
                    "openai-api-key",
                    "--from-literal=api-key=test-key-for-integration-test",
                    "-n",
                    self.test_namespace,
                ]
            )

            if not success:
                raise Exception(f"Failed to create test secret: {stderr}")

    async def test_chief_ai_agent_deployment(self):
        """Test Chief AI Agent deployment."""
        # Deploy Chief AI Agent
        deployment_yaml = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chief-ai-agent-test
  namespace: {self.test_namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: chief-ai-agent-test
  template:
    metadata:
      labels:
        app: chief-ai-agent-test
    spec:
      containers:
      - name: chief-ai-agent
        image: elf-automations/chief-ai-agent:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8091
          name: health
        - containerPort: 8090
          name: a2a
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-api-key
              key: api-key
        - name: AGENT_ID
          value: "chief-ai-agent-test"
        - name: AGENT_ROLE
          value: "Chief Executive Officer"
        livenessProbe:
          httpGet:
            path: /health
            port: 8091
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8091
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: chief-ai-agent-test-service
  namespace: {self.test_namespace}
spec:
  selector:
    app: chief-ai-agent-test
  ports:
  - name: health
    port: 8091
    targetPort: 8091
  - name: a2a
    port: 8090
    targetPort: 8090
"""

        # Apply deployment
        process = await asyncio.create_subprocess_exec(
            "kubectl",
            "apply",
            "-f",
            "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate(deployment_yaml.encode())

        if process.returncode != 0:
            raise Exception(f"Failed to deploy Chief AI Agent: {stderr.decode()}")

        self.deployed_agents.append("chief-ai-agent-test")

    async def test_agent_pod_health(self):
        """Test agent pod is healthy and running."""

        # Wait for pod to be running
        async def pod_running():
            success, stdout, stderr = await run_command(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-n",
                    self.test_namespace,
                    "-l",
                    "app=chief-ai-agent-test",
                    "-o",
                    "jsonpath={.items[0].status.phase}",
                ]
            )
            return success and stdout.strip() == "Running"

        if not await wait_for_condition(pod_running, timeout=120):
            # Get pod status for debugging
            success, stdout, stderr = await run_command(
                [
                    "kubectl",
                    "describe",
                    "pods",
                    "-n",
                    self.test_namespace,
                    "-l",
                    "app=chief-ai-agent-test",
                ]
            )
            raise Exception(f"Pod not running within timeout. Status: {stdout}")

        # Check pod is ready
        async def pod_ready():
            success, stdout, stderr = await run_command(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-n",
                    self.test_namespace,
                    "-l",
                    "app=chief-ai-agent-test",
                    "-o",
                    'jsonpath={.items[0].status.conditions[?(@.type=="Ready")].status}',
                ]
            )
            return success and stdout.strip() == "True"

        if not await wait_for_condition(pod_ready, timeout=60):
            raise Exception("Pod not ready within timeout")

    async def test_agent_api_endpoints(self):
        """Test agent API endpoints are accessible."""
        # Port forward to access the service
        port_forward_process = await asyncio.create_subprocess_exec(
            "kubectl",
            "port-forward",
            f"service/chief-ai-agent-test-service",
            "18091:8091",
            "-n",
            self.test_namespace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait a moment for port forward to establish
        await asyncio.sleep(3)

        try:
            # Test health endpoint
            success, message = await check_http_endpoint(
                "http://localhost:18091/health"
            )
            if not success:
                raise Exception(f"Health endpoint not accessible: {message}")

            # Test ready endpoint
            success, message = await check_http_endpoint("http://localhost:18091/ready")
            if not success:
                raise Exception(f"Ready endpoint not accessible: {message}")

        finally:
            # Clean up port forward
            port_forward_process.terminate()
            await port_forward_process.wait()

    async def test_crewai_task_execution(self):
        """Test CrewAI task execution within the agent."""
        # This would typically involve calling the agent's API to execute a task
        # For now, we'll check that the agent logs show CrewAI activity

        success, stdout, stderr = await run_command(
            [
                "kubectl",
                "logs",
                "-n",
                self.test_namespace,
                "-l",
                "app=chief-ai-agent-test",
                "--tail=50",
            ]
        )

        if not success:
            raise Exception(f"Failed to get agent logs: {stderr}")

        # Look for CrewAI-related log entries
        crewai_indicators = [
            "CrewAI",
            "Agent",
            "Task",
            "Chief Executive Officer",
            "strategic planning",
        ]

        log_content = stdout.lower()
        found_indicators = [
            indicator
            for indicator in crewai_indicators
            if indicator.lower() in log_content
        ]

        if len(found_indicators) < 2:
            raise Exception(
                f"CrewAI activity not detected in logs. Found: {found_indicators}"
            )

    async def test_agent_scaling(self):
        """Test agent scaling capabilities."""
        # Scale up the deployment
        success, stdout, stderr = await run_command(
            [
                "kubectl",
                "scale",
                "deployment",
                "chief-ai-agent-test",
                "--replicas=2",
                "-n",
                self.test_namespace,
            ]
        )

        if not success:
            raise Exception(f"Failed to scale deployment: {stderr}")

        # Wait for scale up
        async def scaled_up():
            success, stdout, stderr = await run_command(
                [
                    "kubectl",
                    "get",
                    "deployment",
                    "chief-ai-agent-test",
                    "-n",
                    self.test_namespace,
                    "-o",
                    "jsonpath={.status.readyReplicas}",
                ]
            )
            return success and stdout.strip() == "2"

        if not await wait_for_condition(scaled_up, timeout=60):
            raise Exception("Deployment did not scale up within timeout")

        # Scale back down
        success, stdout, stderr = await run_command(
            [
                "kubectl",
                "scale",
                "deployment",
                "chief-ai-agent-test",
                "--replicas=1",
                "-n",
                self.test_namespace,
            ]
        )

        if not success:
            raise Exception(f"Failed to scale down deployment: {stderr}")

    async def test_agent_lifecycle_management(self):
        """Test agent lifecycle management operations."""
        # Test deployment update (rolling update)
        success, stdout, stderr = await run_command(
            [
                "kubectl",
                "patch",
                "deployment",
                "chief-ai-agent-test",
                "-n",
                self.test_namespace,
                "-p",
                '{"spec":{"template":{"metadata":{"labels":{"version":"test-update"}}}}}',
            ]
        )

        if not success:
            raise Exception(f"Failed to update deployment: {stderr}")

        # Wait for rollout to complete
        success, stdout, stderr = await run_command(
            [
                "kubectl",
                "rollout",
                "status",
                "deployment/chief-ai-agent-test",
                "-n",
                self.test_namespace,
                "--timeout=60s",
            ]
        )

        if not success:
            raise Exception(f"Deployment rollout failed: {stderr}")

    async def cleanup_test_resources(self):
        """Clean up test resources."""
        for agent in self.deployed_agents:
            await run_command(
                ["kubectl", "delete", "deployment", agent, "-n", self.test_namespace]
            )
            await run_command(
                [
                    "kubectl",
                    "delete",
                    "service",
                    f"{agent}-service",
                    "-n",
                    self.test_namespace,
                ]
            )


# Standalone test runner for this suite
async def main():
    """Run agent deployment tests standalone."""
    from .test_runner import TestRunner

    runner = TestRunner()
    runner.add_suite(AgentDeploymentTestSuite())

    success = await runner.run_all_tests()
    return success


if __name__ == "__main__":
    import sys

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
