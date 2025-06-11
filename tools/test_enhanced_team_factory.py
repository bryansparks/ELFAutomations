#!/usr/bin/env python3
"""
Test script to demonstrate enhanced team factory with contextual prompts
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel

from tools.prompt_template_system import PromptTemplateSystem
from tools.team_factory import TeamFactory

console = Console()


def demonstrate_enhanced_prompts():
    """Show the difference between basic and enhanced prompts"""

    console.print("\n[bold cyan]🚀 Enhanced Team Factory Demo[/bold cyan]\n")

    # Create a simple team member for comparison
    basic_prompt = "You are the Marketing Manager responsible for developing and executing marketing strategies."

    console.print(
        Panel(
            f"[bold]BASIC PROMPT:[/bold]\n{basic_prompt}",
            title="Traditional Prompt",
            border_style="red",
        )
    )

    # Show what an enhanced prompt looks like
    enhanced_example = """You are marketing_manager, the Marketing Manager for the marketing-automation at ElfAutomations.

**ORGANIZATION CONTEXT:**
- Mission: Revolutionize business operations through intelligent agent teams
- Stage: Series A startup, 50 customers, growing 20% monthly
- Current Priorities: Scale customer acquisition, Maintain system reliability, Expand team capabilities

**YOUR TEAM'S PURPOSE:**
Drive customer acquisition through innovative campaigns and data-driven strategies while building a beloved brand.

**TEAM GOALS:**
- Increase qualified leads by 50% quarter-over-quarter
- Build brand awareness in target market segments
- Create scalable, repeatable marketing processes

**YOUR ROLE:**
As the marketing-automation Manager, you orchestrate team activities, make final decisions after considering all input, and ensure alignment with company objectives. You delegate effectively while maintaining accountability.

**YOUR APPROACH:**
Be decisive but inclusive. Listen actively, synthesize diverse viewpoints, and make timely decisions. Ask 'What are we missing?' before finalizing plans.

**TEAM DYNAMICS:**
- content_creator (Content Creator): Innovative thinker, responds well to brainstorming and 'yes, and' approach
- data_analyst (Data Analyst): Data-driven, prefers evidence-based discussions with clear metrics
- campaign_specialist (Campaign Specialist): Domain expert, values precision and practical application
- quality_skeptic (Quality Skeptic): Constructive challenger, values thorough analysis and alternative perspectives

**KEY PRINCIPLES:**
- Time-box discussions to 15 minutes maximum
- Always state assumptions explicitly
- Data beats opinions, but intuition matters
- Perfect is the enemy of good enough
- Managers guide, not micromanage

**SUCCESS CRITERIA:**
- Team achieves objectives without burnout
- Decisions made efficiently with team buy-in
- Clear communication up and down the organization
- Team members grow and develop skills

**COMMUNICATION STYLE:**
Be clear and decisive. Summarize discussions, state decisions explicitly, and explain reasoning. Use 'I've decided...' after considering input.

**YOUR TOOLS:**
- market_research
- competitor_analysis
- campaign_tracker

**OPERATING CONSTRAINTS:**
- Limited to $50K monthly marketing budget
- Must show ROI within 60 days
- Comply with all data privacy regulations"""

    console.print("\n")
    console.print(
        Panel(
            f"[bold]ENHANCED PROMPT:[/bold]\n{enhanced_example}",
            title="Context-Rich Prompt",
            border_style="green",
        )
    )

    console.print("\n[bold yellow]Key Differences:[/bold yellow]")
    console.print("✅ Organization context and mission")
    console.print("✅ Specific team goals and metrics")
    console.print("✅ Detailed role expectations")
    console.print("✅ Team dynamics and interaction styles")
    console.print("✅ Operating principles and constraints")
    console.print("✅ Communication guidelines")
    console.print("✅ Available tools and resources")

    console.print(
        "\n[bold cyan]The enhanced prompt provides 10x more context, leading to:[/bold cyan]"
    )
    console.print("• Better decision making")
    console.print("• More natural team interactions")
    console.print("• Clearer understanding of success")
    console.print("• Improved collaboration")

    console.print(
        "\n[bold green]Ready to create your first team with enhanced prompts![/bold green]"
    )
    console.print("\nRun: [bold]python team_factory.py[/bold]")
    console.print(
        "\nOr modify existing prompts: [bold]python team_factory.py --modify-prompt --team marketing-team --agent marketing_manager[/bold]"
    )


if __name__ == "__main__":
    demonstrate_enhanced_prompts()
