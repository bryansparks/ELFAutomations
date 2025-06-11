#!/usr/bin/env python3
"""
Setup Cost Monitoring in Supabase

Creates tables and configures cost monitoring integration.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from supabase import Client, create_client

# Load environment variables
load_dotenv()

console = Console()


def setup_cost_monitoring():
    """Setup cost monitoring tables and configuration"""
    console.print("[bold cyan]🎯 Setting up Cost Monitoring in Supabase[/bold cyan]\n")

    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        console.print("[red]❌ Missing Supabase credentials![/red]")
        console.print("\nPlease set:")
        console.print("  - SUPABASE_URL")
        console.print("  - SUPABASE_ANON_KEY")
        return False

    # Initialize Supabase client
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        console.print("[green]✅ Connected to Supabase[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to connect to Supabase: {e}[/red]")
        return False

    # Read SQL schema
    sql_file = (
        Path(__file__).parent.parent / "sql" / "create_cost_monitoring_tables.sql"
    )
    if not sql_file.exists():
        console.print(f"[red]❌ SQL file not found: {sql_file}[/red]")
        return False

    with open(sql_file, "r") as f:
        sql_content = f.read()

    # Execute SQL (would need Supabase admin access or use migrations)
    console.print("\n[yellow]📋 SQL Schema Ready[/yellow]")
    console.print("\nTo create the tables, run this SQL in your Supabase SQL editor:")
    console.print(Panel(sql_content[:500] + "...", title="SQL Schema (truncated)"))

    # Set up initial team budgets
    console.print("\n[bold]Setting up team budgets...[/bold]")

    teams_to_configure = [
        ("executive-team", 50.00, 0.80),
        ("marketing-team", 25.00, 0.80),
        ("sales-team", 25.00, 0.80),
        ("engineering-team", 30.00, 0.85),
        ("product-team", 20.00, 0.80),
        ("operations-team", 15.00, 0.75),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Configuring team budgets...", total=len(teams_to_configure)
        )

        for team_name, daily_budget, warning_threshold in teams_to_configure:
            try:
                # Check if budget exists
                result = (
                    supabase.table("team_budgets")
                    .select("*")
                    .eq("team_name", team_name)
                    .execute()
                )

                if not result.data:
                    # Insert new budget
                    supabase.table("team_budgets").insert(
                        {
                            "team_name": team_name,
                            "daily_budget": daily_budget,
                            "monthly_budget": daily_budget * 30,
                            "warning_threshold": warning_threshold,
                            "critical_threshold": 0.95,
                            "auto_fallback": True,
                        }
                    ).execute()
                    console.print(
                        f"  ✅ Created budget for {team_name}: ${daily_budget}/day"
                    )
                else:
                    console.print(f"  ℹ️  Budget already exists for {team_name}")

            except Exception as e:
                console.print(f"  ❌ Failed to configure {team_name}: {e}")

            progress.advance(task)

    # Create monitoring views
    console.print("\n[bold]Creating monitoring configuration...[/bold]")

    # Save configuration
    config_path = Path.home() / ".elf_automations" / "cost_monitoring"
    config_path.mkdir(parents=True, exist_ok=True)

    config_file = config_path / "supabase_config.json"
    import json

    config = {
        "supabase_url": supabase_url,
        "tables": {
            "api_usage": "api_usage",
            "daily_summary": "daily_cost_summary",
            "alerts": "cost_alerts",
            "budgets": "team_budgets",
            "recommendations": "cost_recommendations",
        },
        "views": {
            "current_usage": "current_day_usage",
            "weekly_trends": "weekly_cost_trends",
            "high_cost": "high_cost_requests",
        },
    }

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"✅ Configuration saved to {config_file}")

    # Summary
    summary = f"""
[bold green]✅ Cost Monitoring Setup Complete![/bold green]

Next Steps:
1. Run the SQL schema in Supabase SQL editor
2. Update agents to use integrated cost tracking:
   ```python
   from elf_automations.shared.utils import LLMFactory

   llm = LLMFactory.create_with_quota_tracking(
       team_name="your-team",
       enable_supabase=True  # Coming soon
   )
   ```
3. Monitor costs with:
   - `python scripts/cost_analytics.py show`
   - `python scripts/cost_optimizer.py`
   - `python scripts/quota_dashboard.py`

4. View in Supabase dashboard:
   - api_usage table for detailed logs
   - cost_alerts for notifications
   - daily_cost_summary for trends
"""

    console.print(Panel(summary, title="Setup Complete", border_style="green"))
    return True


def test_connection():
    """Test Supabase connection and tables"""
    console.print("\n[bold]Testing Supabase connection...[/bold]")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        console.print("[red]Missing credentials[/red]")
        return False

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        # Test queries
        tables_to_test = [
            "team_budgets",
            "api_usage",
            "daily_cost_summary",
            "cost_alerts",
        ]

        for table in tables_to_test:
            try:
                result = supabase.table(table).select("*").limit(1).execute()
                console.print(f"  ✅ {table} - accessible")
            except Exception as e:
                console.print(f"  ❌ {table} - {str(e)[:50]}...")

        return True

    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")
        return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Setup Cost Monitoring in Supabase")
    parser.add_argument("--test", action="store_true", help="Test connection only")

    args = parser.parse_args()

    if args.test:
        test_connection()
    else:
        setup_cost_monitoring()


if __name__ == "__main__":
    main()
