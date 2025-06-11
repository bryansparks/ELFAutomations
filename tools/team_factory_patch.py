#!/usr/bin/env python3
"""
Patch for team_factory.py to fix the crew_class bug.
This reads the file, fixes the bug, and writes it back.
"""

import re
from pathlib import Path


def patch_team_factory():
    """Fix the crew_class template bug"""
    factory_path = Path(__file__).parent / "team_factory.py"

    # Read the file
    content = factory_path.read_text()

    # Fix the template string issue on line 2048
    # Change: from crew import {crew_class}
    # To: from crew import {crew_class_name}
    content = content.replace(
        "from crew import {crew_class}", "from crew import {crew_class_name}"
    )

    # Fix line 2071 as well
    content = content.replace(
        "crew_instance = {crew_class}()", "crew_instance = {crew_class_name}()"
    )

    # Find where crew_class is defined and make sure it's used in format
    # Around line 2127-2131
    old_pattern = r'crew_class = ".*?"\n.*?crew_class=crew_class,'
    new_pattern = 'crew_class_name = team_spec.name.replace("-", " ").title().replace(" ", "") + "Crew"\n            crew_class_name=crew_class_name,'

    # This is getting complex - let's check if the bug is in the format call
    if "crew_class_name" not in content:
        # The issue is that the template uses {crew_class} but the format() call might not include it
        print("❌ This bug requires manual fixing in team_factory.py")
        print(
            "The issue is around line 2048 where template variables aren't properly passed to format()"
        )
        return False

    # Write back
    factory_path.write_text(content)
    print("✅ Patched team_factory.py")
    return True


if __name__ == "__main__":
    if not patch_team_factory():
        print("\n🔧 Manual fix needed:")
        print("1. Edit tools/team_factory.py")
        print("2. Search for 'from crew import {crew_class}'")
        print("3. Make sure the format() call includes crew_class=...")
        print("\nOr we can work around this by creating teams manually for now.")
