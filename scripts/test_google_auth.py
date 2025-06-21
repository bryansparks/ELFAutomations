#!/usr/bin/env python3
"""
Test Google OAuth authentication setup.

This script helps verify that Google OAuth credentials are properly configured.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def check_google_credentials():
    """Check if Google OAuth credentials are configured."""
    console.print(
        Panel.fit(
            "[bold cyan]Google OAuth Credential Check[/bold cyan]\n\n"
            "Verifying Google Cloud configuration",
            border_style="cyan",
        )
    )

    # Check for credentials
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8080/oauth2callback"
    )

    table = Table(title="OAuth Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Value", style="yellow")

    # Client ID
    if client_id:
        table.add_row(
            "GOOGLE_CLIENT_ID",
            "✓ Set",
            f"{client_id[:20]}...{client_id[-10:]}"
            if len(client_id) > 30
            else client_id,
        )
    else:
        table.add_row("GOOGLE_CLIENT_ID", "[red]✗ Missing[/red]", "Not set")

    # Client Secret
    if client_secret:
        table.add_row(
            "GOOGLE_CLIENT_SECRET",
            "✓ Set",
            f"{client_secret[:5]}...{client_secret[-5:]}",
        )
    else:
        table.add_row("GOOGLE_CLIENT_SECRET", "[red]✗ Missing[/red]", "Not set")

    # Redirect URI
    table.add_row("GOOGLE_REDIRECT_URI", "✓ Set", redirect_uri)

    console.print(table)

    if not client_id or not client_secret:
        console.print("\n[red]Missing required credentials![/red]")
        console.print("\n[bold]To get Google OAuth credentials:[/bold]")
        console.print("1. Go to https://console.cloud.google.com")
        console.print("2. Create or select a project")
        console.print("3. Enable Google Drive API:")
        console.print(
            "   - APIs & Services > Library > Search 'Google Drive API' > Enable"
        )
        console.print("4. Create OAuth 2.0 credentials:")
        console.print(
            "   - APIs & Services > Credentials > Create Credentials > OAuth client ID"
        )
        console.print("   - Application type: Web application")
        console.print(
            "   - Add authorized redirect URI: http://localhost:8080/oauth2callback"
        )
        console.print("5. Download credentials and add to .env file")
        return False

    return True


def test_google_auth_flow():
    """Test the OAuth flow without full setup."""
    try:
        from elf_automations.shared.auth import GoogleOAuthManager

        console.print("\n[yellow]Testing OAuth manager initialization...[/yellow]")

        manager = GoogleOAuthManager()
        console.print("[green]✓ OAuth manager initialized[/green]")

        # Try to generate auth URL
        test_url = manager.get_authorization_url("test_tenant")
        console.print("[green]✓ Can generate authorization URLs[/green]")
        console.print(f"\n[dim]Sample auth URL (first 100 chars):[/dim]")
        console.print(f"[dim]{test_url[:100]}...[/dim]")

        return True

    except Exception as e:
        console.print(f"[red]✗ OAuth manager test failed: {e}[/red]")
        return False


def check_drive_folders():
    """Check if Google Drive folder structure is documented."""
    console.print("\n[bold]Google Drive Folder Structure:[/bold]")
    console.print(
        """
Your Google Drive should have this structure:

/elf-drops/
├── core/           # Internal ELF documents
├── acme-corp/      # ACME Corporation (tenant: acme_corp)
├── globex-inc/     # Globex Inc (tenant: globex_inc)
└── stanford-edu/   # Stanford University (tenant: stanford_edu)

Each folder will be monitored for the corresponding tenant.
"""
    )


def main():
    """Main test function."""
    # Check credentials
    creds_ok = check_google_credentials()

    if creds_ok:
        # Test OAuth manager
        auth_ok = test_google_auth_flow()

        if auth_ok:
            console.print("\n[green]✅ Google OAuth is properly configured![/green]")

            # Show next steps
            console.print("\n[bold]Next Steps:[/bold]")
            console.print("1. Build the Google Drive MCP:")
            console.print("   ./scripts/setup_drive_watcher.sh")
            console.print("\n2. Set up OAuth for each tenant:")
            console.print("   python scripts/setup_google_oauth.py")
            console.print("\n3. Create the folder structure in Google Drive")

            check_drive_folders()

            return 0
        else:
            console.print("\n[red]OAuth manager initialization failed[/red]")
            console.print("Check that all required packages are installed:")
            console.print(
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
            return 1
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
