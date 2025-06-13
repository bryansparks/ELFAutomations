"""
Constants and configuration values for team factory.
"""

# Personality traits
PERSONALITY_TRAITS = {
    "skeptic": {
        "description": "Constructively challenges ideas and identifies potential issues",
        "modifiers": [
            "You have a skeptical mindset and constructively challenge ideas.",
            "You identify potential flaws, edge cases, and risks in proposals.",
            "You ask critical questions to ensure robustness.",
            "You balance skepticism with support for well-reasoned ideas.",
        ],
    },
    "optimist": {
        "description": "Focuses on possibilities and maintains positive outlook",
        "modifiers": [
            "You maintain an optimistic outlook and focus on possibilities.",
            "You encourage the team and highlight potential benefits.",
            "You help maintain team morale during challenges.",
            "You see opportunities where others might see obstacles.",
        ],
    },
    "detail-oriented": {
        "description": "Ensures thoroughness and catches important details",
        "modifiers": [
            "You are extremely detail-oriented and thorough.",
            "You ensure nothing important is overlooked.",
            "You double-check work for accuracy and completeness.",
            "You maintain high standards for quality.",
        ],
    },
    "innovator": {
        "description": "Brings creative solutions and thinks outside the box",
        "modifiers": [
            "You are creative and bring innovative solutions.",
            "You think outside conventional boundaries.",
            "You propose novel approaches to problems.",
            "You encourage experimentation and creative thinking.",
        ],
    },
    "pragmatist": {
        "description": "Focuses on practical, implementable solutions",
        "modifiers": [
            "You focus on practical, implementable solutions.",
            "You consider resource constraints and feasibility.",
            "You prioritize what can be done over what would be ideal.",
            "You help the team stay grounded in reality.",
        ],
    },
    "collaborator": {
        "description": "Facilitates team cooperation and communication",
        "modifiers": [
            "You excel at facilitating team collaboration.",
            "You ensure everyone's voice is heard.",
            "You help resolve conflicts constructively.",
            "You build consensus and foster team unity.",
        ],
    },
    "analyzer": {
        "description": "Provides data-driven insights and analysis",
        "modifiers": [
            "You provide data-driven analysis and insights.",
            "You break down complex problems systematically.",
            "You use logic and evidence to support decisions.",
            "You help the team make informed choices.",
        ],
    },
}

# Department to executive mappings
DEPARTMENT_EXECUTIVE_MAPPING = {
    "engineering": "CTO",
    "qa": "CTO",
    "devops": "CTO",
    "infrastructure": "CTO",
    "data": "CTO",
    "marketing": "CMO",
    "content": "CMO",
    "brand": "CMO",
    "social": "CMO",
    "pr": "CMO",
    "operations": "COO",
    "hr": "COO",
    "facilities": "COO",
    "logistics": "COO",
    "support": "COO",
    "finance": "CFO",
    "accounting": "CFO",
    "budget": "CFO",
    "treasury": "CFO",
    "audit": "CFO",
    "strategy": "CEO",
    "vision": "CEO",
    "executive": "CEO",
    "board": "CEO",
}

# Framework configurations
FRAMEWORK_CONFIGS = {
    "CrewAI": {
        "supports_process": ["sequential", "hierarchical"],
        "default_process": "sequential",
        "large_team_process": "hierarchical",
        "large_team_threshold": 4,
    },
    "LangGraph": {
        "supports_process": ["workflow"],
        "default_process": "workflow",
        "requires_state": True,
    },
}

# LLM configurations
LLM_PROVIDERS = {
    "OpenAI": {
        "models": ["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"],
        "default_model": "gpt-4",
        "env_var": "OPENAI_API_KEY",
    },
    "Anthropic": {
        "models": [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
        "default_model": "claude-3-sonnet-20240229",
        "env_var": "ANTHROPIC_API_KEY",
    },
}

# Team size constraints
MIN_TEAM_SIZE = 2
MAX_TEAM_SIZE = 7
OPTIMAL_TEAM_SIZE = 5
SKEPTIC_THRESHOLD = 5  # Teams >= this size get a skeptic

# File naming patterns
AGENT_FILE_PATTERN = "{name}.py"
CONFIG_FILE_PATTERN = "{name}_config.yaml"
LOG_FILE_PATTERN = "{name}_communications.log"
