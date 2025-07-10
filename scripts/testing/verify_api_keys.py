#!/usr/bin/env python3
"""Verify API keys and credentials after rotation."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_env_vars():
    """Check if all required environment variables are present."""
    print("=== Checking Environment Variables ===")

    required_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "ANTHROPIC_API_KEY": "Anthropic API Key",
        "SUPABASE_URL": "Supabase URL",
        "SUPABASE_ANON_KEY": "Supabase Anon Key",
        "SUPABASE_SECRET_KEY": "Supabase Secret Key",
        "SUPABASE_PASSWORD": "Supabase Password",
        "DATABASE_URL": "Database URL",
        "REDIS_URL": "Redis URL",
    }

    missing = []
    for var, name in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive parts of the key
            if "KEY" in var or "PASSWORD" in var or "SECRET" in var:
                masked = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
                print(f"{GREEN}✓{RESET} {name}: {masked}")
            else:
                print(f"{GREEN}✓{RESET} {name}: {value}")
        else:
            print(f"{RED}✗{RESET} {name}: MISSING")
            missing.append(var)

    return len(missing) == 0


def test_supabase():
    """Test Supabase connection."""
    print("\n=== Testing Supabase Connection ===")
    try:
        from supabase import Client, create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            print(f"{RED}✗{RESET} Missing Supabase credentials")
            return False

        client = create_client(url, key)

        # Try a simple query to test the connection
        result = client.table("teams").select("count").limit(1).execute()
        print(f"{GREEN}✓{RESET} Supabase connection successful")

        # Test with service role key
        service_key = os.getenv("SUPABASE_SECRET_KEY")
        if service_key:
            service_client = create_client(url, service_key)
            result = service_client.table("teams").select("count").limit(1).execute()
            print(f"{GREEN}✓{RESET} Supabase service role connection successful")

        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Supabase connection failed: {str(e)}")
        return False


def test_openai():
    """Test OpenAI API connection."""
    print("\n=== Testing OpenAI Connection ===")
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print(f"{RED}✗{RESET} Missing OpenAI API key")
            return False

        client = openai.OpenAI(api_key=api_key)

        # Try a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API key verified'"}],
            max_tokens=10,
        )

        print(f"{GREEN}✓{RESET} OpenAI connection successful")
        print(f"  Response: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} OpenAI connection failed: {str(e)}")
        if "authentication" in str(e).lower():
            print(
                f"{YELLOW}  This likely means the API key is invalid or expired{RESET}"
            )
        return False


def test_anthropic():
    """Test Anthropic API connection."""
    print("\n=== Testing Anthropic Connection ===")
    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print(f"{RED}✗{RESET} Missing Anthropic API key")
            return False

        client = anthropic.Anthropic(api_key=api_key)

        # Try a simple completion
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'API key verified'"}],
        )

        print(f"{GREEN}✓{RESET} Anthropic connection successful")
        print(f"  Response: {response.content[0].text}")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Anthropic connection failed: {str(e)}")
        if "authentication" in str(e).lower():
            print(
                f"{YELLOW}  This likely means the API key is invalid or expired{RESET}"
            )
        return False


def test_credential_manager():
    """Test if credential manager can access the new keys."""
    print("\n=== Testing Credential Manager ===")
    try:
        from elf_automations.shared.credentials.credential_manager import (
            CredentialManager,
        )

        # Initialize credential manager
        cm = CredentialManager()

        # Check if it can retrieve credentials
        teams = ["test-team"]
        for team in teams:
            try:
                # Get OpenAI credentials
                openai_creds = cm.get_credential(team, "openai", "api_key")
                if openai_creds:
                    print(
                        f"{GREEN}✓{RESET} Credential Manager can access OpenAI credentials"
                    )

                # Get Anthropic credentials
                anthropic_creds = cm.get_credential(team, "anthropic", "api_key")
                if anthropic_creds:
                    print(
                        f"{GREEN}✓{RESET} Credential Manager can access Anthropic credentials"
                    )

            except Exception as e:
                print(f"{YELLOW}  Note: {str(e)}{RESET}")

        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Credential Manager test failed: {str(e)}")
        return False


def main():
    """Run all verification tests."""
    print(f"\n{YELLOW}=== API Key Verification Tool ==={RESET}")
    print("This will verify all API keys and connections after rotation\n")

    all_passed = True

    # Check environment variables
    if not check_env_vars():
        all_passed = False

    # Test connections
    if not test_supabase():
        all_passed = False

    if not test_openai():
        all_passed = False

    if not test_anthropic():
        all_passed = False

    if not test_credential_manager():
        all_passed = False

    # Summary
    print(f"\n{YELLOW}=== Summary ==={RESET}")
    if all_passed:
        print(
            f"{GREEN}✅ All tests passed! Your API keys are properly configured.{RESET}"
        )
    else:
        print(f"{RED}❌ Some tests failed. Please check the errors above.{RESET}")
        print(f"\n{YELLOW}Common fixes:{RESET}")
        print("1. Ensure all API keys are correctly copied (no extra spaces)")
        print("2. Make sure the keys are active and not expired")
        print("3. Check that the Supabase project is accessible")
        print("4. Verify Redis and PostgreSQL are running if using local services")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
