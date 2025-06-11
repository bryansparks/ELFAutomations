#!/usr/bin/env python3
"""
Script to migrate from hardcoded credentials to secure credential management
PHASE 1: Remove hardcoded credentials and set up secure storage
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.credentials import (
    AuditLogger,
    CredentialManager,
    CredentialType,
    SecureCredentialStore,
    TeamBasedAccessControl,
)
from elf_automations.shared.utils.logging import setup_logger

logger = setup_logger(__name__)


def backup_file(file_path: Path) -> Path:
    """Create backup of file before modifying"""
    backup_path = file_path.with_suffix(file_path.suffix + ".backup")
    shutil.copy2(file_path, backup_path)
    logger.info(f"Created backup: {backup_path}")
    return backup_path


def remove_hardcoded_mcp_config():
    """Remove hardcoded credentials from MCP config files"""

    files_to_fix = [Path("config/mcp_config.json"), Path("mcp_supabase_config.json")]

    for config_file in files_to_fix:
        if not config_file.exists():
            continue

        logger.info(f"Fixing {config_file}")

        # Backup original
        backup_file(config_file)

        # Read config
        with open(config_file, "r") as f:
            config = json.load(f)

        # Replace hardcoded values with environment variable references
        if "servers" in config:
            for server_name, server_config in config["servers"].items():
                if "token" in server_config:
                    # Store the token value for migration
                    token_value = server_config["token"]
                    # Replace with placeholder
                    server_config["token"] = "${SUPABASE_ACCESS_TOKEN}"
                    logger.info(f"Replaced hardcoded token in {server_name}")

                if "env" in server_config:
                    if "SUPABASE_KEY" in server_config["env"]:
                        server_config["env"]["SUPABASE_KEY"] = "${SUPABASE_ANON_KEY}"

        # Write updated config
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Updated {config_file} to use environment variables")


def create_env_template():
    """Create .env.template file with required variables"""

    template_content = """# ElfAutomations Environment Variables Template
# Copy this to .env and fill in your actual values

# Master password for credential encryption
ELF_MASTER_PASSWORD=change_this_to_strong_password

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ACCESS_TOKEN=sbp_...

# Optional: External Services
GITHUB_TOKEN=
DOCKER_USERNAME=
DOCKER_PASSWORD=
SLACK_WEBHOOK_URL=
"""

    template_path = Path(".env.template")
    with open(template_path, "w") as f:
        f.write(template_content)

    logger.info("Created .env.template file")


def migrate_existing_credentials():
    """Migrate credentials from environment to secure storage"""

    # Initialize credential system
    store = SecureCredentialStore()
    access_control = TeamBasedAccessControl()
    audit_logger = AuditLogger()
    cred_manager = CredentialManager(store, access_control, audit_logger)

    # Credentials to migrate
    credentials_to_migrate = [
        ("OPENAI_API_KEY", CredentialType.API_KEY, None),  # Global
        ("ANTHROPIC_API_KEY", CredentialType.API_KEY, None),  # Global
        ("SUPABASE_URL", CredentialType.DATABASE, None),
        ("SUPABASE_ANON_KEY", CredentialType.API_KEY, None),
        ("SUPABASE_SERVICE_KEY", CredentialType.API_KEY, None),
        ("SUPABASE_ACCESS_TOKEN", CredentialType.API_KEY, None),
        ("GITHUB_TOKEN", CredentialType.API_KEY, "engineering-team"),
        ("DOCKER_USERNAME", CredentialType.SERVICE_ACCOUNT, "engineering-team"),
        ("DOCKER_PASSWORD", CredentialType.SERVICE_ACCOUNT, "engineering-team"),
    ]

    migrated = 0

    for cred_name, cred_type, team in credentials_to_migrate:
        value = os.getenv(cred_name)

        if value and value != "your_value_here":  # Skip placeholders
            try:
                cred_manager.create_credential(
                    name=cred_name,
                    value=value,
                    type=cred_type,
                    team=team,
                    expires_in_days=30 if cred_type == CredentialType.API_KEY else None,
                )

                logger.info(f"Migrated {cred_name} to secure storage")
                migrated += 1

            except Exception as e:
                logger.error(f"Failed to migrate {cred_name}: {e}")

    logger.info(f"Migrated {migrated} credentials to secure storage")

    return cred_manager


def update_k8s_secret_template():
    """Update k8s secret template to remove hardcoded values"""

    secret_file = Path("k8s/teams/secrets.yaml")

    if not secret_file.exists():
        logger.warning("K8s secrets file not found")
        return

    # Backup
    backup_file(secret_file)

    template_content = """apiVersion: v1
kind: Secret
metadata:
  name: elf-credentials
  namespace: elf-teams
type: Opaque
stringData:
  # These values will be populated by the credential manager
  # DO NOT hardcode values here!
  OPENAI_API_KEY: "${OPENAI_API_KEY}"
  ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY}"
  SUPABASE_URL: "${SUPABASE_URL}"
  SUPABASE_KEY: "${SUPABASE_ANON_KEY}"
  SUPABASE_SERVICE_KEY: "${SUPABASE_SERVICE_KEY}"
---
# Team-specific secrets will be generated automatically
# by the credential management system
"""

    with open(secret_file, "w") as f:
        f.write(template_content)

    logger.info("Updated k8s secrets template")


def create_credential_cli():
    """Create a simple CLI script for credential management"""

    cli_content = '''#!/usr/bin/env python3
"""
ElfAutomations Credential Management CLI
"""

import sys
import click
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.credentials import CredentialManager, CredentialType
from elf_automations.shared.utils.logging import setup_logger

logger = setup_logger(__name__)


@click.group()
def cli():
    """ElfAutomations Credential Management"""
    pass


@cli.command()
@click.option('--name', required=True, help='Credential name')
@click.option('--value', required=True, help='Credential value')
@click.option('--type', default='api_key', help='Credential type')
@click.option('--team', help='Team name (optional)')
def create(name, value, type, team):
    """Create a new credential"""
    cred_manager = CredentialManager()

    cred_type = CredentialType(type)
    credential = cred_manager.create_credential(
        name=name,
        value=value,
        type=cred_type,
        team=team
    )

    click.echo(f"Created credential: {name}")


@cli.command()
@click.option('--team', help='Filter by team')
def list(team):
    """List credentials"""
    cred_manager = CredentialManager()

    credentials = cred_manager.list_credentials(team)

    for cred in credentials:
        click.echo(f"{cred.name} ({cred.type.value}) - Team: {cred.team or 'global'}")


@cli.command()
@click.option('--name', required=True, help='Credential name')
@click.option('--team', help='Team name')
def rotate(name, team):
    """Rotate a credential"""
    cred_manager = CredentialManager()

    new_value = cred_manager.rotate_credential(name, team)
    click.echo(f"Rotated {name}")


@cli.command()
@click.option('--days', default=7, help='Number of days to audit')
def audit(days):
    """View audit logs"""
    from elf_automations.shared.credentials import AuditLogger

    audit = AuditLogger()
    report = audit.get_access_report(days)

    click.echo(f"\\nAudit Report - {report['period']}")
    click.echo(f"Total events: {report['total_events']}")
    click.echo("\\nBy event type:")
    for event_type, count in report['by_event_type'].items():
        click.echo(f"  {event_type}: {count}")


if __name__ == '__main__':
    cli()
'''

    cli_path = Path("scripts/elf-creds")
    with open(cli_path, "w") as f:
        f.write(cli_content)

    # Make executable
    cli_path.chmod(0o755)

    logger.info("Created credential management CLI at scripts/elf-creds")


def main():
    """Run credential migration"""

    logger.info("Starting credential migration - Phase 1")

    # Step 1: Remove hardcoded credentials from config files
    logger.info("Step 1: Removing hardcoded credentials from config files")
    remove_hardcoded_mcp_config()

    # Step 2: Create environment template
    logger.info("Step 2: Creating environment template")
    create_env_template()

    # Step 3: Migrate existing credentials to secure storage
    logger.info("Step 3: Migrating credentials to secure storage")
    cred_manager = migrate_existing_credentials()

    # Step 4: Update k8s templates
    logger.info("Step 4: Updating k8s secret templates")
    update_k8s_secret_template()

    # Step 5: Create CLI tool
    logger.info("Step 5: Creating credential management CLI")
    create_credential_cli()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("CREDENTIAL MIGRATION COMPLETE - PHASE 1")
    logger.info("=" * 60)

    logger.info("\nIMPORTANT NEXT STEPS:")
    logger.info("1. IMMEDIATELY rotate all exposed credentials:")
    logger.info("   - OpenAI API key")
    logger.info("   - Anthropic API key")
    logger.info("   - Supabase keys")
    logger.info("   - Any other exposed credentials")

    logger.info("\n2. Update your .env file with new credentials")
    logger.info("3. Set a strong ELF_MASTER_PASSWORD environment variable")
    logger.info("4. Remove .env from any git commits")
    logger.info("5. Consider using git-secrets or similar tools")

    logger.info("\n6. Use the credential CLI for management:")
    logger.info("   ./scripts/elf-creds --help")

    logger.info("\n7. Test credential access:")
    logger.info("   python scripts/test_credential_system.py")

    logger.warning("\nWARNING: Your current credentials may be compromised!")
    logger.warning("Rotate them immediately on the respective platforms.")


if __name__ == "__main__":
    main()
