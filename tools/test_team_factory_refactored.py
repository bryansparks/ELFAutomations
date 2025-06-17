#!/usr/bin/env python3
"""
Test the refactored team factory end-to-end.
"""

import shutil
import sys
import tempfile
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from team_factory import TeamFactory
from team_factory.models import TeamMember, TeamSpecification


def test_crewai_team_creation():
    """Test creating a CrewAI team."""
    print("\n=== Testing CrewAI Team Creation ===")
    
    # Create team specification
    spec = TeamSpecification(
        name="test-marketing-team",
        description="A marketing team for testing",
        purpose="Create and execute marketing strategies",
        framework="CrewAI",
        llm_provider="OpenAI",
        llm_model="gpt-4",
        department="marketing",
        reporting_to="CMO",
        members=[
            TeamMember(
                name="Marketing Manager",
                role="Lead Marketing Strategist",
                responsibilities=[
                    "Develop marketing strategies",
                    "Coordinate team efforts",
                    "Report to CMO"
                ],
                skills=["strategy", "leadership", "communication"],
                personality="collaborator",
                is_manager=True,
            ),
            TeamMember(
                name="Content Creator",
                role="Content Marketing Specialist",
                responsibilities=[
                    "Create engaging content",
                    "Manage content calendar",
                    "Optimize for SEO"
                ],
                skills=["writing", "SEO", "creativity"],
                personality="innovator",
            ),
            TeamMember(
                name="Social Media Manager",
                role="Social Media Strategist",
                responsibilities=[
                    "Manage social channels",
                    "Engage with audience",
                    "Track metrics"
                ],
                skills=["social media", "analytics", "engagement"],
                personality="optimist",
            ),
        ]
    )
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            # Change to temp directory
            Path(tmpdir).chmod(0o755)
            import os
            os.chdir(tmpdir)
            
            # Create team factory
            factory = TeamFactory()
            
            # Create the team
            result = factory.create_team(spec)
            
            # Check results
            if result["success"]:
                print("✓ Team created successfully!")
                print(f"  - Generated {len(result['generated_files'])} files")
                print(f"  - Team path: {result['team_path']}")
                
                # Verify key files exist
                team_dir = Path(spec.name)
                key_files = [
                    "agents/marketing_manager.py",
                    "agents/content_creator.py", 
                    "agents/social_media_manager.py",
                    "crew.py",
                    "requirements.txt",
                    "Dockerfile",
                    "team_server.py",
                    "k8s/deployment.yaml",
                    "README.md",
                    "config/team_config.yaml",
                    "config/a2a_config.yaml",
                    "config/llm_config.yaml",
                ]
                
                missing_files = []
                for file_path in key_files:
                    if not (team_dir / file_path).exists():
                        missing_files.append(file_path)
                
                if missing_files:
                    print(f"✗ Missing files: {missing_files}")
                    return False
                else:
                    print("✓ All key files generated")
                
                # Check warnings
                if result.get("warnings"):
                    print("\nWarnings:")
                    for warning in result["warnings"]:
                        print(f"  ⚠ {warning}")
                
                return True
            else:
                print("✗ Team creation failed!")
                for error in result["errors"]:
                    print(f"  - {error}")
                return False
                
        finally:
            # Return to original directory
            os.chdir(original_cwd)


def test_langgraph_team_creation():
    """Test creating a LangGraph team."""
    print("\n=== Testing LangGraph Team Creation ===")
    
    # Create team specification
    spec = TeamSpecification(
        name="test-engineering-team",
        description="An engineering team for testing",
        purpose="Build and maintain software systems",
        framework="LangGraph",
        llm_provider="Anthropic",
        llm_model="claude-3-opus-20240229",
        department="engineering",
        reporting_to="CTO",
        members=[
            TeamMember(
                name="Tech Lead",
                role="Senior Engineering Lead",
                responsibilities=[
                    "Technical architecture",
                    "Code reviews",
                    "Team mentoring"
                ],
                skills=["architecture", "coding", "leadership"],
                personality="pragmatist",
                is_manager=True,
            ),
            TeamMember(
                name="Backend Engineer",
                role="Backend Developer",
                responsibilities=[
                    "API development",
                    "Database design",
                    "Performance optimization"
                ],
                skills=["python", "databases", "APIs"],
                personality="detail-oriented",
            ),
        ]
    )
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            # Change to temp directory
            Path(tmpdir).chmod(0o755)
            import os
            os.chdir(tmpdir)
            
            # Create team factory
            factory = TeamFactory()
            
            # Create the team
            result = factory.create_team(spec)
            
            # Check results
            if result["success"]:
                print("✓ Team created successfully!")
                print(f"  - Generated {len(result['generated_files'])} files")
                
                # Verify LangGraph-specific files
                team_dir = Path(spec.name)
                langgraph_files = [
                    "workflows/state_definitions.py",
                    "workflows/team_workflow.py",
                    "workflows/__init__.py",
                ]
                
                missing_files = []
                for file_path in langgraph_files:
                    if not (team_dir / file_path).exists():
                        missing_files.append(file_path)
                
                if missing_files:
                    print(f"✗ Missing LangGraph files: {missing_files}")
                    return False
                else:
                    print("✓ All LangGraph files generated")
                
                return True
            else:
                print("✗ Team creation failed!")
                for error in result["errors"]:
                    print(f"  - {error}")
                return False
                
        finally:
            # Return to original directory
            os.chdir(original_cwd)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Team Factory Refactoring End-to-End Test")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 2
    
    # Test CrewAI
    if test_crewai_team_creation():
        tests_passed += 1
    
    # Test LangGraph
    if test_langgraph_team_creation():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print("=" * 60)
    
    if tests_passed == tests_total:
        print("\n✓ All tests passed! Refactoring is successful.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())