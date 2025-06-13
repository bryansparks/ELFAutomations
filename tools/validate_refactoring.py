#!/usr/bin/env python3
"""
Validation script to ensure refactoring preserves all functionality.
Run this after each refactoring step to ensure nothing is lost.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class RefactoringValidator:
    """Validates that refactoring preserves all functionality."""

    def __init__(self):
        self.original_analysis = self._load_original_analysis()
        self.issues = []
        self.successes = []

    def _load_original_analysis(self) -> Dict:
        """Load the original analysis results."""
        analysis_file = Path("team_factory_analysis.json")
        if not analysis_file.exists():
            print("Error: Run analyze_team_factory_features.py first!")
            sys.exit(1)

        with open(analysis_file) as f:
            return json.load(f)

    def check_models(self) -> bool:
        """Verify all model classes are properly migrated."""
        print("\n🔍 Checking Models...")

        original_classes = {
            c["name"]
            for c in self.original_analysis["classes"]
            if c["name"] in ["TeamMember", "SubTeamRecommendation", "TeamSpecification"]
        }

        # Check if models exist in new structure
        models_ok = True
        for class_name in original_classes:
            try:
                if class_name == "TeamMember":
                    from team_factory.models import TeamMember

                    self.successes.append(f"✓ {class_name} successfully imported")
                elif class_name == "SubTeamRecommendation":
                    from team_factory.models import SubTeamRecommendation

                    self.successes.append(f"✓ {class_name} successfully imported")
                elif class_name == "TeamSpecification":
                    from team_factory.models import TeamSpecification

                    self.successes.append(f"✓ {class_name} successfully imported")
            except ImportError as e:
                self.issues.append(f"✗ Failed to import {class_name}: {e}")
                models_ok = False

        # Test model creation
        try:
            from team_factory.models import TeamMember, TeamSpecification

            # Create a test member
            member = TeamMember(
                name="Test Agent",
                role="Tester",
                responsibilities=["Testing"],
                personality="skeptic",
            )

            if member.is_skeptic:
                self.successes.append("✓ TeamMember personality assignment works")
            else:
                self.issues.append("✗ TeamMember personality assignment broken")

            # Create a test spec
            spec = TeamSpecification(
                name="Test Team",
                description="Test",
                purpose="Testing",
                framework="CrewAI",
                llm_provider="OpenAI",
                llm_model="gpt-4",
                department="engineering",
                members=[member],
            )

            if spec.manager == member:
                self.successes.append("✓ TeamSpecification manager assignment works")
            else:
                self.issues.append("✗ TeamSpecification manager assignment broken")

        except Exception as e:
            self.issues.append(f"✗ Model functionality test failed: {e}")
            models_ok = False

        return models_ok

    def check_constants(self) -> bool:
        """Verify constants are preserved."""
        print("\n🔍 Checking Constants...")

        constants_ok = True

        try:
            from team_factory.utils.constants import (
                DEPARTMENT_EXECUTIVE_MAPPING,
                FRAMEWORK_CONFIGS,
                LLM_PROVIDERS,
                MAX_TEAM_SIZE,
                MIN_TEAM_SIZE,
                PERSONALITY_TRAITS,
                SKEPTIC_THRESHOLD,
            )

            # Check personality traits
            expected_traits = set(self.original_analysis["personality_traits"])
            actual_traits = set(PERSONALITY_TRAITS.keys())

            if expected_traits.issubset(actual_traits):
                self.successes.append(
                    f"✓ All {len(expected_traits)} personality traits preserved"
                )
            else:
                missing = expected_traits - actual_traits
                self.issues.append(f"✗ Missing personality traits: {missing}")
                constants_ok = False

            # Check department mappings
            if DEPARTMENT_EXECUTIVE_MAPPING.get("engineering") == "CTO":
                self.successes.append("✓ Department mappings preserved")
            else:
                self.issues.append("✗ Department mappings incorrect")
                constants_ok = False

            # Check LLM providers
            if "OpenAI" in LLM_PROVIDERS and "Anthropic" in LLM_PROVIDERS:
                self.successes.append("✓ LLM provider configurations preserved")
            else:
                self.issues.append("✗ LLM provider configurations missing")
                constants_ok = False

        except ImportError as e:
            self.issues.append(f"✗ Failed to import constants: {e}")
            constants_ok = False

        return constants_ok

    def check_utils(self) -> bool:
        """Verify utility functions work correctly."""
        print("\n🔍 Checking Utilities...")

        utils_ok = True

        try:
            from team_factory.utils.sanitizers import get_safe_filename, sanitize_name

            # Test sanitization
            test_cases = [
                ("My Team Name!", "my-team-name"),
                ("Team@#$%123", "team123"),
                (
                    "Very Long Team Name That Exceeds The Maximum Length Allowed",
                    None,
                ),  # Should truncate
                ("", "unnamed-team"),
            ]

            for input_name, expected in test_cases:
                result = sanitize_name(input_name)
                if expected is None:
                    if len(result) <= 50:
                        self.successes.append(
                            f"✓ Sanitization correctly truncated: '{input_name[:20]}...'"
                        )
                    else:
                        self.issues.append(
                            f"✗ Sanitization failed to truncate: {input_name}"
                        )
                        utils_ok = False
                elif result == expected:
                    self.successes.append(
                        f"✓ Sanitization correct: '{input_name}' → '{result}'"
                    )
                else:
                    self.issues.append(
                        f"✗ Sanitization failed: '{input_name}' → '{result}' (expected '{expected}')"
                    )
                    utils_ok = False

            # Test filename generation
            filename = get_safe_filename("Marketing Manager")
            if filename == "marketing_manager.py":
                self.successes.append("✓ Filename generation works correctly")
            else:
                self.issues.append(f"✗ Filename generation failed: got '{filename}'")
                utils_ok = False

        except ImportError as e:
            self.issues.append(f"✗ Failed to import utilities: {e}")
            utils_ok = False
        except Exception as e:
            self.issues.append(f"✗ Utility function error: {e}")
            utils_ok = False

        return utils_ok

    def check_backward_compatibility(self) -> bool:
        """Verify backward compatibility wrapper works."""
        print("\n🔍 Checking Backward Compatibility...")

        compat_ok = True

        try:
            # Import from the wrapper
            import team_factory

            # Check if main classes are accessible
            if hasattr(team_factory, "TeamMember"):
                self.successes.append("✓ TeamMember accessible via wrapper")
            else:
                self.issues.append("✗ TeamMember not accessible via wrapper")
                compat_ok = False

            if hasattr(team_factory, "TeamSpecification"):
                self.successes.append("✓ TeamSpecification accessible via wrapper")
            else:
                self.issues.append("✗ TeamSpecification not accessible via wrapper")
                compat_ok = False

            if hasattr(team_factory, "main"):
                self.successes.append("✓ main() function accessible via wrapper")
            else:
                self.issues.append("✗ main() function not accessible via wrapper")
                compat_ok = False

        except ImportError as e:
            self.issues.append(f"✗ Failed to import team_factory wrapper: {e}")
            compat_ok = False

        return compat_ok

    def check_missing_features(self) -> List[str]:
        """Identify features not yet migrated."""
        missing = []

        # Check for core functions not yet migrated
        original_functions = {f["name"] for f in self.original_analysis["functions"]}

        # These should eventually be in the package
        expected_functions = [
            "generate_agent_file",
            "generate_crew_file",
            "generate_langgraph_workflow",
            "generate_dockerfile",
            "generate_k8s_deployment",
            "generate_readme",
            "create_executive_patch",
            "update_registry",
        ]

        for func in expected_functions:
            if func in original_functions:
                missing.append(f"Function: {func}")

        # Check for integrations
        for integration in self.original_analysis["integrations"]:
            missing.append(f"Integration: {integration}")

        # Check for UI components
        if self.original_analysis["ui_components"]:
            missing.append(
                f"UI Components: {len(self.original_analysis['ui_components'])} components"
            )

        # Check for templates
        if self.original_analysis["template_blocks"]:
            missing.append(
                f"Templates: {len(self.original_analysis['template_blocks'])} template blocks"
            )

        return missing

    def generate_report(self) -> str:
        """Generate validation report."""
        report = ["# Team Factory Refactoring Validation Report\n"]

        # Summary
        total_checks = len(self.successes) + len(self.issues)
        success_rate = (
            (len(self.successes) / total_checks * 100) if total_checks > 0 else 0
        )

        report.append(f"## Summary")
        report.append(f"- Total Checks: {total_checks}")
        report.append(f"- Passed: {len(self.successes)}")
        report.append(f"- Failed: {len(self.issues)}")
        report.append(f"- Success Rate: {success_rate:.1f}%\n")

        # Successes
        if self.successes:
            report.append("## ✓ Successes")
            for success in self.successes:
                report.append(f"- {success}")
            report.append("")

        # Issues
        if self.issues:
            report.append("## ✗ Issues to Fix")
            for issue in self.issues:
                report.append(f"- {issue}")
            report.append("")

        # Missing features
        missing = self.check_missing_features()
        if missing:
            report.append("## 🚧 Features Not Yet Migrated")
            for feature in missing:
                report.append(f"- {feature}")
            report.append("")

        # Next steps
        report.append("## 📋 Next Steps")
        if self.issues:
            report.append("1. Fix the issues listed above")
        report.append("2. Continue migrating missing features")
        report.append("3. Create generator modules for each framework")
        report.append("4. Migrate UI components to ui/ directory")
        report.append("5. Create integration modules")
        report.append("6. Build the core factory class")
        report.append("7. Migrate all templates")
        report.append("8. Test end-to-end team generation")

        return "\n".join(report)

    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("=" * 60)
        print("Team Factory Refactoring Validator")
        print("=" * 60)

        # Run checks
        models_ok = self.check_models()
        constants_ok = self.check_constants()
        utils_ok = self.check_utils()
        compat_ok = self.check_backward_compatibility()

        # Generate report
        report = self.generate_report()

        # Save report
        with open("refactoring_validation_report.md", "w") as f:
            f.write(report)

        print("\n" + "=" * 60)
        print(f"Validation Complete: {'PASSED' if not self.issues else 'FAILED'}")
        print(f"Report saved to: refactoring_validation_report.md")
        print("=" * 60)

        return len(self.issues) == 0


def main():
    """Run validation."""
    validator = RefactoringValidator()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
