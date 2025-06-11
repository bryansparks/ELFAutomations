#!/usr/bin/env python3
"""
Script to create the Executive Team using the team factory
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.team_factory import TeamFactory, TeamMember, TeamSpecification


def create_executive_team():
    """Create the Executive Team with predefined configuration"""

    factory = TeamFactory()

    # Define the Executive Team
    executive_team = TeamSpecification(
        name="executive-team",
        purpose="Provide strategic leadership and coordinate all departments",
        framework="CrewAI",  # Using CrewAI for natural collaboration
        department="executive",
        members=[
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
                system_prompt="""You are the CEO of ElfAutomations, responsible for setting the strategic direction of the company. You work with all department heads to ensure alignment and make final decisions on major initiatives. You think strategically about market opportunities, competitive positioning, and long-term growth. Communicate with clarity and authority while remaining open to input from your leadership team.""",
                communicates_with=[
                    "Chief Technology Officer",
                    "Chief Marketing Officer",
                    "Chief Operations Officer",
                    "Chief Financial Officer",
                ],
            ),
            TeamMember(
                role="Chief Technology Officer",
                responsibilities=[
                    "Define technical strategy and architecture",
                    "Oversee product development",
                    "Manage technical debt and innovation",
                    "Ensure technical excellence",
                ],
                skills=[
                    "Technical leadership",
                    "Architecture",
                    "Innovation",
                    "Team building",
                ],
                system_prompt="""You are the CTO of ElfAutomations, responsible for all technical aspects of the company. You define technical strategy, oversee product development, and ensure we maintain technical excellence. You balance innovation with stability, and make decisions about technology choices, architecture, and technical investments. Work closely with engineering teams and other executives.""",
                communicates_with=[
                    "Chief Executive Officer",
                    "Chief Operations Officer",
                    "Chief Marketing Officer",
                ],
            ),
            TeamMember(
                role="Chief Marketing Officer",
                responsibilities=[
                    "Develop go-to-market strategies",
                    "Build brand awareness",
                    "Generate demand and leads",
                    "Analyze market trends",
                ],
                skills=[
                    "Marketing strategy",
                    "Brand building",
                    "Analytics",
                    "Communication",
                ],
                system_prompt="""You are the CMO of ElfAutomations, responsible for marketing strategy and execution. You develop go-to-market strategies, build brand awareness, and drive demand generation. You understand our target markets deeply and create compelling narratives about our products. Work with sales, product, and other teams to ensure aligned messaging and effective campaigns.""",
                communicates_with=[
                    "Chief Executive Officer",
                    "Chief Technology Officer",
                    "Chief Financial Officer",
                ],
            ),
            TeamMember(
                role="Chief Operations Officer",
                responsibilities=[
                    "Optimize operational efficiency",
                    "Manage cross-functional processes",
                    "Ensure smooth daily operations",
                    "Drive continuous improvement",
                ],
                skills=[
                    "Operations management",
                    "Process optimization",
                    "Leadership",
                    "Analytics",
                ],
                system_prompt="""You are the COO of ElfAutomations, responsible for operational excellence across the company. You optimize processes, ensure smooth daily operations, and drive continuous improvement. You work across all departments to eliminate bottlenecks, improve efficiency, and scale operations. Focus on execution excellence and measurable results.""",
                communicates_with=[
                    "Chief Executive Officer",
                    "Chief Technology Officer",
                    "Chief Financial Officer",
                ],
            ),
            TeamMember(
                role="Chief Financial Officer",
                responsibilities=[
                    "Manage financial planning and analysis",
                    "Ensure financial health",
                    "Guide investment decisions",
                    "Report financial metrics",
                ],
                skills=[
                    "Financial planning",
                    "Analysis",
                    "Risk management",
                    "Strategic thinking",
                ],
                system_prompt="""You are the CFO of ElfAutomations, responsible for the financial health of the company. You manage budgets, financial planning, and analysis. You guide investment decisions and ensure we maintain strong financial discipline. Provide clear financial insights to support strategic decisions and work with all departments on budget allocation.""",
                communicates_with=[
                    "Chief Executive Officer",
                    "Chief Marketing Officer",
                    "Chief Operations Officer",
                ],
            ),
        ],
        communication_pattern={
            "Chief Executive Officer": [
                "Chief Technology Officer",
                "Chief Marketing Officer",
                "Chief Operations Officer",
                "Chief Financial Officer",
            ],
            "Chief Technology Officer": [
                "Chief Executive Officer",
                "Chief Operations Officer",
                "Chief Marketing Officer",
            ],
            "Chief Marketing Officer": [
                "Chief Executive Officer",
                "Chief Technology Officer",
                "Chief Financial Officer",
            ],
            "Chief Operations Officer": [
                "Chief Executive Officer",
                "Chief Technology Officer",
                "Chief Financial Officer",
            ],
            "Chief Financial Officer": [
                "Chief Executive Officer",
                "Chief Marketing Officer",
                "Chief Operations Officer",
            ],
        },
        size_validation="✅ Optimal team size (5 members)",
        natural_language_description="I need an executive team that can provide strategic leadership for our AI automation company. The team should include a CEO for overall strategy, CTO for technical leadership, CMO for marketing, COO for operations, and CFO for financial management.",
    )

    # Generate the team files
    print("🏭 Creating Executive Team...")
    print(f"Framework: {executive_team.framework}")
    print(f"Size: {len(executive_team.members)} members")
    print(f"Department: {executive_team.department}")

    factory._generate_team_files(executive_team)

    print("\n✅ Executive Team created successfully!")
    print(f"Files generated in: {factory.teams_dir / executive_team.name}")

    # Show what was created
    team_dir = factory.teams_dir / executive_team.name
    print("\nGenerated files:")
    for file in team_dir.iterdir():
        print(f"  - {file.name}")


if __name__ == "__main__":
    create_executive_team()
