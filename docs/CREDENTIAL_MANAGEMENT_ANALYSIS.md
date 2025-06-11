# Credential Management Analysis for ElfAutomations

## Current Status (January 2025)

### 1. Current Credential Usage

#### API Keys Required
- **OPENAI_API_KEY**: Used by LLM factory for GPT models
- **ANTHROPIC_API_KEY**: Used by LLM factory for Claude models
- **SUPABASE_URL**: Database connection URL
- **SUPABASE_ANON_KEY**: Public Supabase key
- **SUPABASE_SERVICE_KEY**: Admin Supabase key (for schema operations)

#### Optional Credentials
- **GITHUB_TOKEN**: For GitOps operations
- **DOCKER_USERNAME/PASSWORD**: For registry operations
- **SLACK_WEBHOOK_URL**: Production monitoring
- **PAGERDUTY_API_KEY**: Production alerting

#### Storage Methods Currently Used
1. **Environment Variables**: Primary method via `os.getenv()`
2. **K8s Secrets**: Basic secret manifest in `/k8s/teams/secrets.yaml`
3. **Config Files**: Some credentials exposed in `/config/mcp_config.json`
4. **ConfigManager**: Has encryption capability but underutilized

### 2. Security Gaps Identified

#### Critical Issues
1. **Hardcoded Credentials**:
   - Supabase tokens in `/config/mcp_config.json`
   - Access token: `sbp_ef3207c7d423da1baceba2716f383a33091f5252`
   - Anon key exposed in plain text

2. **No Rotation Mechanism**:
   - Static credentials with no expiration
   - No automated rotation process
   - No tracking of credential age

3. **Shared Credentials**:
   - All teams use same API keys
   - No per-team isolation
   - No usage attribution

4. **Plain Text Storage**:
   - K8s secrets template has placeholder values
   - No encryption at rest for local development
   - .env files with sensitive data

#### Medium Risk Issues
1. **No Access Control**:
   - Any team can access any credential
   - No audit trail for credential usage
   - No principle of least privilege

2. **Manual Management**:
   - Developers manually update .env files
   - No centralized credential distribution
   - Inconsistent across environments

3. **Missing Validation**:
   - No credential validation on startup
   - Silent failures when credentials missing
   - No expiration checking

### 3. Requirements for Comprehensive System

#### Core Requirements
1. **Secure Storage**:
   - Encrypted at rest
   - Secure key management
   - Environment isolation

2. **Access Control**:
   - Team-based access policies
   - Role-based permissions
   - Audit logging

3. **Rotation Support**:
   - Automated rotation workflows
   - Zero-downtime rotation
   - Version management

4. **Integration**:
   - K8s native integration
   - MCP server support
   - Team factory integration

#### Compliance Requirements
1. **Audit Trail**:
   - Who accessed what, when
   - Changes tracked
   - Compliance reporting

2. **Encryption**:
   - TLS in transit
   - AES-256 at rest
   - Key rotation

3. **Backup/Recovery**:
   - Credential backup
   - Disaster recovery
   - Version history

### 4. Integration Points

#### Team Integration
- Teams request credentials via manifest
- Credentials injected at runtime
- Per-team namespaces in K8s

#### MCP Server Integration
- MCPs need database credentials
- API keys for external services
- Secure credential passing

#### K8s Integration
- Native K8s secrets
- ServiceAccount bindings
- RBAC policies

#### Database Connections
- Connection pooling with credentials
- Credential refresh on rotation
- Encrypted connections

### 5. Recommendations

#### Phase 1: Immediate Security Fixes
1. Remove hardcoded credentials from git
2. Implement proper K8s secrets
3. Add credential validation
4. Enable ConfigManager encryption

#### Phase 2: Centralized Management
1. Implement HashiCorp Vault or similar
2. Create credential management service
3. Add team-based access control
4. Implement audit logging

#### Phase 3: Advanced Features
1. Automated rotation
2. Dynamic credentials
3. Just-in-time access
4. Credential analytics

### 6. Proposed Architecture

```
┌─────────────────────┐
│   Vault/KMS        │
│  (Central Store)    │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │  Credential  │
    │   Manager    │
    │   Service    │
    └──────┬──────┘
           │
    ┌──────┴──────────────┬─────────────┬──────────────┐
    │                     │             │              │
┌───▼────┐        ┌──────▼─────┐ ┌─────▼──────┐ ┌─────▼────┐
│  K8s   │        │    Team    │ │    MCP     │ │ Database │
│Secrets │        │  Runtimes  │ │  Servers   │ │  Conns   │
└────────┘        └────────────┘ └────────────┘ └──────────┘
```

### 7. Implementation Priority

1. **Critical** (Do Now):
   - Remove hardcoded credentials
   - Implement basic K8s secrets
   - Add validation

2. **High** (Next Sprint):
   - Credential manager service
   - Team-based access
   - Audit logging

3. **Medium** (Q1 2025):
   - Automated rotation
   - Vault integration
   - Advanced monitoring

4. **Low** (Future):
   - Dynamic credentials
   - ML-based anomaly detection
   - Cross-region replication

### 8. Example Implementation

```python
# Proposed CredentialManager class
class CredentialManager:
    def __init__(self, backend='k8s'):
        self.backend = self._init_backend(backend)

    def get_credential(self, key: str, team: str) -> str:
        # Check access policy
        if not self._check_access(team, key):
            raise PermissionError(f"Team {team} cannot access {key}")

        # Get from backend
        value = self.backend.get(key)

        # Audit log
        self._audit_log(team, key, 'accessed')

        return value

    def rotate_credential(self, key: str):
        # Create new version
        new_value = self._generate_new_value(key)

        # Store with version
        self.backend.store(key, new_value, version='new')

        # Grace period for old version
        self._schedule_deprecation(key, 'old', hours=24)
```

### 9. Security Checklist

- [ ] Remove all hardcoded credentials
- [ ] Implement encryption at rest
- [ ] Add access control policies
- [ ] Enable audit logging
- [ ] Set up rotation schedules
- [ ] Add monitoring/alerting
- [ ] Document procedures
- [ ] Train team on usage
- [ ] Regular security audits
- [ ] Compliance validation

### 10. Next Steps

1. **Immediate**: Fix hardcoded credentials in `/config/mcp_config.json`
2. **This Week**: Implement proper K8s secrets for all teams
3. **Next Week**: Design credential manager service
4. **This Month**: Deploy basic credential management
5. **Q1 2025**: Full system with rotation and audit
