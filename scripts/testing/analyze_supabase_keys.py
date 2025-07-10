#!/usr/bin/env python3
"""Analyze Supabase JWT tokens to debug authentication issues."""

import base64
import json
import os

from dotenv import load_dotenv

load_dotenv()


def decode_jwt_payload(token):
    """Decode JWT token payload without verification."""
    try:
        # JWT has 3 parts separated by dots
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode the payload (second part)
        # Add padding if needed
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding

        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None


def main():
    anon = os.getenv("SUPABASE_ANON_KEY", "")
    secret = os.getenv("SUPABASE_SECRET_KEY", "")

    print("=== Analyzing Supabase Keys ===")
    print()

    print("ANON KEY:")
    anon_data = decode_jwt_payload(anon)
    if anon_data:
        print(f'  Role: {anon_data.get("role", "unknown")}')
        print(f'  Ref: {anon_data.get("ref", "unknown")}')
        print(f'  Issued: {anon_data.get("iat", "unknown")}')
        print(f'  Expires: {anon_data.get("exp", "unknown")}')
    else:
        print("  Failed to decode anon key")

    print()
    print("SECRET KEY:")
    secret_data = decode_jwt_payload(secret)
    if secret_data:
        print(f'  Role: {secret_data.get("role", "unknown")}')
        print(f'  Ref: {secret_data.get("ref", "unknown")}')
        print(f'  Issued: {secret_data.get("iat", "unknown")}')
        print(f'  Expires: {secret_data.get("exp", "unknown")}')
    else:
        print("  Failed to decode secret key")

    # Check if they have same ref (project ID)
    if anon_data and secret_data:
        print()
        if anon_data.get("ref") != secret_data.get("ref"):
            print("⚠️  WARNING: Keys are from different projects!")
            print(f'   Anon key project: {anon_data.get("ref")}')
            print(f'   Secret key project: {secret_data.get("ref")}')
        else:
            print("✓ Both keys are from the same project")

        # Check roles
        if secret_data.get("role") != "service_role":
            print("⚠️  WARNING: Secret key does not have service_role!")
            print(f'   Current role: {secret_data.get("role")}')
            print("   This might be why authentication is failing")


if __name__ == "__main__":
    main()
