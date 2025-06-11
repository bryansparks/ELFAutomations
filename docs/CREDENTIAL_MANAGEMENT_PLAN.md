# Credential Management Plan (Task 9)

## Overview

This plan outlines the implementation of a comprehensive credential management system for ElfAutomations, addressing current security gaps and providing a foundation for secure, automated credential handling.

## Current State Analysis

### Critical Issues
1. **Hardcoded Credentials**: Supabase tokens exposed in `/config/mcp_config.json`
2. **No Isolation**: All teams share the same API keys
3. **No Rotation**: Static credentials with no expiration
4. **Plain Text Storage**: Credentials stored unencrypted in config files
5. **No Audit Trail**: No record of credential access

### Current Credential Types
- **API Keys**: OpenAI, Anthropic, Supabase (URL, anon key, service key)
- **Database**: Supabase connection strings
- **Infrastructure**: Docker registry, K8s contexts
- **External Services**: GitHub tokens, Slack webhooks

## Architecture Design

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Integration Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Team      │  │  Deployment  │  │      MCP         │  │
│  │  Factory    │  │   Pipeline   │  │    Servers       │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Access Control Layer                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Team     │  │     Role     │  │     Audit        │  │
│  │   Based     │  │    Based     │  │    Logger        │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Credential Store Layer                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Encrypted  │  │   Version    │  │   Rotation       │  │
│  │   Storage   │  │   Control    │  │   Manager        │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Secure Current System (Week 1)

#### 1.1 Remove Hardcoded Credentials
```python
# Task: Scan and remove all hardcoded credentials
# Files to fix:
# - /config/mcp_config.json
# - Any YAML configs with embedded secrets

# Replace with references:
{
    "token": "${SUPABASE_SERVICE_KEY}"  # Environment variable reference
}
```

#### 1.2 Implement Encrypted Storage
```python
from elf_automations.shared.infrastructure import ConfigManager

class SecureCredentialStore:
    """Encrypted credential storage using existing ConfigManager"""

    def __init__(self):
        self.config = ConfigManager()
        self.credentials_path = Path.home() / ".elf_automations" / "credentials"

    def store_credential(self, name: str, value: str, team: Optional[str] = None):
        """Store encrypted credential"""
        key = f"{team}:{name}" if team else f"global:{name}"
        self.config.set_secret(key, value, encrypt=True)

    def get_credential(self, name: str, team: Optional[str] = None) -> Optional[str]:
        """Retrieve decrypted credential"""
        key = f"{team}:{name}" if team else f"global:{name}"
        return self.config.get_secret(key)
```

#### 1.3 Add Startup Validation
```python
def validate_credentials_on_startup():
    """Validate all required credentials exist"""
    required = {
        "OPENAI_API_KEY": "OpenAI API access",
        "ANTHROPIC_API_KEY": "Anthropic API access",
        "SUPABASE_URL": "Database connection",
        "SUPABASE_KEY": "Database authentication"
    }

    missing = []
    for key, purpose in required.items():
        if not os.getenv(key) and not credential_store.get_credential(key):
            missing.append(f"{key} ({purpose})")

    if missing:
        raise CredentialError(f"Missing credentials: {', '.join(missing)}")
```

### Phase 2: Credential Manager Service (Week 2)

#### 2.1 Core Credential Manager
```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, List
import json
from datetime import datetime, timedelta

class CredentialType(Enum):
    API_KEY = "api_key"
    DATABASE = "database"
    SERVICE_ACCOUNT = "service_account"
    WEBHOOK = "webhook"

@dataclass
class Credential:
    name: str
    type: CredentialType
    value: str
    team: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_rotated: Optional[datetime]
    metadata: Dict[str, Any]

class CredentialManager:
    """Central credential management service"""

    def __init__(self, store: SecureCredentialStore, audit_logger: AuditLogger):
        self.store = store
        self.audit = audit_logger
        self.access_control = TeamBasedAccessControl()

    def create_credential(self,
                         name: str,
                         type: CredentialType,
                         value: str,
                         team: Optional[str] = None,
                         expires_in_days: Optional[int] = None) -> Credential:
        """Create a new credential"""

        credential = Credential(
            name=name,
            type=type,
            value=value,
            team=team,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None,
            last_rotated=None,
            metadata={}
        )

        # Store encrypted
        self.store.store_credential(name, value, team)

        # Store metadata
        self._store_metadata(credential)

        # Audit
        self.audit.log_creation(name, team, type)

        return credential

    def get_credential(self,
                      name: str,
                      team: str,
                      purpose: str = "general") -> Optional[str]:
        """Get credential with access control"""

        # Check access
        if not self.access_control.can_access(team, name):
            self.audit.log_denied_access(team, name, purpose)
            raise AccessDeniedError(f"Team {team} cannot access {name}")

        # Check if exists
        value = self.store.get_credential(name, team) or self.store.get_credential(name)

        if not value:
            return None

        # Check expiration
        metadata = self._get_metadata(name, team)
        if metadata and metadata.get('expires_at'):
            if datetime.fromisoformat(metadata['expires_at']) < datetime.now():
                self.audit.log_expired_access(team, name)
                raise CredentialExpiredError(f"Credential {name} has expired")

        # Audit successful access
        self.audit.log_access(team, name, purpose)

        return value
```

#### 2.2 Team-Based Access Control
```python
class TeamBasedAccessControl:
    """Manage credential access by team"""

    def __init__(self):
        self.access_rules = self._load_access_rules()

    def _load_access_rules(self) -> Dict[str, List[str]]:
        """Load team access rules"""
        return {
            "global": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],  # All teams
            "marketing-team": ["MARKETING_*", "SOCIAL_MEDIA_*"],
            "sales-team": ["SALESFORCE_*", "HUBSPOT_*"],
            "engineering-team": ["GITHUB_*", "DOCKER_*", "K8S_*"],
            "executive-team": ["*"]  # Access to all
        }

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

        return False

    def grant_access(self, team: str, credential_pattern: str):
        """Grant team access to credentials matching pattern"""
        if team not in self.access_rules:
            self.access_rules[team] = []
        self.access_rules[team].append(credential_pattern)
        self._save_access_rules()
```

#### 2.3 Audit Logger
```python
class AuditLogger:
    """Comprehensive audit logging for credentials"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def log_access(self, team: str, credential: str, purpose: str):
        """Log successful credential access"""
        self._log_event({
            "event": "credential_accessed",
            "team": team,
            "credential": credential,
            "purpose": purpose,
            "timestamp": datetime.now().isoformat(),
            "success": True
        })

    def log_denied_access(self, team: str, credential: str, purpose: str):
        """Log denied credential access"""
        self._log_event({
            "event": "credential_denied",
            "team": team,
            "credential": credential,
            "purpose": purpose,
            "timestamp": datetime.now().isoformat(),
            "success": False
        })

        # Alert on denied access
        self._send_security_alert(f"Team {team} denied access to {credential}")

    def get_access_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate access report"""
        # Analyze access patterns
        # Identify anomalies
        # Return comprehensive report
        pass
```

### Phase 3: Integration (Week 3)

#### 3.1 Team Factory Integration
```python
# Update team factory to provision credentials
def create_team_with_credentials(team_name: str, team_config: Dict):
    """Create team with isolated credentials"""

    # Create team as before
    create_team(team_name, team_config)

    # Provision team-specific credentials
    cred_manager = CredentialManager()

    # Create subdivided API keys (if supported by provider)
    team_openai_key = create_subdivided_key(
        parent_key=cred_manager.get_credential("OPENAI_API_KEY", "global"),
        team=team_name,
        quota_limit=team_config.get('api_budget', 10.0)
    )

    cred_manager.create_credential(
        name=f"OPENAI_API_KEY_{team_name}",
        type=CredentialType.API_KEY,
        value=team_openai_key,
        team=team_name,
        expires_in_days=30
    )

    # Grant access
    access_control = TeamBasedAccessControl()
    access_control.grant_access(team_name, f"*_{team_name}")
```

#### 3.2 Deployment Pipeline Integration
```python
class SecureDeploymentPipeline(DeploymentPipeline):
    """Deployment pipeline with credential injection"""

    def __init__(self, *args, credential_manager: CredentialManager, **kwargs):
        super().__init__(*args, **kwargs)
        self.cred_manager = credential_manager

    async def _deploy_stage(self, context: DeploymentContext):
        """Deploy with injected credentials"""

        # Get team credentials
        team_creds = self._get_team_credentials(context.team_name)

        # Generate K8s secret
        secret_manifest = self._generate_secret_manifest(
            name=f"{context.team_name}-credentials",
            namespace=context.namespace,
            credentials=team_creds
        )

        # Apply secret
        self.k8s.apply_manifest(secret_manifest)

        # Update deployment to use secret
        await super()._deploy_stage(context)
```

#### 3.3 K8s Secret Generation
```python
def generate_k8s_secret(team_name: str, namespace: str) -> Dict[str, Any]:
    """Generate K8s secret for team"""

    cred_manager = CredentialManager()

    # Get all team credentials
    credentials = {}
    for cred_name in get_team_credential_names(team_name):
        value = cred_manager.get_credential(cred_name, team_name)
        if value:
            credentials[cred_name] = base64.b64encode(value.encode()).decode()

    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": f"{team_name}-credentials",
            "namespace": namespace
        },
        "type": "Opaque",
        "data": credentials
    }
```

### Phase 4: Advanced Features (Week 4)

#### 4.1 Automatic Rotation
```python
class CredentialRotationManager:
    """Manage automatic credential rotation"""

    def __init__(self, cred_manager: CredentialManager):
        self.cred_manager = cred_manager
        self.rotation_policies = {
            CredentialType.API_KEY: timedelta(days=30),
            CredentialType.DATABASE: timedelta(days=7),
            CredentialType.SERVICE_ACCOUNT: timedelta(days=90)
        }

    async def check_and_rotate(self):
        """Check all credentials and rotate if needed"""

        credentials = self.cred_manager.list_all_credentials()

        for cred in credentials:
            if self._needs_rotation(cred):
                await self._rotate_credential(cred)

    async def _rotate_credential(self, credential: Credential):
        """Rotate a specific credential"""

        # Generate new value
        new_value = await self._generate_new_credential(credential)

        # Update in zero-downtime manner
        # 1. Create new version
        # 2. Update half of services
        # 3. Verify working
        # 4. Update remaining services
        # 5. Revoke old version

        logger.info(f"Rotated credential {credential.name}")
```

#### 4.2 Dynamic Credentials
```python
class DynamicCredentialProvider:
    """Provide temporary credentials for specific operations"""

    def create_temporary_credential(self,
                                  team: str,
                                  purpose: str,
                                  duration_minutes: int = 60) -> Credential:
        """Create temporary credential"""

        # Generate temporary token
        temp_token = self._generate_temp_token(team, purpose, duration_minutes)

        # Store with expiration
        return self.cred_manager.create_credential(
            name=f"temp_{team}_{purpose}_{uuid.uuid4()}",
            type=CredentialType.API_KEY,
            value=temp_token,
            team=team,
            expires_in_days=0  # Use minutes instead
        )
```

## Security Considerations

### Encryption
- All credentials encrypted at rest using Fernet (AES-128)
- Encryption keys stored separately from data
- Key rotation every 90 days

### Access Control
- Team-based isolation by default
- Role-based permissions (read-only, admin)
- Principle of least privilege

### Audit Trail
- Every access logged with timestamp
- Failed access attempts tracked
- Anomaly detection for unusual patterns

### Compliance
- SOC2 Type 2 compatible logging
- GDPR compliant with right to audit
- ISO 27001 alignment

## Migration Strategy

### Step 1: Inventory
```python
# Script to inventory all current credentials
def inventory_credentials():
    """Find all credentials in use"""
    # Scan environment variables
    # Check K8s secrets
    # Review config files
    # Output comprehensive list
```

### Step 2: Gradual Migration
```python
# Migrate one team at a time
def migrate_team(team_name: str):
    """Migrate team to new credential system"""
    # 1. Create team credentials
    # 2. Update team deployments
    # 3. Monitor for issues
    # 4. Remove old credentials
```

### Step 3: Validation
```python
# Ensure everything still works
def validate_migration():
    """Validate all services working with new credentials"""
    # Test each service
    # Check logs for errors
    # Verify no hardcoded credentials remain
```

## CLI Interface

```bash
# Credential management CLI
elf-creds create --name GITHUB_TOKEN --type api_key --team engineering-team
elf-creds list --team marketing-team
elf-creds rotate --name OPENAI_API_KEY
elf-creds audit --days 7
elf-creds validate --all
```

## Monitoring & Alerts

### Metrics to Track
- Credential access frequency
- Failed access attempts
- Expiring credentials
- Rotation success rate
- Anomalous access patterns

### Alerts
- Credential expiring soon
- Failed rotation
- Denied access attempts
- Unusual access patterns
- Compliance violations

## Success Criteria

1. **No hardcoded credentials** in codebase
2. **100% encrypted** storage
3. **Team isolation** enforced
4. **Audit trail** for all access
5. **Automatic rotation** working
6. **Zero-downtime** updates
7. **Compliance** ready

## Next Steps

1. Implement Phase 1 immediately (security fixes)
2. Design review for Phase 2
3. Integration testing for Phase 3
4. Consider external tools for Phase 4
