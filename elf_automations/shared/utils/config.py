"""
Configuration utilities for teams
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from supabase import create_client, Client


def load_team_config(config_path: Path) -> Dict[str, Any]:
    """
    Load team configuration from YAML file

    Args:
        config_path: Path to team_config.yaml

    Returns:
        Configuration dictionary
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_env_var(
    name: str, default: Optional[str] = None, required: bool = False
) -> Optional[str]:
    """
    Get environment variable with optional default

    Args:
        name: Environment variable name
        default: Default value if not set
        required: Raise error if not set and no default

    Returns:
        Environment variable value
    """
    value = os.getenv(name, default)

    if required and value is None:
        raise ValueError(f"Required environment variable {name} is not set")

    return value


def get_supabase_client() -> Client:
    """
    Get configured Supabase client
    
    Returns:
        Supabase client instance
    """
    url = get_env_var("SUPABASE_URL", required=True)
    key = get_env_var("SUPABASE_KEY", required=True)
    
    return create_client(url, key)
