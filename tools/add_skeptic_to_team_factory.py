#!/usr/bin/env python3
"""
Enhancement to team_factory.py to support skeptic agents
This can be integrated into the main team_factory.py
"""


def create_skeptic_agent(team_name: str, framework: str = "crewai") -> dict:
    """Create a skeptic agent configuration"""

    if framework.lower() == "crewai":
        return {
            "name": f"{team_name}_skeptic",
            "role": "Team Skeptic and Quality Advocate",
            "goal": "Improve team decisions through constructive challenge and risk identification",
            "backstory": """You've seen too many projects fail from uncaught edge cases and
            unquestioned assumptions. Your role is to be the constructive challenger who asks
            the hard questions, identifies risks, and ensures the team has thought through all
            angles. You're not negative for negativity's sake - you want the team to succeed
            by being thoroughly prepared.""",
            "tools": ["risk_assessment", "precedent_search", "assumption_validator"],
            "characteristics": [
                "Questions assumptions constructively",
                "Identifies potential failure modes",
                "Proposes stress tests and edge cases",
                "Offers alternatives when challenging ideas",
                "Knows when to yield to team consensus",
            ],
        }

    elif framework.lower() == "langgraph":
        return {
            "name": f"{team_name}_skeptic",
            "node_type": "skeptic",
            "description": "Reviews and challenges team proposals",
            "inputs": ["proposal", "context"],
            "outputs": ["concerns", "risk_level", "recommendations"],
            "behavior": {
                "challenge_threshold": 0.3,  # How skeptical (0-1)
                "time_limit_minutes": 15,
                "escalation_triggers": [
                    "high_risk",
                    "security_concern",
                    "compliance_issue",
                ],
            },
        }


def add_skeptic_to_team_composition(
    agents: list, team_size: int, include_skeptic: bool = None
) -> list:
    """
    Determine if team should have a skeptic and add if appropriate

    Rules:
    - Teams with 5+ agents: Always include skeptic
    - Teams with 3-4 agents: Optional (ask user)
    - Teams with <3 agents: No dedicated skeptic (too small)
    """

    if team_size >= 5:
        # Always include for larger teams
        return True
    elif team_size >= 3:
        # Optional for medium teams
        if include_skeptic is None:
            # In actual implementation, this would prompt user
            return False
        return include_skeptic
    else:
        # Too small for dedicated skeptic
        return False


def create_skeptic_resolution_protocol(team_name: str) -> dict:
    """Create a resolution protocol for skeptic challenges"""

    return {
        "protocol_name": f"{team_name}_skeptic_resolution",
        "rules": [
            {
                "condition": "minor_concern",
                "action": "team_adjusts_and_proceeds",
                "time_limit": "5 minutes",
            },
            {
                "condition": "major_concern",
                "action": "manager_decides",
                "time_limit": "15 minutes",
                "escalation_path": "executive_team",
            },
            {
                "condition": "critical_risk",
                "action": "immediate_escalation",
                "notify": ["manager", "relevant_executive"],
            },
        ],
        "documentation": {
            "log_decisions": True,
            "capture_rationale": True,
            "track_outcomes": True,
        },
    }


# Example integration with team factory
def enhance_team_with_skeptic(team_config: dict, framework: str = "crewai") -> dict:
    """
    Enhance existing team configuration with skeptic if appropriate
    """

    team_name = team_config.get("name", "team")
    agents = team_config.get("agents", [])
    team_size = len(agents)

    # Check if we should add a skeptic
    should_add_skeptic = add_skeptic_to_team_composition(agents, team_size)

    if should_add_skeptic:
        # Create skeptic agent
        skeptic = create_skeptic_agent(team_name, framework)

        # Add to agents list
        agents.append(skeptic)

        # Add resolution protocol
        team_config["skeptic_resolution"] = create_skeptic_resolution_protocol(
            team_name
        )

        # Update manager's responsibilities
        for agent in agents:
            if agent.get("role", "").lower().find("manager") != -1:
                agent.setdefault("additional_responsibilities", []).extend(
                    [
                        "Arbitrate skeptic challenges",
                        "Ensure time-boxed decision making",
                        "Document overruled concerns and rationale",
                    ]
                )
                break

    team_config["agents"] = agents
    return team_config


if __name__ == "__main__":
    # Example usage
    sample_team = {
        "name": "marketing_automation",
        "agents": [
            {"name": "marketing_manager", "role": "Marketing Manager"},
            {"name": "content_creator", "role": "Content Creator"},
            {"name": "data_analyst", "role": "Data Analyst"},
            {"name": "campaign_specialist", "role": "Campaign Specialist"},
            {"name": "seo_expert", "role": "SEO Expert"},
        ],
    }

    enhanced_team = enhance_team_with_skeptic(sample_team)

    # Show the skeptic was added
    print(f"Team size: {len(enhanced_team['agents'])}")
    print(
        f"Has skeptic: {any(a['name'].endswith('_skeptic') for a in enhanced_team['agents'])}"
    )

    # Show resolution protocol was added
    print(f"Has resolution protocol: {'skeptic_resolution' in enhanced_team}")
