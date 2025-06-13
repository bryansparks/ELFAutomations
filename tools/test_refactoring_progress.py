#!/usr/bin/env python3
"""
Test the refactored team factory components.
"""

import tempfile
from pathlib import Path

from team_factory.generators.agents import CrewAIAgentGenerator
from team_factory.models import TeamMember, TeamSpecification
from team_factory.ui.console import console, display_team_structure
from team_factory.ui.prompts import display_team_summary


def test_models():
    """Test model creation."""
    print("\n=== Testing Models ===")

    # Create team members
    manager = TeamMember(
        name="Marketing Manager",
        role="Lead Marketing Strategist",
        responsibilities=["Develop strategy", "Lead team", "Report to CMO"],
        personality="collaborator",
        is_manager=True,
    )

    specialist = TeamMember(
        name="Content Specialist",
        role="Content Creator",
        responsibilities=["Create content", "Manage calendar"],
        personality="innovator",
    )

    skeptic = TeamMember(
        name="Quality Analyst",
        role="Marketing QA",
        responsibilities=["Review campaigns", "Ensure quality"],
        personality="skeptic",
    )

    # Create team spec
    team_spec = TeamSpecification(
        name="marketing-team",
        description="Marketing team for product launches",
        purpose="Drive product awareness and adoption",
        framework="CrewAI",
        llm_provider="OpenAI",
        llm_model="gpt-4",
        department="marketing",
        reporting_to="CMO",
        members=[manager, specialist, skeptic],
    )

    # Validate
    assert team_spec.manager == manager
    assert team_spec.has_skeptic
    assert len(team_spec.members) == 3

    print("✓ Models working correctly")
    return team_spec


def test_ui_components(team_spec):
    """Test UI components."""
    print("\n=== Testing UI Components ===")

    # Test console display
    display_team_structure(team_spec)

    # Test summary display
    display_team_summary(team_spec)

    print("✓ UI components working")


def test_generator(team_spec):
    """Test agent generation."""
    print("\n=== Testing Agent Generator ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        generator = CrewAIAgentGenerator(output_dir=Path(tmpdir))

        # Generate agents
        results = generator.generate(team_spec)

        print(f"Generated files: {results['generated_files']}")
        print(f"Errors: {results['errors']}")

        # Check generated files
        team_dir = Path(tmpdir) / team_spec.directory_name
        assert (team_dir / "agents" / "__init__.py").exists()
        assert (team_dir / "agents" / "marketing_manager.py").exists()
        assert (team_dir / "agents" / "content_specialist.py").exists()
        assert (team_dir / "agents" / "quality_analyst.py").exists()

        # Read and validate content
        manager_content = (team_dir / "agents" / "marketing_manager.py").read_text()
        assert "Lead Marketing Strategist" in manager_content
        assert "allow_delegation=True" in manager_content
        assert "MemoryAwareCrewAIAgent" in manager_content

        skeptic_content = (team_dir / "agents" / "quality_analyst.py").read_text()
        assert "skeptical mindset" in skeptic_content

        print("✓ Agent generation working")


def test_integration():
    """Test integration of components."""
    print("\n=== Testing Integration ===")

    # Test that we can import from wrapper
    import team_factory

    assert hasattr(team_factory, "TeamMember")
    assert hasattr(team_factory, "TeamSpecification")

    # Create via wrapper
    member = team_factory.TeamMember(
        name="Test Agent", role="Tester", responsibilities=["Test"]
    )

    assert member.name == "Test Agent"

    print("✓ Integration working")


def main():
    """Run all tests."""
    console.print("[bold cyan]Team Factory Refactoring Test[/bold cyan]\n")

    try:
        # Test components
        team_spec = test_models()
        test_ui_components(team_spec)
        test_generator(team_spec)
        test_integration()

        console.print("\n[bold green]✓ All tests passed![/bold green]")
        console.print("\nRefactoring is progressing well:")
        console.print("- Models: ✓ Complete")
        console.print("- UI Components: ✓ Complete")
        console.print("- Agent Generation: ✓ Working")
        console.print("- Backward Compatibility: ✓ Maintained")

        console.print("\n[yellow]Still to migrate:[/yellow]")
        console.print("- LangGraph agent generator")
        console.print("- Crew/workflow generators")
        console.print("- Infrastructure generators")
        console.print("- Integration modules")
        console.print("- Core factory logic")

    except Exception as e:
        console.print(f"\n[bold red]✗ Test failed: {e}[/bold red]")
        raise


if __name__ == "__main__":
    main()
