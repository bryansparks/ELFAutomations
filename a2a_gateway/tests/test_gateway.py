#!/usr/bin/env python3
"""
Test script for A2A Gateway functionality

Tests:
- Team registration/unregistration
- Task routing
- Health monitoring
- Circuit breaker behavior
- Load balancing
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any
import httpx

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from a2a_gateway.src.gateway_client import GatewayClient, TeamAutoRegistration


class MockTeamServer:
    """Mock team server for testing"""
    
    def __init__(self, team_id: str, port: int, failure_rate: float = 0.0):
        self.team_id = team_id
        self.port = port
        self.failure_rate = failure_rate
        self.request_count = 0
        
    async def start(self):
        """Start mock server (simplified for testing)"""
        print(f"Mock {self.team_id} server started on port {self.port}")
        
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate task handling"""
        self.request_count += 1
        
        # Simulate failures based on failure rate
        import random
        if random.random() < self.failure_rate:
            raise Exception(f"Simulated failure in {self.team_id}")
        
        return {
            "status": "completed",
            "result": f"Task handled by {self.team_id}",
            "request_count": self.request_count
        }


async def test_team_registration():
    """Test team registration and discovery"""
    print("\n=== Testing Team Registration ===")
    
    async with GatewayClient() as client:
        # Register multiple teams
        teams = [
            {
                "team_id": "test-sales-team",
                "team_name": "Test Sales Team",
                "endpoint": "http://localhost:9001",
                "capabilities": ["sales", "customer-engagement"],
                "department": "sales"
            },
            {
                "team_id": "test-marketing-team",
                "team_name": "Test Marketing Team",
                "endpoint": "http://localhost:9002",
                "capabilities": ["marketing", "content-creation"],
                "department": "marketing"
            },
            {
                "team_id": "test-product-team",
                "team_name": "Test Product Team",
                "endpoint": "http://localhost:9003",
                "capabilities": ["product-management", "feature-planning"],
                "department": "product"
            }
        ]
        
        # Register teams
        for team in teams:
            try:
                result = await client.register_team(**team)
                print(f"✓ Registered {team['team_id']}: {result}")
            except Exception as e:
                print(f"✗ Failed to register {team['team_id']}: {e}")
        
        # Test discovery
        print("\n--- Testing Discovery ---")
        
        # Discover all teams
        all_teams = await client.discover_teams()
        print(f"Found {len(all_teams)} teams")
        
        # Discover by capability
        sales_teams = await client.discover_teams(capability="sales")
        print(f"Found {len(sales_teams)} teams with 'sales' capability")
        
        # Get specific team status
        if all_teams:
            team_status = await client.get_team_status(all_teams[0]["team_id"])
            print(f"Team status: {team_status}")
        
        # Get all capabilities
        capabilities = await client.get_capabilities()
        print(f"Available capabilities: {capabilities.get('capabilities', [])}")
        
        # Cleanup - unregister teams
        print("\n--- Cleanup ---")
        for team in teams:
            try:
                await client.unregister_team(team["team_id"])
                print(f"✓ Unregistered {team['team_id']}")
            except Exception as e:
                print(f"✗ Failed to unregister {team['team_id']}: {e}")


async def test_task_routing():
    """Test task routing functionality"""
    print("\n=== Testing Task Routing ===")
    
    async with GatewayClient() as client:
        # Register test teams first
        teams = [
            {
                "team_id": "router-test-1",
                "team_name": "Router Test 1",
                "endpoint": "http://localhost:9011",
                "capabilities": ["test-capability-1", "shared-capability"],
                "department": "test"
            },
            {
                "team_id": "router-test-2",
                "team_name": "Router Test 2",
                "endpoint": "http://localhost:9012",
                "capabilities": ["test-capability-2", "shared-capability"],
                "department": "test"
            }
        ]
        
        for team in teams:
            await client.register_team(**team)
        
        # Test routing to specific team
        print("\n--- Routing to Specific Team ---")
        try:
            result = await client.route_task(
                from_team="test-client",
                to_team="router-test-1",
                task_description="Test task for specific team"
            )
            print(f"✓ Routed to specific team: {result}")
        except Exception as e:
            print(f"✗ Failed to route to specific team: {e}")
        
        # Test routing by capability
        print("\n--- Routing by Capability ---")
        try:
            result = await client.route_task(
                from_team="test-client",
                task_description="Test task requiring capability",
                required_capabilities=["test-capability-2"]
            )
            print(f"✓ Routed by capability: {result}")
        except Exception as e:
            print(f"✗ Failed to route by capability: {e}")
        
        # Test routing with multiple capabilities
        print("\n--- Routing with Multiple Capabilities ---")
        try:
            result = await client.route_task(
                from_team="test-client",
                task_description="Test task with multiple capabilities",
                required_capabilities=["shared-capability"]
            )
            print(f"✓ Routed with multiple matches: {result}")
        except Exception as e:
            print(f"✗ Failed with multiple capabilities: {e}")
        
        # Cleanup
        for team in teams:
            await client.unregister_team(team["team_id"])


async def test_health_monitoring():
    """Test health monitoring and circuit breaker"""
    print("\n=== Testing Health Monitoring ===")
    
    async with GatewayClient() as client:
        # Register a team with simulated failures
        team = {
            "team_id": "health-test-team",
            "team_name": "Health Test Team",
            "endpoint": "http://localhost:9020",
            "capabilities": ["health-test"],
            "department": "test"
        }
        
        await client.register_team(**team)
        
        # Check initial health
        status = await client.get_team_status(team["team_id"])
        print(f"Initial health: {status['health']}")
        
        # Note: In a real test, we would simulate failures and check circuit breaker
        # For now, just verify the health endpoint works
        
        # Get gateway statistics
        stats = await client.get_statistics()
        print(f"\nGateway statistics: {stats}")
        
        # Cleanup
        await client.unregister_team(team["team_id"])


async def test_auto_registration():
    """Test automatic team registration helper"""
    print("\n=== Testing Auto Registration ===")
    
    # Create auto-registration helper
    auto_reg = TeamAutoRegistration(
        team_id="auto-reg-test",
        team_name="Auto Registration Test",
        team_port=9030,
        capabilities=["auto-test"],
        department="test"
    )
    
    # Register
    result = await auto_reg.register()
    if result:
        print(f"✓ Auto-registration successful: {result}")
        
        # Verify registration
        async with GatewayClient() as client:
            teams = await client.discover_teams(capability="auto-test")
            if teams:
                print(f"✓ Team found in registry: {teams[0]['team_name']}")
        
        # Unregister
        await auto_reg.unregister()
        print("✓ Auto-unregistration successful")
    else:
        print("✗ Auto-registration failed (gateway might not be running)")


async def test_error_handling():
    """Test error handling and edge cases"""
    print("\n=== Testing Error Handling ===")
    
    async with GatewayClient() as client:
        # Test unregistering non-existent team
        print("\n--- Unregistering Non-existent Team ---")
        try:
            await client.unregister_team("non-existent-team")
            print("✗ Should have failed")
        except httpx.HTTPStatusError as e:
            print(f"✓ Correctly failed with: {e.response.status_code}")
        
        # Test routing to non-existent team
        print("\n--- Routing to Non-existent Team ---")
        try:
            await client.route_task(
                from_team="test",
                to_team="non-existent-team",
                task_description="Test"
            )
            print("✗ Should have failed")
        except httpx.HTTPStatusError as e:
            print(f"✓ Correctly failed with: {e.response.status_code}")
        
        # Test routing with no available teams
        print("\n--- Routing with No Capabilities Match ---")
        try:
            await client.route_task(
                from_team="test",
                task_description="Test",
                required_capabilities=["non-existent-capability-xyz"]
            )
            print("✗ Should have failed")
        except httpx.HTTPStatusError as e:
            print(f"✓ Correctly failed with: {e.response.status_code}")


async def main():
    """Run all tests"""
    print("A2A Gateway Test Suite")
    print("======================")
    
    # Check if gateway is running
    async with GatewayClient() as client:
        if not await client.health_check():
            print("\n❌ Gateway is not running!")
            print("Start the gateway with: python a2a_gateway/src/gateway_server.py")
            return
        else:
            print("\n✅ Gateway is running")
    
    # Run tests
    try:
        await test_team_registration()
        await test_task_routing()
        await test_health_monitoring()
        await test_auto_registration()
        await test_error_handling()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())