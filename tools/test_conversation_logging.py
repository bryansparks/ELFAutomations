#!/usr/bin/env python3
"""
Test script to demonstrate conversation logging functionality
"""

import json
import time
from datetime import datetime
from pathlib import Path

from conversation_logging_system import ConversationLogger, MessageType
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def simulate_team_conversation():
    """Simulate a realistic team conversation with logging"""

    console.print("\n[bold cyan]🎭 Simulating Marketing Team Conversation[/bold cyan]\n")

    # Initialize logger
    logger = ConversationLogger("marketing-team")

    # Start a task
    task_id = f"TASK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    task_description = "Plan Q2 Product Launch Campaign"

    console.print(f"[bold]Starting Task:[/bold] {task_description}")
    console.print(f"[dim]Task ID: {task_id}[/dim]\n")

    logger.start_conversation(task_id, task_description)

    try:
        # Marketing Manager kicks off
        logger.log_message(
            "Marketing Manager",
            "Team, we need to plan our Q2 product launch campaign. Our goal is to generate 1000 qualified leads.",
            MessageType.UPDATE,
        )
        time.sleep(0.5)

        # Content Creator proposes
        logger.log_message(
            "Content Creator",
            "I propose we create a video series showcasing the product's key features. We can distribute across YouTube, LinkedIn, and our website.",
            MessageType.PROPOSAL,
            to_agent="Marketing Manager",
        )
        time.sleep(0.5)

        # Data Analyst provides data
        logger.log_message(
            "Data Analyst",
            "Based on last quarter's data, video content had 73% higher engagement than static posts. Average view duration was 2:34.",
            MessageType.UPDATE,
            metadata={"confidence": 0.95, "data_source": "google_analytics"},
        )
        time.sleep(0.5)

        # Skeptic challenges
        logger.log_message(
            "Marketing Skeptic",
            "Video production for a series could take 6-8 weeks. Do we have enough time before Q2? What about the budget implications?",
            MessageType.CHALLENGE,
            to_agent="Content Creator",
            metadata={"concern_level": "high"},
        )
        time.sleep(0.5)

        # Content Creator responds
        logger.log_message(
            "Content Creator",
            "Good point. We can use AI-assisted video creation tools to cut production time to 2-3 weeks. Budget estimate: $15K vs $45K traditional.",
            MessageType.ANSWER,
            to_agent="Marketing Skeptic",
        )
        time.sleep(0.5)

        # Campaign Specialist adds
        logger.log_message(
            "Campaign Specialist",
            "I can set up automated email sequences to nurture leads from the video campaign. Expected conversion rate: 12-15%.",
            MessageType.PROPOSAL,
        )
        time.sleep(0.5)

        # Marketing Manager makes decision
        logger.log_message(
            "Marketing Manager",
            "Approved. Let's proceed with the AI-assisted video series. Budget: $15K. Timeline: 3 weeks. Content Creator leads, Campaign Specialist handles distribution.",
            MessageType.DECISION,
            metadata={
                "budget_approved": 15000,
                "timeline_weeks": 3,
                "lead_assignment": "Content Creator",
            },
        )

        # Team acknowledges
        logger.log_message(
            "Content Creator",
            "Understood. I'll have the video scripts ready by end of week.",
            MessageType.AGREEMENT,
            to_agent="Marketing Manager",
        )

        logger.log_message(
            "Campaign Specialist",
            "I'll start setting up the campaign infrastructure and automation flows.",
            MessageType.AGREEMENT,
            to_agent="Marketing Manager",
        )

        logger.end_conversation("completed")

    except Exception as e:
        logger.end_conversation(f"failed: {str(e)}")
        raise

    console.print("\n[green]✅ Conversation logged successfully![/green]")

    return logger


def display_conversation_metrics(logger: ConversationLogger):
    """Display metrics from the conversation"""

    metrics = logger.get_metrics()

    # Create metrics table
    table = Table(
        title="Conversation Metrics", show_header=True, header_style="bold magenta"
    )
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="green", justify="right")

    table.add_row("Total Messages", str(metrics["total_messages"]))
    table.add_row("Decisions Made", str(metrics["decision_count"]))
    table.add_row("Challenges Raised", str(metrics["challenge_count"]))
    table.add_row("Active Participants", str(len(metrics["messages_by_agent"])))

    console.print("\n")
    console.print(table)

    # Message type breakdown
    type_table = Table(
        title="Messages by Type", show_header=True, header_style="bold cyan"
    )
    type_table.add_column("Type", style="yellow")
    type_table.add_column("Count", style="green", justify="right")

    for msg_type, count in metrics["messages_by_type"].items():
        type_table.add_row(msg_type.title(), str(count))

    console.print("\n")
    console.print(type_table)

    # Agent participation
    agent_table = Table(
        title="Agent Participation", show_header=True, header_style="bold yellow"
    )
    agent_table.add_column("Agent", style="cyan")
    agent_table.add_column("Messages", style="green", justify="right")

    for agent, count in metrics["messages_by_agent"].items():
        agent_table.add_row(agent, str(count))

    console.print("\n")
    console.print(agent_table)


def display_natural_log(team_name: str):
    """Display the natural language log"""

    log_file = Path(f"logs/conversations/{team_name}_natural.log")

    if log_file.exists():
        console.print("\n[bold]Natural Language Log:[/bold]\n")

        with open(log_file, "r") as f:
            lines = f.readlines()[-20:]  # Last 20 lines

        for line in lines:
            # Color code based on message type
            if "[PROPOSAL]" in line:
                console.print(f"[blue]{line.strip()}[/blue]")
            elif "[CHALLENGE]" in line:
                console.print(f"[yellow]{line.strip()}[/yellow]")
            elif "[DECISION]" in line:
                console.print(f"[green]{line.strip()}[/green]")
            elif "→" in line:
                console.print(f"[cyan]{line.strip()}[/cyan]")
            else:
                console.print(f"[dim]{line.strip()}[/dim]")


def display_conversation_patterns():
    """Show example patterns that Quality Auditor would identify"""

    patterns = Panel(
        """[bold]Identified Patterns:[/bold]

[green]✅ Positive Patterns:[/green]
• Data-driven decision making (analyst provided metrics before decision)
• Constructive challenge resolution (skeptic's concerns addressed with specifics)
• Clear role delegation in final decision
• Rapid consensus building after decision

[yellow]⚠️  Areas for Improvement:[/yellow]
• No discussion of success metrics for the campaign
• Risk mitigation strategies not explicitly discussed
• No mention of competitive analysis

[cyan]💡 Recommendations:[/cyan]
• Include KPI definitions in campaign planning
• Add risk assessment step before major decisions
• Incorporate competitive intelligence in proposals""",
        title="Quality Auditor Analysis",
        border_style="magenta",
    )

    console.print("\n")
    console.print(patterns)


if __name__ == "__main__":
    console.print("=" * 60)
    console.print("[bold]CONVERSATION LOGGING DEMONSTRATION[/bold]")
    console.print("=" * 60)

    # Run simulation
    logger = simulate_team_conversation()

    # Display metrics
    display_conversation_metrics(logger)

    # Show natural log
    display_natural_log("marketing-team")

    # Show analysis patterns
    display_conversation_patterns()

    # Show log file locations
    console.print("\n[bold]📁 Log Files Created:[/bold]")
    console.print(
        f"• Structured: logs/conversations/marketing-team_conversations.jsonl"
    )
    console.print(f"• Natural: logs/conversations/marketing-team_natural.log")

    console.print(
        "\n[bold green]✨ This demonstrates how every team conversation is captured for continuous improvement![/bold green]"
    )
