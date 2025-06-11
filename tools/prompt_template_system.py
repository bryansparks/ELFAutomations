#!/usr/bin/env python3
"""
Prompt Template System for ElfAutomations
Provides rich, contextual prompt generation during team creation
and post-generation modification capabilities
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class PromptTemplateSystem:
    """
    Manages prompt templates and generation for team agents
    """

    def __init__(self, template_dir: str = "templates/prompts"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.company_context = self._load_company_context()
        self.role_templates = self._load_role_templates()

    def _load_company_context(self) -> Dict:
        """Load or create company-wide context"""
        context_file = self.template_dir / "company_context.yaml"

        if context_file.exists():
            with open(context_file, "r") as f:
                return yaml.safe_load(f)
        else:
            # Default company context
            default_context = {
                "company": {
                    "name": "ElfAutomations",
                    "mission": "Revolutionize business operations through intelligent agent teams",
                    "vision": "Every company powered by collaborative AI teams",
                    "stage": "Series A startup, 50 customers, growing 20% monthly",
                    "values": [
                        "Transparency",
                        "Innovation",
                        "Collaboration",
                        "Results",
                    ],
                    "priorities": [
                        "Scale customer acquisition",
                        "Maintain system reliability",
                        "Expand team capabilities",
                    ],
                },
                "principles": {
                    "communication": [
                        "Time-box discussions to 15 minutes maximum",
                        "Always state assumptions explicitly",
                        "Use 'yes, and' instead of 'no, but'",
                        "Document decisions for future reference",
                    ],
                    "decision_making": [
                        "Data beats opinions, but intuition matters",
                        "Perfect is the enemy of good enough",
                        "Fail fast, learn faster",
                        "Measure twice, cut once",
                    ],
                    "collaboration": [
                        "Skeptics improve outcomes when constructive",
                        "Managers guide, not micromanage",
                        "Share knowledge generously",
                        "Celebrate small wins",
                    ],
                },
            }

            with open(context_file, "w") as f:
                yaml.dump(default_context, f, default_flow_style=False)

            return default_context

    def _load_role_templates(self) -> Dict:
        """Load role-specific templates"""
        templates_file = self.template_dir / "role_templates.yaml"

        if templates_file.exists():
            with open(templates_file, "r") as f:
                return yaml.safe_load(f)
        else:
            # Default role templates
            default_templates = {
                "manager": {
                    "role_description": "As the {team_name} Manager, you orchestrate team activities, make final decisions after considering all input, and ensure alignment with company objectives. You delegate effectively while maintaining accountability.",
                    "approach": "Be decisive but inclusive. Listen actively, synthesize diverse viewpoints, and make timely decisions. Ask 'What are we missing?' before finalizing plans.",
                    "success_criteria": [
                        "Team achieves objectives without burnout",
                        "Decisions made efficiently with team buy-in",
                        "Clear communication up and down the organization",
                        "Team members grow and develop skills",
                    ],
                    "communication_style": "Be clear and decisive. Summarize discussions, state decisions explicitly, and explain reasoning. Use 'I've decided...' after considering input.",
                },
                "skeptic": {
                    "role_description": "As the {team_name} Skeptic, you strengthen proposals through constructive challenge. You identify risks, question assumptions, and ensure thorough preparation. Your goal is team success through rigorous thinking.",
                    "approach": "Challenge constructively by asking 'What could go wrong?' and 'Is there a simpler way?' Always couple criticism with alternatives. Acknowledge when convinced.",
                    "success_criteria": [
                        "Prevent costly mistakes through foresight",
                        "Improve proposal quality without slowing progress",
                        "Build team confidence through rigorous preparation",
                        "Document lessons learned from challenges raised",
                    ],
                    "communication_style": "Frame challenges positively. Use 'What if...' and 'Have we considered...' rather than 'This won't work.' Always acknowledge valid points.",
                },
                "analyst": {
                    "role_description": "As the {team_name} Analyst, you provide data-driven insights to guide decisions. You balance thoroughness with timeliness, ensuring the team has the information needed without analysis paralysis.",
                    "approach": "Be precise but practical. Present data clearly, highlight key insights, and recommend actions. Say 'The data suggests...' rather than making absolute statements.",
                    "success_criteria": [
                        "Deliver actionable insights on time",
                        "Balance detail with clarity",
                        "Proactively identify trends and patterns",
                        "Make data accessible to non-technical teammates",
                    ],
                    "communication_style": "Lead with insights, not just data. Use 'This means...' after presenting numbers. Anticipate questions and prepare visualizations when helpful.",
                },
                "specialist": {
                    "role_description": "As a {team_name} Specialist in {specialty}, you bring deep expertise to execute team objectives. You collaborate with teammates, share knowledge generously, and deliver high-quality work on time.",
                    "approach": "Be collaborative and proactive. Share your expertise generously, ask clarifying questions, and focus on delivering value to the team's objectives.",
                    "success_criteria": [
                        "Deliver high-quality work on schedule",
                        "Collaborate effectively with team members",
                        "Continuously improve based on feedback",
                        "Share knowledge to elevate team capabilities",
                    ],
                    "communication_style": "Be proactive in sharing updates. Use 'I'm working on...' and 'I need help with...' to maintain transparency. Celebrate team wins.",
                },
            }

            with open(templates_file, "w") as f:
                yaml.dump(default_templates, f, default_flow_style=False)

            return default_templates

    def generate_team_context(
        self, team_name: str, team_description: str, parent_team: Optional[str] = None
    ) -> Dict:
        """
        Generate team-specific context through guided process
        """
        print(f"\n{'='*60}")
        print(f"GENERATING CONTEXT FOR: {team_name}")
        print(f"{'='*60}\n")

        # Team purpose refinement
        print(f"Initial team description: {team_description}\n")

        team_context = {
            "name": team_name,
            "description": team_description,
            "purpose": input("Refine the team's PURPOSE (why does this team exist?): ")
            or team_description,
            "goals": [],
            "constraints": [],
            "success_metrics": [],
            "key_relationships": [],
        }

        # Gather goals
        print("\nWhat are the team's TOP 3 GOALS? (press enter to skip)")
        for i in range(3):
            goal = input(f"Goal {i+1}: ").strip()
            if goal:
                team_context["goals"].append(goal)

        # Gather constraints
        print(
            "\nWhat CONSTRAINTS does the team operate under? (e.g., budget, timeline, resources)"
        )
        print("Press enter to skip")
        for i in range(3):
            constraint = input(f"Constraint {i+1}: ").strip()
            if constraint:
                team_context["constraints"].append(constraint)

        # Success metrics
        print("\nHow will you MEASURE this team's success?")
        print("Press enter to skip")
        for i in range(3):
            metric = input(f"Metric {i+1}: ").strip()
            if metric:
                team_context["success_metrics"].append(metric)

        # Key relationships
        if parent_team:
            team_context["key_relationships"].append(f"Reports to {parent_team}")

        print("\nWhat other teams does this team COLLABORATE with frequently?")
        print("Press enter when done")
        while True:
            relationship = input("Collaborates with: ").strip()
            if not relationship:
                break
            team_context["key_relationships"].append(relationship)

        # Save team context
        team_context_file = self.template_dir / f"{team_name}_context.yaml"
        with open(team_context_file, "w") as f:
            yaml.dump(team_context, f, default_flow_style=False)

        return team_context

    def generate_agent_prompt(
        self,
        agent_name: str,
        agent_role: str,
        team_context: Dict,
        team_members: List[Dict],
        custom_details: Optional[Dict] = None,
    ) -> str:
        """
        Generate a rich, contextual prompt for an agent
        """
        # Determine role type
        role_type = self._determine_role_type(agent_role)
        template = self.role_templates.get(role_type, self.role_templates["specialist"])

        # Build the prompt
        sections = []

        # Opening
        sections.append(
            f"You are {agent_name}, the {agent_role} for the {team_context['name']} at {self.company_context['company']['name']}."
        )
        sections.append("")

        # Company Context
        sections.append("**ORGANIZATION CONTEXT:**")
        sections.append(f"- Mission: {self.company_context['company']['mission']}")
        sections.append(f"- Stage: {self.company_context['company']['stage']}")
        sections.append(
            f"- Current Priorities: {', '.join(self.company_context['company']['priorities'])}"
        )
        sections.append("")

        # Team Context
        sections.append("**YOUR TEAM'S PURPOSE:**")
        sections.append(team_context["purpose"])
        sections.append("")

        if team_context.get("goals"):
            sections.append("**TEAM GOALS:**")
            for goal in team_context["goals"]:
                sections.append(f"- {goal}")
            sections.append("")

        # Role Description
        sections.append("**YOUR ROLE:**")
        role_desc = template["role_description"].format(
            team_name=team_context["name"],
            specialty=custom_details.get("specialty", "your domain")
            if custom_details
            else "your domain",
        )
        sections.append(role_desc)
        sections.append("")

        # Approach
        sections.append("**YOUR APPROACH:**")
        sections.append(template["approach"])
        sections.append("")

        # Team Dynamics
        sections.append("**TEAM DYNAMICS:**")
        for member in team_members:
            if member["name"] != agent_name:
                interaction = self._get_interaction_style(member["role"])
                sections.append(f"- {member['name']} ({member['role']}): {interaction}")
        sections.append("")

        # Key Principles
        sections.append("**KEY PRINCIPLES:**")
        # Mix company principles based on role
        principles = []
        principles.extend(self.company_context["principles"]["communication"][:2])
        if "manager" in role_type:
            principles.extend(self.company_context["principles"]["decision_making"][:2])
        principles.extend(self.company_context["principles"]["collaboration"][:1])

        for principle in principles:
            sections.append(f"- {principle}")
        sections.append("")

        # Success Criteria
        sections.append("**SUCCESS CRITERIA:**")
        for criteria in template["success_criteria"]:
            sections.append(f"- {criteria}")
        sections.append("")

        # Communication Style
        sections.append("**COMMUNICATION STYLE:**")
        sections.append(template["communication_style"])

        # Custom details
        if custom_details:
            if custom_details.get("tools"):
                sections.append("")
                sections.append("**YOUR TOOLS:**")
                for tool in custom_details["tools"]:
                    sections.append(f"- {tool}")

            if custom_details.get("specific_knowledge"):
                sections.append("")
                sections.append("**SPECIFIC KNOWLEDGE:**")
                sections.append(custom_details["specific_knowledge"])

        # Constraints
        if team_context.get("constraints"):
            sections.append("")
            sections.append("**OPERATING CONSTRAINTS:**")
            for constraint in team_context["constraints"]:
                sections.append(f"- {constraint}")

        return "\n".join(sections)

    def _determine_role_type(self, role: str) -> str:
        """Determine the role type from role name"""
        role_lower = role.lower()

        if any(term in role_lower for term in ["manager", "lead", "director", "head"]):
            return "manager"
        elif any(term in role_lower for term in ["skeptic", "critic", "challenger"]):
            return "skeptic"
        elif any(term in role_lower for term in ["analyst", "data", "research"]):
            return "analyst"
        else:
            return "specialist"

    def _get_interaction_style(self, role: str) -> str:
        """Get interaction style description"""
        styles = {
            "manager": "Strategic thinker, appreciates concise updates with clear recommendations",
            "skeptic": "Constructive challenger, values thorough analysis and alternative perspectives",
            "analyst": "Data-driven, prefers evidence-based discussions with clear metrics",
            "engineer": "Technical expert, enjoys detailed problem-solving discussions",
            "creative": "Innovative thinker, responds well to brainstorming and 'yes, and' approach",
            "specialist": "Domain expert, values precision and practical application",
        }

        role_type = self._determine_role_type(role)
        for key, style in styles.items():
            if key in role.lower() or key == role_type:
                return style

        return "Collaborative teammate, values clear communication and shared goals"

    def modify_agent_prompt(self, team_name: str, agent_name: str) -> str:
        """
        Modify an existing agent's prompt interactively
        """
        agent_file = Path(f"teams/{team_name}/agents/{agent_name}.py")

        if not agent_file.exists():
            print(f"Agent file not found: {agent_file}")
            return None

        # Read current prompt
        with open(agent_file, "r") as f:
            content = f.read()

        # Extract current backstory/prompt
        import re

        backstory_match = re.search(r'backstory="""(.*?)"""', content, re.DOTALL)

        if not backstory_match:
            print("Could not find backstory in agent file")
            return None

        current_prompt = backstory_match.group(1)

        print(f"\n{'='*60}")
        print(f"MODIFYING PROMPT FOR: {agent_name}")
        print(f"{'='*60}\n")
        print("CURRENT PROMPT:")
        print("-" * 40)
        print(current_prompt)
        print("-" * 40)

        # Interactive modification options
        print("\nMODIFICATION OPTIONS:")
        print("1. Add specific knowledge/context")
        print("2. Modify communication style")
        print("3. Add/remove responsibilities")
        print("4. Update success criteria")
        print("5. Complete rewrite")
        print("6. Cancel")

        choice = input("\nSelect option (1-6): ")

        if choice == "1":
            additional = input("\nAdd specific knowledge/context:\n")
            new_prompt = current_prompt + f"\n\n**ADDITIONAL CONTEXT:**\n{additional}"

        elif choice == "2":
            new_style = input("\nNew communication style guidance:\n")
            # Replace communication style section
            new_prompt = re.sub(
                r"\*\*COMMUNICATION STYLE:\*\*\n.*?(?=\n\n|\Z)",
                f"**COMMUNICATION STYLE:**\n{new_style}",
                current_prompt,
                flags=re.DOTALL,
            )

        elif choice == "3":
            print("\nCurrent prompt will be displayed in your editor...")
            # Here you could integrate with the user's editor
            new_prompt = input("\nPaste the modified prompt:\n")

        elif choice == "4":
            new_criteria = []
            print("\nEnter new success criteria (empty line to finish):")
            while True:
                criterion = input("- ")
                if not criterion:
                    break
                new_criteria.append(f"- {criterion}")

            # Replace success criteria section
            new_prompt = re.sub(
                r"\*\*SUCCESS CRITERIA:\*\*\n.*?(?=\n\n|\Z)",
                f"**SUCCESS CRITERIA:**\n" + "\n".join(new_criteria),
                current_prompt,
                flags=re.DOTALL,
            )

        elif choice == "5":
            print("\nEnter new prompt (type END on a new line when done):")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            new_prompt = "\n".join(lines)

        else:
            print("Modification cancelled")
            return None

        # Update the agent file
        new_content = content.replace(
            f'backstory="""{current_prompt}"""', f'backstory="""{new_prompt}"""'
        )

        # Backup original
        backup_file = agent_file.with_suffix(".py.bak")
        with open(backup_file, "w") as f:
            f.write(content)

        # Write new content
        with open(agent_file, "w") as f:
            f.write(new_content)

        print(f"\n✅ Prompt updated successfully!")
        print(f"Backup saved to: {backup_file}")

        # Log the change
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "team": team_name,
            "agent": agent_name,
            "modification_type": [
                "add_context",
                "modify_style",
                "edit",
                "update_criteria",
                "rewrite",
            ][int(choice) - 1],
            "previous_prompt_backup": str(backup_file),
        }

        log_file = Path("logs/prompt_modifications.json")
        log_file.parent.mkdir(exist_ok=True)

        logs = []
        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)

        logs.append(log_entry)

        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)

        return new_prompt


# Integration function for team factory
def integrate_with_team_factory(team_factory_module):
    """
    Function to integrate prompt template system with existing team factory
    """
    template_system = PromptTemplateSystem()

    # Monkey patch or extend the team factory
    original_create_team_member = team_factory_module.TeamMember

    def enhanced_team_member_creation(
        self, team_name, team_description, members, **kwargs
    ):
        # Generate team context first
        team_context = template_system.generate_team_context(
            team_name, team_description, kwargs.get("parent_team")
        )

        # Generate prompts for each member
        enhanced_members = []
        for member in members:
            custom_details = {
                "tools": member.get("tools", []),
                "specific_knowledge": member.get("specific_knowledge", ""),
            }

            prompt = template_system.generate_agent_prompt(
                agent_name=member["name"],
                agent_role=member["role"],
                team_context=team_context,
                team_members=members,
                custom_details=custom_details,
            )

            member["system_prompt"] = prompt
            enhanced_members.append(member)

        return enhanced_members

    return enhanced_team_member_creation


if __name__ == "__main__":
    # Example usage
    pts = PromptTemplateSystem()

    # Example: Generate context for a new team
    team_context = pts.generate_team_context(
        "content-generation", "Creates engaging content for marketing campaigns"
    )

    # Example: Generate prompt for an agent
    team_members = [
        {"name": "content_manager", "role": "Content Manager"},
        {"name": "writer_alice", "role": "Senior Content Writer"},
        {"name": "editor_bob", "role": "Content Editor"},
        {"name": "seo_expert", "role": "SEO Specialist"},
        {"name": "quality_skeptic", "role": "Content Quality Skeptic"},
    ]

    for member in team_members:
        prompt = pts.generate_agent_prompt(
            member["name"],
            member["role"],
            team_context,
            team_members,
            custom_details={
                "tools": ["content_calendar", "seo_analyzer", "grammarly"],
                "specific_knowledge": "Expert in B2B SaaS content marketing",
            },
        )

        print(f"\n{'='*60}")
        print(f"PROMPT FOR {member['name']}")
        print("=" * 60)
        print(prompt)
        print("\n")

        # Only show first one for brevity
        break
