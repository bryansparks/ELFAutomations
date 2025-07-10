#!/usr/bin/env python3
"""Test the skeptic pattern implementation in team factory"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.team_factory import TeamFactory


def test_skeptic_pattern():
    """Test that the skeptic pattern is properly implemented"""

    factory = TeamFactory()

    # Test 1: Create a 5-member marketing team - should auto-add skeptic
    print("Test 1: Creating 5-member marketing team without mentioning skeptic...")
    team_spec = factory._generate_team_suggestion(
        "Create a marketing team focused on digital campaigns and social media growth",
        framework="CrewAI",
        llm_provider="OpenAI",
        llm_model="gpt-4",
    )

    print(f"Team size: {len(team_spec.members)}")
    print("\nTeam members:")
    for member in team_spec.members:
        print(f"  - {member.role}: {member.personality_traits}")

    # Check if skeptic was added
    has_skeptic = any(
        "skeptic" in member.personality_traits for member in team_spec.members
    )
    print(f"\nHas skeptic: {has_skeptic}")

    # Check analytics expert specifically
    analytics_expert = next(
        (m for m in team_spec.members if "Analytics" in m.role), None
    )
    if analytics_expert:
        print(f"\nAnalytics Expert traits: {analytics_expert.personality_traits}")
        print(
            f"Analytics Expert prompt preview: {analytics_expert.system_prompt[:200]}..."
        )

    # Test 2: Create a small team - should not auto-add skeptic
    print("\n\nTest 2: Creating 3-member team...")
    small_team = factory._generate_team_suggestion(
        "Create a small development team",
        framework="CrewAI",
        llm_provider="OpenAI",
        llm_model="gpt-4",
    )

    print(f"Small team size: {len(small_team.members)}")
    print("Small team members:")
    for member in small_team.members:
        print(f"  - {member.role}: {member.personality_traits}")


if __name__ == "__main__":
    test_skeptic_pattern()
