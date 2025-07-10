#!/usr/bin/env python3
"""
Test script to create a team with memory and learning capabilities

This script demonstrates:
- Creating a new team using the enhanced team factory
- Memory system initialization
- Learning from task execution
- Performance improvement over time
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from elf_automations.shared.memory import LearningSystem, TeamMemory

from tools.team_factory import TeamFactory


async def main():
    """Create and test a memory-enabled team"""

    print("🚀 Creating a Research Team with Memory Capabilities")
    print("=" * 60)

    # Initialize team factory
    factory = TeamFactory()

    # Team description
    team_description = """
    Create a research team focused on analyzing technology trends and providing insights.
    The team should have:
    - A lead researcher who coordinates the team
    - A data analyst who processes information
    - A trend analyst who identifies patterns
    - A technical writer who documents findings

    This team should be able to learn from past research projects and improve their
    analysis methods over time.
    """

    print("📝 Team Description:")
    print(team_description)
    print("\n" + "=" * 60 + "\n")

    # Process the team description
    print("🔄 Processing team specification...")
    team_spec = factory.process_team_description(
        team_description,
        framework="langgraph",  # Use LangGraph for state-based workflows
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        department="research",
    )

    print(f"\n✅ Team Specification Created:")
    print(f"   - Name: {team_spec.name}")
    print(f"   - Framework: {team_spec.framework}")
    print(f"   - Department: {team_spec.department}")
    print(f"   - Members: {len(team_spec.members)}")

    for i, member in enumerate(team_spec.members, 1):
        print(f"\n   {i}. {member.role}")
        print(f"      - Responsibilities: {', '.join(member.responsibilities[:2])}")
        print(f"      - Skills: {', '.join(member.skills[:3])}")

    # Get user confirmation
    print("\n" + "=" * 60)
    response = input("\n📋 Create this team? (y/n): ")

    if response.lower() != "y":
        print("❌ Team creation cancelled")
        return

    # Generate the team
    print("\n🏗️ Generating team structure...")
    team_dir = factory.generate_team(team_spec)
    print(f"✅ Team generated at: {team_dir}")

    # Test memory system
    print("\n" + "=" * 60)
    print("\n🧠 Testing Memory System")
    print("=" * 60)

    # Initialize memory for testing
    team_memory = TeamMemory(team_spec.name)
    learning_system = LearningSystem(team_memory)

    # Simulate some task executions
    print("\n📊 Simulating task executions...")

    tasks = [
        {
            "description": "Analyze AI trends in healthcare for Q1 2025",
            "success": True,
            "duration": 120,
            "agent_contributions": {
                "Lead Researcher": ["Coordinated research", "Defined scope"],
                "Data Analyst": [
                    "Collected data from 50 sources",
                    "Created visualizations",
                ],
                "Trend Analyst": ["Identified 5 key trends", "Predicted growth areas"],
                "Technical Writer": ["Wrote executive summary", "Created presentation"],
            },
        },
        {
            "description": "Research blockchain adoption in finance",
            "success": True,
            "duration": 150,
            "agent_contributions": {
                "Lead Researcher": ["Set research parameters", "Interviewed experts"],
                "Data Analyst": ["Analyzed transaction volumes", "Market analysis"],
                "Trend Analyst": ["Identified adoption patterns", "Risk assessment"],
                "Technical Writer": [
                    "Compiled research report",
                    "Created infographics",
                ],
            },
        },
        {
            "description": "Investigate quantum computing applications",
            "success": False,
            "duration": 200,
            "error": {
                "type": "DataInsufficient",
                "message": "Not enough public data available",
            },
            "agent_contributions": {
                "Lead Researcher": ["Attempted expert outreach"],
                "Data Analyst": ["Limited data collection"],
                "Trend Analyst": ["Preliminary analysis only"],
                "Technical Writer": ["Draft report incomplete"],
            },
        },
    ]

    # Store episodes
    for i, task in enumerate(tasks, 1):
        print(f"\n   Task {i}: {task['description']}")

        # Generate mock embedding
        embedding = [0.1] * 1536  # Mock embedding

        episode_id = team_memory.store_episode(task, embedding)
        print(f"   ✅ Stored as episode: {episode_id}")

        # Learn from episode
        learnings = learning_system.learn_from_episode(task)
        print(f"   📚 Extracted {len(learnings)} learnings")

        time.sleep(0.5)  # Small delay for realism

    # Test pattern recognition
    print("\n🔍 Analyzing Success Patterns")
    patterns = team_memory.get_successful_patterns(days_back=1)

    for pattern in patterns[:3]:
        print(f"\n   Agent: {pattern['agent']}")
        print(f"   Success count: {pattern['total_successes']}")
        if pattern["top_actions"]:
            print(f"   Top action: {pattern['top_actions'][0]['action']}")

    # Test strategy synthesis
    print("\n📋 Synthesizing Research Strategy")
    strategy = learning_system.synthesize_strategy("research")

    if strategy:
        print(f"\n   Confidence: {strategy['confidence']:.2f}")
        print(f"   Recommended agents: {', '.join(strategy['recommended_agents'][:2])}")
        print(f"   Key actions: {', '.join(strategy['key_actions'][:3])}")

    # Get performance metrics
    print("\n📈 Performance Metrics")
    metrics = team_memory.get_performance_metrics(days_back=1)

    print(f"   Total episodes: {metrics.get('total_episodes', 0)}")
    print(f"   Success rate: {metrics.get('success_rate', 0):.2%}")
    print(f"   Average duration: {metrics.get('average_duration_seconds', 0):.0f}s")

    # Test improvement recommendations
    print("\n💡 Improvement Recommendations")
    recommendations = learning_system.recommend_improvements()

    for rec in recommendations[:2]:
        print(f"\n   Type: {rec['type']}")
        print(f"   Priority: {rec['priority']}")
        print(f"   Recommendation: {rec['recommendation']}")

    print("\n" + "=" * 60)
    print("\n✨ Summary")
    print("=" * 60)
    print(f"\n✅ Team '{team_spec.name}' created with:")
    print("   - Memory system for experience storage")
    print("   - Learning system for pattern recognition")
    print("   - Continuous improvement loop (24h cycles)")
    print("   - Performance tracking and analytics")

    print("\n📁 Team location:", team_dir)
    print("\n🎯 Next steps:")
    print("   1. Build the team: cd", team_dir, "&& python make-deployable-team.py")
    print("   2. Deploy to K8s using GitOps pipeline")
    print("   3. Monitor performance and learning progress")

    print("\n🧠 Memory Features Enabled:")
    print("   - Agents recall past experiences for similar tasks")
    print("   - Success patterns are identified and reinforced")
    print("   - Failed approaches are avoided in future")
    print("   - Team performance improves over time")
    print("   - Knowledge is preserved across restarts")


if __name__ == "__main__":
    asyncio.run(main())
