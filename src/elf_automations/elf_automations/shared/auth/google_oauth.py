"""
Google OAuth credential management for Drive API access.

This module provides secure storage and management of Google OAuth tokens
for the multi-tenant RAG system.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from ..config import get_supabase_client
from ..credentials.credential_manager import CredentialManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GoogleOAuthManager:
    """Manages Google OAuth credentials for Drive access."""

    # OAuth scopes required for RAG system
    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        "https://www.googleapis.com/auth/drive.file",  # For creating files if needed
    ]

    def __init__(self, credential_manager: Optional[CredentialManager] = None):
        """Initialize OAuth manager with secure credential storage."""
        self.cred_manager = credential_manager or CredentialManager()
        self.supabase = get_supabase_client()

        # OAuth configuration
        self.client_config = self._load_client_config()
        self.redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:8080/oauth2callback"
        )

    def _load_client_config(self) -> Dict[str, Any]:
        """Load Google OAuth client configuration."""
        # Try to load from credential manager first
        try:
            client_id = self.cred_manager.get_credential("google_oauth", "client_id")
            client_secret = self.cred_manager.get_credential(
                "google_oauth", "client_secret"
            )

            if client_id and client_secret:
                return {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": [self.redirect_uri],
                    }
                }
        except Exception as e:
            logger.warning(f"Could not load OAuth config from credential manager: {e}")

        # Fall back to environment variables
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError(
                "Google OAuth credentials not found. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET or use credential manager."
            )

        return {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [self.redirect_uri],
            }
        }

    def get_authorization_url(self, tenant_id: str, state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL for a tenant."""
        flow = Flow.from_client_config(
            self.client_config, scopes=self.SCOPES, redirect_uri=self.redirect_uri
        )

        # Include tenant_id in state for multi-tenant support
        if not state:
            state = json.dumps({"tenant_id": tenant_id, "timestamp": time.time()})

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )

        logger.info(f"Generated auth URL for tenant {tenant_id}")
        return auth_url

    def exchange_code_for_tokens(
        self, code: str, tenant_id: str, state: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri,
            state=state,
        )

        # Exchange code for tokens
        flow.fetch_token(code=code)

        # Get credentials
        credentials = flow.credentials

        # Store tokens securely
        token_data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }

        # Store in credential manager
        self._store_tenant_tokens(tenant_id, token_data)

        # Also store in Supabase for tracking
        self._record_oauth_event(tenant_id, "token_exchanged")

        logger.info(f"Successfully exchanged code for tokens for tenant {tenant_id}")
        return token_data

    def get_credentials(self, tenant_id: str) -> Optional[Credentials]:
        """Get valid OAuth credentials for a tenant, refreshing if needed."""
        # Load stored tokens
        token_data = self._load_tenant_tokens(tenant_id)

        if not token_data:
            logger.warning(f"No stored tokens found for tenant {tenant_id}")
            return None

        # Create credentials object
        credentials = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get(
                "token_uri", "https://oauth2.googleapis.com/token"
            ),
            client_id=self.client_config["installed"]["client_id"],
            client_secret=self.client_config["installed"]["client_secret"],
            scopes=token_data.get("scopes", self.SCOPES),
        )

        # Set expiry if available
        if token_data.get("expiry"):
            credentials.expiry = datetime.fromisoformat(token_data["expiry"])

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            logger.info(f"Refreshing expired token for tenant {tenant_id}")
            credentials.refresh(Request())

            # Store updated tokens
            updated_data = {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expiry": credentials.expiry.isoformat()
                if credentials.expiry
                else None,
            }
            token_data.update(updated_data)
            self._store_tenant_tokens(tenant_id, token_data)
            self._record_oauth_event(tenant_id, "token_refreshed")

        return credentials

    def revoke_credentials(self, tenant_id: str) -> bool:
        """Revoke OAuth credentials for a tenant."""
        credentials = self.get_credentials(tenant_id)

        if not credentials:
            logger.warning(f"No credentials to revoke for tenant {tenant_id}")
            return False

        try:
            # Revoke the token
            import requests

            response = requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": credentials.token},
                headers={"content-type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                # Remove stored tokens
                self._delete_tenant_tokens(tenant_id)
                self._record_oauth_event(tenant_id, "token_revoked")
                logger.info(f"Successfully revoked credentials for tenant {tenant_id}")
                return True
            else:
                logger.error(f"Failed to revoke token: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error revoking credentials: {e}")
            return False

    def test_credentials(self, tenant_id: str) -> bool:
        """Test if credentials are valid by making a simple API call."""
        credentials = self.get_credentials(tenant_id)

        if not credentials:
            return False

        try:
            # Build Drive service
            service = build("drive", "v3", credentials=credentials)

            # Try to list files (limited to 1)
            result = (
                service.files().list(pageSize=1, fields="files(id, name)").execute()
            )

            logger.info(f"Credentials valid for tenant {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"Credentials test failed for tenant {tenant_id}: {e}")
            return False

    def _store_tenant_tokens(self, tenant_id: str, token_data: Dict[str, Any]):
        """Store OAuth tokens securely for a tenant."""
        # Store in credential manager
        self.cred_manager.store_credential(
            service=f"google_oauth_{tenant_id}",
            account="tokens",
            credential=json.dumps(token_data),
        )

    def _load_tenant_tokens(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Load OAuth tokens for a tenant."""
        try:
            token_json = self.cred_manager.get_credential(
                service=f"google_oauth_{tenant_id}", account="tokens"
            )
            if token_json:
                return json.loads(token_json)
        except Exception as e:
            logger.error(f"Failed to load tokens for tenant {tenant_id}: {e}")

        return None

    def _delete_tenant_tokens(self, tenant_id: str):
        """Delete stored OAuth tokens for a tenant."""
        try:
            self.cred_manager.delete_credential(
                service=f"google_oauth_{tenant_id}", account="tokens"
            )
        except Exception as e:
            logger.error(f"Failed to delete tokens for tenant {tenant_id}: {e}")

    def _record_oauth_event(self, tenant_id: str, event_type: str):
        """Record OAuth events in Supabase for auditing."""
        try:
            self.supabase.table("rag.oauth_events").insert(
                {
                    "tenant_id": tenant_id,
                    "event_type": event_type,
                    "timestamp": datetime.now().isoformat(),
                }
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to record OAuth event: {e}")

    def list_authorized_tenants(self) -> list[str]:
        """List all tenants with stored OAuth credentials."""
        # This would query the credential store for all google_oauth_* entries
        # For now, return empty list
        return []


# Convenience functions
def setup_google_oauth(tenant_id: str) -> tuple[bool, str]:
    """
    Set up Google OAuth for a tenant.

    Returns:
        Tuple of (success, auth_url_or_message)
    """
    try:
        manager = GoogleOAuthManager()
        auth_url = manager.get_authorization_url(tenant_id)
        return True, auth_url
    except Exception as e:
        return False, str(e)


def test_google_credentials(tenant_id: str) -> bool:
    """Test if Google credentials are valid for a tenant."""
    try:
        manager = GoogleOAuthManager()
        return manager.test_credentials(tenant_id)
    except Exception:
        return False
