# AI Team Size Patterns: The Two-Pizza Rule for AI Teams

## The Temptation of Mega-Teams

When faced with the overhead of rich inter-team communication, there's a natural temptation:

> "Why not just make one giant team with everyone in it? Then we don't need delegation!"

This is the **Mega-Team Anti-Pattern** - and it defeats the entire purpose of our architecture.

## Why Team Size Matters

### Small Teams (2-5 agents) ✅
```python
# Effective team - clear roles, focused purpose
marketing_team = Team(
    agents=[
        MarketingLead(),      # Coordinator
        ContentCreator(),     # Specialist
        SocialMediaManager(), # Specialist
        SEOSpecialist()      # Specialist
    ],
    communication="natural",  # Everyone can talk to everyone
    decision_time="minutes",  # Quick consensus
    context_sharing="full"    # Everyone knows everything
)
```

### Mega Teams (10+ agents) ❌
```python
# Ineffective mega-team - becomes a black box
everything_team = Team(
    agents=[
        CEO(), CFO(), CTO(),           # Executives?
        MarketingLead(), SalesLead(),  # Middle managers?
        Developer1(), Developer2(),     # Individual contributors?
        Designer(), Writer(),           # Specialists?
        Support1(), Support2()          # Operations?
    ],
    communication="chaotic",    # Too many voices
    decision_time="hours",      # Can't reach consensus
    context_sharing="partial"   # Information overload
)
```

## The Two-Pizza Rule for AI Teams

### Core Principle
> "If you can't feed your AI team with two pizzas, it's too big to collaborate effectively."

For AI teams, this translates to **3-7 agents** with **5 being optimal**.

### Why This Works

1. **Communication Overhead**
   - 3 agents = 3 communication paths
   - 5 agents = 10 communication paths
   - 10 agents = 45 communication paths (chaos!)

2. **Context Window Limits**
   - LLMs have token limits
   - 5 agents discussing = manageable context
   - 10+ agents = context overflow

3. **Decision Making**
   - Small teams reach consensus quickly
   - Large teams get stuck in endless debate

## Optimal Team Patterns

### Pattern 1: The Focused Team (3-4 agents)
**Best for**: Specialized, focused work

```yaml
# teams/content-team.yaml
name: content-team
size: 3
agents:
  - role: Content Lead
    focus: Strategy and coordination
    
  - role: Technical Writer
    focus: Deep technical content
    
  - role: Creative Writer  
    focus: Marketing and narrative

optimal_because:
  - Clear specializations
  - Minimal coordination overhead
  - Fast decision making
```

### Pattern 2: The Balanced Team (5-6 agents)
**Best for**: Multi-faceted departments

```yaml
# teams/marketing-team.yaml
name: marketing-team
size: 5
agents:
  - role: Marketing Manager
    focus: Strategy and coordination
    
  - role: Content Creator
    focus: Content production
    
  - role: Social Media Manager
    focus: Community engagement
    
  - role: SEO Specialist
    focus: Search optimization
    
  - role: Analytics Expert
    focus: Performance measurement

optimal_because:
  - Covers all marketing functions
  - Still maintains cohesion
  - Can make quick decisions
```

### Pattern 3: The Extended Team (7 agents)
**Best for**: Complex operations requiring diverse skills

```yaml
# teams/engineering-team.yaml
name: engineering-team  
size: 7
agents:
  - role: Engineering Manager
    focus: Technical leadership
    
  - role: Backend Developer
    focus: API development
    
  - role: Frontend Developer
    focus: UI implementation
    
  - role: DevOps Engineer
    focus: Infrastructure
    
  - role: QA Engineer
    focus: Quality assurance
    
  - role: Security Engineer
    focus: Security review
    
  - role: Database Expert
    focus: Data architecture

borderline_because:
  - Approaching communication limits
  - May need sub-team structure
  - Decision making slower
```

## Anti-Pattern Detection

### 🚫 The Mega-Team Anti-Pattern
```python
class MegaTeamAntiPattern:
    """Signs you're creating a mega-team to avoid delegation"""
    
    warning_signs = [
        "More than 8 agents in one team",
        "Multiple management layers within team",
        "Agents don't know what others do",
        "Meetings would need a conference room",
        "Context gets lost in conversation",
        "No clear team purpose"
    ]
    
    consequences = [
        "Slow decision making",
        "Context window overflow", 
        "Unclear responsibilities",
        "Black box behavior",
        "Lost effectiveness"
    ]
```

### 🚫 The Kitchen Sink Anti-Pattern
```python
# Trying to avoid inter-team communication by including everyone
bloated_team = Team(
    name="do-everything-team",
    agents=[
        # Executive layer (should be separate team)
        CEO(), CFO(),
        
        # Middle management (should be separate)
        MarketingManager(), SalesManager(),
        
        # Individual contributors (too many)
        Writer1(), Writer2(), Designer1(), Designer2(),
        Developer1(), Developer2(), Developer3(),
        
        # Support functions (should be separate)
        HRAgent(), LegalAgent()
    ]
)
# Result: 15 agents! This is not a team, it's an organization
```

## Right-Sizing Guidelines

### 1. One Clear Purpose
```python
# ✅ Good: Focused purpose
marketing_team = Team(
    purpose="Create and execute marketing campaigns",
    agents=["Manager", "Content", "Social", "Analytics"]  # 4 agents
)

# ❌ Bad: Multiple purposes
confused_team = Team(
    purpose="Marketing and Sales and Customer Support",
    agents=[...10 agents...]  # Too many domains
)
```

### 2. Direct Collaboration Need
```python
# ✅ Good: All agents need to collaborate
product_team = Team(
    agents=[
        ProductManager(),      # Defines requirements
        Designer(),           # Creates mockups
        FrontendDev(),       # Implements UI
        BackendDev(),        # Implements API
        QAEngineer()         # Tests everything
    ],
    collaboration="Daily interaction on same product"
)

# ❌ Bad: Agents rarely interact
artificial_team = Team(
    agents=[
        MarketingManager(),
        LegalCounsel(),      # Why are these together?
        DevOpsEngineer(),    # Different domain
        Salesperson()        # Different workflow
    ]
)
```

### 3. The Stand-Up Test
> "Could these agents have a productive daily stand-up together?"

If your team needs more than 15 minutes for everyone to sync, it's too big.

## Team Composition Patterns

### Horizontal Teams (Peers)
```yaml
composition: horizontal
size: 3-5
structure:
  - 1 coordinator/lead
  - 2-4 specialists
example:
  - Content Lead
  - Blog Writer
  - Video Creator
  - Graphic Designer
```

### Vertical Teams (Hierarchy)
```yaml
composition: vertical
size: 4-6  
structure:
  - 1 manager
  - 1-2 senior agents
  - 2-3 junior agents
example:
  - Engineering Manager
  - Senior Backend Dev
  - Senior Frontend Dev  
  - Junior Developer
  - QA Engineer
```

### Cross-Functional Teams (Mixed)
```yaml
composition: cross-functional
size: 5-7
structure:
  - 1 lead from primary function
  - 1-2 from each supporting function
example:
  - Product Manager (lead)
  - UX Designer
  - Engineer
  - Data Analyst
  - Marketing Rep
```

## Splitting Large Teams

When a team grows too large, split it:

### Before (Too Large):
```python
# 12-agent mega marketing team
mega_marketing_team = Team(
    agents=[
        MarketingVP(),
        BrandManager(), ContentLead(), 
        Writer1(), Writer2(), Writer3(),
        SocialMedia1(), SocialMedia2(),
        SEO(), SEM(), Analytics(), Email()
    ]
)
```

### After (Right-Sized):
```python
# Split into 3 focused teams
brand_team = Team(
    agents=[BrandManager(), Writer1(), Designer()],
    size=3
)

content_team = Team(
    agents=[ContentLead(), Writer2(), Writer3(), SEO()],
    size=4
)

digital_team = Team(
    agents=[DigitalLead(), SocialMedia(), SEM(), Email()],
    size=4
)

# With coordination via delegation culture
marketing_coordination = InterTeamCoordination(
    teams=[brand_team, content_team, digital_team],
    communication="Rich context delegation"
)
```

## Implementation Guidelines

### 1. Team Size Validation
```python
class TeamSizeValidator:
    MIN_SIZE = 2  # Below this, not really a team
    OPTIMAL_SIZE = 5  # Sweet spot
    MAX_SIZE = 7  # Absolute maximum
    
    def validate_team(self, team: Team) -> ValidationResult:
        size = len(team.agents)
        
        if size < self.MIN_SIZE:
            return ValidationResult(
                valid=False,
                issue="Team too small - consider merging"
            )
        
        if size > self.MAX_SIZE:
            return ValidationResult(
                valid=False,
                issue="Team too large - split into sub-teams",
                suggestion=self.suggest_split(team)
            )
        
        return ValidationResult(valid=True)
```

### 2. Automatic Team Splitting
```python
class TeamSplitter:
    def split_team(self, large_team: Team) -> List[Team]:
        """Intelligently split large teams based on roles"""
        
        # Group by function
        functional_groups = self.group_by_function(large_team.agents)
        
        # Create sub-teams
        sub_teams = []
        for function, agents in functional_groups.items():
            if len(agents) <= 5:
                sub_teams.append(Team(name=f"{function}_team", agents=agents))
            else:
                # Further split if needed
                sub_teams.extend(self.split_by_specialization(agents))
        
        return sub_teams
```

### 3. Monitoring Team Health
```python
class TeamHealthMetrics:
    def calculate_health(self, team: Team) -> float:
        scores = {
            "size_score": self.score_size(len(team.agents)),
            "communication_score": self.score_communication_paths(team),
            "decision_speed": self.measure_decision_time(team),
            "context_clarity": self.measure_context_sharing(team)
        }
        
        return sum(scores.values()) / len(scores)
    
    def score_size(self, size: int) -> float:
        if size == 5:
            return 1.0  # Optimal
        elif 3 <= size <= 7:
            return 0.8  # Good
        else:
            return 0.4  # Problematic
```

## Conclusion

The two-pizza rule isn't arbitrary - it reflects fundamental limits on effective collaboration, whether human or AI. By keeping teams small and focused, we:

1. **Preserve effective collaboration** within teams
2. **Force proper delegation culture** between teams  
3. **Maintain system transparency** (no black boxes)
4. **Ensure scalability** (small teams are easier to replicate)

The temptation to create mega-teams to avoid delegation overhead must be resisted. The overhead of proper inter-team communication is not a bug - it's a feature that ensures system clarity and effectiveness.

Remember: **The goal isn't to minimize communication, but to make necessary communication rich and effective.**