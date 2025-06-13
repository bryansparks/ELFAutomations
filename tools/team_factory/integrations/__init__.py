"""
External system integrations for team factory.
"""

from .executive_patch import ExecutivePatchGenerator
from .memory import MemorySystemIntegration
from .registry import RegistryIntegration

__all__ = ["ExecutivePatchGenerator", "MemorySystemIntegration", "RegistryIntegration"]