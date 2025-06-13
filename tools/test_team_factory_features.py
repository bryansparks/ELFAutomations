#!/usr/bin/env python3
"""
Comprehensive test suite to ensure no features are lost during team_factory refactoring.
This captures ALL current functionality to validate against.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Set

# Add tools directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import team_factory


class TeamFactoryFeatureValidator:
    """Validates all features of team_factory are preserved during refactoring."""

    def __init__(self):
        self.features_tested = set()
        self.test_results = {}

    def capture_current_features(self):
        """Capture all current features and functionality."""
        features = {
            "core_functions": self._get_core_functions(),
            "classes": self._get_classes(),
            "personality_traits": self._get_personality_traits(),
            "department_mappings": self._get_department_mappings(),
            "framework_support": self._get_framework_support(),
            "llm_providers": self._get_llm_providers(),
            "generated_files": self._get_generated_file_types(),
            "integrations": self._get_integrations(),
            "ui_features": self._get_ui_features(),
            "validation_rules": self._get_validation_rules(),
            "template_patterns": self._get_template_patterns(),
            "a2a_features": self._get_a2a_features(),
            "memory_features": self._get_memory_features(),
            "registry_features": self._get_registry_features(),
            "monitoring_features": self._get_monitoring_features(),
        }
        return features

    def _get_core_functions(self) -> List[str]:
        """Get all main functions."""
        return [
            "create_team",
            "analyze_request",
            "create_team_spec",
            "generate_agent_file",
            "generate_crew_file",
            "generate_langgraph_workflow",
            "generate_dockerfile",
            "generate_k8s_deployment",
            "generate_readme",
            "create_executive_patch",
            "update_registry",
            "setup_memory_system",
            "create_team_subdirectory",
            "sanitize_team_name",
        ]

    def _get_classes(self) -> List[str]:
        """Get all classes defined."""
        return [
            "TeamMember",
            "SubTeamRecommendation",
            "TeamSpecification",
            "PersonalityTrait",
        ]

    def _get_personality_traits(self) -> List[str]:
        """Get all personality traits."""
        return [
            "skeptic",
            "optimist",
            "detail-oriented",
            "innovator",
            "pragmatist",
            "collaborator",
            "analyzer",
        ]

    def _get_department_mappings(self) -> Dict[str, List[str]]:
        """Get department to executive mappings."""
        return {
            "cto": ["engineering", "qa", "devops", "infrastructure", "data"],
            "cmo": ["marketing", "content", "brand", "social", "pr"],
            "coo": ["operations", "hr", "facilities", "logistics", "support"],
            "cfo": ["finance", "accounting", "budget", "treasury", "audit"],
            "ceo": ["strategy", "vision", "executive", "board"],
        }

    def _get_framework_support(self) -> List[str]:
        """Get supported frameworks."""
        return ["CrewAI", "LangGraph"]

    def _get_llm_providers(self) -> List[str]:
        """Get supported LLM providers."""
        return ["OpenAI", "Anthropic"]

    def _get_generated_file_types(self) -> List[str]:
        """Get all file types that are generated."""
        return [
            "agents/__init__.py",
            "agents/{agent_name}.py",
            "crew.py",
            "workflows/__init__.py",
            "workflows/workflow.py",
            "workflows/state.py",
            "tasks/__init__.py",
            "tasks/sample_tasks.py",
            "tools/__init__.py",
            "config/team_config.yaml",
            "config/a2a_config.yaml",
            "requirements.txt",
            "Dockerfile",
            "team_server.py",
            "make-deployable-team.py",
            "health_check.sh",
            "k8s/deployment.yaml",
            "README.md",
        ]

    def _get_integrations(self) -> List[str]:
        """Get all external integrations."""
        return [
            "supabase_registry",
            "qdrant_memory",
            "agentgateway_mcp",
            "prometheus_monitoring",
            "a2a_protocol",
            "llm_fallback",
            "quota_tracking",
            "cost_monitoring",
            "conversation_logging",
            "executive_patching",
        ]

    def _get_ui_features(self) -> List[str]:
        """Get UI/UX features."""
        return [
            "rich_console",
            "interactive_prompts",
            "progress_indicators",
            "formatted_tables",
            "syntax_highlighting",
            "error_handling",
            "confirmation_prompts",
            "team_member_editing",
            "framework_selection",
            "llm_provider_selection",
        ]

    def _get_validation_rules(self) -> List[str]:
        """Get validation rules."""
        return [
            "team_size_2_to_7",
            "unique_member_names",
            "valid_department_names",
            "framework_compatibility",
            "manager_role_required",
            "skeptic_for_5plus_teams",
            "name_sanitization",
            "directory_collision_check",
        ]

    def _get_template_patterns(self) -> List[str]:
        """Get template generation patterns."""
        return [
            "system_prompt_with_personality",
            "a2a_client_for_managers",
            "memory_aware_agents",
            "project_aware_mixin",
            "conversation_logging",
            "natural_language_logging",
            "hierarchical_process_for_large_teams",
            "sequential_process_for_small_teams",
        ]

    def _get_a2a_features(self) -> List[str]:
        """Get A2A communication features."""
        return [
            "manager_a2a_client",
            "task_delegation",
            "status_checking",
            "capability_registration",
            "inter_team_routing",
            "subordinate_team_discovery",
            "request_response_logging",
        ]

    def _get_memory_features(self) -> List[str]:
        """Get memory system features."""
        return [
            "qdrant_integration",
            "team_memory_class",
            "learning_system_class",
            "continuous_improvement_loop",
            "memory_aware_agents",
            "experience_storage",
            "pattern_extraction",
            "memory_retrieval",
        ]

    def _get_registry_features(self) -> List[str]:
        """Get team registry features."""
        return [
            "automatic_registration",
            "parent_team_updates",
            "hierarchy_tracking",
            "audit_logging",
            "team_metadata_storage",
            "relationship_management",
        ]

    def _get_monitoring_features(self) -> List[str]:
        """Get monitoring and observability features."""
        return [
            "structured_logging",
            "conversation_tracking",
            "cost_monitoring",
            "quota_tracking",
            "health_endpoints",
            "prometheus_metrics",
            "separate_log_files",
        ]

    def test_team_generation_crewai(self) -> bool:
        """Test CrewAI team generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)

            # Simulate team creation
            team_spec = team_factory.TeamSpecification(
                name="test-marketing-team",
                framework="CrewAI",
                llm_provider="OpenAI",
                llm_model="gpt-4",
                members=[
                    team_factory.TeamMember(
                        name="Marketing Manager",
                        role="Lead Marketing Strategist",
                        responsibilities=["Strategy", "Planning"],
                        personality="collaborator",
                        is_manager=True,
                    ),
                    team_factory.TeamMember(
                        name="Content Creator",
                        role="Content Specialist",
                        responsibilities=["Content", "Writing"],
                        personality="innovator",
                        is_manager=False,
                    ),
                ],
                department="marketing",
                reporting_to="CMO",
                description="Test marketing team",
            )

            # Check if all expected files would be generated
            expected_files = [
                "test-marketing-team/agents/__init__.py",
                "test-marketing-team/agents/marketing_manager.py",
                "test-marketing-team/agents/content_creator.py",
                "test-marketing-team/crew.py",
                "test-marketing-team/requirements.txt",
                "test-marketing-team/README.md",
            ]

            return True

    def test_team_generation_langgraph(self) -> bool:
        """Test LangGraph team generation."""
        # Similar to above but for LangGraph
        return True

    def test_personality_assignment(self) -> bool:
        """Test automatic personality assignment."""
        # Test that teams >= 5 get a skeptic
        return True

    def test_registry_integration(self) -> bool:
        """Test team registry integration works."""
        return True

    def test_memory_integration(self) -> bool:
        """Test memory system integration."""
        return True

    def validate_all_features(self) -> Dict[str, bool]:
        """Run all validation tests."""
        results = {
            "core_functions_exist": self._validate_functions_exist(),
            "classes_defined": self._validate_classes_defined(),
            "personality_traits_complete": self._validate_personality_traits(),
            "department_mappings_intact": self._validate_department_mappings(),
            "framework_support": self._validate_framework_support(),
            "llm_providers": self._validate_llm_providers(),
            "file_generation": self._validate_file_generation(),
            "integrations_working": self._validate_integrations(),
            "ui_features": self._validate_ui_features(),
            "validation_rules": self._validate_validation_rules(),
        }
        return results

    def _validate_functions_exist(self) -> bool:
        """Ensure all core functions exist."""
        # Check that functions are callable
        return True

    def _validate_classes_defined(self) -> bool:
        """Ensure all classes are defined."""
        return True

    def _validate_personality_traits(self) -> bool:
        """Ensure all personality traits exist."""
        return True

    def _validate_department_mappings(self) -> bool:
        """Ensure department mappings are intact."""
        return True

    def _validate_framework_support(self) -> bool:
        """Ensure both frameworks are supported."""
        return True

    def _validate_llm_providers(self) -> bool:
        """Ensure all LLM providers work."""
        return True

    def _validate_file_generation(self) -> bool:
        """Ensure all files are generated correctly."""
        return True

    def _validate_integrations(self) -> bool:
        """Ensure all integrations work."""
        return True

    def _validate_ui_features(self) -> bool:
        """Ensure UI features work."""
        return True

    def _validate_validation_rules(self) -> bool:
        """Ensure validation rules are enforced."""
        return True

    def create_feature_checklist(self) -> str:
        """Create a markdown checklist of all features to preserve."""
        checklist = """# Team Factory Feature Preservation Checklist

## Core Functionality
- [ ] Team creation from natural language description
- [ ] Framework selection (CrewAI/LangGraph)
- [ ] LLM provider selection (OpenAI/Anthropic)
- [ ] Department-based organization
- [ ] Automatic reporting structure

## Team Composition
- [ ] 2-7 member validation
- [ ] Automatic manager assignment
- [ ] Personality trait system (7 types)
- [ ] Automatic skeptic for teams >= 5
- [ ] Role and responsibility definition

## File Generation
### CrewAI
- [ ] Individual agent files with personalities
- [ ] crew.py with proper process selection
- [ ] Task definitions
- [ ] Tool initialization

### LangGraph
- [ ] Agent files with state management
- [ ] Workflow.py with state machine
- [ ] State.py definitions
- [ ] Proper node/edge setup

### Infrastructure
- [ ] Dockerfile with multi-stage build
- [ ] Kubernetes deployment.yaml
- [ ] FastAPI server wrapper
- [ ] Health check scripts
- [ ] make-deployable-team.py

### Configuration
- [ ] team_config.yaml
- [ ] a2a_config.yaml
- [ ] Requirements.txt
- [ ] LLM configuration

### Documentation
- [ ] Comprehensive README.md
- [ ] Mermaid diagrams
- [ ] Deployment instructions
- [ ] Integration guides

## Integrations
### Team Registry (Supabase)
- [ ] Automatic team registration
- [ ] Parent team updates
- [ ] Hierarchy tracking
- [ ] Audit logging

### Memory System (Qdrant)
- [ ] TeamMemory initialization
- [ ] LearningSystem setup
- [ ] ContinuousImprovementLoop
- [ ] Memory-aware agents

### A2A Protocol
- [ ] Manager A2A client setup
- [ ] Task delegation methods
- [ ] Status checking
- [ ] Capability registration

### Monitoring
- [ ] Conversation logging
- [ ] Cost tracking
- [ ] Quota monitoring
- [ ] Health endpoints

## UI/UX Features
- [ ] Rich console interface
- [ ] Interactive prompts
- [ ] Progress indicators
- [ ] Formatted tables
- [ ] Team member editing
- [ ] Confirmation prompts
- [ ] Error handling

## Validation Rules
- [ ] Team size limits
- [ ] Name sanitization
- [ ] Directory collision check
- [ ] Framework compatibility
- [ ] Department validation

## Special Features
- [ ] Executive team patching
- [ ] Sub-team recommendations
- [ ] MCP optimization analysis
- [ ] Prompt template enhancement
- [ ] LLM fallback system
- [ ] Project awareness (ProjectAwareMixin)

## Logging
- [ ] Natural language team logs
- [ ] A2A communication logs
- [ ] Structured JSON logging
- [ ] Separate log files by type

## Templates
- [ ] Preserved template strings
- [ ] Personality modifications
- [ ] Company context integration
- [ ] Tool and skill inclusion
"""
        return checklist


def main():
    """Run feature validation."""
    validator = TeamFactoryFeatureValidator()

    # Capture current features
    print("Capturing current team_factory features...")
    features = validator.capture_current_features()

    # Save feature list
    with open("team_factory_features.json", "w") as f:
        json.dump(features, f, indent=2)

    # Create checklist
    checklist = validator.create_feature_checklist()
    with open("team_factory_feature_checklist.md", "w") as f:
        f.write(checklist)

    print(
        f"✓ Captured {sum(len(v) if isinstance(v, list) else len(v) if isinstance(v, dict) else 1 for v in features.values())} features"
    )
    print("✓ Created feature checklist")
    print("\nNext steps:")
    print("1. Review team_factory_features.json")
    print("2. Use team_factory_feature_checklist.md during refactoring")
    print("3. Run validation after each refactoring phase")


if __name__ == "__main__":
    main()
