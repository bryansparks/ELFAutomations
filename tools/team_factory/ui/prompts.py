"""
Interactive prompts for team factory.
"""

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..models import TeamMember, TeamSpecification
from ..utils.constants import PERSONALITY_TRAITS
from .console import console, create_panel, print_info, print_warning


def prompt_text(message: str, default: str = "", password: bool = False) -> str:
    """
    Prompt for text input.

    Args:
        message: Prompt message
        default: Default value
        password: Whether to hide input

    Returns:
        User input
    """
    return Prompt.ask(message, default=default, password=password, console=console)


def prompt_choice(
    message: str, choices: List[str], default: Optional[str] = None
) -> str:
    """
    Prompt for choice from list.

    Args:
        message: Prompt message
        choices: List of choices
        default: Default choice

    Returns:
        Selected choice
    """
    if default and default not in choices:
        default = None

    # Display choices
    for i, choice in enumerate(choices, 1):
        console.print(f"{i}. {choice}")

    while True:
        response = Prompt.ask(message, default=default, console=console)

        # Check if numeric
        if response.isdigit():
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]

        # Check if exact match
        if response in choices:
            return response

        # Check if partial match
        matches = [c for c in choices if c.lower().startswith(response.lower())]
        if len(matches) == 1:
            return matches[0]

        print_warning(f"Invalid choice. Please select from: {', '.join(choices)}")


def confirm(message: str, default: bool = False) -> bool:
    """
    Prompt for confirmation.

    Args:
        message: Confirmation message
        default: Default value

    Returns:
        True if confirmed
    """
    return Confirm.ask(message, default=default, console=console)


def prompt_team_details(initial_spec: Dict[str, Any]) -> Optional[TeamSpecification]:
    """
    Interactively prompt for team details and modifications.

    Args:
        initial_spec: Initial team specification from LLM

    Returns:
        Final TeamSpecification or None if cancelled
    """
    console.print(
        create_panel(
            f"## Suggested Team: {initial_spec.get('name', 'Unnamed Team')}\n\n"
            f"**Purpose**: {initial_spec.get('purpose', 'No purpose specified')}\n\n"
            f"**Department**: {initial_spec.get('department', 'Unknown')}\n\n"
            f"**Framework**: {initial_spec.get('framework', 'CrewAI')}",
            title="Team Suggestion",
            style="green",
        )
    )

    # Display suggested members
    if "members" in initial_spec:
        table = Table(title="Suggested Team Members", show_lines=True)
        table.add_column("Name", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Personality", style="yellow")

        for member in initial_spec["members"]:
            table.add_row(
                member.get("name", "Unknown"),
                member.get("role", "Unknown"),
                member.get("personality", "collaborator"),
            )

        console.print(table)

    # Confirm or modify
    if not confirm(
        "Would you like to proceed with this team composition?", default=True
    ):
        if not confirm("Would you like to modify the team?", default=True):
            return None

        # Interactive modification
        initial_spec = modify_team_interactive(initial_spec)

    # Convert to TeamSpecification
    return dict_to_team_spec(initial_spec)


def modify_team_interactive(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interactively modify team specification.

    Args:
        spec: Current specification

    Returns:
        Modified specification
    """
    while True:
        console.print("\n[cyan]What would you like to modify?[/cyan]")
        action = prompt_choice(
            "Select action",
            [
                "Add member",
                "Remove member",
                "Edit member",
                "Change team name",
                "Change framework",
                "Change department",
                "Done",
            ],
            default="Done",
        )

        if action == "Done":
            break
        elif action == "Add member":
            spec = add_member_interactive(spec)
        elif action == "Remove member":
            spec = remove_member_interactive(spec)
        elif action == "Edit member":
            spec = edit_member_interactive(spec)
        elif action == "Change team name":
            spec["name"] = prompt_text(
                "Enter new team name", default=spec.get("name", "")
            )
        elif action == "Change framework":
            spec["framework"] = prompt_choice(
                "Select framework", ["CrewAI", "LangGraph"]
            )
        elif action == "Change department":
            spec["department"] = prompt_text(
                "Enter department", default=spec.get("department", "")
            )

    return spec


def add_member_interactive(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new member interactively."""
    print_info("Adding new team member...")

    member = {
        "name": prompt_text("Member name"),
        "role": prompt_text("Member role"),
        "responsibilities": [],
        "personality": prompt_choice(
            "Select personality trait",
            list(PERSONALITY_TRAITS.keys()),
            default="collaborator",
        ),
    }

    # Add responsibilities
    print_info("Enter responsibilities (empty line to finish):")
    while True:
        resp = prompt_text("Responsibility", default="")
        if not resp:
            break
        member["responsibilities"].append(resp)

    if "members" not in spec:
        spec["members"] = []
    spec["members"].append(member)

    return spec


def remove_member_interactive(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Remove a member interactively."""
    if not spec.get("members"):
        print_warning("No members to remove")
        return spec

    member_names = [m.get("name", f"Member {i}") for i, m in enumerate(spec["members"])]
    to_remove = prompt_choice("Select member to remove", member_names)

    idx = member_names.index(to_remove)
    spec["members"].pop(idx)

    print_info(f"Removed {to_remove}")
    return spec


def edit_member_interactive(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Edit a member interactively."""
    if not spec.get("members"):
        print_warning("No members to edit")
        return spec

    member_names = [m.get("name", f"Member {i}") for i, m in enumerate(spec["members"])]
    to_edit = prompt_choice("Select member to edit", member_names)

    idx = member_names.index(to_edit)
    member = spec["members"][idx]

    # Edit fields
    member["name"] = prompt_text("Member name", default=member.get("name", ""))
    member["role"] = prompt_text("Member role", default=member.get("role", ""))
    member["personality"] = prompt_choice(
        "Select personality trait",
        list(PERSONALITY_TRAITS.keys()),
        default=member.get("personality", "collaborator"),
    )

    return spec


def display_team_summary(team_spec: TeamSpecification):
    """
    Display final team summary.

    Args:
        team_spec: Final team specification
    """
    from .console import display_team_structure

    console.print("\n")
    console.print(
        create_panel(
            "## Team Created Successfully! 🎉\n\n"
            f"Your team **{team_spec.name}** has been generated with {len(team_spec.members)} members.",
            title="Success",
            style="green",
        )
    )

    display_team_structure(team_spec)

    if team_spec.sub_team_recommendations:
        console.print("\n")
        console.print(
            create_panel(
                "## Recommended Sub-Teams\n\n"
                "Based on your team's size and responsibilities, consider creating these sub-teams:",
                title="Recommendations",
                style="yellow",
            )
        )

        for rec in team_spec.sub_team_recommendations:
            console.print(f"\n[cyan]{rec.name}[/cyan]")
            console.print(f"  Purpose: {rec.purpose}")
            console.print(f"  Rationale: {rec.rationale}")


def dict_to_team_spec(data: Dict[str, Any]) -> TeamSpecification:
    """Convert dictionary to TeamSpecification."""
    # Convert member dictionaries to TeamMember objects
    members = []
    for i, member_data in enumerate(data.get("members", [])):
        member = TeamMember(
            name=member_data.get("name", f"Member {i+1}"),
            role=member_data.get("role", "Team Member"),
            responsibilities=member_data.get("responsibilities", []),
            skills=member_data.get("skills", []),
            personality=member_data.get("personality", "collaborator"),
            is_manager=member_data.get(
                "is_manager", i == 0
            ),  # First member is manager by default
        )
        members.append(member)

    # Create specification
    return TeamSpecification(
        name=data.get("name", "Unnamed Team"),
        description=data.get("description", ""),
        purpose=data.get("purpose", ""),
        framework=data.get("framework", "CrewAI"),
        llm_provider=data.get("llm_provider", "OpenAI"),
        llm_model=data.get("llm_model", "gpt-4"),
        department=data.get("department", "general"),
        members=members,
        reporting_to=data.get("reports_to"),
        natural_language_description=data.get("natural_language_description", ""),
    )
