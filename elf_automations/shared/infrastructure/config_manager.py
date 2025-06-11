"""
Configuration management for infrastructure automation

Handles:
- Environment variables
- Configuration files
- Secrets management
- Dynamic configuration updates
"""

import base64
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentConfig:
    """Environment configuration"""

    name: str  # e.g., "development", "staging", "production"
    k8s_context: str
    k8s_namespace: str
    docker_registry: str
    argocd_repo: str
    argocd_branch: str
    monitoring_enabled: bool = True
    secrets: Dict[str, str] = None

    def __post_init__(self):
        if self.secrets is None:
            self.secrets = {}


class ConfigManager:
    """Centralized configuration management"""

    DEFAULT_CONFIGS = {
        "development": EnvironmentConfig(
            name="development",
            k8s_context="docker-desktop",
            k8s_namespace="elf-teams",
            docker_registry="localhost:5000",
            argocd_repo="https://github.com/bryansparks/ELFAutomations.git",
            argocd_branch="main",
        ),
        "staging": EnvironmentConfig(
            name="staging",
            k8s_context="orbstack",
            k8s_namespace="elf-teams-staging",
            docker_registry="localhost:5000",
            argocd_repo="https://github.com/bryansparks/ELFAutomations.git",
            argocd_branch="staging",
        ),
        "production": EnvironmentConfig(
            name="production",
            k8s_context="production-cluster",
            k8s_namespace="elf-teams",
            docker_registry="registry.elf-automations.io",
            argocd_repo="https://github.com/bryansparks/ELFAutomations.git",
            argocd_branch="production",
        ),
    }

    def __init__(
        self, config_path: Optional[Path] = None, environment: str = "development"
    ):
        """
        Initialize config manager

        Args:
            config_path: Path to configuration directory
            environment: Environment name
        """
        self.config_path = config_path or Path.home() / ".elf_automations" / "config"
        self.config_path.mkdir(parents=True, exist_ok=True)

        self.environment = environment
        self._cipher_suite = None

        # Load or create environment config
        self.env_config = self._load_environment_config()

    def _load_environment_config(self) -> EnvironmentConfig:
        """Load environment configuration"""
        config_file = self.config_path / f"{self.environment}.yaml"

        if config_file.exists():
            logger.info(f"Loading config from {config_file}")
            with open(config_file) as f:
                data = yaml.safe_load(f)
                return EnvironmentConfig(**data)
        else:
            # Use default and save it
            logger.info(f"Creating default config for {self.environment}")
            config = self.DEFAULT_CONFIGS.get(
                self.environment, self.DEFAULT_CONFIGS["development"]
            )
            self._save_environment_config(config)
            return config

    def _save_environment_config(self, config: EnvironmentConfig):
        """Save environment configuration"""
        config_file = self.config_path / f"{config.name}.yaml"

        # Convert to dict, excluding secrets
        data = {
            "name": config.name,
            "k8s_context": config.k8s_context,
            "k8s_namespace": config.k8s_namespace,
            "docker_registry": config.docker_registry,
            "argocd_repo": config.argocd_repo,
            "argocd_branch": config.argocd_branch,
            "monitoring_enabled": config.monitoring_enabled,
        }

        with open(config_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        logger.info(f"Saved config to {config_file}")

    def get_required_env_vars(self) -> List[str]:
        """Get list of required environment variables"""
        required = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_KEY",
        ]

        # Add environment-specific vars
        if self.environment == "production":
            required.extend(["SLACK_WEBHOOK_URL", "PAGERDUTY_API_KEY"])

        return required

    def validate_environment(self) -> Dict[str, Any]:
        """Validate environment configuration"""
        validation = {"valid": True, "missing": [], "warnings": []}

        # Check required env vars
        for var in self.get_required_env_vars():
            if not os.getenv(var):
                validation["valid"] = False
                validation["missing"].append(var)

        # Check optional but recommended vars
        optional_vars = ["GITHUB_TOKEN", "DOCKER_USERNAME", "DOCKER_PASSWORD"]
        for var in optional_vars:
            if not os.getenv(var):
                validation["warnings"].append(f"{var} not set (optional)")

        return validation

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value"""
        # First check environment
        env_value = os.getenv(key)
        if env_value:
            return env_value

        # Then check encrypted secrets
        if key in self.env_config.secrets:
            return self._decrypt_secret(self.env_config.secrets[key])

        return None

    def set_secret(self, key: str, value: str, encrypt: bool = True):
        """Set a secret value"""
        if encrypt:
            self.env_config.secrets[key] = self._encrypt_secret(value)
            self._save_secrets()
        else:
            # Just set in environment
            os.environ[key] = value

    def _get_cipher_suite(self) -> Fernet:
        """Get or create cipher suite for encryption"""
        if self._cipher_suite:
            return self._cipher_suite

        key_file = self.config_path / ".encryption_key"

        if key_file.exists():
            key = key_file.read_bytes()
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Restrict permissions

        self._cipher_suite = Fernet(key)
        return self._cipher_suite

    def _encrypt_secret(self, value: str) -> str:
        """Encrypt a secret value"""
        cipher = self._get_cipher_suite()
        encrypted = cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt_secret(self, encrypted: str) -> str:
        """Decrypt a secret value"""
        cipher = self._get_cipher_suite()
        encrypted_bytes = base64.b64decode(encrypted.encode())
        decrypted = cipher.decrypt(encrypted_bytes)
        return decrypted.decode()

    def _save_secrets(self):
        """Save encrypted secrets"""
        secrets_file = self.config_path / f"{self.environment}_secrets.json"

        with open(secrets_file, "w") as f:
            json.dump(self.env_config.secrets, f)

        secrets_file.chmod(0o600)  # Restrict permissions

    def generate_k8s_secret_manifest(
        self, secret_name: str, namespace: str, keys: List[str]
    ) -> str:
        """Generate Kubernetes secret manifest"""

        # Collect secret data
        secret_data = {}
        for key in keys:
            value = self.get_secret(key)
            if value:
                # Base64 encode for K8s
                encoded = base64.b64encode(value.encode()).decode()
                secret_data[key] = encoded
            else:
                logger.warning(f"Secret {key} not found")

        # Generate manifest
        manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": secret_name, "namespace": namespace},
            "type": "Opaque",
            "data": secret_data,
        }

        return yaml.dump(manifest, default_flow_style=False)

    def export_env_file(self, output_path: Optional[Path] = None) -> Path:
        """Export environment variables to .env file"""
        if not output_path:
            output_path = Path(".env")

        lines = []

        # Add required vars
        for var in self.get_required_env_vars():
            value = self.get_secret(var) or ""
            lines.append(f"{var}={value}")

        # Add infrastructure vars
        lines.extend(
            [
                f"ENVIRONMENT={self.environment}",
                f"K8S_CONTEXT={self.env_config.k8s_context}",
                f"K8S_NAMESPACE={self.env_config.k8s_namespace}",
                f"DOCKER_REGISTRY={self.env_config.docker_registry}",
                f"ARGOCD_REPO={self.env_config.argocd_repo}",
                f"ARGOCD_BRANCH={self.env_config.argocd_branch}",
            ]
        )

        output_path.write_text("\n".join(lines))
        output_path.chmod(0o600)  # Restrict permissions

        logger.info(f"Exported environment to {output_path}")
        return output_path

    def get_docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration"""
        return {
            "registry": self.env_config.docker_registry,
            "username": os.getenv("DOCKER_USERNAME"),
            "password": self.get_secret("DOCKER_PASSWORD"),
            "insecure_registries": ["localhost:5000"]
            if "localhost" in self.env_config.docker_registry
            else [],
        }

    def get_k8s_config(self) -> Dict[str, Any]:
        """Get Kubernetes configuration"""
        return {
            "context": self.env_config.k8s_context,
            "namespace": self.env_config.k8s_namespace,
            "image_pull_policy": "Never"
            if "localhost" in self.env_config.docker_registry
            else "Always",
        }

    def update_team_config(self, team_name: str, config_updates: Dict[str, Any]):
        """Update team-specific configuration"""
        team_config_file = self.config_path / "teams" / f"{team_name}.yaml"
        team_config_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing or create new
        if team_config_file.exists():
            with open(team_config_file) as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

        # Update
        config.update(config_updates)

        # Save
        with open(team_config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        logger.info(f"Updated config for team {team_name}")
