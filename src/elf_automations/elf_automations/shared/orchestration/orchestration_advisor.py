"""
Orchestration Advisor - Helps managers make intelligent orchestration decisions

This module provides tools and guidance for manager agents to decide when and how
to use different orchestration capabilities (direct delegation, project management,
or workflow engine).
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ComplexityFactors:
    """Factors that determine task complexity."""

    estimated_hours: float
    team_count: int
    skill_count: int
    dependency_type: str  # none, linear, complex
    approval_count: int
    error_impact: str  # low, medium, high
    visibility_required: str  # low, medium, high
    has_conditional_logic: bool
    requires_parallel_execution: bool


@dataclass
class OrchestrationDecision:
    """Result of orchestration analysis."""

    approach: str  # direct_delegation, project_management, workflow_engine
    confidence: float  # 0.0 to 1.0
    reasoning: List[str]
    decomposition: Optional[Dict] = None
    pattern_match: Optional[str] = None
    key_considerations: Optional[List[str]] = None


class OrchestrationAdvisor:
    """
    Provides guidance to manager agents on orchestration decisions.
    """

    # Decision thresholds
    THRESHOLDS = {
        "hours": {"direct": 2, "project": 24, "workflow": float("inf")},
        "teams": {"direct": 1, "project": 2, "workflow": float("inf")},
        "complexity_score": {"direct": 3, "project": 7, "workflow": float("inf")},
    }

    # Pattern indicators
    PATTERN_INDICATORS = {
        "workflow_required": [
            r"across all (teams|departments)",
            r"coordinate.*multiple teams",
            r"company-wide",
            r"rollout",
            r"staged deployment",
            r"approval.*gates?",
            r"executive.*approval",
            r"critical.*escalation",
            r"incident response",
        ],
        "project_suitable": [
            r"campaign",
            r"project",
            r"initiative",
            r"series of",
            r"phased approach",
            r"milestone",
            r"deliverable",
        ],
        "direct_suitable": [
            r"quick",
            r"simple",
            r"brief",
            r"review",
            r"update",
            r"fix",
            r"check",
            r"verify",
        ],
    }

    def __init__(self, patterns_file: Optional[Path] = None):
        self.patterns = self._load_patterns(patterns_file) if patterns_file else {}
        self.decision_history = []

    def analyze_request(
        self, request: str, context: Dict = None
    ) -> OrchestrationDecision:
        """
        Analyze a request and recommend orchestration approach.

        Args:
            request: The task request text
            context: Additional context (team capabilities, current workload, etc.)

        Returns:
            OrchestrationDecision with recommendation and reasoning
        """
        context = context or {}

        # Extract complexity factors
        factors = self._assess_complexity_factors(request, context)

        # Check for pattern matches
        pattern_match = self._match_patterns(request)

        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(factors)

        # Make decision
        decision = self._make_decision(factors, complexity_score, pattern_match)

        # Add reasoning
        decision.reasoning = self._generate_reasoning(
            factors, complexity_score, pattern_match
        )

        # Add decomposition if needed
        if decision.approach in ["project_management", "workflow_engine"]:
            decision.decomposition = self._decompose_request(
                request, decision.approach, factors
            )

        # Record decision for learning
        self._record_decision(request, context, factors, decision)

        logger.info(
            f"Orchestration decision: {decision.approach} (confidence: {decision.confidence:.2f})"
        )

        return decision

    def _assess_complexity_factors(
        self, request: str, context: Dict
    ) -> ComplexityFactors:
        """Extract complexity factors from request."""

        # Estimate hours based on keywords and request length
        hours = self._estimate_hours(request)

        # Count potential teams involved
        teams = self._estimate_teams(request, context)

        # Count unique skills needed
        skills = self._count_skills(request)

        # Assess dependency type
        dependency_type = self._assess_dependencies(request)

        # Count approval requirements
        approvals = self._count_approvals(request)

        # Assess error impact
        error_impact = self._assess_error_impact(request, context)

        # Determine visibility requirements
        visibility = self._assess_visibility(request, context)

        # Check for conditional logic
        has_conditionals = self._has_conditional_logic(request)

        # Check for parallel execution needs
        needs_parallel = self._needs_parallel_execution(request)

        return ComplexityFactors(
            estimated_hours=hours,
            team_count=teams,
            skill_count=skills,
            dependency_type=dependency_type,
            approval_count=approvals,
            error_impact=error_impact,
            visibility_required=visibility,
            has_conditional_logic=has_conditionals,
            requires_parallel_execution=needs_parallel,
        )

    def _calculate_complexity_score(self, factors: ComplexityFactors) -> float:
        """Calculate overall complexity score (0-10)."""

        score = 0.0

        # Time complexity (0-3 points)
        if factors.estimated_hours < 2:
            score += 0.5
        elif factors.estimated_hours < 8:
            score += 1.5
        elif factors.estimated_hours < 24:
            score += 2.5
        else:
            score += 3.0

        # Team complexity (0-2 points)
        score += min(factors.team_count * 0.5, 2.0)

        # Dependency complexity (0-2 points)
        if factors.dependency_type == "complex":
            score += 2.0
        elif factors.dependency_type == "linear":
            score += 1.0

        # Approval complexity (0-1 point)
        score += min(factors.approval_count * 0.25, 1.0)

        # Risk complexity (0-2 points)
        if factors.error_impact == "high":
            score += 2.0
        elif factors.error_impact == "medium":
            score += 1.0

        return min(score, 10.0)

    def _make_decision(
        self, factors: ComplexityFactors, score: float, pattern: Optional[str]
    ) -> OrchestrationDecision:
        """Make orchestration decision based on factors."""

        # Default to score-based decision
        if score <= self.THRESHOLDS["complexity_score"]["direct"]:
            approach = "direct_delegation"
            confidence = 0.9
        elif score <= self.THRESHOLDS["complexity_score"]["project"]:
            approach = "project_management"
            confidence = 0.8
        else:
            approach = "workflow_engine"
            confidence = 0.85

        # Override based on specific factors
        if factors.team_count >= 3 or factors.requires_parallel_execution:
            approach = "workflow_engine"
            confidence = 0.95
        elif factors.has_conditional_logic and factors.team_count > 1:
            approach = "workflow_engine"
            confidence = 0.9
        elif factors.approval_count >= 2:
            approach = "workflow_engine"
            confidence = 0.9

        # Pattern match can increase confidence
        if pattern:
            pattern_data = self.patterns.get(pattern, {})
            if pattern_data.get("recommended_approach") == approach:
                confidence = min(confidence + 0.1, 1.0)

        return OrchestrationDecision(
            approach=approach,
            confidence=confidence,
            reasoning=[],
            pattern_match=pattern,
        )

    def _generate_reasoning(
        self, factors: ComplexityFactors, score: float, pattern: Optional[str]
    ) -> List[str]:
        """Generate human-readable reasoning for decision."""

        reasoning = []

        # Time-based reasoning
        if factors.estimated_hours < 2:
            reasoning.append(
                f"Task estimated at {factors.estimated_hours:.1f} hours - suitable for direct handling"
            )
        elif factors.estimated_hours > 24:
            reasoning.append(
                f"Task estimated at {factors.estimated_hours:.1f} hours - requires structured coordination"
            )

        # Team-based reasoning
        if factors.team_count == 1:
            reasoning.append("Single team involved - minimal coordination needed")
        elif factors.team_count == 2:
            reasoning.append(
                "Two teams involved - project management can handle coordination"
            )
        else:
            reasoning.append(
                f"{factors.team_count} teams required - complex coordination needed"
            )

        # Dependency reasoning
        if factors.dependency_type == "complex":
            reasoning.append("Complex dependencies require workflow orchestration")
        elif factors.dependency_type == "linear":
            reasoning.append("Linear dependencies can be managed with project tracking")

        # Risk reasoning
        if factors.error_impact == "high":
            reasoning.append(
                "High error impact requires robust error handling of workflow engine"
            )

        # Pattern reasoning
        if pattern:
            reasoning.append(
                f"Matches '{pattern}' pattern - typically handled with this approach"
            )

        # Special conditions
        if factors.requires_parallel_execution:
            reasoning.append(
                "Parallel execution required - workflow engine recommended"
            )
        if factors.has_conditional_logic:
            reasoning.append(
                "Conditional logic present - workflow engine provides best support"
            )

        return reasoning

    def _decompose_request(
        self, request: str, approach: str, factors: ComplexityFactors
    ) -> Dict:
        """Decompose request into structured format for chosen approach."""

        if approach == "project_management":
            return self._decompose_for_project(request, factors)
        elif approach == "workflow_engine":
            return self._decompose_for_workflow(request, factors)
        else:
            return {}

    def _decompose_for_project(self, request: str, factors: ComplexityFactors) -> Dict:
        """Decompose into project structure."""

        return {
            "project_name": self._generate_project_name(request),
            "estimated_duration": f"{factors.estimated_hours:.0f} hours",
            "priority": "high" if factors.error_impact == "high" else "medium",
            "suggested_tasks": [
                {
                    "title": "Initial assessment and planning",
                    "estimated_hours": factors.estimated_hours * 0.1,
                    "dependencies": [],
                },
                {
                    "title": "Core implementation",
                    "estimated_hours": factors.estimated_hours * 0.6,
                    "dependencies": ["Initial assessment and planning"],
                },
                {
                    "title": "Review and validation",
                    "estimated_hours": factors.estimated_hours * 0.2,
                    "dependencies": ["Core implementation"],
                },
                {
                    "title": "Documentation and handoff",
                    "estimated_hours": factors.estimated_hours * 0.1,
                    "dependencies": ["Review and validation"],
                },
            ],
        }

    def _decompose_for_workflow(self, request: str, factors: ComplexityFactors) -> Dict:
        """Decompose into workflow structure."""

        phases = []

        # Assessment phase (usually needed)
        if factors.team_count > 2 or factors.error_impact == "high":
            phases.append(
                {
                    "name": "Assessment",
                    "type": "sequential",
                    "steps": [
                        "Analyze requirements",
                        "Identify risks",
                        "Plan approach",
                    ],
                }
            )

        # Execution phase
        if factors.requires_parallel_execution:
            phases.append(
                {
                    "name": "Parallel Execution",
                    "type": "parallel",
                    "steps": [f"Team {i+1} tasks" for i in range(factors.team_count)],
                }
            )
        else:
            phases.append(
                {
                    "name": "Sequential Execution",
                    "type": "sequential",
                    "steps": ["Phase 1 execution", "Phase 2 execution", "Integration"],
                }
            )

        # Approval phase
        if factors.approval_count > 0:
            phases.append(
                {
                    "name": "Approval",
                    "type": "approval",
                    "steps": [
                        f"Approval gate {i+1}" for i in range(factors.approval_count)
                    ],
                }
            )

        # Validation phase
        phases.append(
            {
                "name": "Validation",
                "type": "sequential",
                "steps": ["Quality check", "Integration testing", "Final review"],
            }
        )

        return {
            "workflow_name": self._generate_workflow_name(request),
            "estimated_duration": f"{factors.estimated_hours:.0f} hours",
            "phases": phases,
            "teams_involved": factors.team_count,
            "has_conditionals": factors.has_conditional_logic,
            "error_handling": "required"
            if factors.error_impact in ["medium", "high"]
            else "standard",
        }

    # Helper methods

    def _estimate_hours(self, request: str) -> float:
        """Estimate hours based on request complexity."""

        # Simple heuristic based on keywords and length
        hours = 2.0  # Base estimate

        # Adjust based on keywords
        if re.search(r"\b(quick|simple|brief|minor)\b", request, re.I):
            hours *= 0.5
        elif re.search(r"\b(comprehensive|detailed|extensive|major)\b", request, re.I):
            hours *= 3.0
        elif re.search(r"\b(complex|complicated|sophisticated)\b", request, re.I):
            hours *= 4.0

        # Adjust based on action words
        if re.search(r"\b(analyze|investigate|research)\b", request, re.I):
            hours *= 1.5
        elif re.search(r"\b(implement|build|develop|create)\b", request, re.I):
            hours *= 2.0
        elif re.search(r"\b(redesign|refactor|migrate)\b", request, re.I):
            hours *= 3.0

        # Adjust based on request length
        word_count = len(request.split())
        if word_count > 100:
            hours *= 1.5
        elif word_count < 20:
            hours *= 0.7

        return round(hours, 1)

    def _estimate_teams(self, request: str, context: Dict) -> int:
        """Estimate number of teams needed."""

        teams = 1  # Default

        # Check for explicit team mentions
        team_keywords = [
            "engineering",
            "marketing",
            "sales",
            "support",
            "finance",
            "operations",
            "hr",
            "legal",
            "executive",
        ]
        mentioned_teams = sum(1 for team in team_keywords if team in request.lower())

        if mentioned_teams > 1:
            teams = mentioned_teams

        # Check for cross-functional keywords
        if re.search(
            r"\b(cross-functional|all teams|company-wide|organization-wide)\b",
            request,
            re.I,
        ):
            teams = 5  # Assume significant coordination
        elif re.search(
            r"\b(multiple teams|several teams|various departments)\b", request, re.I
        ):
            teams = 3

        return teams

    def _count_skills(self, request: str) -> int:
        """Count unique skills mentioned."""

        # Common skill keywords
        skills = set()

        skill_patterns = [
            r"\b(python|javascript|react|java|sql|api)\b",
            r"\b(design|ux|ui|graphics|visual)\b",
            r"\b(writing|content|copy|documentation)\b",
            r"\b(analysis|data|metrics|reporting)\b",
            r"\b(testing|qa|quality|validation)\b",
            r"\b(deployment|devops|infrastructure)\b",
        ]

        for pattern in skill_patterns:
            if re.search(pattern, request, re.I):
                skills.add(pattern)

        return len(skills)

    def _assess_dependencies(self, request: str) -> str:
        """Assess dependency complexity."""

        # Check for dependency indicators
        if re.search(
            r"\b(after|then|followed by|depends on|requires)\b", request, re.I
        ):
            # Check for complex patterns
            if re.search(
                r"\b(if.*then|when.*then|conditional|branch)\b", request, re.I
            ):
                return "complex"
            else:
                return "linear"

        return "none"

    def _count_approvals(self, request: str) -> int:
        """Count approval requirements."""

        approvals = 0

        # Direct approval mentions
        approval_matches = re.findall(
            r"\b(approval|approve|sign-off|authorization)\b", request, re.I
        )
        approvals += len(approval_matches)

        # Executive mentions often imply approval
        if re.search(r"\b(executive|ceo|cfo|cto|board)\b", request, re.I):
            approvals += 1

        # Budget mentions often require approval
        if re.search(
            r"\b(budget|funding|investment|cost.*thousand|cost.*million)\b",
            request,
            re.I,
        ):
            approvals += 1

        return min(approvals, 3)  # Cap at 3

    def _assess_error_impact(self, request: str, context: Dict) -> str:
        """Assess potential error impact."""

        # High impact indicators
        if re.search(
            r"\b(critical|emergency|urgent|production|customer-facing|revenue)\b",
            request,
            re.I,
        ):
            return "high"

        # Medium impact indicators
        elif re.search(
            r"\b(important|significant|user-facing|external)\b", request, re.I
        ):
            return "medium"

        # Low impact by default
        return "low"

    def _assess_visibility(self, request: str, context: Dict) -> str:
        """Assess visibility requirements."""

        # High visibility indicators
        if re.search(
            r"\b(executive|board|investor|public|company-wide)\b", request, re.I
        ):
            return "high"

        # Medium visibility indicators
        elif re.search(
            r"\b(stakeholder|management|report|metrics|kpi)\b", request, re.I
        ):
            return "medium"

        return "low"

    def _has_conditional_logic(self, request: str) -> bool:
        """Check for conditional logic indicators."""

        conditional_patterns = [
            r"\b(if.*then|when.*then)\b",
            r"\b(conditional|depends on|based on)\b",
            r"\b(either.*or|whether)\b",
            r"\b(in case of|should.*occur)\b",
        ]

        return any(
            re.search(pattern, request, re.I) for pattern in conditional_patterns
        )

    def _needs_parallel_execution(self, request: str) -> bool:
        """Check if parallel execution is needed."""

        parallel_patterns = [
            r"\b(parallel|simultaneously|at the same time|concurrently)\b",
            r"\b(while.*also|both.*and)\b",
            r"\b(multiple.*teams.*same time)\b",
        ]

        return any(re.search(pattern, request, re.I) for pattern in parallel_patterns)

    def _match_patterns(self, request: str) -> Optional[str]:
        """Match request against known patterns."""

        request_lower = request.lower()

        # Check each pattern
        for pattern_name, pattern_data in self.patterns.items():
            indicators = pattern_data.get("indicators", [])
            if any(indicator in request_lower for indicator in indicators):
                return pattern_name

        # Check regex patterns
        for pattern_type, patterns in self.PATTERN_INDICATORS.items():
            for pattern in patterns:
                if re.search(pattern, request, re.I):
                    return pattern_type

        return None

    def _generate_project_name(self, request: str) -> str:
        """Generate a project name from request."""

        # Extract key words
        words = request.split()[:10]  # First 10 words

        # Remove common words
        stop_words = {"the", "a", "an", "to", "for", "of", "and", "or", "in", "on"}
        key_words = [w for w in words if w.lower() not in stop_words]

        # Take first 3-4 key words
        name_words = key_words[:4]

        return " ".join(name_words).title()

    def _generate_workflow_name(self, request: str) -> str:
        """Generate a workflow name from request."""

        # Similar to project name but formatted differently
        project_name = self._generate_project_name(request)

        # Convert to workflow format
        return project_name.lower().replace(" ", "-") + "-workflow"

    def _load_patterns(self, patterns_file: Path) -> Dict:
        """Load patterns from YAML file."""

        try:
            with open(patterns_file) as f:
                data = yaml.safe_load(f)
                return {p["name"]: p for p in data.get("patterns", [])}
        except Exception as e:
            logger.warning(f"Could not load patterns: {e}")
            return {}

    def _record_decision(
        self,
        request: str,
        context: Dict,
        factors: ComplexityFactors,
        decision: OrchestrationDecision,
    ):
        """Record decision for future learning."""

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "request": request[:200],  # First 200 chars
            "context": context,
            "factors": {
                "hours": factors.estimated_hours,
                "teams": factors.team_count,
                "skills": factors.skill_count,
                "dependencies": factors.dependency_type,
                "approvals": factors.approval_count,
                "error_impact": factors.error_impact,
            },
            "decision": decision.approach,
            "confidence": decision.confidence,
            "pattern_match": decision.pattern_match,
        }

        self.decision_history.append(record)

        # Keep only last 1000 decisions
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]


# Example usage
if __name__ == "__main__":
    advisor = OrchestrationAdvisor()

    # Test various requests
    test_requests = [
        "Create a blog post about our new feature",
        "Launch a comprehensive marketing campaign for our new product across all channels",
        "Coordinate the rollout of the new AI model across all teams with staged deployment",
        "Fix the typo in the homepage header",
        "Handle critical customer escalation from Fortune 500 client",
        "Create a series of training videos for the sales team",
    ]

    for request in test_requests:
        print(f"\nRequest: {request}")
        decision = advisor.analyze_request(request)
        print(f"Decision: {decision.approach} (confidence: {decision.confidence:.2f})")
        print(f"Reasoning: {decision.reasoning[0] if decision.reasoning else 'N/A'}")
