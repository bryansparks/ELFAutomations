#!/usr/bin/env python3
"""
Sample tasks for product-team
"""

from typing import List

from crewai import Task


def create_strategic_planning_task(agent) -> Task:
    """Create a strategic planning task"""
    return Task(
        description="""
        Develop a comprehensive strategic plan for the next quarter.
        Consider market conditions, resource allocation, and team capabilities.
        Provide specific recommendations and action items.
        """,
        agent=agent,
        expected_output="A detailed strategic plan with specific goals and timelines",
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
        expected_output="A structured status report with clear insights and recommendations",
    )


def get_all_tasks(agents: dict) -> List[Task]:
    """Get all tasks for the team"""
    tasks = []

    # Add tasks based on team composition
    if "Chief Executive Officer" in agents:
        tasks.append(create_strategic_planning_task(agents["Chief Executive Officer"]))

    # Add more tasks as needed
    return tasks
