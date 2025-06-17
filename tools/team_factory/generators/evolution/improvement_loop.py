"""
Improvement loop generator for team evolution.
"""

import logging
from pathlib import Path
from typing import Any, Dict

from ...models import TeamSpecification


class ImprovementLoopGenerator:
    """Generates improvement loop configuration and scripts for teams."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate(self, spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate improvement loop setup for the team.

        Returns:
            Dict with results including generated files
        """
        results = {"success": True, "generated_files": [], "errors": []}

        if not spec.enable_evolution:
            self.logger.info(
                f"Evolution disabled for {spec.name}, skipping improvement loop"
            )
            return results

        team_dir = Path(spec.name)

        # Create evolution directory
        evolution_dir = team_dir / "evolution"
        evolution_dir.mkdir(exist_ok=True)

        # Generate improvement loop script
        loop_script = self._generate_improvement_loop_script(spec)
        script_file = evolution_dir / "run_improvement_loop.py"
        with open(script_file, "w") as f:
            f.write(loop_script)
        results["generated_files"].append(str(script_file))

        # Generate evolution config
        config = self._generate_evolution_config(spec)
        config_file = evolution_dir / "evolution_config.yaml"
        with open(config_file, "w") as f:
            f.write(config)
        results["generated_files"].append(str(config_file))

        # Generate cron job setup (for automated cycles)
        if spec.improvement_cycle_frequency != "manual":
            cron_script = self._generate_cron_script(spec)
            cron_file = evolution_dir / "setup_cron.sh"
            with open(cron_file, "w") as f:
                f.write(cron_script)
            # Make executable
            cron_file.chmod(0o755)
            results["generated_files"].append(str(cron_file))

        return results

    def _generate_improvement_loop_script(self, spec: TeamSpecification) -> str:
        """Generate the improvement loop execution script."""
        return f'''#!/usr/bin/env python3
"""
Improvement Loop for {spec.name}

This script runs the team improvement cycle:
1. Analyzes team performance from conversation logs
2. Identifies successful patterns
3. Generates evolved prompts with high-confidence improvements
4. Tests evolved agents against base versions
5. Applies successful evolutions
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from elf_automations.shared.memory import (
    ImprovementLoop, PromptEvolution, EvolutionABTesting,
    LearningSystem, TeamMemory
)
from elf_automations.shared.utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_improvement_cycle():
    """Run a complete improvement cycle for the team."""
    logger.info("Starting improvement cycle for {spec.name}")

    try:
        # Initialize components
        supabase = get_supabase_client()
        team_id = "{spec.name}"

        # Initialize improvement loop
        improvement_loop = ImprovementLoop(
            supabase=supabase,
            improvement_frequency="{spec.improvement_cycle_frequency}"
        )

        # Initialize learning system
        learning_system = LearningSystem(supabase)

        # Initialize team memory
        team_memory = TeamMemory(
            team_id=team_id,
            supabase_client=supabase,
            retention_days={spec.memory_retention_days}
        )

        # Run improvement cycle
        logger.info("Analyzing team performance...")
        results = improvement_loop.run_improvement_cycle(team_id)

        # Log results
        logger.info(f"Improvement cycle completed:")
        logger.info(f"  - Episodes analyzed: {{results.get('episodes_analyzed', 0)}}")
        logger.info(f"  - Patterns identified: {{results.get('patterns_found', 0)}}")
        logger.info(f"  - Agents evolved: {{len(results.get('evolved_agents', []))}}")
        logger.info(f"  - Success rate improvement: {{results.get('avg_improvement', 0):.1%}}")

        # Generate evolution report
        if results.get('evolved_agents'):
            report = improvement_loop.generate_improvement_report(team_id)

            # Save report
            report_dir = Path("evolution/reports")
            report_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"improvement_report_{{timestamp}}.md"

            with open(report_file, "w") as f:
                f.write(report)

            logger.info(f"Improvement report saved to {{report_file}}")

        # Clean up old memories if needed
        if team_memory.retention_days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=team_memory.retention_days)
            logger.info(f"Cleaning memories older than {{cutoff_date}}")
            team_memory.cleanup_old_memories(cutoff_date)

        return results

    except Exception as e:
        logger.error(f"Error in improvement cycle: {{e}}", exc_info=True)
        return {{"error": str(e)}}


def test_evolution(agent_role: str):
    """
    Run A/B test for a specific agent role.

    Args:
        agent_role: Role of the agent to test
    """
    logger.info(f"Running A/B test for {{agent_role}}")

    try:
        supabase = get_supabase_client()
        ab_testing = EvolutionABTesting(supabase)

        # Get latest evolution for this role
        evolution_result = supabase.table('agent_evolutions').select("*").eq(
            'team_id', '{spec.name}'
        ).eq('agent_role', agent_role).eq('applied_at', None).order(
            'created_at', desc=True
        ).limit(1).execute()

        if not evolution_result.data:
            logger.info(f"No pending evolutions for {{agent_role}}")
            return

        evolution = evolution_result.data[0]

        # Create A/B test
        test_id = ab_testing.create_ab_test(
            team_id='{spec.name}',
            agent_role=agent_role,
            evolution_id=evolution['id'],
            test_duration_hours=24,
            min_episodes=20
        )

        logger.info(f"Created A/B test {{test_id}} for {{agent_role}}")

        # The test will run automatically as the team operates
        # Results will be analyzed by the next improvement cycle

    except Exception as e:
        logger.error(f"Error in A/B test: {{e}}", exc_info=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test evolution for specific role
        if len(sys.argv) > 2:
            test_evolution(sys.argv[2])
        else:
            print("Usage: python run_improvement_loop.py test <agent_role>")
    else:
        # Run full improvement cycle
        results = run_improvement_cycle()

        # Exit with error code if cycle failed
        if "error" in results:
            sys.exit(1)
'''

    def _generate_evolution_config(self, spec: TeamSpecification) -> str:
        """Generate evolution configuration."""
        return f"""# Evolution Configuration for {spec.name}

team:
  name: {spec.name}
  id: {spec.name}
  department: {spec.department}

evolution:
  enabled: {spec.enable_evolution}
  confidence_threshold: {spec.evolution_confidence_threshold}
  improvement_frequency: {spec.improvement_cycle_frequency}

memory:
  enabled: {spec.enable_memory}
  retention_days: {spec.memory_retention_days}

conversation_logging:
  enabled: {spec.enable_conversation_logging}

# Agent roles to evolve
agents:
"""
        # Add agent roles
        for member in spec.members:
            config += f"""  - role: {member.role}
    name: {member.name}
    can_evolve: true
    evolution_types:
      - prompt
      - strategies
      - tool_preferences
"""

        config += """
# Evolution constraints
constraints:
  max_prompt_length: 2000
  min_success_episodes: 10
  max_evolution_rate: 0.2  # Max 20% change per cycle

# A/B testing settings
ab_testing:
  enabled: true
  min_test_duration_hours: 24
  min_episodes_per_variant: 20
  confidence_level: 0.95
"""
        return config

    def _generate_cron_script(self, spec: TeamSpecification) -> str:
        """Generate cron setup script."""
        # Determine cron schedule
        if spec.improvement_cycle_frequency == "daily":
            schedule = "0 2 * * *"  # 2 AM daily
        elif spec.improvement_cycle_frequency == "weekly":
            schedule = "0 2 * * 0"  # 2 AM on Sundays
        else:
            schedule = "0 2 * * *"  # Default to daily

        return f"""#!/bin/bash
# Setup cron job for team improvement loop

# Get the directory of this script
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"

# Create log directory
mkdir -p "$DIR/logs"

# Add cron job
(crontab -l 2>/dev/null; echo "{schedule} cd $DIR && /usr/bin/python3 run_improvement_loop.py >> logs/improvement_loop.log 2>&1") | crontab -

echo "Cron job scheduled for {spec.improvement_cycle_frequency} improvement cycles"
echo "Schedule: {schedule}"
echo "Logs will be written to: $DIR/logs/improvement_loop.log"

# To remove the cron job, run:
# crontab -l | grep -v "run_improvement_loop.py" | crontab -
"""
