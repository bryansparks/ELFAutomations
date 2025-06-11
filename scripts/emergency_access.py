#!/usr/bin/env python3
"""
Emergency access script for credential system
Use this only when normal access methods fail
"""

import json
import os
import sys
from datetime import datetime
from getpass import getpass
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.credentials import (
    BreakGlassAccess,
    CredentialManager,
    SecureCredentialStore,
)
from elf_automations.shared.utils.logging import setup_logger

logger = setup_logger(__name__)


def check_master_password():
    """Verify master password is set"""
    if not os.getenv("ELF_MASTER_PASSWORD"):
        print("\n⚠️  WARNING: Master password not found in environment!")
        print("Would you like to:")
        print("1. Enter it now (temporary)")
        print("2. Exit and set it properly")

        choice = input("\nChoice (1 or 2): ")

        if choice == "1":
            password = getpass("Enter master password: ")
            os.environ["ELF_MASTER_PASSWORD"] = password
            print("✓ Master password set for this session only")
        else:
            print("\nTo set master password permanently:")
            print("export ELF_MASTER_PASSWORD='your-secure-password'")
            sys.exit(1)


def show_system_status():
    """Display credential system status"""
    print("\n" + "=" * 60)
    print("CREDENTIAL SYSTEM STATUS CHECK")
    print("=" * 60)

    # Check files exist
    cred_dir = Path.home() / ".elf_automations" / "credentials"

    print(f"\n1. Credential Directory: {cred_dir}")
    if cred_dir.exists():
        print("   ✓ Directory exists")

        files = {
            ".key": "Master key file",
            "credentials.enc": "Encrypted credentials",
            "metadata.json": "Credential metadata",
        }

        for filename, description in files.items():
            filepath = cred_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"   ✓ {description}: {filename} ({size} bytes)")
            else:
                print(f"   ✗ {description}: {filename} (MISSING)")
    else:
        print("   ✗ Directory does not exist!")
        print("   → Run migration script first: python scripts/migrate_credentials.py")
        return False

    # Try to initialize credential manager
    print("\n2. Credential Manager:")
    try:
        mgr = CredentialManager()
        creds = mgr.list_credentials()
        print(f"   ✓ Initialized successfully")
        print(f"   ✓ Found {len(creds)} credentials")

        # Show credential summary
        if creds:
            print("\n   Credentials by team:")
            by_team = {}
            for cred in creds:
                team = cred.team or "global"
                if team not in by_team:
                    by_team[team] = []
                by_team[team].append(cred.name)

            for team, names in sorted(by_team.items()):
                print(f"   - {team}: {len(names)} credentials")

    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return False

    return True


def create_break_glass_token():
    """Create emergency access token"""
    print("\n" + "=" * 60)
    print("CREATE BREAK GLASS TOKEN")
    print("=" * 60)

    print("\n⚠️  WARNING: Break glass tokens should only be used in emergencies!")
    print("All usage is logged and alerts are generated.\n")

    name = input("Your name: ")
    reason = input("Reason for emergency access: ")

    confirm = input(f"\nCreate 1-hour emergency token for {name}? (yes/no): ")

    if confirm.lower() != "yes":
        print("Cancelled.")
        return

    try:
        break_glass = BreakGlassAccess()
        token = break_glass.create_token(
            created_by=name, reason=reason, duration_minutes=60
        )

        print("\n" + "=" * 60)
        print("EMERGENCY TOKEN CREATED")
        print("=" * 60)
        print(f"\nToken: {token}")
        print("\n⚠️  This token will expire in 1 hour")
        print("⚠️  This token can only be used ONCE")
        print("⚠️  All usage will be logged")
        print("\nStore this token securely. It cannot be retrieved again.")

    except Exception as e:
        print(f"\n✗ Failed to create token: {e}")


def export_all_credentials():
    """Export all credentials for emergency backup"""
    print("\n" + "=" * 60)
    print("EXPORT ALL CREDENTIALS")
    print("=" * 60)

    print("\n⚠️  This will export ALL credentials to a JSON file.")
    print("The exported file will contain UNENCRYPTED credentials!")

    confirm = input("\nProceed with export? (yes/no): ")

    if confirm.lower() != "yes":
        print("Cancelled.")
        return

    try:
        mgr = CredentialManager()

        # Need executive access for this
        print("\nUsing executive-level access to export all credentials...")

        backup = {"exported_at": datetime.now().isoformat(), "credentials": {}}

        # Get all credentials
        all_creds = mgr.list_credentials()
        exported = 0
        failed = 0

        for cred in all_creds:
            try:
                # Use executive team access to bypass restrictions
                value = mgr.get_credential(
                    cred.name, "executive-team", "emergency_export"
                )

                backup["credentials"][cred.name] = {
                    "value": value,
                    "type": cred.type.value,
                    "team": cred.team,
                    "created_at": cred.created_at.isoformat()
                    if cred.created_at
                    else None,
                    "expires_at": cred.expires_at.isoformat()
                    if cred.expires_at
                    else None,
                }
                exported += 1

            except Exception as e:
                print(f"   ✗ Failed to export {cred.name}: {e}")
                failed += 1

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"credential_backup_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(backup, f, indent=2)

        print(f"\n✓ Exported {exported} credentials to {filename}")
        if failed:
            print(f"✗ Failed to export {failed} credentials")

        print("\n⚠️  IMPORTANT: This file contains unencrypted credentials!")
        print("⚠️  Store it securely and delete after use!")

        # Set restrictive permissions
        os.chmod(filename, 0o600)
        print(f"✓ Set file permissions to 600 (owner read/write only)")

    except Exception as e:
        print(f"\n✗ Export failed: {e}")


def show_recovery_options():
    """Display recovery options menu"""
    while True:
        print("\n" + "=" * 60)
        print("CREDENTIAL SYSTEM EMERGENCY ACCESS")
        print("=" * 60)

        print("\nOptions:")
        print("1. Check system status")
        print("2. Create break glass token")
        print("3. Export all credentials (emergency backup)")
        print("4. Show recent audit logs")
        print("5. Test credential access")
        print("6. Exit")

        choice = input("\nSelect option (1-6): ")

        if choice == "1":
            show_system_status()

        elif choice == "2":
            create_break_glass_token()

        elif choice == "3":
            export_all_credentials()

        elif choice == "4":
            show_audit_logs()

        elif choice == "5":
            test_credential_access()

        elif choice == "6":
            print("\nExiting emergency access tool.")
            break

        else:
            print("\nInvalid option. Please try again.")

        input("\nPress Enter to continue...")


def show_audit_logs():
    """Display recent audit logs"""
    print("\n" + "=" * 60)
    print("RECENT AUDIT LOGS")
    print("=" * 60)

    try:
        from elf_automations.shared.credentials import AuditLogger

        audit = AuditLogger()
        events = audit.get_events(days=1)

        if not events:
            print("\nNo audit events in the last 24 hours.")
            return

        print(f"\nFound {len(events)} events in the last 24 hours:\n")

        for event in events[:20]:  # Show last 20
            timestamp = event.get("timestamp", "N/A")
            event_type = event.get("event", "N/A")
            team = event.get("team", "N/A")
            credential = event.get("credential", "N/A")
            success = "✓" if event.get("success", False) else "✗"

            print(f"{timestamp} | {success} | {event_type} | {team} | {credential}")

        if len(events) > 20:
            print(f"\n... and {len(events) - 20} more events")

    except Exception as e:
        print(f"\n✗ Failed to read audit logs: {e}")


def test_credential_access():
    """Test accessing a specific credential"""
    print("\n" + "=" * 60)
    print("TEST CREDENTIAL ACCESS")
    print("=" * 60)

    cred_name = input("\nCredential name (e.g., OPENAI_API_KEY): ")
    team_name = input("Team name (e.g., engineering-team): ")

    try:
        mgr = CredentialManager()
        value = mgr.get_credential(cred_name, team_name, "emergency_test")

        # Only show first/last few characters for security
        if len(value) > 10:
            masked = f"{value[:4]}...{value[-4:]}"
        else:
            masked = "***"

        print(f"\n✓ Successfully accessed {cred_name}")
        print(f"  Value: {masked} (length: {len(value)})")

    except Exception as e:
        print(f"\n✗ Failed to access {cred_name}: {e}")


def main():
    """Main emergency access function"""
    print("\n" + "=" * 60)
    print("ELFAUTOMATIONS CREDENTIAL SYSTEM - EMERGENCY ACCESS")
    print("=" * 60)

    # Check master password
    check_master_password()

    # Show menu
    show_recovery_options()


if __name__ == "__main__":
    main()
