#!/usr/bin/env python3
"""
MCP Wish List Manager
Tracks MCPs that teams need but don't exist yet
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@dataclass
class MCPWishListItem:
    """Represents a wished-for MCP"""

    name: str
    requested_by: str
    date_requested: str
    priority: str  # high, medium, low
    capabilities_needed: List[str]
    use_case: str
    similar_existing: List[str]
    estimated_complexity: str  # simple, medium, complex


class MCPWishListManager:
    """Manages the MCP wish list"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.wishlist_file = self.project_root / "mcp-wish-list.yaml"
        self.existing_mcps_file = self.project_root / "existing-mcps.yaml"

    def load_wishlist(self) -> List[MCPWishListItem]:
        """Load current wish list"""
        if not self.wishlist_file.exists():
            return []

        with open(self.wishlist_file, "r") as f:
            data = yaml.safe_load(f)

        items = []
        for item_data in data.get("wish_list", []):
            items.append(MCPWishListItem(**item_data))
        return items

    def save_wishlist(self, items: List[MCPWishListItem]):
        """Save wish list"""
        data = {"wish_list": [asdict(item) for item in items]}

        with open(self.wishlist_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def add_mcp_request(
        self,
        name: str,
        requested_by: str,
        capabilities_needed: List[str],
        use_case: str,
        priority: str = "medium",
        similar_existing: List[str] = None,
        estimated_complexity: str = "medium",
    ) -> bool:
        """Add a new MCP request to the wish list"""

        # Check if already exists
        items = self.load_wishlist()
        if any(item.name == name for item in items):
            # Update existing request
            for item in items:
                if item.name == name:
                    # Add requesting team if not already there
                    if requested_by not in item.requested_by:
                        item.requested_by += f", {requested_by}"
                    # Merge capabilities
                    for cap in capabilities_needed:
                        if cap not in item.capabilities_needed:
                            item.capabilities_needed.append(cap)
                    self.save_wishlist(items)
                    return False  # Not a new request
        else:
            # Add new request
            new_item = MCPWishListItem(
                name=name,
                requested_by=requested_by,
                date_requested=datetime.now().strftime("%Y-%m-%d"),
                priority=priority,
                capabilities_needed=capabilities_needed,
                use_case=use_case,
                similar_existing=similar_existing or [],
                estimated_complexity=estimated_complexity,
            )
            items.append(new_item)
            self.save_wishlist(items)
            return True  # New request added

    def check_if_mcp_exists(self, mcp_name: str) -> bool:
        """Check if an MCP already exists in our ecosystem"""
        # Check existing MCPs file
        if self.existing_mcps_file.exists():
            with open(self.existing_mcps_file, "r") as f:
                existing = yaml.safe_load(f)
                return mcp_name in existing.get("mcps", [])

        # Also check the mcps directory
        mcps_dir = self.project_root / "mcps"
        if mcps_dir.exists():
            return (mcps_dir / mcp_name).exists()

        return False

    def display_wishlist(self):
        """Display the current wish list"""
        items = self.load_wishlist()

        if not items:
            console.print("[yellow]No MCPs in wish list yet.[/yellow]")
            return

        # Sort by priority and date
        priority_order = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda x: (priority_order.get(x.priority, 3), x.date_requested))

        table = Table(
            title="MCP Wish List", show_header=True, header_style="bold magenta"
        )
        table.add_column("MCP Name", style="cyan")
        table.add_column("Requested By", style="green")
        table.add_column("Date", style="blue")
        table.add_column("Priority", style="yellow")
        table.add_column("Capabilities", style="white")
        table.add_column("Complexity", style="red")

        for item in items:
            priority_style = {
                "high": "[red]HIGH[/red]",
                "medium": "[yellow]MEDIUM[/yellow]",
                "low": "[green]LOW[/green]",
            }.get(item.priority, item.priority)

            caps_preview = ", ".join(item.capabilities_needed[:3])
            if len(item.capabilities_needed) > 3:
                caps_preview += f" (+{len(item.capabilities_needed) - 3} more)"

            table.add_row(
                item.name,
                item.requested_by,
                item.date_requested,
                priority_style,
                caps_preview,
                item.estimated_complexity,
            )

        console.print(table)

        # Show detailed view of high priority items
        high_priority = [item for item in items if item.priority == "high"]
        if high_priority:
            console.print("\n[bold red]High Priority MCPs:[/bold red]")
            for item in high_priority[:3]:  # Show top 3
                panel = Panel(
                    f"[bold]Use Case:[/bold] {item.use_case}\n\n"
                    f"[bold]Capabilities Needed:[/bold]\n"
                    + "\n".join(f"  • {cap}" for cap in item.capabilities_needed),
                    title=f"🔴 {item.name}",
                    border_style="red",
                )
                console.print(panel)

    def get_mcps_for_team(self, team_name: str) -> List[str]:
        """Get all MCPs requested by a specific team"""
        items = self.load_wishlist()
        mcps = []
        for item in items:
            if team_name in item.requested_by:
                mcps.append(item.name)
        return mcps


def integrate_with_team_factory(team_name: str, suggested_mcps: List[str]) -> List[str]:
    """
    Called by team factory to check and add MCPs to wish list
    Returns list of MCPs that don't exist yet
    """
    manager = MCPWishListManager()
    missing_mcps = []

    for mcp in suggested_mcps:
        if not manager.check_if_mcp_exists(mcp):
            missing_mcps.append(mcp)

            # Add to wish list
            # Extract capabilities from MCP name (heuristic)
            capabilities = []
            if "twitter" in mcp:
                capabilities = ["search_tweets", "get_timeline", "analyze_engagement"]
            elif "web-scraper" in mcp:
                capabilities = ["scrape_url", "extract_content", "follow_links"]
            elif "arxiv" in mcp:
                capabilities = ["search_papers", "get_paper_details", "download_pdf"]
            # Add more mappings as needed

            manager.add_mcp_request(
                name=mcp,
                requested_by=team_name,
                capabilities_needed=capabilities,
                use_case=f"{team_name} needs this MCP for their operations",
                priority="medium",
            )

    if missing_mcps:
        console.print(
            f"\n[yellow]⚠️  {len(missing_mcps)} MCPs added to wish list:[/yellow]"
        )
        for mcp in missing_mcps:
            console.print(f"  • {mcp}")

    return missing_mcps


if __name__ == "__main__":
    # Demo the wish list manager
    manager = MCPWishListManager()

    # Add some sample requests
    manager.add_mcp_request(
        name="twitter-mcp",
        requested_by="research-team",
        capabilities_needed=[
            "search_tweets",
            "get_user_timeline",
            "analyze_engagement",
        ],
        use_case="Monitor competitor mentions and sentiment on Twitter/X",
        priority="high",
    )

    manager.add_mcp_request(
        name="arxiv-mcp",
        requested_by="research-team",
        capabilities_needed=["search_papers", "get_abstracts", "download_pdfs"],
        use_case="Search and analyze academic papers for research tasks",
        priority="medium",
    )

    manager.add_mcp_request(
        name="web-scraper-mcp",
        requested_by="marketing-team",
        capabilities_needed=[
            "scrape_url",
            "extract_structured_data",
            "monitor_changes",
        ],
        use_case="Monitor competitor websites for pricing and feature changes",
        priority="high",
    )

    # Display the wish list
    manager.display_wishlist()

    # Show MCPs for a specific team
    print(
        f"\n\nMCPs requested by research-team: {manager.get_mcps_for_team('research-team')}"
    )
