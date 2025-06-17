"""
Command-line interface for team factory.
"""

import sys
from pathlib import Path

from .core.factory import TeamFactory
from .ui.console import TeamFactoryConsole


def main():
    """Main CLI entry point."""
    # Create factory instance
    factory = TeamFactory()
    console = TeamFactoryConsole()
    
    try:
        # Show welcome
        console.show_welcome()
        
        # Get team requirements from user
        team_spec = console.get_team_requirements()
        
        if not team_spec:
            console.show_error("No team specification provided. Exiting.")
            return 1
        
        # Create the team
        result = factory.create_team(team_spec)
        
        if result['success']:
            console.show_success(f"\nTeam '{team_spec.name}' created successfully!")
            if 'team_path' in result:
                console.show_info(f"Location: {result['team_path']}")
            
            # Show next steps
            console.show_next_steps(team_spec.name)
        else:
            console.show_error(f"Failed to create team: {result.get('error', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        console.show_info("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        console.show_error(f"Unexpected error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
