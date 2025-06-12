# Orchestration Decision Framework for Manager Agents

**Date**: January 22, 2025
**Purpose**: Help manager agents decide when and how to use orchestration capabilities

## The Challenge

Manager agents need to make intelligent decisions about:
- When to handle tasks directly vs. delegate
- When to use project management vs. workflow engine vs. simple A2A
- How to decompose complex requests effectively
- When to create new teams vs. enhance existing ones

## Proposed Solution: Multi-Layer Guidance System

### 1. Enhanced Manager System Prompts

```python
ORCHESTRATION_AWARE_MANAGER_PROMPT = """
You are a {role} managing the {team_name} team. Beyond your domain expertise, you are an orchestration specialist who excels at:

## Decision Framework for Task Handling

When you receive a request, analyze it using this framework:

### 1. Task Complexity Assessment
- **Simple Task** (< 2 hours, single skill): Handle directly or delegate to one team member
- **Moderate Task** (2-24 hours, 2-3 skills): Use project management for tracking
- **Complex Task** (> 24 hours, multiple skills): Consider workflow engine
- **Program** (multiple projects): Definitely use workflow engine

### 2. Coordination Requirements
- **No coordination**: Direct delegation via A2A
- **Sequential steps**: Use project management with dependencies
- **Parallel work**: Use workflow engine
- **Conditional logic**: Use workflow engine
- **Multiple team involvement**: Use workflow engine

### 3. Visibility Requirements
- **Low** (internal task): Simple A2A sufficient
- **Medium** (stakeholder interest): Use project management
- **High** (executive visibility): Use workflow engine with reporting

### 4. Error Sensitivity
- **Low impact**: Simple delegation fine
- **Medium impact**: Project management for tracking
- **High impact**: Workflow engine for error handling

## Decision Matrix

| Criteria | Direct/A2A | Project Mgmt | Workflow Engine |
|----------|------------|--------------|-----------------|
| Duration | < 2 hours | 2-24 hours | > 24 hours |
| Teams | 1 | 1-2 | 3+ |
| Steps | 1-2 | 3-5 | 6+ |
| Dependencies | None | Linear | Complex |
| Approvals | None | Informal | Formal gates |
| Error Impact | Low | Medium | High |

## Examples of When to Use Each

### Use Direct Delegation/A2A When:
- "Create a blog post about our new feature"
- "Review this document for accuracy"
- "Update the team's weekly metrics"

### Use Project Management When:
- "Launch a marketing campaign for product X" (multiple tasks, one team)
- "Redesign our website homepage" (dependencies, progress tracking)
- "Create a customer case study" (sequential tasks)

### Use Workflow Engine When:
- "Coordinate a product launch across all departments"
- "Handle a critical customer escalation"
- "Implement a new AI model across all teams"
- "Execute our quarterly planning process"

## Your Orchestration Responsibilities

1. **Assess incoming requests** against the framework above
2. **Decompose complex work** into appropriate structures
3. **Choose the right tool** for coordination
4. **Monitor progress** and escalate when needed
5. **Learn from outcomes** to improve future decisions

Remember: Over-orchestration wastes resources, under-orchestration causes failures. Aim for the minimum viable coordination that ensures success.
"""
```

### 2. Decision Support Tools

Create specific tools that help managers analyze requests:

```python
class OrchestrationDecisionTool:
    """Help managers decide how to handle complex requests."""

    async def analyze_request(self, request: Dict) -> Dict:
        """Analyze a request and recommend orchestration approach."""

        analysis = {
            "complexity_score": self._assess_complexity(request),
            "coordination_needs": self._assess_coordination(request),
            "recommended_approach": None,
            "reasoning": [],
            "decomposition": None
        }

        # Complexity factors
        factors = {
            "estimated_hours": self._estimate_hours(request),
            "unique_skills": self._count_unique_skills(request),
            "team_count": self._estimate_teams_needed(request),
            "dependency_complexity": self._assess_dependencies(request),
            "approval_gates": self._count_approvals(request),
            "error_impact": self._assess_error_impact(request)
        }

        # Decision logic
        if factors["estimated_hours"] < 2 and factors["team_count"] == 1:
            analysis["recommended_approach"] = "direct_delegation"
            analysis["reasoning"].append("Simple task suitable for direct handling")

        elif factors["team_count"] <= 2 and factors["dependency_complexity"] == "linear":
            analysis["recommended_approach"] = "project_management"
            analysis["reasoning"].append("Moderate complexity with trackable progress")
            analysis["decomposition"] = self._decompose_for_project(request)

        else:
            analysis["recommended_approach"] = "workflow_engine"
            analysis["reasoning"].append(f"Complex coordination across {factors['team_count']} teams")
            analysis["decomposition"] = self._decompose_for_workflow(request)

        return analysis

    def _decompose_for_workflow(self, request: Dict) -> Dict:
        """Decompose request into workflow structure."""

        return {
            "workflow_name": self._suggest_workflow_name(request),
            "phases": [
                {
                    "name": "Assessment",
                    "parallel": False,
                    "steps": self._identify_assessment_steps(request)
                },
                {
                    "name": "Execution",
                    "parallel": True,
                    "steps": self._identify_execution_steps(request)
                },
                {
                    "name": "Validation",
                    "parallel": False,
                    "steps": self._identify_validation_steps(request)
                }
            ],
            "estimated_duration": f"{factors['estimated_hours']} hours",
            "key_risks": self._identify_risks(request)
        }
```

### 3. Learning System Integration

```python
class OrchestrationLearningSystem:
    """Learn from past orchestration decisions to improve future ones."""

    def __init__(self):
        self.decision_history = []
        self.outcome_metrics = {}

    async def record_decision(self, context: Dict, decision: str, reasoning: List[str]):
        """Record an orchestration decision for learning."""

        record = {
            "timestamp": datetime.utcnow(),
            "manager_team": context["team_id"],
            "request_type": self._categorize_request(context["request"]),
            "decision": decision,  # direct, project, workflow
            "reasoning": reasoning,
            "complexity_factors": context["factors"],
            "instance_id": str(uuid4())
        }

        await self._store_decision(record)
        return record["instance_id"]

    async def record_outcome(self, instance_id: str, outcome: Dict):
        """Record the outcome of an orchestration decision."""

        metrics = {
            "success": outcome["success"],
            "duration_actual": outcome["duration"],
            "duration_estimated": outcome["estimated_duration"],
            "teams_involved": outcome["teams_involved"],
            "error_count": outcome["errors"],
            "rework_needed": outcome["rework"],
            "stakeholder_satisfaction": outcome.get("satisfaction", None)
        }

        await self._store_outcome(instance_id, metrics)
        await self._update_patterns()

    async def get_recommendations(self, context: Dict) -> Dict:
        """Get recommendations based on similar past decisions."""

        similar_cases = await self._find_similar_cases(context)

        if not similar_cases:
            return {"confidence": "low", "recommendation": None}

        # Analyze what worked well
        success_patterns = self._analyze_success_patterns(similar_cases)

        return {
            "confidence": "high" if len(similar_cases) > 5 else "medium",
            "recommendation": success_patterns["best_approach"],
            "reasoning": success_patterns["why"],
            "similar_cases": len(similar_cases),
            "average_success_rate": success_patterns["success_rate"],
            "common_pitfalls": success_patterns["pitfalls"]
        }
```

### 4. Contextual Guidance System

```yaml
# orchestration_patterns.yaml
# Pattern library for common scenarios

patterns:
  - name: product_launch
    description: "Launching a new product or feature"
    indicators:
      - "launch"
      - "release"
      - "rollout"
      - "new product"
    recommended_approach: workflow_engine
    workflow_template: product-launch-workflow
    key_considerations:
      - "Requires coordination across marketing, engineering, sales, support"
      - "Has formal approval gates"
      - "Needs staged rollout capability"
      - "High visibility to executives"

  - name: customer_escalation
    description: "Handling critical customer issues"
    indicators:
      - "escalation"
      - "critical customer"
      - "urgent issue"
      - "executive complaint"
    recommended_approach: workflow_engine
    workflow_template: escalation-response-workflow
    key_considerations:
      - "Time-sensitive with SLA requirements"
      - "Needs parallel investigation and communication"
      - "Requires executive notifications"
      - "Must track resolution closely"

  - name: content_campaign
    description: "Creating marketing content campaign"
    indicators:
      - "campaign"
      - "content series"
      - "marketing push"
    recommended_approach: project_management
    key_considerations:
      - "Mostly within marketing team"
      - "Sequential creative process"
      - "Predictable dependencies"
      - "Benefits from progress tracking"

  - name: simple_analysis
    description: "Analyzing data or creating reports"
    indicators:
      - "analyze"
      - "report on"
      - "summarize"
      - "review"
    recommended_approach: direct_delegation
    key_considerations:
      - "Single skill required"
      - "No coordination needed"
      - "Clear deliverable"
      - "Low error impact"
```

### 5. Manager Enhancement Mixin

```python
class OrchestrationAwareManagerMixin:
    """Enhance any manager with orchestration decision capabilities."""

    def __init__(self):
        self.decision_tool = OrchestrationDecisionTool()
        self.learning_system = OrchestrationLearningSystem()
        self.pattern_matcher = PatternMatcher("orchestration_patterns.yaml")

    async def analyze_request_for_orchestration(self, request: str, context: Dict) -> Dict:
        """Analyze a request and decide how to orchestrate it."""

        # Step 1: Pattern matching
        patterns = self.pattern_matcher.match(request)

        # Step 2: Complexity analysis
        analysis = await self.decision_tool.analyze_request({
            "request": request,
            "context": context,
            "patterns": patterns
        })

        # Step 3: Learning system recommendations
        learning_recs = await self.learning_system.get_recommendations({
            "request": request,
            "team": self.team_id,
            "factors": analysis["complexity_factors"]
        })

        # Step 4: Combine insights
        decision = self._make_orchestration_decision(
            analysis,
            patterns,
            learning_recs
        )

        # Step 5: Record for learning
        await self.learning_system.record_decision(
            context={
                "team_id": self.team_id,
                "request": request,
                "factors": analysis["complexity_factors"]
            },
            decision=decision["approach"],
            reasoning=decision["reasoning"]
        )

        return decision

    def _make_orchestration_decision(self, analysis, patterns, learning):
        """Synthesize inputs into final decision."""

        # Weight different inputs
        scores = {
            "direct_delegation": 0,
            "project_management": 0,
            "workflow_engine": 0
        }

        # Analysis recommendation (40% weight)
        scores[analysis["recommended_approach"]] += 0.4

        # Pattern matching (30% weight)
        if patterns:
            scores[patterns[0]["recommended_approach"]] += 0.3

        # Learning system (30% weight)
        if learning["confidence"] != "low":
            scores[learning["recommendation"]] += 0.3

        # Choose highest scoring approach
        best_approach = max(scores, key=scores.get)

        return {
            "approach": best_approach,
            "confidence": self._calculate_confidence(scores),
            "reasoning": self._compile_reasoning(analysis, patterns, learning),
            "decomposition": analysis.get("decomposition"),
            "pattern_match": patterns[0] if patterns else None,
            "learning_insights": learning if learning["confidence"] != "low" else None
        }
```

### 6. Integration with Team Factory

When creating new teams, automatically inject orchestration awareness:

```python
# Enhanced team factory manager agent template

MANAGER_AGENT_TEMPLATE = """
def {manager_role_snake_case}():
    return Agent(
        role="{manager_role}",
        goal="{manager_goal}",
        backstory=\"\"\"{manager_backstory}

        As a manager, you excel at orchestration and know when to:
        - Handle tasks directly (simple, single-skill work)
        - Use project management (multi-task, single team work)
        - Deploy workflow engine (complex, multi-team coordination)

        You analyze each request for complexity, coordination needs, and risks
        before deciding the best approach. You learn from outcomes to improve.
        \"\"\",
        tools=[
            analyze_orchestration_needs,
            create_project,
            start_workflow,
            delegate_task,
            monitor_progress,
            escalate_issue
        ],
        verbose=True,
        allow_delegation=True,
        llm_config={{
            "provider": "{llm_provider}",
            "model": "{llm_model}",
            "temperature": 0.7
        }}
    )
"""
```

### 7. Real-Time Guidance System

```python
class OrchestrationAdvisor:
    """Real-time advisor for orchestration decisions."""

    async def provide_guidance(self, manager_id: str, request: str) -> Dict:
        """Provide real-time guidance on request handling."""

        guidance = {
            "primary_recommendation": None,
            "alternative_approaches": [],
            "key_questions": [],
            "similar_past_cases": [],
            "estimated_outcomes": {}
        }

        # Generate key questions for the manager to consider
        guidance["key_questions"] = [
            "How many teams need to be involved?",
            "Are there formal approval requirements?",
            "What's the error impact if this fails?",
            "Do tasks need to happen in parallel?",
            "Is executive visibility required?",
            "Are there conditional branches in execution?"
        ]

        # Provide estimated outcomes for each approach
        guidance["estimated_outcomes"] = {
            "direct_delegation": {
                "duration": "2-4 hours",
                "success_rate": "95%",
                "visibility": "Low",
                "coordination_overhead": "Minimal"
            },
            "project_management": {
                "duration": "1-3 days",
                "success_rate": "90%",
                "visibility": "Medium",
                "coordination_overhead": "Moderate"
            },
            "workflow_engine": {
                "duration": "2-5 days",
                "success_rate": "85%",
                "visibility": "High",
                "coordination_overhead": "Significant"
            }
        }

        return guidance
```

## Implementation Strategy

### Phase 1: Enhance System Prompts
- Update all manager agents with orchestration framework
- Add decision matrices to prompts
- Include examples of each approach

### Phase 2: Deploy Decision Tools
- Implement OrchestrationDecisionTool
- Add to manager agent toolkits
- Create pattern library

### Phase 3: Enable Learning
- Deploy learning system
- Start recording decisions
- Build recommendation engine

### Phase 4: Continuous Improvement
- Analyze outcomes
- Refine patterns
- Update guidance

## Success Metrics

1. **Decision Quality**
   - % of correct orchestration choices
   - Reduction in over/under-orchestration
   - Time to decision

2. **Outcome Metrics**
   - Task success rates by approach
   - Average completion time
   - Resource efficiency

3. **Learning Metrics**
   - Pattern recognition accuracy
   - Recommendation acceptance rate
   - Improvement over time

## Conclusion

This multi-layered guidance system ensures that manager agents don't just have powerful orchestration tools, but know exactly when and how to use them. By combining enhanced prompts, decision tools, pattern matching, and continuous learning, managers will make increasingly better orchestration decisions, maximizing the value of the project management and workflow engine capabilities.
