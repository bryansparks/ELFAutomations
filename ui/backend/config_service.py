"""
YAML Configuration Management Service
Handles CRUD operations for agent and crew YAML configurations
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Agent configuration model"""

    apiVersion: str = "kagent.dev/v1alpha1"
    kind: str = "Agent"
    metadata: Dict[str, Any]
    spec: Dict[str, Any]


class CrewConfig(BaseModel):
    """Crew configuration model"""

    apiVersion: str = "kagent.dev/v1alpha1"
    kind: str = "Team"
    metadata: Dict[str, Any]
    spec: Dict[str, Any]


class ConfigValidationError(Exception):
    """Configuration validation error"""

    pass


class ConfigService:
    """Service for managing YAML configurations"""

    def __init__(self, config_root: str = None):
        """Initialize configuration service"""
        if config_root is None:
            # Default to project root + agent-configs
            project_root = Path(__file__).parent.parent.parent
            config_root = project_root / "agent-configs"

        self.config_root = Path(config_root)
        self.agents_dir = self.config_root / "agents"
        self.crews_dir = self.config_root / "crews"
        self.templates_dir = self.config_root / "templates"

        # Ensure directories exist
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.crews_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse YAML file"""
        try:
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading YAML file {file_path}: {e}")
            raise ConfigValidationError(f"Failed to load YAML file: {e}")

    def _save_yaml_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save data to YAML file"""
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            logger.error(f"Error saving YAML file {file_path}: {e}")
            raise ConfigValidationError(f"Failed to save YAML file: {e}")

    def _validate_agent_config(self, config: Dict[str, Any]) -> AgentConfig:
        """Validate agent configuration"""
        try:
            return AgentConfig(**config)
        except ValidationError as e:
            raise ConfigValidationError(f"Invalid agent configuration: {e}")

    def _validate_crew_config(self, config: Dict[str, Any]) -> CrewConfig:
        """Validate crew configuration"""
        try:
            return CrewConfig(**config)
        except ValidationError as e:
            raise ConfigValidationError(f"Invalid crew configuration: {e}")

    def _get_department_from_labels(self, config: Dict[str, Any]) -> str:
        """Extract department from config labels"""
        return config.get("metadata", {}).get("labels", {}).get("department", "unknown")

    def _get_agent_file_path(self, name: str, department: str = None) -> Path:
        """Get file path for agent configuration"""
        if department:
            return self.agents_dir / department / f"{name}.yaml"

        # Search across all departments
        for dept_dir in self.agents_dir.iterdir():
            if dept_dir.is_dir():
                agent_file = dept_dir / f"{name}.yaml"
                if agent_file.exists():
                    return agent_file

        # Default to unknown department
        return self.agents_dir / "unknown" / f"{name}.yaml"

    def _get_crew_file_path(self, name: str) -> Path:
        """Get file path for crew configuration"""
        return self.crews_dir / f"{name}.yaml"

    # Agent Configuration Methods

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agent configurations"""
        agents = []

        for dept_dir in self.agents_dir.iterdir():
            if dept_dir.is_dir():
                for agent_file in dept_dir.glob("*.yaml"):
                    try:
                        config = self._load_yaml_file(agent_file)
                        config["_file_path"] = str(
                            agent_file.relative_to(self.config_root)
                        )
                        config["_department"] = dept_dir.name
                        agents.append(config)
                    except Exception as e:
                        logger.error(f"Error loading agent config {agent_file}: {e}")

        return agents

    def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific agent configuration"""
        agent_file = self._get_agent_file_path(name)

        if not agent_file.exists():
            return None

        try:
            config = self._load_yaml_file(agent_file)
            config["_file_path"] = str(agent_file.relative_to(self.config_root))
            config["_department"] = agent_file.parent.name
            return config
        except Exception as e:
            logger.error(f"Error loading agent config {name}: {e}")
            return None

    def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new agent configuration"""
        # Validate configuration
        validated_config = self._validate_agent_config(config)

        name = validated_config.metadata["name"]
        department = self._get_department_from_labels(config)

        agent_file = self._get_agent_file_path(name, department)

        if agent_file.exists():
            raise ConfigValidationError(f"Agent configuration {name} already exists")

        # Save configuration
        self._save_yaml_file(agent_file, config)

        # Return saved configuration with metadata
        result = config.copy()
        result["_file_path"] = str(agent_file.relative_to(self.config_root))
        result["_department"] = department
        result["_created"] = datetime.now().isoformat()

        return result

    def update_agent(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing agent configuration"""
        # Validate configuration
        validated_config = self._validate_agent_config(config)

        # Ensure name matches
        if validated_config.metadata["name"] != name:
            raise ConfigValidationError(
                "Agent name in configuration must match URL parameter"
            )

        agent_file = self._get_agent_file_path(name)

        if not agent_file.exists():
            raise ConfigValidationError(f"Agent configuration {name} does not exist")

        # Save updated configuration
        self._save_yaml_file(agent_file, config)

        # Return updated configuration with metadata
        result = config.copy()
        result["_file_path"] = str(agent_file.relative_to(self.config_root))
        result["_department"] = agent_file.parent.name
        result["_updated"] = datetime.now().isoformat()

        return result

    def delete_agent(self, name: str) -> bool:
        """Delete agent configuration"""
        agent_file = self._get_agent_file_path(name)

        if not agent_file.exists():
            return False

        try:
            agent_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting agent config {name}: {e}")
            raise ConfigValidationError(f"Failed to delete agent configuration: {e}")

    # Crew Configuration Methods

    def list_crews(self) -> List[Dict[str, Any]]:
        """List all crew configurations"""
        crews = []

        for crew_file in self.crews_dir.glob("*.yaml"):
            try:
                config = self._load_yaml_file(crew_file)
                config["_file_path"] = str(crew_file.relative_to(self.config_root))
                crews.append(config)
            except Exception as e:
                logger.error(f"Error loading crew config {crew_file}: {e}")

        return crews

    def get_crew(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific crew configuration"""
        crew_file = self._get_crew_file_path(name)

        if not crew_file.exists():
            return None

        try:
            config = self._load_yaml_file(crew_file)
            config["_file_path"] = str(crew_file.relative_to(self.config_root))
            return config
        except Exception as e:
            logger.error(f"Error loading crew config {name}: {e}")
            return None

    def create_crew(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new crew configuration"""
        # Validate configuration
        validated_config = self._validate_crew_config(config)

        name = validated_config.metadata["name"]
        crew_file = self._get_crew_file_path(name)

        if crew_file.exists():
            raise ConfigValidationError(f"Crew configuration {name} already exists")

        # Save configuration
        self._save_yaml_file(crew_file, config)

        # Return saved configuration with metadata
        result = config.copy()
        result["_file_path"] = str(crew_file.relative_to(self.config_root))
        result["_created"] = datetime.now().isoformat()

        return result

    def update_crew(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing crew configuration"""
        # Validate configuration
        validated_config = self._validate_crew_config(config)

        # Ensure name matches
        if validated_config.metadata["name"] != name:
            raise ConfigValidationError(
                "Crew name in configuration must match URL parameter"
            )

        crew_file = self._get_crew_file_path(name)

        if not crew_file.exists():
            raise ConfigValidationError(f"Crew configuration {name} does not exist")

        # Save updated configuration
        self._save_yaml_file(crew_file, config)

        # Return updated configuration with metadata
        result = config.copy()
        result["_file_path"] = str(crew_file.relative_to(self.config_root))
        result["_updated"] = datetime.now().isoformat()

        return result

    def delete_crew(self, name: str) -> bool:
        """Delete crew configuration"""
        crew_file = self._get_crew_file_path(name)

        if not crew_file.exists():
            return False

        try:
            crew_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting crew config {name}: {e}")
            raise ConfigValidationError(f"Failed to delete crew configuration: {e}")

    # Template Methods

    def get_agent_template(self) -> Dict[str, Any]:
        """Get agent configuration template"""
        template_file = self.templates_dir / "agent-template.yaml"

        if not template_file.exists():
            # Return default template
            return {
                "apiVersion": "kagent.dev/v1alpha1",
                "kind": "Agent",
                "metadata": {
                    "name": "agent-name",
                    "namespace": "elf-automations",
                    "labels": {
                        "app": "elf-automations",
                        "component": "agent",
                        "department": "department-name",
                        "agent-type": "agent-type",
                        "version": "v1.0.0",
                    },
                },
                "spec": {
                    "description": "Agent description",
                    "systemMessage": "Detailed system prompt and instructions",
                    "modelConfig": "anthropic-claude",
                    "tools": [],
                    "resources": {
                        "requests": {"memory": "256Mi", "cpu": "100m"},
                        "limits": {"memory": "512Mi", "cpu": "200m"},
                    },
                },
            }

        return self._load_yaml_file(template_file)

    def get_crew_template(self) -> Dict[str, Any]:
        """Get crew configuration template"""
        template_file = self.templates_dir / "crew-template.yaml"

        if not template_file.exists():
            # Return default template
            return {
                "apiVersion": "kagent.dev/v1alpha1",
                "kind": "Team",
                "metadata": {
                    "name": "crew-name",
                    "namespace": "elf-automations",
                    "labels": {
                        "app": "elf-automations",
                        "component": "team",
                        "department": "department-name",
                        "version": "v1.0.0",
                    },
                },
                "spec": {
                    "description": "Crew description",
                    "agents": [],
                    "workflow": {"type": "sequential", "steps": []},
                },
            }

        return self._load_yaml_file(template_file)

    # Utility Methods

    def get_departments(self) -> List[str]:
        """Get list of all departments"""
        departments = []

        for dept_dir in self.agents_dir.iterdir():
            if dept_dir.is_dir():
                departments.append(dept_dir.name)

        return sorted(departments)

    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of all configurations"""
        agents = self.list_agents()
        crews = self.list_crews()
        departments = self.get_departments()

        return {
            "agents": {
                "total": len(agents),
                "by_department": {
                    dept: len([a for a in agents if a.get("_department") == dept])
                    for dept in departments
                },
            },
            "crews": {"total": len(crews)},
            "departments": departments,
            "last_updated": datetime.now().isoformat(),
        }
