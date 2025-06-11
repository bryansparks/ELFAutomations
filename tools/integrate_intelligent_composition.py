#!/usr/bin/env python3
"""
Integration guide for adding intelligent team composition to team factory
"""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def show_integration_approach():
    """Show how intelligent composition integrates with team factory"""

    integration_code = '''
# In team_factory.py, modify the create_team method:

def create_team(self):
    """Create a new team with intelligent composition"""

    self.console.print(Panel.fit(
        "🚀 [bold]ElfAutomations Team Factory[/bold] 🚀\\n"
        "Natural language team creation with AI-powered composition",
        border_style="cyan"
    ))

    # Get team request
    self.console.print("\\n[bold]Step 1: Describe Your Team Need[/bold]")
    self.console.print("[dim]Be specific about purpose, goals, and context[/dim]\\n")

    team_request = Prompt.ask(
        "What kind of team do you need?",
        default="A team to improve our customer experience"
    )

    # NEW: Use intelligent composition
    if Confirm.ask("\\nWould you like AI to propose the optimal team composition?", default=True):
        # Initialize composer
        from intelligent_team_composer import IntelligentTeamComposer
        composer = IntelligentTeamComposer()

        # Get organizational context
        context = self._gather_organizational_context()

        # Generate proposal
        self.console.print("\\n[bold cyan]🤖 Analyzing requirements and designing optimal team...[/bold cyan]")
        proposal = composer.propose_team_composition(team_request, context)

        # Display proposal
        composer.display_proposal(proposal)

        # Allow refinement
        if Confirm.ask("\\nWould you like to refine this composition?"):
            proposal = composer.refine_proposal_interactively(proposal)

        # Convert proposal to team specification
        team_spec = self._convert_proposal_to_spec(proposal)

    else:
        # Original flow - manual composition
        team_spec = self._manual_team_composition(team_request)

    # Continue with enhanced prompts, code generation, etc.
    return self._generate_team_with_enhancements(team_spec)

def _gather_organizational_context(self) -> Dict:
    """Gather context about existing organization"""

    context = {
        "existing_teams": [],
        "business_stage": "Growth",
        "industry": "Technology"
    }

    # Get existing teams from registry if available
    if REGISTRY_AVAILABLE:
        try:
            teams = self._get_existing_teams_from_registry()
            context["existing_teams"] = [t["name"] for t in teams]
        except:
            pass

    # Could ask for more context
    if Confirm.ask("\\nProvide additional organizational context?"):
        context["business_stage"] = Prompt.ask(
            "Business stage",
            choices=["Startup", "Growth", "Scale-up", "Enterprise"],
            default="Growth"
        )
        context["industry"] = Prompt.ask("Industry", default="Technology")

    return context

def _convert_proposal_to_spec(self, proposal: TeamCompositionProposal) -> TeamSpecification:
    """Convert AI proposal to team specification"""

    # Create team members from proposal
    members = []
    for proposed_member in proposal.members:
        # Determine communication patterns
        communicates_with = self._infer_communication_patterns(
            proposed_member,
            proposal.members
        )

        # Check if this is a manager role
        is_manager = any(term in proposed_member.role.lower()
                        for term in ["lead", "manager", "director"])

        member = TeamMember(
            role=proposed_member.role,
            responsibilities=proposed_member.key_responsibilities,
            skills=proposed_member.required_skills,
            system_prompt=f"""You are the {proposed_member.role}.

Purpose: {proposed_member.purpose}

Key Traits: {', '.join(proposed_member.personality_traits)}
Interaction Style: {proposed_member.interaction_style}

Your success depends on: {proposed_member.rationale}""",
            communicates_with=communicates_with,
            manages_teams=[] if not is_manager else ["subordinate-teams"]
        )

        members.append(member)

    # Build communication pattern
    communication_pattern = {}
    for member in members:
        communication_pattern[member.role] = member.communicates_with

    # Determine framework
    framework = self._suggest_framework_for_team(proposal)

    return TeamSpecification(
        name=proposal.team_name,
        purpose=proposal.team_purpose,
        framework=framework,
        llm_provider=self._select_llm_provider(),
        llm_model=self._select_llm_model(),
        department=self._determine_department(proposal.team_name),
        members=members,
        communication_pattern=communication_pattern,
        size_validation=self._validate_team_size(len(members)),
        natural_language_description=proposal.team_purpose
    )

def _infer_communication_patterns(self, member: ProposedMember,
                                all_members: List[ProposedMember]) -> List[str]:
    """Infer who this member should communicate with"""

    communications = []

    # Leaders communicate with everyone
    if any(term in member.role.lower() for term in ["lead", "manager"]):
        communications = [m.role for m in all_members if m.role != member.role]

    # Specialists communicate with leaders and related roles
    else:
        # Always communicate with leaders
        for other in all_members:
            if any(term in other.role.lower() for term in ["lead", "manager"]):
                communications.append(other.role)

        # Communicate with complementary roles
        for other in all_members:
            if other.role != member.role:
                # Check for complementary skills
                shared_skills = set(member.required_skills) & set(other.required_skills)
                if shared_skills:
                    communications.append(other.role)

    return list(set(communications))  # Remove duplicates

def _suggest_framework_for_team(self, proposal: TeamCompositionProposal) -> str:
    """Suggest best framework based on team composition"""

    # Teams with complex workflows benefit from LangGraph
    if any(word in proposal.team_dynamics.lower()
           for word in ["complex", "workflow", "state", "process"]):
        return "LangGraph"

    # Creative, collaborative teams work well with CrewAI
    if any(word in proposal.team_dynamics.lower()
           for word in ["creative", "collaborative", "innovative"]):
        return "CrewAI"

    # Default to CrewAI for natural collaboration
    return "CrewAI"
'''

    return integration_code


def show_benefits():
    """Show the benefits of intelligent composition"""

    benefits = Panel(
        """[bold cyan]Benefits of Intelligent Team Composition:[/bold cyan]

[green]1. Optimal Team Design[/green]
   • AI considers purpose, context, and proven patterns
   • Automatically includes essential roles (including skeptics!)
   • Balances skills and personalities

[green]2. Faster Team Creation[/green]
   • No need to manually specify each role
   • AI proposes complete team in seconds
   • Interactive refinement if needed

[green]3. Better Outcomes[/green]
   • Teams designed with success factors in mind
   • Potential challenges identified upfront
   • Clear role definitions and interactions

[green]4. Learning System[/green]
   • AI learns from successful team patterns
   • Incorporates organizational context
   • Evolves recommendations over time

[green]5. Flexibility[/green]
   • Accept AI proposal as-is
   • Refine interactively
   • Or fall back to manual composition""",
        title="Why Use Intelligent Composition?",
        border_style="green",
    )

    return benefits


def show_example_flow():
    """Show example interaction flow"""

    example = """
# Example User Flow:

User: "I need a team to reduce customer churn through better engagement"

AI Analysis:
- Purpose: Customer retention
- Pattern: Customer-facing team with analytics
- Key needs: Understanding, action, measurement

AI Proposal:
1. Customer Success Manager - Owns retention strategy
2. Churn Analyst - Identifies at-risk customers
3. Engagement Specialist - Creates retention programs
4. Customer Advocate - Voice of the customer
5. Retention Skeptic - Challenges assumptions

User: "Looks good, but add a technical integration role"

AI: *Adds Integration Specialist to handle technical touchpoints*

Result: Perfectly balanced 6-person team ready for enhanced prompts and code generation!
"""

    return example


def create_minimal_integration():
    """Create minimal code to add to team factory"""

    minimal_code = '''
# Add this method to TeamFactory class:

def propose_team_composition(self, request: str) -> List[Dict]:
    """Get AI-proposed team composition"""

    prompt = f"""
    Propose optimal team composition for: {request}

    Consider:
    - Two-pizza rule (3-7 members, 5 optimal)
    - Include diverse perspectives
    - Add a constructive skeptic if 5+ members
    - Clear, non-overlapping roles

    For each member provide:
    - Role name
    - Key responsibilities (3-4)
    - Required skills
    - Who they communicate with

    Format: JSON list
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in team design."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        # Fallback to template
        return self._get_template_team(request)
'''

    return minimal_code


if __name__ == "__main__":
    console.print("=" * 60)
    console.print("[bold]INTELLIGENT TEAM COMPOSITION INTEGRATION[/bold]")
    console.print("=" * 60)

    # Show benefits
    console.print(show_benefits())

    # Show integration approach
    console.print("\n[bold]Integration Approach:[/bold]")
    syntax = Syntax(
        show_integration_approach(), "python", theme="monokai", line_numbers=True
    )
    console.print(Panel(syntax, title="Full Integration", border_style="blue"))

    # Show minimal integration
    console.print("\n[bold]Minimal Integration Option:[/bold]")
    minimal_syntax = Syntax(
        create_minimal_integration(), "python", theme="monokai", line_numbers=True
    )
    console.print(Panel(minimal_syntax, title="Quick Start", border_style="yellow"))

    # Show example flow
    console.print("\n[bold]Example Flow:[/bold]")
    console.print(
        Panel(show_example_flow(), title="User Experience", border_style="green")
    )

    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Add IntelligentTeamComposer import to team_factory.py")
    console.print("2. Modify create_team() to offer AI composition")
    console.print("3. Test with various team requests")
    console.print("4. Refine patterns based on outcomes")

    console.print(
        "\n[bold green]✨ Let AI design optimal teams from the start![/bold green]"
    )
