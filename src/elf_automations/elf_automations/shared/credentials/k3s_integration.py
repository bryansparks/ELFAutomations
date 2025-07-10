"""
K3s/Kubernetes integration for credential management
"""

import base64
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..utils.logging import setup_logger
from .credential_manager import CredentialManager, CredentialType

logger = setup_logger(__name__)


class K3sSecretManager:
    """
    Manage Kubernetes secrets for teams in k3s
    """

    def __init__(
        self, credential_manager: CredentialManager, namespace: str = "elf-teams"
    ):
        self.cred_manager = credential_manager
        self.namespace = namespace

    def create_team_secret(self, team_name: str) -> Dict[str, Any]:
        """
        Create a Kubernetes secret for a team with all their credentials
        """

        # Get all credentials the team can access
        credentials = self._get_team_credentials(team_name)

        if not credentials:
            logger.warning(f"No credentials found for team {team_name}")
            return {}

        # Build secret manifest
        secret_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{team_name}-credentials",
                "namespace": self.namespace,
                "labels": {
                    "app.kubernetes.io/managed-by": "elf-automations",
                    "elf.dev/team": team_name,
                },
            },
            "type": "Opaque",
            "data": {},
        }

        # Add each credential as base64 encoded
        for cred_name, cred_value in credentials.items():
            encoded_value = base64.b64encode(cred_value.encode()).decode()
            secret_manifest["data"][cred_name] = encoded_value

        return secret_manifest

    def _get_team_credentials(self, team_name: str) -> Dict[str, str]:
        """Get all credentials a team can access"""
        credentials = {}

        # Get credential patterns the team can access
        patterns = self.cred_manager.access_control.get_team_credentials(team_name)

        # Get all credentials
        all_creds = self.cred_manager.list_credentials()

        for cred in all_creds:
            # Check if team can access this credential
            if self.cred_manager.access_control.can_access(team_name, cred.name):
                try:
                    value = self.cred_manager.get_credential(
                        cred.name, team_name, purpose="k8s_deployment"
                    )
                    credentials[cred.name] = value
                except Exception as e:
                    logger.error(
                        f"Failed to get credential {cred.name} for team {team_name}: {e}"
                    )

        return credentials

    def apply_secret(self, team_name: str) -> bool:
        """Apply the secret to k3s cluster"""

        # Create secret manifest
        manifest = self.create_team_secret(team_name)

        if not manifest:
            return False

        # Write to temp file
        temp_file = Path(f"/tmp/{team_name}-secret.yaml")
        with open(temp_file, "w") as f:
            yaml.dump(manifest, f)

        try:
            # Apply using kubectl
            result = subprocess.run(
                ["kubectl", "apply", "-f", str(temp_file)],
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Applied secret for team {team_name}: {result.stdout}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply secret: {e.stderr}")
            return False

        finally:
            # Clean up temp file
            temp_file.unlink(missing_ok=True)

    def update_deployment_with_secret(
        self, team_name: str, deployment_path: Path
    ) -> bool:
        """Update a deployment YAML to use the team's secret"""

        try:
            # Read deployment
            with open(deployment_path, "r") as f:
                deployment = yaml.safe_load(f)

            # Find container spec
            containers = deployment["spec"]["template"]["spec"]["containers"]

            for container in containers:
                # Add envFrom to use all secret values
                if "envFrom" not in container:
                    container["envFrom"] = []

                # Add secret ref
                secret_ref = {"secretRef": {"name": f"{team_name}-credentials"}}

                # Avoid duplicates
                if secret_ref not in container["envFrom"]:
                    container["envFrom"].append(secret_ref)

            # Write updated deployment
            with open(deployment_path, "w") as f:
                yaml.dump(deployment, f, default_flow_style=False)

            logger.info(
                f"Updated deployment for team {team_name} to use credentials secret"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update deployment: {e}")
            return False

    def create_sealed_secret(
        self, team_name: str, output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Create a SealedSecret for GitOps (requires kubeseal installed)
        This allows safe storage of encrypted secrets in Git
        """

        # First create the regular secret
        manifest = self.create_team_secret(team_name)

        if not manifest:
            return None

        # Write to temp file
        temp_secret = Path(f"/tmp/{team_name}-secret.yaml")
        with open(temp_secret, "w") as f:
            yaml.dump(manifest, f)

        # Output path for sealed secret
        if not output_path:
            output_path = Path(f"k8s/teams/{team_name}/sealed-secret.yaml")
            output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Seal the secret using kubeseal
            result = subprocess.run(
                [
                    "kubeseal",
                    "--format",
                    "yaml",
                    "--cert",
                    "/etc/kubeseal/cert.pem",  # Update path as needed
                    "-f",
                    str(temp_secret),
                    "-o",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Created sealed secret for team {team_name} at {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create sealed secret: {e.stderr}")
            logger.info("Make sure kubeseal is installed and configured")
            return None

        except FileNotFoundError:
            logger.error("kubeseal not found. For k3s, you can install Sealed Secrets:")
            logger.info(
                "kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml"
            )
            return None

        finally:
            # Clean up temp file
            temp_secret.unlink(missing_ok=True)

    def rotate_team_credentials(self, team_name: str) -> bool:
        """Rotate all credentials for a team"""

        rotated = []
        failed = []

        # Get team credentials
        credentials = self._get_team_credentials(team_name)

        for cred_name in credentials:
            try:
                # Rotate the credential
                self.cred_manager.rotate_credential(cred_name, team_name)
                rotated.append(cred_name)

            except Exception as e:
                logger.error(f"Failed to rotate {cred_name}: {e}")
                failed.append(cred_name)

        # Reapply the secret with new values
        if rotated:
            success = self.apply_secret(team_name)
            if success:
                logger.info(f"Rotated {len(rotated)} credentials for team {team_name}")

                # Restart deployment to pick up new credentials
                self._restart_deployment(team_name)

            return success

        return False

    def _restart_deployment(self, team_name: str) -> bool:
        """Restart a team's deployment to pick up new credentials"""

        try:
            # Restart by updating an annotation
            result = subprocess.run(
                [
                    "kubectl",
                    "-n",
                    self.namespace,
                    "patch",
                    "deployment",
                    team_name,
                    "-p",
                    '{"spec":{"template":{"metadata":{"annotations":{"credential-rotation":"'
                    + f"{datetime.now().isoformat()}"
                    + '"}}}}}',
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Restarted deployment for team {team_name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart deployment: {e.stderr}")
            return False

    def generate_rbac_for_secret(self, team_name: str) -> Dict[str, Any]:
        """Generate RBAC rules for team to access their secret"""

        return {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {
                "name": f"{team_name}-secret-reader",
                "namespace": self.namespace,
            },
            "rules": [
                {
                    "apiGroups": [""],
                    "resources": ["secrets"],
                    "resourceNames": [f"{team_name}-credentials"],
                    "verbs": ["get", "list"],
                }
            ],
        }

    def create_emergency_access_secret(
        self, reason: str, created_by: str
    ) -> Dict[str, Any]:
        """Create emergency break-glass secret with all credentials"""

        # This should be used sparingly and with proper authorization
        logger.critical(
            f"Creating emergency access secret - Reason: {reason}, By: {created_by}"
        )

        # Get all credentials (executive team access)
        all_credentials = self._get_team_credentials("executive-team")

        # Create secret with expiration annotation
        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "emergency-access-credentials",
                "namespace": self.namespace,
                "annotations": {
                    "elf.dev/expires-at": (
                        datetime.now() + timedelta(hours=1)
                    ).isoformat(),
                    "elf.dev/created-by": created_by,
                    "elf.dev/reason": reason,
                },
                "labels": {"elf.dev/emergency-access": "true"},
            },
            "type": "Opaque",
            "data": {
                k: base64.b64encode(v.encode()).decode()
                for k, v in all_credentials.items()
            },
        }
