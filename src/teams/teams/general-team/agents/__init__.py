"""
general-team Agents

This module contains all agent implementations for the general-team.
"""

from .coordinator import coordinator
from .specialist_1 import specialist_1
from .specialist_2 import specialist_2
from .team_lead import team_lead

__all__ = ["team_lead", "specialist_1", "specialist_2", "coordinator"]
