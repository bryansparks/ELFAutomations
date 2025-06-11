# Agent vs MCP Guidelines: When to Code vs When to Call

## Core Principle
**Agents provide intelligence and decision-making. MCPs provide capabilities and tools.**

## Decision Framework

### Use MCPs When:

1. **Single-Purpose Tool Access**
   - Twitter API calls → `twitter-mcp`
   - Web scraping → `web-scraper-mcp`
   - Database queries → `supabase-mcp`
   - File operations → `filesystem-mcp`

2. **Standardized Operations**
   - CRUD operations
   - API integrations
   - Data transformations
   - Search operations

3. **Reusable Across Teams**
   - Multiple teams need the same capability
   - Standard interface suffices
   - No team-specific logic required

4. **External Service Integration**
   - Third-party APIs
   - Cloud services
   - Databases
   - Authentication services

### Use Coded Agents When:

1. **Complex Decision Making**
   - Multi-step reasoning
   - Context-aware choices
   - Strategy formulation
   - Trade-off analysis

2. **Orchestration Required**
   - Coordinating multiple MCPs
   - Workflow management
   - Error recovery strategies
   - Conditional logic flows

3. **Domain Expertise**
   - Specialized knowledge application
   - Industry-specific reasoning
   - Custom business logic
   - Nuanced interpretation

4. **Team Dynamics**
   - Personality traits matter
   - Collaborative reasoning
   - Debate and consensus
   - Role-specific perspectives

## Research Team Example Refactored

### Original Design (All Coded Agents):
```yaml
Research Team:
  - Research Team Lead (coded agent)
  - Web Research Specialist (coded agent)
  - Academic Research Specialist (coded agent)
  - Social Media Analyst (coded agent)
  - Technical Research Specialist (coded agent)
```

### Recommended Hybrid Design:
```yaml
Research Team:
  agents:
    - Research Team Lead:
        role: "Orchestration and quality control"
        personality: ["pragmatist", "detail-oriented"]
        uses_mcps: ["task-router-mcp"]

    - Research Strategist:
        role: "Determine research approach and synthesize findings"
        personality: ["analyzer", "innovator"]
        uses_mcps: ["all research MCPs"]

    - Research Quality Skeptic:
        role: "Validate sources and challenge conclusions"
        personality: ["skeptic"]
        uses_mcps: ["fact-checker-mcp", "source-validator-mcp"]

  mcps:
    - web-research-mcp:
        capabilities: ["web_scraping", "content_extraction", "site_monitoring"]

    - academic-research-mcp:
        capabilities: ["arxiv_search", "pubmed_search", "semantic_scholar", "citation_analysis"]

    - social-research-mcp:
        capabilities: ["twitter_search", "reddit_analysis", "linkedin_search", "sentiment_analysis"]

    - technical-research-mcp:
        capabilities: ["github_search", "documentation_parsing", "api_discovery"]
```

## Key Insights

### 1. **Agents = Brains, MCPs = Hands**
- Agents decide WHAT to research and HOW to interpret it
- MCPs execute the actual searches and data retrieval

### 2. **Smaller, Smarter Teams**
- Instead of 5-6 specialists, have 3 smart agents
- Each agent can use multiple MCPs as needed
- Reduces coordination overhead

### 3. **Flexibility Through Composition**
- Agents can mix and match MCPs
- New capabilities = new MCPs, not new agents
- Easier to maintain and scale

## Implementation in Team Factory

### Enhanced Team Creation Logic:
```python
def suggest_mcp_usage(self, team_spec: TeamSpecification) -> Dict[str, List[str]]:
    """Suggest which roles should use MCPs instead of being fully coded"""

    suggestions = {}

    for member in team_spec.members:
        role_lower = member.role.lower()

        # Roles that are primarily tool-users
        if any(keyword in role_lower for keyword in ["analyst", "researcher", "monitor", "tracker"]):
            if "social" in role_lower:
                suggestions[member.role] = ["social-media-mcp", "sentiment-analysis-mcp"]
            elif "web" in role_lower:
                suggestions[member.role] = ["web-scraper-mcp", "content-parser-mcp"]
            elif "academic" in role_lower:
                suggestions[member.role] = ["academic-search-mcp", "paper-analysis-mcp"]

        # Roles that need orchestration stay as full agents
        elif any(keyword in role_lower for keyword in ["manager", "lead", "strategist", "coordinator"]):
            suggestions[member.role] = ["task-router-mcp"]  # Minimal MCP usage

    return suggestions
```

### Team Factory Prompt:
```
Creating Research Team...

📊 MCP Optimization Analysis:
- Web Research Specialist → Convert to MCP usage (90% tool operations)
- Academic Research Specialist → Convert to MCP usage (85% tool operations)
- Social Media Analyst → Convert to MCP usage (95% tool operations)

Recommended Architecture:
✓ 3 Intelligent Agents (decision makers)
✓ 4 Specialized MCPs (capability providers)
✓ 60% reduction in coordination complexity

Would you like to:
1. Keep original design (5 coded agents)
2. Use optimized design (3 agents + 4 MCPs)
3. Customize the mix
```

## Benefits of This Approach

1. **Clearer Responsibilities**
   - Agents own decisions
   - MCPs own executions

2. **Better Scalability**
   - Add capabilities via MCPs
   - Don't bloat teams with specialists

3. **Easier Maintenance**
   - MCPs are simpler to update
   - Agents focus on logic, not implementation

4. **Cost Efficiency**
   - Fewer LLM calls for simple operations
   - Agents used only when intelligence needed

## Rule of Thumb
**If 80% of a role is using tools/APIs, it should be an MCP, not an agent.**
