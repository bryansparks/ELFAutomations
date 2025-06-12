# Agent Evolution Integration Guide

## Overview

The Agent Evolution system enables AI agents to learn from their experiences and evolve their prompts, behaviors, and workflows based on proven patterns. This guide shows how to integrate this capability into your teams.

## Key Components

### 1. Prompt Evolution (`elf_automations/shared/memory/prompt_evolution.py`)
- Tracks successful patterns and strategies
- Generates evolved prompts with learned enhancements
- Stores evolution history with confidence scores
- Supports rollback if performance degrades

### 2. Evolved Agent Loader (`elf_automations/shared/memory/evolved_agent_loader.py`)
- Loads agents with their evolved configurations
- Applies personality trait evolutions
- Integrates learned strategies and tool preferences
- Maintains backward compatibility

### 3. A/B Testing Framework (`elf_automations/shared/memory/evolution_ab_testing.py`)
- Tests evolved agents against base versions
- Measures performance impact statistically
- Provides recommendations based on results
- Automatically finalizes tests and applies successful evolutions

### 4. Improvement Loop Integration
- Runs daily/weekly cycles to analyze performance
- Triggers prompt evolution for high-performing agents
- Shares learnings across teams
- Maintains audit trail of all changes

## Integration Steps

### 1. Database Setup

Run the evolution schema migrations:

```bash
# Create agent evolution tables
psql $DATABASE_URL < sql/create_agent_evolutions_table.sql

# Create A/B testing tables
psql $DATABASE_URL < sql/create_ab_testing_tables.sql
```

### 2. Modify Agent Initialization

Update your agent creation to use evolved prompts:

```python
from elf_automations.shared.memory import EvolvedAgentLoader
from elf_automations.shared.utils.supabase_client import get_supabase_client

# In your agent creation function
def create_evolved_agent(team_id: str, agent_role: str, base_config: dict):
    # Get Supabase client
    supabase = get_supabase_client()

    # Create evolved loader
    loader = EvolvedAgentLoader(supabase)

    # Load evolved configuration
    evolved_config = loader.load_evolved_agent_config(
        team_id=team_id,
        agent_role=agent_role,
        base_config=base_config
    )

    # Create agent with evolved prompt
    agent = Agent(
        role=agent_role,
        goal=base_config['goal'],
        backstory=evolved_config.evolved_prompt,  # Use evolved prompt
        allow_delegation=base_config.get('allow_delegation', False),
        verbose=True,
        tools=base_config.get('tools', []),
        llm=base_config['llm']
    )

    # Apply additional evolutions
    agent = loader.apply_evolution_to_agent(agent, evolved_config)

    return agent
```

### 3. Enable A/B Testing

For critical teams, use A/B testing before fully applying evolutions:

```python
from elf_automations.shared.memory import EvolutionABTesting

# Create A/B test
ab_testing = EvolutionABTesting(supabase)

test_id = ab_testing.create_ab_test(
    team_id=team_id,
    agent_role="developer",
    evolution_id=evolution_id,
    test_duration_hours=48,
    traffic_split=0.5  # 50% get evolved version
)

# During task execution
use_evolved, test_config = ab_testing.should_use_treatment(test_id)

if use_evolved:
    # Use evolved agent
    agent = create_evolved_agent(...)
else:
    # Use base agent
    agent = create_base_agent(...)

# Record results
ab_testing.record_test_result(
    test_id=test_id,
    group='treatment' if use_evolved else 'control',
    success=task_succeeded,
    duration_seconds=execution_time
)
```

### 4. Team Factory Integration

Modify the team factory to generate evolution-aware agents:

```python
# In team_factory.py _generate_crewai_agents method

# Add evolution support
agent_code += '''
# Import evolution support
from elf_automations.shared.memory import EvolvedAgentLoader
from elf_automations.shared.utils.supabase_client import get_supabase_client

def {role}_agent(
    llm: Optional[Union[ChatOpenAI, ChatAnthropic]] = None,
    a2a_client: Optional[A2AClient] = None,
    tools: Optional[list] = None,
    team_id: Optional[str] = None,  # Add team_id parameter
    enable_evolution: bool = True    # Add evolution flag
) -> Agent:
    """
    Create {role} agent with optional evolution support.
    """

    # Base configuration
    base_config = {{
        'role': '{role}',
        'goal': '{goal}',
        'backstory': """{backstory}""",
        'allow_delegation': {allow_delegation},
        'tools': tools or [],
        'llm': llm or LLMFactory.create_llm(...)
    }}

    # Apply evolution if enabled and team_id provided
    if enable_evolution and team_id:
        try:
            supabase = get_supabase_client()
            loader = EvolvedAgentLoader(supabase)

            evolved_config = loader.load_evolved_agent_config(
                team_id=team_id,
                agent_role='{role}',
                base_config=base_config
            )

            # Use evolved prompt
            base_config['backstory'] = evolved_config.evolved_prompt

        except Exception as e:
            logger.warning(f"Failed to load evolved config: {{e}}")

    # Create agent
    agent = Agent(**base_config)

    # Wrap with memory awareness
    return MemoryAwareCrewAIAgent(agent, ...)
'''
```

## Example: Evolved Developer Agent

Here's how a developer agent might evolve based on learnings:

### Base Prompt
```
You are a software developer responsible for writing and debugging code.
Focus on clean, maintainable solutions.
```

### Evolved Prompt (after 50 successful tasks)
```
You are a software developer responsible for writing and debugging code.
Focus on clean, maintainable solutions.

Based on experience and proven patterns:
- Always check error logs before making assumptions (95% success rate, used 47 times)
- Use binary search for isolating issues (reduces debug time by 60%, used 23 times)
- Document root causes to prevent recurrence (prevents 80% of repeat bugs, used 31 times)
- Run tests incrementally during development (catches 70% of bugs early, used 28 times)
- Use type hints for better IDE support (reduces errors by 40%, used 19 times)

Prioritize these proven approaches when applicable.
```

## Monitoring Evolution Impact

### 1. View Active Evolutions
```sql
SELECT * FROM active_agent_evolutions
WHERE team_name = 'product-team';
```

### 2. Check A/B Test Results
```python
results = ab_testing.get_test_results(test_id)
print(f"Control success rate: {results.control_metrics['success_rate']:.2%}")
print(f"Treatment success rate: {results.treatment_metrics['success_rate']:.2%}")
print(f"Recommendation: {results.recommendation}")
```

### 3. Evolution Performance Dashboard
```python
# Run the evolution dashboard
python scripts/evolution_dashboard.py --team product-team
```

## Best Practices

1. **Start Small**: Begin with one agent role in a non-critical team
2. **Monitor Closely**: Track performance metrics during evolution
3. **Use A/B Testing**: For production teams, always A/B test first
4. **Set Confidence Thresholds**: Only apply evolutions with >90% confidence
5. **Regular Reviews**: Review evolution history monthly
6. **Rollback Plan**: Always have a way to revert to base prompts

## Troubleshooting

### Evolution Not Applied
- Check if team is registered in Supabase
- Verify sufficient learning data exists (>5 successful patterns)
- Ensure improvement loop is running

### Performance Degradation
- Use rollback_evolution() to revert
- Analyze what patterns led to degradation
- Adjust confidence thresholds

### A/B Test Not Completing
- Check test duration settings
- Verify sufficient traffic volume
- Manual finalization: `ab_testing._finalize_test(test_id)`

## Next Steps

1. Enable evolution for one team as pilot
2. Run for 2 weeks collecting baseline metrics
3. Review evolution impact and adjust parameters
4. Gradually roll out to other teams
5. Share successful patterns across organization
