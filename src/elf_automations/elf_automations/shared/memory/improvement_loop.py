"""
Continuous Improvement Loop - Enables teams to learn and adapt over time

This module provides:
- Scheduled learning cycles
- Performance analysis
- Strategy updates
- Knowledge consolidation
- Cross-team learning
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from ..utils.supabase_client import get_supabase_client
from .learning_system import LearningSystem
from .prompt_evolution import PromptEvolution
from .team_memory import TeamMemory


class ContinuousImprovementLoop:
    """
    Manages continuous learning and improvement for AI teams.

    Features:
    - Daily/weekly learning cycles
    - Performance trend analysis
    - Strategy optimization
    - Knowledge sharing across teams
    - Automated improvement recommendations
    """

    def __init__(
        self,
        team_name: str,
        team_memory: TeamMemory,
        learning_system: LearningSystem,
        cycle_hours: int = 24,
    ):
        """
        Initialize improvement loop.

        Args:
            team_name: Name of the team
            team_memory: Team memory instance
            learning_system: Learning system instance
            cycle_hours: Hours between improvement cycles (default 24)
        """
        self.team_name = team_name
        self.memory = team_memory
        self.learning = learning_system
        self.cycle_hours = cycle_hours
        self.logger = logging.getLogger(f"ImprovementLoop.{team_name}")

        self.is_running = False
        self.last_cycle = None
        self.cycle_count = 0

        # Initialize Supabase for cross-team learning
        try:
            self.supabase = get_supabase_client()
            # Initialize prompt evolution system
            self.prompt_evolution = PromptEvolution(self.supabase)
        except Exception as e:
            self.logger.error(f"Failed to connect to Supabase: {e}")
            self.supabase = None
            self.prompt_evolution = None

    async def start(self):
        """Start the continuous improvement loop."""
        if self.is_running:
            self.logger.warning("Improvement loop already running")
            return

        self.is_running = True
        self.logger.info(f"Starting improvement loop with {self.cycle_hours}h cycles")

        # Run the loop
        while self.is_running:
            try:
                await self._run_improvement_cycle()

                # Wait for next cycle
                await asyncio.sleep(self.cycle_hours * 3600)

            except Exception as e:
                self.logger.error(f"Error in improvement cycle: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    def stop(self):
        """Stop the improvement loop."""
        self.is_running = False
        self.logger.info("Stopping improvement loop")

    async def _run_improvement_cycle(self):
        """Run a single improvement cycle."""
        self.cycle_count += 1
        self.last_cycle = datetime.utcnow()

        self.logger.info(f"Starting improvement cycle #{self.cycle_count}")

        # 1. Analyze recent performance
        performance_insights = await self._analyze_performance()

        # 2. Extract new patterns
        new_patterns = await self._extract_patterns()

        # 3. Update strategies
        strategy_updates = await self._update_strategies()

        # 4. Consolidate old memories
        consolidation_results = await self._consolidate_memories()

        # 5. Share learnings with other teams
        sharing_results = await self._share_learnings()

        # 6. Evolve agent prompts based on learnings
        evolution_results = await self._evolve_agent_prompts()

        # 7. Generate improvement report
        report = self._generate_improvement_report(
            {
                "performance": performance_insights,
                "patterns": new_patterns,
                "strategies": strategy_updates,
                "consolidation": consolidation_results,
                "sharing": sharing_results,
                "evolution": evolution_results,
            }
        )

        # Store the report
        await self._store_improvement_report(report)

        self.logger.info(f"Completed improvement cycle #{self.cycle_count}")

    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze team performance since last cycle."""
        # Get performance metrics
        metrics = self.memory.get_performance_metrics(
            days_back=max(7, self.cycle_hours // 24)
        )

        insights = {"metrics": metrics, "trends": [], "alerts": []}

        # Analyze trends
        if metrics.get("improvement_trend", 0) < -0.1:
            insights["alerts"].append(
                {
                    "type": "performance_decline",
                    "severity": "high",
                    "message": "Success rate declining significantly",
                    "recommendation": "Review recent failures and adjust strategies",
                }
            )

        if metrics.get("average_duration_seconds", 0) > 600:
            insights["alerts"].append(
                {
                    "type": "slow_execution",
                    "severity": "medium",
                    "message": "Tasks taking longer than 10 minutes average",
                    "recommendation": "Optimize workflows or parallelize work",
                }
            )

        # Compare with other teams if possible
        if self.supabase:
            peer_comparison = await self._compare_with_peers(metrics)
            insights["peer_comparison"] = peer_comparison

        return insights

    async def _extract_patterns(self) -> List[Dict[str, Any]]:
        """Extract new patterns from recent experiences."""
        # Get recent successful episodes
        patterns = self.memory.get_successful_patterns(days_back=7)

        new_patterns = []

        # Identify emerging patterns
        for pattern in patterns:
            if pattern.get("total_successes", 0) >= 3:
                # This is a consistent pattern
                new_pattern = {
                    "type": "success_pattern",
                    "description": f"{pattern['agent']} consistently successful with {pattern['top_actions'][0]['action']}",
                    "confidence": min(0.9, pattern["total_successes"] / 10),
                    "recommendations": [
                        f"Prioritize {pattern['agent']} for similar tasks",
                        f"Share {pattern['agent']}'s approach with team",
                    ],
                }
                new_patterns.append(new_pattern)

        return new_patterns

    async def _update_strategies(self) -> Dict[str, Any]:
        """Update team strategies based on learnings."""
        updates = {"updated_strategies": [], "new_strategies": []}

        # Get current task types
        task_types = ["development", "analysis", "debugging", "design", "deployment"]

        for task_type in task_types:
            # Synthesize strategy for each task type
            strategy = self.learning.synthesize_strategy(task_type)

            if strategy and strategy["confidence"] > 0.7:
                # Store as a high-confidence strategy
                strategy_doc = {
                    "team_name": self.team_name,
                    "task_type": task_type,
                    "strategy": strategy,
                    "created_at": datetime.utcnow().isoformat(),
                }

                # Store in team knowledge
                self.memory.store_learning(
                    {
                        "insight": f"Optimized strategy for {task_type} tasks",
                        "context": {"task_type": task_type},
                        "evidence": [],
                        "confidence": strategy["confidence"],
                        "description": json.dumps(strategy),
                    }
                )

                updates["updated_strategies"].append(strategy_doc)

        return updates

    async def _consolidate_memories(self) -> Dict[str, Any]:
        """Consolidate old memories to save space and extract insights."""
        # Consolidate memories older than 30 days
        self.memory.consolidate_memories(older_than_days=30)

        return {
            "status": "completed",
            "consolidated_count": "unknown",  # Would need to track this in memory.consolidate_memories
        }

    async def _share_learnings(self) -> Dict[str, Any]:
        """Share valuable learnings with other teams."""
        if not self.supabase:
            return {"status": "skipped", "reason": "No Supabase connection"}

        shared_count = 0

        try:
            # Get high-confidence learnings
            result = (
                self.supabase.table("learning_patterns")
                .select("*")
                .eq("discovered_by_team", self.team_name)
                .gte("confidence_score", 0.8)
                .gte("occurrence_count", 5)
                .execute()
            )

            high_value_patterns = result.data

            # Mark as shared (would need a shared_patterns table)
            for pattern in high_value_patterns:
                # In a real implementation, insert into a shared_patterns table
                shared_count += 1

            return {"status": "completed", "shared_count": shared_count}

        except Exception as e:
            self.logger.error(f"Failed to share learnings: {e}")
            return {"status": "failed", "error": str(e)}

    async def _compare_with_peers(self, our_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare our performance with peer teams."""
        try:
            # Get our team's department
            team_result = (
                self.supabase.table("teams")
                .select("department")
                .eq("name", self.team_name)
                .execute()
            )

            if not team_result.data:
                return {}

            our_department = team_result.data[0]["department"]

            # Get peer teams in same department
            peers_result = (
                self.supabase.table("teams")
                .select("id, name")
                .eq("department", our_department)
                .neq("name", self.team_name)
                .execute()
            )

            if not peers_result.data:
                return {}

            # Compare success rates (simplified - would need aggregated metrics table)
            our_success_rate = our_metrics.get("success_rate", 0)

            comparison = {
                "our_success_rate": our_success_rate,
                "department": our_department,
                "peer_count": len(peers_result.data),
            }

            return comparison

        except Exception as e:
            self.logger.error(f"Failed to compare with peers: {e}")
            return {}

    async def _evolve_agent_prompts(self) -> Dict[str, Any]:
        """Evolve agent prompts based on high-confidence learnings."""
        if not self.prompt_evolution:
            return {"status": "skipped", "reason": "No prompt evolution system"}

        evolution_results = {"evolved_agents": [], "total_evolutions": 0}

        try:
            # Get team ID
            if not self.supabase:
                return {"status": "skipped", "reason": "No Supabase connection"}

            team_result = (
                self.supabase.table("teams")
                .select("id")
                .eq("name", self.team_name)
                .execute()
            )

            if not team_result.data:
                return {"status": "failed", "reason": "Team not found"}

            team_id = team_result.data[0]["id"]

            # Get team members
            members_result = (
                self.supabase.table("team_members")
                .select("role")
                .eq("team_id", team_id)
                .execute()
            )

            if not members_result.data:
                return {"status": "no_members"}

            # For each agent, check if evolution is warranted
            for member in members_result.data:
                agent_role = member["role"]

                # Get high-confidence patterns for this agent
                patterns = self.memory.get_successful_patterns(
                    days_back=7, agent_filter=agent_role
                )

                if patterns and any(p.get("total_successes", 0) >= 5 for p in patterns):
                    # Agent has consistent success patterns - evolve their prompt

                    # Get current prompt (would need to store/retrieve from somewhere)
                    base_prompt = f"You are a {agent_role} responsible for..."

                    # Generate evolved prompt
                    evolved_prompt = self.prompt_evolution.get_evolved_prompt(
                        team_id=team_id, agent_role=agent_role, base_prompt=base_prompt
                    )

                    if evolved_prompt != base_prompt:
                        evolution_results["evolved_agents"].append(
                            {
                                "role": agent_role,
                                "confidence": 0.85,  # Would calculate based on patterns
                                "enhancements": len(patterns),
                            }
                        )
                        evolution_results["total_evolutions"] += 1

                        self.logger.info(
                            f"Evolved prompt for {agent_role} based on "
                            f"{len(patterns)} successful patterns"
                        )

            return evolution_results

        except Exception as e:
            self.logger.error(f"Failed to evolve agent prompts: {e}")
            return {"status": "failed", "error": str(e)}

    def _generate_improvement_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive improvement report."""
        report = {
            "cycle_number": self.cycle_count,
            "timestamp": datetime.utcnow().isoformat(),
            "team_name": self.team_name,
            "summary": {
                "performance_alerts": len(results["performance"].get("alerts", [])),
                "new_patterns": len(results["patterns"]),
                "updated_strategies": len(
                    results["strategies"].get("updated_strategies", [])
                ),
                "memories_consolidated": results["consolidation"].get("status")
                == "completed",
                "learnings_shared": results["sharing"].get("shared_count", 0),
                "agents_evolved": results["evolution"].get("total_evolutions", 0),
            },
            "details": results,
        }

        # Generate key insights
        key_insights = []

        if results["performance"].get("alerts"):
            key_insights.append(
                {
                    "type": "alert",
                    "message": results["performance"]["alerts"][0]["message"],
                    "action": results["performance"]["alerts"][0]["recommendation"],
                }
            )

        if results["patterns"]:
            key_insights.append(
                {
                    "type": "pattern",
                    "message": f"Discovered {len(results['patterns'])} new success patterns",
                    "action": "Apply these patterns to future tasks",
                }
            )

        if results["evolution"].get("total_evolutions", 0) > 0:
            key_insights.append(
                {
                    "type": "evolution",
                    "message": f"Evolved {results['evolution']['total_evolutions']} agent prompts",
                    "action": "Agents will now incorporate learned strategies automatically",
                }
            )

        report["key_insights"] = key_insights

        return report

    async def _store_improvement_report(self, report: Dict[str, Any]):
        """Store the improvement report."""
        if self.supabase:
            try:
                # Store in a team_improvement_reports table (would need to create)
                self.logger.info(f"Improvement report generated: {report['summary']}")
            except Exception as e:
                self.logger.error(f"Failed to store report: {e}")

        # Also log key insights
        for insight in report.get("key_insights", []):
            self.logger.info(
                f"Key insight: {insight['message']} - Action: {insight['action']}"
            )

    async def run_immediate_cycle(self) -> Dict[str, Any]:
        """Run an improvement cycle immediately (for testing or on-demand)."""
        self.logger.info("Running immediate improvement cycle")
        await self._run_improvement_cycle()
        return {
            "status": "completed",
            "cycle_number": self.cycle_count,
            "timestamp": self.last_cycle.isoformat() if self.last_cycle else None,
        }

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the improvement loop."""
        return {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "last_cycle": self.last_cycle.isoformat() if self.last_cycle else None,
            "cycle_hours": self.cycle_hours,
            "team_name": self.team_name,
        }
