#!/usr/bin/env python3
"""
Cost Optimizer - Analyzes usage patterns and provides optimization recommendations

Features:
- Identifies cost-saving opportunities
- Suggests model switches
- Recommends prompt optimizations
- Provides ROI analysis
"""

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.quota import QuotaManager

console = Console()


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation"""

    title: str
    description: str
    potential_savings: float
    effort: str  # "Low", "Medium", "High"
    impact: str  # "Low", "Medium", "High"
    implementation: str


class CostOptimizer:
    """Analyzes usage and provides optimization recommendations"""

    def __init__(self, quota_manager: QuotaManager):
        self.quota_manager = quota_manager
        self.recommendations: List[OptimizationRecommendation] = []

    def analyze_all_teams(self) -> Dict[str, List[OptimizationRecommendation]]:
        """Analyze all teams and generate recommendations"""
        recommendations = {}

        teams = self._get_all_teams()
        for team in teams:
            team_recs = self.analyze_team(team)
            if team_recs:
                recommendations[team] = team_recs

        return recommendations

    def analyze_team(self, team: str) -> List[OptimizationRecommendation]:
        """Analyze a specific team's usage"""
        recommendations = []

        # Get last 7 days of data
        usage_data = self._get_team_usage(team, days=7)
        if not usage_data:
            return recommendations

        # Analysis 1: Model usage optimization
        model_recs = self._analyze_model_usage(team, usage_data)
        recommendations.extend(model_recs)

        # Analysis 2: Usage patterns
        pattern_recs = self._analyze_usage_patterns(team, usage_data)
        recommendations.extend(pattern_recs)

        # Analysis 3: Cost efficiency
        efficiency_recs = self._analyze_cost_efficiency(team, usage_data)
        recommendations.extend(efficiency_recs)

        # Analysis 4: Budget optimization
        budget_recs = self._analyze_budget_usage(team, usage_data)
        recommendations.extend(budget_recs)

        return recommendations

    def _analyze_model_usage(
        self, team: str, usage_data: Dict
    ) -> List[OptimizationRecommendation]:
        """Analyze model usage and suggest optimizations"""
        recommendations = []

        # Aggregate model usage
        model_costs = {}
        model_requests = {}

        for day_data in usage_data.values():
            if "models" in day_data:
                for model, data in day_data["models"].items():
                    model_costs[model] = model_costs.get(model, 0) + data.get("cost", 0)
                    model_requests[model] = model_requests.get(model, 0) + data.get(
                        "calls", 0
                    )

        # Check for expensive model overuse
        if (
            "gpt-4" in model_costs
            and model_costs["gpt-4"] > sum(model_costs.values()) * 0.7
        ):
            # GPT-4 is >70% of costs
            potential_savings = (
                model_costs["gpt-4"] * 0.5
            )  # Assume 50% could use cheaper model

            recommendations.append(
                OptimizationRecommendation(
                    title="Switch to GPT-3.5 for simple tasks",
                    description=f"GPT-4 accounts for {(model_costs['gpt-4']/sum(model_costs.values())*100):.0f}% of costs. Many tasks could use GPT-3.5-turbo.",
                    potential_savings=potential_savings,
                    effort="Low",
                    impact="High",
                    implementation="""
1. Review agent prompts and identify simple tasks
2. Add logic to use GPT-3.5 for:
   - Simple questions/answers
   - Data formatting
   - Basic summaries
3. Reserve GPT-4 for complex reasoning tasks
""",
                )
            )

        # Check for Claude Opus overuse
        if "claude-3-opus" in model_costs:
            opus_percentage = model_costs["claude-3-opus"] / sum(model_costs.values())
            if opus_percentage > 0.5:
                potential_savings = model_costs["claude-3-opus"] * 0.6

                recommendations.append(
                    OptimizationRecommendation(
                        title="Use Claude Haiku for routine tasks",
                        description="Claude Opus is expensive. Switch to Haiku for routine tasks.",
                        potential_savings=potential_savings,
                        effort="Low",
                        impact="High",
                        implementation="""
1. Use Claude Haiku for:
   - Short responses
   - Simple analysis
   - Data extraction
2. Use Claude Opus only for:
   - Complex reasoning
   - Creative tasks
   - Long-form content
""",
                    )
                )

        return recommendations

    def _analyze_usage_patterns(
        self, team: str, usage_data: Dict
    ) -> List[OptimizationRecommendation]:
        """Analyze usage patterns for optimization"""
        recommendations = []

        # Calculate daily averages
        total_days = len(usage_data)
        total_tokens = sum(day.get("token_count", 0) for day in usage_data.values())
        avg_tokens_per_day = total_tokens / total_days if total_days > 0 else 0

        # High token usage
        if avg_tokens_per_day > 100000:  # 100k tokens per day
            recommendations.append(
                OptimizationRecommendation(
                    title="Implement response caching",
                    description="High token usage detected. Cache common responses.",
                    potential_savings=total_tokens * 0.2 * 0.001,  # 20% reduction
                    effort="Medium",
                    impact="Medium",
                    implementation="""
1. Identify frequently asked questions
2. Implement caching layer for common queries
3. Use semantic similarity to match cached responses
4. Set appropriate cache TTL (e.g., 24 hours)
""",
                )
            )

        # Check for inefficient prompt usage
        total_cost = sum(day.get("total_cost", 0) for day in usage_data.values())
        if total_cost > 0 and total_tokens > 0:
            cost_per_1k_tokens = (total_cost / total_tokens) * 1000
            if cost_per_1k_tokens > 0.01:  # High cost per token
                recommendations.append(
                    OptimizationRecommendation(
                        title="Optimize prompt engineering",
                        description="High cost per token. Prompts may be inefficient.",
                        potential_savings=total_cost * 0.15,
                        effort="Low",
                        impact="Medium",
                        implementation="""
1. Review and shorten system prompts
2. Remove redundant instructions
3. Use concise language
4. Move static content out of prompts
5. Use prompt templates efficiently
""",
                    )
                )

        return recommendations

    def _analyze_cost_efficiency(
        self, team: str, usage_data: Dict
    ) -> List[OptimizationRecommendation]:
        """Analyze cost efficiency metrics"""
        recommendations = []

        # Get budget
        budget = self.quota_manager.get_team_budget(team)
        total_cost = sum(day.get("total_cost", 0) for day in usage_data.values())
        avg_daily_cost = total_cost / len(usage_data) if usage_data else 0

        # Underutilized budget
        if avg_daily_cost < budget * 0.3:
            recommendations.append(
                OptimizationRecommendation(
                    title="Budget reallocation opportunity",
                    description=f"Team uses only {(avg_daily_cost/budget*100):.0f}% of budget. Consider reallocation.",
                    potential_savings=0,  # Not a savings, but optimization
                    effort="Low",
                    impact="Low",
                    implementation=f"""
1. Current budget: ${budget:.2f}/day
2. Average usage: ${avg_daily_cost:.2f}/day
3. Consider:
   - Reducing budget to ${avg_daily_cost * 1.5:.2f}/day
   - Reallocating to teams near limit
   - Investing in more advanced models for better results
""",
                )
            )

        # Near budget limit
        elif avg_daily_cost > budget * 0.9:
            recommendations.append(
                OptimizationRecommendation(
                    title="Implement strict token limits",
                    description="Team frequently near budget limit. Need better controls.",
                    potential_savings=avg_daily_cost * 0.1,
                    effort="Medium",
                    impact="High",
                    implementation="""
1. Set max tokens per request
2. Implement request queuing
3. Add priority levels for tasks
4. Create budget alerts at 70%, 80%, 90%
5. Auto-switch to cheaper models at 80%
""",
                )
            )

        return recommendations

    def _analyze_budget_usage(
        self, team: str, usage_data: Dict
    ) -> List[OptimizationRecommendation]:
        """Analyze budget usage patterns"""
        recommendations = []

        # Check for weekend/off-hours usage
        weekend_cost = 0
        weekday_cost = 0

        for date_str, day_data in usage_data.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date.weekday() in [5, 6]:  # Weekend
                weekend_cost += day_data.get("total_cost", 0)
            else:
                weekday_cost += day_data.get("total_cost", 0)

        if weekend_cost > weekday_cost * 0.2:  # Significant weekend usage
            recommendations.append(
                OptimizationRecommendation(
                    title="Optimize weekend operations",
                    description="Significant weekend usage detected. Consider scheduling.",
                    potential_savings=weekend_cost * 0.5,
                    effort="Medium",
                    impact="Low",
                    implementation="""
1. Batch non-urgent tasks for weekdays
2. Use cheaper models on weekends
3. Implement task scheduling
4. Reduce agent activity on weekends
""",
                )
            )

        return recommendations

    def _get_all_teams(self) -> List[str]:
        """Get all teams"""
        teams = set()
        for key, value in self.quota_manager.usage_data.items():
            if key != "budgets" and isinstance(value, dict):
                teams.add(key)
        return list(teams)

    def _get_team_usage(self, team: str, days: int = 7) -> Dict:
        """Get team usage for specified days"""
        usage = {}

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if team in self.quota_manager.usage_data:
                if date in self.quota_manager.usage_data[team]:
                    usage[date] = self.quota_manager.usage_data[team][date]

        return usage


def show_recommendations():
    """Display optimization recommendations"""
    console.print("[bold cyan]💡 ElfAutomations Cost Optimization Advisor[/bold cyan]\n")

    # Initialize
    quota_path = Path.home() / ".elf_automations" / "quota_data"
    if not quota_path.exists():
        console.print("[yellow]No usage data found. Run some agents first![/yellow]")
        return

    quota_manager = QuotaManager(storage_path=quota_path)
    optimizer = CostOptimizer(quota_manager)

    # Analyze all teams
    all_recommendations = optimizer.analyze_all_teams()

    if not all_recommendations:
        console.print("[green]✨ No optimization recommendations at this time![/green]")
        console.print("\nYour teams are running efficiently. Keep up the good work!")
        return

    # Calculate total potential savings
    total_savings = sum(
        rec.potential_savings for recs in all_recommendations.values() for rec in recs
    )

    # Summary panel
    summary = f"""
[bold]Optimization Summary[/bold]
Teams with recommendations: {len(all_recommendations)}
Total recommendations: {sum(len(recs) for recs in all_recommendations.values())}
Total potential savings: [green]${total_savings:.2f}/week[/green]
"""
    console.print(Panel(summary.strip(), title="Summary", border_style="green"))

    # Show recommendations by team
    for team, recommendations in sorted(all_recommendations.items()):
        console.print(f"\n[bold cyan]📋 {team}[/bold cyan]")

        # Create recommendations table
        table = Table(box=box.ROUNDED, show_header=True)
        table.add_column("Recommendation", style="yellow", width=40)
        table.add_column("Savings", justify="right", style="green")
        table.add_column("Effort", justify="center")
        table.add_column("Impact", justify="center")

        for rec in sorted(
            recommendations, key=lambda r: r.potential_savings, reverse=True
        ):
            # Color code effort and impact
            effort_color = {"Low": "green", "Medium": "yellow", "High": "red"}[
                rec.effort
            ]
            impact_color = {"Low": "red", "Medium": "yellow", "High": "green"}[
                rec.impact
            ]

            table.add_row(
                rec.title,
                f"${rec.potential_savings:.2f}",
                f"[{effort_color}]{rec.effort}[/{effort_color}]",
                f"[{impact_color}]{rec.impact}[/{impact_color}]",
            )

        console.print(table)

        # Show top recommendation details
        if recommendations:
            top_rec = max(recommendations, key=lambda r: r.potential_savings)
            console.print(
                Panel(
                    f"[bold]{top_rec.title}[/bold]\n\n"
                    f"{top_rec.description}\n\n"
                    f"[dim]Implementation:[/dim]\n{top_rec.implementation}",
                    title="Top Recommendation",
                    border_style="yellow",
                )
            )

    # General tips
    console.print("\n[bold green]💡 General Cost-Saving Tips[/bold green]")
    tips = [
        "• Set up automatic model fallback chains (GPT-4 → GPT-3.5 → Claude Haiku)",
        "• Implement request batching to reduce API calls",
        "• Use streaming for long responses to fail fast on errors",
        "• Cache frequently used prompts and responses",
        "• Monitor and optimize agent iteration limits",
        "• Use token counting before requests to predict costs",
        "• Implement semantic search instead of repeated LLM calls",
        "• Schedule non-urgent tasks during off-peak hours",
    ]
    for tip in tips:
        console.print(tip)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ElfAutomations Cost Optimizer")
    parser.add_argument("--team", "-t", help="Analyze specific team only")
    parser.add_argument(
        "--export", "-e", action="store_true", help="Export recommendations to file"
    )

    args = parser.parse_args()

    if args.team:
        # TODO: Implement single team analysis
        console.print("[yellow]Single team analysis not yet implemented[/yellow]")
    else:
        show_recommendations()

    if args.export:
        # TODO: Implement export functionality
        console.print("\n[yellow]Export functionality coming soon![/yellow]")


if __name__ == "__main__":
    main()
