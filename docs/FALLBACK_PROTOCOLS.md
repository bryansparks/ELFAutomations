# Fallback Protocols for Resource Management

## Overview

The ElfAutomations platform now includes a comprehensive fallback protocol system that ensures reliability and resilience across all resource types. This system automatically handles resource failures and implements intelligent fallback strategies to maintain service availability.

## Key Components

### 1. Resource Manager (`resource_manager.py`)
Monitors and manages all system resources with automatic fallback capabilities.

**Supported Resource Types:**
- **API_QUOTA**: API rate limits and quotas
- **MEMORY**: System memory usage
- **CPU**: CPU utilization
- **DATABASE**: Database connections and pools
- **MCP_SERVER**: MCP server availability
- **NETWORK**: Network endpoints
- **DOCKER**: Docker daemon and containers
- **K8S_POD**: Kubernetes pod health

### 2. Fallback Protocol (`fallback_protocol.py`)
Defines and executes fallback strategies when resources fail.

**Fallback Strategies:**
- **RETRY**: Retry with configurable backoff
- **SWITCH_PROVIDER**: Switch to alternate provider (e.g., OpenAI → Anthropic)
- **DEGRADE_SERVICE**: Reduce service quality to conserve resources
- **QUEUE_REQUEST**: Queue requests for later processing
- **USE_CACHE**: Use cached responses when available
- **SCALE_DOWN**: Reduce resource allocation
- **CIRCUIT_BREAK**: Prevent cascading failures

### 3. Circuit Breaker (`circuit_breaker.py`)
Implements the circuit breaker pattern to prevent cascading failures.

**States:**
- **CLOSED**: Normal operation
- **OPEN**: Failing, reject requests
- **HALF_OPEN**: Testing recovery

### 4. Retry Policy (`retry_policy.py`)
Provides configurable retry strategies with backoff.

**Strategies:**
- **Fixed Delay**: Constant delay between retries
- **Exponential Backoff**: Exponentially increasing delays
- **Linear Backoff**: Linearly increasing delays

### 5. Health Monitor (`health_monitor.py`)
Continuously monitors component health.

## Usage Examples

### Basic Team Integration

```python
from elf_automations.shared.resilience import ResilienceManager
from elf_automations.shared.resilience import with_fallback, ResourceType

class MarketingTeam:
    def __init__(self):
        self.resilience = ResilienceManager("marketing-team")

    async def start(self):
        # Start resilience monitoring
        await self.resilience.start()

        # Register custom monitors
        self.resilience.register_mcp_monitor("supabase")
        self.resilience.register_api_quota_monitor(
            "openai",
            self.check_openai_quota
        )

    @with_fallback(ResourceType.API_QUOTA)
    async def generate_content(self, prompt: str):
        # Automatically handles API quota failures
        return await self.llm.invoke(prompt)
```

### Using Circuit Breaker

```python
from elf_automations.shared.resilience import circuit_breaker

@circuit_breaker("external_api", failure_threshold=5, recovery_timeout=60)
async def call_external_api(data):
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.example.com", json=data) as resp:
            return await resp.json()
```

### Retry with Custom Policy

```python
from elf_automations.shared.resilience import retry, ExponentialBackoff

@retry(max_attempts=5, strategy=ExponentialBackoff(base_delay=2.0))
async def flaky_database_operation():
    # Will retry up to 5 times with exponential backoff
    return await db.execute("SELECT * FROM users")
```

### Full Resilience Stack

```python
async def process_request(self, request_data):
    # Execute with full resilience protection
    return await self.resilience.with_resilience(
        self._process_impl,
        ResourceType.API_QUOTA,
        request_data
    )
```

## Default Fallback Protocols

### API Quota Exhaustion
1. **Retry** (2 attempts with exponential backoff)
2. **Switch Provider** (OpenAI → Anthropic → Local)
3. **Degrade Service** (Use cheaper models)
4. **Queue Request** (Process later)

### Memory/CPU Critical
1. **Use Cache** (Return cached results)
2. **Degrade Service** (Disable features, reduce batch sizes)
3. **Scale Down** (Reduce parallelism)

### Database Connection Failure
1. **Retry** (3 attempts)
2. **Switch to Replica** (Primary → Replica1 → Replica2)
3. **Use Cache** (If available)
4. **Circuit Break** (Prevent overload)

### MCP Server Unavailable
1. **Retry** (With backoff)
2. **Switch to Secondary** (Primary → Secondary → Mock)
3. **Circuit Break** (After repeated failures)

## Monitoring and Alerts

### Health Status Dashboard
```python
# Get comprehensive health report
report = await team.resilience.get_health_report()
```

Returns:
```json
{
    "team": "marketing-team",
    "overall_health": "healthy",
    "components": {
        "system": {
            "status": "healthy",
            "uptime": 3600,
            "error_rate": 0.02
        }
    },
    "resources": {
        "api_quota:openai": {
            "status": "degraded",
            "usage": 85.5
        }
    },
    "circuits": {
        "database_query": {
            "state": "closed",
            "success_rate": 0.98
        }
    }
}
```

## Integration with Existing Systems

### LLM Fallback (Already Implemented)
The existing `FallbackLLM` in `llm_wrapper.py` automatically integrates with the new resilience system:
- Monitors quota usage
- Switches providers on failure
- Reports to health monitor

### MCP Client Enhancement
```python
from elf_automations.shared.resilience import with_fallback

class ResilientMCPClient(MCPClient):
    @with_fallback(ResourceType.MCP_SERVER)
    async def call_tool(self, server, tool, arguments):
        return await super().call_tool(server, tool, arguments)
```

### A2A Communication
```python
class ResilientA2AClient(A2AClient):
    @retry(max_attempts=3)
    @circuit_breaker("a2a_communication")
    async def send_task(self, target_team, task_description, context=None):
        return await super().send_task(target_team, task_description, context)
```

## Best Practices

1. **Always Start Resilience Manager**: Initialize in team's `__init__` and start in `start()` method
2. **Register Custom Monitors**: Add monitors for team-specific resources
3. **Use Decorators**: Apply `@with_fallback` to critical operations
4. **Monitor Health**: Regularly check health reports
5. **Test Fallbacks**: Simulate failures in development
6. **Configure Appropriately**: Adjust thresholds based on criticality

## Configuration

### Environment Variables
```bash
# Resilience configuration
RESILIENCE_CHECK_INTERVAL=30  # Health check interval (seconds)
RESILIENCE_STORAGE_PATH=/data/resilience  # State storage location

# Circuit breaker defaults
CIRCUIT_FAILURE_THRESHOLD=5
CIRCUIT_RECOVERY_TIMEOUT=60

# Retry defaults
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
```

### Per-Team Configuration
```python
# In team's __init__.py
resilience_config = {
    "check_interval": 20,
    "fallback_strategies": {
        ResourceType.API_QUOTA: [
            FallbackAction(FallbackStrategy.SWITCH_PROVIDER, target="anthropic"),
            FallbackAction(FallbackStrategy.USE_CACHE, priority=1)
        ]
    }
}
```

## Troubleshooting

### Common Issues

1. **Circuit Breaker Always Open**
   - Check failure threshold
   - Verify recovery timeout
   - Look for persistent failures

2. **Fallback Not Triggering**
   - Ensure resource monitor is registered
   - Check resource status thresholds
   - Verify fallback protocol registration

3. **Performance Impact**
   - Adjust monitoring intervals
   - Disable unnecessary health checks
   - Use async operations

### Debug Logging
```python
import logging
logging.getLogger("elf_automations.shared.resilience").setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Predictive Failures**: Use ML to predict resource exhaustion
2. **Dynamic Thresholds**: Adjust based on historical data
3. **Cross-Team Coordination**: Share resource state between teams
4. **External Monitoring**: Integration with Prometheus/Grafana
5. **Cost Optimization**: Choose fallbacks based on cost
