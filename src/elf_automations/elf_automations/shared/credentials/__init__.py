"""
Credential Management System for ElfAutomations

A lightweight, k3s-native credential management solution that provides:
- Encrypted storage using Fernet
- Team-based access control
- Audit logging
- Automatic rotation
- Emergency break-glass access
"""

from .access_control import BreakGlassAccess, TeamBasedAccessControl
from .audit_logger import AuditLogger
from .credential_manager import Credential, CredentialManager, CredentialType
from .credential_store import CredentialStore, SecureCredentialStore
from .k3s_integration import K3sSecretManager
from .rotation_manager import RotationManager

__all__ = [
    "CredentialStore",
    "SecureCredentialStore",
    "CredentialManager",
    "Credential",
    "CredentialType",
    "TeamBasedAccessControl",
    "BreakGlassAccess",
    "AuditLogger",
    "RotationManager",
    "K3sSecretManager",
]
