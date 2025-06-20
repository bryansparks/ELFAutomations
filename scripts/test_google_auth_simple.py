#!/usr/bin/env python3
"""
Simple test for Google OAuth authentication setup.

This version doesn't require the full elf_automations module.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def check_google_credentials():
    """Check if Google OAuth credentials are configured."""
    console.print(Panel.fit(
        "[bold cyan]Google OAuth Credential Check[/bold cyan]\n\n"
        "Verifying Google Cloud configuration",
        border_style="cyan"
    ))
    
    # Check for credentials
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/oauth2callback")
    
    table = Table(title="OAuth Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Value", style="yellow")
    
    # Client ID
    if client_id:
        table.add_row(
            "GOOGLE_CLIENT_ID",
            "✓ Set",
            f"{client_id[:20]}...{client_id[-10:]}" if len(client_id) > 30 else client_id
        )
    else:
        table.add_row("GOOGLE_CLIENT_ID", "[red]✗ Missing[/red]", "Not set")
    
    # Client Secret
    if client_secret:
        table.add_row(
            "GOOGLE_CLIENT_SECRET",
            "✓ Set",
            f"{client_secret[:5]}...{client_secret[-5:]}"
        )
    else:
        table.add_row("GOOGLE_CLIENT_SECRET", "[red]✗ Missing[/red]", "Not set")
    
    # Redirect URI
    table.add_row("GOOGLE_REDIRECT_URI", "✓ Set", redirect_uri)
    
    console.print(table)
    
    if not client_id or not client_secret:
        console.print("\n[red]Missing required credentials![/red]")
        return False
    
    return True


def test_google_packages():
    """Test if Google packages are installed."""
    console.print("\n[yellow]Checking Google API packages...[/yellow]")
    
    packages = {
        "google.auth": "google-auth",
        "google_auth_oauthlib": "google-auth-oauthlib",
        "googleapiclient": "google-api-python-client"
    }
    
    all_installed = True
    for module, package in packages.items():
        try:
            __import__(module)
            console.print(f"[green]✓ {package} is installed[/green]")
        except ImportError:
            console.print(f"[red]✗ {package} is NOT installed[/red]")
            all_installed = False
    
    if not all_installed:
        console.print("\n[yellow]Install missing packages with:[/yellow]")
        console.print("pip install google-auth google-auth-oauthlib google-api-python-client")
    
    return all_installed


def test_oauth_url_generation():
    """Test generating an OAuth URL without full module."""
    try:
        from google_auth_oauthlib.flow import Flow
        
        console.print("\n[yellow]Testing OAuth URL generation...[/yellow]")
        
        client_config = {
            "installed": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/oauth2callback"]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/drive.metadata.readonly'
            ],
            redirect_uri="http://localhost:8080/oauth2callback"
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        console.print("[green]✓ OAuth URL generation successful![/green]")
        console.print(f"\n[dim]Sample auth URL (first 100 chars):[/dim]")
        console.print(f"[dim]{auth_url[:100]}...[/dim]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ OAuth URL generation failed: {e}[/red]")
        return False


def check_drive_folders():
    """Check if Google Drive folder structure is documented."""
    console.print("\n[bold]Google Drive Folder Structure:[/bold]")
    console.print("""
Your Google Drive should have this structure:

/elf-drops/
├── core/           # Internal ELF documents
├── acme-corp/      # ACME Corporation (tenant: acme_corp)
├── globex-inc/     # Globex Inc (tenant: globex_inc)
└── stanford-edu/   # Stanford University (tenant: stanford_edu)

Each folder will be monitored for the corresponding tenant.
""")


def check_nodejs_npm():
    """Check if Node.js and npm are installed."""
    console.print("\n[yellow]Checking Node.js and npm...[/yellow]")
    
    import subprocess
    
    try:
        # Check Node.js
        node_result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if node_result.returncode == 0:
            console.print(f"[green]✓ Node.js is installed: {node_result.stdout.strip()}[/green]")
        else:
            console.print("[red]✗ Node.js is NOT installed[/red]")
            return False
            
        # Check npm
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if npm_result.returncode == 0:
            console.print(f"[green]✓ npm is installed: {npm_result.stdout.strip()}[/green]")
        else:
            console.print("[red]✗ npm is NOT installed[/red]")
            return False
            
        return True
        
    except FileNotFoundError:
        console.print("[red]✗ Node.js/npm not found in PATH[/red]")
        return False


def main():
    """Main test function."""
    all_good = True
    
    # Check credentials
    creds_ok = check_google_credentials()
    all_good = all_good and creds_ok
    
    # Check packages
    packages_ok = test_google_packages()
    all_good = all_good and packages_ok
    
    # Check Node.js (needed for MCP)
    node_ok = check_nodejs_npm()
    all_good = all_good and node_ok
    
    if creds_ok and packages_ok:
        # Test OAuth URL generation
        oauth_ok = test_oauth_url_generation()
        all_good = all_good and oauth_ok
    
    if all_good:
        console.print("\n[green]✅ All checks passed! Ready to build Google Drive MCP.[/green]")
        
        # Show next steps
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Build the Google Drive MCP:")
        console.print("   ./scripts/setup_drive_watcher.sh")
        console.print("\n2. Set up OAuth for each tenant:")
        console.print("   python scripts/setup_google_oauth.py")
        console.print("\n3. Create the folder structure in Google Drive")
        
        check_drive_folders()
        
        console.print("\n[bold]Manual Build Steps:[/bold]")
        console.print("cd mcps/google-drive-watcher")
        console.print("npm install")
        console.print("npm run build")
        console.print("docker build -t elf-automations/google-drive-watcher:latest .")
        
        return 0
    else:
        console.print("\n[red]Some checks failed. Please fix the issues above.[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())