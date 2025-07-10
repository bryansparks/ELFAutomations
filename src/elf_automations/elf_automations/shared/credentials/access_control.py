"""
Team-based access control with break-glass emergency access
"""

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..utils.logging import setup_logger

logger = setup_logger(__name__)


@dataclass
class BreakGlassToken:
    """Emergency access token"""

    token_hash: str
    created_at: datetime
    expires_at: datetime
    created_by: str
    reason: str
    used: bool = False
    used_at: Optional[datetime] = None
    used_by: Optional[str] = None


class TeamBasedAccessControl:
    """
    Manage credential access by team with pattern matching
    """

    def __init__(self, rules_path: Optional[Path] = None):
        self.rules_path = (
            rules_path or Path.home() / ".elf_automations" / "access_rules.json"
        )
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)

        self.access_rules = self._load_access_rules()

    def _load_access_rules(self) -> Dict[str, List[str]]:
        """Load team access rules from disk"""
        if not self.rules_path.exists():
            # Default rules
            return {
                "global": [
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "SUPABASE_URL",
                    "SUPABASE_ANON_KEY",
                ],
                "executive-team": ["*"],  # Full access
                "engineering-team": [
                    "GITHUB_*",
                    "DOCKER_*",
                    "K8S_*",
                    "SUPABASE_*",
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                ],
                "marketing-team": [
                    "MARKETING_*",
                    "SOCIAL_*",
                    "ANALYTICS_*",
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                ],
                "sales-team": [
                    "SALESFORCE_*",
                    "HUBSPOT_*",
                    "CRM_*",
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                ],
                "finance-team": ["STRIPE_*", "QUICKBOOKS_*", "BANKING_*"],
                "operations-team": ["SLACK_*", "JIRA_*", "CONFLUENCE_*"],
            }

        try:
            with open(self.rules_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load access rules: {e}")
            return {}

    def _save_access_rules(self) -> None:
        """Save access rules to disk"""
        with open(self.rules_path, "w") as f:
            json.dump(self.access_rules, f, indent=2)

    def can_access(self, team: str, credential_name: str) -> bool:
        """Check if team can access credential"""

        # Check team-specific rules
        if team in self.access_rules:
            for pattern in self.access_rules[team]:
                if self._matches_pattern(credential_name, pattern):
                    return True

        # Check global rules
        for pattern in self.access_rules.get("global", []):
            if self._matches_pattern(credential_name, pattern):
                return True

        # Check parent team access (e.g., marketing.social can access marketing's creds)
        if "." in team:
            parent_team = team.rsplit(".", 1)[0]
            return self.can_access(parent_team, credential_name)

        return False

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if credential name matches pattern"""
        if pattern == "*":
            return True

        if "*" in pattern:
            # Simple wildcard matching
            import fnmatch

            return fnmatch.fnmatch(name, pattern)

        return name == pattern

    def grant_access(self, team: str, credential_pattern: str) -> None:
        """Grant team access to credentials matching pattern"""
        if team not in self.access_rules:
            self.access_rules[team] = []

        if credential_pattern not in self.access_rules[team]:
            self.access_rules[team].append(credential_pattern)
            self._save_access_rules()
            logger.info(f"Granted {team} access to {credential_pattern}")

    def revoke_access(self, team: str, credential_pattern: str) -> None:
        """Revoke team access to credentials matching pattern"""
        if team in self.access_rules and credential_pattern in self.access_rules[team]:
            self.access_rules[team].remove(credential_pattern)
            self._save_access_rules()
            logger.info(f"Revoked {team} access to {credential_pattern}")

    def get_team_credentials(self, team: str) -> List[str]:
        """Get list of credential patterns a team can access"""
        patterns = []

        # Team-specific patterns
        patterns.extend(self.access_rules.get(team, []))

        # Global patterns
        patterns.extend(self.access_rules.get("global", []))

        # Parent team patterns
        if "." in team:
            parent_team = team.rsplit(".", 1)[0]
            patterns.extend(self.get_team_credentials(parent_team))

        return list(set(patterns))  # Remove duplicates

    def list_teams(self) -> List[str]:
        """List all teams with access rules"""
        return [t for t in self.access_rules.keys() if t != "global"]


class BreakGlassAccess:
    """
    Emergency access system with secure token generation and audit trail

    Design principles:
    1. Tokens are one-time use only
    2. Short expiration (default 1 hour)
    3. Requires multi-factor authentication (simulated)
    4. Full audit trail
    5. Automatic alerts on use
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = (
            storage_path or Path.home() / ".elf_automations" / "break_glass"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.tokens_file = self.storage_path / "tokens.json"
        self.tokens: Dict[str, BreakGlassToken] = self._load_tokens()

    def _load_tokens(self) -> Dict[str, BreakGlassToken]:
        """Load break glass tokens"""
        if not self.tokens_file.exists():
            return {}

        try:
            with open(self.tokens_file, "r") as f:
                data = json.load(f)

            tokens = {}
            for token_hash, token_data in data.items():
                tokens[token_hash] = BreakGlassToken(
                    token_hash=token_hash,
                    created_at=datetime.fromisoformat(token_data["created_at"]),
                    expires_at=datetime.fromisoformat(token_data["expires_at"]),
                    created_by=token_data["created_by"],
                    reason=token_data["reason"],
                    used=token_data["used"],
                    used_at=datetime.fromisoformat(token_data["used_at"])
                    if token_data.get("used_at")
                    else None,
                    used_by=token_data.get("used_by"),
                )
            return tokens
        except Exception as e:
            logger.error(f"Failed to load break glass tokens: {e}")
            return {}

    def _save_tokens(self) -> None:
        """Save break glass tokens"""
        data = {}
        for token_hash, token in self.tokens.items():
            data[token_hash] = {
                "created_at": token.created_at.isoformat(),
                "expires_at": token.expires_at.isoformat(),
                "created_by": token.created_by,
                "reason": token.reason,
                "used": token.used,
                "used_at": token.used_at.isoformat() if token.used_at else None,
                "used_by": token.used_by,
            }

        with open(self.tokens_file, "w") as f:
            json.dump(data, f, indent=2)

    def create_token(
        self,
        created_by: str,
        reason: str,
        duration_minutes: int = 60,
        require_mfa: bool = True,
    ) -> str:
        """
        Create a break glass token

        Returns the actual token (not the hash)
        """

        # In production, verify MFA here
        if require_mfa:
            logger.warning(
                "MFA verification simulated - implement actual MFA in production"
            )

        # Generate secure token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Create token record
        break_glass_token = BreakGlassToken(
            token_hash=token_hash,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=duration_minutes),
            created_by=created_by,
            reason=reason,
        )

        # Store token
        self.tokens[token_hash] = break_glass_token
        self._save_tokens()

        # Alert on creation
        self._send_alert(f"Break glass token created by {created_by} for: {reason}")

        logger.warning(f"Break glass token created by {created_by} for: {reason}")

        return token

    def validate_token(self, token: str, used_by: str) -> bool:
        """
        Validate and consume a break glass token

        Tokens are one-time use only
        """

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        if token_hash not in self.tokens:
            logger.error(f"Invalid break glass token attempted by {used_by}")
            self._send_alert(
                f"SECURITY: Invalid break glass token attempted by {used_by}"
            )
            return False

        break_glass_token = self.tokens[token_hash]

        # Check if already used
        if break_glass_token.used:
            logger.error(f"Reuse of break glass token attempted by {used_by}")
            self._send_alert(
                f"SECURITY: Break glass token reuse attempted by {used_by}"
            )
            return False

        # Check expiration
        if datetime.now() > break_glass_token.expires_at:
            logger.error(f"Expired break glass token used by {used_by}")
            self._send_alert(
                f"SECURITY: Expired break glass token attempted by {used_by}"
            )
            return False

        # Mark as used
        break_glass_token.used = True
        break_glass_token.used_at = datetime.now()
        break_glass_token.used_by = used_by
        self._save_tokens()

        # Alert on use
        self._send_alert(
            f"EMERGENCY ACCESS: Break glass token used by {used_by} "
            f"(created by {break_glass_token.created_by} for: {break_glass_token.reason})"
        )

        logger.warning(f"Break glass token used by {used_by}")

        return True

    def _send_alert(self, message: str) -> None:
        """Send security alert"""
        # In production, integrate with:
        # - Slack/Teams
        # - PagerDuty
        # - Email
        # - Security monitoring system

        alert_file = self.storage_path / "alerts.log"
        with open(alert_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")

        logger.critical(message)

    def cleanup_expired_tokens(self) -> int:
        """Remove expired unused tokens"""
        now = datetime.now()
        removed = 0

        tokens_to_remove = []
        for token_hash, token in self.tokens.items():
            if not token.used and token.expires_at < now:
                tokens_to_remove.append(token_hash)

        for token_hash in tokens_to_remove:
            del self.tokens[token_hash]
            removed += 1

        if removed > 0:
            self._save_tokens()
            logger.info(f"Cleaned up {removed} expired break glass tokens")

        return removed

    def get_audit_trail(self, days: int = 30) -> List[Dict]:
        """Get break glass usage audit trail"""
        cutoff = datetime.now() - timedelta(days=days)

        audit_trail = []
        for token in self.tokens.values():
            if token.created_at > cutoff:
                audit_trail.append(
                    {
                        "created_at": token.created_at.isoformat(),
                        "created_by": token.created_by,
                        "reason": token.reason,
                        "expires_at": token.expires_at.isoformat(),
                        "used": token.used,
                        "used_at": token.used_at.isoformat() if token.used_at else None,
                        "used_by": token.used_by,
                    }
                )

        return sorted(audit_trail, key=lambda x: x["created_at"], reverse=True)
