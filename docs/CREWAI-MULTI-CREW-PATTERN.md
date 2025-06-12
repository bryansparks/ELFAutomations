# CrewAI Hierarchical Multi-Crew Agent Pattern

## Overview

This document describes a hierarchical organizational pattern for CrewAI where agents can participate in multiple crews simultaneously. This pattern enables complex organizational structures with both high-level strategic coordination and specialized execution teams.

## Pattern Description

### Core Concept
An agent can serve as both a member of a master/strategic crew AND as a leader/manager of a specialized sub-crew. This creates a hierarchical delegation structure that mirrors real-world organizational patterns.

### Key Benefits
- **Organizational Realism**: Mirrors how real organizations operate with managers who report up and manage down
- **Context Continuity**: Agents maintain memory and context across both crew participations
- **Efficient Resource Utilization**: Single agent handles both strategic and tactical responsibilities
- **Scalable Architecture**: Pattern can be extended to multiple levels and specializations

## Architecture Pattern

```
Master Crew (Strategic Level)
├── CEO Agent
├── Marketing Agent (Dual Role)
├── Sales Agent (Dual Role)
└── Operations Agent (Dual Role)

Marketing Sub-Crew (Tactical Level)
├── Marketing Agent (Leader/Manager)
├── Content Creation Agent
├── Social Media Agent
└── Analytics Agent

Sales Sub-Crew (Tactical Level)
├── Sales Agent (Leader/Manager)
├── Lead Generation Agent
├── Customer Relations Agent
└── Proposal Agent
```

## Implementation Components

### 1. Dual-Role Agent Definition

```python
# Agent that participates in both master crew and leads specialized crew
marketing_agent = Agent(
    role='Marketing Manager',
    goal='Develop strategic marketing direction and lead tactical execution',
    backstory='Senior marketing professional with both strategic vision and execution expertise',
    allow_delegation=True,  # Enable delegation to sub-crew members
    memory=True,           # Maintain context across crews
    verbose=True,
    # Additional configurations for multi-crew participation
)
```

### 2. Master Crew Structure

The master crew focuses on:
- Strategic planning and coordination
- High-level decision making
- Resource allocation
- Inter-departmental communication

```python
master_crew = Crew(
    agents=[ceo_agent, marketing_agent, sales_agent, operations_agent],
    tasks=[
        strategic_planning_task,
        budget_allocation_task,
        quarterly_planning_task
    ],
    manager_agent=ceo_agent,  # Optional: CEO as overall manager
    process=Process.hierarchical,  # or Process.sequential
)
```

### 3. Specialized Sub-Crews

Each sub-crew focuses on:
- Tactical execution within their domain
- Specialized task completion
- Detailed implementation
- Domain-specific expertise

```python
marketing_crew = Crew(
    agents=[marketing_agent, content_agent, social_media_agent, analytics_agent],
    tasks=[
        campaign_development_task,
        content_creation_task,
        social_media_execution_task,
        performance_analysis_task
    ],
    manager_agent=marketing_agent,  # Marketing agent leads this crew
    process=Process.hierarchical,
)
```

## Execution Patterns

### Pattern 1: Sequential Execution

```python
# Step 1: Execute master crew for strategic direction
master_result = master_crew.kickoff()

# Step 2: Extract strategic inputs for sub-crews
strategic_context = {
    'budget': master_result.tasks_output[1].output,
    'strategic_priorities': master_result.tasks_output[0].output,
    'timeline': master_result.tasks_output[2].output
}

# Step 3: Execute specialized crews with strategic context
marketing_result = marketing_crew.kickoff(inputs=strategic_context)
sales_result = sales_crew.kickoff(inputs=strategic_context)
```

### Pattern 2: Concurrent with Synchronization

```python
import asyncio

async def execute_hierarchical_crews():
    # Execute master crew first
    master_result = await master_crew.kickoff_async()

    # Extract context and execute sub-crews concurrently
    context = extract_strategic_context(master_result)

    marketing_task = marketing_crew.kickoff_async(inputs=context)
    sales_task = sales_crew.kickoff_async(inputs=context)

    # Wait for all sub-crews to complete
    sub_results = await asyncio.gather(marketing_task, sales_task)

    return master_result, sub_results
```

## Task Design Patterns

### Master Crew Tasks
Focus on strategic, high-level outputs:

```python
strategic_planning_task = Task(
    description="Develop quarterly strategic plan including priorities, budget allocation, and success metrics",
    agent=ceo_agent,
    expected_output="Strategic plan document with clear priorities and resource allocation",
    output_format="structured_data"  # For easy parsing by sub-crews
)
```

### Sub-Crew Tasks
Focus on tactical, detailed execution:

```python
campaign_development_task = Task(
    description="Create detailed marketing campaign based on strategic priorities: {strategic_priorities}",
    agent=marketing_agent,
    context=[strategic_planning_task],  # Reference to master crew output
    expected_output="Complete campaign plan with timelines, channels, and success metrics"
)
```

## Communication Patterns

### Upward Communication
- Sub-crew results inform master crew decisions
- Progress reports flow to strategic level
- Resource requests escalate through hierarchy

### Downward Communication
- Strategic direction flows to specialized crews
- Budget and resource allocations
- Priority changes and adjustments

### Lateral Communication
- Coordination between specialized crews
- Shared resource management
- Cross-functional project collaboration

## Memory and Context Management

### Agent Memory Continuity
```python
# Ensure agents maintain context across crews
agent_config = {
    'memory': True,
    'max_memory_size': 1000,  # Adjust based on needs
    'memory_storage': 'local',  # or 'redis' for distributed systems
}
```

### Context Passing Between Crews
```python
# Structure for passing context between hierarchical levels
crew_context = {
    'strategic_inputs': master_crew_outputs,
    'constraints': budget_and_resource_limits,
    'timeline': project_deadlines,
    'success_metrics': kpi_definitions
}
```

## Best Practices

### Agent Design
1. **Clear Role Boundaries**: Define what the agent does in each crew context
2. **Consistent Personality**: Maintain agent character across both roles
3. **Appropriate Delegation**: Use `allow_delegation=True` for manager roles
4. **Memory Management**: Configure appropriate memory settings for context retention

### Task Design
1. **Hierarchical Dependencies**: Structure tasks to flow logically from strategic to tactical
2. **Clear Outputs**: Define structured outputs that can be consumed by other crews
3. **Context References**: Use task context to pass information between levels
4. **Avoid Conflicts**: Ensure tasks don't create contradictory instructions

### Execution Management
1. **Sequential When Dependent**: Use sequential execution when sub-crews depend on master crew outputs
2. **Concurrent When Possible**: Run independent sub-crews concurrently for efficiency
3. **Error Handling**: Implement robust error handling for multi-crew failures
4. **Resource Monitoring**: Monitor computational resources across multiple active crews

## Implementation Checklist

- [ ] Define dual-role agents with appropriate configurations
- [ ] Structure master crew with strategic focus
- [ ] Create specialized sub-crews with tactical focus
- [ ] Design task dependencies and context flow
- [ ] Implement execution pattern (sequential/concurrent)
- [ ] Configure memory and context management
- [ ] Set up communication patterns between crews
- [ ] Test hierarchical execution flow
- [ ] Implement error handling and monitoring
- [ ] Document crew relationships and dependencies

## Common Pitfalls to Avoid

1. **Context Overload**: Don't pass too much information between crews
2. **Circular Dependencies**: Avoid situations where crews wait on each other indefinitely
3. **Resource Conflicts**: Monitor for agents being overutilized across multiple crews
4. **Inconsistent Outputs**: Ensure agent behavior is consistent across different crew contexts
5. **Memory Leaks**: Properly manage agent memory across long-running multi-crew operations

## Example Use Cases

- **Corporate Structure**: CEO crew delegates to department-specific crews
- **Project Management**: Project manager coordinates multiple specialized teams
- **Product Development**: Product manager works with engineering, design, and marketing crews
- **Consulting Firm**: Senior consultant manages both client relationships and specialized delivery teams
- **Content Production**: Editorial director oversees writing, design, and distribution teams

This pattern enables sophisticated organizational structures while maintaining the benefits of CrewAI's agent-based approach to task execution and delegation.
