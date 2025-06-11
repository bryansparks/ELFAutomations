#!/usr/bin/env python3
"""
Intelligent Team Composition System
Uses LLM to propose optimal team rosters based on purpose and context
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import openai
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


@dataclass
class ProposedMember:
    """Represents a proposed team member"""

    role: str
    purpose: str
    key_responsibilities: List[str]
    required_skills: List[str]
    personality_traits: List[str]
    interaction_style: str
    reporting_to: Optional[str] = None
    manages: List[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class TeamCompositionProposal:
    """Complete team composition proposal"""

    team_name: str
    team_purpose: str
    proposed_size: int
    members: List[ProposedMember]
    team_dynamics: str
    success_factors: List[str]
    potential_challenges: List[str]
    rationale: str


class IntelligentTeamComposer:
    """
    Uses LLM to propose optimal team compositions
    """

    def __init__(self):
        self.console = console

        # Knowledge base of successful team patterns
        self.team_patterns = {
            "innovation": {
                "key_roles": ["visionary", "implementer", "skeptic", "researcher"],
                "optimal_size": 5,
                "dynamics": "Creative tension with structured execution",
            },
            "execution": {
                "key_roles": [
                    "manager",
                    "specialist",
                    "coordinator",
                    "quality_checker",
                ],
                "optimal_size": 4,
                "dynamics": "Clear hierarchy with efficient workflows",
            },
            "analysis": {
                "key_roles": [
                    "lead_analyst",
                    "data_specialist",
                    "domain_expert",
                    "visualizer",
                ],
                "optimal_size": 4,
                "dynamics": "Collaborative deep-dive with peer review",
            },
            "customer_facing": {
                "key_roles": [
                    "relationship_manager",
                    "technical_expert",
                    "communicator",
                    "problem_solver",
                ],
                "optimal_size": 5,
                "dynamics": "Empathetic service with technical backing",
            },
        }

        # Role archetypes with characteristics
        self.role_archetypes = {
            "leader": {
                "traits": ["decisive", "strategic", "delegator"],
                "skills": ["planning", "communication", "conflict_resolution"],
            },
            "innovator": {
                "traits": ["creative", "risk-taking", "visionary"],
                "skills": ["ideation", "prototyping", "trend_analysis"],
            },
            "executor": {
                "traits": ["detail-oriented", "reliable", "methodical"],
                "skills": [
                    "project_management",
                    "process_optimization",
                    "quality_control",
                ],
            },
            "analyst": {
                "traits": ["analytical", "objective", "thorough"],
                "skills": ["data_analysis", "pattern_recognition", "reporting"],
            },
            "skeptic": {
                "traits": ["questioning", "risk-aware", "thorough"],
                "skills": ["critical_thinking", "risk_assessment", "validation"],
            },
            "connector": {
                "traits": ["collaborative", "empathetic", "communicative"],
                "skills": ["relationship_building", "negotiation", "coordination"],
            },
        }

    def propose_team_composition(
        self, team_request: str, organizational_context: Optional[Dict] = None
    ) -> TeamCompositionProposal:
        """
        Propose optimal team composition based on natural language request
        """
        self.console.print(f"\n[bold cyan]🤖 Analyzing team requirements...[/bold cyan]")

        # Step 1: Understand the request
        understanding = self._understand_team_request(
            team_request, organizational_context
        )

        # Step 2: Determine team pattern
        pattern = self._determine_team_pattern(understanding)

        # Step 3: Generate detailed proposal
        proposal = self._generate_team_proposal(
            understanding, pattern, organizational_context
        )

        # Step 4: Optimize for balance
        optimized_proposal = self._optimize_team_balance(proposal)

        return optimized_proposal

    def _understand_team_request(
        self, request: str, context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Use LLM to deeply understand the team request
        """
        understanding_prompt = f"""
        Analyze this team creation request and extract key requirements:

        Request: "{request}"

        Organizational Context:
        - Current Teams: {context.get('existing_teams', 'Not specified') if context else 'Not specified'}
        - Business Stage: {context.get('business_stage', 'Growth') if context else 'Growth'}
        - Industry: {context.get('industry', 'Technology') if context else 'Technology'}

        Extract and provide in JSON format:
        1. Primary purpose/mission
        2. Key objectives (3-5)
        3. Required capabilities
        4. Expected deliverables
        5. Interaction needs (who they'll work with)
        6. Time sensitivity (ongoing vs project-based)
        7. Innovation vs execution balance needed
        8. Suggested team name

        Be specific and actionable.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in organizational design and team composition.",
                    },
                    {"role": "user", "content": understanding_prompt},
                ],
                temperature=0.7,
            )

            understanding = json.loads(response.choices[0].message.content)
            return understanding

        except Exception as e:
            self.console.print(
                f"[yellow]Using pattern matching for understanding: {e}[/yellow]"
            )

            # Fallback understanding
            return {
                "primary_purpose": request[:100],
                "key_objectives": [
                    "Execute team mission",
                    "Collaborate effectively",
                    "Deliver results",
                ],
                "required_capabilities": self._extract_capabilities_from_request(
                    request
                ),
                "expected_deliverables": ["Team outputs"],
                "interaction_needs": ["Internal collaboration"],
                "time_sensitivity": "ongoing",
                "innovation_execution_balance": 0.5,
                "suggested_team_name": self._suggest_team_name(request),
            }

    def _determine_team_pattern(self, understanding: Dict) -> str:
        """
        Determine which team pattern best fits the requirements
        """
        purpose_lower = understanding.get("primary_purpose", "").lower()

        # Match against patterns
        if any(
            word in purpose_lower
            for word in ["innovate", "create", "design", "develop"]
        ):
            return "innovation"
        elif any(
            word in purpose_lower
            for word in ["analyze", "research", "investigate", "data"]
        ):
            return "analysis"
        elif any(
            word in purpose_lower
            for word in ["customer", "client", "support", "service"]
        ):
            return "customer_facing"
        else:
            return "execution"

    def _generate_team_proposal(
        self, understanding: Dict, pattern: str, context: Optional[Dict]
    ) -> TeamCompositionProposal:
        """
        Generate detailed team composition proposal using LLM
        """
        self.console.print("\n[bold]Generating optimal team composition...[/bold]")

        proposal_prompt = f"""
        Design an optimal team composition for:

        Purpose: {understanding.get('primary_purpose')}
        Pattern: {pattern} team
        Objectives: {json.dumps(understanding.get('key_objectives', []))}
        Required Capabilities: {json.dumps(understanding.get('required_capabilities', []))}

        Team Design Principles:
        1. Follow the two-pizza rule (3-7 members, 5 is optimal)
        2. Include diverse perspectives and complementary skills
        3. Consider including a constructive skeptic/challenger
        4. Ensure clear roles without overlap
        5. Balance autonomy with collaboration needs

        For each team member, provide:
        - Role title (specific and descriptive)
        - Primary purpose on the team
        - 3-4 key responsibilities
        - Required skills
        - Personality traits that would be beneficial
        - How they interact with other team members
        - Why this role is essential (rationale)

        Also provide:
        - Overall team dynamics description
        - Success factors for this team
        - Potential challenges to watch for

        Format as JSON with a 'team_composition' object.
        Aim for {self.team_patterns[pattern]['optimal_size']} members.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in team design and organizational psychology. You understand how to create balanced, effective teams.",
                    },
                    {"role": "user", "content": proposal_prompt},
                ],
                temperature=0.8,
            )

            result = json.loads(response.choices[0].message.content)

            # Convert to proposal object
            team_comp = result.get("team_composition", {})

            members = []
            for member_data in team_comp.get("members", []):
                members.append(
                    ProposedMember(
                        role=member_data["role"],
                        purpose=member_data["purpose"],
                        key_responsibilities=member_data["responsibilities"],
                        required_skills=member_data["skills"],
                        personality_traits=member_data["traits"],
                        interaction_style=member_data.get(
                            "interaction_style", "collaborative"
                        ),
                        rationale=member_data.get("rationale", ""),
                    )
                )

            return TeamCompositionProposal(
                team_name=understanding.get("suggested_team_name", "new-team"),
                team_purpose=understanding["primary_purpose"],
                proposed_size=len(members),
                members=members,
                team_dynamics=team_comp.get("dynamics", ""),
                success_factors=team_comp.get("success_factors", []),
                potential_challenges=team_comp.get("challenges", []),
                rationale=team_comp.get("overall_rationale", ""),
            )

        except Exception as e:
            self.console.print(f"[yellow]Using template-based proposal: {e}[/yellow]")
            return self._generate_template_proposal(understanding, pattern)

    def _optimize_team_balance(
        self, proposal: TeamCompositionProposal
    ) -> TeamCompositionProposal:
        """
        Optimize team for balance and effectiveness
        """
        # Check for critical roles
        roles = [m.role.lower() for m in proposal.members]

        # Ensure leadership
        has_leader = any("lead" in r or "manager" in r for r in roles)
        if not has_leader and proposal.proposed_size >= 4:
            self.console.print(
                "[yellow]Note: Consider adding a team lead for coordination[/yellow]"
            )

        # Ensure skeptic/challenger
        has_skeptic = any(
            "skeptic" in r or "critic" in r or "challenger" in r for r in roles
        )
        if not has_skeptic and proposal.proposed_size >= 5:
            # Add a skeptic role
            self._add_skeptic_to_proposal(proposal)

        # Check skill coverage
        all_skills = set()
        for member in proposal.members:
            all_skills.update(member.required_skills)

        # Ensure key skills are covered
        required_skills = {"communication", "analysis", "execution", "planning"}
        missing_skills = required_skills - all_skills

        if missing_skills:
            self.console.print(
                f"[yellow]Note: Consider adding members with skills: {missing_skills}[/yellow]"
            )

        return proposal

    def _add_skeptic_to_proposal(self, proposal: TeamCompositionProposal):
        """
        Add a constructive skeptic to the team
        """
        skeptic = ProposedMember(
            role=f"{proposal.team_name} Quality Advocate",
            purpose="Ensure robust solutions through constructive challenge",
            key_responsibilities=[
                "Challenge assumptions constructively",
                "Identify potential risks and edge cases",
                "Validate proposals against success criteria",
                "Ensure thorough preparation",
            ],
            required_skills=[
                "critical thinking",
                "risk assessment",
                "domain knowledge",
                "communication",
            ],
            personality_traits=[
                "analytical",
                "constructive",
                "thorough",
                "collaborative",
            ],
            interaction_style="Constructive challenger who helps the team excel",
            rationale="Every team benefits from constructive challenge to ensure quality",
        )

        proposal.members.append(skeptic)
        proposal.proposed_size += 1

    def display_proposal(self, proposal: TeamCompositionProposal):
        """
        Display the team composition proposal beautifully
        """
        # Team Overview
        overview = Panel(
            f"[bold]Team Name:[/bold] {proposal.team_name}\n"
            f"[bold]Purpose:[/bold] {proposal.team_purpose}\n"
            f"[bold]Proposed Size:[/bold] {proposal.proposed_size} members\n"
            f"[bold]Team Dynamics:[/bold] {proposal.team_dynamics}",
            title="Team Composition Proposal",
            border_style="cyan",
        )
        self.console.print(overview)

        # Member Details
        self.console.print("\n[bold]Proposed Team Members:[/bold]\n")

        for i, member in enumerate(proposal.members, 1):
            member_panel = Panel(
                f"[bold cyan]Role:[/bold cyan] {member.role}\n"
                f"[bold]Purpose:[/bold] {member.purpose}\n\n"
                f"[bold]Key Responsibilities:[/bold]\n"
                + "\n".join(f"  • {r}" for r in member.key_responsibilities)
                + "\n\n"
                f"[bold]Required Skills:[/bold] {', '.join(member.required_skills)}\n"
                f"[bold]Personality Traits:[/bold] {', '.join(member.personality_traits)}\n"
                f"[bold]Interaction Style:[/bold] {member.interaction_style}\n\n"
                f"[dim]Rationale: {member.rationale}[/dim]",
                title=f"Member {i}",
                border_style="green",
            )
            self.console.print(member_panel)

        # Success Factors
        if proposal.success_factors:
            self.console.print("\n[bold green]Success Factors:[/bold green]")
            for factor in proposal.success_factors:
                self.console.print(f"  ✓ {factor}")

        # Potential Challenges
        if proposal.potential_challenges:
            self.console.print("\n[bold yellow]Potential Challenges:[/bold yellow]")
            for challenge in proposal.potential_challenges:
                self.console.print(f"  ⚠️  {challenge}")

    def refine_proposal_interactively(
        self, proposal: TeamCompositionProposal
    ) -> TeamCompositionProposal:
        """
        Allow interactive refinement of the proposal
        """
        while True:
            self.console.print("\n[bold]Refinement Options:[/bold]")
            self.console.print("1. Add a team member")
            self.console.print("2. Remove a team member")
            self.console.print("3. Modify a role")
            self.console.print("4. Adjust team size")
            self.console.print("5. Accept proposal")

            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"])

            if choice == "5":
                break
            elif choice == "1":
                self._add_member_interactive(proposal)
            elif choice == "2":
                self._remove_member_interactive(proposal)
            elif choice == "3":
                self._modify_role_interactive(proposal)
            elif choice == "4":
                self._adjust_size_interactive(proposal)

            # Redisplay
            self.display_proposal(proposal)

        return proposal

    def _generate_template_proposal(
        self, understanding: Dict, pattern: str
    ) -> TeamCompositionProposal:
        """
        Fallback template-based proposal generation
        """
        team_name = understanding.get("suggested_team_name", "new-team")

        # Base roles for pattern
        if pattern == "innovation":
            members = [
                ProposedMember(
                    role=f"{team_name} Innovation Lead",
                    purpose="Drive creative vision and strategy",
                    key_responsibilities=[
                        "Set innovation direction",
                        "Guide ideation",
                        "Ensure feasibility",
                    ],
                    required_skills=["strategic thinking", "creativity", "leadership"],
                    personality_traits=["visionary", "inspiring", "open-minded"],
                    interaction_style="Collaborative leader",
                    rationale="Every innovation team needs clear vision",
                ),
                ProposedMember(
                    role=f"{team_name} Research Specialist",
                    purpose="Investigate possibilities and validate concepts",
                    key_responsibilities=[
                        "Market research",
                        "Technology assessment",
                        "Feasibility studies",
                    ],
                    required_skills=["research", "analysis", "synthesis"],
                    personality_traits=["curious", "methodical", "objective"],
                    interaction_style="Knowledge provider",
                    rationale="Innovation requires solid research foundation",
                ),
                ProposedMember(
                    role=f"{team_name} Prototype Developer",
                    purpose="Transform ideas into tangible solutions",
                    key_responsibilities=[
                        "Build prototypes",
                        "Test concepts",
                        "Iterate quickly",
                    ],
                    required_skills=[
                        "technical skills",
                        "rapid prototyping",
                        "problem-solving",
                    ],
                    personality_traits=["hands-on", "adaptable", "pragmatic"],
                    interaction_style="Builder and maker",
                    rationale="Ideas need tangible form to evaluate",
                ),
                ProposedMember(
                    role=f"{team_name} Innovation Skeptic",
                    purpose="Ensure ideas are robust and practical",
                    key_responsibilities=[
                        "Challenge assumptions",
                        "Identify risks",
                        "Validate viability",
                    ],
                    required_skills=[
                        "critical thinking",
                        "risk assessment",
                        "business acumen",
                    ],
                    personality_traits=["analytical", "constructive", "thorough"],
                    interaction_style="Constructive challenger",
                    rationale="Innovation benefits from constructive challenge",
                ),
                ProposedMember(
                    role=f"{team_name} User Advocate",
                    purpose="Ensure innovations meet real user needs",
                    key_responsibilities=[
                        "User research",
                        "Feedback gathering",
                        "Experience design",
                    ],
                    required_skills=["empathy", "user research", "communication"],
                    personality_traits=["empathetic", "observant", "user-focused"],
                    interaction_style="Voice of the customer",
                    rationale="Innovation must solve real problems",
                ),
            ]
        else:
            # Default execution team
            members = [
                ProposedMember(
                    role=f"{team_name} Team Lead",
                    purpose="Coordinate team efforts and ensure delivery",
                    key_responsibilities=[
                        "Plan work",
                        "Coordinate team",
                        "Track progress",
                        "Remove blockers",
                    ],
                    required_skills=["leadership", "planning", "communication"],
                    personality_traits=["organized", "decisive", "supportive"],
                    interaction_style="Servant leader",
                    rationale="Teams need coordination",
                ),
                ProposedMember(
                    role=f"{team_name} Domain Expert",
                    purpose="Provide deep expertise in the problem domain",
                    key_responsibilities=[
                        "Advise on solutions",
                        "Validate approaches",
                        "Share knowledge",
                    ],
                    required_skills=["domain expertise", "teaching", "problem-solving"],
                    personality_traits=["knowledgeable", "patient", "thorough"],
                    interaction_style="Expert advisor",
                    rationale="Domain expertise ensures quality",
                ),
                ProposedMember(
                    role=f"{team_name} Implementation Specialist",
                    purpose="Execute solutions with high quality",
                    key_responsibilities=[
                        "Build solutions",
                        "Ensure quality",
                        "Document work",
                    ],
                    required_skills=[
                        "technical skills",
                        "attention to detail",
                        "execution",
                    ],
                    personality_traits=["meticulous", "reliable", "skilled"],
                    interaction_style="Reliable executor",
                    rationale="Ideas need excellent execution",
                ),
            ]

        return TeamCompositionProposal(
            team_name=team_name,
            team_purpose=understanding["primary_purpose"],
            proposed_size=len(members),
            members=members,
            team_dynamics=f"Balanced {pattern} team with complementary skills",
            success_factors=["Clear roles", "Good communication", "Shared goals"],
            potential_challenges=["Coordination overhead", "Skill gaps"],
            rationale="Team composed based on proven patterns",
        )


def demonstrate_intelligent_composition():
    """Demonstrate the intelligent team composition system"""

    composer = IntelligentTeamComposer()

    # Example requests
    example_requests = [
        "We need a team to revolutionize our customer onboarding experience using AI and automation",
        "Create a data analytics team to provide real-time business intelligence across all departments",
        "Build a rapid response team for handling critical production issues",
        "Form an innovation lab to explore new product opportunities in the metaverse",
    ]

    console.print("[bold cyan]🎯 Intelligent Team Composition Examples[/bold cyan]\n")

    # Show one detailed example
    request = example_requests[0]

    console.print(f"[bold]Request:[/bold] {request}\n")

    # Organizational context
    context = {
        "existing_teams": ["sales-team", "engineering-team", "support-team"],
        "business_stage": "Scale-up",
        "industry": "B2B SaaS",
    }

    # Generate proposal
    proposal = composer.propose_team_composition(request, context)

    # Display it
    composer.display_proposal(proposal)

    # Show composition reasoning
    console.print("\n[bold magenta]Composition Reasoning:[/bold magenta]")
    console.print(
        f"The AI analyzed your request and identified this as an '{proposal.team_dynamics}' team."
    )
    console.print(
        f"It proposed {proposal.proposed_size} members to balance effectiveness with coordination overhead."
    )
    console.print(
        "Each role was selected to provide essential capabilities while maintaining team cohesion."
    )

    # Show other example patterns
    console.print("\n[bold]Other Team Patterns Available:[/bold]")
    patterns_table = Table(show_header=True, header_style="bold magenta")
    patterns_table.add_column("Request Type", style="cyan")
    patterns_table.add_column("Likely Composition", style="green")

    patterns_table.add_row(
        "Data Analytics Team",
        "Lead Analyst, Data Engineer, Visualization Expert, Domain Specialist, Quality Validator",
    )
    patterns_table.add_row(
        "Innovation Lab",
        "Innovation Lead, Researcher, Prototyper, Innovation Skeptic, User Advocate",
    )
    patterns_table.add_row(
        "Crisis Response Team",
        "Incident Commander, Technical Lead, Communications Manager, Solutions Architect, Recovery Specialist",
    )

    console.print(patterns_table)

    console.print(
        "\n[bold green]✨ The AI considers purpose, context, and proven patterns to propose optimal teams![/bold green]"
    )


if __name__ == "__main__":
    demonstrate_intelligent_composition()
