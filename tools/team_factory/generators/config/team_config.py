"""
Team configuration generator.
"""

from pathlib import Path
from typing import Any, Dict

import yaml

from ...models import TeamSpecification
from ..base import BaseGenerator


class TeamConfigGenerator(BaseGenerator):
    """Generates team configuration files."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate team configuration.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        team_dir = Path(team_spec.name)
        config_dir = team_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / "team_config.yaml"
        
        # Generate team config
        team_config = self._generate_team_config(team_spec)
        
        # Write config file
        with open(config_path, "w") as f:
            yaml.dump(team_config, f, default_flow_style=False, sort_keys=False)
        
        return {
            "generated_files": [str(config_path)],
            "errors": []
        }
    
    def _generate_team_config(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """Generate team configuration content."""
        # Find manager
        manager = next((m for m in team_spec.members if m.is_manager), None)
        
        config = {
            "team": {
                "name": team_spec.name,
                "purpose": team_spec.purpose,
                "department": team_spec.department,
                "framework": team_spec.framework,
                "reporting_to": team_spec.reporting_to,
                "members": [
                    {
                        "name": member.name,
                        "role": member.role,
                        "responsibilities": member.responsibilities,
                        "skills": member.skills,
                        "personality": member.personality,
                        "is_manager": member.is_manager,
                        "manages_teams": member.manages_teams,
                    }
                    for member in team_spec.members
                ],
                "communication": {
                    "internal": {
                        "style": "natural_language",
                        "logging": {
                            "enabled": True,
                            "format": "conversation",
                            "path": f"logs/{team_spec.name}_communications.log",
                        },
                    },
                    "external": {
                        "protocol": "a2a",
                        "manager_only": True,
                        "logging": {
                            "enabled": True,
                            "format": "structured",
                            "path": f"logs/{team_spec.name}_a2a.log",
                        },
                    },
                },
                "workflow": {
                    "type": "hierarchical" if len(team_spec.members) >= 5 else "sequential",
                    "manager": manager.role if manager else None,
                    "delegation_enabled": bool(manager and manager.manages_teams),
                },
                "memory": {
                    "enabled": True,
                    "provider": "qdrant",
                    "continuous_learning": True,
                    "experience_replay": True,
                },
                "monitoring": {
                    "metrics": {
                        "enabled": True,
                        "prometheus_port": 9090,
                    },
                    "health_check": {
                        "enabled": True,
                        "endpoint": "/health",
                        "interval": 30,
                    },
                    "logging": {
                        "level": "INFO",
                        "format": "json",
                        "separate_files": True,
                    },
                },
            }
        }
        
        # Add sub-team recommendations if any
        if team_spec.sub_team_recommendations:
            config["team"]["recommended_sub_teams"] = [
                {
                    "name": sub.name,
                    "purpose": sub.purpose,
                    "reason": sub.reason,
                    "size": sub.size,
                }
                for sub in team_spec.sub_team_recommendations
            ]
        
        return config