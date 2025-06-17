# OpenRouter.ai & Local Model Integration for ElfAutomations

## Overview
This document outlines how to integrate OpenRouter.ai for intelligent model selection and local Small Language Models (SLMs) into the ElfAutomations LLM infrastructure.

## Current State
ElfAutomations currently uses a fallback chain approach:
- Primary: OpenAI (GPT-4, GPT-3.5)
- Fallback: Anthropic (Claude-3 variants)
- Location: `/elf_automations/shared/utils/llm_factory.py`

## Integration Approach

### 1. OpenRouter.ai Integration

OpenRouter provides intelligent routing to 100+ models based on:
- Cost optimization
- Speed requirements
- Quality needs
- Availability

#### Implementation Strategy

```python
# Enhanced LLMFactory with OpenRouter support
class LLMFactory:
    FALLBACK_CHAIN = [
        # OpenRouter as primary option
        ("openrouter", "auto", 0.7),  # Let OpenRouter choose
        ("openrouter", "gpt-4", 0.7),  # Specific model via OpenRouter
        ("openrouter", "claude-3-opus", 0.7),

        # Direct providers as fallback
        ("openai", "gpt-4", 0.7),
        ("anthropic", "claude-3-opus-20240229", 0.7),

        # Local models
        ("local", "llama3-8b", 0.7),
        ("local", "mistral-7b", 0.5),
    ]
```

### 2. Local Model Integration

#### Architecture Options

##### Option A: Direct Integration
```
ElfAutomations Teams
       ↓
   LLMFactory
   ↙    ↓    ↘
OpenAI  OpenRouter  LocalModelServer
                         ↓
                    (LM Studio/Ollama)
```

##### Option B: OpenRouter Proxy (Recommended)
```
ElfAutomations Teams
       ↓
   LLMFactory
       ↓
   OpenRouter
   ↙    ↓    ↘
OpenAI Claude LocalModels
              (via custom endpoint)
```

### 3. Implementation Plan

#### Phase 1: OpenRouter Integration

##### 1.1 Create OpenRouter Provider
```python
# /elf_automations/shared/utils/providers/openrouter.py
from langchain.chat_models.base import BaseChatModel
import httpx

class ChatOpenRouter(BaseChatModel):
    """OpenRouter chat model implementation"""

    def __init__(
        self,
        model: str = "auto",  # Let OpenRouter choose
        api_key: str = None,
        base_url: str = "https://openrouter.ai/api/v1",
        preferences: dict = None,  # Cost, speed, quality preferences
        **kwargs
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url
        self.preferences = preferences or {
            "max_cost_per_token": 0.0001,
            "prefer_faster": False,
            "quality_threshold": 0.8
        }
```

##### 1.2 Update LLMFactory
```python
@classmethod
def _create_single_llm(cls, provider: str, model: str, temperature: float):
    """Create a single LLM instance"""
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        return ChatOpenRouter(
            model=model,
            temperature=temperature,
            api_key=api_key,
            preferences={
                "prefer_local": True,  # Prefer local models when available
                "fallback_to_cloud": True
            }
        )
    elif provider == "local":
        # Direct local model connection
        return ChatLocalModel(
            model=model,
            temperature=temperature,
            base_url=os.getenv("LOCAL_MODEL_URL", "http://localhost:11434")
        )
    # ... existing providers
```

#### Phase 2: Local Model Server Setup

##### 2.1 Local Model MCP
Create an MCP to manage local models:

```yaml
# /mcp/typescript/servers/local-models/config.json
{
  "name": "local-models",
  "tools": [
    {
      "name": "list_models",
      "description": "List available local models"
    },
    {
      "name": "load_model",
      "description": "Load a model into memory"
    },
    {
      "name": "unload_model",
      "description": "Unload model to free memory"
    },
    {
      "name": "model_info",
      "description": "Get model capabilities and requirements"
    }
  ]
}
```

##### 2.2 Deployment Configuration
```yaml
# /k8s/local-models/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: local-model-server
  namespace: elf-automations
spec:
  replicas: 1
  template:
    spec:
      nodeSelector:
        # Pin to machine with GPU/sufficient resources
        node-role: ml-node
      containers:
      - name: ollama
        image: ollama/ollama:latest
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            nvidia.com/gpu: 1  # If GPU available
```

### 4. Configuration

#### Environment Variables
```bash
# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_DEFAULT_MODEL=auto
OPENROUTER_PREFERENCES='{"prefer_local": true, "max_cost": 0.01}'

# Local Model Configuration
LOCAL_MODEL_URL=http://ml-server.local:11434
LOCAL_MODEL_PREFERENCE=llama3-8b,mistral-7b
LOCAL_MODEL_TIMEOUT=30

# Routing Preferences
LLM_ROUTING_STRATEGY=cost_optimized  # or: quality_first, speed_first, local_first
LLM_FALLBACK_ENABLED=true
```

#### Team-Specific Configuration
```python
# teams/engineering/config/llm_config.yaml
llm_preferences:
  primary_provider: openrouter
  model_preferences:
    - local:codellama-13b  # Prefer local code model
    - openrouter:gpt-4    # Fallback to GPT-4
  routing_hints:
    code_generation: prefer_local
    documentation: prefer_quality
    debugging: prefer_fast
```

### 5. Usage Examples

#### Example 1: Cost-Optimized Team
```python
# Marketing team - cost sensitive
llm = LLMFactory.create_llm(
    preferred_provider="openrouter",
    preferred_model="auto",
    team_name="marketing-team",
    preferences={
        "max_cost_per_1k_tokens": 0.001,
        "acceptable_models": ["gpt-3.5", "claude-haiku", "local:*"]
    }
)
```

#### Example 2: Local-First Development
```python
# Engineering team - prefer local for privacy
llm = LLMFactory.create_llm(
    preferred_provider="local",
    preferred_model="codellama-13b",
    team_name="engineering-team",
    enable_fallback=True  # Fall back to cloud if local unavailable
)
```

#### Example 3: Quality-First Executive
```python
# Executive team - quality matters most
llm = LLMFactory.create_llm(
    preferred_provider="openrouter",
    preferred_model="auto",
    team_name="executive-team",
    preferences={
        "quality_threshold": 0.95,
        "acceptable_models": ["gpt-4", "claude-3-opus"]
    }
)
```

### 6. Monitoring & Observability

#### Metrics to Track
```python
# Enhanced quota tracking with routing metrics
class RoutingMetrics:
    - model_selection_count: Counter by model
    - routing_decisions: Why each model was chosen
    - cost_per_team: Track costs across all providers
    - local_vs_cloud_ratio: Usage distribution
    - response_times: By model and provider
    - quality_scores: If available from OpenRouter
```

### 7. Benefits

1. **Cost Optimization**: OpenRouter automatically selects cheapest suitable model
2. **Privacy**: Sensitive data can stay on local models
3. **Availability**: Multiple fallback options ensure high availability
4. **Performance**: Local models for low-latency needs
5. **Flexibility**: Easy to add new models/providers

### 8. Implementation Timeline

**Week 1**: OpenRouter integration
- Create ChatOpenRouter provider
- Update LLMFactory
- Test with existing teams

**Week 2**: Local model setup
- Deploy Ollama/LM Studio
- Create local model MCP
- Configure networking

**Week 3**: Integration testing
- Test fallback chains
- Optimize routing logic
- Monitor costs/performance

**Week 4**: Production rollout
- Update team configurations
- Document best practices
- Set up monitoring

## Next Steps

1. **Immediate**: Add OPENROUTER_API_KEY to credentials
2. **Short-term**: Implement ChatOpenRouter provider
3. **Medium-term**: Deploy local model infrastructure
4. **Long-term**: Optimize routing algorithms based on usage patterns
