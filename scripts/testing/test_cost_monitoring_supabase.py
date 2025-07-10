#!/usr/bin/env python3
"""
Test script to verify Supabase cost monitoring integration

Tests that QuotaTrackedLLM correctly records usage to Supabase.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import after adding to path
from elf_automations.shared.utils import LLMFactory
from supabase import create_client


def test_cost_monitoring():
    """Test that cost monitoring records to Supabase"""

    # Check environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set")
        print("Please run: source scripts/setup_supabase.py")
        return False

    # Create Supabase client
    try:
        supabase = create_client(url, key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

    # Check if tables exist
    try:
        result = supabase.table("api_usage").select("*").limit(1).execute()
        print("✅ Cost monitoring tables exist")
    except Exception as e:
        print(f"❌ Cost monitoring tables not found: {e}")
        print(
            "Please run the SQL schema from /sql/create_cost_monitoring_tables.sql in Supabase"
        )
        return False

    # Create quota-tracked LLM with Supabase
    try:
        llm = LLMFactory.create_with_quota_tracking(
            team_name="test-team",
            preferred_provider="openai",
            preferred_model="gpt-3.5-turbo",
            temperature=0.5,
            supabase_client=supabase,
        )
        print("✅ Created quota-tracked LLM with Supabase integration")
    except Exception as e:
        print(f"❌ Failed to create LLM: {e}")
        return False

    # Make a test request
    try:
        print("\n🔄 Making test LLM request...")
        response = llm.invoke("Say 'Hello, cost monitoring!' in exactly 5 words.")
        print(f"📝 Response: {response.content}")
        print("✅ LLM request successful")
    except Exception as e:
        print(f"❌ LLM request failed: {e}")
        return False

    # Check if usage was recorded in Supabase
    try:
        import time

        time.sleep(1)  # Give it a moment to record

        # Query recent usage
        result = (
            supabase.table("api_usage")
            .select("*")
            .eq("team_name", "test-team")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if result.data and len(result.data) > 0:
            usage = result.data[0]
            print(f"\n✅ Usage recorded in Supabase:")
            print(f"   - Team: {usage['team_name']}")
            print(f"   - Model: {usage['model']}")
            print(
                f"   - Tokens: {usage['input_tokens']} in, {usage['output_tokens']} out"
            )
            print(f"   - Cost: ${usage['cost']:.4f}")
            return True
        else:
            print("❌ No usage record found in Supabase")
            print("Note: This might be due to API key issues or quota limits")
            return False

    except Exception as e:
        print(f"❌ Failed to query usage from Supabase: {e}")
        return False


def check_daily_summary():
    """Check if daily summaries are being updated"""
    try:
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Check daily summary
        result = (
            supabase.table("daily_cost_summary")
            .select("*")
            .eq("team_name", "test-team")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            summary = result.data[0]
            print(f"\n📊 Daily Summary for {summary['date']}:")
            print(f"   - Total Requests: {summary['total_requests']}")
            print(f"   - Total Tokens: {summary['total_tokens']}")
            print(f"   - Total Cost: ${summary['total_cost']:.4f}")
        else:
            print("\n📊 No daily summary found (will be created on first usage)")

    except Exception as e:
        print(f"\n⚠️  Could not check daily summary: {e}")


if __name__ == "__main__":
    print("🧪 Testing Supabase Cost Monitoring Integration")
    print("=" * 50)

    success = test_cost_monitoring()

    if success:
        check_daily_summary()
        print("\n✅ All tests passed! Cost monitoring is working correctly.")
        print("\n📈 You can view the data in:")
        print("   - Local dashboard: python scripts/cost_analytics.py")
        print(
            "   - Supabase dashboard: Check the api_usage and daily_cost_summary tables"
        )
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        print("\n💡 Common issues:")
        print(
            "   1. Supabase credentials not set - run: source scripts/setup_supabase.py"
        )
        print(
            "   2. Tables not created - run SQL from /sql/create_cost_monitoring_tables.sql"
        )
        print("   3. OpenAI API key not set or quota exceeded")
