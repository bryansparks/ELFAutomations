#!/usr/bin/env python3
"""
Team Factory - Natural language team creation tool for ElfAutomations

This tool:
1. Accepts natural language team descriptions
2. Suggests team composition based on best practices
3. Generates prompts for each team member
4. Defines communication patterns within the team
5. Supports both CrewAI and LangGraph frameworks
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Using OpenAI for natural language understanding
import openai
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Import prompt template system
try:
    from prompt_template_system import PromptTemplateSystem

    PROMPT_TEMPLATES_AVAILABLE = True
except ImportError:
    PROMPT_TEMPLATES_AVAILABLE = False
    print("Warning: Prompt template system not available. Using basic prompts.")

# Import Supabase utilities
try:
    from utils.supabase_client import get_supabase_client

    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False
    print("Warning: Supabase client not available. Team Registry features disabled.")

console = Console()


@dataclass
class TeamMember:
    """Represents a single team member"""

    role: str
    responsibilities: List[str]
    skills: List[str]
    system_prompt: str
    communicates_with: List[str] = field(
        default_factory=list
    )  # Intra-team communication
    manages_teams: List[str] = field(
        default_factory=list
    )  # Inter-team A2A communication
    personality_traits: List[str] = field(
        default_factory=list
    )  # Personality traits like "skeptic", "optimist", etc.


@dataclass
class TeamSpecification:
    """Complete team specification"""

    name: str
    purpose: str
    framework: str  # CrewAI or LangGraph
    llm_provider: str  # OpenAI or Anthropic
    llm_model: str  # Specific model to use
    department: str
    members: List[TeamMember]
    communication_pattern: Dict[str, List[str]]
    size_validation: str
    natural_language_description: str


class TeamFactory:
    """Factory for creating teams from natural language descriptions"""

    def __init__(self):
        self.console = console
        self.project_root = Path(__file__).parent.parent
        self.teams_dir = self.project_root / "teams"
        self.teams_dir.mkdir(exist_ok=True)

        # Team size guidelines from AI Team Size Patterns document
        self.MIN_TEAM_SIZE = 2
        self.OPTIMAL_TEAM_SIZE = 5
        self.MAX_TEAM_SIZE = 7

        # Personality trait definitions and their prompt modifiers
        self.PERSONALITY_TRAITS = {
            "skeptic": {
                "description": "Constructively challenges ideas to strengthen them",
                "prompt_modifier": "You have a skeptical nature and are skilled at identifying potential problems, edge cases, and risks. You ask probing questions like 'What happens if...?' and 'Have we considered...?' Your goal is to strengthen proposals through constructive challenge, not to be negative. You're particularly good at spotting failure modes, questioning assumptions, and ensuring robustness.",
            },
            "optimist": {
                "description": "Focuses on possibilities and positive outcomes",
                "prompt_modifier": "You have an optimistic outlook and excel at seeing opportunities and potential. You help the team stay motivated and focused on what's possible, while still being realistic about challenges.",
            },
            "detail-oriented": {
                "description": "Ensures nothing is overlooked",
                "prompt_modifier": "You are extremely detail-oriented and thorough. You excel at catching small issues before they become big problems, ensuring documentation is complete, and maintaining high quality standards.",
            },
            "innovator": {
                "description": "Brings creative solutions and new perspectives",
                "prompt_modifier": "You are an innovative thinker who enjoys exploring unconventional solutions. You bring fresh perspectives and aren't afraid to suggest radical new approaches when appropriate.",
            },
            "pragmatist": {
                "description": "Focuses on practical, implementable solutions",
                "prompt_modifier": "You are pragmatic and focused on what can actually be implemented given real-world constraints. You balance idealism with practicality and help ensure solutions are feasible.",
            },
            "collaborator": {
                "description": "Excels at bringing team members together",
                "prompt_modifier": "You are a natural collaborator who excels at facilitating team discussions, ensuring everyone's voice is heard, and finding common ground between different viewpoints.",
            },
            "analyzer": {
                "description": "Provides data-driven insights and logical analysis",
                "prompt_modifier": "You are analytical and data-driven, always looking for evidence to support decisions. You excel at breaking down complex problems, identifying patterns, and providing logical analysis.",
            },
        }

        # Initialize prompt template system if available
        if PROMPT_TEMPLATES_AVAILABLE:
            self.prompt_system = PromptTemplateSystem()
        else:
            self.prompt_system = None

        # Executive to subordinate team mappings
        self.EXECUTIVE_TEAM_MAPPINGS = {
            "Chief Executive Officer": [
                "executive-team"
            ],  # CEO manages all through other executives
            "Chief Technology Officer": ["engineering-team", "qa-team", "devops-team"],
            "Chief Marketing Officer": ["marketing-team", "content-team", "brand-team"],
            "Chief Operations Officer": [
                "operations-team",
                "hr-team",
                "facilities-team",
            ],
            "Chief Financial Officer": [
                "finance-team",
                "accounting-team",
                "budget-team",
            ],
            "Chief Sales Officer": ["sales-team", "business-development-team"],
            "Chief Product Officer": ["product-team", "design-team", "research-team"],
        }

    def create_team(self):
        """Main entry point for team creation"""
        self.console.print(
            "\n[bold cyan]🏭 Team Factory - Natural Language Team Creation[/bold cyan]\n"
        )

        # Step 1: Get framework choice upfront
        framework = self._choose_framework()

        # Step 2: Get LLM provider choice
        llm_provider, llm_model = self._choose_llm_provider()

        # Step 3: Get natural language description
        description = self._get_team_description()

        # Step 4: Get organizational placement
        department, subteam, reports_to = self._get_organizational_placement()

        # Step 5: Analyze and suggest team composition
        team_spec = self._analyze_team_requirements(
            description, framework, llm_provider, llm_model
        )

        # Update team spec with organizational info
        team_spec.department = department
        if subteam:
            team_spec.name = f"{department}-{subteam}-team"
        else:
            team_spec.name = f"{department}-team"

        # Configure manager's A2A reporting if needed
        if reports_to and team_spec.members:
            # Find the manager role (usually first member or one with "Manager" in title)
            manager = None
            for member in team_spec.members:
                if "Manager" in member.role or "Lead" in member.role:
                    manager = member
                    break
            if not manager:
                manager = team_spec.members[0]  # Default to first member

            # Configure A2A reporting
            if reports_to in self.EXECUTIVE_TEAM_MAPPINGS:
                # Reporting to an executive who manages teams
                manager.manages_teams = (
                    []
                )  # Will be configured based on user input later
            # Update system prompt to include reporting structure
            manager.system_prompt += f" You report to {reports_to} via A2A protocol for inter-team communication."

        # Step 6: Review and refine team composition
        team_spec = self._review_and_refine_team(team_spec)

        # Step 7: Generate team configuration files
        self._generate_team_files(team_spec)

        # Step 8: Register team in Team Registry
        if self._register_team_in_registry(team_spec):
            self.console.print(
                "\n[bold green]✅ Team created and registered successfully![/bold green]"
            )
        else:
            self.console.print(
                "\n[bold yellow]⚠️  Team created but registry registration failed[/bold yellow]"
            )
            self.console.print(
                "[dim]The team files were generated but may need manual registry update[/dim]"
            )

    def _choose_framework(self) -> str:
        """Let user choose the agentic framework"""
        self.console.print(
            "[bold]Which agentic framework would you like to use?[/bold]\n"
        )

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

        self.console.print(framework_table)

        choice = Prompt.ask(
            "\nChoose framework", choices=["CrewAI", "LangGraph"], default="CrewAI"
        )

        return choice

    def _choose_llm_provider(self) -> Tuple[str, str]:
        """Let user choose the LLM provider and model"""
        self.console.print("\n[bold]Which LLM provider would you like to use?[/bold]\n")

        llm_table = Table(show_header=True, header_style="bold magenta")
        llm_table.add_column("Provider", style="cyan")
        llm_table.add_column("Models", style="green")
        llm_table.add_column("Best For")

        llm_table.add_row(
            "OpenAI",
            "• GPT-4\n• GPT-4 Turbo\n• GPT-3.5 Turbo",
            "• General purpose\n• Wide tool support\n• Fast responses",
        )
        llm_table.add_row(
            "Anthropic",
            "• Claude 3 Opus\n• Claude 3 Sonnet\n• Claude 3 Haiku",
            "• Complex reasoning\n• Detailed analysis\n• Safety focused",
        )

        self.console.print(llm_table)

        provider = Prompt.ask(
            "\nChoose provider", choices=["OpenAI", "Anthropic"], default="OpenAI"
        )

        # Choose specific model based on provider
        if provider == "OpenAI":
            model = Prompt.ask(
                "\nChoose OpenAI model",
                choices=["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"],
                default="gpt-4",
            )
        else:  # Anthropic
            model = Prompt.ask(
                "\nChoose Anthropic model",
                choices=[
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                ],
                default="claude-3-opus-20240229",
            )

        self.console.print(f"\n[green]Selected: {provider} - {model}[/green]")
        return provider, model

    def _get_team_description(self) -> str:
        """Get natural language description of the team"""
        self.console.print("\n[bold]Describe the team you want to create:[/bold]")
        self.console.print(
            "[dim]Example: I need a marketing team that can create content, manage social media, and run campaigns. They should be able to analyze performance and adjust strategies.[/dim]\n"
        )

        # Show personality traits if user wants
        if Confirm.ask(
            "Would you like to see available personality traits?", default=False
        ):
            self._show_personality_traits()

        description = Prompt.ask("Team description")
        return description

    def _get_organizational_placement(self) -> Tuple[str, Optional[str], Optional[str]]:
        """Get where this team fits in the organization"""
        self.console.print(
            "\n[bold]Where does this team fit in your organization?[/bold]"
        )
        self.console.print(
            "[dim]Use dot notation: department.subteam (e.g., marketing.socialmedia, engineering.backend, executive)[/dim]"
        )
        self.console.print("[dim]Examples:[/dim]")
        self.console.print("[dim]  - executive (top-level executive team)[/dim]")
        self.console.print("[dim]  - marketing (department-level team)[/dim]")
        self.console.print(
            "[dim]  - marketing.socialmedia (sub-team under marketing)[/dim]"
        )
        self.console.print(
            "[dim]  - engineering.platform.infrastructure (nested sub-teams)[/dim]\n"
        )

        placement = Prompt.ask("Organizational placement", default="standalone")

        # Parse the placement
        parts = placement.split(".")
        department = parts[0]
        subteam = parts[1] if len(parts) > 1 else None
        reports_to = None

        # Determine reporting structure
        if placement == "standalone":
            reports_to = None
        elif placement == "executive":
            reports_to = None  # Executive team doesn't report up
        elif subteam:
            # Sub-team reports to department manager
            reports_to = f"{department}-team"  # e.g., marketing.socialmedia reports to marketing-team
        else:
            # Department team reports to executive
            if department == "marketing":
                reports_to = "Chief Marketing Officer"
            elif department == "engineering":
                reports_to = "Chief Technology Officer"
            elif department == "sales":
                reports_to = "Chief Sales Officer"
            elif department == "operations":
                reports_to = "Chief Operations Officer"
            elif department == "finance":
                reports_to = "Chief Financial Officer"
            else:
                # Ask for clarification
                self.console.print(
                    f"\n[yellow]Which executive does the {department} team report to?[/yellow]"
                )
                reports_to = Prompt.ask("Reports to", default="Chief Executive Officer")

        return department, subteam, reports_to

    def _show_personality_traits(self):
        """Display available personality traits to the user"""
        self.console.print("\n[bold cyan]Available Personality Traits:[/bold cyan]\n")

        traits_table = Table(show_header=True, header_style="bold magenta")
        traits_table.add_column("Trait", style="cyan", width=20)
        traits_table.add_column("Description", style="white", width=60)

        for trait, info in self.PERSONALITY_TRAITS.items():
            traits_table.add_row(trait.capitalize(), info["description"])

        self.console.print(traits_table)
        self.console.print(
            "\n[dim]Note: Include these traits in your team description to apply them to team members.[/dim]"
        )
        self.console.print(
            "[dim]Example: 'I need a marketing team with a skeptical analytics expert who challenges assumptions...'[/dim]\n"
        )

    def _analyze_team_requirements(
        self, description: str, framework: str, llm_provider: str, llm_model: str
    ) -> TeamSpecification:
        """Analyze the description and suggest team composition"""
        self.console.print(
            "\n[bold yellow]🤔 Analyzing team requirements...[/bold yellow]"
        )

        # This is where we'd use AI to analyze the description
        # For now, using a template-based approach
        analysis_prompt = f"""
        Analyze this team description and suggest a team composition:

        Description: {description}
        Framework: {framework}

        Guidelines:
        - Team size should be 3-7 members (5 is optimal)
        - Each member should have a clear role and responsibilities
        - Define who each member communicates with
        - Follow the Two-Pizza Rule (if you can't feed the team with 2 pizzas, it's too big)

        Return a structured team specification with:
        1. Team name and purpose
        2. List of team members with roles
        3. Each member's key responsibilities
        4. Communication patterns (who talks to whom)
        5. System prompts for each member
        """

        # Simulate AI response (in production, this would call OpenAI/Claude)
        suggested_team = self._generate_team_suggestion(
            description, framework, llm_provider, llm_model
        )

        return suggested_team

    def _generate_team_suggestion(
        self,
        description: str,
        framework: str,
        llm_provider: str = "OpenAI",
        llm_model: str = "gpt-4",
    ) -> TeamSpecification:
        """Generate team suggestion based on description"""
        # This is a simplified implementation
        # In production, this would use AI to generate suggestions

        # Parse keywords from description
        keywords = description.lower()

        # Determine department
        if "marketing" in keywords:
            department = "marketing"
            team_name = "marketing-team"
        elif "sales" in keywords:
            department = "sales"
            team_name = "sales-team"
        elif "engineering" in keywords or "development" in keywords:
            department = "engineering"
            team_name = "engineering-team"
        elif "executive" in keywords or "leadership" in keywords:
            department = "executive"
            team_name = "executive-team"
        else:
            department = "general"
            team_name = "custom-team"

        # Create sample team based on department
        if department == "marketing":
            members = [
                TeamMember(
                    role="Marketing Manager",
                    responsibilities=[
                        "Develop marketing strategy",
                        "Coordinate team activities",
                        "Report to CMO via A2A",
                        "Manage sales lead campaigns",
                        "Oversee public image initiatives",
                    ],
                    skills=[
                        "Strategic planning",
                        "Team leadership",
                        "Analytics",
                        "Campaign management",
                    ],
                    system_prompt="You are the Marketing Manager responsible for developing and executing marketing strategies including sales lead campaigns, social media efforts, and public image management. You coordinate with your team to ensure campaigns are effective and aligned with company goals. You report directly to the CMO through A2A protocol.",
                    communicates_with=[
                        "Content Creator",
                        "Social Media Manager",
                        "Analytics Expert",
                    ],
                    manages_teams=[
                        "social-media-team",
                        "content-team",
                    ],  # Can delegate to subordinate teams
                ),
                TeamMember(
                    role="Content Creator",
                    responsibilities=[
                        "Create blog posts and articles",
                        "Develop marketing materials",
                        "Maintain content calendar",
                        "Manage website content",
                        "Ensure brand consistency",
                    ],
                    skills=[
                        "Writing",
                        "SEO",
                        "Content strategy",
                        "Web content management",
                    ],
                    system_prompt="You are a Content Creator specializing in creating engaging content for websites, blogs, and marketing materials. You maintain the public image through high-quality content that drives traffic and conversions. You work closely with the marketing team to ensure brand consistency.",
                    communicates_with=["Marketing Manager", "Social Media Manager"],
                ),
                TeamMember(
                    role="Social Media Manager",
                    responsibilities=[
                        "Manage social media presence",
                        "Engage with community",
                        "Track social metrics",
                    ],
                    skills=["Social media", "Community management", "Analytics"],
                    system_prompt="You are the Social Media Manager responsible for building and maintaining the company's social media presence. You create engaging content and interact with the community.",
                    communicates_with=[
                        "Marketing Manager",
                        "Content Creator",
                        "Analytics Expert",
                    ],
                ),
                TeamMember(
                    role="Analytics Expert",
                    responsibilities=[
                        "Track campaign performance",
                        "Generate insights",
                        "Optimize strategies",
                    ],
                    skills=["Data analysis", "Reporting", "Optimization"],
                    system_prompt="You are an Analytics Expert who measures marketing performance and provides data-driven insights to improve campaigns and strategies.",
                    communicates_with=["Marketing Manager", "Social Media Manager"],
                ),
                TeamMember(
                    role="Campaign Strategist",
                    responsibilities=[
                        "Develop campaign strategies",
                        "Coordinate cross-channel initiatives",
                        "Measure campaign effectiveness",
                    ],
                    skills=["Strategy", "Campaign planning", "Cross-channel marketing"],
                    system_prompt="You are a Campaign Strategist who develops integrated marketing campaigns across multiple channels. You ensure campaigns are cohesive and effective.",
                    communicates_with=[
                        "Marketing Manager",
                        "Content Creator",
                        "Analytics Expert",
                    ],
                ),
            ]
        elif department == "executive":
            members = [
                TeamMember(
                    role="Chief Executive Officer",
                    responsibilities=[
                        "Set company vision and strategy",
                        "Make final decisions on major initiatives",
                        "Coordinate with all department heads",
                        "Report to board and stakeholders",
                    ],
                    skills=[
                        "Strategic thinking",
                        "Leadership",
                        "Decision making",
                        "Communication",
                    ],
                    system_prompt="You are the CEO of ElfAutomations, responsible for setting the strategic direction of the company. You work with all department heads to ensure alignment and make final decisions on major initiatives. You coordinate with other executives through natural language within your team, but when communicating with subordinate teams, you use formal A2A messages through the executive team's interfaces.",
                    communicates_with=[
                        "Chief Technology Officer",
                        "Chief Marketing Officer",
                        "Chief Operations Officer",
                        "Chief Financial Officer",
                    ],
                    manages_teams=self.EXECUTIVE_TEAM_MAPPINGS.get(
                        "Chief Executive Officer", []
                    ),
                ),
                TeamMember(
                    role="Chief Technology Officer",
                    responsibilities=[
                        "Define technical strategy and architecture",
                        "Oversee product development",
                        "Manage engineering teams through A2A",
                        "Ensure technical excellence",
                    ],
                    skills=[
                        "Technical leadership",
                        "Architecture",
                        "Innovation",
                        "Product development",
                    ],
                    system_prompt="You are the CTO of ElfAutomations, responsible for all technical aspects of the company. You communicate naturally with other executives in your team, but when you need work from engineering, QA, or DevOps teams, you formulate clear A2A requests with specifications, success criteria, and deadlines. You receive progress updates and deliverables through A2A channels.",
                    communicates_with=[
                        "Chief Executive Officer",
                        "Chief Operations Officer",
                        "Chief Marketing Officer",
                    ],
                    manages_teams=self.EXECUTIVE_TEAM_MAPPINGS.get(
                        "Chief Technology Officer", []
                    ),
                ),
                TeamMember(
                    role="Chief Marketing Officer",
                    responsibilities=[
                        "Develop go-to-market strategies",
                        "Build brand awareness",
                        "Manage marketing teams through A2A",
                        "Drive demand generation",
                    ],
                    skills=[
                        "Marketing strategy",
                        "Brand building",
                        "Go-to-market",
                        "Analytics",
                    ],
                    system_prompt="You are the CMO of ElfAutomations, responsible for marketing strategy and execution. Within the executive team, you collaborate naturally with other C-suite members. When you need marketing campaigns, content, or brand work executed, you send detailed A2A requests to the marketing team manager, including campaign objectives, target metrics, and deliverable specifications.",
                    communicates_with=[
                        "Chief Executive Officer",
                        "Chief Technology Officer",
                        "Chief Financial Officer",
                    ],
                    manages_teams=self.EXECUTIVE_TEAM_MAPPINGS.get(
                        "Chief Marketing Officer", []
                    ),
                ),
                TeamMember(
                    role="Chief Operations Officer",
                    responsibilities=[
                        "Optimize operational efficiency",
                        "Manage cross-functional processes",
                        "Oversee operations teams through A2A",
                        "Drive continuous improvement",
                    ],
                    skills=[
                        "Operations management",
                        "Process optimization",
                        "Cross-functional leadership",
                    ],
                    system_prompt="You are the COO of ElfAutomations, responsible for operational excellence. You work with fellow executives using natural dialogue, but interface with operations, HR, and facilities teams through structured A2A messages that clearly define operational requirements, process improvements, and performance metrics.",
                    communicates_with=[
                        "Chief Executive Officer",
                        "Chief Technology Officer",
                        "Chief Financial Officer",
                    ],
                    manages_teams=self.EXECUTIVE_TEAM_MAPPINGS.get(
                        "Chief Operations Officer", []
                    ),
                ),
                TeamMember(
                    role="Chief Financial Officer",
                    responsibilities=[
                        "Manage financial planning and analysis",
                        "Ensure financial health",
                        "Oversee finance teams through A2A",
                        "Guide investment decisions",
                    ],
                    skills=[
                        "Financial planning",
                        "Analysis",
                        "Budgeting",
                        "Investment strategy",
                    ],
                    system_prompt="You are the CFO of ElfAutomations, responsible for the financial health of the company. You collaborate with executive peers through natural conversation, but communicate with finance, accounting, and budget teams via A2A protocols, sending clear directives about financial reporting requirements, budget allocations, and analysis needs.",
                    communicates_with=[
                        "Chief Executive Officer",
                        "Chief Marketing Officer",
                        "Chief Operations Officer",
                    ],
                    manages_teams=self.EXECUTIVE_TEAM_MAPPINGS.get(
                        "Chief Financial Officer", []
                    ),
                ),
            ]
        else:
            # Default small team
            members = [
                TeamMember(
                    role="Team Lead",
                    responsibilities=[
                        "Coordinate team",
                        "Set priorities",
                        "Communicate with other teams",
                    ],
                    skills=["Leadership", "Communication", "Planning"],
                    system_prompt=f"You are the Team Lead for the {team_name}. You coordinate activities and ensure the team meets its objectives.",
                    communicates_with=["Specialist 1", "Specialist 2"],
                ),
                TeamMember(
                    role="Specialist 1",
                    responsibilities=[
                        "Execute core tasks",
                        "Collaborate with team",
                        "Report progress",
                    ],
                    skills=["Domain expertise", "Collaboration"],
                    system_prompt=f"You are a specialist in the {team_name}. You execute tasks and collaborate with the team.",
                    communicates_with=["Team Lead", "Specialist 2"],
                ),
                TeamMember(
                    role="Specialist 2",
                    responsibilities=[
                        "Support team objectives",
                        "Provide expertise",
                        "Complete assignments",
                    ],
                    skills=["Technical skills", "Problem solving"],
                    system_prompt=f"You are a specialist in the {team_name}. You provide expertise and complete assigned tasks.",
                    communicates_with=["Team Lead", "Specialist 1"],
                ),
            ]

        # Apply personality traits based on description and role
        for member in members:
            if not member.personality_traits:
                member.personality_traits = self._extract_personality_traits(
                    description, member.role
                )

        # Automatic skeptic assignment for teams >= 5 members (per Skeptic Agent Pattern)
        if len(members) >= 5:
            # Check if team already has a member with skeptic trait
            has_skeptic = any(
                "skeptic" in member.personality_traits
                for member in members
                if member.personality_traits
            )

            if not has_skeptic:
                # Add a dedicated Quality Assurance Skeptic
                skeptic_role = (
                    f"{team_name.replace('-team', '').title()} Quality Skeptic"
                )
                other_members = [
                    m.role
                    for m in members
                    if "Manager" not in m.role and "Lead" not in m.role
                ]

                skeptic_member = TeamMember(
                    role=skeptic_role,
                    responsibilities=[
                        "Challenge assumptions constructively",
                        "Identify potential failure modes and edge cases",
                        "Propose stress tests and validation criteria",
                        "Ensure robustness of solutions",
                        "Play devil's advocate in team discussions",
                    ],
                    skills=[
                        "Critical thinking",
                        "Risk assessment",
                        "Quality assurance",
                        "Problem analysis",
                    ],
                    system_prompt=f"You are the Quality Assurance Skeptic for the {team_name}. Your role is to constructively challenge proposals and identify potential issues before they become problems. You ask probing questions, identify edge cases, and ensure the team has considered all angles. While skeptical, you remain constructive and aim to strengthen ideas, not destroy them.",
                    communicates_with=[
                        "Team Lead"
                        if any("Lead" in m.role for m in members)
                        else members[0].role
                    ]
                    + other_members[:2],  # Communicates with lead and 2 other members
                    personality_traits=["skeptic"],
                )

                members.append(skeptic_member)

                # Update other members' communication patterns to include the skeptic
                for member in members[:-1]:  # All except the newly added skeptic
                    if (
                        len(member.communicates_with) < 4
                    ):  # Don't overload communication channels
                        member.communicates_with.append(skeptic_role)

        # Build communication pattern
        communication_pattern = {}
        for member in members:
            communication_pattern[member.role] = member.communicates_with

        return TeamSpecification(
            name=team_name,
            purpose=f"Team created from: {description[:100]}...",
            framework=framework,
            llm_provider=llm_provider,
            llm_model=llm_model,
            department=department,
            members=members,
            communication_pattern=communication_pattern,
            size_validation=self._validate_team_size(len(members)),
            natural_language_description=description,
        )

    def _validate_team_size(self, size: int) -> str:
        """Validate team size according to Two-Pizza Rule"""
        if size < self.MIN_TEAM_SIZE:
            return f"⚠️  Team too small ({size} members). Consider adding more members."
        elif size > self.MAX_TEAM_SIZE:
            return f"⚠️  Team too large ({size} members). Consider splitting into sub-teams."
        elif size == self.OPTIMAL_TEAM_SIZE:
            return f"✅ Optimal team size ({size} members)"
        else:
            return f"✅ Good team size ({size} members)"

    def _generate_enhanced_prompt(
        self, member: TeamMember, team_spec: TeamSpecification
    ) -> str:
        """Generate enhanced contextual prompt for an agent"""

        # If prompt template system is not available, enhance the basic prompt with personality
        if not self.prompt_system:
            if member.personality_traits:
                return self._apply_personality_traits(
                    member.system_prompt, member.personality_traits
                )
            return member.system_prompt

        # Check if we already have a rich prompt (avoid double-enhancing)
        if (
            "**" in member.system_prompt
            and "ORGANIZATION CONTEXT" in member.system_prompt
        ):
            return member.system_prompt

        # Generate or load team context
        team_context_file = (
            self.prompt_system.template_dir / f"{team_spec.name}_context.yaml"
        )

        if not team_context_file.exists():
            self.console.print(f"\n🎯 Let's define the context for {team_spec.name}")
            team_context = self.prompt_system.generate_team_context(
                team_spec.name,
                team_spec.purpose,
                parent_team=None,  # Could be enhanced to track parent teams
            )
        else:
            with open(team_context_file, "r") as f:
                team_context = yaml.safe_load(f)

        # Prepare member data
        members_data = [
            {"name": m.role, "role": m.role}  # Using role as name for now
            for m in team_spec.members
        ]

        # Generate custom details
        custom_details = {
            "tools": member.skills,  # Using skills as tools for now
            "specific_knowledge": f"Expertise in {team_spec.department} domain",
        }

        # Add manages_teams info if applicable
        if member.manages_teams:
            custom_details[
                "specific_knowledge"
            ] += f"\nManages these teams via A2A: {', '.join(member.manages_teams)}"

        # Generate the enhanced prompt
        enhanced_prompt = self.prompt_system.generate_agent_prompt(
            agent_name=member.role,
            agent_role=member.role,
            team_context=team_context,
            team_members=members_data,
            custom_details=custom_details,
        )

        # Apply personality traits if present
        if member.personality_traits:
            enhanced_prompt = self._apply_personality_traits(
                enhanced_prompt, member.personality_traits
            )

        return enhanced_prompt

    def _extract_personality_traits(self, description: str, role: str) -> List[str]:
        """Extract personality traits from natural language description"""
        traits = []

        # Keywords to trait mapping
        trait_keywords = {
            "skeptic": [
                "skeptical",
                "skeptic",
                "challenger",
                "devil's advocate",
                "critical",
                "questioning",
            ],
            "optimist": ["optimistic", "positive", "enthusiastic", "hopeful", "upbeat"],
            "detail-oriented": [
                "detail",
                "thorough",
                "meticulous",
                "precise",
                "careful",
            ],
            "innovator": ["innovative", "creative", "inventive", "novel", "original"],
            "pragmatist": ["pragmatic", "practical", "realistic", "grounded"],
            "collaborator": [
                "collaborative",
                "team player",
                "cooperative",
                "inclusive",
            ],
            "analyzer": ["analytical", "data-driven", "logical", "systematic"],
        }

        # Check description for trait keywords
        desc_lower = description.lower()
        for trait, keywords in trait_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                traits.append(trait)

        # Role-specific default traits
        role_defaults = {
            "Analytics Expert": ["analyzer", "detail-oriented"],
            "Content Creator": ["innovator", "collaborator"],
            "Social Media Manager": ["collaborator", "optimist"],
            "Team Lead": ["pragmatist", "collaborator"],
            "Marketing Manager": ["pragmatist", "collaborator"],
            "Chief Executive Officer": ["pragmatist", "collaborator"],
            "Chief Technology Officer": ["innovator", "analyzer"],
            "Chief Marketing Officer": ["innovator", "optimist"],
            "Chief Operations Officer": ["pragmatist", "detail-oriented"],
            "Chief Financial Officer": [
                "analyzer",
                "skeptic",
            ],  # CFOs are naturally skeptical about spending
        }

        # Add role-specific defaults if not already present
        if role in role_defaults:
            for default_trait in role_defaults[role]:
                if (
                    default_trait not in traits
                    and default_trait in self.PERSONALITY_TRAITS
                ):
                    traits.append(default_trait)

        # Special case: if description mentions "with a skeptical analytics expert"
        if "skeptical" in desc_lower and "analytics" in role.lower():
            if "skeptic" not in traits:
                traits.append("skeptic")

        return traits[:2]  # Limit to 2 traits to avoid overwhelming the prompt

    def _apply_personality_traits(
        self, prompt: str, personality_traits: List[str]
    ) -> str:
        """Apply personality trait modifiers to a system prompt"""

        # Add personality section to the prompt
        personality_section = "\n\n**PERSONALITY & BEHAVIORAL TRAITS:**\n\n"

        for trait in personality_traits:
            if trait.lower() in self.PERSONALITY_TRAITS:
                trait_info = self.PERSONALITY_TRAITS[trait.lower()]
                personality_section += (
                    f"**{trait.capitalize()}**: {trait_info['description']}\n"
                )
                personality_section += f"{trait_info['prompt_modifier']}\n\n"

        # If no template system, just append to the prompt
        if not self.prompt_system or "**" not in prompt:
            return prompt + personality_section

        # If using template system, insert before the closing section
        # Look for a good insertion point (before any final instructions)
        if "Remember to" in prompt or "Always maintain" in prompt:
            # Find the last major section before final instructions
            import re

            sections = re.split(r"\n\*\*[A-Z\s]+:\*\*\n", prompt)
            if len(sections) > 1:
                # Reconstruct with personality section inserted
                return prompt.replace(sections[-1], personality_section + sections[-1])

        # Default: append at the end
        return prompt + personality_section

    def modify_agent_prompt(self, team_name: str, agent_name: str):
        """Modify an existing agent's prompt interactively"""
        if not self.prompt_system:
            self.console.print(
                "[red]Prompt template system not available. Please install prompt_template_system.py[/red]"
            )
            return None

        return self.prompt_system.modify_agent_prompt(team_name, agent_name)

    def _review_and_refine_team(
        self, team_spec: TeamSpecification
    ) -> TeamSpecification:
        """Allow user to review and refine the team composition"""

        # Generate enhanced prompts for all members if prompt system is available
        if self.prompt_system and Confirm.ask(
            "\n🚀 Would you like to generate enhanced contextual prompts for all agents?",
            default=True,
        ):
            self.console.print(
                "\n[bold cyan]Generating enhanced prompts...[/bold cyan]"
            )
            for member in team_spec.members:
                member.system_prompt = self._generate_enhanced_prompt(member, team_spec)
            self.console.print("[green]✅ Enhanced prompts generated![/green]")

        self.console.print("\n[bold]Suggested Team Composition:[/bold]\n")

        # Display team overview
        org_placement = team_spec.name.replace("-team", "").replace("-", ".")
        overview = Panel(
            f"[bold]Team Name:[/bold] {team_spec.name}\n"
            f"[bold]Purpose:[/bold] {team_spec.purpose}\n"
            f"[bold]Framework:[/bold] {team_spec.framework}\n"
            f"[bold]Department:[/bold] {team_spec.department}\n"
            f"[bold]Organizational Placement:[/bold] {org_placement}\n"
            f"[bold]Size:[/bold] {len(team_spec.members)} members - {team_spec.size_validation}",
            title="Team Overview",
            border_style="blue",
        )
        self.console.print(overview)

        # Display team members
        self.console.print("\n[bold]Team Members:[/bold]")
        for i, member in enumerate(team_spec.members, 1):
            member_info = Panel(
                f"[bold cyan]Role:[/bold cyan] {member.role}\n\n"
                f"[bold]Responsibilities:[/bold]\n"
                + "\n".join(f"  • {r}" for r in member.responsibilities)
                + "\n\n"
                f"[bold]Skills:[/bold] {', '.join(member.skills)}\n\n"
                + (
                    f"[bold]Personality Traits:[/bold] {', '.join(member.personality_traits)}\n\n"
                    if member.personality_traits
                    else ""
                )
                + f"[bold]Communicates with:[/bold] {', '.join(member.communicates_with)}\n\n"
                + (
                    f"[bold]Manages Teams (A2A):[/bold] {', '.join(member.manages_teams)}\n\n"
                    if member.manages_teams
                    else ""
                )
                + f"[bold]System Prompt:[/bold]\n[dim]{member.system_prompt}[/dim]",
                title=f"Member {i}",
                border_style="green",
            )
            self.console.print(member_info)

        # Display communication pattern
        self._display_communication_pattern(team_spec)

        # Ask for confirmation or refinement
        if Confirm.ask("\nWould you like to proceed with this team composition?"):
            return team_spec
        else:
            # In a full implementation, we'd allow editing here
            self.console.print(
                "[yellow]Team refinement not yet implemented. Proceeding with suggested composition.[/yellow]"
            )
            return team_spec

    def _display_communication_pattern(self, team_spec: TeamSpecification):
        """Display the communication pattern as a table"""
        self.console.print("\n[bold]Communication Patterns:[/bold]")

        # Intra-team communication
        self.console.print("\n[bold cyan]Intra-Team Communication:[/bold cyan]")
        comm_table = Table(show_header=True, header_style="bold magenta")
        comm_table.add_column("Team Member", style="cyan")
        comm_table.add_column("Communicates With", style="green")

        for member, connections in team_spec.communication_pattern.items():
            comm_table.add_row(member, ", ".join(connections))

        self.console.print(comm_table)

        # Inter-team communication (A2A)
        managers_with_teams = [m for m in team_spec.members if m.manages_teams]
        if managers_with_teams:
            self.console.print(
                "\n[bold cyan]Inter-Team Communication (A2A):[/bold cyan]"
            )
            a2a_table = Table(show_header=True, header_style="bold magenta")
            a2a_table.add_column("Manager", style="cyan")
            a2a_table.add_column("Manages Teams", style="yellow")

            for manager in managers_with_teams:
                a2a_table.add_row(manager.role, ", ".join(manager.manages_teams))

            self.console.print(a2a_table)

    def _generate_team_files(self, team_spec: TeamSpecification):
        """Generate all necessary files for the team"""
        self.console.print(
            "\n[bold yellow]📝 Generating team configuration files...[/bold yellow]"
        )

        team_dir = self.teams_dir / team_spec.name
        team_dir.mkdir(exist_ok=True)

        # Generate framework-specific configuration
        if team_spec.framework == "CrewAI":
            self._generate_crewai_config(team_spec, team_dir)
        else:
            self._generate_langgraph_config(team_spec, team_dir)

        # Generate Kubernetes manifests
        self._generate_k8s_manifests(team_spec, team_dir)

        # Generate A2A configuration
        self._generate_a2a_config(team_spec, team_dir)

        # Generate documentation
        self._generate_team_documentation(team_spec, team_dir)

        self.console.print(f"\n[green]✅ Team files generated in: {team_dir}[/green]")

    def _generate_crewai_config(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate CrewAI-specific configuration following framework conventions"""

        # Create directory structure
        (team_dir / "agents").mkdir(exist_ok=True)
        (team_dir / "tasks").mkdir(exist_ok=True)
        (team_dir / "tools").mkdir(exist_ok=True)
        (team_dir / "config").mkdir(exist_ok=True)
        (team_dir / "k8s").mkdir(exist_ok=True)

        # Generate configuration
        config = {
            "team_name": team_spec.name,
            "framework": "crewai",
            "llm_provider": team_spec.llm_provider,
            "llm_model": team_spec.llm_model,
            "department": team_spec.department,
            "agents": [],
            "process": "hierarchical" if len(team_spec.members) > 4 else "sequential",
            "memory": True,
            "verbose": True,
        }

        # Generate agent configurations
        for member in team_spec.members:
            agent_config = {
                "role": member.role,
                "goal": " ".join(member.responsibilities[:2]),
                "backstory": member.system_prompt,
                "allow_delegation": "Manager" in member.role or "Lead" in member.role,
                "tools": [],  # Tools will be added via MCP
            }
            config["agents"].append(agent_config)

        # Save team configuration
        config_file = team_dir / "config" / "team_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        # Generate A2A configuration
        self._generate_a2a_config(team_spec, team_dir / "config")

        # Generate individual agent files
        self._generate_crewai_agents(team_spec, team_dir)

        # Generate crew.py (main orchestrator)
        self._generate_crewai_crew(team_spec, team_dir)

        # Generate sample tasks
        self._generate_sample_tasks(team_spec, team_dir)

        # Generate make-deployable script
        self._generate_deployable_script(team_spec, team_dir)

        # Generate README
        self._generate_readme(team_spec, team_dir)

    def _generate_crewai_agents(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate individual CrewAI agent source files"""
        agents_dir = team_dir / "agents"

        # Create __init__.py
        init_content = '''"""
Team agents for {team_name}
"""

'''.format(
            team_name=team_spec.name
        )

        agent_imports = []

        for member in team_spec.members:
            # Convert role to filename
            filename = member.role.lower().replace(" ", "_") + ".py"
            class_name = member.role.replace(" ", "") + "Agent"

            agent_imports.append(f"from .{filename[:-3]} import {class_name}")

            # Generate enhanced prompt for this member
            enhanced_prompt = self._generate_enhanced_prompt(member, team_spec)
            # Escape triple quotes in the prompt
            enhanced_prompt_escaped = enhanced_prompt.replace('"""', '\\"\\"\\""')

            # Generate individual agent file
            # Generate LLM import based on provider
            llm_import = ""
            llm_init = ""
            if team_spec.llm_provider == "OpenAI":
                llm_import = "from langchain_openai import ChatOpenAI"
                llm_init = f'ChatOpenAI(model="{team_spec.llm_model}", temperature=0.7)'
            else:  # Anthropic
                llm_import = "from langchain_anthropic import ChatAnthropic"
                llm_init = (
                    f'ChatAnthropic(model="{team_spec.llm_model}", temperature=0.7)'
                )

            # Check if this is a manager role that needs A2A capabilities
            is_manager = bool(member.manages_teams)
            a2a_imports = ""
            a2a_init = ""
            if is_manager:
                a2a_imports = """
from agents.distributed.a2a.client import A2AClientManager
from agents.distributed.a2a.messages import TaskRequest, TaskResponse
from datetime import datetime
import json"""
                a2a_init = """
        # Initialize A2A client for inter-team communication
        self.a2a_client = None
        if self.manages_teams:
            self._init_a2a_client()"""

            agent_content = f'''#!/usr/bin/env python3
"""
{member.role} Agent for {team_spec.name}
"""

from crewai import Agent
from typing import Optional, List, Dict, Any
import logging
import os
from datetime import datetime
from tools.conversation_logging_system import ConversationLogger, MessageType
{llm_import}{a2a_imports}


class {class_name}:
    """
    {member.role} implementation

    Responsibilities:
{chr(10).join(f"    - {r}" for r in member.responsibilities)}

    Skills: {', '.join(member.skills)}""" + (f"""
    Personality Traits: {', '.join(member.personality_traits)}""" if member.personality_traits else "") + (f"""
    Manages Teams: {', '.join(member.manages_teams)}""" if member.manages_teams else "") + f"""
    """

    def __init__(self, tools: Optional[List] = None):
        self.logger = logging.getLogger(f"{team_spec.name}.{member.role}")
        self.tools = tools or []
        self.manages_teams = {member.manages_teams}
        self.role = "{member.role}"
        self.agent = self._create_agent()

        # Initialize conversation logger
        self.conversation_logger = ConversationLogger("{team_spec.name}")
        self.team_name = "{team_spec.name}"{a2a_init}

    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        # Initialize LLM
        llm = {llm_init}

        # Get the enhanced system prompt with personality traits
        backstory = """{enhanced_prompt_escaped}"""

        return Agent(
            role="{member.role}",
            goal="{' '.join(member.responsibilities[:2])}",
            backstory=backstory,
            allow_delegation={"Manager" in member.role or "Lead" in member.role},
            verbose=True,
            tools=self.tools,
            llm=llm
        )

    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent

    def log_communication(self, message: str, to_agent: Optional[str] = None):
        """Log internal team communications naturally"""
        # Just log the natural conversation - no structure imposed
        if to_agent:
            self.logger.info(f"[{member.role} → {{to_agent}}]: {{message}}")
        else:
            self.logger.info(f"[{member.role}]: {{message}}")

    def log_proposal(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a proposal message with rich context"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.PROPOSAL,
            to_agent=to_agent,
            metadata=metadata
        )
        # Also use traditional logging
        self.log_communication(f"[PROPOSAL] {{message}}", to_agent)

    def log_challenge(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a challenge/skeptical message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.CHALLENGE,
            to_agent=to_agent,
            metadata=metadata
        )
        self.log_communication(f"[CHALLENGE] {{message}}", to_agent)

    def log_decision(self, message: str, **metadata):
        """Log a decision message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.DECISION,
            metadata=metadata
        )
        self.log_communication(f"[DECISION] {{message}}")

    def log_update(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a general update message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.UPDATE,
            to_agent=to_agent,
            metadata=metadata
        )
        self.log_communication(message, to_agent)

    def execute_with_logging(self, task):
        """Execute task with conversation logging"""
        task_id = getattr(task, 'id', f"task_{{datetime.now().timestamp()}}")
        task_description = str(task)

        self.conversation_logger.start_conversation(task_id, task_description)
        self.log_update(f"Starting task: {{task_description[:100]}}...")

        try:
            # Execute the actual task
            result = self.agent.execute(task)

            # Log completion
            self.log_update(f"Task completed successfully")
            self.conversation_logger.end_conversation("completed")

            return result

        except Exception as e:
            self.log_update(f"Task failed: {{str(e)}}")
            self.conversation_logger.end_conversation(f"failed: {{str(e)}}")
            raise'''

            if is_manager:
                agent_content += f"""

    def _init_a2a_client(self):
        \"\"\"Initialize A2A client for inter-team communication\"\"\"
        try:
            self.a2a_client = A2AClientManager()
            self.logger.info(f"A2A client initialized for managing teams: {{self.manages_teams}}")
        except Exception as e:
            self.logger.error(f"Failed to initialize A2A client: {{e}}")
            self.a2a_client = None

    async def send_task_to_team(self, team_name: str, task_description: str,
                               success_criteria: List[str], deadline: Optional[str] = None,
                               context: Optional[Dict[str, Any]] = None) -> Optional[TaskResponse]:
        \"\"\"
        Send a task to a subordinate team via A2A protocol

        Args:
            team_name: Name of the team to send the task to
            task_description: Detailed description of the task
            success_criteria: List of criteria that define successful completion
            deadline: Optional deadline for the task
            context: Optional additional context for the task

        Returns:
            TaskResponse from the team or None if failed
        \"\"\"
        if not self.a2a_client:
            self.logger.error("A2A client not initialized")
            return None

        if team_name not in self.manages_teams:
            self.logger.error(f"{{team_name}} is not in managed teams: {{self.manages_teams}}")
            return None

        # Create formal A2A task request
        task_request = TaskRequest(
            from_team="{team_spec.name}",
            from_agent="{member.role}",
            to_team=team_name,
            task_description=task_description,
            success_criteria=success_criteria,
            deadline=deadline,
            context=context or {{}},
            priority="normal"
        )

        # Log structured A2A request
        a2a_log = {{
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "communication_type": "inter_team_request",
            "from_team": "{team_spec.name}",
            "from_agent": "{member.role}",
            "to_team": team_name,
            "task_id": task_request.task_id if hasattr(task_request, 'task_id') else None,
            "request": {{
                "description": task_description,
                "success_criteria": success_criteria,
                "deadline": deadline,
                "context": context
            }}
        }}

        self.logger.info(f"Sending A2A task to {{team_name}}: {{task_description[:100]}}")
        self.logger.info(f"A2A_REQUEST_LOG: {{json.dumps(a2a_log)}}")

        try:
            response = await self.a2a_client.send_task(team_name, task_request)

            # Log structured response
            response_log = {{
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "communication_type": "inter_team_response",
                "task_id": task_request.task_id if hasattr(task_request, 'task_id') else None,
                "from_team": team_name,
                "to_team": "{team_spec.name}",
                "to_agent": "{member.role}",
                "status": response.status,
                "response_data": response.data if hasattr(response, 'data') else None
            }}

            self.logger.info(f"Received response from {{team_name}}: {{response.status}}")
            self.logger.info(f"A2A_RESPONSE_LOG: {{json.dumps(response_log)}}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to send task to {{team_name}}: {{e}}")
            return None

    async def check_task_status(self, team_name: str, task_id: str) -> Optional[Dict[str, Any]]:
        \"\"\"Check the status of a previously sent task\"\"\"
        if not self.a2a_client:
            return None

        try:
            status = await self.a2a_client.check_status(team_name, task_id)
            return status
        except Exception as e:
            self.logger.error(f"Failed to check task status: {{e}}")
            return None
"""

            agent_content += """
"""

            agent_file = agents_dir / filename
            with open(agent_file, "w") as f:
                f.write(agent_content)

        # Write __init__.py with imports
        init_content += "\n".join(agent_imports)
        init_content += "\n\n__all__ = ["
        init_content += ", ".join(
            f'"{member.role.replace(" ", "") + "Agent"}"'
            for member in team_spec.members
        )
        init_content += "]\n"

        init_file = agents_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write(init_content)

    def _generate_crewai_crew(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate the main crew.py file following CrewAI conventions"""
        crew_content = f'''#!/usr/bin/env python3
"""
{team_spec.name} Crew Definition
Generated by Team Factory

Purpose: {team_spec.purpose}
Framework: CrewAI
Department: {team_spec.department}
"""

from crewai import Crew, Process, Task
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Import all team agents
from agents import (
{chr(10).join(f"    {member.role.replace(' ', '')}Agent," for member in team_spec.members)}
)

# Set up logging for natural language communication tracking
log_dir = Path("/logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_dir / '{team_spec.name}_communications.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s'
)


class {team_spec.name.replace("-", " ").title().replace(" ", "")}Crew:
    """
    Orchestrates the {team_spec.name} using {team_spec.framework}

    This team follows the communication patterns defined in the team specification,
    ensuring efficient collaboration between team members.
    """

    def __init__(self, tools: Optional[Dict[str, List]] = None):
        self.logger = logging.getLogger("{team_spec.name}")
        self.tools = tools or {{}}
        self.agents = self._initialize_agents()
        self.crew = self._create_crew()

        # Log team initialization
        self.logger.info(f"Initialized {team_spec.name} with {{len(self.agents)}} agents")

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all team agents with their tools"""
        agents = {{}}

'''

        # Add agent initialization
        for member in team_spec.members:
            agent_var = member.role.lower().replace(" ", "_")
            class_name = member.role.replace(" ", "") + "Agent"
            crew_content += f"""        # Initialize {member.role}
        {agent_var}_tools = self.tools.get("{member.role}", [])
        agents["{member.role}"] = {class_name}(tools={agent_var}_tools)
        self.logger.info(f"Initialized {member.role} with {{len({agent_var}_tools)}} tools")

"""

        crew_content += (
            '''        return agents

    def _create_crew(self) -> Crew:
        """Create the crew with all agents"""
        # Get CrewAI agent instances
        crew_agents = [agent.get_agent() for agent in self.agents.values()]

        return Crew(
            agents=crew_agents,
            process=Process.'''
            + ("hierarchical" if len(team_spec.members) > 4 else "sequential")
            + ''',
            verbose=True,
            memory=True,  # Enable memory for context preservation
            embedder={
                "provider": "openai",
                "config": {"model": "text-embedding-3-small"}
            }
        )

    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task with the team

        Args:
            task_description: Natural language description of the task
            context: Optional context for the task

        Returns:
            Result of the task execution
        """
        self.logger.info(f"Team received task: {task_description}")
        if context:
            self.logger.info(f"Task context: {context}")

        # Create a task for the crew
        task = Task(
            description=task_description,
            expected_output="Comprehensive result addressing all aspects of the task"
        )

        # Execute with the crew
        result = self.crew.kickoff(inputs={"task": task_description, "context": context or {}})

        self.logger.info(f"Team completed task. Result: {result}")
        return {
            "status": "completed",
            "result": result,
            "team": "'''
            + team_spec.name
            + '''"
        }

    def get_team_status(self) -> Dict[str, Any]:
        """Get the current status of the team"""
        return {
            "team_name": "'''
            + team_spec.name
            + '''",
            "framework": "'''
            + team_spec.framework
            + """",
            "agents": list(self.agents.keys()),
            "status": "active",
            "communication_pattern": """
            + str(team_spec.communication_pattern)
            + '''
        }


# Create a singleton instance
_orchestrator_instance = None

def get_orchestrator(tools: Optional[Dict[str, List]] = None):
    """Get or create the team orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = '''
            + team_spec.name.replace("-", " ").title().replace(" ", "")
            + """Crew(tools=tools)
    return _orchestrator_instance


if __name__ == "__main__":
    # Example usage
    orchestrator = get_orchestrator()
    result = orchestrator.execute_task("Develop a strategic plan for Q2")
    print(result)
"""
        )

        crew_file = team_dir / "crew.py"
        with open(crew_file, "w") as f:
            f.write(crew_content)

    def _generate_sample_tasks(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate sample task definitions for the team"""
        tasks_dir = team_dir / "tasks"

        # Create __init__.py
        init_file = tasks_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write('"""Task definitions for the team"""\n')

        # Generate a sample task
        sample_task_content = f'''#!/usr/bin/env python3
"""
Sample tasks for {team_spec.name}
"""

from crewai import Task
from typing import List


def create_strategic_planning_task(agent) -> Task:
    """Create a strategic planning task"""
    return Task(
        description="""
        Develop a comprehensive strategic plan for the next quarter.
        Consider market conditions, resource allocation, and team capabilities.
        Provide specific recommendations and action items.
        """,
        agent=agent,
        expected_output="A detailed strategic plan with specific goals and timelines"
    )


def create_status_report_task(agent) -> Task:
    """Create a status report task"""
    return Task(
        description="""
        Generate a comprehensive status report covering:
        1. Current progress on key initiatives
        2. Challenges and blockers
        3. Resource needs
        4. Recommendations for next steps
        """,
        agent=agent,
        expected_output="A structured status report with clear insights and recommendations"
    )


def get_all_tasks(agents: dict) -> List[Task]:
    """Get all tasks for the team"""
    tasks = []

    # Add tasks based on team composition
    if "Chief Executive Officer" in agents:
        tasks.append(create_strategic_planning_task(agents["Chief Executive Officer"]))

    # Add more tasks as needed
    return tasks
'''

        task_file = tasks_dir / "sample_tasks.py"
        with open(task_file, "w") as f:
            f.write(sample_task_content)

    def _generate_deployable_script(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate script to create deployable version of the team"""
        script_content = f'''#!/usr/bin/env python3
"""
Make Deployable Team Script
Creates a containerized version of the team that can run as a single K8s pod

This script:
1. Creates a team_server.py that wraps the crew with A2A protocol
2. Generates a Dockerfile for containerization
3. Creates requirements.txt with all dependencies
4. Prepares the team for GitOps deployment
"""

import os
import shutil
from pathlib import Path


def create_deployable_team():
    """Create a deployable version of the team"""
    team_dir = Path(__file__).parent

    print("🚀 Creating deployable team package...")

    # Create team_server.py - the main entry point
    create_team_server(team_dir)

    # Create Dockerfile
    create_dockerfile(team_dir)

    # Create requirements.txt
    create_requirements(team_dir)

    # Create a simple health check endpoint
    create_health_check(team_dir)

    print("✅ Team is ready for containerization!")
    print("📦 Next steps:")
    print("   1. Build: docker build -t elf-automations/{team_spec.name} .")
    print("   2. Push to registry accessible by your K8s cluster")
    print("   3. Update k8s/deployment.yaml with correct image")
    print("   4. Commit to GitOps repo for ArgoCD")


def create_team_server(team_dir: Path):
    """Create the main server that runs the team"""
    server_content = """#!/usr/bin/env python3
\"\"\"
Team Server - Runs the CrewAI team with A2A protocol endpoint
\"\"\"

import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any

# Import the team
from crew import {crew_class}

# Import A2A server components
from agents.distributed.a2a.server import A2AServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="{team_spec.name} API")

# Initialize the crew
crew_instance = None

@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize the crew on startup\"\"\"
    global crew_instance
    logger.info("Initializing {team_spec.name}...")
    crew_instance = {crew_class}()
    logger.info("Team initialized successfully")

@app.get("/health")
async def health_check():
    \"\"\"Health check endpoint\"\"\"
    return {{"status": "healthy", "team": "{team_spec.name}"}}

@app.post("/task")
async def execute_task(request: Dict[str, Any]):
    \"\"\"Execute a task via A2A protocol\"\"\"
    try:
        task_description = request.get("task", "")
        context = request.get("context", {{}})

        logger.info(f"Received task: {{task_description[:100]}}...")

        # Execute with the crew
        result = await crew_instance.execute_task(task_description, context)

        return JSONResponse(content={{
            "status": "success",
            "result": result,
            "team": "{team_spec.name}"
        }})

    except Exception as e:
        logger.error(f"Error executing task: {{str(e)}}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/capabilities")
async def get_capabilities():
    \"\"\"Return team capabilities for A2A discovery\"\"\"
    return {{
        "team_name": "{team_spec.name}",
        "department": "{team_spec.department}",
        "framework": "CrewAI",
        "agents": [
            {{% raw %}}
            {{
                "role": agent,
                "status": "active"
            }}
            for agent in crew_instance.get_team_status()["agents"]
            {{% endraw %}}
        ],
        "accepts_tasks": True,
        "a2a_version": "1.0"
    }}

if __name__ == "__main__":
    # Run the server
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
\"\"\"

    crew_class = "{team_spec.name}".replace("-", " ").title().replace(" ", "") + "Crew"

    with open(team_dir / "team_server.py", "w") as f:
        f.write(server_content.format(
            crew_class=crew_class,
            team_spec=team_spec
        ))


def create_dockerfile(team_dir: Path):
    \"\"\"Create Dockerfile for the team\"\"\"
    dockerfile_content = \"\"\"FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\\\
    build-essential \\\\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy team source code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create logs directory
RUN mkdir -p /logs

# Expose A2A port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\\\
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run the team server
CMD ["python", "team_server.py"]
\"\"\"

    with open(team_dir / "Dockerfile", "w") as f:
        f.write(dockerfile_content)


def create_requirements(team_dir: Path):
    \"\"\"Create requirements.txt with all dependencies\"\"\"
    requirements = \"\"\"# Core dependencies
crewai>=0.70.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# LLM providers
openai>=1.0.0
anthropic>=0.39.0

# A2A communication
httpx>=0.25.0
websockets>=12.0

# Monitoring and logging
structlog>=23.0.0
prometheus-client>=0.19.0

# Utilities
python-dotenv>=1.0.0
tenacity>=8.2.0
\"\"\"

    with open(team_dir / "requirements.txt", "w") as f:
        f.write(requirements)


def create_health_check(team_dir: Path):
    \"\"\"Create a simple health check script\"\"\"
    health_check_content = \"\"\"#!/usr/bin/env python3
import requests
import sys

try:
    response = requests.get("http://localhost:8080/health", timeout=3)
    if response.status_code == 200:
        print("✅ Health check passed")
        sys.exit(0)
    else:
        print(f"❌ Health check failed: {{response.status_code}}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Health check error: {{e}}")
    sys.exit(1)
\"\"\"

    health_check_file = team_dir / "health_check.py"
    with open(health_check_file, "w") as f:
        f.write(health_check_content)
    os.chmod(health_check_file, 0o755)


if __name__ == "__main__":
    create_deployable_team()
'''

        script_file = team_dir / "make-deployable-team.py"
        with open(script_file, "w") as f:
            f.write(script_content)

        # Make script executable
        os.chmod(script_file, 0o755)

    def _generate_crewai_python(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate Python implementation for CrewAI team"""
        implementation = f'''#!/usr/bin/env python3
"""
{team_spec.name} - CrewAI Implementation
Generated by Team Factory

Purpose: {team_spec.purpose}
"""

from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any
import logging

# Set up logging for natural language communication tracking
logging.basicConfig(
    filename='{team_spec.name}_communications.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s'
)


class {team_spec.name.replace("-", "_").title()}:
    """Implementation of {team_spec.name} using CrewAI"""

    def __init__(self):
        self.logger = logging.getLogger("{team_spec.name}")
        self.agents = self._create_agents()
        self.crew = self._create_crew()

    def _create_agents(self) -> List[Agent]:
        """Create all team agents"""
        agents = []

'''

        # Add agent definitions
        for member in team_spec.members:
            agent_var = member.role.lower().replace(" ", "_")
            implementation += f'''        # {member.role}
        {agent_var} = Agent(
            role="{member.role}",
            goal="{' '.join(member.responsibilities[:2])}",
            backstory="""{member.system_prompt}""",
            allow_delegation={"Manager" in member.role or "Lead" in member.role},
            verbose=True
        )
        agents.append({agent_var})

'''

        implementation += '''        return agents

    def _create_crew(self) -> Crew:
        """Create the crew with all agents"""
        return Crew(
            agents=self.agents,
            process=Process.hierarchical,
            verbose=True,
            memory=True  # Enable memory for context preservation
        )

    def execute(self, task_description: str) -> Dict[str, Any]:
        """Execute a task with the team"""
        self.logger.info(f"Team received task: {task_description}")

        # Log internal communications
        result = self.crew.kickoff(task_description)

        self.logger.info(f"Team completed task. Result: {result}")
        return result


if __name__ == "__main__":
    team = {team_spec.name.replace("-", "_").title()}()
    # Example usage
    result = team.execute("Your task description here")
    print(result)
'''

        impl_file = team_dir / f"{team_spec.name}.py"
        with open(impl_file, "w") as f:
            f.write(implementation)

    def _generate_langgraph_config(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate LangGraph-specific configuration following best practices"""

        # Create directory structure for LangGraph
        (team_dir / "agents").mkdir(exist_ok=True)
        (team_dir / "workflows").mkdir(exist_ok=True)
        (team_dir / "tools").mkdir(exist_ok=True)
        (team_dir / "config").mkdir(exist_ok=True)
        (team_dir / "k8s").mkdir(exist_ok=True)

        # Generate configuration
        config = {
            "team_name": team_spec.name,
            "framework": "langgraph",
            "llm_provider": team_spec.llm_provider,
            "llm_model": team_spec.llm_model,
            "department": team_spec.department,
            "agents": [],
            "workflow_type": "state_machine",
            "checkpointing": True,
            "memory_type": "postgres",  # For production use
        }

        # Generate agent configurations
        for member in team_spec.members:
            agent_config = {
                "role": member.role,
                "goal": " ".join(member.responsibilities[:2]),
                "backstory": member.system_prompt,
                "is_manager": "Manager" in member.role or "Lead" in member.role,
                "tools": [],  # Tools will be added via MCP
            }
            config["agents"].append(agent_config)

        # Save team configuration
        config_file = team_dir / "config" / "team_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        # Generate A2A configuration
        self._generate_a2a_config(team_spec, team_dir / "config")

        # Generate individual agent files for LangGraph
        self._generate_langgraph_agents(team_spec, team_dir)

        # Generate workflow orchestrator
        self._generate_langgraph_workflow(team_spec, team_dir)

        # Generate state definitions
        self._generate_langgraph_state(team_spec, team_dir)

        # Generate make-deployable script
        self._generate_langgraph_deployable_script(team_spec, team_dir)

        # Generate README
        self._generate_langgraph_readme(team_spec, team_dir)

    def _generate_langgraph_agents(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate individual LangGraph agent source files"""
        agents_dir = team_dir / "agents"

        # Create __init__.py
        init_content = '''"""
Team agents for {team_name} using LangGraph
"""

'''.format(
            team_name=team_spec.name
        )

        agent_imports = []

        for member in team_spec.members:
            # Convert role to filename
            filename = member.role.lower().replace(" ", "_") + ".py"
            class_name = member.role.replace(" ", "") + "Agent"

            agent_imports.append(f"from .{filename[:-3]} import {class_name}")

            # Generate LLM import based on provider
            llm_import = ""
            llm_init = ""
            if team_spec.llm_provider == "OpenAI":
                llm_import = "from langchain_openai import ChatOpenAI"
                llm_init = f'ChatOpenAI(model="{team_spec.llm_model}", temperature=0.7)'
            else:  # Anthropic
                llm_import = "from langchain_anthropic import ChatAnthropic"
                llm_init = (
                    f'ChatAnthropic(model="{team_spec.llm_model}", temperature=0.7)'
                )

            # Check if this is a manager role that needs A2A capabilities
            is_manager = bool(member.manages_teams)
            a2a_imports = ""
            a2a_methods = ""
            if is_manager:
                a2a_imports = """
from agents.distributed.a2a.client import A2AClientManager
from agents.distributed.a2a.messages import TaskRequest, TaskResponse
from datetime import datetime
import json"""

                a2a_methods = (
                    '''
    def _init_a2a_client(self):
        """Initialize A2A client for inter-team communication"""
        try:
            self.a2a_client = A2AClientManager()
            self.logger.info(f"A2A client initialized for managing teams: {self.manages_teams}")
        except Exception as e:
            self.logger.error(f"Failed to initialize A2A client: {e}")
            self.a2a_client = None

    async def send_task_to_team(self, team_name: str, task_description: str,
                               success_criteria: List[str], deadline: Optional[str] = None,
                               context: Optional[Dict[str, Any]] = None) -> Optional[TaskResponse]:
        """
        Send a task to a subordinate team via A2A protocol
        """
        if not self.a2a_client:
            self.logger.error("A2A client not initialized")
            return None

        if team_name not in self.manages_teams:
            self.logger.error(f"{team_name} is not in managed teams: {self.manages_teams}")
            return None

        # Create formal A2A task request
        task_request = TaskRequest(
            from_team="'''
                    + team_spec.name
                    + '''",
            from_agent="'''
                    + member.role
                    + '''",
            to_team=team_name,
            task_description=task_description,
            success_criteria=success_criteria,
            deadline=deadline,
            context=context or {},
            priority="normal"
        )

        # Log structured A2A request
        a2a_log = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "communication_type": "inter_team_request",
            "from_team": "'''
                    + team_spec.name
                    + '''",
            "from_agent": "'''
                    + member.role
                    + '''",
            "to_team": team_name,
            "request": {
                "description": task_description,
                "success_criteria": success_criteria,
                "deadline": deadline,
                "context": context
            }
        }

        self.logger.info(f"Sending A2A task to {team_name}: {task_description[:100]}")
        self.logger.info(f"A2A_REQUEST_LOG: {json.dumps(a2a_log)}")

        try:
            response = await self.a2a_client.send_task(team_name, task_request)

            # Log structured response
            if response:
                response_log = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "communication_type": "inter_team_response",
                    "from_team": team_name,
                    "to_team": "'''
                    + team_spec.name
                    + '''",
                    "to_agent": "'''
                    + member.role
                    + """",
                    "status": response.status,
                    "response_data": response.data if hasattr(response, 'data') else None
                }

                self.logger.info(f"Received response from {team_name}: {response.status}")
                self.logger.info(f"A2A_RESPONSE_LOG: {json.dumps(response_log)}")

            return response
        except Exception as e:
            self.logger.error(f"Failed to send task to {team_name}: {e}")
            return None
"""
                )

            agent_content = (
                f'''#!/usr/bin/env python3
"""
{member.role} Agent for {team_spec.name}
LangGraph-based implementation
"""

from typing import Optional, List, Dict, Any, TypedDict, Annotated
from datetime import datetime
import logging
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from tools.conversation_logging_system import ConversationLogger, MessageType
{llm_import}{a2a_imports}

from agents.langgraph_base import LangGraphBaseAgent, LangGraphAgentState


class {class_name}State(TypedDict):
    """State specific to {member.role}"""
    messages: Annotated[List[BaseMessage], add_messages]
    agent_id: str
    current_task: Optional[str]
    task_context: Dict[str, Any]
    available_tools: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    error_count: int
    last_activity: datetime
    metadata: Dict[str, Any]
    # Agent-specific state
    manages_teams: List[str]
    pending_a2a_requests: Dict[str, Any]


class {class_name}(LangGraphBaseAgent):
    """
    {member.role} implementation using LangGraph

    Responsibilities:
{chr(10).join(f"    - {r}" for r in member.responsibilities)}

    Skills: {', '.join(member.skills)}
    """ + (f"""
    Manages Teams: {', '.join(member.manages_teams)}""" if member.manages_teams else "") + f"""
    """

    def __init__(self,
                 agent_id: Optional[str] = None,
                 gateway_url: str = "http://agentgateway-service:3000",
                 gateway_api_key: Optional[str] = None):

        # Generate unique agent ID if not provided
        if not agent_id:
            agent_id = f"{team_spec.name}-{member.role.lower().replace(' ', '-')}-{{uuid4().hex[:8]}}"

        super().__init__(
            agent_id=agent_id,
            name="{member.role}",
            department="{team_spec.department}",
            system_prompt="""{member.system_prompt}""",
            gateway_url=gateway_url,
            gateway_api_key=gateway_api_key
        )

        self.logger = logging.getLogger(f"{team_spec.name}.{member.role}")
        self.role = "{member.role}"
        self.manages_teams = {member.manages_teams}
        self.pending_a2a_requests = {{}}

        # Initialize conversation logger
        self.conversation_logger = ConversationLogger("{team_spec.name}")
        self.team_name = "{team_spec.name}"

        # Initialize custom LLM
        self.llm = {llm_init}

        # Initialize A2A client if this is a manager
        if self.manages_teams:
            self._init_a2a_client()

        # Override base graph with custom workflow
        self._initialize_custom_workflow()

    def _initialize_custom_workflow(self):
        """Initialize the custom workflow for this agent"""
        # Create the state graph
        workflow = StateGraph({class_name}State)

        # Add nodes specific to this agent's responsibilities
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("analyze_task", self._analyze_task_node)
        workflow.add_node("plan_execution", self._plan_execution_node)'''
                + (
                    """
        workflow.add_node("delegate_tasks", self._delegate_tasks_node)"""
                    if is_manager
                    else ""
                )
                + """
        workflow.add_node("execute_task", self._execute_task_node)
        workflow.add_node("review_results", self._review_results_node)
        workflow.add_node("finalize", self._finalize_node)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges
        workflow.add_edge("initialize", "analyze_task")
        workflow.add_edge("analyze_task", "plan_execution")"""
                + (
                    """
        workflow.add_conditional_edges(
            "plan_execution",
            self._should_delegate,
            {
                "delegate": "delegate_tasks",
                "execute": "execute_task"
            }
        )
        workflow.add_edge("delegate_tasks", "review_results")"""
                    if is_manager
                    else """
        workflow.add_edge("plan_execution", "execute_task")"""
                )
                + '''
        workflow.add_edge("execute_task", "review_results")
        workflow.add_edge("review_results", "finalize")
        workflow.add_edge("finalize", END)

        # Compile the graph
        self.graph = workflow
        self.compiled_graph = workflow.compile(checkpointer=self.checkpointer)

        self.logger.info("Custom workflow initialized for {member.role}")

    async def _analyze_task_node(self, state: {class_name}State) -> {class_name}State:
        """Analyze the incoming task and determine approach"""
        messages = state.get("messages", [])

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=self.system_prompt))

        # Create analysis prompt
        analysis_prompt = HumanMessage(content=f"""
        Analyze this task and determine the best approach:

        Task: {{state.get('current_task', 'No specific task')}}
        Context: {{state.get('task_context', {{}})}}

        Consider:
        1. What are the key objectives?
        2. What resources or information do we need?
        3. What are the success criteria?'''
                + (
                    """
        4. Should this be delegated to subordinate teams?"""
                    if is_manager
                    else ""
                )
                + '''
        """)

        messages.append(analysis_prompt)

        # Get LLM analysis
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        state["messages"] = messages
        state["last_activity"] = datetime.utcnow()

        return state

    async def _plan_execution_node(self, state: {class_name}State) -> {class_name}State:
        """Plan the execution strategy"""
        messages = state["messages"]

        planning_prompt = HumanMessage(content="""
        Based on your analysis, create a detailed execution plan.
        Include specific steps, dependencies, and expected outcomes.
        """)

        messages.append(planning_prompt)
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        state["messages"] = messages
        return state'''
                + (
                    f"""

    def _should_delegate(self, state: {class_name}State) -> str:
        \"\"\"Determine if task should be delegated to subordinate teams\"\"\"
        # Parse the last message to check if delegation is recommended
        messages = state["messages"]
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                content = last_message.content.lower()
                if any(team in content for team in self.manages_teams):
                    return "delegate"
        return "execute"

    async def _delegate_tasks_node(self, state: {class_name}State) -> {class_name}State:
        \"\"\"Delegate tasks to subordinate teams via A2A\"\"\"
        messages = state["messages"]

        delegation_prompt = HumanMessage(content=f\"\"\"
        You manage these teams: {{', '.join(self.manages_teams)}}

        For any tasks that should be delegated, specify:
        1. Which team should handle it
        2. Clear task description
        3. Success criteria (list of measurable outcomes)
        4. Deadline (if applicable)
        5. Any relevant context

        Format your response as structured delegation requests.
        \"\"\")

        messages.append(delegation_prompt)
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        # In a real implementation, parse the response and send A2A requests
        # This is a placeholder for the actual delegation logic

        state["messages"] = messages
        return state{a2a_methods}"""
                    if is_manager
                    else ""
                )
                + f'''

    async def _execute_task_node(self, state: {class_name}State) -> {class_name}State:
        """Execute the task directly"""
        messages = state["messages"]

        execution_prompt = HumanMessage(content="""
        Execute the planned approach. Use available tools as needed.
        Provide detailed results and any issues encountered.
        """)

        messages.append(execution_prompt)
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        state["messages"] = messages
        return state

    async def _review_results_node(self, state: {class_name}State) -> {class_name}State:
        """Review and validate results"""
        messages = state["messages"]

        review_prompt = HumanMessage(content="""
        Review the execution results:
        1. Were the objectives met?
        2. Are there any issues or gaps?
        3. What are the key outcomes?
        4. Any recommendations for next steps?
        """)

        messages.append(review_prompt)
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        state["messages"] = messages
        return state

    async def _finalize_node(self, state: {class_name}State) -> {class_name}State:
        """Finalize the task and prepare response"""
        state["last_activity"] = datetime.utcnow()

        # Log task completion
        self.logger.info(f"Task completed by {member.role}")

        return state

    async def _startup_tasks(self) -> None:
        """Agent-specific startup tasks"""
        self.logger.info(f"Starting {member.role} agent")
        # Add any specific startup logic here

    async def _shutdown_tasks(self) -> None:
        """Agent-specific shutdown tasks"""
        self.logger.info(f"Shutting down {member.role} agent")
        # Add any specific shutdown logic here

    async def _cleanup_resources(self) -> None:
        """Agent-specific resource cleanup"""
        self.logger.info(f"Cleaning up resources for {member.role} agent")
        # Add any specific cleanup logic here

    def log_communication(self, message: str, to_agent: Optional[str] = None):
        """Log internal team communications naturally"""
        if to_agent:
            self.logger.info(f"[{member.role} → {{to_agent}}]: {{message}}")
        else:
            self.logger.info(f"[{member.role}]: {{message}}")

    def log_proposal(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a proposal message with rich context"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.PROPOSAL,
            to_agent=to_agent,
            metadata=metadata
        )
        self.log_communication(f"[PROPOSAL] {{message}}", to_agent)

    def log_challenge(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a challenge/skeptical message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.CHALLENGE,
            to_agent=to_agent,
            metadata=metadata
        )
        self.log_communication(f"[CHALLENGE] {{message}}", to_agent)

    def log_decision(self, message: str, **metadata):
        """Log a decision message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.DECISION,
            metadata=metadata
        )
        self.log_communication(f"[DECISION] {{message}}")

    def log_update(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a general update message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.UPDATE,
            to_agent=to_agent,
            metadata=metadata
        )
        self.log_communication(message, to_agent)

    async def process_message_with_logging(self, state: Dict, message: BaseMessage) -> Dict:
        """Process a message and log the conversation"""

        # Extract sender info from message metadata
        sender = message.additional_kwargs.get('sender', self.name)
        message_type = message.additional_kwargs.get('type', MessageType.UPDATE)

        # Log the message
        self.conversation_logger.log_message(
            agent_name=sender,
            message=message.content,
            message_type=message_type,
            metadata={{
                'state_id': state.get('agent_id'),
                'task': state.get('current_task')
            }}
        )

        return state
'''
            )

            agent_file = agents_dir / filename
            with open(agent_file, "w") as f:
                f.write(agent_content)

        # Write __init__.py with imports
        init_content += "\n".join(agent_imports)
        init_content += "\n\n__all__ = ["
        init_content += ", ".join(
            f'"{member.role.replace(" ", "") + "Agent"}"'
            for member in team_spec.members
        )
        init_content += "]\n"

        init_file = agents_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write(init_content)

    def _generate_langgraph_state(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate state definitions for the team"""
        workflows_dir = team_dir / "workflows"

        state_content = f'''#!/usr/bin/env python3
"""
State definitions for {team_spec.name}
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TeamState(TypedDict):
    """Shared state for the entire team"""
    messages: Annotated[List[BaseMessage], add_messages]
    team_name: str
    current_objective: Optional[str]
    team_context: Dict[str, Any]
    agent_states: Dict[str, Dict[str, Any]]  # Individual agent states
    workflow_status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class TaskState(TypedDict):
    """State for individual tasks"""
    task_id: str
    description: str
    assigned_to: Optional[str]
    status: str  # pending, in_progress, completed, failed
    priority: str  # high, medium, low
    dependencies: List[str]
    results: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]


class CommunicationState(TypedDict):
    """State for tracking team communications"""
    sender: str
    recipients: List[str]
    message_type: str  # intra_team, inter_team
    content: str
    timestamp: datetime
    thread_id: Optional[str]
    metadata: Dict[str, Any]
'''

        state_file = workflows_dir / "state_definitions.py"
        with open(state_file, "w") as f:
            f.write(state_content)

        # Create __init__.py for workflows
        init_file = workflows_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write('"""Workflow definitions for the team"""\n')

    def _generate_langgraph_workflow(
        self, team_spec: TeamSpecification, team_dir: Path
    ):
        """Generate the main workflow orchestrator for LangGraph"""
        workflow_content = f'''#!/usr/bin/env python3
"""
{team_spec.name} Workflow Orchestrator
LangGraph-based team coordination
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage, SystemMessage

from workflows.state_definitions import TeamState, TaskState
from agents import (
{chr(10).join(f"    {member.role.replace(' ', '')}Agent," for member in team_spec.members)}
)

# Set up logging
log_dir = Path("/logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_dir / '{team_spec.name}_communications.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s'
)


class {team_spec.name.replace("-", " ").title().replace(" ", "")}Workflow:
    """
    Orchestrates the {team_spec.name} using LangGraph state machines

    This team follows a {"hierarchical" if any(m.manages_teams for m in team_spec.members) else "collaborative"} pattern
    with well-defined state transitions and checkpointing.
    """

    def __init__(self, checkpoint_url: Optional[str] = None):
        self.logger = logging.getLogger("{team_spec.name}")
        self.team_name = "{team_spec.name}"
        self.agents = self._initialize_agents()
        self.workflow = self._create_workflow()

        # Set up checkpointing for production
        if checkpoint_url:
            self.checkpointer = PostgresSaver.from_conn_string(checkpoint_url)
        else:
            from langgraph.checkpoint.memory import MemorySaver
            self.checkpointer = MemorySaver()

        # Compile the workflow
        self.app = self.workflow.compile(checkpointer=self.checkpointer)

        self.logger.info(f"Initialized {team_spec.name} workflow with {{len(self.agents)}} agents")

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all team agents"""
        agents = {{}}

'''

        # Add agent initialization
        for member in team_spec.members:
            agent_var = member.role.lower().replace(" ", "_")
            class_name = member.role.replace(" ", "") + "Agent"
            workflow_content += f"""        # Initialize {member.role}
        agents["{member.role}"] = {class_name}()
        self.logger.info(f"Initialized {member.role}")

"""

        workflow_content += '''        return agents

    def _create_workflow(self) -> StateGraph:
        """Create the team workflow graph"""
        workflow = StateGraph(TeamState)

        # Add nodes for team coordination
        workflow.add_node("initialize_team", self._initialize_team_node)
        workflow.add_node("assign_roles", self._assign_roles_node)
        workflow.add_node("coordinate_work", self._coordinate_work_node)
        workflow.add_node("aggregate_results", self._aggregate_results_node)
        workflow.add_node("finalize", self._finalize_node)

        # Add individual agent nodes
'''

        for member in team_spec.members:
            node_name = member.role.lower().replace(" ", "_") + "_work"
            workflow_content += (
                f'        workflow.add_node("{node_name}", self._{node_name}_node)\n'
            )

        workflow_content += """
        # Set entry point
        workflow.set_entry_point("initialize_team")

        # Define the workflow edges
        workflow.add_edge("initialize_team", "assign_roles")
        workflow.add_edge("assign_roles", "coordinate_work")

        # Add conditional edges for agent coordination
        workflow.add_conditional_edges(
            "coordinate_work",
            self._route_to_agents,
            {
"""

        # Add routing for each agent
        for member in team_spec.members:
            node_name = member.role.lower().replace(" ", "_") + "_work"
            workflow_content += f'                "{member.role}": "{node_name}",\n'

        workflow_content += """                "aggregate": "aggregate_results"
            }
        )

        # Connect agent nodes back to coordination or aggregation
"""

        for member in team_spec.members:
            node_name = member.role.lower().replace(" ", "_") + "_work"
            workflow_content += (
                f'        workflow.add_edge("{node_name}", "coordinate_work")\n'
            )

        workflow_content += '''
        workflow.add_edge("aggregate_results", "finalize")
        workflow.add_edge("finalize", END)

        return workflow

    async def _initialize_team_node(self, state: TeamState) -> TeamState:
        """Initialize the team for a new objective"""
        self.logger.info(f"Initializing team for objective: {state.get('current_objective')}")

        state["team_name"] = self.team_name
        state["workflow_status"] = "initialized"
        state["created_at"] = datetime.utcnow()
        state["updated_at"] = datetime.utcnow()
        state["agent_states"] = {}

        # Add system message explaining team structure
        system_msg = SystemMessage(content=f"""
        This is the {self.team_name} with the following members:
{chr(10).join(f"        - {member.role}: {', '.join(member.responsibilities[:2])}" for member in team_spec.members)}

        Team communication pattern: {"Hierarchical with managers" if any(m.manages_teams for m in team_spec.members) else "Collaborative peer-to-peer"}
        """)

        if "messages" not in state:
            state["messages"] = []
        state["messages"].insert(0, system_msg)

        return state

    async def _assign_roles_node(self, state: TeamState) -> TeamState:
        """Assign roles and responsibilities based on the objective"""
        self.logger.info("Assigning roles to team members")

        # In a real implementation, this would analyze the objective
        # and assign specific tasks to team members
        state["workflow_status"] = "roles_assigned"
        state["updated_at"] = datetime.utcnow()

        return state

    async def _coordinate_work_node(self, state: TeamState) -> TeamState:
        """Coordinate work between team members"""
        self.logger.info("Coordinating team work")

        state["workflow_status"] = "coordinating"
        state["updated_at"] = datetime.utcnow()

        return state

    def _route_to_agents(self, state: TeamState) -> str:
        """Route to specific agents based on current needs"""
        # This is a simplified routing logic
        # In production, this would analyze the state and route intelligently

        # Check if all agents have completed their work
        agent_states = state.get("agent_states", {})
        all_completed = all(
            agent_state.get("status") == "completed"
            for agent_state in agent_states.values()
        ) if agent_states else False

        if all_completed and agent_states:
            return "aggregate"

        # Route to the next available agent
        for member in [f.role for f in team_spec.members]:
            if member not in agent_states or agent_states[member].get("status") != "completed":
                return member

        return "aggregate"
'''

        # Add node methods for each agent
        for member in team_spec.members:
            node_name = member.role.lower().replace(" ", "_") + "_work"
            workflow_content += f'''
    async def _{node_name}_node(self, state: TeamState) -> TeamState:
        """Execute work for {member.role}"""
        self.logger.info(f"{member.role} executing work")

        agent = self.agents["{member.role}"]

        # Process with the agent
        result = await agent.process_message(
            message=state.get("current_objective", ""),
            thread_id=state.get("metadata", {{}}).get("thread_id")
        )

        # Update agent state
        if "agent_states" not in state:
            state["agent_states"] = {{}}

        state["agent_states"]["{member.role}"] = {{
            "status": "completed",
            "result": result,
            "completed_at": datetime.utcnow()
        }}

        state["updated_at"] = datetime.utcnow()

        # Log natural communication
        agent.log_communication(f"Completed my portion of the task")

        return state
'''

        workflow_content += (
            '''
    async def _aggregate_results_node(self, state: TeamState) -> TeamState:
        """Aggregate results from all agents"""
        self.logger.info("Aggregating team results")

        state["workflow_status"] = "aggregating"
        state["updated_at"] = datetime.utcnow()

        # Compile results from all agents
        results = {}
        for agent_name, agent_state in state.get("agent_states", {}).items():
            if "result" in agent_state:
                results[agent_name] = agent_state["result"]

        state["metadata"]["aggregated_results"] = results

        return state

    async def _finalize_node(self, state: TeamState) -> TeamState:
        """Finalize the team's work"""
        self.logger.info("Finalizing team work")

        state["workflow_status"] = "completed"
        state["updated_at"] = datetime.utcnow()

        return state

    async def execute_objective(self, objective: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a team objective using the workflow

        Args:
            objective: The objective to accomplish
            context: Optional context for the objective

        Returns:
            Results from the team execution
        """
        thread_id = str(uuid4())

        initial_state = {
            "messages": [HumanMessage(content=objective)],
            "team_name": self.team_name,
            "current_objective": objective,
            "team_context": context or {},
            "agent_states": {},
            "workflow_status": "starting",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {"thread_id": thread_id}
        }

        try:
            # Run the workflow
            config = {"configurable": {"thread_id": thread_id}}
            final_state = await self.app.ainvoke(initial_state, config)

            self.logger.info(f"Team objective completed: {objective}")

            return {
                "status": "success",
                "objective": objective,
                "results": final_state.get("metadata", {}).get("aggregated_results", {}),
                "team": self.team_name,
                "thread_id": thread_id
            }

        except Exception as e:
            self.logger.error(f"Failed to execute objective: {str(e)}")
            return {
                "status": "error",
                "objective": objective,
                "error": str(e),
                "team": self.team_name,
                "thread_id": thread_id
            }

    def get_team_status(self) -> Dict[str, Any]:
        """Get the current status of the team"""
        return {
            "team_name": self.team_name,
            "framework": "langgraph",
            "agents": list(self.agents.keys()),
            "status": "active",
            "workflow_type": "state_machine"
        }


# Create a singleton instance
_workflow_instance = None

def get_workflow(checkpoint_url: Optional[str] = None):
    """Get or create the team workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = '''
            + team_spec.name.replace("-", " ").title().replace(" ", "")
            + """Workflow(checkpoint_url=checkpoint_url)
    return _workflow_instance


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        workflow = get_workflow()
        result = await workflow.execute_objective("Develop a comprehensive marketing strategy for Q2")
        print(result)

    asyncio.run(main())
"""
        )

        workflow_file = team_dir / "workflows" / "team_workflow.py"
        with open(workflow_file, "w") as f:
            f.write(workflow_content)

    def _generate_langgraph_deployable_script(
        self, team_spec: TeamSpecification, team_dir: Path
    ):
        """Generate deployment script for LangGraph team"""
        script_content = f'''#!/usr/bin/env python3
"""
Make Deployable Team Script for LangGraph
Creates a containerized version of the team that can run as a single K8s pod
"""

import os
import shutil
from pathlib import Path


def create_deployable_team():
    """Create a deployable version of the team"""
    team_dir = Path(__file__).parent

    print("🚀 Creating deployable LangGraph team package...")

    # Create team_server.py - the main entry point
    create_team_server(team_dir)

    # Create Dockerfile
    create_dockerfile(team_dir)

    # Create requirements.txt
    create_requirements(team_dir)

    # Create health check endpoint
    create_health_check(team_dir)

    print("✅ LangGraph team is ready for containerization!")
    print("📦 Next steps:")
    print("   1. Build: docker build -t elf-automations/{team_spec.name} .")
    print("   2. Push to registry accessible by your K8s cluster")
    print("   3. Update k8s/deployment.yaml with correct image")
    print("   4. Commit to GitOps repo for ArgoCD")


def create_team_server(team_dir: Path):
    """Create the main server that runs the LangGraph team"""
    server_content = """#!/usr/bin/env python3
\"\"\"
Team Server - Runs the LangGraph team with A2A protocol endpoint
\"\"\"

import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any

# Import the workflow
from workflows.team_workflow import get_workflow

# Import A2A server components
from agents.distributed.a2a.server import A2AServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="{team_spec.name} API")

# Initialize the workflow
workflow_instance = None

@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize the workflow on startup\"\"\"
    global workflow_instance
    logger.info("Initializing {team_spec.name} workflow...")

    # Get checkpoint URL from environment
    checkpoint_url = os.getenv("CHECKPOINT_DATABASE_URL")
    workflow_instance = get_workflow(checkpoint_url)

    logger.info("Team workflow initialized successfully")

@app.get("/health")
async def health_check():
    \"\"\"Health check endpoint\"\"\"
    return {{"status": "healthy", "team": "{team_spec.name}", "framework": "langgraph"}}

@app.post("/task")
async def execute_task(request: Dict[str, Any]):
    \"\"\"Execute a task via A2A protocol\"\"\"
    try:
        task_description = request.get("task", "")
        context = request.get("context", {{}})

        logger.info(f"Received task: {{task_description[:100]}}...")

        # Execute with the workflow
        result = await workflow_instance.execute_objective(task_description, context)

        return JSONResponse(content={{
            "status": "success",
            "result": result,
            "team": "{team_spec.name}"
        }})

    except Exception as e:
        logger.error(f"Error executing task: {{str(e)}}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/capabilities")
async def get_capabilities():
    \"\"\"Return team capabilities for A2A discovery\"\"\"
    return {{
        "team_name": "{team_spec.name}",
        "department": "{team_spec.department}",
        "framework": "langgraph",
        "workflow_type": "state_machine",
        "agents": workflow_instance.get_team_status()["agents"] if workflow_instance else [],
        "accepts_tasks": True,
        "a2a_version": "1.0",
        "features": [
            "stateful_workflows",
            "checkpointing",
            "parallel_execution",
            "conditional_routing"
        ]
    }}

@app.get("/workflow/state")
async def get_workflow_state():
    \"\"\"Get the current workflow state (for debugging)\"\"\"
    if workflow_instance:
        return workflow_instance.get_team_status()
    return {{"error": "Workflow not initialized"}}

if __name__ == "__main__":
    # Run the server
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
\"\"\"

    with open(team_dir / "team_server.py", "w") as f:
        f.write(server_content)


def create_dockerfile(team_dir: Path):
    \"\"\"Create Dockerfile for the LangGraph team\"\"\"
    dockerfile_content = \"\"\"FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\\\
    build-essential \\\\
    postgresql-client \\\\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy team source code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create logs directory
RUN mkdir -p /logs

# Expose A2A port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\\\
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run the team server
CMD ["python", "team_server.py"]
\"\"\"

    with open(team_dir / "Dockerfile", "w") as f:
        f.write(dockerfile_content)


def create_requirements(team_dir: Path):
    \"\"\"Create requirements.txt with all dependencies\"\"\"
    requirements = \"\"\"# Core dependencies
langgraph>=0.2.0
langchain>=0.2.0
langchain-openai>=0.1.0
langchain-anthropic>=0.1.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# State management
redis>=5.0.0
psycopg2-binary>=2.9.0

# A2A communication
httpx>=0.25.0
websockets>=12.0

# Monitoring and logging
structlog>=23.0.0
prometheus-client>=0.19.0

# Utilities
python-dotenv>=1.0.0
tenacity>=8.2.0
\"\"\"

    with open(team_dir / "requirements.txt", "w") as f:
        f.write(requirements)


def create_health_check(team_dir: Path):
    \"\"\"Create a simple health check script\"\"\"
    health_check_content = \"\"\"#!/usr/bin/env python3
import requests
import sys

try:
    response = requests.get("http://localhost:8080/health", timeout=3)
    if response.status_code == 200:
        print("✅ Health check passed")
        sys.exit(0)
    else:
        print(f"❌ Health check failed: {{response.status_code}}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Health check error: {{e}}")
    sys.exit(1)
\"\"\"

    health_check_file = team_dir / "health_check.py"
    with open(health_check_file, "w") as f:
        f.write(health_check_content)
    os.chmod(health_check_file, 0o755)


if __name__ == "__main__":
    create_deployable_team()
'''

        script_file = team_dir / "make-deployable-team.py"
        with open(script_file, "w") as f:
            f.write(script_content)

        # Make script executable
        os.chmod(script_file, 0o755)

    def _generate_langgraph_readme(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate README for LangGraph team"""
        readme_content = f"""# {team_spec.name.replace("-", " ").title()}

## Overview
{team_spec.purpose}

**Framework**: LangGraph (State Machine-based)
**Department**: {team_spec.department}
**Workflow Type**: {"Hierarchical State Machine" if any(m.manages_teams for m in team_spec.members) else "Collaborative State Machine"}
**Team Size**: {len(team_spec.members)} agents
**LLM Provider**: {team_spec.llm_provider}
**LLM Model**: {team_spec.llm_model}

## Team Members

"""
        for i, member in enumerate(team_spec.members, 1):
            is_manager = bool(member.manages_teams)
            role_type = " (Manager)" if is_manager else ""
            readme_content += f"{i}. **{member.role}**{role_type}\n"
            for resp in member.responsibilities:
                readme_content += f"   - {resp}\n"
            readme_content += f"   - Skills: {', '.join(member.skills)}\n"
            if is_manager:
                readme_content += f"   - Manages: {', '.join(member.manages_teams)}\n"
            readme_content += "\n"

        readme_content += """## LangGraph Architecture

### State Management
This team uses LangGraph's state machine architecture with:
- **Checkpointing**: Persistent state storage for fault tolerance
- **Conditional Routing**: Dynamic workflow paths based on state
- **Parallel Execution**: Agents can work concurrently when appropriate
- **State Transitions**: Well-defined transitions between workflow nodes

### Workflow Nodes
"""

        # List the main workflow nodes
        readme_content += """1. **Initialize Team**: Sets up team state and context
2. **Assign Roles**: Distributes work based on agent capabilities
3. **Coordinate Work**: Manages agent interactions and dependencies
"""

        for member in team_spec.members:
            node_name = member.role.lower().replace(" ", "_") + "_work"
            readme_content += (
                f"4. **{member.role} Work**: Executes {member.role}-specific tasks\n"
            )

        readme_content += """5. **Aggregate Results**: Combines outputs from all agents
6. **Finalize**: Completes the workflow and returns results

### Communication Patterns

#### Intra-Team Communication (Within Team)
The team uses LangGraph's message passing system for coordination:
"""

        # Show internal communication patterns
        for member in team_spec.members:
            if member.communicates_with:
                readme_content += f"- **{member.role}** communicates with: {', '.join(member.communicates_with)}\n"

        # Add inter-team communication section if there are managers
        managers_with_teams = [m for m in team_spec.members if m.manages_teams]
        if managers_with_teams:
            readme_content += f"""
#### Inter-Team Communication (A2A Protocol)
Managers communicate with subordinate teams using formal A2A messages:

"""
            for manager in managers_with_teams:
                readme_content += f"**{manager.role}** manages via A2A:\n"
                for team in manager.manages_teams:
                    readme_content += f"- `{team}`\n"
                readme_content += "\n"

        readme_content += f"""
## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the workflow directly
python workflows/team_workflow.py

# Or run the FastAPI server
python team_server.py
```

### Environment Variables
```bash
# LLM Configuration
"""

        if team_spec.llm_provider == "OpenAI":
            readme_content += "OPENAI_API_KEY=your-api-key\n"
        else:
            readme_content += "ANTHROPIC_API_KEY=your-api-key\n"

        readme_content += """
# AgentGateway Configuration
AGENT_GATEWAY_URL=http://agentgateway:3003

# Checkpoint Database (for production)
CHECKPOINT_DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Supabase Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

### Containerization
```bash
# Generate deployment files
python make-deployable-team.py

# Build Docker image
docker build -t elf-automations/{team_spec.name} .

# Run container
docker run -p 8080:8080 -e OPENAI_API_KEY=$OPENAI_API_KEY elf-automations/{team_spec.name}
```

### Kubernetes Deployment
```bash
# Apply the deployment
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods -l app={team_spec.name}
```

## API Endpoints

The team exposes these endpoints when deployed:

- `GET /health` - Health check
- `GET /capabilities` - Team capabilities and metadata
- `POST /task` - Execute a task with the team
- `GET /workflow/state` - Current workflow state (debugging)

### Example Task Request
```json
{{
  "task": "Develop a comprehensive marketing campaign for our new product launch",
  "context": {{
    "product": "AI Assistant Tool",
    "target_audience": "Small businesses",
    "budget": "$50,000",
    "timeline": "Q2 2025"
  }}
}}
```

### Example Response
```json
{{
  "status": "success",
  "result": {{
    "objective": "Develop marketing campaign",
    "results": {{
      "Marketing Manager": {{"campaign_strategy": "..."}},
      "Content Creator": {{"content_calendar": "..."}},
      "Social Media Manager": {{"social_strategy": "..."}}
    }},
    "team": "{team_spec.name}",
    "thread_id": "abc123"
  }}
}}
```

## Monitoring

### Logs
- Team communications: `/logs/{team_spec.name}_communications.log`
- Structured logs include natural language exchanges between agents
- A2A communications are logged separately with full traceability

### State Persistence
- LangGraph checkpoints are stored in PostgreSQL (production)
- In-memory checkpointing for development
- Full workflow replay capability from any checkpoint

## LangGraph Best Practices

1. **State Immutability**: Never modify state directly, always return new state
2. **Error Handling**: Each node includes error handling and recovery
3. **Checkpointing**: Critical state changes are checkpointed
4. **Conditional Logic**: Use graph edges for flow control, not in-node logic
5. **Parallel Execution**: Leverage when agents can work independently
6. **Message History**: Maintained in state for full context

## Development Tips

1. Test individual agents: `python -m agents.{agent_name}`
2. Visualize workflow: LangGraph can export workflow diagrams
3. Debug with checkpoints: Inspect state at each transition
4. Monitor with logs: Natural language logs help understand team dynamics
"""

        readme_file = team_dir / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme_content)

    def _generate_k8s_manifests(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate Kubernetes manifests for the team"""
        k8s_dir = team_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)

        manifest = (
            f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {team_spec.name}
  namespace: elf-automations
  labels:
    app: {team_spec.name}
    team-type: {team_spec.department}
    framework: {team_spec.framework.lower()}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {team_spec.name}
  template:
    metadata:
      labels:
        app: {team_spec.name}
        team-type: {team_spec.department}
        framework: {team_spec.framework.lower()}
    spec:
      containers:
      - name: team-runtime
        image: elf-automations/{team_spec.name}:latest
        ports:
        - containerPort: 8080
          name: a2a
        env:
        - name: TEAM_NAME
          value: "{team_spec.name}"
        - name: TEAM_TYPE
          value: "{team_spec.department}"
        - name: FRAMEWORK
          value: "{team_spec.framework}"
        - name: AGENT_GATEWAY_URL
          value: "http://agentgateway:3003"
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: supabase-credentials
              key: url
        - name: SUPABASE_KEY
          valueFrom:
            secretKeyRef:
              name: supabase-credentials
              key: key"""
            + (
                f"""
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-api-keys
              key: openai-api-key"""
                if team_spec.llm_provider == "OpenAI"
                else f"""
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-api-keys
              key: anthropic-api-key"""
            )
            + """
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: team-config
          mountPath: /config
      volumes:
      - name: team-config
        configMap:
          name: {team_spec.name}-config
---
apiVersion: v1
kind: Service
metadata:
  name: {team_spec.name}-service
  namespace: elf-automations
spec:
  selector:
    app: {team_spec.name}
  ports:
  - port: 8080
    targetPort: 8080
    name: a2a
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {team_spec.name}-config
  namespace: elf-automations
data:
  team.yaml: |
{yaml.dump({"name": team_spec.name, "framework": team_spec.framework, "members": [m.role for m in team_spec.members]}, default_flow_style=False, indent=4)}
"""
        )

        manifest_file = k8s_dir / "deployment.yaml"
        with open(manifest_file, "w") as f:
            f.write(manifest)

    def _generate_a2a_config(self, team_spec: TeamSpecification, config_dir: Path):
        """Generate A2A communication configuration"""
        a2a_config = {
            "team_name": team_spec.name,
            "capabilities": [member.role for member in team_spec.members],
            "accepts_requests": True,
            "a2a_port": 8080,
            "internal_communication": {
                "framework": team_spec.framework,
                "logging": True,
                "log_path": f"/logs/{team_spec.name}_internal_comms.log",
            },
            "communication_pattern": team_spec.communication_pattern,
        }

        a2a_file = config_dir / "a2a_config.yaml"
        with open(a2a_file, "w") as f:
            yaml.dump(a2a_config, f, default_flow_style=False)

    def _generate_team_documentation(
        self, team_spec: TeamSpecification, team_dir: Path
    ):
        """Generate comprehensive team documentation"""
        doc_content = f"""# {team_spec.name}

## Overview
**Framework:** {team_spec.framework}
**Department:** {team_spec.department}
**Created:** {datetime.now().strftime("%Y-%m-%d")}

### Purpose
{team_spec.purpose}

### Original Description
> {team_spec.natural_language_description}

## Team Composition

### Size Analysis
{team_spec.size_validation}

### Team Members

"""

        for member in team_spec.members:
            doc_content += f"""#### {member.role}

**Responsibilities:**
{chr(10).join(f"- {r}" for r in member.responsibilities)}

**Skills:**
{', '.join(member.skills)}

**System Prompt:**
> {member.system_prompt}

**Communicates With:** {', '.join(member.communicates_with)}

---

"""

        doc_content += f"""## Communication Pattern

The following diagram shows how team members communicate:

```mermaid
graph TD
"""

        for member, connections in team_spec.communication_pattern.items():
            for connection in connections:
                doc_content += f"    {member.replace(' ', '_')} --> {connection.replace(' ', '_')}\n"

        doc_content += """```

## Deployment

### Kubernetes
```bash
kubectl apply -f k8s-deployment.yaml
```

### Local Development
```bash
python {team_spec.name}.py
```

## Integration

This team integrates with the ElfAutomations platform via:
- **A2A Protocol**: For inter-team communication
- **AgentGateway**: For MCP tool access
- **Supabase**: For structured data storage

## Monitoring

Team communications are logged to:
- Internal: `/logs/{team_spec.name}_internal_comms.log`
- Inter-team: Via A2A protocol monitoring
"""

        doc_file = team_dir / "README.md"
        with open(doc_file, "w") as f:
            f.write(doc_content)

    def _generate_readme(self, team_spec: TeamSpecification, team_dir: Path):
        """Generate README.md for the team"""
        readme_content = f"""# {team_spec.name.replace("-", " ").title()}

## Overview
{team_spec.purpose}

**Framework**: {team_spec.framework}
**Department**: {team_spec.department}
**Process Type**: {"Hierarchical" if len(team_spec.members) > 4 else "Sequential"} ({len(team_spec.members)} members)
**LLM Provider**: {team_spec.llm_provider}
**LLM Model**: {team_spec.llm_model}

## Team Members

"""
        for i, member in enumerate(team_spec.members, 1):
            is_manager = "Manager" in member.role or "Lead" in member.role
            role_type = " (Manager)" if is_manager else ""
            readme_content += f"{i}. **{member.role}**{role_type}\n"
            for resp in member.responsibilities:
                readme_content += f"   - {resp}\n"
            readme_content += f"   - Skills: {', '.join(member.skills)}\n\n"

        readme_content += f"""## Communication Patterns

### Intra-Team Communication (Within Team)
The team follows a {"hierarchical" if len(team_spec.members) > 4 else "sequential"} communication pattern"""

        if len(team_spec.members) > 4:
            readme_content += " with managers who can delegate tasks to team members."
        else:
            readme_content += " where tasks flow sequentially between team members."

        readme_content += """

Team members communicate naturally using the framework's built-in collaboration features:
"""
        # Show internal communication patterns
        for member in team_spec.members:
            if member.communicates_with:
                readme_content += f"- **{member.role}** communicates with: {', '.join(member.communicates_with)}\n"

        # Add inter-team communication section if there are managers
        managers_with_teams = [m for m in team_spec.members if m.manages_teams]
        if managers_with_teams:
            readme_content += f"""
### Inter-Team Communication (A2A Protocol)
This team has managers who communicate with subordinate teams using formal A2A messages:

"""
            for manager in managers_with_teams:
                readme_content += (
                    f"**{manager.role}** manages the following teams via A2A:\n"
                )
                for team in manager.manages_teams:
                    readme_content += f"- `{team}`\n"
                readme_content += "\n"

            readme_content += """#### A2A Communication Flow:
1. **Manager formulates request**: Creates detailed task with success criteria, deadlines, and context
2. **A2A message sent**: Formal request sent to subordinate team's manager
3. **Team executes**: Subordinate team works on the task internally
4. **Results returned**: Deliverables and status updates sent back via A2A

This separation ensures:
- Clear accountability and tracking
- Proper team boundaries and autonomy
- Scalable communication as organization grows
- Audit trail for all inter-team requests
"""

        readme_content += f"""

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the crew directly
python crew.py
```

### Containerization
```bash
# Generate deployment files
python make-deployable-team.py

# Build Docker image
docker build -t elf-automations/{team_spec.name} .

# Run container
docker run -p 8090:8090 elf-automations/{team_spec.name}
```

### Kubernetes Deployment
```bash
# Apply the deployment
kubectl apply -f k8s/deployment.yaml
```

## API Endpoints

Once deployed, the team exposes the following endpoints:

- `GET /health` - Health check
- `GET /capabilities` - Get team capabilities and status
- `POST /task` - Execute a task with the team

### Example Task Request
```json
{{
  "description": "Your task description here",
  "context": {{
    "key": "value"
  }}
}}
```

## Configuration

### Team Configuration
See `config/team_config.yaml` for agent definitions and team settings.

### A2A Configuration
See `config/a2a_config.yaml` for inter-team communication settings.

### LLM Configuration
This team is configured to use **{team_spec.llm_provider}** with model **{team_spec.llm_model}**.

Required environment variables:
"""

        if team_spec.llm_provider == "OpenAI":
            readme_content += "- `OPENAI_API_KEY`: Your OpenAI API key\n"
        else:  # Anthropic
            readme_content += "- `ANTHROPIC_API_KEY`: Your Anthropic API key\n"

        readme_content += f"""
## Logs
Team communications are logged to `/logs/{team_spec.name}_communications.log` for natural language analysis and optimization.
"""

        readme_file = team_dir / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme_content)

    def _register_team_in_registry(self, team_spec: TeamSpecification) -> bool:
        """Register the team in the Team Registry (Supabase)"""
        if not REGISTRY_AVAILABLE:
            self.console.print(
                "[yellow]Team Registry not available - skipping registration[/yellow]"
            )
            return False

        try:
            client = get_supabase_client()

            # Extract display name and reporting info
            display_name = team_spec.name.replace("-", " ").title()
            reports_to = None

            # Find the manager to determine reporting structure
            for member in team_spec.members:
                if "Manager" in member.role or "Lead" in member.role:
                    # Check if they have A2A reporting in their prompt
                    if (
                        "report to" in member.system_prompt
                        and "via A2A" in member.system_prompt
                    ):
                        # Extract who they report to
                        import re

                        match = re.search(
                            r"report to ([^.]+) via A2A", member.system_prompt
                        )
                        if match:
                            reports_to = match.group(1).strip()
                    break

            # Register the team
            team_data = {
                "name": team_spec.name,
                "display_name": display_name,
                "department": team_spec.department,
                "placement": team_spec.name.replace("-team", "").replace("-", "."),
                "purpose": team_spec.purpose,
                "framework": team_spec.framework,
                "llm_provider": team_spec.llm_provider,
                "llm_model": team_spec.llm_model,
                "status": "active",
            }

            # Insert team
            result = client.table("teams").insert(team_data).execute()
            team_id = result.data[0]["id"]

            self.console.print(f"[green]✓ Team registered with ID: {team_id}[/green]")

            # Register team members
            for member in team_spec.members:
                member_data = {
                    "team_id": team_id,
                    "role": member.role,
                    "is_manager": "Manager" in member.role or "Lead" in member.role,
                    "responsibilities": member.responsibilities,
                    "skills": member.skills,
                    "system_prompt": member.system_prompt,
                }
                client.table("team_members").insert(member_data).execute()

            self.console.print(
                f"[green]✓ Registered {len(team_spec.members)} team members[/green]"
            )

            # Register reporting relationship if exists
            if reports_to:
                if reports_to.startswith("Chief") and reports_to.endswith("Officer"):
                    # Reporting to executive
                    rel_data = {
                        "child_team_id": team_id,
                        "parent_entity_type": "executive",
                        "parent_entity_name": reports_to,
                        "relationship_type": "reports_to",
                    }
                    client.table("team_relationships").insert(rel_data).execute()

                    # Also update executive management
                    exec_data = {
                        "executive_role": reports_to,
                        "managed_team_id": team_id,
                    }
                    client.table("executive_management").insert(exec_data).execute()

                    self.console.print(
                        f"[green]✓ Registered reporting relationship to {reports_to}[/green]"
                    )

                    # Generate patch for executive team configuration
                    self._generate_executive_patch(reports_to, team_spec.name)
                else:
                    # Reporting to another team
                    rel_data = {
                        "child_team_id": team_id,
                        "parent_entity_type": "team",
                        "parent_entity_name": reports_to,
                        "relationship_type": "reports_to",
                    }
                    client.table("team_relationships").insert(rel_data).execute()

                    self.console.print(
                        f"[green]✓ Registered reporting relationship to {reports_to}[/green]"
                    )

            # Register intra-team communication patterns
            for (
                member_role,
                communicates_with,
            ) in team_spec.communication_pattern.items():
                for target_role in communicates_with:
                    comm_data = {
                        "team_id": team_id,
                        "from_role": member_role,
                        "to_role": target_role,
                        "communication_type": "collaborates",
                    }
                    try:
                        client.table("team_communication_patterns").insert(
                            comm_data
                        ).execute()
                    except:
                        # Ignore duplicates
                        pass

            # Log the creation
            audit_data = {
                "team_id": team_id,
                "action": "created",
                "description": f"Team {team_spec.name} created via team-factory",
                "performed_by": "team-factory",
                "details": {
                    "framework": team_spec.framework,
                    "member_count": len(team_spec.members),
                    "reports_to": reports_to,
                },
            }
            client.table("team_audit_log").insert(audit_data).execute()

            self.console.print(
                "[green]✓ Team successfully registered in Team Registry[/green]"
            )
            return True

        except Exception as e:
            self.console.print(f"[red]✗ Failed to register team: {str(e)}[/red]")
            return False

    def _generate_executive_patch(self, executive_role: str, new_team_name: str):
        """Generate a patch file to update executive team configuration"""
        patch_dir = self.teams_dir / "executive-team" / "patches"
        patch_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        patch_file = patch_dir / f"add_{new_team_name}_{timestamp}.yaml"

        patch_content = f"""# Patch to add {new_team_name} to {executive_role}'s managed teams
# Generated by team-factory on {datetime.now().isoformat()}
#
# Apply this patch to update the executive team's configuration
# to include the newly created {new_team_name}

executive_updates:
  - role: "{executive_role}"
    add_managed_teams:
      - "{new_team_name}"

# Instructions:
# 1. Review this patch
# 2. Apply to executive team configuration
# 3. Rebuild and redeploy executive team
# 4. Commit both team creation and this patch to GitOps repo
"""

        with open(patch_file, "w") as f:
            f.write(patch_content)

        self.console.print(f"\n[yellow]📝 Generated executive team patch:[/yellow]")
        self.console.print(f"   {patch_file}")
        self.console.print(
            "[dim]   Apply this patch to update executive team configuration[/dim]"
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Team Factory - Create teams from natural language descriptions"
    )
    parser.add_argument("--config", help="Path to configuration file", default=None)
    parser.add_argument(
        "--modify-prompt", action="store_true", help="Modify an existing agent's prompt"
    )
    parser.add_argument("--team", help="Team name (for modify-prompt)")
    parser.add_argument("--agent", help="Agent name (for modify-prompt)")

    args = parser.parse_args()

    factory = TeamFactory()

    if args.modify_prompt:
        if not args.team or not args.agent:
            console.print(
                "[red]Error: --team and --agent are required when using --modify-prompt[/red]"
            )
            parser.print_help()
            return

        factory.modify_agent_prompt(args.team, args.agent)
    else:
        factory.create_team()


if __name__ == "__main__":
    main()
