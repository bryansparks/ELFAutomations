# Credential Management System - What We Built

## Overview

We've implemented a **local, self-contained credential management system** for ElfAutomations that runs entirely within your k3s infrastructure without requiring external services like AWS Secrets Manager or HashiCorp Vault.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Your Access                        │
│  Master Password → Encryption Key → All Credentials  │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────┐
│              Credential Store                        │
│  • Encrypted files in ~/.elf_automations/           │
│  • Fernet encryption (AES-128)                      │
│  • Master password derives encryption key           │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────┐
│           Credential Manager                         │
│  • CRUD operations                                  │
│  • Team-based access control                        │
│  • Automatic rotation                              │
│  • Audit logging                                    │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────┐
│         K3s Integration                              │
│  • Generates Kubernetes secrets                     │
│  • Per-team isolation                              │
│  • RBAC policies                                   │
└─────────────────────────────────────────────────────┘
```

## What Gets Created

### 1. Local Storage Directory
```
~/.elf_automations/
├── credentials/
│   ├── .key                    # Encrypted master key (derived from password)
│   ├── credentials.enc         # Encrypted credential values
│   └── metadata.json          # Credential metadata (non-sensitive)
├── audit/
│   └── audit_2025-01-21.jsonl # Daily audit logs
├── break_glass/
│   └── tokens.json            # Emergency access tokens
└── access_rules.json          # Team access control rules
```

### 2. How Encryption Works

1. **Master Password** → You provide this (environment variable: `ELF_MASTER_PASSWORD`)
2. **Key Derivation** → Password + salt → PBKDF2 → 256-bit key
3. **Encryption** → Fernet (symmetric encryption) using derived key
4. **Storage** → Encrypted credentials saved to disk

**Important**: The master password is NEVER stored anywhere. It must be provided each time the system starts.

### 3. Access Control Layers

#### Layer 1: Master Password
- **What it does**: Unlocks the entire credential store
- **Without it**: Cannot decrypt ANY credentials
- **Storage**: Only in your environment/memory

#### Layer 2: Team-Based Access
- **What it does**: Controls which teams can access which credentials
- **Example**: marketing-team can only access MARKETING_* credentials
- **Override**: executive-team has access to all credentials

#### Layer 3: Audit Trail
- **What it does**: Logs every access attempt (successful and failed)
- **Purpose**: Compliance and security monitoring

## Security Features

### 1. No Hardcoded Credentials
- All credentials moved from config files to encrypted storage
- Config files now use placeholders like `${OPENAI_API_KEY}`

### 2. Credential Types & Rotation
```
API Keys        → Rotate every 30 days
Database        → Rotate every 7 days
Service Account → Rotate every 90 days
JWT Secrets     → Rotate every 14 days
Certificates    → Rotate every 365 days
```

### 3. Break Glass Emergency Access
- **Purpose**: Emergency access when normal systems fail
- **How it works**:
  1. Generate time-limited token (1 hour)
  2. Token can only be used ONCE
  3. Full audit trail created
  4. Alerts sent on use
- **No backdoor**: Tokens expire and cannot be reused

### 4. Team Isolation
```
marketing-team → Can access:
  - MARKETING_*
  - SOCIAL_*
  - OPENAI_API_KEY (global)
  - ANTHROPIC_API_KEY (global)

engineering-team → Can access:
  - GITHUB_*
  - DOCKER_*
  - K8S_*
  - SUPABASE_*
  - OPENAI_API_KEY (global)
  - ANTHROPIC_API_KEY (global)

executive-team → Can access:
  - * (everything)
```

## What Changes for You

### Before (Insecure)
```json
// config/mcp_config.json
{
  "token": "sbp_ef3207c7d423da1baceba2716f383a33091f5252"
}
```

```yaml
# k8s/secrets.yaml
data:
  OPENAI_API_KEY: "sk-proj-actualkey"
```

### After (Secure)
```json
// config/mcp_config.json
{
  "token": "${SUPABASE_ACCESS_TOKEN}"
}
```

```yaml
# k8s/secrets.yaml - Generated automatically
data:
  OPENAI_API_KEY: "base64-encoded-encrypted-value"
```

## Key Files Created

1. **Credential Store Module**
   - `/elf_automations/shared/credentials/credential_store.py`
   - Handles encryption/decryption

2. **Credential Manager**
   - `/elf_automations/shared/credentials/credential_manager.py`
   - Main interface for all operations

3. **Access Control**
   - `/elf_automations/shared/credentials/access_control.py`
   - Team permissions and break-glass access

4. **Migration Script**
   - `/scripts/migrate_credentials.py`
   - Moves credentials from env/configs to secure storage

5. **CLI Tool**
   - `/scripts/elf-creds`
   - Command-line interface for credential management

## Data Flow Example

1. **Team requests credential**:
   ```
   marketing-team → requests → OPENAI_API_KEY
   ```

2. **Access control check**:
   ```
   Can marketing-team access OPENAI_API_KEY? → YES (global credential)
   ```

3. **Decrypt credential**:
   ```
   Master Password → Derive Key → Decrypt → Return Value
   ```

4. **Audit log**:
   ```
   [2025-01-21T10:30:45] credential_accessed: marketing-team accessed OPENAI_API_KEY
   ```

## What's Protected

1. **All API Keys**: OpenAI, Anthropic, Supabase, GitHub, etc.
2. **Database Credentials**: Connection strings, passwords
3. **Service Accounts**: Docker, K8s, cloud services
4. **Secrets**: JWT secrets, webhook URLs
5. **Future Credentials**: Any new credentials automatically protected

## Recovery Mechanisms

1. **Master Password**: As long as you have this, you can access everything
2. **Break Glass**: Emergency one-time tokens for critical situations
3. **Audit Trail**: Complete history of all credential operations
4. **Backups**: Credential files can be backed up (they're encrypted)

## Migration Process

The migration script (`migrate_credentials.py`) will:

1. **Backup** all modified files (*.backup)
2. **Remove** hardcoded credentials from configs
3. **Import** existing credentials from environment
4. **Create** secure storage with encryption
5. **Generate** templates and documentation
6. **Provide** CLI tool for management

## Important Notes

1. **Master Password**: This is your key to everything. Store it securely!
2. **No External Dependencies**: Runs entirely local, no cloud services needed
3. **GitOps Safe**: Configs can be committed (no secrets in them)
4. **Team Autonomy**: Teams can only access their own credentials
5. **Full Audit**: Every action is logged for compliance

## Next Steps After Migration

1. Set master password in environment
2. Run migration script
3. Rotate compromised credentials on platforms
4. Test with provided test script
5. Start using CLI for credential management
