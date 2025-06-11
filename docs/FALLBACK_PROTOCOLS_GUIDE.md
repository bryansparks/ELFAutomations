# Fallback Protocols Guide (Task 7)

## Overview

The Fallback Protocols framework provides comprehensive resilience for ElfAutomations, ensuring the system can gracefully handle resource constraints, service failures, and unexpected errors without complete failure.

## Architecture

```
/elf_automations/shared/resilience/
├── __init__.py              # Package exports
├── resource_manager.py      # Resource monitoring & management
├── fallback_protocols.py    # Fallback strategy implementation
├── circuit_breaker.py       # Circuit breaker pattern
├── retry_policies.py        # Various retry strategies
└── health_monitor.py        # Continuous health monitoring
```

## Core Concepts

### Resource Types
The framework monitors and manages 8 types of resources:
- **API_QUOTA**: LLM API usage limits
- **MEMORY**: System RAM usage
- **CPU**: Processor utilization
- **DATABASE**: Connection pool and query capacity
- **MCP_SERVER**: MCP server availability
- **NETWORK**: Network endpoints and APIs
- **DOCKER**: Container resources
- **K8S_POD**: Kubernetes pod resources

### Fallback Strategies
When resources are constrained, the framework applies these strategies in order:
1. **RETRY**: Retry with configurable backoff
2. **SWITCH_PROVIDER**: Use alternative provider (e.g., GPT-4 → Claude)
3. **DEGRADE_SERVICE**: Reduce quality for lower resource usage
4. **QUEUE_REQUEST**: Queue for later processing
5. **USE_CACHE**: Return cached response if available
6. **CIRCUIT_BREAK**: Temporarily stop attempting failed operations
7. **LOAD_SHED**: Reject requests to protect system

## Components

### 1. Resource Manager

**Purpose**: Monitors resource usage and availability across the system.

**Key Features**:
- Real-time resource monitoring
- Configurable warning/critical thresholds
- Usage caching for performance
- Alternative resource suggestions
- Historical usage tracking

**Usage Example**:
```python
from elf_automations.shared.resilience import ResourceManager, ResourceType

# Initialize manager
rm = ResourceManager()

# Check resource status
status, usage_pct = rm.check_resource(
    ResourceType.API_QUOTA,
    context={"team_name": "marketing-team", "model": "gpt-4"}
)

if status == ResourceStatus.CRITICAL:
    # Get alternative
    alt = rm.get_alternative_resource(
        ResourceType.API_QUOTA,
        context={"model": "gpt-4"}
    )
    print(f"Switch to: {alt['model']}")

# Check if resource available
if rm.can_use_resource(ResourceType.MEMORY):
    # Proceed with memory-intensive operation
    process_large_dataset()

# Record usage for tracking
rm.record_usage(
    ResourceType.API_QUOTA,
    amount=1000,  # tokens
    context={"team_name": "marketing-team"}
)

# Get comprehensive report
report = rm.get_resource_report(hours=24)
```

**Thresholds Configuration**:
```python
# Custom thresholds
rm = ResourceManager(
    warning_thresholds={
        ResourceType.API_QUOTA: 70,    # Warn at 70% usage
        ResourceType.MEMORY: 80,       # Warn at 80% memory
        ResourceType.CPU: 85,          # Warn at 85% CPU
    },
    critical_thresholds={
        ResourceType.API_QUOTA: 90,    # Critical at 90%
        ResourceType.MEMORY: 95,       # Critical at 95%
        ResourceType.CPU: 98,          # Critical at 98%
    }
)
```

### 2. Fallback Protocols

**Purpose**: Implements strategies for graceful degradation when resources are exhausted.

**Usage with Decorators**:
```python
from elf_automations.shared.resilience import with_fallback, FallbackStrategy

# Automatic fallback for API quota
@with_fallback(ResourceType.API_QUOTA)
async def call_llm(prompt: str, model: str = "gpt-4"):
    # This will automatically:
    # 1. Check quota before calling
    # 2. Switch to alternative model if needed
    # 3. Degrade service if necessary
    # 4. Queue request if all else fails
    response = await llm.invoke(prompt, model=model)
    return response

# Custom strategy order
@with_fallback(
    ResourceType.DATABASE,
    strategies=[
        FallbackStrategy.RETRY,
        FallbackStrategy.USE_CACHE,
        FallbackStrategy.CIRCUIT_BREAK
    ]
)
def query_database(query: str):
    return db.execute(query)
```

**Manual Usage**:
```python
from elf_automations.shared.resilience import FallbackProtocol

protocol = FallbackProtocol()

# Execute with fallback
result = await protocol.execute_with_fallback(
    func=expensive_operation,
    resource_type=ResourceType.MEMORY,
    context={"operation": "data_processing"},
    data=large_dataset
)

# Add custom hooks
async def log_fallback(context):
    logger.info(f"Fallback triggered for {context.team_name}")

protocol.add_stage_hook(DeploymentStage.PRE_BUILD, log_fallback)
```

**Service Degradation Example**:
```python
# Original high-quality function
async def generate_report(data, quality="high"):
    if quality == "high":
        return await complex_analysis(data, max_tokens=2000)
    else:
        return await simple_summary(data, max_tokens=500)

# With automatic degradation
@with_fallback(
    ResourceType.API_QUOTA,
    strategies=[FallbackStrategy.DEGRADE_SERVICE]
)
async def generate_report_resilient(data):
    # Framework automatically reduces max_tokens and temperature
    # when quota is low
    return await generate_report(data)
```

### 3. Circuit Breaker

**Purpose**: Prevents cascading failures by temporarily stopping calls to failing services.

**States**:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Too many failures, requests rejected immediately
- **HALF_OPEN**: Testing recovery with limited requests

**Usage Example**:
```python
from elf_automations.shared.resilience import CircuitBreaker, with_circuit_breaker

# Manual circuit breaker
cb = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Try recovery after 60 seconds
    expected_exception=APIError,
    name="OpenAI-API"
)

# Use manually
try:
    result = cb.call(lambda: api.chat_completion(prompt))
except Exception as e:
    if "Circuit breaker is OPEN" in str(e):
        # Use fallback service
        result = fallback_service(prompt)

# With decorator
@with_circuit_breaker(failure_threshold=3, recovery_timeout=30)
def call_external_api(endpoint: str):
    return requests.get(endpoint).json()

# Get circuit statistics
stats = cb.get_stats()
print(f"State: {stats['state']}")
print(f"Success rate: {stats['success_rate']}%")
print(f"Rejected calls: {stats['rejected_calls']}")

# Manual control
cb.trip()   # Manually open circuit
cb.reset()  # Manually close circuit
```

### 4. Retry Policies

**Purpose**: Configurable retry strategies with various backoff patterns.

**Available Policies**:
- **ExponentialBackoff**: Delay doubles each attempt (1s, 2s, 4s, 8s...)
- **LinearBackoff**: Delay increases linearly (1s, 2s, 3s, 4s...)
- **FixedDelay**: Same delay for all attempts
- **FibonacciBackoff**: Fibonacci sequence delays (1s, 1s, 2s, 3s, 5s...)
- **AdaptiveBackoff**: Adjusts based on success/failure rate

**Usage Example**:
```python
from elf_automations.shared.resilience import (
    with_retry, ExponentialBackoff, AdaptiveBackoff
)

# Simple retry with exponential backoff
@with_retry(max_retries=3)
def flaky_operation():
    if random.random() < 0.7:
        raise Exception("Random failure")
    return "Success"

# Custom backoff policy
policy = ExponentialBackoff(
    max_retries=5,
    base_delay=0.5,      # Start with 0.5s
    multiplier=3,        # Triple each time
    max_delay=30,        # Cap at 30s
    jitter=True          # Add randomization
)

@with_retry(backoff=policy)
async def api_call():
    return await external_api.fetch()

# Adaptive backoff that learns
adaptive = AdaptiveBackoff(
    initial_delay=1.0,
    success_reduction=0.5,   # Halve delay on success
    failure_increase=2.0     # Double delay on failure
)

for i in range(10):
    try:
        result = api_call_with_adaptive_retry()
        adaptive.record_success()  # Reduces future delays
    except:
        adaptive.record_failure()  # Increases future delays
```

### 5. Health Monitor

**Purpose**: Continuous health monitoring with configurable checks and alerts.

**Features**:
- Async health checks with timeouts
- Critical vs non-critical checks
- Aggregated health status
- Alert callbacks
- Historical health tracking

**Usage Example**:
```python
from elf_automations.shared.resilience import HealthMonitor, HealthCheck

# Initialize monitor
monitor = HealthMonitor(
    alert_callback=lambda result: send_slack_alert(result)
)

# Register default checks (CPU, memory, disk, API quota)
monitor.register_default_checks()

# Add custom health check
async def check_database_connections():
    active = db.get_active_connections()
    max_connections = db.get_max_connections()
    return active < (max_connections * 0.8)  # Healthy if under 80%

monitor.register_check(HealthCheck(
    name="database_connections",
    check_func=check_database_connections,
    interval=60,         # Check every minute
    timeout=10,          # 10 second timeout
    critical=True        # Affects overall health
))

# Start monitoring
await monitor.start_monitoring()

# Get current health
status = monitor.get_health_status()  # Overall status
db_status = monitor.get_health_status("database_connections")

# Get detailed report
report = monitor.get_health_report()
for check_name, details in report['checks'].items():
    print(f"{check_name}: {details['status']} - {details['message']}")

# Run check immediately
result = await monitor.run_check_now("database_connections")
if result.status == HealthStatus.UNHEALTHY:
    # Take corrective action
    await db.close_idle_connections()
```

## Integration Patterns

### 1. LLM Calls with Full Resilience
```python
from elf_automations.shared.resilience import (
    with_fallback, with_retry, with_circuit_breaker
)

@with_circuit_breaker(failure_threshold=5)
@with_retry(max_retries=3)
@with_fallback(ResourceType.API_QUOTA)
async def resilient_llm_call(prompt: str, team_name: str):
    """
    This function will:
    1. Check circuit breaker first
    2. Retry up to 3 times on failure
    3. Use fallback strategies if quota exhausted
    """
    llm = LLMFactory.create_with_quota_tracking(
        team_name=team_name,
        preferred_model="gpt-4"
    )
    return await llm.invoke(prompt)
```

### 2. Database Operations with Resilience
```python
@with_fallback(
    ResourceType.DATABASE,
    strategies=[
        FallbackStrategy.RETRY,
        FallbackStrategy.USE_CACHE,
        FallbackStrategy.CIRCUIT_BREAK
    ]
)
async def get_user_data(user_id: str):
    # Try primary database
    return await db.query(f"SELECT * FROM users WHERE id = {user_id}")

# The framework will:
# 1. Retry with backoff on connection errors
# 2. Return cached data if available
# 3. Open circuit if database is down
```

### 3. Memory-Intensive Operations
```python
@with_fallback(
    ResourceType.MEMORY,
    strategies=[
        FallbackStrategy.DEGRADE_SERVICE,
        FallbackStrategy.QUEUE_REQUEST
    ]
)
def process_large_file(file_path: str, batch_size: int = 10000):
    # Framework will automatically:
    # 1. Reduce batch_size if memory is constrained
    # 2. Queue request if memory is critical

    with open(file_path) as f:
        batch = []
        for line in f:
            batch.append(line)
            if len(batch) >= batch_size:
                process_batch(batch)
                batch = []
```

### 4. Full Team Deployment with Resilience
```python
async def deploy_team_with_resilience(team_name: str):
    # Resource checks
    rm = ResourceManager()

    # Check all required resources
    resources_ok = all(
        rm.can_use_resource(resource_type)
        for resource_type in [
            ResourceType.CPU,
            ResourceType.MEMORY,
            ResourceType.DOCKER,
            ResourceType.K8S_POD
        ]
    )

    if not resources_ok:
        # Queue for later
        await deployment_queue.put(team_name)
        return

    # Deploy with circuit breaker
    cb = CircuitBreaker(name=f"deploy-{team_name}")

    try:
        result = await cb.call_async(
            pipeline.deploy_team,
            team_name=team_name
        )
        return result
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        # Will be retried when circuit closes
```

## Best Practices

### 1. Layer Your Resilience
```python
# Good: Multiple layers of protection
@with_circuit_breaker()  # Outermost: Prevent cascading failures
@with_retry()           # Middle: Handle transient errors
@with_fallback()        # Innermost: Handle resource exhaustion
async def critical_operation():
    pass
```

### 2. Configure Appropriate Timeouts
```python
# Set timeouts based on operation importance
monitor.register_check(HealthCheck(
    name="critical_api",
    check_func=check_api,
    timeout=30,     # Generous timeout for critical services
    interval=300    # Check every 5 minutes
))

monitor.register_check(HealthCheck(
    name="optional_feature",
    check_func=check_feature,
    timeout=5,      # Quick timeout for optional features
    interval=3600   # Check hourly
))
```

### 3. Use Context for Better Decisions
```python
# Provide context for smarter fallbacks
status, usage = rm.check_resource(
    ResourceType.API_QUOTA,
    context={
        "team_name": "sales-team",
        "priority": "high",
        "model": "gpt-4",
        "operation": "customer_analysis"
    }
)

# Resource manager can make better decisions with context
```

### 4. Monitor and Alert
```python
# Set up comprehensive monitoring
async def health_alert(result: HealthCheckResult):
    if result.status == HealthStatus.UNHEALTHY and result.critical:
        await send_pagerduty_alert({
            "service": result.name,
            "severity": "critical",
            "message": result.message
        })
    elif result.status == HealthStatus.DEGRADED:
        await send_slack_notification({
            "channel": "#infrastructure",
            "text": f"Service degraded: {result.name}"
        })

monitor = HealthMonitor(alert_callback=health_alert)
```

### 5. Test Your Resilience
```python
# Test script for resilience
async def chaos_test():
    # Simulate resource exhaustion
    rm = ResourceManager()
    rm._usage_cache[f"{ResourceType.API_QUOTA}:{{}}"] = (
        ResourceStatus.EXHAUSTED, 100.0
    )

    # Should fallback gracefully
    result = await resilient_llm_call("test prompt", "test-team")
    assert "fallback" in result.lower()

    # Simulate circuit breaker trip
    cb = CircuitBreaker(name="test-breaker", failure_threshold=1)
    try:
        cb.call(lambda: 1/0)  # Fail once
    except:
        pass

    # Should be open now
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        cb.call(lambda: "This should fail")
```

## Monitoring and Debugging

### View Resource Status
```python
# Quick resource check script
import asyncio
from elf_automations.shared.resilience import ResourceManager, ResourceType

async def check_all_resources():
    rm = ResourceManager()

    print("Resource Status Report")
    print("=" * 50)

    for resource_type in ResourceType:
        status, usage = rm.check_resource(resource_type)
        emoji = "✅" if status.value == "healthy" else "⚠️" if status.value == "warning" else "❌"
        print(f"{emoji} {resource_type.value:15} {status.value:10} {usage:5.1f}%")

    print("\nResource Report:")
    report = rm.get_resource_report()
    print(f"CPU: {report['system']['cpu_count']} cores")
    print(f"Memory: {report['system']['memory_total_gb']:.1f} GB")
    print(f"Disk: {report['system']['disk_usage_percent']:.1f}% used")

asyncio.run(check_all_resources())
```

### Circuit Breaker Dashboard
```python
# Monitor circuit breakers
from elf_automations.shared.resilience import CircuitBreaker

# Get all active circuit breakers (would need registry)
breakers = get_all_circuit_breakers()

for breaker in breakers:
    stats = breaker.get_stats()
    print(f"\n{stats['name']}:")
    print(f"  State: {stats['state']}")
    print(f"  Calls: {stats['total_calls']} total, {stats['rejected_calls']} rejected")
    print(f"  Success Rate: {stats['success_rate']}%")
    print(f"  Time in State: {stats['time_in_state']}")
```

## Summary

The Fallback Protocols framework provides:

1. **Comprehensive Monitoring**: 8 resource types with configurable thresholds
2. **Multiple Strategies**: 7 fallback strategies for different scenarios
3. **Circuit Breaking**: Prevents cascading failures automatically
4. **Flexible Retries**: 5 retry policies for different use cases
5. **Health Monitoring**: Continuous health checks with alerting
6. **Easy Integration**: Simple decorators for existing code

This ensures ElfAutomations remains operational even under severe resource constraints or external service failures.
