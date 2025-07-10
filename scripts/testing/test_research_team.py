#!/usr/bin/env python3
"""Test the Research team (free agent) creation"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.team_factory import TeamFactory


def test_research_team():
    """Test creating a free agent Research team"""

    factory = TeamFactory()

    print("Testing Research Team Creation (Free Agent Pattern)...")

    # Create research team
    team_spec = factory._generate_team_suggestion(
        "Create a free agent research team that can help any team with web research, academic paper analysis, and social media monitoring",
        framework="CrewAI",
        llm_provider="OpenAI",
        llm_model="gpt-4",
    )

    print(f"\nTeam: {team_spec.name}")
    print(f"Department: {team_spec.department}")
    print(f"Is Free Agent: {team_spec.is_free_agent}")
    print(f"Reports To: {team_spec.reports_to}")
    print(f"Team size: {len(team_spec.members)}")

    print("\nTeam members:")
    for member in team_spec.members:
        print(f"  - {member.role}")
        if member.manages_teams:
            print(f"    Manages: {', '.join(member.manages_teams)}")

    print(f"\nA2A Capabilities ({len(team_spec.a2a_capabilities)}):")
    for cap in team_spec.a2a_capabilities:
        print(f"  - {cap}")

    print(f"\nSub-team Recommendations ({len(team_spec.sub_team_recommendations)}):")
    for rec in team_spec.sub_team_recommendations:
        print(f"\n  {rec.name}:")
        print(f"    Purpose: {rec.purpose}")
        print(f"    Capabilities: {', '.join(rec.required_capabilities)}")
        print(f"    Rationale: {rec.rationale}")

    # Check team lead's prompt
    team_lead = next((m for m in team_spec.members if "Lead" in m.role), None)
    if team_lead:
        print(f"\nTeam Lead System Prompt Preview:")
        print(f"{team_lead.system_prompt[:300]}...")


if __name__ == "__main__":
    test_research_team()
