"""
Utility functions for team factory.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple


def sanitize_name(name: str, max_length: int = 50) -> str:
    """
    Sanitize a name for use as file/directory name.

    Args:
        name: The name to sanitize
        max_length: Maximum length for the name

    Returns:
        Sanitized name safe for filesystem use
    """
    # Remove special characters
    sanitized = re.sub(r"[^a-zA-Z0-9\s-]", "", name)

    # Replace spaces with hyphens
    sanitized = sanitized.strip().replace(" ", "-")

    # Remove multiple consecutive hyphens
    sanitized = re.sub(r"-+", "-", sanitized)

    # Convert to lowercase
    sanitized = sanitized.lower()

    # Truncate if too long
    if len(sanitized) > max_length:
        # Try to cut at word boundary
        truncated = sanitized[:max_length]
        last_hyphen = truncated.rfind("-")
        if last_hyphen > max_length - 10:  # Keep at least 10 chars
            sanitized = truncated[:last_hyphen]
        else:
            sanitized = truncated

    # Ensure it doesn't start or end with hyphen
    sanitized = sanitized.strip("-")

    # If empty after sanitization, use default
    if not sanitized:
        sanitized = "unnamed-team"

    return sanitized


def validate_team_name(
    name: str, existing_teams: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Validate a team name.

    Args:
        name: Team name to validate
        existing_teams: List of existing team names to check against

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Team name cannot be empty"

    if len(name) < 3:
        return False, "Team name must be at least 3 characters"

    if existing_teams and name in existing_teams:
        return False, f"Team '{name}' already exists"

    # Check if name would result in empty sanitized version
    sanitized = sanitize_name(name)
    if not sanitized or sanitized == "unnamed-team":
        return False, "Team name contains only special characters"

    return True, ""


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Returns:
        The path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_safe_filename(name: str, extension: str = ".py") -> str:
    """
    Convert a name to a safe filename.

    Args:
        name: Name to convert
        extension: File extension to add

    Returns:
        Safe filename
    """
    # Convert to lowercase and replace spaces with underscores
    safe_name = name.lower().replace(" ", "_").replace("-", "_")

    # Remove any remaining special characters
    safe_name = re.sub(r"[^a-z0-9_]", "", safe_name)

    # Ensure it's a valid Python identifier if .py extension
    if extension == ".py" and safe_name and safe_name[0].isdigit():
        safe_name = "m_" + safe_name

    return safe_name + extension
