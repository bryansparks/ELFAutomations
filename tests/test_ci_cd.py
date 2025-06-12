"""
Test suite for CI/CD pipeline validation
"""
import asyncio
import os
import subprocess
from pathlib import Path

import pytest
import yaml


class TestCICDPipeline:
    """Test CI/CD pipeline components"""

    def test_github_workflows_exist(self):
        """Test that GitHub workflow files exist"""
        workflows_dir = Path(".github/workflows")
        assert workflows_dir.exists(), "GitHub workflows directory not found"

        ci_workflow = workflows_dir / "ci.yml"
        security_workflow = workflows_dir / "security.yml"

        assert ci_workflow.exists(), "CI workflow file not found"
        assert security_workflow.exists(), "Security workflow file not found"

    def test_workflow_yaml_valid(self):
        """Test that workflow YAML files are valid"""
        workflows_dir = Path(".github/workflows")

        for workflow_file in workflows_dir.glob("*.yml"):
            with open(workflow_file, "r") as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {workflow_file}: {e}")

    def test_dockerfiles_exist(self):
        """Test that Dockerfiles exist for all components"""
        docker_dir = Path("docker")
        assert docker_dir.exists(), "Docker directory not found"

        web_dockerfile = docker_dir / "web" / "Dockerfile"
        agents_dockerfile = docker_dir / "agents" / "Dockerfile"

        assert web_dockerfile.exists(), "Web Dockerfile not found"
        assert agents_dockerfile.exists(), "Agents Dockerfile not found"

    def test_kubernetes_manifests_exist(self):
        """Test that Kubernetes manifests exist for staging and production"""
        k8s_dir = Path("k8s")
        assert k8s_dir.exists(), "Kubernetes directory not found"

        # Check staging manifests
        staging_dir = k8s_dir / "staging"
        assert staging_dir.exists(), "Staging directory not found"
        assert (staging_dir / "web-deployment.yaml").exists()
        assert (staging_dir / "agents-deployment.yaml").exists()
        assert (staging_dir / "namespace.yaml").exists()

        # Check production manifests
        production_dir = k8s_dir / "production"
        assert production_dir.exists(), "Production directory not found"
        assert (production_dir / "web-deployment.yaml").exists()
        assert (production_dir / "agents-deployment.yaml").exists()

    def test_kubernetes_yaml_valid(self):
        """Test that Kubernetes YAML files are valid"""
        k8s_dir = Path("k8s")

        for yaml_file in k8s_dir.rglob("*.yaml"):
            with open(yaml_file, "r") as f:
                try:
                    # Load all documents in the file
                    documents = list(yaml.safe_load_all(f))
                    assert len(documents) > 0, f"No documents found in {yaml_file}"

                    for doc in documents:
                        if doc is not None:
                            assert (
                                "apiVersion" in doc
                            ), f"Missing apiVersion in {yaml_file}"
                            assert "kind" in doc, f"Missing kind in {yaml_file}"
                            assert "metadata" in doc, f"Missing metadata in {yaml_file}"

                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {yaml_file}: {e}")

    def test_docker_build_web(self):
        """Test that web Docker image can be built"""
        if not os.getenv("CI"):
            pytest.skip("Skipping Docker build test in local environment")

        try:
            result = subprocess.run(
                [
                    "docker",
                    "build",
                    "-t",
                    "test-web:latest",
                    "-f",
                    "docker/web/Dockerfile",
                    ".",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            assert result.returncode == 0, f"Docker build failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            pytest.fail("Docker build timed out")

    def test_docker_build_agents(self):
        """Test that agents Docker image can be built"""
        if not os.getenv("CI"):
            pytest.skip("Skipping Docker build test in local environment")

        try:
            result = subprocess.run(
                [
                    "docker",
                    "build",
                    "-t",
                    "test-agents:latest",
                    "-f",
                    "docker/agents/Dockerfile",
                    ".",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            assert result.returncode == 0, f"Docker build failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            pytest.fail("Docker build timed out")

    def test_security_tools_config(self):
        """Test that security tools are properly configured"""
        # Check for security scanning in workflows
        ci_workflow = Path(".github/workflows/ci.yml")
        with open(ci_workflow, "r") as f:
            content = f.read()
            assert "safety check" in content, "Safety check not found in CI"
            assert "bandit" in content, "Bandit security scan not found in CI"
            assert (
                "trivy" in content.lower()
            ), "Trivy vulnerability scan not found in CI"

    def test_code_quality_gates(self):
        """Test that code quality gates are configured"""
        ci_workflow = Path(".github/workflows/ci.yml")
        with open(ci_workflow, "r") as f:
            content = f.read()
            assert "black --check" in content, "Black formatting check not found"
            assert "isort --check" in content, "Import sorting check not found"
            assert "flake8" in content, "Flake8 linting not found"
            assert "mypy" in content, "Type checking not found"

    def test_test_coverage_config(self):
        """Test that test coverage is configured"""
        ci_workflow = Path(".github/workflows/ci.yml")
        with open(ci_workflow, "r") as f:
            content = f.read()
            assert "pytest" in content, "Pytest not found in CI"
            assert "--cov" in content, "Coverage reporting not found"
            assert "codecov" in content, "Codecov upload not found"

    @pytest.mark.asyncio
    async def test_deployment_environments(self):
        """Test that deployment environments are properly configured"""
        # Check staging environment
        staging_ns = Path("k8s/staging/namespace.yaml")
        with open(staging_ns, "r") as f:
            content = f.read()
            assert "virtual-ai-platform-staging" in content
            assert "environment: staging" in content

        # Check production has HPA
        prod_web = Path("k8s/production/web-deployment.yaml")
        with open(prod_web, "r") as f:
            content = f.read()
            assert "HorizontalPodAutoscaler" in content
            assert "minReplicas: 3" in content


class TestSecurityConfiguration:
    """Test security configuration"""

    def test_secret_management(self):
        """Test that secrets are properly configured"""
        staging_ns = Path("k8s/staging/namespace.yaml")
        with open(staging_ns, "r") as f:
            content = f.read()
            assert "supabase-secrets" in content
            assert "ai-api-secrets" in content
            assert "PLACEHOLDER" in content, "Secrets should use placeholders"

    def test_security_context(self):
        """Test that security contexts are configured"""
        web_deployment = Path("k8s/staging/web-deployment.yaml")
        with open(web_deployment, "r") as f:
            content = f.read()
            assert "runAsNonRoot: true" in content
            assert "allowPrivilegeEscalation: false" in content
            assert "readOnlyRootFilesystem: true" in content

    def test_rbac_configuration(self):
        """Test that RBAC is properly configured"""
        agents_deployment = Path("k8s/staging/agents-deployment.yaml")
        with open(agents_deployment, "r") as f:
            content = f.read()
            assert "ServiceAccount" in content
            assert "Role" in content
            assert "RoleBinding" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
