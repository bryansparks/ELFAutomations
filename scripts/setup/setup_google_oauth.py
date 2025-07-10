#!/usr/bin/env python3
"""
Setup Google OAuth for multi-tenant Drive access.

This script helps configure Google OAuth credentials for each tenant
that needs access to Google Drive for document ingestion.
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from elf_automations.shared.auth import GoogleOAuthManager
from elf_automations.shared.config import get_supabase_client
from elf_automations.shared.utils.logging import get_logger
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()
logger = get_logger(__name__)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def do_GET(self):
        """Handle OAuth callback."""
        # Parse query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)

        # Get authorization code
        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.server.state = params.get("state", [None])[0]

            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = """
            <html>
            <head><title>OAuth Success</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✅ Authorization Successful!</h1>
                <p>You can now close this window and return to the terminal.</p>
                <script>window.setTimeout(function(){window.close();}, 3000);</script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            # Error response
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            error = params.get("error", ["Unknown error"])[0]
            html = f"""
            <html>
            <head><title>OAuth Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: red;">❌ Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>Please return to the terminal and try again.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress request logging."""
        pass


def start_callback_server(port: int = 8080) -> HTTPServer:
    """Start local server for OAuth callback."""
    server = HTTPServer(("localhost", port), OAuthCallbackHandler)
    server.auth_code = None
    server.state = None

    # Start server in background thread
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    return server


def setup_tenant_oauth(tenant_name: str):
    """Set up Google OAuth for a specific tenant."""
    console.print(
        f"\n[bold cyan]Setting up Google OAuth for tenant: {tenant_name}[/bold cyan]\n"
    )

    try:
        # Get Supabase client and tenant info
        supabase = get_supabase_client()
        tenant = (
            supabase.table("rag.tenants")
            .select("*")
            .eq("name", tenant_name)
            .single()
            .execute()
        )

        if not tenant.data:
            console.print(f"[red]Tenant '{tenant_name}' not found in database[/red]")
            return False

        tenant_id = tenant.data["id"]

        # Initialize OAuth manager
        oauth_manager = GoogleOAuthManager()

        # Check if already authorized
        if oauth_manager.test_credentials(tenant_id):
            console.print("[green]✓ Tenant already has valid OAuth credentials[/green]")
            if not Confirm.ask("Do you want to reauthorize?"):
                return True

            # Revoke existing credentials
            console.print("[yellow]Revoking existing credentials...[/yellow]")
            oauth_manager.revoke_credentials(tenant_id)

        # Start callback server
        console.print("[yellow]Starting OAuth callback server...[/yellow]")
        server = start_callback_server()

        # Generate authorization URL
        auth_url = oauth_manager.get_authorization_url(tenant_id)

        console.print("\n[bold]Authorization Required[/bold]")
        console.print(f"Please visit the following URL to authorize access:\n")
        console.print(f"[link]{auth_url}[/link]\n")

        # Try to open in browser
        if Confirm.ask("Open URL in browser?", default=True):
            webbrowser.open(auth_url)

        # Wait for callback
        console.print("\n[yellow]Waiting for authorization...[/yellow]")
        console.print(
            "[dim]The browser will redirect to http://localhost:8080 after authorization[/dim]\n"
        )

        # Poll for auth code
        import time

        timeout = 300  # 5 minutes
        start_time = time.time()

        while server.auth_code is None and (time.time() - start_time) < timeout:
            time.sleep(1)

        # Shutdown server
        server.shutdown()

        if server.auth_code:
            console.print("[green]✓ Authorization code received[/green]")

            # Exchange code for tokens
            console.print("[yellow]Exchanging code for tokens...[/yellow]")
            tokens = oauth_manager.exchange_code_for_tokens(
                server.auth_code, tenant_id, server.state
            )

            console.print("[green]✓ Tokens obtained and stored securely[/green]")

            # Test credentials
            console.print("[yellow]Testing credentials...[/yellow]")
            if oauth_manager.test_credentials(tenant_id):
                console.print("[green]✓ Credentials verified successfully![/green]")

                # Update tenant record
                supabase.table("rag.tenants").update(
                    {"drive_authorized": True, "drive_auth_date": tokens.get("expiry")}
                ).eq("id", tenant_id).execute()

                return True
            else:
                console.print("[red]✗ Credential test failed[/red]")
                return False
        else:
            console.print("[red]✗ Authorization timeout - no code received[/red]")
            return False

    except Exception as e:
        console.print(f"[red]Error during OAuth setup: {e}[/red]")
        logger.error(f"OAuth setup failed: {e}", exc_info=True)
        return False


def list_tenant_auth_status():
    """List OAuth authorization status for all tenants."""
    console.print("\n[bold cyan]Tenant OAuth Status[/bold cyan]\n")

    try:
        supabase = get_supabase_client()
        oauth_manager = GoogleOAuthManager()

        # Get all tenants
        tenants = supabase.table("rag.tenants").select("*").execute()

        table = Table(title="Google OAuth Status")
        table.add_column("Tenant", style="cyan")
        table.add_column("Display Name", style="yellow")
        table.add_column("OAuth Status", style="green")
        table.add_column("Drive Folder", style="blue")

        for tenant in tenants.data:
            # Check OAuth status
            has_oauth = oauth_manager.test_credentials(tenant["id"])
            status = (
                "[green]✓ Authorized[/green]"
                if has_oauth
                else "[red]✗ Not Authorized[/red]"
            )

            table.add_row(
                tenant["name"],
                tenant["display_name"],
                status,
                tenant.get("drive_folder_id", "Not Set"),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing tenant status: {e}[/red]")


def setup_google_project_instructions():
    """Display instructions for setting up Google Cloud project."""
    instructions = """
[bold cyan]Google Cloud Project Setup Instructions[/bold cyan]

1. [bold]Create a Google Cloud Project[/bold]
   - Go to https://console.cloud.google.com
   - Create a new project or select existing
   - Note the project ID

2. [bold]Enable Google Drive API[/bold]
   - Go to APIs & Services > Library
   - Search for "Google Drive API"
   - Click Enable

3. [bold]Create OAuth 2.0 Credentials[/bold]
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URI: http://localhost:8080/oauth2callback
   - Download the credentials JSON

4. [bold]Set Environment Variables[/bold]
   ```bash
   export GOOGLE_CLIENT_ID="your-client-id"
   export GOOGLE_CLIENT_SECRET="your-client-secret"
   ```

5. [bold]Configure OAuth Consent Screen[/bold]
   - Go to APIs & Services > OAuth consent screen
   - Choose "External" user type
   - Fill in required fields
   - Add test users if in testing mode
   - Add scopes:
     - .../auth/drive.readonly
     - .../auth/drive.metadata.readonly

[yellow]Note: Keep your credentials secure and never commit them to git![/yellow]
"""

    console.print(Panel(instructions, border_style="cyan"))


def main():
    """Main entry point."""
    console.print(
        Panel.fit(
            "[bold cyan]Google OAuth Setup for RAG System[/bold cyan]\n\n"
            "Configure Google Drive access for document ingestion",
            border_style="cyan",
        )
    )

    # Check for Google credentials
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        console.print("\n[red]Google OAuth credentials not found![/red]")
        console.print(
            "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.\n"
        )

        if Confirm.ask("Show setup instructions?", default=True):
            setup_google_project_instructions()
        return 1

    # Menu options
    while True:
        console.print("\n[bold]Options:[/bold]")
        console.print("1. Set up OAuth for a tenant")
        console.print("2. List tenant authorization status")
        console.print("3. Show Google Cloud setup instructions")
        console.print("4. Exit")

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"])

        if choice == "1":
            # Get tenant name
            tenant_name = Prompt.ask("Enter tenant name (e.g., 'acme_corp')")
            if setup_tenant_oauth(tenant_name):
                console.print(
                    f"\n[green]✅ OAuth setup complete for {tenant_name}![/green]"
                )
            else:
                console.print(f"\n[red]❌ OAuth setup failed for {tenant_name}[/red]")

        elif choice == "2":
            list_tenant_auth_status()

        elif choice == "3":
            setup_google_project_instructions()

        elif choice == "4":
            break

    console.print("\n[green]Setup complete![/green]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
