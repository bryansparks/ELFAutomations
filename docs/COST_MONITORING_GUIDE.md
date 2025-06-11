# Cost Monitoring Guide (Task 6)

## Overview

The Cost Monitoring framework provides comprehensive tracking, analysis, and optimization of LLM API costs across all ElfAutomations teams. It integrates with both local storage and Supabase for real-time monitoring and historical analysis.

## Architecture

```
/elf_automations/shared/
├── monitoring/
│   └── cost_monitor.py      # Advanced analytics and alerting
├── utils/
│   ├── llm_wrapper.py       # Fallback LLM wrapper
│   ├── llm_with_quota.py    # Quota tracking with Supabase integration
│   └── llm_factory.py       # Factory with quota support
└── quota/
    ├── __init__.py
    ├── manager.py           # Quota management
    └── tracker.py           # Usage tracking

/scripts/
├── quota_dashboard.py       # Real-time quota dashboard
├── cost_analytics.py        # Cost analysis and trends
├── cost_optimizer.py        # Optimization recommendations
└── test_cost_monitoring_supabase.py  # Integration test

/sql/
└── create_cost_monitoring_tables.sql  # Supabase schema
```

## Database Schema

The Supabase schema includes:

```sql
-- Core usage tracking
api_usage (
    id, team_name, provider, model,
    input_tokens, output_tokens, cost,
    created_at
)

-- Daily aggregations (auto-updated)
daily_cost_summary (
    team_name, date, provider, model,
    total_requests, total_tokens, total_cost
)

-- Budget management
team_budgets (
    team_name, daily_budget, monthly_budget,
    alert_threshold
)

-- Alert tracking
cost_alerts (
    team_name, alert_type, message,
    threshold_exceeded, created_at
)

-- Optimization recommendations
cost_recommendations (
    team_name, recommendation_type,
    current_cost, potential_savings,
    recommendation_data
)
```

## Components

### 1. Quota Tracked LLM

**Purpose**: Wraps LLMs with automatic usage tracking and Supabase integration.

**Features**:
- Automatic token counting
- Real-time cost calculation
- Local and remote storage
- Budget enforcement
- Fallback on quota exhaustion

**Usage Example**:
```python
from elf_automations.shared.utils import LLMFactory
from supabase import create_client

# Create Supabase client
supabase = create_client(url, key)

# Create LLM with quota tracking
llm = LLMFactory.create_with_quota_tracking(
    team_name="marketing-team",
    preferred_provider="openai",
    preferred_model="gpt-4",
    temperature=0.7,
    supabase_client=supabase  # Optional - enables remote tracking
)

# Use normally - tracking happens automatically
response = llm.invoke("Generate a marketing campaign for...")

# Check remaining budget
remaining = llm.get_remaining_budget()
print(f"Remaining today: ${remaining:.2f}")

# Get usage report
report = llm.get_usage_report(days=7)
print(f"Weekly cost: ${report['total_cost']:.2f}")
```

**How It Works**:
1. Intercepts all LLM calls
2. Extracts token usage from response metadata
3. Calculates cost based on model pricing
4. Records to local JSON (fast access)
5. Records to Supabase (centralized monitoring)
6. Enforces daily budgets
7. Falls back to cheaper models if needed

### 2. Cost Monitor

**Purpose**: Advanced analytics engine for cost analysis and optimization.

**Features**:
- Cost trend analysis
- Anomaly detection
- Budget alerts
- Team comparisons
- Predictive modeling
- ROI calculations

**Usage Example**:
```python
from elf_automations.shared.monitoring import CostMonitor

monitor = CostMonitor()

# Analyze team costs
analysis = monitor.analyze_team_costs("marketing-team", days=30)
print(f"Average daily cost: ${analysis['avg_daily_cost']:.2f}")
print(f"Cost trend: {analysis['trend']}")  # 'increasing', 'stable', 'decreasing'
print(f"Predicted monthly: ${analysis['predicted_monthly']:.2f}")

# Detect anomalies
anomalies = monitor.detect_anomalies("marketing-team")
for anomaly in anomalies:
    print(f"Anomaly on {anomaly['date']}: ${anomaly['cost']:.2f} "
          f"({anomaly['deviation']:.1f} std devs)")

# Compare teams
comparison = monitor.compare_teams(["marketing", "sales", "engineering"])
# Returns ranked list with efficiency metrics

# Get optimization recommendations
recommendations = monitor.get_recommendations("marketing-team")
for rec in recommendations:
    print(f"{rec['action']}: Save ${rec['potential_savings']:.2f}/month")
```

### 3. Quota Dashboard

**Purpose**: Real-time terminal UI for monitoring quota usage.

**Features**:
- Live usage updates
- Team budget status
- Model usage breakdown
- Visual progress bars
- Alert indicators
- Watch mode

**Usage**:
```bash
# Basic dashboard
python scripts/quota_dashboard.py

# Watch mode (updates every 5 seconds)
python scripts/quota_dashboard.py --watch

# Specific team focus
python scripts/quota_dashboard.py --team marketing-team

# Last 30 days
python scripts/quota_dashboard.py --days 30
```

**Dashboard Example**:
```
╭─────────────────── ElfAutomations Quota Dashboard ───────────────────╮
│                                                                       │
│  Team: marketing-team                    Date: 2025-01-21           │
│  ═══════════════════════════════════════════════════════════════    │
│                                                                       │
│  Daily Budget: $10.00                                                │
│  Used Today:   $7.32 (73.2%)                                        │
│  [████████████████████░░░░░░░]                                      │
│                                                                       │
│  Model Usage Today:                                                  │
│  ├─ gpt-4:        $5.20 (71.0%) - 2,600 tokens                     │
│  ├─ gpt-3.5:      $1.12 (15.3%) - 11,200 tokens                    │
│  └─ claude-3:     $1.00 (13.7%) - 1,000 tokens                     │
│                                                                       │
│  ⚠️  Approaching daily limit (73.2% used)                            │
│                                                                       │
╰──────────────────────────────────────────────────────────────────────╯
```

### 4. Cost Analytics

**Purpose**: Deep analysis of cost patterns and trends.

**Features**:
- Historical trend analysis
- Cost breakdown by model/team
- Predictive analytics
- Efficiency scoring
- Export to JSON/CSV

**Usage**:
```bash
# Analyze all teams
python scripts/cost_analytics.py

# Focus on specific team
python scripts/cost_analytics.py --team marketing-team

# Export data
python scripts/cost_analytics.py --export costs_report.json

# Show predictions
python scripts/cost_analytics.py --predict

# Compare periods
python scripts/cost_analytics.py --compare-weeks
```

**Analytics Output**:
```
Cost Analytics Report
====================

Period: Last 30 days
Total Cost: $432.18
Daily Average: $14.41

Top Spending Teams:
1. engineering-team:  $187.32 (43.3%)
2. marketing-team:    $134.21 (31.0%)
3. sales-team:        $110.65 (25.6%)

Model Distribution:
- gpt-4:       $298.43 (69.1%)
- gpt-3.5:     $89.21 (20.6%)
- claude-3:    $44.54 (10.3%)

Trends:
- Cost increasing 12.3% week-over-week
- Peak usage: Wednesdays 2-4 PM
- Most efficient team: sales (0.82 cost/value ratio)

Predictions (Next 30 days):
- Estimated cost: $521.43
- Budget risk: HIGH (exceeds $500 limit)
- Recommended action: Switch 30% of gpt-4 to gpt-3.5

Anomalies Detected:
- 2025-01-18: Unusual spike ($45.23 vs $14.41 avg)
- 2025-01-20: engineering-team 3x normal usage
```

### 5. Cost Optimizer

**Purpose**: Provides actionable recommendations to reduce costs.

**Features**:
- Model optimization suggestions
- Usage pattern analysis
- ROI calculations
- A/B testing recommendations
- Implementation guides

**Usage**:
```bash
# Get optimization recommendations
python scripts/cost_optimizer.py

# Analyze specific team
python scripts/cost_optimizer.py --team marketing-team

# Test optimization impact
python scripts/cost_optimizer.py --simulate

# Generate implementation plan
python scripts/cost_optimizer.py --create-plan
```

**Optimization Report**:
```
Cost Optimization Recommendations
=================================

Team: marketing-team
Current Monthly Cost: $312.45
Optimization Potential: $94.21 (30.2%)

Recommendations:

1. Model Optimization
   Action: Switch routine tasks from gpt-4 to gpt-3.5
   Savings: $52.30/month (16.7%)
   Impact: Minimal - 95% quality retention
   Implementation:
   - Update prompts for clarity
   - Use gpt-3.5 for summaries
   - Reserve gpt-4 for complex analysis

2. Caching Strategy
   Action: Implement response caching for repeated queries
   Savings: $23.41/month (7.5%)
   Impact: None - Identical responses
   Implementation:
   - Cache campaign templates
   - Cache market analysis < 7 days old

3. Batch Processing
   Action: Batch similar requests together
   Savings: $18.50/month (5.9%)
   Impact: 2-3 hour delay acceptable
   Implementation:
   - Queue non-urgent requests
   - Process in 4-hour batches

ROI Analysis:
- Implementation effort: 8 hours
- Monthly savings: $94.21
- Payback period: 2.5 days
- Annual savings: $1,130.52
```

## Integration Patterns

### 1. Team Creation with Budget
```python
# When creating a team, set their budget
from elf_automations.shared.utils import LLMFactory
from elf_automations.shared.quota import QuotaManager

# Set team budget
quota_manager = QuotaManager()
quota_manager.set_team_budget("new-team", daily_budget=15.00)

# Create LLM with tracking
llm = LLMFactory.create_with_quota_tracking(
    team_name="new-team",
    quota_manager=quota_manager
)
```

### 2. Budget Alerts
```python
# Set up budget alerts
monitor = CostMonitor()

# Configure alerts
monitor.configure_alerts(
    team_name="marketing-team",
    thresholds={
        "daily_50": 5.00,    # Alert at $5 (50%)
        "daily_80": 8.00,    # Alert at $8 (80%)
        "daily_100": 10.00   # Alert at $10 (100%)
    },
    callbacks={
        "daily_50": lambda t, c: logger.info(f"{t} at 50% budget: ${c}"),
        "daily_80": lambda t, c: send_slack(f"⚠️ {t} at 80% budget!"),
        "daily_100": lambda t, c: escalate_to_manager(t, c)
    }
)
```

### 3. Automated Optimization
```python
# Automatically optimize based on usage
@with_cost_optimization
async def generate_content(prompt: str, team: str):
    # This decorator will:
    # 1. Check recent usage patterns
    # 2. Select optimal model
    # 3. Apply caching if beneficial
    # 4. Track ROI

    llm = LLMFactory.create_with_quota_tracking(
        team_name=team,
        preferred_model="gpt-4"  # Will be overridden if needed
    )
    return await llm.invoke(prompt)
```

### 4. Cost-Aware Fallback
```python
from elf_automations.shared.resilience import with_fallback

@with_fallback(
    ResourceType.API_QUOTA,
    strategies=[FallbackStrategy.SWITCH_PROVIDER]
)
async def cost_aware_generation(prompt: str):
    # Automatically switches to cheaper model when budget low
    return await llm.invoke(prompt)
```

## Supabase Integration

### Initial Setup
```bash
# 1. Set environment variables
export SUPABASE_URL="your-project-url"
export SUPABASE_KEY="your-anon-key"

# 2. Run SQL schema
# Copy contents of sql/create_cost_monitoring_tables.sql
# Paste in Supabase SQL editor and run

# 3. Initialize monitoring
python scripts/setup_cost_monitoring.py

# 4. Test integration
python scripts/test_cost_monitoring_supabase.py
```

### Real-time Queries
```python
# Query costs from Supabase
supabase = create_client(url, key)

# Get today's costs
result = supabase.table('daily_cost_summary')\
    .select('*')\
    .eq('date', datetime.now().date())\
    .execute()

for team in result.data:
    print(f"{team['team_name']}: ${team['total_cost']:.2f}")

# Get alerts
alerts = supabase.table('cost_alerts')\
    .select('*')\
    .eq('acknowledged', False)\
    .order('created_at', desc=True)\
    .execute()
```

## Best Practices

### 1. Set Appropriate Budgets
```python
# Set budgets based on team size and needs
budgets = {
    "engineering-team": 20.00,  # Higher for development
    "marketing-team": 15.00,    # Medium for content
    "sales-team": 10.00,        # Lower for queries
    "executive-team": 25.00     # Higher for analysis
}

for team, budget in budgets.items():
    quota_manager.set_team_budget(team, daily_budget=budget)
```

### 2. Use Model Tiers
```python
# Define model usage tiers
MODEL_TIERS = {
    "premium": "gpt-4",           # Complex reasoning
    "standard": "gpt-3.5-turbo",  # General tasks
    "economy": "claude-3-haiku"   # Simple tasks
}

def select_model_tier(task_complexity: str) -> str:
    return MODEL_TIERS.get(task_complexity, "standard")
```

### 3. Implement Caching
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_llm_call(prompt_hash: str):
    # Cache by prompt hash
    return llm_response

def generate_with_cache(prompt: str, team: str):
    # Hash the prompt for caching
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

    # Check cache first
    cached = get_from_cache(prompt_hash)
    if cached and cached['age'] < timedelta(hours=24):
        return cached['response']

    # Generate new response
    response = llm.invoke(prompt)
    save_to_cache(prompt_hash, response)
    return response
```

### 4. Monitor Efficiency
```python
# Track cost per successful outcome
monitor.track_outcome(
    team_name="sales-team",
    cost=2.34,
    outcome="lead_converted",
    value=500.00  # Revenue generated
)

# Get efficiency metrics
efficiency = monitor.get_efficiency_metrics("sales-team")
print(f"Cost per conversion: ${efficiency['cost_per_outcome']:.2f}")
print(f"ROI: {efficiency['roi']:.1f}x")
```

### 5. Regular Reviews
```python
# Weekly cost review script
async def weekly_cost_review():
    for team in get_all_teams():
        # Get weekly summary
        summary = monitor.get_weekly_summary(team)

        # Check if optimization needed
        if summary['avg_daily_cost'] > summary['daily_budget'] * 0.8:
            # Get recommendations
            recs = monitor.get_recommendations(team)

            # Send to team lead
            await send_cost_report(team, summary, recs)
```

## Troubleshooting

### High Costs
```python
# Diagnose high costs
diagnosis = monitor.diagnose_high_costs("team-name")
print(f"Primary cause: {diagnosis['primary_cause']}")
print(f"Suggested action: {diagnosis['recommendation']}")

# Common causes:
# - Inefficient prompts (too long)
# - Wrong model selection
# - Repeated similar queries
# - Missing error handling
```

### Quota Errors
```python
# Check quota status
status = quota_manager.check_team_status("team-name")
if status['exceeded']:
    print(f"Exceeded by: ${status['overage']:.2f}")
    print(f"Reset in: {status['hours_until_reset']} hours")
```

### Supabase Sync Issues
```python
# Verify Supabase connection
test_result = test_supabase_connection()
if not test_result['connected']:
    print("Check SUPABASE_URL and SUPABASE_KEY")

# Resync local data
from scripts.sync_cost_data import sync_to_supabase
sync_to_supabase(days=7)  # Sync last 7 days
```

## Reports and Dashboards

### Daily Report Email
```python
# Automated daily report
def generate_daily_report():
    report = {
        "date": datetime.now().date(),
        "total_cost": monitor.get_total_cost_today(),
        "teams": {}
    }

    for team in get_all_teams():
        report["teams"][team] = {
            "cost": monitor.get_team_cost_today(team),
            "requests": monitor.get_request_count(team),
            "efficiency": monitor.get_efficiency_score(team)
        }

    return report

# Send via email/Slack
send_daily_report(generate_daily_report())
```

### Executive Dashboard
```python
# High-level metrics for executives
dashboard = monitor.get_executive_dashboard()

print(f"Monthly Spend: ${dashboard['monthly_total']:,.2f}")
print(f"Projected Annual: ${dashboard['projected_annual']:,.2f}")
print(f"Cost Trend: {dashboard['trend_direction']} {dashboard['trend_percent']:.1f}%")
print(f"Budget Status: {dashboard['budget_status']}")
print(f"Top Cost Driver: {dashboard['top_cost_driver']}")
```

## Summary

The Cost Monitoring framework provides:

1. **Real-time Tracking**: Every LLM call is tracked locally and in Supabase
2. **Budget Enforcement**: Teams can't exceed their daily budgets
3. **Advanced Analytics**: Trends, predictions, and anomaly detection
4. **Optimization Tools**: Actionable recommendations with ROI analysis
5. **Integration**: Works seamlessly with fallback protocols
6. **Visibility**: Dashboards for teams and executives

This ensures ElfAutomations maintains cost efficiency while preserving functionality and performance.
