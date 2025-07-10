#!/usr/bin/env python3
"""
Setup script for A2A Gateway

This script:
1. Creates the database schema in Supabase
2. Generates secure tokens
3. Creates Kubernetes secrets
4. Provides setup instructions
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()


def setup_database_schema(supabase: Client):
    """Create A2A Gateway tables in Supabase"""
    print("Setting up A2A Gateway database schema...")

    # Read the SQL schema
    schema_path = (
        Path(__file__).parent.parent
        / "a2a_gateway"
        / "sql"
        / "create_a2a_gateway_schema.sql"
    )

    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        return False

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # Execute the schema
    # Note: Supabase Python client doesn't support raw SQL execution
    # You'll need to run this through the Supabase SQL editor or psql
    print("\nPlease run the following SQL in your Supabase SQL editor:")
    print("-" * 60)
    print(schema_sql[:500] + "...\n")
    print("-" * 60)
    print(f"\nFull schema available at: {schema_path}")

    return True


def generate_registration_token():
    """Generate a secure registration token"""
    token = secrets.token_urlsafe(32)
    print(f"\nGenerated registration token: {token}")
    return token


def create_kubernetes_secrets(token: str, namespace: str = "elf-teams"):
    """Create Kubernetes secrets for the gateway"""
    print(f"\nCreating Kubernetes secrets in namespace '{namespace}'...")

    # Check if kubectl is available
    try:
        subprocess.run(
            ["kubectl", "version", "--client"], check=True, capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("kubectl not found. Skipping Kubernetes setup.")
        return False

    # Create namespace if it doesn't exist
    try:
        subprocess.run(
            ["kubectl", "create", "namespace", namespace],
            check=True,
            capture_output=True,
        )
        print(f"Created namespace: {namespace}")
    except subprocess.CalledProcessError:
        print(f"Namespace '{namespace}' already exists")

    # Create gateway secrets
    try:
        subprocess.run(
            [
                "kubectl",
                "create",
                "secret",
                "generic",
                "a2a-gateway-secrets",
                f"--from-literal=registration-token={token}",
                "-n",
                namespace,
                "--dry-run=client",
                "-o",
                "yaml",
            ],
            check=True,
        )

        # Actually create the secret
        subprocess.run(
            [
                "kubectl",
                "create",
                "secret",
                "generic",
                "a2a-gateway-secrets",
                f"--from-literal=registration-token={token}",
                "-n",
                namespace,
            ],
            check=True,
        )
        print("Created a2a-gateway-secrets")

    except subprocess.CalledProcessError as e:
        print(f"Failed to create secrets: {e}")
        return False

    # Check if Supabase secrets exist
    try:
        subprocess.run(
            ["kubectl", "get", "secret", "supabase-credentials", "-n", namespace],
            check=True,
            capture_output=True,
        )
        print("Supabase credentials secret already exists")
    except subprocess.CalledProcessError:
        print("\nWarning: supabase-credentials secret not found!")
        print("Create it with:")
        print(f"kubectl create secret generic supabase-credentials \\")
        print(f"  --from-literal=url=$SUPABASE_URL \\")
        print(f"  --from-literal=anon-key=$SUPABASE_ANON_KEY \\")
        print(f"  -n {namespace}")

    return True


def print_setup_instructions(token: str):
    """Print setup instructions for the user"""
    print("\n" + "=" * 60)
    print("A2A Gateway Setup Instructions")
    print("=" * 60)

    print("\n1. Database Setup:")
    print("   - Run the SQL schema in your Supabase SQL editor")
    print("   - Schema location: a2a_gateway/sql/create_a2a_gateway_schema.sql")

    print("\n2. Environment Variables:")
    print("   Add these to your .env file:")
    print(f"   A2A_GATEWAY_URL=http://a2a-gateway-service:8080")
    print(f"   GATEWAY_REGISTRATION_TOKEN={token}")

    print("\n3. Build and Deploy:")
    print("   # Build Docker image")
    print("   cd a2a_gateway")
    print("   docker build -t elf-automations/a2a-gateway:latest .")
    print("   ")
    print("   # Deploy to Kubernetes")
    print("   kubectl apply -f k8s/")

    print("\n4. Update Team Configurations:")
    print("   In each team's a2a_config.yaml, add:")
    print("   a2a:")
    print("     gateway_url: http://a2a-gateway-service:8080")
    print("     auto_register: true")

    print("\n5. Verify Deployment:")
    print("   kubectl port-forward -n elf-teams svc/a2a-gateway-service 8080:8080")
    print("   curl http://localhost:8080/health")

    print("\n6. Monitor Gateway:")
    print("   - Health: http://localhost:8080/health")
    print("   - Stats: http://localhost:8080/stats")
    print("   - Teams: http://localhost:8080/teams")

    print("\n" + "=" * 60)


def main():
    """Main setup function"""
    print("A2A Gateway Setup Script")
    print("========================\n")

    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if supabase_url and supabase_key:
        print("Found Supabase credentials")
        supabase = create_client(supabase_url, supabase_key)
        setup_database_schema(supabase)
    else:
        print("Warning: Supabase credentials not found in environment")
        print("Set SUPABASE_URL and SUPABASE_ANON_KEY to enable database setup")

    # Generate registration token
    token = generate_registration_token()

    # Create Kubernetes secrets
    create_kubernetes_secrets(token)

    # Print instructions
    print_setup_instructions(token)

    print("\nSetup complete! Follow the instructions above to deploy the A2A Gateway.")


if __name__ == "__main__":
    main()
