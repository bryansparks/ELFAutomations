"""
A2A configuration generator.
"""

from pathlib import Path
from typing import Any, Dict

import yaml

from ...models import TeamSpecification
from ..base import BaseGenerator


class A2AConfigGenerator(BaseGenerator):
    """Generates A2A configuration for teams."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate A2A configuration.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        team_dir = Path(team_spec.name)
        config_dir = team_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / "a2a_config.yaml"
        
        # Generate A2A config
        a2a_config = self._generate_a2a_config(team_spec)
        
        # Write config file
        with open(config_path, "w") as f:
            yaml.dump(a2a_config, f, default_flow_style=False, sort_keys=False)
        
        return {
            "generated_files": [str(config_path)],
            "errors": []
        }
    
    def _generate_a2a_config(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """Generate A2A configuration content."""
        # Find manager
        manager = next((m for m in team_spec.members if m.is_manager), None)
        
        config = {
            "a2a": {
                "enabled": True,
                "team_id": f"{team_spec.name}-team",
                "manager_agent": manager.role if manager else "Team Manager",
                "gateway_url": "http://agentgateway-service:3003",
                "capabilities": [
                    team_spec.purpose,
                    "Task execution",
                    "Status reporting",
                    "Team coordination",
                ],
                "protocols": {
                    "task_request": {
                        "enabled": True,
                        "timeout": 3600,
                        "retry_count": 3,
                    },
                    "status_check": {
                        "enabled": True,
                        "timeout": 300,
                    },
                    "capability_registration": {
                        "enabled": True,
                        "auto_register": True,
                    },
                },
                "routing": {
                    "internal": {
                        "enabled": True,
                        "log_conversations": True,
                    },
                    "external": {
                        "enabled": True,
                        "require_auth": True,
                    },
                },
            }
        }
        
        # Add subordinate teams if manager has them
        if manager and manager.manages_teams:
            config["a2a"]["subordinate_teams"] = manager.manages_teams
        
        return config