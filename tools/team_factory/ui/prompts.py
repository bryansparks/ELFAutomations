"""
Interactive prompts for team factory.
"""

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..models import TeamMember, TeamSpecification
from ..models.team_charter import TeamCharter
from ..utils.constants import PERSONALITY_TRAITS
from .console import console, create_panel


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

        console.print(f"[yellow]Invalid choice. Please select from: {', '.join(choices)}[/yellow]")


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
    console.print("[cyan]Adding new team member...[/cyan]")

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
    console.print("[cyan]Enter responsibilities (empty line to finish):[/cyan]")
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
        console.print("[yellow]No members to remove[/yellow]")
        return spec

    member_names = [m.get("name", f"Member {i}") for i, m in enumerate(spec["members"])]
    to_remove = prompt_choice("Select member to remove", member_names)

    idx = member_names.index(to_remove)
    spec["members"].pop(idx)

    console.print(f"[cyan]Removed {to_remove}[/cyan]")
    return spec


def edit_member_interactive(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Edit a member interactively."""
    if not spec.get("members"):
        console.print("[yellow]No members to edit[/yellow]")
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
    # Check if we have an enhanced spec from LLM analysis
    if "_enhanced_spec" in data and isinstance(data["_enhanced_spec"], TeamSpecification):
        # Return the already-enhanced specification with LLM-optimized prompts
        return data["_enhanced_spec"]
    
    # Otherwise, convert member dictionaries to TeamMember objects
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
        charter=data.get("charter"),  # Include charter if present
    )


def get_team_charter() -> TeamCharter:
    """
    Capture team charter information from user.
    
    Returns:
        TeamCharter with mission, objectives, and operating principles
    """
    console.print("\n[bold cyan]Let's define your team's charter[/bold cyan]\n")
    console.print("[dim]A clear charter ensures every agent understands their purpose and how to achieve it.[/dim]\n")
    
    # Mission and vision
    mission = prompt_text(
        "Team mission statement (one sentence describing the team's core purpose)",
        default=""
    )
    
    vision = prompt_text(
        "Team vision (what does success look like for this team?)",
        default=""
    )
    
    # Objectives
    console.print("\n[cyan]Define 3-5 primary objectives for the team:[/cyan]")
    objectives = []
    for i in range(5):
        obj = prompt_text(f"Objective {i+1} (or press Enter to skip)", default="")
        if not obj:
            if i < 3:
                console.print("[yellow]Please provide at least 3 objectives[/yellow]")
                i -= 1
                continue
            else:
                break
        objectives.append(obj)
    
    # Success metrics
    console.print("\n[cyan]How will you measure success? (2-3 metrics):[/cyan]")
    metrics = []
    for i in range(3):
        metric = prompt_text(f"Success metric {i+1} (or press Enter to skip)", default="")
        if not metric and i < 2:
            console.print("[yellow]Please provide at least 2 metrics[/yellow]")
            i -= 1
            continue
        elif metric:
            metrics.append(metric)
        else:
            break
    
    # Decision making
    decision_process = prompt_choice(
        "\nDecision-making process",
        ["consensus", "hierarchical", "delegated", "data-driven"],
        default="consensus"
    )
    
    # Multi-team projects
    participates_multi_team = confirm(
        "\nWill this team participate in multi-team projects?",
        default=True
    )
    
    # Evolution settings
    console.print("\n[cyan]Team Evolution Settings:[/cyan]")
    enable_evolution = confirm(
        "Enable continuous improvement through prompt evolution?",
        default=True
    )
    
    if enable_evolution:
        improvement_frequency = prompt_choice(
            "How often should the team analyze and improve?",
            ["daily", "weekly", "manual"],
            default="daily"
        )
        
        confidence_threshold = float(prompt_text(
            "Minimum confidence for applying evolutions (0.0-1.0)",
            default="0.9"
        ))
    else:
        improvement_frequency = "manual"
        confidence_threshold = 0.9
    
    # Boundaries (optional)
    console.print("\n[cyan]Define scope boundaries (what this team does NOT do):[/cyan]")
    console.print("[dim]Press Enter to skip[/dim]")
    boundaries = []
    for i in range(3):
        boundary = prompt_text(f"Boundary {i+1}", default="")
        if boundary:
            boundaries.append(boundary)
        elif i == 0:
            break
    
    charter = TeamCharter(
        mission_statement=mission,
        vision=vision,
        primary_objectives=objectives,
        success_metrics=metrics,
        decision_making_process=decision_process,
        participates_in_multi_team_projects=participates_multi_team,
        scope_boundaries=boundaries
    )
    
    # Store evolution settings in charter for later use
    charter._evolution_settings = {
        "enable_evolution": enable_evolution,
        "improvement_frequency": improvement_frequency,
        "confidence_threshold": confidence_threshold
    }
    
    return charter


def get_team_specification() -> Optional[TeamSpecification]:
    """
    Main entry point for getting team specification from user.
    
    Returns:
        TeamSpecification or None if cancelled
    """
    # Step 1: Choose framework
    console.print("\n[bold]Which agentic framework would you like to use?[/bold]\n")
    
    framework_table = Table(show_header=True, header_style="bold magenta")
    framework_table.add_column("Framework", style="cyan")
    framework_table.add_column("Best For", style="green")
    framework_table.add_column("Key Features")
    
    framework_table.add_row(
        "CrewAI",
        "Role-based collaboration",
        "• Natural language communication\n• Simple task delegation\n• Built-in collaboration patterns",
    )
    framework_table.add_row(
        "LangGraph",
        "Complex workflows",
        "• State machine based\n• Advanced control flow\n• Conditional branching",
    )
    
    console.print(framework_table)
    
    framework = prompt_choice(
        "\nChoose framework", 
        ["CrewAI", "LangGraph"], 
        default="CrewAI"
    )
    
    # Step 2: Choose LLM provider
    console.print("\n[bold]Which LLM provider would you like to use?[/bold]")
    
    llm_table = Table(show_header=True, header_style="bold magenta")
    llm_table.add_column("Provider", style="cyan")
    llm_table.add_column("Models", style="green")
    llm_table.add_column("Best For")
    
    llm_table.add_row(
        "OpenAI",
        "GPT-4, GPT-3.5",
        "• General purpose\n• Fast responses\n• Cost effective",
    )
    llm_table.add_row(
        "Anthropic",
        "Claude 3 Opus/Sonnet",
        "• Complex reasoning\n• Long context\n• Nuanced tasks",
    )
    
    console.print(llm_table)
    
    llm_provider = prompt_choice(
        "\nChoose LLM provider",
        ["OpenAI", "Anthropic"],
        default="OpenAI"
    )
    
    # Select model based on provider
    if llm_provider == "OpenAI":
        llm_model = prompt_choice(
            "Choose model",
            ["gpt-4", "gpt-3.5-turbo"],
            default="gpt-4"
        )
    else:
        llm_model = prompt_choice(
            "Choose model",
            ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
            default="claude-3-opus-20240229"
        )
    
    # Step 3: Capture team charter FIRST
    charter = get_team_charter()
    
    # Step 4: Offer AI suggestion or manual description
    # Check if charter is well-defined (has mission, objectives, and metrics)
    charter_is_complete = (
        charter.mission_statement and 
        len(charter.primary_objectives) >= 3 and 
        len(charter.success_metrics) >= 2
    )
    
    if charter_is_complete:
        console.print("\n[bold]Team Composition Options:[/bold]")
        console.print("[green]✓ Your charter is well-defined with clear objectives and metrics![/green]")
        console.print("[dim]You can either:[/dim]\n")
        console.print("1. Let AI suggest an optimal team composition based on your objectives")
        console.print("2. Describe the team composition yourself\n")
        
        composition_choice = prompt_choice(
            "How would you like to define the team?",
            ["AI suggestion", "Manual description"],
            default="AI suggestion"
        )
    else:
        # If charter is incomplete, go straight to manual description
        console.print("\n[yellow]Note: For AI suggestions, please provide a complete charter with mission, objectives, and metrics.[/yellow]")
        composition_choice = "Manual description"
    
    if composition_choice == "AI suggestion":
        console.print("\n[cyan]AI will analyze your charter and suggest an optimal team composition...[/cyan]")
        # Create a description based on the charter for the AI to work with
        description = f"Create a team to achieve: {charter.mission_statement}. Objectives: {', '.join(charter.primary_objectives[:3])}. Success metrics: {', '.join(charter.success_metrics[:2])}"
    else:
        console.print("\n[bold]Describe your team's composition:[/bold]")
        console.print("[dim]Based on your charter, what roles and skills does this team need?[/dim]\n")
        
        description = prompt_text("Team composition description")
        if not description:
            return None
    
    # Step 5: Get department info
    console.print("\n[bold]What department/area does this team belong to?[/bold]")
    console.print("[dim]Examples: marketing, engineering, sales, operations, etc.[/dim]\n")
    
    department = prompt_text("Department", default="general")
    
    # Step 6: Organizational placement
    console.print("\n[bold]Does this team report to anyone?[/bold]")
    console.print("[dim]Leave empty for independent teams[/dim]\n")
    
    reports_to = prompt_text("Reports to (optional)", default="")
    
    # Create initial specification
    initial_spec = {
        "name": f"{department}-team",
        "description": description,
        "purpose": charter.mission_statement,  # Use charter mission as purpose
        "framework": framework,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "department": department,
        "reports_to": reports_to or None,
        "natural_language_description": description,
        "charter": charter,  # Include the full charter
        "members": []  # Will be populated by factory analysis
    }
    
    # Create team specification for LLM analysis
    from ..core.factory import TeamFactory
    factory = TeamFactory()
    
    # Create initial spec with charter and evolution settings
    evolution_settings = getattr(charter, '_evolution_settings', {})
    initial_team_spec = TeamSpecification(
        name=f"{department}-team",
        description=description,
        purpose=charter.mission_statement,
        framework=framework,
        llm_provider=llm_provider,
        llm_model=llm_model,
        department=department,
        reporting_to=reports_to or None,
        charter=charter,
        natural_language_description=description,
        members=[],  # Will be populated by LLM
        enable_evolution=evolution_settings.get('enable_evolution', True),
        enable_conversation_logging=evolution_settings.get('enable_evolution', True),  # Same as evolution
        improvement_cycle_frequency=evolution_settings.get('improvement_frequency', 'daily'),
        evolution_confidence_threshold=evolution_settings.get('confidence_threshold', 0.9)
    )
    
    # Use LLM to analyze and generate optimal team composition
    console.print("\n[cyan]Using AI to analyze team requirements and generate optimal composition...[/cyan]\n")
    
    try:
        # Analyze with LLM
        enhanced_spec = factory.analyze_request(initial_team_spec)
        
        # Convert to dict for compatibility with prompt_team_details
        initial_spec["members"] = [
            {
                "name": member.name,
                "role": member.role,
                "personality": member.personality,
                "is_manager": member.is_manager,
                "responsibilities": member.responsibilities,
                "skills": member.skills
            }
            for member in enhanced_spec.members
        ]
        
        # Store the enhanced spec for later use
        initial_spec["_enhanced_spec"] = enhanced_spec
        
    except Exception as e:
        console.print(f"[yellow]AI analysis unavailable, using template: {str(e)}[/yellow]\n")
        
        # Fallback to template-based approach
        if "executive" in department.lower() or "leadership" in description.lower():
            # Executive team
            initial_spec["members"] = [
                {"name": "ceo", "role": "Chief Executive Officer", "personality": "visionary", "is_manager": True},
                {"name": "cto", "role": "Chief Technology Officer", "personality": "analytical"},
                {"name": "cmo", "role": "Chief Marketing Officer", "personality": "creative"},
                {"name": "coo", "role": "Chief Operating Officer", "personality": "pragmatic"},
                {"name": "cfo", "role": "Chief Financial Officer", "personality": "detail_oriented"},
            ]
        elif "marketing" in department.lower():
            # Marketing team
            initial_spec["members"] = [
                {"name": "marketing_manager", "role": "Marketing Manager", "personality": "collaborative", "is_manager": True},
                {"name": "content_creator", "role": "Content Creator", "personality": "creative"},
                {"name": "social_media_manager", "role": "Social Media Manager", "personality": "enthusiastic"},
                {"name": "analyst", "role": "Marketing Analyst", "personality": "analytical"},
            ]
        elif "engineering" in department.lower() or "development" in description.lower():
            # Engineering team
            initial_spec["members"] = [
                {"name": "tech_lead", "role": "Technical Lead", "personality": "methodical", "is_manager": True},
                {"name": "senior_engineer", "role": "Senior Engineer", "personality": "analytical"},
                {"name": "backend_engineer", "role": "Backend Engineer", "personality": "detail_oriented"},
                {"name": "frontend_engineer", "role": "Frontend Engineer", "personality": "creative"},
                {"name": "qa_engineer", "role": "QA Engineer", "personality": "skeptical"},
            ]
        else:
            # Generic team
            initial_spec["members"] = [
                {"name": "team_lead", "role": "Team Lead", "personality": "collaborative", "is_manager": True},
                {"name": "specialist_1", "role": "Specialist", "personality": "analytical"},
                {"name": "specialist_2", "role": "Specialist", "personality": "creative"},
                {"name": "coordinator", "role": "Coordinator", "personality": "pragmatic"},
            ]
    
    # Let user review and modify
    return prompt_team_details(initial_spec)
