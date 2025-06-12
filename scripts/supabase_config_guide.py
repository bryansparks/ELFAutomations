#!/usr/bin/env python3
"""
Supabase Configuration Guide

Helps users configure their Supabase environment variables correctly.
"""

import os
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def main():
    """Display Supabase configuration guide."""
    logger.info("🔧 Supabase Configuration Guide")
    logger.info("=" * 50)

    # Load current environment
    load_dotenv()

    # Check current configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase_access_token = os.getenv("SUPABASE_ACCESS_TOKEN")

    logger.info("Current Configuration Status:")
    logger.info(f"  SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    logger.info(f"  SUPABASE_ANON_KEY: {'✅ Set' if supabase_anon_key else '❌ Missing'}")
    logger.info(
        f"  SUPABASE_SERVICE_KEY: {'✅ Set' if supabase_service_key else '❌ Missing (Optional)'}"
    )
    logger.info(
        f"  SUPABASE_ACCESS_TOKEN: {'✅ Set' if supabase_access_token else '❌ Missing'}"
    )

    logger.info("\n📋 Required Environment Variables:")
    logger.info("=" * 40)

    logger.info("\n1. SUPABASE_URL")
    logger.info("   Description: Your Supabase project URL")
    logger.info("   Location: Supabase Dashboard → Project Settings → API")
    logger.info("   Format: https://your-project-ref.supabase.co")
    if supabase_url:
        logger.info(f"   Current: {supabase_url}")

    logger.info("\n2. SUPABASE_ANON_KEY")
    logger.info("   Description: Anonymous/public API key")
    logger.info("   Location: Supabase Dashboard → Project Settings → API")
    logger.info("   Format: eyJ... (long JWT token)")
    if supabase_anon_key:
        logger.info(f"   Current: {supabase_anon_key[:20]}...")

    logger.info("\n3. SUPABASE_SERVICE_KEY (Optional)")
    logger.info("   Description: Service role key for admin operations")
    logger.info("   Location: Supabase Dashboard → Project Settings → API")
    logger.info("   Format: eyJ... (long JWT token)")
    logger.info("   ⚠️  Keep this secret - has full database access")
    if supabase_service_key:
        logger.info(f"   Current: {supabase_service_key[:20]}...")

    logger.info("\n4. SUPABASE_ACCESS_TOKEN")
    logger.info("   Description: Personal access token for MCP server")
    logger.info("   Location: Supabase Dashboard → Account → Access Tokens")
    logger.info("   Format: sbp_... (personal access token)")
    logger.info("   Purpose: Allows MCP server to manage projects and schemas")
    if supabase_access_token:
        logger.info(f"   Current: {supabase_access_token[:20]}...")

    logger.info("\n5. SUPABASE_PROJECT_REF (Optional)")
    logger.info("   Description: Project reference ID for scoped access")
    logger.info("   Location: Supabase Dashboard → Project Settings → General")
    logger.info("   Format: abcdefghijklmnop (16-character string)")

    logger.info("\n🔗 How to Get These Values:")
    logger.info("=" * 30)
    logger.info("1. Go to https://supabase.com/dashboard")
    logger.info("2. Select your project")
    logger.info("3. Navigate to Settings → API")
    logger.info("4. Copy the URL and anon key")
    logger.info(
        "5. For access token: Account Settings → Access Tokens → Create New Token"
    )

    logger.info("\n📝 Example .env Configuration:")
    logger.info("=" * 30)
    logger.info("SUPABASE_URL=https://your-project-ref.supabase.co")
    logger.info("SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    logger.info("SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    logger.info("SUPABASE_ACCESS_TOKEN=sbp_1234567890abcdef...")
    logger.info("SUPABASE_PROJECT_REF=abcdefghijklmnop")

    # Check if we can proceed
    missing_required = []
    if not supabase_url:
        missing_required.append("SUPABASE_URL")
    if not supabase_anon_key:
        missing_required.append("SUPABASE_ANON_KEY")
    if not supabase_access_token:
        missing_required.append("SUPABASE_ACCESS_TOKEN")

    if missing_required:
        logger.info(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        logger.info(
            "Please add these to your .env file before running setup_supabase.py"
        )
        return 1
    else:
        logger.info("\n✅ All required variables are set!")
        logger.info("You can now run: python scripts/setup_supabase.py")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
