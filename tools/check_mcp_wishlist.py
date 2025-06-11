#!/usr/bin/env python3
"""
Check MCP Wish List Status
A monitoring tool for the MCP wish list
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

from tools.mcp_wishlist_manager import MCPWishListManager

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Check MCP Wish List Status")
    parser.add_argument("--team", help="Filter by requesting team")
    parser.add_argument(
        "--priority", choices=["high", "medium", "low"], help="Filter by priority"
    )
    parser.add_argument(
        "--add", action="store_true", help="Add a new MCP request interactively"
    )

    args = parser.parse_args()

    manager = MCPWishListManager()

    if args.add:
        # Interactive add
        console.print("[bold cyan]Add New MCP Request[/bold cyan]")
        name = console.input("MCP Name: ")
        requested_by = console.input("Requested By (team name): ")
        use_case = console.input("Use Case: ")
        priority = console.input("Priority (high/medium/low) [medium]: ") or "medium"

        capabilities = []
        console.print("Enter capabilities (one per line, empty line to finish):")
        while True:
            cap = console.input("  > ")
            if not cap:
                break
            capabilities.append(cap)

        manager.add_mcp_request(
            name=name,
            requested_by=requested_by,
            capabilities_needed=capabilities,
            use_case=use_case,
            priority=priority,
        )
        console.print(f"[green]✓ Added {name} to wish list[/green]")

    else:
        # Display wish list
        if args.team:
            mcps = manager.get_mcps_for_team(args.team)
            console.print(f"\n[bold]MCPs requested by {args.team}:[/bold]")
            for mcp in mcps:
                console.print(f"  • {mcp}")
        else:
            manager.display_wishlist()

            # Show summary stats
            items = manager.load_wishlist()
            if items:
                high = len([i for i in items if i.priority == "high"])
                medium = len([i for i in items if i.priority == "medium"])
                low = len([i for i in items if i.priority == "low"])

                console.print(f"\n[bold]Summary:[/bold]")
                console.print(f"  Total MCPs wished: {len(items)}")
                console.print(f"  High Priority: {high}")
                console.print(f"  Medium Priority: {medium}")
                console.print(f"  Low Priority: {low}")

                # Show requesting teams
                teams = set()
                for item in items:
                    teams.update(item.requested_by.split(", "))
                console.print(f"\n[bold]Requesting Teams:[/bold]")
                for team in sorted(teams):
                    team_mcps = manager.get_mcps_for_team(team)
                    console.print(f"  • {team}: {len(team_mcps)} MCPs")


if __name__ == "__main__":
    main()
