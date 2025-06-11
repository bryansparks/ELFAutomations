#!/usr/bin/env python3
"""
Test script for fallback protocols and resource management

Tests the resilience framework including:
- Resource monitoring
- Fallback strategies
- Circuit breakers
- Retry policies
- Health monitoring
"""

import asyncio
import sys
from pathlib import Path

import psutil

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elf_automations.shared.resilience import (
    CircuitBreaker,
    CircuitState,
    ExponentialBackoff,
    FallbackProtocol,
    FallbackStrategy,
    HealthMonitor,
    HealthStatus,
    LinearBackoff,
    ResourceManager,
    ResourceStatus,
    ResourceType,
    with_circuit_breaker,
    with_fallback,
    with_retry,
)

# Test functions that simulate various failure scenarios


def failing_api_call(attempt: int = 0):
    """Simulates an API call that fails sometimes"""
    if attempt < 2:
        raise Exception(f"API quota exceeded (attempt {attempt})")
    return "Success after retries"


async def async_failing_call(attempt: int = 0):
    """Async version of failing call"""
    await asyncio.sleep(0.1)
    if attempt < 2:
        raise Exception(f"Async API failed (attempt {attempt})")
    return "Async success"


@with_retry(max_retries=3)
def retriable_function():
    """Function decorated with retry"""
    import random

    if random.random() < 0.7:  # 70% failure rate
        raise Exception("Random failure")
    return "Got lucky!"


@with_circuit_breaker(failure_threshold=3, recovery_timeout=5)
def protected_function():
    """Function protected by circuit breaker"""
    import random

    if random.random() < 0.8:  # 80% failure rate
        raise Exception("Service unavailable")
    return "Service responded"


@with_fallback(ResourceType.API_QUOTA)
async def quota_protected_function(model: str = "gpt-4"):
    """Function with quota fallback protection"""
    print(f"Attempting to use model: {model}")
    if model == "gpt-4":
        raise Exception("GPT-4 quota exceeded")
    return f"Success with {model}"


async def test_resource_manager():
    """Test resource monitoring"""
    print("\n🔍 Testing Resource Manager")
    print("=" * 50)

    rm = ResourceManager()

    # Check various resources
    resources = [
        ResourceType.MEMORY,
        ResourceType.CPU,
        ResourceType.API_QUOTA,
    ]

    for resource in resources:
        status, usage = rm.check_resource(resource, {"team_name": "test-team"})
        icon = (
            "✅"
            if status == ResourceStatus.HEALTHY
            else "⚠️"
            if status == ResourceStatus.WARNING
            else "❌"
        )
        print(f"{icon} {resource.value}: {status.value} ({usage:.1f}% used)")

    # Test alternative suggestions
    alt = rm.get_alternative_resource(ResourceType.API_QUOTA, {"model": "gpt-4"})
    if alt:
        print(f"\n💡 Alternative suggestion: {alt}")

    # Get resource report
    report = rm.get_resource_report()
    print(f"\n📊 System Info:")
    print(f"   CPU cores: {report['system']['cpu_count']}")
    print(f"   Memory: {report['system']['memory_total_gb']:.1f} GB")
    print(f"   Disk usage: {report['system']['disk_usage_percent']:.1f}%")


async def test_fallback_protocols():
    """Test fallback strategies"""
    print("\n🛡️  Testing Fallback Protocols")
    print("=" * 50)

    fp = FallbackProtocol()

    # Test retry strategy
    print("\n1. Testing retry with backoff...")
    try:
        attempt_count = 0

        def counting_function():
            nonlocal attempt_count
            result = failing_api_call(attempt_count)
            attempt_count += 1
            return result

        result = await fp.execute_with_fallback(
            counting_function,
            ResourceType.API_QUOTA,
            strategies=[FallbackStrategy.RETRY],
        )
        print(f"✅ Retry successful: {result}")
    except Exception as e:
        print(f"❌ Retry failed: {e}")

    # Test provider switching
    print("\n2. Testing provider switching...")

    async def model_function(model="gpt-4"):
        if model == "gpt-4":
            raise Exception("GPT-4 quota exceeded")
        return f"Success with {model}"

    try:
        result = await fp.execute_with_fallback(
            model_function,
            ResourceType.API_QUOTA,
            context={"model": "gpt-4"},
            strategies=[FallbackStrategy.SWITCH_PROVIDER],
            model="gpt-4",
        )
        print(f"✅ Provider switch successful: {result}")
    except Exception as e:
        print(f"❌ Provider switch failed: {e}")

    # Test service degradation
    print("\n3. Testing service degradation...")

    async def quality_function(max_tokens=1000, temperature=0.7):
        return f"Response with max_tokens={max_tokens}, temp={temperature}"

    try:
        result = await fp.execute_with_fallback(
            quality_function,
            ResourceType.API_QUOTA,
            strategies=[FallbackStrategy.DEGRADE_SERVICE],
            max_tokens=1000,
            temperature=0.7,
        )
        print(f"✅ Degraded service: {result}")
    except Exception as e:
        print(f"❌ Service degradation failed: {e}")


def test_circuit_breaker():
    """Test circuit breaker"""
    print("\n⚡ Testing Circuit Breaker")
    print("=" * 50)

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=2, name="TestBreaker")

    # Cause failures to trip the circuit
    print("\n1. Causing failures to trip circuit...")
    for i in range(5):
        try:
            cb.call(lambda: 1 / 0)  # Always fails
        except:
            pass

        stats = cb.get_stats()
        print(
            f"   Attempt {i+1}: State={stats['state']}, Failures={stats['failure_count']}"
        )

    # Try when circuit is open
    print("\n2. Attempting call with open circuit...")
    try:
        cb.call(lambda: "This won't work")
        print("❌ Circuit should have been open!")
    except Exception as e:
        print(f"✅ Circuit correctly rejected call: {e}")

    # Wait for recovery
    print("\n3. Waiting for recovery timeout...")
    import time

    time.sleep(2.5)

    # Test recovery
    print("\n4. Testing recovery with successful call...")
    try:
        result = cb.call(lambda: "Recovery successful")
        print(f"✅ Circuit recovered: {result}")
        print(f"   Final state: {cb.get_stats()['state']}")
    except Exception as e:
        print(f"❌ Recovery failed: {e}")


def test_retry_policies():
    """Test different retry policies"""
    print("\n🔄 Testing Retry Policies")
    print("=" * 50)

    policies = [
        ("Exponential", ExponentialBackoff(max_retries=4)),
        ("Linear", LinearBackoff(max_retries=4)),
        ("Fixed", LinearBackoff(max_retries=4, increment=0)),
    ]

    for name, policy in policies:
        print(f"\n{name} Backoff delays:")
        for attempt in range(4):
            delay = policy.get_delay(attempt)
            print(f"   Attempt {attempt + 1}: {delay:.2f}s delay")


async def test_health_monitor():
    """Test health monitoring"""
    print("\n🏥 Testing Health Monitor")
    print("=" * 50)

    # Alert callback
    def alert(result):
        print(f"🚨 ALERT: {result.name} is {result.status.value} - {result.message}")

    monitor = HealthMonitor(alert_callback=alert)

    # Register default checks
    monitor.register_default_checks()

    # Add custom check
    def custom_check():
        return True  # Always healthy for demo

    from elf_automations.shared.resilience.health_monitor import HealthCheck

    monitor.register_check(
        HealthCheck(
            name="custom_service", check_func=custom_check, interval=10, critical=False
        )
    )

    # Start monitoring
    await monitor.start_monitoring()
    print("✅ Started health monitoring")

    # Wait a bit for checks to run
    await asyncio.sleep(2)

    # Get health report
    report = monitor.get_health_report()
    print(f"\n📋 Health Report:")
    print(f"   Overall Status: {report['overall_status']}")
    print(f"   Checks:")
    for check_name, check_data in report["checks"].items():
        icon = (
            "✅"
            if check_data["status"] == "healthy"
            else "❓"
            if check_data["status"] == "unknown"
            else "❌"
        )
        critical = "CRITICAL" if check_data["critical"] else "non-critical"
        print(f"   {icon} {check_name}: {check_data['status']} ({critical})")

    # Stop monitoring
    await monitor.stop_monitoring()
    print("\n✅ Stopped health monitoring")


async def test_decorated_functions():
    """Test decorator-based resilience"""
    print("\n🎯 Testing Decorated Functions")
    print("=" * 50)

    # Test retry decorator
    print("\n1. Testing @with_retry decorator...")
    success_count = 0
    total_attempts = 5

    for i in range(total_attempts):
        try:
            result = retriable_function()
            success_count += 1
            print(f"   Attempt {i+1}: ✅ {result}")
        except Exception as e:
            print(f"   Attempt {i+1}: ❌ {e}")

    print(
        f"   Success rate: {success_count}/{total_attempts} ({success_count/total_attempts*100:.0f}%)"
    )

    # Test circuit breaker decorator
    print("\n2. Testing @with_circuit_breaker decorator...")
    for i in range(10):
        try:
            result = protected_function()
            print(f"   Call {i+1}: ✅ {result}")
        except Exception as e:
            print(f"   Call {i+1}: ❌ {e}")
        await asyncio.sleep(0.5)

    # Test fallback decorator
    print("\n3. Testing @with_fallback decorator...")
    try:
        result = await quota_protected_function(model="gpt-4")
        print(f"✅ Fallback result: {result}")
    except Exception as e:
        print(f"❌ Fallback failed: {e}")


async def main():
    """Run all tests"""
    print("🧪 Fallback Protocols Test Suite")
    print("================================\n")

    # Run tests
    await test_resource_manager()
    await test_fallback_protocols()
    test_circuit_breaker()
    test_retry_policies()
    await test_health_monitor()
    await test_decorated_functions()

    print("\n✅ All tests completed!")
    print("\n📌 Summary:")
    print("- Resource monitoring tracks API quotas, memory, CPU, etc.")
    print("- Fallback strategies handle failures gracefully")
    print("- Circuit breakers prevent cascading failures")
    print("- Retry policies provide configurable backoff")
    print("- Health monitoring provides continuous system checks")
    print("- Decorators make resilience easy to add to any function")


if __name__ == "__main__":
    asyncio.run(main())
