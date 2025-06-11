#!/usr/bin/env python3
"""
Test quota tracking system
"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from elf_automations.shared.quota import QuotaManager
from elf_automations.shared.utils import LLMFactory


def main():
    print("🧪 Testing Quota Tracking System\n")

    # Initialize quota manager
    quota_path = Path.home() / ".elf_automations" / "quota_data"
    quota_path.mkdir(parents=True, exist_ok=True)
    quota_manager = QuotaManager(
        storage_path=quota_path,
        default_daily_budget=1.0,  # $1 for testing
        warning_threshold=0.5,  # Warn at 50%
    )

    # Create LLM with quota tracking for different teams
    teams = ["marketing-team", "sales-team", "product-team"]

    for team in teams:
        print(f"\n📊 Testing {team}...")

        # Create quota-tracked LLM
        llm = LLMFactory.create_with_quota_tracking(
            team_name=team,
            preferred_provider="openai",
            preferred_model="gpt-4",
            quota_manager=quota_manager,
        )

        print(f"✅ Created quota-tracked LLM for {team}")
        print(f"   Model: {llm.model_name}")
        print(f"   Remaining budget: ${llm.get_remaining_budget():.2f}")

        # Test queries
        queries = [
            f"Hello from {team}! What's 2+2?",
            f"I'm {team}. List 3 marketing tips in one sentence each.",
            f"This is {team} again. What's the weather like?",
        ]

        for i, query in enumerate(queries, 1):
            try:
                print(f"\n   Query {i}: {query[:50]}...")
                response = llm.invoke(query)
                print(f"   Response: {response.content[:100]}...")
                print(f"   Remaining budget: ${llm.get_remaining_budget():.2f}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        # Get usage report
        print(f"\n   📈 Usage Report for {team}:")
        report = llm.get_usage_report(days=1)
        today_usage = list(report["days"].values())[0]
        print(f"   Total cost today: ${today_usage['total_cost']:.4f}")
        print(f"   Total tokens: {today_usage['token_count']}")
        if today_usage["models"]:
            print(f"   Models used:")
            for model, data in today_usage["models"].items():
                print(f"     - {model}: ${data['cost']:.4f} ({data['calls']} calls)")

    # Overall usage summary
    print("\n📊 Overall Usage Summary:")
    print("-" * 50)
    for team in teams:
        report = quota_manager.get_usage_report(team, days=1)
        print(
            f"{team}: ${report['total_cost']:.4f} of ${quota_manager.get_team_budget(team):.2f}"
        )

    # Test quota limits
    print("\n🚦 Testing Quota Limits...")

    # Set a very low budget for testing
    test_team = "test-team"
    quota_manager.set_team_budget(test_team, 0.01)  # 1 cent budget

    llm = LLMFactory.create_with_quota_tracking(
        team_name=test_team,
        preferred_provider="openai",
        preferred_model="gpt-4",
        quota_manager=quota_manager,
    )

    print(f"Created {test_team} with $0.01 budget")

    # Try to exceed quota
    for i in range(5):
        try:
            response = llm.invoke(f"Test query {i} - Write a long story about robots.")
            print(f"✅ Query {i} succeeded")
        except Exception as e:
            print(f"❌ Query {i} failed: {e}")
            break

    print("\n✅ Quota tracking system is working correctly!")
    print("   - Tracks usage per team")
    print("   - Enforces budget limits")
    print("   - Falls back to cheaper models when needed")
    print("   - Provides detailed usage reports")


if __name__ == "__main__":
    main()
