"""
LLM configuration generator.
"""

from pathlib import Path
from typing import Any, Dict

import yaml

from ...models import TeamSpecification
from ..base import BaseGenerator


class LLMConfigGenerator(BaseGenerator):
    """Generates LLM configuration for teams."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate LLM configuration.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        team_dir = Path(team_spec.name)
        config_dir = team_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / "llm_config.yaml"
        
        # Generate LLM config
        llm_config = self._generate_llm_config(team_spec)
        
        # Write config file
        with open(config_path, "w") as f:
            yaml.dump(llm_config, f, default_flow_style=False, sort_keys=False)
        
        return {
            "generated_files": [str(config_path)],
            "errors": []
        }
    
    def _generate_llm_config(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """Generate LLM configuration content."""
        config = {
            "llm": {
                "provider": team_spec.llm_provider,
                "model": team_spec.llm_model,
                "temperature": 0.7,
                "max_tokens": 4096,
                "fallback": {
                    "enabled": True,
                    "chain": self._get_fallback_chain(team_spec.llm_provider),
                },
                "quota": {
                    "enabled": True,
                    "daily_limit": 10.0,  # $10 daily limit
                    "track_by_team": True,
                },
                "retry": {
                    "enabled": True,
                    "max_attempts": 3,
                    "backoff_factor": 2,
                },
            }
        }
        
        # Add provider-specific settings
        if team_spec.llm_provider == "OpenAI":
            config["llm"]["openai"] = {
                "api_key_env": "OPENAI_API_KEY",
                "organization_env": "OPENAI_ORG_ID",
                "base_url": None,
            }
        elif team_spec.llm_provider == "Anthropic":
            config["llm"]["anthropic"] = {
                "api_key_env": "ANTHROPIC_API_KEY",
                "base_url": None,
            }
        
        return config
    
    def _get_fallback_chain(self, primary_provider: str) -> list:
        """Get fallback chain based on primary provider."""
        if primary_provider == "OpenAI":
            return [
                {"provider": "OpenAI", "model": "gpt-4"},
                {"provider": "OpenAI", "model": "gpt-3.5-turbo"},
                {"provider": "Anthropic", "model": "claude-3-opus-20240229"},
                {"provider": "Anthropic", "model": "claude-3-sonnet-20240229"},
                {"provider": "Anthropic", "model": "claude-3-haiku-20240307"},
            ]
        else:  # Anthropic
            return [
                {"provider": "Anthropic", "model": "claude-3-opus-20240229"},
                {"provider": "Anthropic", "model": "claude-3-sonnet-20240229"},
                {"provider": "Anthropic", "model": "claude-3-haiku-20240307"},
                {"provider": "OpenAI", "model": "gpt-4"},
                {"provider": "OpenAI", "model": "gpt-3.5-turbo"},
            ]