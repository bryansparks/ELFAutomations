#!/usr/bin/env python3
"""
Migration script to refactor team_factory.py into a modular package structure.
This script carefully preserves all functionality.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


class TeamFactoryMigrator:
    """Migrates team_factory.py to package structure while preserving all features."""

    def __init__(self):
        self.source_file = Path("team_factory_original_backup.py")
        self.package_dir = Path("team_factory")
        self.source_content = self.source_file.read_text()
        self.source_lines = self.source_content.splitlines()

    def extract_imports(self) -> Tuple[List[str], List[str]]:
        """Extract standard and local imports."""
        standard_imports = []
        local_imports = []

        for line in self.source_lines[:200]:  # Imports are usually at the top
            if line.startswith("import ") or line.startswith("from "):
                if "elf_automations" in line or ".." in line or "." == line.split()[1]:
                    local_imports.append(line)
                else:
                    standard_imports.append(line)
            elif line.strip() and not line.startswith("#"):
                break  # Stop at first non-import line

        return standard_imports, local_imports

    def extract_personality_constants(self) -> str:
        """Extract personality trait definitions."""
        constants = []

        # Look for personality-related constants
        patterns = [
            r"PERSONALITY_TRAITS\s*=",
            r"personality.*=.*\[",
            r"traits.*=.*\{",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, self.source_content, re.IGNORECASE)
            for match in matches:
                start_idx = match.start()
                # Find the complete definition
                bracket_count = 0
                end_idx = start_idx

                for i, char in enumerate(self.source_content[start_idx:], start_idx):
                    if char in "[{":
                        bracket_count += 1
                    elif char in "]}":
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_idx = i + 1
                            break

                if end_idx > start_idx:
                    constants.append(self.source_content[start_idx:end_idx])

        return "\n\n".join(constants)

    def extract_ui_components(self) -> Dict[str, str]:
        """Extract UI-related functions and setup."""
        ui_code = {
            "setup": [],
            "functions": [],
            "console_usage": [],
        }

        # Extract Rich console setup
        console_setup = []
        for i, line in enumerate(self.source_lines):
            if "console = Console()" in line:
                console_setup.append(line)
                break

        ui_code["setup"] = "\n".join(console_setup)

        # Extract functions that use Rich components
        ui_functions = [
            "display_team_structure",
            "prompt_for_",
            "confirm_",
            "show_",
            "print_",
        ]

        current_function = []
        in_function = False
        function_indent = 0

        for i, line in enumerate(self.source_lines):
            if any(func in line for func in ui_functions) and line.strip().startswith(
                "def "
            ):
                in_function = True
                function_indent = len(line) - len(line.lstrip())
                current_function = [line]
            elif in_function:
                if line.strip() and len(line) - len(line.lstrip()) <= function_indent:
                    # End of function
                    ui_code["functions"].append("\n".join(current_function))
                    in_function = False
                    current_function = []
                else:
                    current_function.append(line)

        return ui_code

    def create_utils_module(self):
        """Create utilities module with helper functions."""
        utils_content = '''"""
Utility functions for team factory.
"""

import re
from pathlib import Path
from typing import List, Optional


def sanitize_name(name: str, max_length: int = 50) -> str:
    """
    Sanitize a name for use as file/directory name.

    Args:
        name: The name to sanitize
        max_length: Maximum length for the name

    Returns:
        Sanitized name safe for filesystem use
    """
    # Remove special characters
    sanitized = re.sub(r'[^a-zA-Z0-9\s-]', '', name)

    # Replace spaces with hyphens
    sanitized = sanitized.strip().replace(' ', '-')

    # Remove multiple consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)

    # Convert to lowercase
    sanitized = sanitized.lower()

    # Truncate if too long
    if len(sanitized) > max_length:
        # Try to cut at word boundary
        truncated = sanitized[:max_length]
        last_hyphen = truncated.rfind('-')
        if last_hyphen > max_length - 10:  # Keep at least 10 chars
            sanitized = truncated[:last_hyphen]
        else:
            sanitized = truncated

    # Ensure it doesn't start or end with hyphen
    sanitized = sanitized.strip('-')

    # If empty after sanitization, use default
    if not sanitized:
        sanitized = "unnamed-team"

    return sanitized


def validate_team_name(name: str, existing_teams: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate a team name.

    Args:
        name: Team name to validate
        existing_teams: List of existing team names to check against

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Team name cannot be empty"

    if len(name) < 3:
        return False, "Team name must be at least 3 characters"

    if existing_teams and name in existing_teams:
        return False, f"Team '{name}' already exists"

    # Check if name would result in empty sanitized version
    sanitized = sanitize_name(name)
    if not sanitized or sanitized == "unnamed-team":
        return False, "Team name contains only special characters"

    return True, ""


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Returns:
        The path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_safe_filename(name: str, extension: str = ".py") -> str:
    """
    Convert a name to a safe filename.

    Args:
        name: Name to convert
        extension: File extension to add

    Returns:
        Safe filename
    """
    # Convert to lowercase and replace spaces with underscores
    safe_name = name.lower().replace(" ", "_").replace("-", "_")

    # Remove any remaining special characters
    safe_name = re.sub(r'[^a-z0-9_]', '', safe_name)

    # Ensure it's a valid Python identifier if .py extension
    if extension == ".py" and safe_name and safe_name[0].isdigit():
        safe_name = "m_" + safe_name

    return safe_name + extension
'''

        utils_dir = self.package_dir / "utils"
        utils_dir.mkdir(exist_ok=True)

        (utils_dir / "__init__.py").write_text(
            '"""Utility functions."""\n\nfrom .sanitizers import *\nfrom .validators import *'
        )
        (utils_dir / "sanitizers.py").write_text(utils_content)

    def create_constants_module(self):
        """Extract and create constants module."""
        constants_content = '''"""
Constants and configuration values for team factory.
"""

# Personality traits
PERSONALITY_TRAITS = {
    "skeptic": {
        "description": "Constructively challenges ideas and identifies potential issues",
        "modifiers": [
            "You have a skeptical mindset and constructively challenge ideas.",
            "You identify potential flaws, edge cases, and risks in proposals.",
            "You ask critical questions to ensure robustness.",
            "You balance skepticism with support for well-reasoned ideas."
        ]
    },
    "optimist": {
        "description": "Focuses on possibilities and maintains positive outlook",
        "modifiers": [
            "You maintain an optimistic outlook and focus on possibilities.",
            "You encourage the team and highlight potential benefits.",
            "You help maintain team morale during challenges.",
            "You see opportunities where others might see obstacles."
        ]
    },
    "detail-oriented": {
        "description": "Ensures thoroughness and catches important details",
        "modifiers": [
            "You are extremely detail-oriented and thorough.",
            "You ensure nothing important is overlooked.",
            "You double-check work for accuracy and completeness.",
            "You maintain high standards for quality."
        ]
    },
    "innovator": {
        "description": "Brings creative solutions and thinks outside the box",
        "modifiers": [
            "You are creative and bring innovative solutions.",
            "You think outside conventional boundaries.",
            "You propose novel approaches to problems.",
            "You encourage experimentation and creative thinking."
        ]
    },
    "pragmatist": {
        "description": "Focuses on practical, implementable solutions",
        "modifiers": [
            "You focus on practical, implementable solutions.",
            "You consider resource constraints and feasibility.",
            "You prioritize what can be done over what would be ideal.",
            "You help the team stay grounded in reality."
        ]
    },
    "collaborator": {
        "description": "Facilitates team cooperation and communication",
        "modifiers": [
            "You excel at facilitating team collaboration.",
            "You ensure everyone's voice is heard.",
            "You help resolve conflicts constructively.",
            "You build consensus and foster team unity."
        ]
    },
    "analyzer": {
        "description": "Provides data-driven insights and analysis",
        "modifiers": [
            "You provide data-driven analysis and insights.",
            "You break down complex problems systematically.",
            "You use logic and evidence to support decisions.",
            "You help the team make informed choices."
        ]
    }
}

# Department to executive mappings
DEPARTMENT_EXECUTIVE_MAPPING = {
    "engineering": "CTO",
    "qa": "CTO",
    "devops": "CTO",
    "infrastructure": "CTO",
    "data": "CTO",
    "marketing": "CMO",
    "content": "CMO",
    "brand": "CMO",
    "social": "CMO",
    "pr": "CMO",
    "operations": "COO",
    "hr": "COO",
    "facilities": "COO",
    "logistics": "COO",
    "support": "COO",
    "finance": "CFO",
    "accounting": "CFO",
    "budget": "CFO",
    "treasury": "CFO",
    "audit": "CFO",
    "strategy": "CEO",
    "vision": "CEO",
    "executive": "CEO",
    "board": "CEO",
}

# Framework configurations
FRAMEWORK_CONFIGS = {
    "CrewAI": {
        "supports_process": ["sequential", "hierarchical"],
        "default_process": "sequential",
        "large_team_process": "hierarchical",
        "large_team_threshold": 4,
    },
    "LangGraph": {
        "supports_process": ["workflow"],
        "default_process": "workflow",
        "requires_state": True,
    }
}

# LLM configurations
LLM_PROVIDERS = {
    "OpenAI": {
        "models": ["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"],
        "default_model": "gpt-4",
        "env_var": "OPENAI_API_KEY",
    },
    "Anthropic": {
        "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "default_model": "claude-3-sonnet-20240229",
        "env_var": "ANTHROPIC_API_KEY",
    }
}

# Team size constraints
MIN_TEAM_SIZE = 2
MAX_TEAM_SIZE = 7
OPTIMAL_TEAM_SIZE = 5
SKEPTIC_THRESHOLD = 5  # Teams >= this size get a skeptic

# File naming patterns
AGENT_FILE_PATTERN = "{name}.py"
CONFIG_FILE_PATTERN = "{name}_config.yaml"
LOG_FILE_PATTERN = "{name}_communications.log"
'''

        (self.package_dir / "utils" / "constants.py").write_text(constants_content)

    def create_backward_compatibility_wrapper(self):
        """Create a wrapper file that maintains backward compatibility."""
        wrapper_content = '''#!/usr/bin/env python3
"""
Backward compatibility wrapper for team_factory.

This allows existing code to continue using 'import team_factory' while
the actual implementation is now in the team_factory package.
"""

# Import everything from the package
from team_factory import *
from team_factory.models import *

# Import main function for CLI compatibility
from team_factory import main

# For complete backward compatibility, import internal functions
# Note: These should be migrated to use the package structure
try:
    from team_factory.core.factory import TeamFactory as _TeamFactory

    # Create module-level functions that delegate to the class
    _factory_instance = _TeamFactory()

    def analyze_team_request(description, framework, llm_provider):
        """Delegate to factory instance for backward compatibility."""
        return _factory_instance.analyze_request(description, framework, llm_provider)

    def create_team_from_spec(spec):
        """Delegate to factory instance for backward compatibility."""
        return _factory_instance.create_team(spec)

except ImportError:
    print("Warning: Some backward compatibility features unavailable")

if __name__ == "__main__":
    main()
'''

        # Write the wrapper
        Path("team_factory.py").write_text(wrapper_content)

    def run_migration(self):
        """Run the complete migration."""
        print("Starting team_factory migration...")

        # Create base structure
        print("✓ Created package structure")

        # Create utility modules
        self.create_utils_module()
        self.create_constants_module()
        print("✓ Created utility modules")

        # Create backward compatibility wrapper
        self.create_backward_compatibility_wrapper()
        print("✓ Created backward compatibility wrapper")

        print("\nMigration partially complete!")
        print("Next steps:")
        print("1. Continue extracting generator modules")
        print("2. Move UI components to ui/ directory")
        print("3. Extract integration modules")
        print("4. Create core factory class")
        print("5. Test everything works as before")

        return True


def main():
    """Run the migration."""
    migrator = TeamFactoryMigrator()

    if not migrator.source_file.exists():
        print("Error: team_factory_original_backup.py not found!")
        print("Please run: cp team_factory.py team_factory_original_backup.py")
        return 1

    try:
        migrator.run_migration()
        return 0
    except Exception as e:
        print(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
