"""
Prompt Evolution System - Dynamic Agent Enhancement through Learned Patterns

This module enables agents to evolve their prompts based on successful patterns
discovered through the memory and learning systems.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from supabase import Client

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PromptEvolution:
    """Manages the evolution of agent prompts based on learned patterns."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure agent_evolutions table exists."""
        # Table creation handled by SQL migrations
        pass

    def get_evolved_prompt(
        self,
        team_id: str,
        agent_role: str,
        base_prompt: str,
        task_type: Optional[str] = None,
    ) -> str:
        """
        Get an evolved prompt for an agent, incorporating learned strategies.

        Args:
            team_id: The team this agent belongs to
            agent_role: The role of the agent (e.g., 'developer', 'analyst')
            base_prompt: The original base prompt
            task_type: Optional task type for context-specific enhancements

        Returns:
            The evolved prompt with learned strategies appended
        """
        try:
            # Get the latest evolution for this agent
            result = (
                self.supabase.table("agent_evolutions")
                .select("evolved_version, confidence_score")
                .eq("team_id", team_id)
                .eq("agent_role", agent_role)
                .eq("evolution_type", "prompt")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                evolution = result.data[0]
                if evolution["confidence_score"] >= 0.9:
                    logger.info(
                        f"Using evolved prompt for {agent_role} (confidence: {evolution['confidence_score']})"
                    )
                    return evolution["evolved_version"]

            # Get learned strategies from team memory
            strategies = self._get_proven_strategies(team_id, agent_role, task_type)

            if strategies:
                evolved_prompt = self._enhance_prompt_with_strategies(
                    base_prompt, strategies
                )

                # Store the evolution
                self._store_evolution(
                    team_id=team_id,
                    agent_role=agent_role,
                    original=base_prompt,
                    evolved=evolved_prompt,
                    confidence=self._calculate_confidence(strategies),
                )

                return evolved_prompt

            return base_prompt

        except Exception as e:
            logger.error(f"Error getting evolved prompt: {e}")
            return base_prompt

    def _get_proven_strategies(
        self, team_id: str, agent_role: str, task_type: Optional[str] = None
    ) -> List[Dict]:
        """Get proven strategies from team learnings."""
        try:
            # Query learnings for successful patterns
            query = (
                self.supabase.table("team_learnings")
                .select("pattern, success_rate, usage_count, context")
                .eq("team_id", team_id)
                .gte("confidence_score", 0.8)
                .gte("success_rate", 0.85)
            )

            # Filter by role if needed
            if agent_role:
                query = query.contains("context", {"role": agent_role})

            # Filter by task type if provided
            if task_type:
                query = query.contains("context", {"task_type": task_type})

            result = query.order("success_rate", desc=True).limit(5).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting proven strategies: {e}")
            return []

    def _enhance_prompt_with_strategies(
        self, base_prompt: str, strategies: List[Dict]
    ) -> str:
        """Enhance a prompt with learned strategies."""
        if not strategies:
            return base_prompt

        # Build strategy section
        strategy_text = "\n\nBased on experience and proven patterns:"

        for strategy in strategies:
            pattern = strategy["pattern"]
            success_rate = strategy["success_rate"] * 100
            usage_count = strategy["usage_count"]

            # Extract actionable insight from pattern
            if "action" in strategy.get("context", {}):
                action = strategy["context"]["action"]
                strategy_text += f"\n- {action} ({success_rate:.0f}% success rate, used {usage_count} times)"
            else:
                strategy_text += f"\n- {pattern} ({success_rate:.0f}% success rate)"

        # Add general guidance
        strategy_text += "\n\nPrioritize these proven approaches when applicable."

        return base_prompt + strategy_text

    def _calculate_confidence(self, strategies: List[Dict]) -> float:
        """Calculate confidence score for evolved prompt."""
        if not strategies:
            return 0.0

        # Weighted average based on success rate and usage count
        total_weight = 0
        weighted_score = 0

        for strategy in strategies:
            weight = strategy["usage_count"] * strategy["success_rate"]
            weighted_score += strategy["success_rate"] * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _store_evolution(
        self,
        team_id: str,
        agent_role: str,
        original: str,
        evolved: str,
        confidence: float,
    ):
        """Store an agent evolution in the database."""
        try:
            self.supabase.table("agent_evolutions").insert(
                {
                    "id": str(uuid4()),
                    "team_id": team_id,
                    "agent_role": agent_role,
                    "evolution_type": "prompt",
                    "original_version": original,
                    "evolved_version": evolved,
                    "confidence_score": confidence,
                    "performance_delta": 0.0,  # Will be calculated after A/B testing
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            logger.info(
                f"Stored prompt evolution for {agent_role} (confidence: {confidence:.2f})"
            )

        except Exception as e:
            logger.error(f"Error storing evolution: {e}")

    def evolve_workflow(
        self, team_id: str, workflow_definition: Dict, learnings: List[Dict]
    ) -> Tuple[Dict, float]:
        """
        Evolve a workflow based on learned patterns.

        Args:
            team_id: The team ID
            workflow_definition: Current workflow definition
            learnings: Relevant learnings for this workflow

        Returns:
            Tuple of (evolved_workflow, confidence_score)
        """
        evolved_workflow = workflow_definition.copy()
        modifications = []

        for learning in learnings:
            if learning["confidence_score"] >= 0.9:
                pattern = learning["pattern"]

                # Add validation step if errors are common
                if "validation_prevents_errors" in pattern:
                    if "validate" not in evolved_workflow.get("nodes", []):
                        evolved_workflow.setdefault("nodes", []).append(
                            {
                                "id": "validate_before_execute",
                                "type": "validation",
                                "config": {"strict": True, "fail_fast": False},
                            }
                        )
                        modifications.append("Added validation step")

                # Add review step if quality issues detected
                if "review_improves_quality" in pattern:
                    if "review" not in evolved_workflow.get("nodes", []):
                        evolved_workflow.setdefault("nodes", []).append(
                            {
                                "id": "quality_review",
                                "type": "review",
                                "config": {
                                    "criteria": learning.get("context", {}).get(
                                        "criteria", []
                                    )
                                },
                            }
                        )
                        modifications.append("Added quality review step")

        confidence = len(modifications) / max(len(learnings), 1) if learnings else 0.0

        if modifications:
            # Store workflow evolution
            self.supabase.table("agent_evolutions").insert(
                {
                    "id": str(uuid4()),
                    "team_id": team_id,
                    "agent_role": "team_workflow",
                    "evolution_type": "workflow",
                    "original_version": json.dumps(workflow_definition),
                    "evolved_version": json.dumps(evolved_workflow),
                    "confidence_score": confidence,
                    "performance_delta": 0.0,
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            logger.info(f"Evolved workflow with {len(modifications)} modifications")

        return evolved_workflow, confidence

    def get_evolution_history(
        self, team_id: str, agent_role: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """Get evolution history for a team or specific agent."""
        try:
            query = (
                self.supabase.table("agent_evolutions")
                .select("*")
                .eq("team_id", team_id)
            )

            if agent_role:
                query = query.eq("agent_role", agent_role)

            result = query.order("created_at", desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting evolution history: {e}")
            return []

    def rollback_evolution(self, evolution_id: str) -> bool:
        """
        Rollback to a previous evolution version.

        Args:
            evolution_id: The ID of the evolution to rollback to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the evolution
            result = (
                self.supabase.table("agent_evolutions")
                .select("*")
                .eq("id", evolution_id)
                .execute()
            )

            if not result.data:
                logger.error(f"Evolution {evolution_id} not found")
                return False

            evolution = result.data[0]

            # Create a new evolution that reverts to the original
            self.supabase.table("agent_evolutions").insert(
                {
                    "id": str(uuid4()),
                    "team_id": evolution["team_id"],
                    "agent_role": evolution["agent_role"],
                    "evolution_type": evolution["evolution_type"],
                    "original_version": evolution[
                        "evolved_version"
                    ],  # Current becomes original
                    "evolved_version": evolution[
                        "original_version"
                    ],  # Revert to original
                    "confidence_score": 1.0,  # High confidence in rollback
                    "performance_delta": -evolution.get("performance_delta", 0),
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()

            logger.info(f"Rolled back evolution for {evolution['agent_role']}")
            return True

        except Exception as e:
            logger.error(f"Error rolling back evolution: {e}")
            return False

    def measure_evolution_impact(
        self, evolution_id: str, performance_metrics: Dict[str, float]
    ) -> float:
        """
        Measure the impact of an evolution on performance.

        Args:
            evolution_id: The evolution to measure
            performance_metrics: Dict of metric_name -> value

        Returns:
            Performance delta as a percentage
        """
        try:
            # This would typically compare against baseline metrics
            # For now, we'll calculate a simple average improvement
            baseline = 0.7  # Baseline performance assumption
            current = sum(performance_metrics.values()) / len(performance_metrics)
            delta = (current - baseline) / baseline

            # Update the evolution record
            self.supabase.table("agent_evolutions").update(
                {"performance_delta": delta}
            ).eq("id", evolution_id).execute()

            logger.info(f"Evolution {evolution_id} impact: {delta:.2%}")
            return delta

        except Exception as e:
            logger.error(f"Error measuring evolution impact: {e}")
            return 0.0
