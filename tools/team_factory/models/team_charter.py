"""
Team Charter model for capturing team purpose and goals.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TeamCharter:
    """Defines the team's purpose, goals, and operating principles."""
    
    # Core purpose
    mission_statement: str
    vision: str  # What success looks like
    
    # Objectives
    primary_objectives: List[str] = field(default_factory=list)  # 3-5 key goals
    success_metrics: List[str] = field(default_factory=list)  # How we measure success
    
    # Operating principles
    decision_making_process: str = "consensus"  # consensus, hierarchical, delegated
    communication_style: str = "collaborative"  # collaborative, formal, rapid
    
    # Boundaries
    scope_boundaries: List[str] = field(default_factory=list)  # What we DON'T do
    resource_constraints: List[str] = field(default_factory=list)  # Limitations
    
    # External relationships
    key_stakeholders: List[str] = field(default_factory=list)  # Who we serve/report to
    dependencies: List[str] = field(default_factory=list)  # What we need from others
    
    # Project management awareness
    participates_in_multi_team_projects: bool = True
    project_coordination_approach: str = "autonomous"  # autonomous, directed, collaborative
    
    # Review and adaptation
    review_frequency: str = "weekly"  # How often to review performance
    adaptation_triggers: List[str] = field(default_factory=list)  # When to change approach
    
    def to_prompt_context(self) -> str:
        """Convert charter to context for agent prompts."""
        return f"""
Team Charter:

Mission: {self.mission_statement}
Vision: {self.vision}

Key Objectives:
{chr(10).join(f'- {obj}' for obj in self.primary_objectives)}

Success Metrics:
{chr(10).join(f'- {metric}' for metric in self.success_metrics)}

Decision Making: {self.decision_making_process}
Communication Style: {self.communication_style}

Scope Boundaries:
{chr(10).join(f'- {boundary}' for boundary in self.scope_boundaries)}

Multi-Team Project Participation: {'Yes' if self.participates_in_multi_team_projects else 'No'}
Project Coordination: {self.project_coordination_approach}
"""
    
    def to_manager_addendum(self) -> str:
        """Additional context for manager agents about project management."""
        if not self.participates_in_multi_team_projects:
            return ""
            
        return """
        
As a team manager, you have access to the organization's Project Management System. You can:
- Query for available projects matching your team's skills
- Create subtasks for complex projects requiring multiple teams
- Coordinate with other teams through task dependencies
- Track progress across multi-team initiatives

Use the project management MCP tools when:
- The task is too large for your team alone
- You need specific expertise from other teams
- Coordination with multiple teams is required
- Progress tracking across teams is needed

Remember: Your team is part of a larger ecosystem. Complex challenges often require 
orchestrating multiple teams effectively.
"""