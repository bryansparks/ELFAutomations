#!/usr/bin/env python3
"""
Improvement Loop for general-team

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
    logger.info("Starting improvement cycle for general-team")
    
    try:
        # Initialize components
        supabase = get_supabase_client()
        team_id = "general-team"
        
        # Initialize improvement loop
        improvement_loop = ImprovementLoop(
            supabase=supabase,
            improvement_frequency="daily"
        )
        
        # Initialize learning system
        learning_system = LearningSystem(supabase)
        
        # Initialize team memory
        team_memory = TeamMemory(
            team_id=team_id,
            supabase_client=supabase,
            retention_days=30
        )
        
        # Run improvement cycle
        logger.info("Analyzing team performance...")
        results = improvement_loop.run_improvement_cycle(team_id)
        
        # Log results
        logger.info(f"Improvement cycle completed:")
        logger.info(f"  - Episodes analyzed: {results.get('episodes_analyzed', 0)}")
        logger.info(f"  - Patterns identified: {results.get('patterns_found', 0)}")
        logger.info(f"  - Agents evolved: {len(results.get('evolved_agents', []))}")
        logger.info(f"  - Success rate improvement: {results.get('avg_improvement', 0):.1%}")
        
        # Generate evolution report
        if results.get('evolved_agents'):
            report = improvement_loop.generate_improvement_report(team_id)
            
            # Save report
            report_dir = Path("evolution/reports")
            report_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"improvement_report_{timestamp}.md"
            
            with open(report_file, "w") as f:
                f.write(report)
            
            logger.info(f"Improvement report saved to {report_file}")
        
        # Clean up old memories if needed
        if team_memory.retention_days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=team_memory.retention_days)
            logger.info(f"Cleaning memories older than {cutoff_date}")
            team_memory.cleanup_old_memories(cutoff_date)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in improvement cycle: {e}", exc_info=True)
        return {"error": str(e)}


def test_evolution(agent_role: str):
    """
    Run A/B test for a specific agent role.
    
    Args:
        agent_role: Role of the agent to test
    """
    logger.info(f"Running A/B test for {agent_role}")
    
    try:
        supabase = get_supabase_client()
        ab_testing = EvolutionABTesting(supabase)
        
        # Get latest evolution for this role
        evolution_result = supabase.table('agent_evolutions').select("*").eq(
            'team_id', 'general-team'
        ).eq('agent_role', agent_role).eq('applied_at', None).order(
            'created_at', desc=True
        ).limit(1).execute()
        
        if not evolution_result.data:
            logger.info(f"No pending evolutions for {agent_role}")
            return
        
        evolution = evolution_result.data[0]
        
        # Create A/B test
        test_id = ab_testing.create_ab_test(
            team_id='general-team',
            agent_role=agent_role,
            evolution_id=evolution['id'],
            test_duration_hours=24,
            min_episodes=20
        )
        
        logger.info(f"Created A/B test {test_id} for {agent_role}")
        
        # The test will run automatically as the team operates
        # Results will be analyzed by the next improvement cycle
        
    except Exception as e:
        logger.error(f"Error in A/B test: {e}", exc_info=True)


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
