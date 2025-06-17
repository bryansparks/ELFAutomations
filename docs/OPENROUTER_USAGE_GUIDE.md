# OpenRouter Usage Guide for ElfAutomations

## Quick Start

### 1. Get OpenRouter API Key
1. Sign up at [OpenRouter.ai](https://openrouter.ai)
2. Generate an API key from the dashboard
3. Add to your environment:
   ```bash
   export OPENROUTER_API_KEY=sk-or-...
   ```

### 2. Basic Usage

#### Let OpenRouter Choose (Auto Mode)
```python
from elf_automations.shared.utils.llm_factory import LLMFactory

# Create LLM that lets OpenRouter choose best model
llm = LLMFactory.create_llm(
    preferred_provider="openrouter",
    preferred_model="auto",
    team_name="my-team"
)
```

#### Specific Model via OpenRouter
```python
# Use specific model through OpenRouter
llm = LLMFactory.create_llm(
    preferred_provider="openrouter",
    preferred_model="gpt-4",
    team_name="my-team"
)
```

### 3. Cost Optimization

```python
# Configure for low cost
llm = LLMFactory.create_llm(
    preferred_provider="openrouter",
    preferred_model="auto",
    team_name="budget-team",
    preferences={
        "max_cost_per_token": 0.00001,  # Very low cost
        "acceptable_models": ["gpt-3.5", "claude-haiku", "gemini-flash"]
    }
)
```

### 4. Local Model Integration

#### Setup Local Model Server
```bash
# Using Ollama (recommended)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
ollama pull codellama
ollama serve  # Runs on http://localhost:11434
```

#### Configure Environment
```bash
export LOCAL_MODEL_URL=http://localhost:11434
export LOCAL_MODEL_PREFERENCE=codellama,llama3
```

#### Use Local Models
```python
# Direct local model usage
llm = LLMFactory.create_llm(
    preferred_provider="local",
    preferred_model="codellama",
    team_name="dev-team"
)
```

## Team Configuration Examples

### Engineering Team (Local-First)
```yaml
# teams/engineering/config/llm_config.yaml
llm_preferences:
  primary_provider: local
  fallback_provider: openrouter
  model_preferences:
    - local:codellama-13b
    - local:llama3-8b
    - openrouter:auto  # Fallback to cloud
```

### Marketing Team (Cost-Optimized)
```yaml
# teams/marketing/config/llm_config.yaml
llm_preferences:
  primary_provider: openrouter
  model_preferences:
    - openrouter:auto
  routing_hints:
    preferences:
      max_cost_per_token: 0.00005
      prefer_faster: true
```

### Executive Team (Quality-First)
```yaml
# teams/executive/config/llm_config.yaml
llm_preferences:
  primary_provider: openrouter
  model_preferences:
    - openrouter:gpt-4
    - openrouter:claude-3-opus
  routing_hints:
    preferences:
      quality_threshold: 0.95
      max_cost_per_token: 0.01
```

## Environment Variables

### Required
```bash
# At least one of these
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Optional
```bash
# OpenRouter configuration
OPENROUTER_DEFAULT_MODEL=auto
OPENROUTER_PREFERENCES='{"prefer_local": true, "max_cost": 0.01}'

# Local model configuration
LOCAL_MODEL_URL=http://localhost:11434
LOCAL_MODEL_PREFERENCE=llama3-8b,codellama-13b

# Routing strategy
LLM_ROUTING_STRATEGY=cost_optimized  # or: quality_first, speed_first, local_first
```

## Monitoring Costs

### View Current Usage
```python
from scripts.cost_analytics import show_cost_dashboard

# Show cost breakdown by team and model
show_cost_dashboard()
```

### Set Budget Alerts
```python
# In team config
cost_constraints:
  daily_budget: 10.00
  alert_threshold: 0.8  # Alert at 80%
  hard_stop: true      # Stop at 100%
```

## Best Practices

### 1. Start with Auto Mode
Let OpenRouter choose the best model based on your constraints:
```python
preferences = {
    "max_cost_per_token": 0.0001,
    "quality_threshold": 0.8,
    "prefer_faster": False
}
```

### 2. Use Local for Sensitive Data
```python
# Route sensitive data to local models
if contains_pii(prompt):
    provider = "local"
    model = "llama3-8b"
else:
    provider = "openrouter"
    model = "auto"
```

### 3. Monitor and Optimize
- Track which models OpenRouter selects
- Analyze cost vs quality tradeoffs
- Adjust preferences based on results

### 4. Implement Fallbacks
```python
# Fallback chain ensures availability
FALLBACK_CHAIN = [
    ("local", "llama3", 0.7),        # Try local first
    ("openrouter", "auto", 0.7),     # Then OpenRouter
    ("openai", "gpt-3.5", 0.5),      # Direct as last resort
]
```

## Troubleshooting

### OpenRouter Connection Issues
```bash
# Test connection
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Local Model Issues
```bash
# Check Ollama status
ollama list
curl http://localhost:11434/api/tags
```

### Debug Routing Decisions
```python
import logging
logging.getLogger("elf_automations.shared.utils.providers.openrouter").setLevel(logging.DEBUG)
```

## Advanced Usage

### Custom Routing Logic
```python
class CustomRoutingLLM(ChatOpenRouter):
    def _get_preferred_models(self):
        # Custom logic based on time of day, load, etc.
        if is_business_hours():
            return ["local/llama3", "openai/gpt-3.5-turbo"]
        else:
            return ["openai/gpt-4", "anthropic/claude-3-opus"]
```

### Multi-Region Deployment
```yaml
# Use different endpoints by region
regions:
  us-east:
    local_model_url: http://us-east-models:11434
  eu-west:
    local_model_url: http://eu-west-models:11434
  asia-pac:
    local_model_url: http://asia-models:11434
```

## Next Steps

1. **Test Setup**: Run `python scripts/test_openrouter_integration.py`
2. **Configure Teams**: Update team configs to use OpenRouter
3. **Deploy Local Models**: Set up Ollama or LM Studio
4. **Monitor Usage**: Use cost analytics dashboard
5. **Optimize**: Adjust preferences based on results
