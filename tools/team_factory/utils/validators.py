"""
Validation functions for team factory.
"""

from typing import List, Optional, Tuple

from .constants import MAX_TEAM_SIZE, MIN_TEAM_SIZE
from .sanitizers import sanitize_name


def validate_team_size(size: int) -> Tuple[bool, str]:
    """
    Validate team size is within acceptable range.

    Args:
        size: Number of team members

    Returns:
        Tuple of (is_valid, message)
    """
    if size < MIN_TEAM_SIZE:
        return False, f"Team size {size} is below minimum of {MIN_TEAM_SIZE}"
    elif size > MAX_TEAM_SIZE:
        return False, f"Team size {size} exceeds maximum of {MAX_TEAM_SIZE}"
    else:
        return True, f"Team size {size} is optimal"


def validate_framework(framework: str) -> Tuple[bool, str]:
    """
    Validate framework choice.

    Args:
        framework: Framework name

    Returns:
        Tuple of (is_valid, message)
    """
    valid_frameworks = ["CrewAI", "LangGraph"]

    if framework not in valid_frameworks:
        return (
            False,
            f"Invalid framework '{framework}'. Must be one of: {', '.join(valid_frameworks)}",
        )

    return True, f"Framework '{framework}' is valid"


def validate_llm_provider(provider: str) -> Tuple[bool, str]:
    """
    Validate LLM provider choice.

    Args:
        provider: Provider name

    Returns:
        Tuple of (is_valid, message)
    """
    valid_providers = ["OpenAI", "Anthropic"]

    if provider not in valid_providers:
        return (
            False,
            f"Invalid provider '{provider}'. Must be one of: {', '.join(valid_providers)}",
        )

    return True, f"Provider '{provider}' is valid"


def validate_member_names(members: List[str]) -> Tuple[bool, str]:
    """
    Validate team member names are unique.

    Args:
        members: List of member names

    Returns:
        Tuple of (is_valid, message)
    """
    if len(members) != len(set(members)):
        duplicates = [name for name in members if members.count(name) > 1]
        return False, f"Duplicate member names found: {', '.join(set(duplicates))}"

    return True, "All member names are unique"
