#!/usr/bin/env python3
"""
Test Agent Evolution System

This script demonstrates:
1. Creating an agent with base prompt
2. Recording successful patterns
3. Triggering prompt evolution
4. A/B testing evolved vs base agent
5. Viewing evolution results
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.memory import (
    TeamMemory, 
    LearningSystem,
    ContinuousImprovementLoop,
    PromptEvolution,
    EvolvedAgentLoader,
    EvolutionABTesting
)
from elf_automations.shared.utils.supabase_client import get_supabase_client
from elf_automations.shared.utils.logging import get_logger

logger = get_logger(__name__)


async def simulate_successful_patterns(team_memory: TeamMemory, agent_role: str):
    """Simulate successful task patterns for an agent."""
    
    patterns = [
        {
            'action': 'Always validate input parameters first',
            'context': {'task_type': 'data_processing', 'error_prevention': True},
            'success_count': 45,
            'failure_count': 2
        },
        {
            'action': 'Use caching for repeated API calls',
            'context': {'task_type': 'api_integration', 'performance': True},
            'success_count': 38,
            'failure_count': 1
        },
        {
            'action': 'Implement retry logic with exponential backoff',
            'context': {'task_type': 'network_operations', 'reliability': True},
            'success_count': 52,
            'failure_count': 3
        },
        {
            'action': 'Log detailed context before critical operations',
            'context': {'task_type': 'debugging', 'observability': True},
            'success_count': 41,
            'failure_count': 0
        },
        {
            'action': 'Batch database operations for efficiency',
            'context': {'task_type': 'database', 'performance': True},
            'success_count': 33,
            'failure_count': 2
        }
    ]
    
    # Store patterns as successful episodes
    for pattern in patterns:
        for i in range(pattern['success_count']):
            episode_data = {
                'task': f"Task using pattern: {pattern['action']}",
                'agent': agent_role,
                'actions': [pattern['action']],
                'outcome': 'success',
                'context': pattern['context'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await team_memory.store_episode(
                episode_id=str(uuid4()),
                episode_data=episode_data,
                embeddings={'task': [0.1] * 384}  # Mock embedding
            )
    
    logger.info(f"Simulated {sum(p['success_count'] for p in patterns)} successful patterns")


async def main():
    """Run agent evolution demonstration."""
    
    print("=== Agent Evolution System Demo ===\n")
    
    # Initialize systems
    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        print("\nPlease ensure Supabase is configured with proper credentials.")
        return
    
    # Test configuration
    team_name = "evolution-test-team"
    team_id = str(uuid4())
    agent_role = "data_analyst"
    
    print(f"Team: {team_name}")
    print(f"Agent Role: {agent_role}\n")
    
    # Initialize memory systems
    team_memory = TeamMemory(
        team_name=team_name,
        collection_name=f"{team_name}_memory"
    )
    
    learning_system = LearningSystem(
        team_name=team_name,
        memory=team_memory
    )
    
    # 1. Create base agent configuration
    base_config = {
        'role': agent_role,
        'goal': 'Analyze data and provide insights',
        'backstory': """You are a data analyst responsible for processing and analyzing data.
Focus on accuracy and clarity in your analysis.""",
        'personality_traits': {
            'detail-oriented': 'Pay attention to data quality and edge cases'
        }
    }
    
    print("1. Base Agent Configuration:")
    print(f"   Role: {base_config['role']}")
    print(f"   Prompt: {base_config['backstory'][:100]}...")
    print()
    
    # 2. Simulate successful patterns
    print("2. Simulating successful task patterns...")
    await simulate_successful_patterns(team_memory, agent_role)
    
    # Extract patterns to learnings
    patterns = team_memory.get_successful_patterns(days_back=1)
    for pattern in patterns[:3]:
        if pattern.get('total_successes', 0) >= 30:
            learning = {
                'insight': f"Effective pattern: {pattern['top_actions'][0]['action']}",
                'confidence': min(0.95, pattern['total_successes'] / 50),
                'evidence': [f"Used successfully {pattern['total_successes']} times"],
                'timestamp': datetime.utcnow().isoformat()
            }
            await learning_system.record_learning(learning)
    
    print("   ✓ Patterns recorded and converted to learnings\n")
    
    # 3. Initialize improvement loop
    print("3. Running improvement cycle to trigger evolution...")
    improvement_loop = ContinuousImprovementLoop(
        team_name=team_name,
        team_memory=team_memory,
        learning_system=learning_system,
        cycle_hours=24
    )
    
    # Run immediate cycle
    await improvement_loop.run_immediate_cycle()
    print("   ✓ Improvement cycle completed\n")
    
    # 4. Load evolved agent configuration
    print("4. Loading evolved agent configuration...")
    loader = EvolvedAgentLoader(supabase)
    
    evolved_config = loader.load_evolved_agent_config(
        team_id=team_id,
        agent_role=agent_role,
        base_config=base_config
    )
    
    print(f"   Evolution confidence: {evolved_config.evolution_confidence:.2f}")
    print(f"   Strategies learned: {len(evolved_config.learned_strategies)}")
    
    if evolved_config.evolved_prompt != base_config['backstory']:
        print("\n   Evolved Prompt:")
        print("   " + "-" * 50)
        print(evolved_config.evolved_prompt)
        print("   " + "-" * 50)
    print()
    
    # 5. Create A/B test
    print("5. Setting up A/B test for evolved agent...")
    
    # First, create an evolution record
    prompt_evolution = PromptEvolution(supabase)
    
    # Get the latest evolution
    evolutions = prompt_evolution.get_evolution_history(team_id, agent_role, limit=1)
    
    if evolutions:
        evolution_id = evolutions[0]['id']
        
        ab_testing = EvolutionABTesting(supabase)
        test_id = ab_testing.create_ab_test(
            team_id=team_id,
            agent_role=agent_role,
            evolution_id=evolution_id,
            test_duration_hours=1,  # Short for demo
            traffic_split=0.5
        )
        
        print(f"   ✓ A/B test created: {test_id}")
        
        # Simulate some test executions
        print("\n   Simulating task executions...")
        for i in range(20):
            use_treatment, config = ab_testing.should_use_treatment(test_id)
            group = 'treatment' if use_treatment else 'control'
            
            # Simulate performance (evolved agents perform better)
            if use_treatment:
                success = i % 10 != 9  # 90% success
                duration = 2.5 + (i % 3) * 0.5
            else:
                success = i % 10 > 2  # 70% success  
                duration = 3.0 + (i % 4) * 0.5
            
            ab_testing.record_test_result(
                test_id=test_id,
                group=group,
                success=success,
                duration_seconds=duration
            )
        
        # Get results
        results = ab_testing.get_test_results(test_id)
        
        print(f"\n   A/B Test Results:")
        print(f"   Control (Base) Success Rate: {results.control_metrics['success_rate']:.1%}")
        print(f"   Treatment (Evolved) Success Rate: {results.treatment_metrics['success_rate']:.1%}")
        print(f"   Statistical Significance: {results.statistical_significance:.2f}")
        print(f"   Recommendation: {results.recommendation}")
    else:
        print("   No evolutions found to test")
    
    # 6. Show evolution impact
    print("\n6. Evolution Impact Summary:")
    print("   - Agents now incorporate proven strategies automatically")
    print("   - Performance improvements are measured statistically")
    print("   - Unsuccessful evolutions can be rolled back")
    print("   - Knowledge is preserved and shared across team members")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(main())