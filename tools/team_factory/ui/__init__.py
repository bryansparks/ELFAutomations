"""
User interface components for team factory.
"""

from .console import console, create_panel, create_table
from .prompts import (
    confirm,
    display_team_summary,
    prompt_choice,
    prompt_team_details,
    prompt_text,
)

__all__ = [
    "console",
    "create_panel",
    "create_table",
    "prompt_text",
    "prompt_choice",
    "confirm",
    "prompt_team_details",
    "display_team_summary",
]
