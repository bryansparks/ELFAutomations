"""
Command-line interface for team factory.
"""

import sys
from pathlib import Path


def main():
    """Main CLI entry point."""
    print("Team Factory Refactoring In Progress")
    print("-" * 40)
    print("The team factory is being refactored into a modular package structure.")
    print("This will preserve all functionality while making it more maintainable.")
    print("\nCurrent status:")
    print("✓ Models migrated")
    print("✓ Constants migrated")
    print("✓ Utilities created")
    print("⏳ Generators in progress")
    print("⏳ UI components pending")
    print("⏳ Integrations pending")
    print("\nTo use the original version:")
    print("python team_factory_original_backup.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
