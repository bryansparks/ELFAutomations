#!/usr/bin/env python3
"""Add missing credentials that weren't in .env"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.credentials import CredentialManager, CredentialType

# Initialize
mgr = CredentialManager()

# Add missing credentials
credentials_to_add = [
    (
        "SUPABASE_ACCESS_TOKEN",
        "sbp_ef3207c7d423da1baceba2716f383a33091f5252",
        CredentialType.API_KEY,
    ),
    (
        "SUPABASE_SERVICE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxjeXpwcXlkb3FwY3NkbHRzdXlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODk5MDY0OCwiZXhwIjoyMDY0NTY2NjQ4fQ.bzdPUB0Nz-iK50zgQp4LSNY6ILDehiFMw4tpU6MhJws",
        CredentialType.API_KEY,
    ),
]

for name, value, cred_type in credentials_to_add:
    try:
        # Check if already exists
        existing = mgr.get_credential(name, "system", "check")
        print(f"✓ {name} already exists")
    except:
        # Add it
        mgr.create_credential(
            name=name,
            value=value,
            type=cred_type,
            team=None,  # Global
            expires_in_days=30,
        )
        print(f"✓ Added {name} to secure storage")

print("\n⚠️  IMPORTANT: These credentials were exposed in git!")
print("Please rotate them immediately on the Supabase platform.")
