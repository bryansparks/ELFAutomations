#!/usr/bin/env python3
"""
Analyze team composition and suggest MCP optimizations
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.team_factory import TeamMember, TeamSpecification


@dataclass
class MCPSuggestion:
    """Suggestion for converting an agent to MCP usage"""

    original_role: str
    suggested_mcps: List[str]
    tool_operation_percentage: int
    recommendation: str  # "convert", "hybrid", "keep"
    rationale: str


class MCPOptimizationAnalyzer:
    """Analyzes teams and suggests MCP optimizations"""

    def __init__(self):
        # Keywords that indicate tool-heavy operations
        self.tool_keywords = {
            "search": 90,
            "fetch": 85,
            "scrape": 95,
            "analyze": 70,
            "extract": 90,
            "monitor": 85,
            "track": 80,
            "collect": 85,
            "parse": 90,
            "query": 85,
        }

        # Keywords that indicate decision-making
        self.decision_keywords = {
            "strategize": 90,
            "decide": 85,
            "coordinate": 80,
            "plan": 75,
            "design": 70,
            "lead": 85,
            "manage": 80,
            "synthesize": 70,
            "evaluate": 65,
            "prioritize": 75,
        }

        # MCP mappings by domain
        self.mcp_suggestions = {
            "web": ["web-scraper-mcp", "content-parser-mcp", "url-monitor-mcp"],
            "social": ["twitter-mcp", "linkedin-mcp", "reddit-mcp", "sentiment-mcp"],
            "academic": [
                "arxiv-mcp",
                "pubmed-mcp",
                "semantic-scholar-mcp",
                "citation-mcp",
            ],
            "technical": ["github-mcp", "docs-parser-mcp", "api-explorer-mcp"],
            "data": ["database-mcp", "analytics-mcp", "visualization-mcp"],
            "communication": ["email-mcp", "slack-mcp", "notification-mcp"],
        }

    def analyze_team(self, team_spec: TeamSpecification) -> Dict[str, MCPSuggestion]:
        """Analyze team and suggest MCP optimizations"""
        suggestions = {}

        for member in team_spec.members:
            suggestion = self._analyze_member(member)
            suggestions[member.role] = suggestion

        return suggestions

    def _analyze_member(self, member: TeamMember) -> MCPSuggestion:
        """Analyze individual team member for MCP potential"""

        # Calculate tool vs decision percentages
        tool_score = self._calculate_tool_score(member)
        decision_score = self._calculate_decision_score(member)

        # Determine recommendation
        if tool_score > 80:
            recommendation = "convert"
            rationale = f"This role is {tool_score}% tool operations. Perfect for MCP conversion."
        elif tool_score > 60 and decision_score < 40:
            recommendation = "hybrid"
            rationale = f"This role mixes tools ({tool_score}%) and decisions ({decision_score}%). Consider hybrid approach."
        else:
            recommendation = "keep"
            rationale = f"This role requires significant decision-making ({decision_score}%). Keep as intelligent agent."

        # Suggest appropriate MCPs
        suggested_mcps = self._suggest_mcps_for_role(member)

        return MCPSuggestion(
            original_role=member.role,
            suggested_mcps=suggested_mcps,
            tool_operation_percentage=tool_score,
            recommendation=recommendation,
            rationale=rationale,
        )

    def _calculate_tool_score(self, member: TeamMember) -> int:
        """Calculate percentage of role that is tool operations"""
        score = 0
        count = 0

        # Check responsibilities
        for responsibility in member.responsibilities:
            resp_lower = responsibility.lower()
            for keyword, weight in self.tool_keywords.items():
                if keyword in resp_lower:
                    score += weight
                    count += 1
                    break

        # Check skills
        for skill in member.skills:
            skill_lower = skill.lower()
            for keyword, weight in self.tool_keywords.items():
                if keyword in skill_lower:
                    score += weight * 0.5  # Skills weighted less than responsibilities
                    count += 0.5
                    break

        return int(score / max(count, 1))

    def _calculate_decision_score(self, member: TeamMember) -> int:
        """Calculate percentage of role that is decision-making"""
        score = 0
        count = 0

        # Check responsibilities
        for responsibility in member.responsibilities:
            resp_lower = responsibility.lower()
            for keyword, weight in self.decision_keywords.items():
                if keyword in resp_lower:
                    score += weight
                    count += 1
                    break

        # Check if manager/lead role
        if any(
            word in member.role.lower()
            for word in ["manager", "lead", "chief", "director"]
        ):
            score += 20
            count += 0.25

        return int(score / max(count, 1))

    def _suggest_mcps_for_role(self, member: TeamMember) -> List[str]:
        """Suggest appropriate MCPs based on role"""
        suggested = []
        role_lower = member.role.lower()

        # Check each domain
        for domain, mcps in self.mcp_suggestions.items():
            if domain in role_lower or any(
                domain in resp.lower() for resp in member.responsibilities
            ):
                suggested.extend(mcps[:2])  # Take top 2 MCPs from each matching domain

        # Remove duplicates while preserving order
        seen = set()
        unique_suggested = []
        for mcp in suggested:
            if mcp not in seen:
                seen.add(mcp)
                unique_suggested.append(mcp)

        return unique_suggested[:4]  # Limit to 4 MCPs per role

    def generate_optimized_team(
        self, team_spec: TeamSpecification, suggestions: Dict[str, MCPSuggestion]
    ) -> Tuple[List[TeamMember], List[str]]:
        """Generate optimized team structure based on suggestions"""

        new_members = []
        required_mcps = set()

        # Keep decision-making agents
        for member in team_spec.members:
            suggestion = suggestions[member.role]

            if suggestion.recommendation == "keep":
                new_members.append(member)
            elif suggestion.recommendation == "hybrid":
                # Keep but note MCP dependencies
                new_members.append(member)
                required_mcps.update(suggestion.suggested_mcps)
            # "convert" recommendation means this role becomes MCP-only
            else:
                required_mcps.update(suggestion.suggested_mcps)

        # Ensure at least one orchestrator
        if not any(
            "lead" in m.role.lower() or "manager" in m.role.lower() for m in new_members
        ):
            # Keep the first member as orchestrator
            if team_spec.members:
                new_members.insert(0, team_spec.members[0])

        return new_members, list(required_mcps)


def demo_analysis():
    """Demo the MCP optimization analysis"""
    from tools.team_factory import TeamFactory

    factory = TeamFactory()

    # Create a research team
    team_spec = factory._generate_team_suggestion(
        "Create a research team for web research, academic papers, and social media",
        framework="CrewAI",
        llm_provider="OpenAI",
        llm_model="gpt-4",
    )

    # Analyze it
    analyzer = MCPOptimizationAnalyzer()
    suggestions = analyzer.analyze_team(team_spec)

    print(f"\n🔍 MCP Optimization Analysis for {team_spec.name}")
    print("=" * 60)

    for role, suggestion in suggestions.items():
        emoji = {"convert": "🔄", "hybrid": "🤝", "keep": "✅"}[suggestion.recommendation]
        print(f"\n{emoji} {role}")
        print(f"   Tool Operations: {suggestion.tool_operation_percentage}%")
        print(f"   Recommendation: {suggestion.recommendation.upper()}")
        print(f"   Rationale: {suggestion.rationale}")
        if suggestion.suggested_mcps:
            print(f"   Suggested MCPs: {', '.join(suggestion.suggested_mcps)}")

    # Generate optimized team
    new_members, required_mcps = analyzer.generate_optimized_team(
        team_spec, suggestions
    )

    print(f"\n🚀 Optimized Team Structure")
    print("=" * 60)
    print(f"Original: {len(team_spec.members)} agents")
    print(f"Optimized: {len(new_members)} agents + {len(required_mcps)} MCPs")
    print(f"\nRemaining Agents:")
    for member in new_members:
        print(f"  - {member.role}")
    print(f"\nRequired MCPs:")
    for mcp in required_mcps:
        print(f"  - {mcp}")


if __name__ == "__main__":
    demo_analysis()
