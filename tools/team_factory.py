#!/usr/bin/env python3
"""
Backward compatibility wrapper for team_factory.

This allows existing code to continue using 'import team_factory' while
the actual implementation is now in the team_factory package.
"""

from pathlib import Path

# Import everything from the package
try:
    # Import main function for CLI compatibility
    from team_factory import *
    from team_factory import main
    from team_factory.models import *
except ImportError:
    # Fallback for when package is not yet complete
    import sys

    sys.path.insert(0, str(Path(__file__).parent))

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
