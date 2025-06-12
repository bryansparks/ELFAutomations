#!/usr/bin/env python3
"""
Comprehensive Integration Test Runner for ELF Automations
Tests the complete distributed agent architecture:
- K8s base infrastructure
- kagent agent deployment
- A2A communication
- AgentGateway + MCP integration
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_runner")


class TestStatus(Enum):
    """Test execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class TestResult:
    """Individual test result."""

    name: str
    status: TestStatus
    duration: float
    message: str = ""
    details: Optional[Dict] = None


class TestSuite:
    """Base class for test suites."""

    def __init__(self, name: str):
        self.name = name
        self.results: List[TestResult] = []

    async def run_tests(self) -> List[TestResult]:
        """Run all tests in this suite."""
        raise NotImplementedError

    def add_result(
        self,
        name: str,
        status: TestStatus,
        duration: float,
        message: str = "",
        details: Optional[Dict] = None,
    ):
        """Add a test result."""
        self.results.append(TestResult(name, status, duration, message, details))


class TestRunner:
    """Main test runner with pretty output."""

    def __init__(self):
        self.suites: List[TestSuite] = []
        self.start_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0

    def add_suite(self, suite: TestSuite):
        """Add a test suite."""
        self.suites.append(suite)

    def print_header(self):
        """Print test runner header."""
        print("\n" + "=" * 80)
        print("🧪 ELF AUTOMATIONS - COMPREHENSIVE INTEGRATION TEST SUITE")
        print("=" * 80)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Testing: Distributed Agent Architecture")
        print("   • K8s Base Infrastructure")
        print("   • kagent Agent Deployment")
        print("   • A2A Communication Protocol")
        print("   • AgentGateway + MCP Integration")
        print("=" * 80)

    def print_suite_header(self, suite_name: str):
        """Print test suite header."""
        print(f"\n📦 {suite_name}")
        print("-" * (len(suite_name) + 4))

    def print_test_result(self, result: TestResult):
        """Print individual test result with pretty formatting."""
        status_icons = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.RUNNING: "🔄",
        }

        icon = status_icons.get(result.status, "❓")
        duration_str = f"({result.duration:.2f}s)" if result.duration > 0 else ""

        print(f"  {icon} {result.name} {duration_str}")

        if result.message:
            print(f"     💬 {result.message}")

        if result.details:
            for key, value in result.details.items():
                print(f"     📋 {key}: {value}")

    def print_summary(self):
        """Print test execution summary."""
        duration = time.time() - self.start_time if self.start_time else 0

        print("\n" + "=" * 80)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total Duration: {duration:.2f}s")
        print(f"📈 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"⏭️  Skipped: {self.skipped_tests}")

        success_rate = (
            (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        )
        print(f"📊 Success Rate: {success_rate:.1f}%")

        if self.failed_tests == 0:
            print(
                "\n🎉 ALL TESTS PASSED! Your distributed agent architecture is ready! 🚀"
            )
        else:
            print(
                f"\n⚠️  {self.failed_tests} test(s) failed. Please review the results above."
            )

        print("=" * 80)

    async def run_all_tests(self) -> bool:
        """Run all test suites."""
        self.start_time = time.time()
        self.print_header()

        all_passed = True

        for suite in self.suites:
            self.print_suite_header(suite.name)

            try:
                results = await suite.run_tests()

                for result in results:
                    self.print_test_result(result)
                    self.total_tests += 1

                    if result.status == TestStatus.PASSED:
                        self.passed_tests += 1
                    elif result.status == TestStatus.FAILED:
                        self.failed_tests += 1
                        all_passed = False
                    elif result.status == TestStatus.SKIPPED:
                        self.skipped_tests += 1

            except Exception as e:
                logger.error(f"Test suite {suite.name} failed with exception: {e}")
                self.print_test_result(
                    TestResult(
                        f"{suite.name} (SUITE ERROR)",
                        TestStatus.FAILED,
                        0,
                        f"Suite execution failed: {str(e)}",
                    )
                )
                self.total_tests += 1
                self.failed_tests += 1
                all_passed = False

        self.print_summary()
        return all_passed


# Utility functions for tests
async def run_command(cmd: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
    """Run a command and return success, stdout, stderr."""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

        return (
            process.returncode == 0,
            stdout.decode() if stdout else "",
            stderr.decode() if stderr else "",
        )
    except asyncio.TimeoutError:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


async def check_http_endpoint(
    url: str, timeout: int = 10, expected_status: int = 200
) -> Tuple[bool, str]:
    """Check if HTTP endpoint is accessible."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            if response.status_code == expected_status:
                return True, f"Status: {response.status_code}"
            else:
                return False, f"Expected {expected_status}, got {response.status_code}"
    except Exception as e:
        return False, str(e)


async def wait_for_condition(
    condition_func, timeout: int = 60, interval: int = 2
) -> bool:
    """Wait for a condition to become true."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            if await condition_func():
                return True
        except Exception:
            pass
        await asyncio.sleep(interval)

    return False


from .test_a2a_communication import A2ACommunicationTestSuite
from .test_agent_deployment import AgentDeploymentTestSuite
from .test_agentgateway_mcp import AgentGatewayMCPTestSuite
from .test_k8s_foundation import K8sFoundationTestSuite


async def main():
    """Main test runner entry point."""
    runner = TestRunner()

    # Add all test suites
    runner.add_suite(K8sFoundationTestSuite())
    runner.add_suite(AgentDeploymentTestSuite())
    runner.add_suite(A2ACommunicationTestSuite())
    runner.add_suite(AgentGatewayMCPTestSuite())

    # Run all tests
    success = await runner.run_all_tests()
    return success


if __name__ == "__main__":
    asyncio.run(main())
