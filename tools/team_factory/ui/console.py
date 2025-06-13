"""
Rich console components and utilities.
"""

from typing import Any, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Global console instance
console = Console()


def create_panel(
    content: str,
    title: str = "",
    subtitle: str = "",
    style: str = "blue",
    expand: bool = True,
) -> Panel:
    """
    Create a styled panel.

    Args:
        content: Panel content (can include markdown)
        title: Panel title
        subtitle: Panel subtitle
        style: Panel border style
        expand: Whether to expand to full width

    Returns:
        Rich Panel object
    """
    return Panel(
        Markdown(content) if "##" in content or "**" in content else content,
        title=title,
        subtitle=subtitle,
        style=style,
        expand=expand,
    )


def create_table(
    title: str = "", show_header: bool = True, show_lines: bool = False
) -> Table:
    """
    Create a styled table.

    Args:
        title: Table title
        show_header: Whether to show header row
        show_lines: Whether to show row lines

    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=show_header, show_lines=show_lines)
    return table


def print_success(message: str):
    """Print a success message in green."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Print an error message in red."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str):
    """Print a warning message in yellow."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(message: str):
    """Print an info message in blue."""
    console.print(f"[blue]ℹ[/blue] {message}")


def create_progress() -> Progress:
    """Create a progress indicator."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def display_team_structure(team_spec: Any):
    """
    Display team structure in a formatted table.

    Args:
        team_spec: TeamSpecification object
    """
    table = create_table(title=f"Team: {team_spec.name}", show_lines=True)

    # Add columns
    table.add_column("Member", style="cyan", no_wrap=True)
    table.add_column("Role", style="magenta")
    table.add_column("Responsibilities", style="green")
    table.add_column("Personality", style="yellow")
    table.add_column("Type", style="blue")

    # Add rows
    for member in team_spec.members:
        responsibilities = "\n".join(f"• {r}" for r in member.responsibilities[:3])
        member_type = "Manager" if member.is_manager else "Member"
        if member.is_skeptic:
            member_type += " (Skeptic)"

        table.add_row(
            member.name, member.role, responsibilities, member.personality, member_type
        )

    console.print(table)

    # Show team metadata
    metadata = create_table(title="Team Configuration", show_header=False)
    metadata.add_column("Property", style="cyan")
    metadata.add_column("Value", style="white")

    metadata.add_row("Framework", team_spec.framework)
    metadata.add_row(
        "LLM Provider", f"{team_spec.llm_provider} ({team_spec.llm_model})"
    )
    metadata.add_row("Department", team_spec.department)
    metadata.add_row("Reports To", team_spec.reporting_to or "Independent")
    metadata.add_row("Team Size", team_spec.size_validation)

    console.print(metadata)
