#!/usr/bin/env python3
"""
Quota Dashboard - Monitor API usage across all teams

Run this to see current usage, budgets, and trends.
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.quota import QuotaManager

console = Console()


def create_usage_bar(current: float, budget: float) -> str:
    """Create a visual progress bar for usage"""
    if budget == 0:
        return "[red]No budget set[/red]"

    percentage = (current / budget) * 100
    filled = int(percentage / 5)  # 20 chars total
    bar = "█" * filled + "░" * (20 - filled)

    if percentage >= 100:
        color = "red"
    elif percentage >= 80:
        color = "yellow"
    else:
        color = "green"

    return f"[{color}]{bar}[/{color}] {percentage:.1f}%"


def get_all_teams(quota_manager: QuotaManager) -> list:
    """Get all teams that have used the API"""
    teams = set()
    for team_data in quota_manager.usage_data.values():
        if isinstance(team_data, dict) and not team_data.get("budgets"):
            teams.add(list(quota_manager.usage_data.keys())[0])

    # More robust way to get teams
    teams = set()
    for key, value in quota_manager.usage_data.items():
        if key != "budgets" and isinstance(value, dict):
            teams.add(key)

    return sorted(list(teams))


def show_dashboard():
    """Display the quota dashboard"""
    console.print("\n[bold cyan]🎯 ElfAutomations Quota Dashboard[/bold cyan]\n")

    # Initialize quota manager
    quota_path = Path.home() / ".elf_automations" / "quota_data"
    if not quota_path.exists():
        console.print(
            "[yellow]No quota data found. Teams haven't started using the API yet.[/yellow]"
        )
        return

    quota_manager = QuotaManager(storage_path=quota_path)

    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")

    # Create main table
    table = Table(title=f"Team Usage for {today}")
    table.add_column("Team", style="cyan", no_wrap=True)
    table.add_column("Daily Budget", style="green", justify="right")
    table.add_column("Used Today", style="yellow", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Usage", justify="center", width=30)
    table.add_column("Top Model", style="magenta")

    # Get all teams
    teams = get_all_teams(quota_manager)

    if not teams:
        console.print("[yellow]No teams found in quota data.[/yellow]")
        return

    total_budget = 0
    total_used = 0

    for team in teams:
        # Get budget
        budget = quota_manager.get_team_budget(team)
        total_budget += budget

        # Get today's usage
        used_today = 0
        top_model = "N/A"
        model_costs = {}

        if team in quota_manager.usage_data and today in quota_manager.usage_data[team]:
            daily_data = quota_manager.usage_data[team][today]
            used_today = daily_data.get("total_cost", 0)

            # Find top model
            if "models" in daily_data:
                for model, data in daily_data["models"].items():
                    model_costs[model] = data.get("cost", 0)
                if model_costs:
                    top_model = max(model_costs, key=model_costs.get)

        total_used += used_today
        remaining = budget - used_today

        # Color code remaining
        if remaining < 0:
            remaining_str = f"[red]-${abs(remaining):.2f}[/red]"
        elif remaining < budget * 0.2:
            remaining_str = f"[yellow]${remaining:.2f}[/yellow]"
        else:
            remaining_str = f"[green]${remaining:.2f}[/green]"

        # Add row
        table.add_row(
            team,
            f"${budget:.2f}",
            f"${used_today:.2f}",
            remaining_str,
            create_usage_bar(used_today, budget),
            top_model,
        )

    console.print(table)

    # Summary panel
    summary_text = f"""
[bold]Daily Summary[/bold]
Total Budget: [green]${total_budget:.2f}[/green]
Total Used: [yellow]${total_used:.2f}[/yellow]
Total Remaining: [{'red' if total_budget - total_used < 0 else 'green'}]${total_budget - total_used:.2f}[/{'red' if total_budget - total_used < 0 else 'green'}]

[bold]7-Day Trend[/bold]
"""

    # Add 7-day trend
    trend_data = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_total = 0
        for team in teams:
            if (
                team in quota_manager.usage_data
                and date in quota_manager.usage_data[team]
            ):
                day_total += quota_manager.usage_data[team][date].get("total_cost", 0)
        trend_data.append((date, day_total))

    # Reverse to show oldest to newest
    trend_data.reverse()

    for date, cost in trend_data:
        day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%a")
        bar_length = int((cost / max(total_budget, 0.01)) * 20)
        bar = "▪" * bar_length
        summary_text += f"{day_name}: [cyan]{bar}[/cyan] ${cost:.2f}\n"

    console.print(Panel(summary_text.strip(), title="Summary", border_style="blue"))

    # Alerts
    alerts = []
    for team in teams:
        budget = quota_manager.get_team_budget(team)
        if team in quota_manager.usage_data and today in quota_manager.usage_data[team]:
            used = quota_manager.usage_data[team][today].get("total_cost", 0)
            if used > budget:
                alerts.append(
                    f"[red]⚠️  {team} is OVER BUDGET by ${used - budget:.2f}[/red]"
                )
            elif used > budget * 0.8:
                alerts.append(
                    f"[yellow]⚠️  {team} has used {(used/budget)*100:.0f}% of budget[/yellow]"
                )

    if alerts:
        console.print("\n[bold]Alerts[/bold]")
        for alert in alerts:
            console.print(alert)

    # Model usage breakdown
    console.print("\n[bold]Model Usage Breakdown[/bold]")
    model_table = Table()
    model_table.add_column("Model", style="cyan")
    model_table.add_column("Total Cost", style="yellow", justify="right")
    model_table.add_column("Call Count", style="green", justify="right")
    model_table.add_column("Avg Cost/Call", justify="right")

    model_totals = {}
    for team in teams:
        if team in quota_manager.usage_data and today in quota_manager.usage_data[team]:
            daily_data = quota_manager.usage_data[team][today]
            if "models" in daily_data:
                for model, data in daily_data["models"].items():
                    if model not in model_totals:
                        model_totals[model] = {"cost": 0, "calls": 0}
                    model_totals[model]["cost"] += data.get("cost", 0)
                    model_totals[model]["calls"] += data.get("calls", 0)

    for model, data in sorted(
        model_totals.items(), key=lambda x: x[1]["cost"], reverse=True
    ):
        avg_cost = data["cost"] / data["calls"] if data["calls"] > 0 else 0
        model_table.add_row(
            model, f"${data['cost']:.4f}", str(data["calls"]), f"${avg_cost:.4f}"
        )

    if model_totals:
        console.print(model_table)

    # Tips
    console.print("\n[bold green]💡 Cost Saving Tips[/bold green]")
    console.print(
        "• Use [cyan]gpt-3.5-turbo[/cyan] instead of [cyan]gpt-4[/cyan] for simple tasks"
    )
    console.print(
        "• Use [cyan]claude-3-haiku[/cyan] instead of [cyan]claude-3-opus[/cyan] for basic queries"
    )
    console.print("• Keep prompts concise to reduce token usage")
    console.print("• Set up fallback chains in your agents")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ElfAutomations Quota Dashboard")
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Watch mode - refresh every 30 seconds",
    )
    parser.add_argument("--team", "-t", help="Show details for specific team")

    args = parser.parse_args()

    if args.watch:
        # Watch mode
        try:
            while True:
                console.clear()
                show_dashboard()
                console.print(
                    "\n[dim]Refreshing in 30 seconds... Press Ctrl+C to exit[/dim]"
                )
                time.sleep(30)
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped[/yellow]")
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
