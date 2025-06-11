"""
Central credential management service
"""

import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ..utils.logging import setup_logger
from .access_control import TeamBasedAccessControl
from .audit_logger import AuditLogger
from .credential_store import SecureCredentialStore

logger = setup_logger(__name__)


class CredentialType(Enum):
    """Types of credentials supported"""

    API_KEY = "api_key"
    DATABASE = "database"
    SERVICE_ACCOUNT = "service_account"
    WEBHOOK = "webhook"
    JWT_SECRET = "jwt_secret"
    CERTIFICATE = "certificate"


@dataclass
class Credential:
    """Credential data model"""

    name: str
    type: CredentialType
    team: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_rotated: Optional[datetime]
    last_accessed: Optional[datetime]
    metadata: Dict[str, Any]

    @property
    def is_expired(self) -> bool:
        """Check if credential is expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    @property
    def needs_rotation(self) -> bool:
        """Check if credential needs rotation based on type"""
        if not self.last_rotated:
            return True

        rotation_periods = {
            CredentialType.API_KEY: timedelta(days=30),
            CredentialType.DATABASE: timedelta(days=7),
            CredentialType.SERVICE_ACCOUNT: timedelta(days=90),
            CredentialType.WEBHOOK: timedelta(days=60),
            CredentialType.JWT_SECRET: timedelta(days=14),
            CredentialType.CERTIFICATE: timedelta(days=365),
        }

        period = rotation_periods.get(self.type, timedelta(days=30))
        return datetime.now() > self.last_rotated + period


class CredentialError(Exception):
    """Base credential error"""

    pass


class AccessDeniedError(CredentialError):
    """Access denied to credential"""

    pass


class CredentialExpiredError(CredentialError):
    """Credential has expired"""

    pass


class CredentialNotFoundError(CredentialError):
    """Credential not found"""

    pass


class CredentialManager:
    """
    Central credential management service
    Handles creation, retrieval, rotation, and access control
    """

    def __init__(
        self,
        store: Optional[SecureCredentialStore] = None,
        access_control: Optional[TeamBasedAccessControl] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        self.store = store or SecureCredentialStore()
        self.access_control = access_control or TeamBasedAccessControl()
        self.audit = audit_logger or AuditLogger()

    def create_credential(
        self,
        name: str,
        value: str,
        type: CredentialType,
        team: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> Credential:
        """Create a new credential"""

        # Build credential object
        credential = Credential(
            name=name,
            type=type,
            team=team,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=expires_in_days)
            if expires_in_days
            else None,
            last_rotated=None,
            last_accessed=None,
            metadata=metadata or {},
        )

        # Store the value
        key = self._make_key(name, team)
        self.store.store(
            key,
            value,
            {
                "type": type.value,
                "team": team,
                "created_at": credential.created_at.isoformat(),
                "expires_at": credential.expires_at.isoformat()
                if credential.expires_at
                else None,
                "metadata": credential.metadata,
            },
        )

        # Grant team access if specified
        if team:
            self.access_control.grant_access(team, name)

        # Audit
        self.audit.log_creation(name, team, type.value)

        logger.info(f"Created credential: {name} for team: {team or 'global'}")
        return credential

    def get_credential(self, name: str, team: str, purpose: str = "general") -> str:
        """Get credential value with access control"""

        # Check access
        if not self.access_control.can_access(team, name):
            self.audit.log_denied_access(team, name, purpose)
            raise AccessDeniedError(f"Team {team} cannot access {name}")

        # Try team-specific first, then global
        key = self._make_key(name, team)
        value = self.store.retrieve(key)

        if not value:
            key = self._make_key(name, None)
            value = self.store.retrieve(key)

        if not value:
            raise CredentialNotFoundError(f"Credential {name} not found")

        # Check expiration
        metadata = self.store.get_metadata(key)
        if metadata and metadata.get("expires_at"):
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            if expires_at < datetime.now():
                self.audit.log_expired_access(team, name)
                raise CredentialExpiredError(f"Credential {name} has expired")

        # Update last accessed
        metadata["last_accessed"] = datetime.now().isoformat()
        self.store.store(key, value, metadata)

        # Audit successful access
        self.audit.log_access(team, name, purpose)

        return value

    def list_credentials(self, team: Optional[str] = None) -> List[Credential]:
        """List credentials, optionally filtered by team"""
        credentials = []

        pattern = f"{team}:*" if team else "global:*"
        keys = self.store.list_keys(pattern)

        for key in keys:
            metadata = self.store.get_metadata(key)
            if not metadata:
                continue

            name = key.split(":", 1)[1]

            credentials.append(
                Credential(
                    name=name,
                    type=CredentialType(metadata.get("type", "api_key")),
                    team=metadata.get("team"),
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                    expires_at=datetime.fromisoformat(metadata["expires_at"])
                    if metadata.get("expires_at")
                    else None,
                    last_rotated=datetime.fromisoformat(metadata["last_rotated"])
                    if metadata.get("last_rotated")
                    else None,
                    last_accessed=datetime.fromisoformat(metadata["last_accessed"])
                    if metadata.get("last_accessed")
                    else None,
                    metadata=metadata.get("metadata", {}),
                )
            )

        return credentials

    def update_credential(
        self,
        name: str,
        value: str,
        team: Optional[str] = None,
        requester_team: Optional[str] = None,
    ) -> None:
        """Update an existing credential"""

        # Check access if requester specified
        if requester_team and not self.access_control.can_access(requester_team, name):
            self.audit.log_denied_access(requester_team, name, "update")
            raise AccessDeniedError(f"Team {requester_team} cannot update {name}")

        key = self._make_key(name, team)
        metadata = self.store.get_metadata(key)

        if not metadata:
            raise CredentialNotFoundError(f"Credential {name} not found")

        # Update metadata
        metadata["last_updated"] = datetime.now().isoformat()

        # Store updated value
        self.store.store(key, value, metadata)

        # Audit
        self.audit.log_update(name, team, requester_team)

        logger.info(f"Updated credential: {name}")

    def delete_credential(
        self,
        name: str,
        team: Optional[str] = None,
        requester_team: Optional[str] = None,
    ) -> bool:
        """Delete a credential"""

        # Check access if requester specified
        if requester_team and not self.access_control.can_access(requester_team, name):
            self.audit.log_denied_access(requester_team, name, "delete")
            raise AccessDeniedError(f"Team {requester_team} cannot delete {name}")

        key = self._make_key(name, team)
        success = self.store.delete(key)

        if success:
            # Revoke access
            if team:
                self.access_control.revoke_access(team, name)

            # Audit
            self.audit.log_deletion(name, team, requester_team)

            logger.info(f"Deleted credential: {name}")

        return success

    def rotate_credential(
        self, name: str, team: Optional[str] = None, new_value: Optional[str] = None
    ) -> str:
        """Rotate a credential"""

        key = self._make_key(name, team)
        metadata = self.store.get_metadata(key)

        if not metadata:
            raise CredentialNotFoundError(f"Credential {name} not found")

        # Generate new value if not provided
        if not new_value:
            cred_type = CredentialType(metadata.get("type", "api_key"))
            new_value = self._generate_credential_value(cred_type)

        # Update metadata
        metadata["last_rotated"] = datetime.now().isoformat()
        metadata["rotation_count"] = metadata.get("rotation_count", 0) + 1

        # Store new value
        self.store.store(key, new_value, metadata)

        # Audit
        self.audit.log_rotation(name, team)

        logger.info(f"Rotated credential: {name}")
        return new_value

    def _make_key(self, name: str, team: Optional[str]) -> str:
        """Create storage key from name and team"""
        return f"{team}:{name}" if team else f"global:{name}"

    def _generate_credential_value(self, type: CredentialType) -> str:
        """Generate a new credential value based on type"""
        if type == CredentialType.API_KEY:
            # Generate API key format
            prefix = "sk-elf-"
            chars = string.ascii_letters + string.digits
            suffix = "".join(secrets.choice(chars) for _ in range(32))
            return f"{prefix}{suffix}"

        elif type == CredentialType.JWT_SECRET:
            # Generate strong JWT secret
            return secrets.token_urlsafe(64)

        elif type == CredentialType.DATABASE:
            # Generate database password
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            return "".join(secrets.choice(chars) for _ in range(24))

        else:
            # Default strong random
            return secrets.token_urlsafe(32)
