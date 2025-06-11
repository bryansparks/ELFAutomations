#!/usr/bin/env python3
"""
Test script for personality traits in team factory
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.team_factory import TeamFactory, TeamMember, TeamSpecification


def test_personality_traits():
    """Test the personality trait functionality"""
    factory = TeamFactory()

    # Test trait extraction
    print("Testing personality trait extraction...")

    test_descriptions = [
        "I need a marketing team with a skeptical analytics expert who challenges assumptions",
        "Create a development team with detail-oriented engineers and an optimistic team lead",
        "Build an executive team where the CFO is pragmatic and the CEO is visionary",
        "I want innovators and creative thinkers in my design team",
    ]

    for desc in test_descriptions:
        print(f"\nDescription: {desc}")
        print("Extracted traits:")

        # Test for different roles
        roles = ["Analytics Expert", "Team Lead", "Engineer", "CEO", "CFO", "Designer"]
        for role in roles:
            traits = factory._extract_personality_traits(desc, role)
            if traits:
                print(f"  {role}: {traits}")

    # Test trait application to prompts
    print("\n\nTesting personality trait application to prompts...")

    test_member = TeamMember(
        role="Analytics Expert",
        responsibilities=["Analyze data", "Generate insights"],
        skills=["Data analysis", "Statistics"],
        system_prompt="You are an Analytics Expert who measures performance.",
        personality_traits=["skeptic", "detail-oriented"],
    )

    # Test basic prompt enhancement
    enhanced_prompt = factory._apply_personality_traits(
        test_member.system_prompt, test_member.personality_traits
    )

    print(f"\nOriginal prompt: {test_member.system_prompt}")
    print(f"\nEnhanced prompt:\n{enhanced_prompt}")

    # Show available traits
    print("\n\nAvailable personality traits:")
    for trait, info in factory.PERSONALITY_TRAITS.items():
        print(f"\n{trait.upper()}: {info['description']}")
        print("Prompt modifiers:")
        for modifier in info["prompt_modifiers"][:2]:  # Show first 2 modifiers
            print(f"  - {modifier}")


if __name__ == "__main__":
    test_personality_traits()
