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


class TeamFactoryConsole:
    """Console UI for team factory operations."""
    
    def __init__(self):
        """Initialize console."""
        self.console = console
    
    def show_progress(self, message: str) -> None:
        """Show a progress message."""
        self.console.print(f"[cyan]→[/cyan] {message}")
    
    def show_success(self, message: str) -> None:
        """Show a success message."""
        self.console.print(f"[green]✓[/green] {message}")
    
    def show_error(self, message: str) -> None:
        """Show an error message."""
        self.console.print(f"[red]✗[/red] {message}")
    
    def show_info(self, message: str) -> None:
        """Show an informational message."""
        self.console.print(f"[blue]ℹ[/blue] {message}")
    
    def show_welcome(self) -> None:
        """Show welcome banner."""
        welcome_text = """
# 🤖 ElfAutomations Team Factory

Create production-ready AI teams with:
- 🧠 CrewAI or LangGraph frameworks
- 💬 Natural language team design
- 🔄 A2A inter-team communication
- 📊 Monitoring and observability
- 🚀 K8s deployment ready
"""
        panel = Panel(
            Markdown(welcome_text),
            title="Welcome to Team Factory",
            border_style="bright_blue"
        )
        self.console.print(panel)
    
    def get_team_requirements(self):
        """Get team requirements from user interactively."""
        from ..ui.prompts import get_team_specification
        return get_team_specification()
    
    def show_next_steps(self, team_name: str) -> None:
        """Show next steps after team creation."""
        next_steps = f"""
## ✅ Team '{team_name}' created successfully!

### 📁 Generated Files:
- `teams/{team_name}/` - Team implementation
- `k8s/teams/{team_name}/` - Kubernetes manifests

### 🚀 Next Steps:

1. **Build Docker Image:**
   ```bash
   cd teams/{team_name}
   docker build -t elf-automations/{team_name}:latest .
   ```

2. **Transfer to ArgoCD Machine:**
   ```bash
   ./scripts/transfer-docker-images-ssh.sh
   ```

3. **Deploy via GitOps:**
   ```bash
   git add -A
   git commit -m "Deploy {team_name}"
   git push
   ```

4. **Monitor Deployment:**
   ```bash
   kubectl get pods -n elf-teams
   kubectl logs -n elf-teams -l team={team_name}
   ```
"""
        panel = Panel(
            Markdown(next_steps),
            title="Next Steps",
            border_style="green"
        )
        self.console.print(panel)


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
