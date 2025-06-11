#!/usr/bin/env python3
"""
Cost Analytics Dashboard - Advanced cost monitoring and reporting

Features:
- Real-time cost metrics
- Trend analysis
- Cost predictions
- Alert management
- Report generation
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

import plotext as plt
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.monitoring import AlertLevel, CostMonitor
from elf_automations.shared.quota import QuotaManager

console = Console()


def create_trend_chart(data: dict, title: str, width: int = 50, height: int = 15):
    """Create ASCII trend chart"""
    if not data:
        return "No data available"

    dates = list(data.keys())[-7:]  # Last 7 days
    values = [data[d] for d in dates]

    plt.clf()
    plt.theme("dark")
    plt.plot_size(width, height)
    plt.title(title)

    x_labels = [datetime.strptime(d, "%Y-%m-%d").strftime("%m/%d") for d in dates]
    plt.plot(x_labels, values, marker="braille")

    return plt.build()


def format_currency(value: float) -> str:
    """Format currency with color coding"""
    if value < 0:
        return f"[red]-${abs(value):.2f}[/red]"
    elif value > 100:
        return f"[red]${value:.2f}[/red]"
    elif value > 50:
        return f"[yellow]${value:.2f}[/yellow]"
    else:
        return f"[green]${value:.2f}[/green]"


def format_percentage(value: float, threshold: float = 80) -> str:
    """Format percentage with color coding"""
    if value >= 100:
        return f"[red]{value:.1f}%[/red]"
    elif value >= threshold:
        return f"[yellow]{value:.1f}%[/yellow]"
    else:
        return f"[green]{value:.1f}%[/green]"


async def show_analytics(args):
    """Display cost analytics dashboard"""
    console.clear()
    console.print("[bold cyan]📊 ElfAutomations Cost Analytics[/bold cyan]\n")

    # Initialize managers
    quota_path = Path.home() / ".elf_automations" / "quota_data"
    if not quota_path.exists():
        console.print("[yellow]No quota data found. Run some agents first![/yellow]")
        return

    quota_manager = QuotaManager(storage_path=quota_path)

    monitoring_path = Path.home() / ".elf_automations" / "cost_monitoring"
    cost_monitor = CostMonitor(storage_path=monitoring_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Analyzing costs...", total=None)

        # Get metrics
        metrics = await cost_monitor.analyze_costs(quota_manager)

        progress.update(task, completed=True)

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )

    # Header
    layout["header"].update(
        Panel(
            f"[bold]Cost Analytics Dashboard[/bold] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            style="cyan",
        )
    )

    # Split main area
    layout["main"].split_row(
        Layout(name="metrics", ratio=2), Layout(name="alerts", ratio=1)
    )

    # Metrics table
    metrics_table = Table(title="Team Metrics", box=box.ROUNDED)
    metrics_table.add_column("Team", style="cyan")
    metrics_table.add_column("Today's Cost", justify="right")
    metrics_table.add_column("Requests", justify="right")
    metrics_table.add_column("Avg Cost/Req", justify="right")
    metrics_table.add_column("Top Model", style="magenta")
    metrics_table.add_column("Budget Used", justify="right")

    total_cost = 0
    total_requests = 0

    for team, team_metrics in sorted(metrics.items()):
        budget = quota_manager.get_team_budget(team)
        budget_used = (team_metrics.total_cost / budget * 100) if budget > 0 else 0

        metrics_table.add_row(
            team,
            format_currency(team_metrics.total_cost),
            str(team_metrics.request_count),
            format_currency(team_metrics.avg_cost_per_request),
            team_metrics.most_expensive_model,
            format_percentage(budget_used),
        )

        total_cost += team_metrics.total_cost
        total_requests += team_metrics.request_count

    # Add totals
    metrics_table.add_section()
    metrics_table.add_row(
        "[bold]TOTAL[/bold]",
        format_currency(total_cost),
        str(total_requests),
        format_currency(total_cost / total_requests if total_requests > 0 else 0),
        "-",
        "-",
    )

    layout["metrics"].update(metrics_table)

    # Alerts panel
    alerts_content = []
    for alert in cost_monitor.alerts[-10:]:  # Last 10 alerts
        icon = (
            "🔴"
            if alert.level == AlertLevel.CRITICAL
            else "🟡"
            if alert.level == AlertLevel.WARNING
            else "🔵"
        )
        alerts_content.append(f"{icon} [{alert.timestamp[:10]}] {alert.message}")

    if not alerts_content:
        alerts_content.append("[green]No recent alerts[/green]")

    layout["alerts"].update(
        Panel("\n".join(alerts_content), title="Recent Alerts", border_style="yellow")
    )

    # Footer with summary
    total_budget = sum(quota_manager.get_team_budget(team) for team in metrics.keys())
    remaining = total_budget - total_cost

    layout["footer"].update(
        Panel(
            f"Total Budget: {format_currency(total_budget)} | "
            f"Used: {format_currency(total_cost)} | "
            f"Remaining: {format_currency(remaining)}",
            style="bold",
        )
    )

    console.print(layout)

    # Show predictions if requested
    if args.predict:
        console.print("\n[bold cyan]📈 Cost Predictions (Next 7 Days)[/bold cyan]\n")

        predictions_table = Table(box=box.SIMPLE)
        predictions_table.add_column("Team", style="cyan")

        # Add date columns
        for i in range(1, 8):
            date = (datetime.now() + timedelta(days=i)).strftime("%m/%d")
            predictions_table.add_column(date, justify="right")

        predictions_table.add_column("7-Day Total", justify="right", style="bold")

        for team in sorted(metrics.keys()):
            predictions = cost_monitor.get_cost_predictions(
                quota_manager, team, days_ahead=7
            )
            row = [team]
            total_predicted = 0

            for i in range(1, 8):
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                cost = predictions.get(date, 0)
                total_predicted += cost
                row.append(f"${cost:.2f}")

            row.append(format_currency(total_predicted))
            predictions_table.add_row(*row)

        console.print(predictions_table)

    # Show trends if requested
    if args.trends:
        console.print("\n[bold cyan]📊 Cost Trends[/bold cyan]\n")

        # Get last 30 days of data for trend
        trend_data = {}
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_total = 0

            for team in metrics.keys():
                if (
                    team in quota_manager.usage_data
                    and date in quota_manager.usage_data[team]
                ):
                    daily_total += quota_manager.usage_data[team][date].get(
                        "total_cost", 0
                    )

            trend_data[date] = daily_total

        # Create chart
        chart = create_trend_chart(trend_data, "30-Day Cost Trend")
        console.print(Panel(chart, title="Cost Trend", border_style="blue"))

    # Generate report if requested
    if args.report:
        console.print("\n[bold cyan]📄 Generating Report...[/bold cyan]")

        report = cost_monitor.generate_cost_report(
            quota_manager, start_date=args.start_date, end_date=args.end_date
        )

        # Export report
        report_path = cost_monitor.export_report(report, format=args.format)
        console.print(f"\n✅ Report saved to: [green]{report_path}[/green]")

        # Show summary
        summary_table = Table(title="Report Summary", box=box.SIMPLE)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", justify="right")

        summary_table.add_row(
            "Period", f"{report['period']['start']} to {report['period']['end']}"
        )
        summary_table.add_row(
            "Total Cost", format_currency(report["summary"]["total_cost"])
        )
        summary_table.add_row("Total Tokens", f"{report['summary']['total_tokens']:,}")
        summary_table.add_row(
            "Teams Over Budget", str(report["summary"]["teams_over_budget"])
        )
        summary_table.add_row(
            "Most Expensive Team",
            max(report["summary"]["cost_by_team"].items(), key=lambda x: x[1])[0],
        )
        summary_table.add_row(
            "Most Used Model",
            max(report["summary"]["cost_by_model"].items(), key=lambda x: x[1])[0]
            if report["summary"]["cost_by_model"]
            else "N/A",
        )

        console.print(summary_table)


async def monitor_costs(interval: int = 300):
    """Monitor costs continuously"""
    console.print("[bold cyan]🔍 Cost Monitor Active[/bold cyan]")
    console.print(
        f"[dim]Checking every {interval} seconds. Press Ctrl+C to stop.[/dim]\n"
    )

    quota_path = Path.home() / ".elf_automations" / "quota_data"
    monitoring_path = Path.home() / ".elf_automations" / "cost_monitoring"

    quota_manager = QuotaManager(storage_path=quota_path)
    cost_monitor = CostMonitor(storage_path=monitoring_path)

    try:
        while True:
            # Analyze costs
            metrics = await cost_monitor.analyze_costs(quota_manager)

            # Check for critical alerts
            critical_alerts = [
                alert
                for alert in cost_monitor.alerts
                if alert.level == AlertLevel.CRITICAL
                and datetime.fromisoformat(alert.timestamp)
                > datetime.now() - timedelta(hours=1)
            ]

            if critical_alerts:
                console.print(
                    f"\n[red]⚠️  {len(critical_alerts)} CRITICAL ALERTS![/red]"
                )
                for alert in critical_alerts:
                    console.print(f"   - {alert.message}")

            # Show current status
            total_cost = sum(m.total_cost for m in metrics.values())
            total_budget = sum(
                quota_manager.get_team_budget(team) for team in metrics.keys()
            )

            console.print(
                f"\n[{datetime.now().strftime('%H:%M:%S')}] "
                f"Total: {format_currency(total_cost)} / {format_currency(total_budget)} "
                f"({(total_cost/total_budget*100):.1f}%)"
            )

            # Sleep
            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ElfAutomations Cost Analytics")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Analytics command
    analytics_parser = subparsers.add_parser("show", help="Show analytics dashboard")
    analytics_parser.add_argument(
        "--predict", "-p", action="store_true", help="Show cost predictions"
    )
    analytics_parser.add_argument(
        "--trends", "-t", action="store_true", help="Show cost trends"
    )
    analytics_parser.add_argument(
        "--report", "-r", action="store_true", help="Generate report"
    )
    analytics_parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Report format"
    )
    analytics_parser.add_argument("--start-date", help="Report start date (YYYY-MM-DD)")
    analytics_parser.add_argument("--end-date", help="Report end date (YYYY-MM-DD)")

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor costs continuously")
    monitor_parser.add_argument(
        "--interval", "-i", type=int, default=300, help="Check interval in seconds"
    )

    args = parser.parse_args()

    if args.command == "show":
        asyncio.run(show_analytics(args))
    elif args.command == "monitor":
        asyncio.run(monitor_costs(args.interval))
    else:
        # Default to show
        args.predict = False
        args.trends = True
        args.report = False
        asyncio.run(show_analytics(args))


if __name__ == "__main__":
    main()
