"""
Kubernetes cluster management and operations

Handles:
- Cluster setup and validation
- Namespace and RBAC management
- Resource deployment
- Pod operations
- Service discovery
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class K8sResource:
    """Kubernetes resource"""

    api_version: str
    kind: str
    name: str
    namespace: str
    manifest: Dict[str, Any]


class K8sManager:
    """Kubernetes operations manager"""

    def __init__(self, context: str = "docker-desktop"):
        """
        Initialize K8s manager

        Args:
            context: Kubernetes context to use
        """
        self.context = context
        self._kubectl_base = ["kubectl", "--context", context]

    def check_cluster_access(self) -> bool:
        """Check if we can access the cluster"""
        try:
            cmd = self._kubectl_base + ["cluster-info"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to check cluster access: {e}")
            return False

    def create_namespace(
        self, namespace: str, labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """Create a namespace"""
        manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": namespace},
        }

        if labels:
            manifest["metadata"]["labels"] = labels

        return self.apply_manifest(manifest)

    def apply_manifest(self, manifest: Dict[str, Any]) -> bool:
        """Apply a manifest to the cluster"""
        try:
            # Convert to YAML
            yaml_content = yaml.dump(manifest, default_flow_style=False)

            # Apply via kubectl
            cmd = self._kubectl_base + ["apply", "-f", "-"]
            result = subprocess.run(
                cmd, input=yaml_content, text=True, capture_output=True
            )

            if result.returncode == 0:
                logger.info(
                    f"Applied {manifest['kind']} {manifest['metadata']['name']}"
                )
                return True
            else:
                logger.error(f"Failed to apply manifest: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error applying manifest: {e}")
            return False

    def apply_manifests_from_directory(
        self, directory: Path, namespace: Optional[str] = None
    ) -> Dict[str, bool]:
        """Apply all manifests from a directory"""
        results = {}

        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return results

        # Find all YAML files
        yaml_files = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))

        for yaml_file in yaml_files:
            try:
                cmd = self._kubectl_base + ["apply", "-f", str(yaml_file)]
                if namespace:
                    cmd.extend(["-n", namespace])

                result = subprocess.run(cmd, capture_output=True, text=True)
                results[yaml_file.name] = result.returncode == 0

                if result.returncode != 0:
                    logger.error(f"Failed to apply {yaml_file.name}: {result.stderr}")

            except Exception as e:
                logger.error(f"Error applying {yaml_file.name}: {e}")
                results[yaml_file.name] = False

        return results

    def get_resource(
        self, resource_type: str, name: str, namespace: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """Get a specific resource"""
        try:
            cmd = self._kubectl_base + [
                "get",
                resource_type,
                name,
                "-n",
                namespace,
                "-o",
                "json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting resource: {e}")
            return None

    def list_resources(
        self,
        resource_type: str,
        namespace: str = "default",
        label_selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List resources"""
        try:
            cmd = self._kubectl_base + [
                "get",
                resource_type,
                "-n",
                namespace,
                "-o",
                "json",
            ]

            if label_selector:
                cmd.extend(["-l", label_selector])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("items", [])
            else:
                logger.error(f"Failed to list resources: {result.stderr}")
                return []

        except Exception as e:
            logger.error(f"Error listing resources: {e}")
            return []

    def wait_for_deployment(
        self, deployment_name: str, namespace: str = "default", timeout: int = 300
    ) -> bool:
        """Wait for deployment to be ready"""
        try:
            cmd = self._kubectl_base + [
                "wait",
                "--for=condition=available",
                f"--timeout={timeout}s",
                f"deployment/{deployment_name}",
                "-n",
                namespace,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error waiting for deployment: {e}")
            return False

    def scale_deployment(
        self, deployment_name: str, replicas: int, namespace: str = "default"
    ) -> bool:
        """Scale a deployment"""
        try:
            cmd = self._kubectl_base + [
                "scale",
                f"deployment/{deployment_name}",
                f"--replicas={replicas}",
                "-n",
                namespace,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Scaled {deployment_name} to {replicas} replicas")
                return True
            else:
                logger.error(f"Failed to scale deployment: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error scaling deployment: {e}")
            return False

    def get_pod_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None,
        follow: bool = False,
        tail: Optional[int] = None,
    ) -> Optional[str]:
        """Get pod logs"""
        try:
            cmd = self._kubectl_base + ["logs", pod_name, "-n", namespace]

            if container:
                cmd.extend(["-c", container])
            if follow:
                cmd.append("-f")
            if tail:
                cmd.extend(["--tail", str(tail)])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Failed to get logs: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return None

    def exec_in_pod(
        self,
        pod_name: str,
        command: List[str],
        namespace: str = "default",
        container: Optional[str] = None,
    ) -> Optional[str]:
        """Execute command in pod"""
        try:
            cmd = self._kubectl_base + ["exec", pod_name, "-n", namespace]

            if container:
                cmd.extend(["-c", container])

            cmd.append("--")
            cmd.extend(command)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Failed to exec: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Error executing in pod: {e}")
            return None

    def port_forward(
        self,
        resource: str,
        local_port: int,
        remote_port: int,
        namespace: str = "default",
    ) -> subprocess.Popen:
        """Start port forwarding (returns process to manage)"""
        try:
            cmd = self._kubectl_base + [
                "port-forward",
                resource,
                f"{local_port}:{remote_port}",
                "-n",
                namespace,
            ]

            process = subprocess.Popen(cmd)
            logger.info(
                f"Started port forward: localhost:{local_port} -> {resource}:{remote_port}"
            )
            return process

        except Exception as e:
            logger.error(f"Error starting port forward: {e}")
            return None

    def create_secret(
        self,
        secret_name: str,
        namespace: str,
        data: Dict[str, str],
        secret_type: str = "Opaque",
    ) -> bool:
        """Create a secret"""
        import base64

        # Base64 encode the data
        encoded_data = {}
        for key, value in data.items():
            encoded_data[key] = base64.b64encode(value.encode()).decode()

        manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": secret_name, "namespace": namespace},
            "type": secret_type,
            "data": encoded_data,
        }

        return self.apply_manifest(manifest)

    def create_configmap(
        self, configmap_name: str, namespace: str, data: Dict[str, str]
    ) -> bool:
        """Create a ConfigMap"""
        manifest = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": configmap_name, "namespace": namespace},
            "data": data,
        }

        return self.apply_manifest(manifest)

    def rollout_restart(self, deployment_name: str, namespace: str = "default") -> bool:
        """Restart a deployment"""
        try:
            cmd = self._kubectl_base + [
                "rollout",
                "restart",
                f"deployment/{deployment_name}",
                "-n",
                namespace,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Restarted deployment {deployment_name}")
                return True
            else:
                logger.error(f"Failed to restart deployment: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error restarting deployment: {e}")
            return False

    def get_service_url(
        self,
        service_name: str,
        namespace: str = "default",
        port_name: Optional[str] = None,
    ) -> Optional[str]:
        """Get service URL"""
        service = self.get_resource("service", service_name, namespace)

        if not service:
            return None

        spec = service.get("spec", {})

        # Get port
        ports = spec.get("ports", [])
        if not ports:
            return None

        if port_name:
            port = next((p for p in ports if p.get("name") == port_name), None)
        else:
            port = ports[0]

        if not port:
            return None

        # Build URL
        return f"http://{service_name}.{namespace}.svc.cluster.local:{port['port']}"


class ClusterSetup:
    """Kubernetes cluster setup automation"""

    def __init__(self, k8s_manager: K8sManager):
        """
        Initialize cluster setup

        Args:
            k8s_manager: K8sManager instance
        """
        self.k8s = k8s_manager

    def setup_base_resources(self) -> Dict[str, bool]:
        """Setup base cluster resources"""
        results = {}

        # Create namespaces
        namespaces = [
            (
                "elf-teams",
                {"environment": "production", "managed-by": "elf-automations"},
            ),
            ("elf-monitoring", {"environment": "production", "purpose": "monitoring"}),
            ("argocd", {"environment": "production", "purpose": "gitops"}),
        ]

        for ns_name, labels in namespaces:
            results[f"namespace/{ns_name}"] = self.k8s.create_namespace(ns_name, labels)

        # Apply RBAC
        rbac_path = Path("k8s/base/rbac.yaml")
        if rbac_path.exists():
            rbac_results = self.k8s.apply_manifests_from_directory(rbac_path.parent)
            results.update(rbac_results)

        return results

    def install_argocd(self) -> bool:
        """Install ArgoCD"""
        try:
            # Check if already installed
            if self.k8s.get_resource("deployment", "argocd-server", "argocd"):
                logger.info("ArgoCD already installed")
                return True

            # Install ArgoCD
            logger.info("Installing ArgoCD...")
            cmd = [
                "kubectl",
                "apply",
                "-n",
                "argocd",
                "-f",
                "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("ArgoCD installed successfully")

                # Wait for it to be ready
                return self.k8s.wait_for_deployment(
                    "argocd-server", "argocd", timeout=300
                )
            else:
                logger.error(f"Failed to install ArgoCD: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error installing ArgoCD: {e}")
            return False

    def setup_monitoring(self) -> Dict[str, bool]:
        """Setup monitoring stack"""
        results = {}

        monitoring_path = Path("k8s/base")

        # Apply Prometheus
        if (monitoring_path / "prometheus.yaml").exists():
            results["prometheus"] = self.k8s.apply_manifest(
                yaml.safe_load((monitoring_path / "prometheus.yaml").read_text())
            )

        # Apply Grafana
        if (monitoring_path / "grafana.yaml").exists():
            results["grafana"] = self.k8s.apply_manifest(
                yaml.safe_load((monitoring_path / "grafana.yaml").read_text())
            )

        return results
