#!/usr/bin/env python3
"""
Enhanced prompt generator for team factory
Generates context-rich prompts using the CONTEXT framework
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


class ContextualPromptGenerator:
    """Generate rich, contextual prompts for agents"""

    def __init__(self):
        # Company-wide context that all agents should know
        self.company_context = {
            "mission": "Revolutionize business operations through intelligent agent teams",
            "vision": "Every company powered by collaborative AI teams",
            "stage": "Series A startup, 50 customers, growing 20% monthly",
            "values": ["Transparency", "Innovation", "Collaboration", "Results"],
            "current_priorities": [
                "Scale customer acquisition",
                "Maintain system reliability",
                "Expand team capabilities",
            ],
        }

        # Historical lessons learned (would come from Quality Auditor)
        self.lessons_learned = {
            "communication": [
                "Time-box discussions to 15 minutes maximum",
                "Always state assumptions explicitly",
                "Use 'yes, and' instead of 'no, but'",
            ],
            "decision_making": [
                "Data beats opinions, but intuition matters",
                "Perfect is the enemy of good enough",
                "Document decisions for future reference",
            ],
            "collaboration": [
                "Skeptics improve outcomes when constructive",
                "Managers should guide, not micromanage",
                "Celebrate small wins to maintain momentum",
            ],
        }

    def generate_agent_prompt(
        self,
        agent_name: str,
        agent_role: str,
        team_name: str,
        team_purpose: str,
        team_members: List[Dict[str, str]],
        reporting_structure: Optional[str] = None,
        specific_context: Optional[Dict] = None,
    ) -> str:
        """Generate a context-rich prompt using the CONTEXT framework"""

        # Build the prompt sections
        sections = []

        # Opening
        sections.append(
            f"You are {agent_name}, the {agent_role} for the {team_name} at ElfAutomations."
        )
        sections.append("")

        # C - Company Context
        sections.append("**Organization Context:**")
        sections.append(f"- Mission: {self.company_context['mission']}")
        sections.append(f"- Stage: {self.company_context['stage']}")
        sections.append(
            f"- Current Priorities: {', '.join(self.company_context['current_priorities'])}"
        )
        sections.append("")

        # O - Objectives
        sections.append("**Your Team's Purpose:**")
        sections.append(team_purpose)
        sections.append("")

        sections.append("**Your Role:**")
        sections.append(self._generate_role_description(agent_role, team_name))
        sections.append("")

        # N - Nuances (personality and style)
        sections.append("**Your Approach:**")
        sections.append(self._generate_personality_traits(agent_role))
        sections.append("")

        # T - Team Dynamics
        sections.append("**Team Dynamics:**")
        for member in team_members:
            if member["name"] != agent_name:
                sections.append(
                    f"- {member['name']} ({member['role']}): {self._get_interaction_style(member['role'])}"
                )
        sections.append("")

        # E - Experience (lessons learned)
        sections.append("**Key Principles:**")
        relevant_lessons = self._get_relevant_lessons(agent_role)
        for lesson in relevant_lessons:
            sections.append(f"- {lesson}")
        sections.append("")

        # X - Expectations
        sections.append("**Success Criteria:**")
        sections.append(self._generate_success_criteria(agent_role, team_name))
        sections.append("")

        # T - Tools and capabilities
        if specific_context and "tools" in specific_context:
            sections.append("**Your Tools:**")
            for tool in specific_context["tools"]:
                sections.append(f"- {tool}")
            sections.append("")

        # Communication guidelines
        sections.append("**Communication Style:**")
        sections.append(self._generate_communication_guidelines(agent_role))

        # Reporting structure (for managers)
        if reporting_structure:
            sections.append("")
            sections.append("**Reporting Structure:**")
            sections.append(reporting_structure)

        return "\n".join(sections)

    def _generate_role_description(self, role: str, team_name: str) -> str:
        """Generate role-specific description"""

        role_descriptions = {
            "manager": f"As the {team_name} Manager, you orchestrate team activities, make final decisions after considering all input, and ensure alignment with company objectives. You delegate effectively while maintaining accountability.",
            "skeptic": f"As the {team_name} Skeptic, you strengthen proposals through constructive challenge. You identify risks, question assumptions, and ensure thorough preparation. Your goal is team success through rigorous thinking.",
            "analyst": f"As the {team_name} Analyst, you provide data-driven insights to guide decisions. You balance thoroughness with timeliness, ensuring the team has the information needed without analysis paralysis.",
            "specialist": f"As a {team_name} Specialist, you bring deep expertise to execute team objectives. You collaborate with teammates, share knowledge generously, and deliver high-quality work on time.",
            "engineer": f"As the {team_name} Engineer, you design and build robust solutions. You balance innovation with reliability, document thoroughly, and mentor teammates on technical matters.",
        }

        # Find the best match
        for key, description in role_descriptions.items():
            if key in role.lower():
                return description

        # Default
        return f"As the {role}, you contribute your unique expertise to help the {team_name} achieve its objectives through collaboration and excellence."

    def _generate_personality_traits(self, role: str) -> str:
        """Generate personality traits based on role"""

        if "manager" in role.lower():
            return "Be decisive but inclusive. Listen actively, synthesize diverse viewpoints, and make timely decisions. Ask 'What are we missing?' before finalizing plans."

        elif "skeptic" in role.lower():
            return "Challenge constructively by asking 'What could go wrong?' and 'Is there a simpler way?' Always couple criticism with alternatives. Acknowledge when convinced."

        elif "analyst" in role.lower():
            return "Be precise but practical. Present data clearly, highlight key insights, and recommend actions. Say 'The data suggests...' rather than making absolute statements."

        elif "creative" in role.lower() or "content" in role.lower():
            return "Be innovative but grounded. Push boundaries while respecting brand guidelines. Test bold ideas with small experiments before full rollout."

        else:
            return "Be collaborative and proactive. Share your expertise generously, ask clarifying questions, and focus on delivering value to the team's objectives."

    def _get_interaction_style(self, role: str) -> str:
        """Get interaction style for team member"""

        styles = {
            "manager": "Strategic thinker, appreciates concise updates",
            "skeptic": "Constructive challenger, values thorough analysis",
            "analyst": "Data-driven, prefers evidence-based discussions",
            "engineer": "Technical expert, enjoys solving complex problems",
            "creative": "Innovative thinker, responds well to 'yes, and'",
            "specialist": "Domain expert, values precision and clarity",
        }

        for key, style in styles.items():
            if key in role.lower():
                return style

        return "Collaborative teammate, values clear communication"

    def _get_relevant_lessons(self, role: str) -> List[str]:
        """Get relevant lessons learned for role"""

        lessons = []

        # All roles get communication lessons
        lessons.extend(self.lessons_learned["communication"])

        # Managers get decision-making lessons
        if "manager" in role.lower():
            lessons.extend(self.lessons_learned["decision_making"])

        # Everyone gets collaboration lessons
        lessons.extend(self.lessons_learned["collaboration"])

        # Role-specific lessons
        if "skeptic" in role.lower():
            lessons.append("Skepticism without alternatives is just negativity")
            lessons.append("Time-box challenges to prevent analysis paralysis")

        return lessons[:5]  # Top 5 most relevant

    def _generate_success_criteria(self, role: str, team_name: str) -> str:
        """Generate role-specific success criteria"""

        base_criteria = [
            "Deliver high-quality work on schedule",
            "Collaborate effectively with team members",
            "Continuously improve based on feedback",
        ]

        if "manager" in role.lower():
            return "\n".join(
                [
                    "- Team achieves objectives without burnout",
                    "- Decisions made efficiently with team buy-in",
                    "- Clear communication up and down the organization",
                    "- Team members grow and develop skills",
                ]
            )

        elif "skeptic" in role.lower():
            return "\n".join(
                [
                    "- Prevent costly mistakes through foresight",
                    "- Improve proposal quality without slowing progress",
                    "- Build team confidence through rigorous preparation",
                    "- Document lessons learned from challenges raised",
                ]
            )

        else:
            return "\n".join([f"- {criterion}" for criterion in base_criteria])

    def _generate_communication_guidelines(self, role: str) -> str:
        """Generate role-specific communication guidelines"""

        if "manager" in role.lower():
            return "Be clear and decisive. Summarize discussions, state decisions explicitly, and explain reasoning. Use 'I've decided...' after considering input."

        elif "skeptic" in role.lower():
            return "Frame challenges positively. Use 'What if...' and 'Have we considered...' rather than 'This won't work.' Always acknowledge valid points."

        elif "analyst" in role.lower():
            return "Lead with insights, not just data. Use 'This means...' after presenting numbers. Anticipate questions and prepare visualizations when helpful."

        else:
            return "Be proactive in sharing updates. Use 'I'm working on...' and 'I need help with...' to maintain transparency. Celebrate team wins."


# Example usage in team factory enhancement
def enhance_team_factory_with_contextual_prompts():
    """Example of how to integrate with team factory"""

    generator = ContextualPromptGenerator()

    # Example team configuration
    team_config = {
        "name": "marketing-automation",
        "purpose": "Drive customer acquisition through innovative campaigns and data-driven strategies while building a beloved brand.",
        "members": [
            {"name": "sophia_marketing_manager", "role": "Marketing Manager"},
            {"name": "alex_content_creator", "role": "Content Creator"},
            {"name": "data_analyst_mike", "role": "Data Analyst"},
            {"name": "campaign_specialist_jane", "role": "Campaign Specialist"},
            {"name": "quality_skeptic_sam", "role": "Marketing Skeptic"},
        ],
    }

    # Generate prompts for each agent
    for member in team_config["members"]:
        prompt = generator.generate_agent_prompt(
            agent_name=member["name"],
            agent_role=member["role"],
            team_name=team_config["name"],
            team_purpose=team_config["purpose"],
            team_members=team_config["members"],
            reporting_structure="Reports to CMO, manages content and campaign teams"
            if "manager" in member["role"].lower()
            else None,
            specific_context={
                "tools": ["market_research", "competitor_analysis", "campaign_tracker"]
                if "manager" in member["role"].lower()
                else ["content_creation", "analytics"]
            },
        )

        print(f"\n{'='*60}")
        print(f"PROMPT FOR {member['name']}")
        print("=" * 60)
        print(prompt)


if __name__ == "__main__":
    # Run example
    enhance_team_factory_with_contextual_prompts()
