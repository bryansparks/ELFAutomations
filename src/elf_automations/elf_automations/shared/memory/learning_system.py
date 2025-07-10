"""
Learning System - Enables teams to learn and improve from their experiences

This module provides:
- Automatic pattern extraction from successful episodes
- Strategy optimization based on outcomes
- Knowledge transfer between team members
- Continuous improvement loops
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .team_memory import TeamMemory


class LearningSystem:
    """
    Learning system that enables teams to improve over time.

    Features:
    - Pattern recognition: Identify what works
    - Strategy evolution: Improve approaches over time
    - Failure analysis: Learn from mistakes
    - Knowledge synthesis: Combine learnings into strategies
    - Performance prediction: Estimate success likelihood
    """

    def __init__(self, team_memory: TeamMemory):
        """
        Initialize learning system.

        Args:
            team_memory: Team memory instance
        """
        self.memory = team_memory
        self.team_name = team_memory.team_name
        self.logger = logging.getLogger(f"LearningSystem.{self.team_name}")

        # Learning parameters
        self.min_episodes_for_learning = 5
        self.confidence_threshold = 0.7
        self.learning_rate = 0.1

    def learn_from_episode(self, episode: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract learnings from a completed episode.

        Args:
            episode: Completed episode data

        Returns:
            List of extracted learnings
        """
        learnings = []

        # Analyze success factors
        if episode.get("success"):
            success_factors = self._identify_success_factors(episode)
            for factor in success_factors:
                learning = {
                    "insight": f"Success factor: {factor['description']}",
                    "context": {
                        "task_type": self._categorize_task(episode["task_description"]),
                        "conditions": factor["conditions"],
                    },
                    "evidence": [episode["id"]],
                    "confidence": factor["confidence"],
                }
                learnings.append(learning)
        else:
            # Analyze failure causes
            failure_causes = self._identify_failure_causes(episode)
            for cause in failure_causes:
                learning = {
                    "insight": f"Failure cause: {cause['description']}",
                    "context": {
                        "task_type": self._categorize_task(episode["task_description"]),
                        "conditions": cause["conditions"],
                    },
                    "evidence": [episode["id"]],
                    "confidence": cause["confidence"],
                }
                learnings.append(learning)

        # Store learnings
        for learning in learnings:
            self.memory.store_learning(learning)

        self.logger.info(f"Extracted {len(learnings)} learnings from episode")
        return learnings

    def _identify_success_factors(
        self, episode: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify factors that contributed to success."""
        factors = []

        # Analyze agent contributions
        contributions = episode.get("agent_contributions", {})
        for agent, actions in contributions.items():
            if actions:
                factor = {
                    "description": f"{agent} effectively performed {len(actions)} actions",
                    "conditions": {
                        "agent": agent,
                        "action_count": len(actions),
                        "actions": actions[:3],  # Sample actions
                    },
                    "confidence": 0.8,
                }
                factors.append(factor)

        # Analyze timing
        duration = episode.get("duration", 0)
        if duration > 0:
            # Compare with similar past episodes
            similar_episodes = self._get_similar_past_episodes(
                episode["task_description"]
            )
            if similar_episodes:
                avg_duration = np.mean(
                    [e["duration_seconds"] for e in similar_episodes]
                )
                if duration < avg_duration * 0.8:
                    factor = {
                        "description": "Task completed faster than average",
                        "conditions": {
                            "duration": duration,
                            "average_duration": avg_duration,
                            "improvement": (avg_duration - duration) / avg_duration,
                        },
                        "confidence": 0.9,
                    }
                    factors.append(factor)

        return factors

    def _identify_failure_causes(self, episode: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify causes of failure."""
        causes = []

        # Check for common failure patterns
        error_info = episode.get("error", {})
        if error_info:
            cause = {
                "description": f"Error encountered: {error_info.get('type', 'Unknown')}",
                "conditions": {
                    "error_type": error_info.get("type"),
                    "error_message": error_info.get("message", "")[:100],
                },
                "confidence": 0.9,
            }
            causes.append(cause)

        # Check for missing contributions
        contributions = episode.get("agent_contributions", {})
        expected_agents = self._get_expected_agents_for_task(
            episode["task_description"]
        )

        missing_agents = set(expected_agents) - set(contributions.keys())
        if missing_agents:
            cause = {
                "description": f"Missing contributions from: {', '.join(missing_agents)}",
                "conditions": {
                    "missing_agents": list(missing_agents),
                    "participating_agents": list(contributions.keys()),
                },
                "confidence": 0.8,
            }
            causes.append(cause)

        return causes

    def synthesize_strategy(self, task_type: str) -> Optional[Dict[str, Any]]:
        """
        Synthesize an optimal strategy for a task type based on learnings.

        Args:
            task_type: Type of task to create strategy for

        Returns:
            Synthesized strategy or None
        """
        # Get successful patterns for this task type
        patterns = self.memory.get_successful_patterns(task_type=task_type)
        if len(patterns) < self.min_episodes_for_learning:
            self.logger.info(
                f"Insufficient data for strategy synthesis ({len(patterns)} patterns)"
            )
            return None

        # Get relevant learnings
        learnings = self.memory.get_relevant_learnings({"task_type": task_type})

        # Synthesize strategy
        strategy = {
            "task_type": task_type,
            "recommended_agents": [],
            "key_actions": [],
            "success_factors": [],
            "avoid": [],
            "estimated_duration": None,
            "confidence": 0.0,
        }

        # Identify best performing agents
        agent_scores = defaultdict(float)
        for pattern in patterns:
            agent_scores[pattern["agent"]] += pattern["total_successes"]

        top_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        strategy["recommended_agents"] = [agent for agent, _ in top_agents]

        # Extract key actions
        all_actions = defaultdict(int)
        for pattern in patterns:
            for action_data in pattern.get("top_actions", []):
                all_actions[action_data["action"]] += action_data["frequency"]

        top_actions = sorted(all_actions.items(), key=lambda x: x[1], reverse=True)[:5]
        strategy["key_actions"] = [action for action, _ in top_actions]

        # Extract success factors and things to avoid
        for learning in learnings:
            if "Success factor" in learning["insight"]:
                strategy["success_factors"].append(learning["insight"])
            elif "Failure cause" in learning["insight"]:
                strategy["avoid"].append(learning["insight"])

        # Estimate duration from recent successful episodes
        recent_episodes = self._get_recent_successful_episodes(task_type, days=30)
        if recent_episodes:
            durations = [
                e["duration_seconds"]
                for e in recent_episodes
                if e.get("duration_seconds")
            ]
            if durations:
                strategy["estimated_duration"] = int(np.median(durations))

        # Calculate confidence
        total_episodes = len(patterns) + len(recent_episodes)
        strategy["confidence"] = min(0.95, 0.5 + (total_episodes / 100))

        self.logger.info(
            f"Synthesized strategy for {task_type} with confidence {strategy['confidence']}"
        )
        return strategy

    def predict_success_probability(
        self, task_description: str, planned_approach: Dict[str, Any]
    ) -> float:
        """
        Predict the probability of success for a planned approach.

        Args:
            task_description: Description of the task
            planned_approach: Planned approach including agents and actions

        Returns:
            Probability of success (0-1)
        """
        task_type = self._categorize_task(task_description)

        # Get historical success rate for this task type
        recent_episodes = self._get_recent_episodes(task_type, days=90)
        if not recent_episodes:
            return 0.5  # No data, assume 50%

        base_success_rate = sum(1 for e in recent_episodes if e["success"]) / len(
            recent_episodes
        )

        # Adjust based on planned approach
        adjustment = 0.0

        # Check if using recommended agents
        strategy = self.synthesize_strategy(task_type)
        if strategy:
            planned_agents = set(planned_approach.get("agents", []))
            recommended_agents = set(strategy["recommended_agents"])

            if planned_agents & recommended_agents:
                adjustment += 0.1  # Using recommended agents

            # Check if avoiding known failure causes
            avoiding_failures = True
            for avoid_item in strategy["avoid"]:
                if avoid_item.lower() in str(planned_approach).lower():
                    avoiding_failures = False
                    break

            if avoiding_failures:
                adjustment += 0.05

        # Check team readiness (recent performance)
        recent_performance = self._get_team_recent_performance(days=7)
        if recent_performance > 0.8:
            adjustment += 0.05
        elif recent_performance < 0.5:
            adjustment -= 0.05

        # Calculate final probability
        probability = max(0.1, min(0.95, base_success_rate + adjustment))

        self.logger.info(f"Predicted success probability: {probability:.2f}")
        return probability

    def recommend_improvements(self, recent_episodes: int = 10) -> List[Dict[str, Any]]:
        """
        Recommend improvements based on recent performance.

        Args:
            recent_episodes: Number of recent episodes to analyze

        Returns:
            List of improvement recommendations
        """
        recommendations = []

        # Get recent episodes
        metrics = self.memory.get_performance_metrics(days_back=30)
        if not metrics:
            return recommendations

        # Check success rate trend
        if metrics.get("improvement_trend", 0) < 0:
            recommendations.append(
                {
                    "type": "performance",
                    "priority": "high",
                    "recommendation": "Success rate declining. Review recent failures and adjust strategies.",
                    "evidence": {
                        "current_success_rate": metrics.get("success_rate", 0),
                        "trend": metrics.get("improvement_trend", 0),
                    },
                }
            )

        # Check for slow tasks
        avg_duration = metrics.get("average_duration_seconds", 0)
        if avg_duration > 300:  # More than 5 minutes average
            recommendations.append(
                {
                    "type": "efficiency",
                    "priority": "medium",
                    "recommendation": "Average task duration is high. Consider parallelizing work or optimizing workflows.",
                    "evidence": {"average_duration": avg_duration},
                }
            )

        # Check for underutilized agents
        patterns = self.memory.get_successful_patterns()
        all_agents = self._get_all_team_agents()
        active_agents = {p["agent"] for p in patterns}
        inactive_agents = set(all_agents) - active_agents

        if inactive_agents:
            recommendations.append(
                {
                    "type": "utilization",
                    "priority": "low",
                    "recommendation": f'Agents not contributing to recent successes: {", ".join(inactive_agents)}. Consider task redistribution.',
                    "evidence": {"inactive_agents": list(inactive_agents)},
                }
            )

        self.logger.info(
            f"Generated {len(recommendations)} improvement recommendations"
        )
        return recommendations

    def _categorize_task(self, task_description: str) -> str:
        """Categorize task based on description."""
        task_lower = task_description.lower()

        categories = {
            "development": ["create", "build", "implement", "develop", "code"],
            "analysis": ["analyze", "investigate", "research", "study", "examine"],
            "debugging": ["fix", "debug", "resolve", "troubleshoot", "repair"],
            "design": ["design", "architect", "plan", "structure", "layout"],
            "documentation": ["document", "write", "describe", "explain"],
            "testing": ["test", "verify", "validate", "check", "ensure"],
            "deployment": ["deploy", "release", "launch", "publish"],
            "optimization": ["optimize", "improve", "enhance", "refactor"],
        }

        for category, keywords in categories.items():
            if any(keyword in task_lower for keyword in keywords):
                return category

        return "general"

    def _get_similar_past_episodes(self, task_description: str) -> List[Dict[str, Any]]:
        """Get similar past episodes from memory."""
        # This would use vector similarity in real implementation
        # For now, using simple category matching
        task_type = self._categorize_task(task_description)
        return self._get_recent_episodes(task_type, days=90)

    def _get_recent_episodes(self, task_type: str, days: int) -> List[Dict[str, Any]]:
        """Get recent episodes of a specific type."""
        if not self.memory.supabase:
            return []

        try:
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            # Get team_id
            team_result = (
                self.memory.supabase.table("teams")
                .select("id")
                .eq("name", self.team_name)
                .execute()
            )
            team_id = team_result.data[0]["id"] if team_result.data else None

            if not team_id:
                return []

            result = (
                self.memory.supabase.table("memory_entries")
                .select("*")
                .eq("team_id", team_id)
                .eq("entry_type", "experience")
                .gte("created_at", since_date)
                .execute()
            )

            # Filter by task type
            episodes = []
            for entry in result.data:
                content = json.loads(entry["content"])
                if (
                    self._categorize_task(content.get("task_description", ""))
                    == task_type
                ):
                    episodes.append(
                        {
                            "id": entry["id"],
                            "task_description": content.get("task_description"),
                            "success": content.get("success", False),
                            "duration_seconds": content.get("duration", 0),
                        }
                    )

            return episodes
        except:
            return []

    def _get_recent_successful_episodes(
        self, task_type: str, days: int
    ) -> List[Dict[str, Any]]:
        """Get recent successful episodes of a specific type."""
        episodes = self._get_recent_episodes(task_type, days)
        return [e for e in episodes if e.get("success", False)]

    def _get_expected_agents_for_task(self, task_description: str) -> List[str]:
        """Determine which agents should participate in a task."""
        # This would be more sophisticated in practice
        # For now, return a basic set based on task type
        task_type = self._categorize_task(task_description)

        agent_map = {
            "development": ["developer", "architect", "tester"],
            "analysis": ["analyst", "researcher", "strategist"],
            "debugging": ["developer", "tester", "analyst"],
            "design": ["designer", "architect", "strategist"],
            "documentation": ["writer", "analyst", "reviewer"],
            "testing": ["tester", "developer", "analyst"],
            "deployment": ["devops", "developer", "tester"],
            "optimization": ["developer", "analyst", "architect"],
        }

        return agent_map.get(task_type, ["manager", "analyst", "developer"])

    def _get_team_recent_performance(self, days: int) -> float:
        """Get team's recent performance rate."""
        metrics = self.memory.get_performance_metrics(days_back=days)
        return metrics.get("success_rate", 0.5)

    def _get_all_team_agents(self) -> List[str]:
        """Get all agents in the team."""
        # This would query the team registry in practice
        # For now, return a placeholder
        return ["manager", "developer", "analyst", "tester", "designer"]
