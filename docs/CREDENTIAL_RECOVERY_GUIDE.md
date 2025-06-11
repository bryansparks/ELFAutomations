# Credential System Recovery Guide

## Quick Recovery Checklist

If you're locked out or something isn't working, follow these steps in order:

### 1. ✅ Check Master Password
```bash
echo $ELF_MASTER_PASSWORD
```
If empty, set it:
```bash
export ELF_MASTER_PASSWORD="your-master-password"
```

### 2. ✅ Verify Credential Files Exist
```bash
ls -la ~/.elf_automations/credentials/
```
Should see:
- `.key` - Your encrypted master key
- `credentials.enc` - Your encrypted credentials
- `metadata.json` - Credential metadata

### 3. ✅ Test Basic Access
```bash
python scripts/test_credential_system.py
```

### 4. ✅ Use Break Glass (Emergency Only)
```bash
python scripts/emergency_access.py
```

---

## Common Scenarios & Solutions

### Scenario 1: "I forgot my master password"

**Symptoms**:
- Can't decrypt any credentials
- Getting "Failed to decrypt" errors

**Recovery Options**:

1. **If you have backups** of `~/.elf_automations/`:
   - Restore the backup
   - Try to remember the password used when backup was created

2. **If credentials are still in .env file**:
   - Create new master password
   - Re-run migration:
   ```bash
   rm -rf ~/.elf_automations/credentials/
   export ELF_MASTER_PASSWORD="new-strong-password"
   python scripts/migrate_credentials.py
   ```

3. **If no backups and no .env**:
   - You'll need to regenerate all credentials on their platforms
   - Set new master password and start fresh

### Scenario 2: "The system says team can't access credential"

**Symptoms**:
- "AccessDeniedError: Team X cannot access Y"

**Solution**:
```bash
# Check current access rules
cat ~/.elf_automations/access_rules.json

# Grant access using CLI
./scripts/elf-creds grant-access --team "your-team" --pattern "CREDENTIAL_*"

# Or manually edit access_rules.json and add your pattern
```

### Scenario 3: "I need emergency access to all credentials"

**Use Break Glass Access**:

1. Create emergency token:
```python
from elf_automations.shared.credentials import BreakGlassAccess

break_glass = BreakGlassAccess()
token = break_glass.create_token(
    created_by="your_name",
    reason="Emergency: System down, need credential access",
    duration_minutes=60
)
print(f"Emergency token: {token}")
```

2. Use token to bypass access controls:
```python
# This grants temporary executive-level access
# Token expires in 1 hour and can only be used once
```

### Scenario 4: "Credentials aren't loading in my app"

**Check these in order**:

1. **Environment variable set?**
   ```bash
   env | grep ELF_MASTER_PASSWORD
   ```

2. **Credential exists?**
   ```bash
   ./scripts/elf-creds list
   ```

3. **Team has access?**
   ```bash
   ./scripts/elf-creds check-access --team "your-team" --credential "CRED_NAME"
   ```

4. **View audit logs**:
   ```bash
   ./scripts/elf-creds audit --days 1
   ```

### Scenario 5: "System is completely broken"

**Nuclear Option - Start Fresh**:

1. **Backup current state** (just in case):
   ```bash
   cp -r ~/.elf_automations ~/.elf_automations.backup
   ```

2. **Reset everything**:
   ```bash
   rm -rf ~/.elf_automations
   ```

3. **Set new master password**:
   ```bash
   export ELF_MASTER_PASSWORD="new-password"
   ```

4. **Re-import from .env**:
   ```bash
   python scripts/migrate_credentials.py
   ```

---

## Manual Credential Operations

### View Encrypted Credential (for debugging)
```python
from elf_automations.shared.credentials import SecureCredentialStore

store = SecureCredentialStore()
# List all credential keys
print(store.list_keys())

# Get specific credential
value = store.retrieve("global:OPENAI_API_KEY")
print(value)
```

### Manually Add Credential
```python
from elf_automations.shared.credentials import CredentialManager, CredentialType

mgr = CredentialManager()
mgr.create_credential(
    name="NEW_API_KEY",
    value="your-api-key-value",
    type=CredentialType.API_KEY,
    team="your-team"
)
```

### Export All Credentials (Backup)
```python
from elf_automations.shared.credentials import CredentialManager
import json

mgr = CredentialManager()
backup = {}

for cred in mgr.list_credentials():
    try:
        value = mgr.get_credential(cred.name, "executive-team", "backup")
        backup[cred.name] = {
            "value": value,
            "type": cred.type.value,
            "team": cred.team
        }
    except:
        pass

with open("credentials_backup.json", "w") as f:
    json.dump(backup, f, indent=2)
print("Backed up to credentials_backup.json")
```

### Restore from Backup
```python
import json
from elf_automations.shared.credentials import CredentialManager, CredentialType

mgr = CredentialManager()

with open("credentials_backup.json", "r") as f:
    backup = json.load(f)

for name, data in backup.items():
    mgr.create_credential(
        name=name,
        value=data["value"],
        type=CredentialType(data["type"]),
        team=data.get("team")
    )
print(f"Restored {len(backup)} credentials")
```

---

## Understanding the File Structure

### Credential Storage
```
~/.elf_automations/credentials/
├── .key                    # Your master key (encrypted with master password)
├── credentials.enc         # All credentials (double encrypted)
└── metadata.json          # Non-sensitive metadata
```

### What Each File Does

1. **`.key`**:
   - Contains the Fernet encryption key
   - Encrypted using PBKDF2 from your master password
   - Without master password, this file is useless

2. **`credentials.enc`**:
   - Contains all your actual credential values
   - Encrypted with the key from `.key` file
   - Double protection: master password → key → credentials

3. **`metadata.json`**:
   - Tracks when credentials were created/updated
   - Stores credential types and expiration
   - Not encrypted (contains no sensitive data)

---

## CLI Tool Reference

### List all credentials
```bash
./scripts/elf-creds list
```

### Get specific credential
```bash
./scripts/elf-creds get --name OPENAI_API_KEY --team engineering-team
```

### Create new credential
```bash
./scripts/elf-creds create \
  --name NEW_API_KEY \
  --value "secret-value" \
  --type api_key \
  --team your-team
```

### Rotate credential
```bash
./scripts/elf-creds rotate --name OPENAI_API_KEY
```

### View audit log
```bash
./scripts/elf-creds audit --days 7
```

### Check team access
```bash
./scripts/elf-creds check-access \
  --team marketing-team \
  --credential OPENAI_API_KEY
```

---

## Security Best Practices

1. **Master Password**:
   - Use a strong, unique password
   - Store it in a password manager
   - Never commit it to git
   - Consider using a passphrase

2. **Backups**:
   - Regularly backup `~/.elf_automations/`
   - Backups are encrypted, safe to store
   - Test restore process periodically

3. **Rotation**:
   - Follow the rotation schedule
   - Rotate immediately if compromised
   - Update all services after rotation

4. **Access Control**:
   - Follow principle of least privilege
   - Only grant access teams actually need
   - Review access quarterly

5. **Monitoring**:
   - Check audit logs regularly
   - Set up alerts for failed access
   - Monitor break glass usage

---

## Troubleshooting Commands

### Check if master password is correct
```python
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

password = os.getenv("ELF_MASTER_PASSWORD", "").encode()
salt = b'elf-automations-salt'
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
key = base64.urlsafe_b64encode(kdf.derive(password))

try:
    cipher = Fernet(key)
    print("✓ Master password appears valid")
except:
    print("✗ Master password might be wrong")
```

### View recent audit events
```bash
tail -n 50 ~/.elf_automations/audit/audit_$(date +%Y-%m-%d).jsonl | jq .
```

### Check credential age
```bash
./scripts/elf-creds list --verbose | grep -E "(created_at|last_rotated)"
```

---

## Emergency Contact

If you're completely locked out and none of the above works:

1. **Check your backups** first
2. **Check .env.backup** files created by migration
3. **Check git history** for old .env files (before deletion)
4. **Last resort**: Regenerate all credentials on their platforms

Remember: The master password is the key to everything. Without it, the encrypted credentials cannot be recovered. This is by design for security, but means you must remember or securely store this password!
