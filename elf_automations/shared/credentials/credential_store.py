"""
Secure credential storage with encryption at rest
"""

import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class CredentialStore:
    """Base credential storage interface"""

    def store(self, key: str, value: str, metadata: Optional[Dict] = None) -> None:
        """Store a credential"""
        raise NotImplementedError

    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve a credential"""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """Delete a credential"""
        raise NotImplementedError

    def list_keys(self, pattern: Optional[str] = None) -> list:
        """List credential keys"""
        raise NotImplementedError


class SecureCredentialStore(CredentialStore):
    """
    Encrypted credential storage using Fernet encryption
    Suitable for local k3s deployments
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = (
            storage_path or Path.home() / ".elf_automations" / "credentials"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        self.cipher = self._init_cipher()

        # Credential storage file
        self.creds_file = self.storage_path / "credentials.enc"
        self.metadata_file = self.storage_path / "metadata.json"

        # Load existing credentials
        self._credentials = self._load_credentials()
        self._metadata = self._load_metadata()

    def _init_cipher(self) -> Fernet:
        """Initialize encryption cipher"""
        key_file = self.storage_path / ".key"

        if key_file.exists():
            # Load existing key
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            # Generate new key from master password
            master_password = os.getenv("ELF_MASTER_PASSWORD", "changeme")
            salt = b"elf-automations-salt"  # In production, use random salt

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))

            # Save key (in production, use KMS or hardware security module)
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Read/write for owner only

        return Fernet(key)

    def _load_credentials(self) -> Dict[str, bytes]:
        """Load encrypted credentials from disk"""
        if not self.creds_file.exists():
            return {}

        try:
            with open(self.creds_file, "rb") as f:
                encrypted_data = f.read()

            if not encrypted_data:
                return {}

            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}

    def _load_metadata(self) -> Dict[str, Dict]:
        """Load credential metadata"""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}

    def _save_credentials(self) -> None:
        """Save encrypted credentials to disk"""
        data = json.dumps(self._credentials).encode()
        encrypted_data = self.cipher.encrypt(data)

        with open(self.creds_file, "wb") as f:
            f.write(encrypted_data)
        os.chmod(self.creds_file, 0o600)

    def _save_metadata(self) -> None:
        """Save credential metadata"""
        with open(self.metadata_file, "w") as f:
            json.dump(self._metadata, f, indent=2)
        os.chmod(self.metadata_file, 0o600)

    def store(self, key: str, value: str, metadata: Optional[Dict] = None) -> None:
        """Store an encrypted credential"""
        # Encrypt the value
        encrypted_value = self.cipher.encrypt(value.encode())
        self._credentials[key] = base64.b64encode(encrypted_value).decode()

        # Store metadata
        self._metadata[key] = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            **(metadata or {}),
        }

        # Save to disk
        self._save_credentials()
        self._save_metadata()

        logger.info(f"Stored credential: {key}")

    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve and decrypt a credential"""
        if key not in self._credentials:
            return None

        try:
            encrypted_value = base64.b64decode(self._credentials[key])
            decrypted_value = self.cipher.decrypt(encrypted_value)
            return decrypted_value.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt credential {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a credential"""
        if key in self._credentials:
            del self._credentials[key]
            del self._metadata[key]

            self._save_credentials()
            self._save_metadata()

            logger.info(f"Deleted credential: {key}")
            return True

        return False

    def list_keys(self, pattern: Optional[str] = None) -> list:
        """List credential keys, optionally filtered by pattern"""
        keys = list(self._credentials.keys())

        if pattern:
            import fnmatch

            keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]

        return keys

    def get_metadata(self, key: str) -> Optional[Dict]:
        """Get metadata for a credential"""
        return self._metadata.get(key)

    def rotate_encryption_key(self, new_master_password: str) -> None:
        """Rotate the encryption key"""
        # Decrypt all credentials with old key
        credentials = {}
        for key in self._credentials:
            value = self.retrieve(key)
            if value:
                credentials[key] = value

        # Generate new cipher with new password
        os.environ["ELF_MASTER_PASSWORD"] = new_master_password
        key_file = self.storage_path / ".key"
        key_file.unlink(missing_ok=True)
        self.cipher = self._init_cipher()

        # Re-encrypt all credentials
        self._credentials = {}
        for key, value in credentials.items():
            self.store(key, value, self._metadata.get(key, {}))

        logger.info("Successfully rotated encryption key")
