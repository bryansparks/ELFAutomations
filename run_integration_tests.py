#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Distributed Agent Architecture - Complete Integration Test Suite

This script runs the comprehensive test suite for the entire distributed agent architecture:
- Kubernetes foundation infrastructure
- Agent deployment and lifecycle (kagent)
- A2A communication protocol
- AgentGateway + MCP integration

Usage:
    python3 run_integration_tests.py [--suite SUITE_NAME] [--verbose]

Suite options:
    - k8s: Kubernetes foundation tests only
    - agents: Agent deployment tests only
    - a2a: A2A communication tests only
    - gateway: AgentGateway + MCP tests only
    - all: All test suites (default)
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.integration.test_a2a_communication import A2ACommunicationTestSuite
from tests.integration.test_agent_deployment import AgentDeploymentTestSuite
from tests.integration.test_agentgateway_mcp import AgentGatewayMCPTestSuite
from tests.integration.test_k8s_foundation import K8sFoundationTestSuite
from tests.integration.test_runner import TestRunner


def print_banner():
    """Print test suite banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DISTRIBUTED AGENT ARCHITECTURE                           ║
║                        INTEGRATION TEST SUITE                               ║
║                                                                              ║
║  Testing: Kubernetes + kagent + A2A + AgentGateway + MCP                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_suite_info():
    """Print information about available test suites."""
    info = """
🧪 TEST SUITES AVAILABLE:

1. 🏗️  Kubernetes Foundation
   - Cluster connectivity and health
   - Docker and kubectl availability
   - RBAC permissions and CRDs
   - kagent controller status
   - Resource quotas and limits

2. 🚀 Agent Deployment
   - Docker image availability
   - Namespace and secrets setup
   - Chief AI Agent deployment
   - Pod health and API endpoints
   - CrewAI task execution
   - Agent scaling and lifecycle

3. 🔄 A2A Communication
   - A2A SDK availability and imports
   - AgentCard generation and validation
   - A2A server deployment
   - Agent registration and discovery
   - Task store and queue management
   - Agent-to-agent messaging
   - Multi-agent workflows
   - Event streaming

4. 🌐 AgentGateway + MCP
   - AgentGateway Docker image and config
   - Kubernetes deployment
   - MCP server discovery
   - Proxy functionality testing
   - Agent-MCP integration
   - Tool execution via gateway
   - Multiple MCP server support
   - Error handling and resilience

"""
    print(info)


async def run_specific_suite(suite_name: str, verbose: bool = False):
    """Run a specific test suite."""
    runner = TestRunner()

    suite_map = {
        "k8s": K8sFoundationTestSuite,
        "agents": AgentDeploymentTestSuite,
        "a2a": A2ACommunicationTestSuite,
        "gateway": AgentGatewayMCPTestSuite,
    }

    if suite_name not in suite_map:
        print(f"❌ Unknown suite: {suite_name}")
        print(f"Available suites: {', '.join(suite_map.keys())}")
        return False

    suite_class = suite_map[suite_name]
    runner.add_suite(suite_class())

    print(f"\n🎯 Running {suite_name.upper()} test suite only...\n")
    success = await runner.run_all_tests()
    return success


async def run_all_suites(verbose: bool = False):
    """Run all test suites in sequence."""
    runner = TestRunner()

    # Add all test suites in logical order
    runner.add_suite(K8sFoundationTestSuite())
    runner.add_suite(AgentDeploymentTestSuite())
    runner.add_suite(A2ACommunicationTestSuite())
    runner.add_suite(AgentGatewayMCPTestSuite())

    print("\n🚀 Running complete integration test suite...\n")
    success = await runner.run_all_tests()
    return success


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Distributed Agent Architecture Integration Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--suite",
        choices=["k8s", "agents", "a2a", "gateway", "all"],
        default="all",
        help="Test suite to run (default: all)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Show information about test suites and exit",
    )

    args = parser.parse_args()

    print_banner()

    if args.info:
        print_suite_info()
        return 0

    try:
        if args.suite == "all":
            success = asyncio.run(run_all_suites(args.verbose))
        else:
            success = asyncio.run(run_specific_suite(args.suite, args.verbose))

        if success:
            print("\n✅ All tests completed successfully!")
            print("\n🎉 Distributed agent architecture is ready for production!")
            return 0
        else:
            print("\n❌ Some tests failed. Check output above for details.")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
