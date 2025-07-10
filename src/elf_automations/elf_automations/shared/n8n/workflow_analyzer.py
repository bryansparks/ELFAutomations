"""
N8N Workflow Analyzer

Analyzes workflows for optimization opportunities, security issues, and best practices.
Provides recommendations for improvements and cost optimization.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class IssueType(Enum):
    """Types of issues that can be detected"""

    PERFORMANCE = "performance"
    SECURITY = "security"
    COST = "cost"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best_practice"


class IssueSeverity(Enum):
    """Severity levels for detected issues"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class WorkflowIssue:
    """Represents an issue found in a workflow"""

    type: IssueType
    severity: IssueSeverity
    node_id: Optional[str]
    title: str
    description: str
    recommendation: str
    estimated_impact: Optional[str] = None


@dataclass
class OptimizationSuggestion:
    """Represents an optimization suggestion"""

    title: str
    description: str
    expected_improvement: str
    implementation_steps: List[str]
    complexity: str  # "low", "medium", "high"


@dataclass
class WorkflowMetrics:
    """Metrics calculated from workflow analysis"""

    node_count: int
    connection_count: int
    complexity_score: float
    estimated_execution_time: float
    estimated_cost_per_run: float
    parallel_execution_opportunities: int
    ai_node_count: int
    external_api_calls: int
    database_operations: int


class WorkflowAnalyzer:
    """Analyzes N8N workflows for issues and optimization opportunities"""

    def __init__(self):
        # Define node costs (approximate)
        self.node_costs = {
            "n8n-nodes-base.webhook": 0.00001,
            "n8n-nodes-base.httpRequest": 0.0001,
            "@n8n/n8n-nodes-langchain.agent": 0.01,  # AI agents are expensive
            "n8n-nodes-base.postgres": 0.0005,
            "n8n-nodes-base.emailSend": 0.0002,
            "n8n-nodes-base.slack": 0.0001,
            "@n8n/n8n-nodes-langchain.vectorStore": 0.001,
        }

        # Define node execution times (seconds)
        self.node_times = {
            "n8n-nodes-base.webhook": 0.01,
            "n8n-nodes-base.httpRequest": 0.5,
            "@n8n/n8n-nodes-langchain.agent": 3.0,
            "n8n-nodes-base.postgres": 0.2,
            "n8n-nodes-base.code": 0.05,
        }

    def analyze_workflow(
        self, workflow: Dict[str, Any]
    ) -> Tuple[List[WorkflowIssue], WorkflowMetrics]:
        """Analyze a workflow and return issues and metrics"""

        issues = []

        # Calculate basic metrics
        metrics = self._calculate_metrics(workflow)

        # Run various checks
        issues.extend(self._check_security_issues(workflow))
        issues.extend(self._check_performance_issues(workflow, metrics))
        issues.extend(self._check_reliability_issues(workflow))
        issues.extend(self._check_cost_issues(workflow, metrics))
        issues.extend(self._check_best_practices(workflow))
        issues.extend(self._check_ai_specific_issues(workflow))

        return issues, metrics

    def _calculate_metrics(self, workflow: Dict[str, Any]) -> WorkflowMetrics:
        """Calculate workflow metrics"""

        nodes = workflow.get("nodes", [])
        connections = workflow.get("connections", {})

        # Count connections
        connection_count = sum(
            len(outputs.get("main", [[]])[0]) for outputs in connections.values()
        )

        # Calculate complexity (nodes + connections + branches)
        branch_count = len(
            [
                n
                for n in nodes
                if n.get("type") in ["n8n-nodes-base.if", "n8n-nodes-base.switch"]
            ]
        )
        complexity_score = len(nodes) + connection_count + (branch_count * 2)

        # Count specific node types
        ai_nodes = [n for n in nodes if "@n8n/n8n-nodes-langchain" in n.get("type", "")]
        api_nodes = [n for n in nodes if n.get("type") == "n8n-nodes-base.httpRequest"]
        db_nodes = [
            n
            for n in nodes
            if n.get("type") in ["n8n-nodes-base.postgres", "n8n-nodes-base.supabase"]
        ]

        # Estimate execution time
        total_time = sum(
            self.node_times.get(node.get("type", ""), 0.1) for node in nodes
        )

        # Estimate cost
        total_cost = sum(
            self.node_costs.get(node.get("type", ""), 0.0001) for node in nodes
        )

        # Find parallel opportunities
        parallel_opportunities = self._find_parallel_opportunities(workflow)

        return WorkflowMetrics(
            node_count=len(nodes),
            connection_count=connection_count,
            complexity_score=complexity_score,
            estimated_execution_time=total_time,
            estimated_cost_per_run=total_cost,
            parallel_execution_opportunities=parallel_opportunities,
            ai_node_count=len(ai_nodes),
            external_api_calls=len(api_nodes),
            database_operations=len(db_nodes),
        )

    def _check_security_issues(self, workflow: Dict[str, Any]) -> List[WorkflowIssue]:
        """Check for security issues"""

        issues = []
        nodes = workflow.get("nodes", [])

        for node in nodes:
            node_type = node.get("type", "")
            node_id = node.get("id", node.get("name", "unknown"))
            params = node.get("parameters", {})

            # Check for hardcoded credentials
            if self._contains_credentials(params):
                issues.append(
                    WorkflowIssue(
                        type=IssueType.SECURITY,
                        severity=IssueSeverity.CRITICAL,
                        node_id=node_id,
                        title="Hardcoded Credentials Detected",
                        description=f"Node '{node_id}' contains hardcoded credentials",
                        recommendation="Use n8n credentials system instead of hardcoding sensitive data",
                    )
                )

            # Check for unencrypted HTTP requests
            if node_type == "n8n-nodes-base.httpRequest":
                url = params.get("url", "")
                if url.startswith("http://") and "localhost" not in url:
                    issues.append(
                        WorkflowIssue(
                            type=IssueType.SECURITY,
                            severity=IssueSeverity.HIGH,
                            node_id=node_id,
                            title="Unencrypted HTTP Request",
                            description=f"Node '{node_id}' makes unencrypted HTTP request",
                            recommendation="Use HTTPS for external API calls",
                        )
                    )

            # Check for missing authentication
            if node_type == "n8n-nodes-base.webhook" and not params.get(
                "authentication"
            ):
                issues.append(
                    WorkflowIssue(
                        type=IssueType.SECURITY,
                        severity=IssueSeverity.MEDIUM,
                        node_id=node_id,
                        title="Webhook Without Authentication",
                        description=f"Webhook '{node_id}' has no authentication configured",
                        recommendation="Add authentication to prevent unauthorized access",
                    )
                )

        return issues

    def _check_performance_issues(
        self, workflow: Dict[str, Any], metrics: WorkflowMetrics
    ) -> List[WorkflowIssue]:
        """Check for performance issues"""

        issues = []
        nodes = workflow.get("nodes", [])
        connections = workflow.get("connections", {})

        # Check for sequential operations that could be parallel
        if metrics.parallel_execution_opportunities > 0:
            issues.append(
                WorkflowIssue(
                    type=IssueType.PERFORMANCE,
                    severity=IssueSeverity.MEDIUM,
                    node_id=None,
                    title="Parallel Execution Opportunities",
                    description=f"Found {metrics.parallel_execution_opportunities} operations that could run in parallel",
                    recommendation="Use Split In Batches or parallel execution patterns",
                    estimated_impact=f"Could reduce execution time by up to {metrics.parallel_execution_opportunities * 20}%",
                )
            )

        # Check for inefficient loops
        code_nodes = [n for n in nodes if n.get("type") == "n8n-nodes-base.code"]
        for node in code_nodes:
            code = node.get("parameters", {}).get("jsCode", "")
            if "for" in code and "await" in code:
                issues.append(
                    WorkflowIssue(
                        type=IssueType.PERFORMANCE,
                        severity=IssueSeverity.HIGH,
                        node_id=node.get("id"),
                        title="Inefficient Async Loop",
                        description="Sequential await in loop detected",
                        recommendation="Use Promise.all() for parallel async operations",
                    )
                )

        # Check for missing pagination
        db_nodes = [
            n
            for n in nodes
            if n.get("type") in ["n8n-nodes-base.postgres", "n8n-nodes-base.supabase"]
        ]
        for node in db_nodes:
            if node.get("parameters", {}).get("operation") == "select" and not node.get(
                "parameters", {}
            ).get("limit"):
                issues.append(
                    WorkflowIssue(
                        type=IssueType.PERFORMANCE,
                        severity=IssueSeverity.MEDIUM,
                        node_id=node.get("id"),
                        title="Unbounded Database Query",
                        description="Database query without limit could return excessive data",
                        recommendation="Add pagination or limit to database queries",
                    )
                )

        return issues

    def _check_reliability_issues(
        self, workflow: Dict[str, Any]
    ) -> List[WorkflowIssue]:
        """Check for reliability issues"""

        issues = []
        nodes = workflow.get("nodes", [])
        settings = workflow.get("settings", {})

        # Check for missing error handling
        if not settings.get("errorWorkflow"):
            issues.append(
                WorkflowIssue(
                    type=IssueType.RELIABILITY,
                    severity=IssueSeverity.HIGH,
                    node_id=None,
                    title="No Error Workflow Configured",
                    description="Workflow has no error handling configured",
                    recommendation="Add an error workflow to handle failures gracefully",
                )
            )

        # Check for missing retries on HTTP requests
        http_nodes = [n for n in nodes if n.get("type") == "n8n-nodes-base.httpRequest"]
        for node in http_nodes:
            if not node.get("parameters", {}).get("options", {}).get("retry"):
                issues.append(
                    WorkflowIssue(
                        type=IssueType.RELIABILITY,
                        severity=IssueSeverity.MEDIUM,
                        node_id=node.get("id"),
                        title="HTTP Request Without Retry",
                        description="HTTP request has no retry configuration",
                        recommendation="Add retry logic for better reliability",
                    )
                )

        # Check for missing timeouts
        for node in http_nodes:
            if not node.get("parameters", {}).get("options", {}).get("timeout"):
                issues.append(
                    WorkflowIssue(
                        type=IssueType.RELIABILITY,
                        severity=IssueSeverity.LOW,
                        node_id=node.get("id"),
                        title="HTTP Request Without Timeout",
                        description="HTTP request has no timeout configured",
                        recommendation="Set appropriate timeout to prevent hanging",
                    )
                )

        return issues

    def _check_cost_issues(
        self, workflow: Dict[str, Any], metrics: WorkflowMetrics
    ) -> List[WorkflowIssue]:
        """Check for cost optimization opportunities"""

        issues = []
        nodes = workflow.get("nodes", [])

        # Check for expensive AI operations
        if metrics.ai_node_count > 0 and metrics.estimated_cost_per_run > 0.05:
            issues.append(
                WorkflowIssue(
                    type=IssueType.COST,
                    severity=IssueSeverity.HIGH,
                    node_id=None,
                    title="High AI Operation Cost",
                    description=f"Workflow uses {metrics.ai_node_count} AI nodes with estimated cost ${metrics.estimated_cost_per_run:.4f} per run",
                    recommendation="Consider using cheaper models or caching AI responses",
                    estimated_impact=f"Current cost: ${metrics.estimated_cost_per_run * 1000:.2f} per 1000 runs",
                )
            )

        # Check for redundant AI calls
        ai_nodes = [n for n in nodes if "@n8n/n8n-nodes-langchain" in n.get("type", "")]
        if len(ai_nodes) > 1:
            issues.append(
                WorkflowIssue(
                    type=IssueType.COST,
                    severity=IssueSeverity.MEDIUM,
                    node_id=None,
                    title="Multiple AI Calls",
                    description="Workflow makes multiple AI calls that might be combinable",
                    recommendation="Consider combining AI operations into a single call",
                )
            )

        # Check for unnecessary data fetching
        if metrics.database_operations > 3:
            issues.append(
                WorkflowIssue(
                    type=IssueType.COST,
                    severity=IssueSeverity.LOW,
                    node_id=None,
                    title="Multiple Database Operations",
                    description=f"Workflow performs {metrics.database_operations} database operations",
                    recommendation="Consider batching database operations or using joins",
                )
            )

        return issues

    def _check_best_practices(self, workflow: Dict[str, Any]) -> List[WorkflowIssue]:
        """Check for best practice violations"""

        issues = []
        nodes = workflow.get("nodes", [])

        # Check for missing workflow description
        if not workflow.get("name"):
            issues.append(
                WorkflowIssue(
                    type=IssueType.BEST_PRACTICE,
                    severity=IssueSeverity.LOW,
                    node_id=None,
                    title="Missing Workflow Name",
                    description="Workflow has no descriptive name",
                    recommendation="Add a clear, descriptive name to the workflow",
                )
            )

        # Check for missing node names
        for node in nodes:
            if not node.get("name") or node.get("name") == node.get("type"):
                issues.append(
                    WorkflowIssue(
                        type=IssueType.BEST_PRACTICE,
                        severity=IssueSeverity.LOW,
                        node_id=node.get("id"),
                        title="Generic Node Name",
                        description=f"Node has generic or missing name",
                        recommendation="Use descriptive names for nodes",
                    )
                )

        # Check workflow complexity
        if len(nodes) > 20:
            issues.append(
                WorkflowIssue(
                    type=IssueType.MAINTAINABILITY,
                    severity=IssueSeverity.MEDIUM,
                    node_id=None,
                    title="Complex Workflow",
                    description=f"Workflow has {len(nodes)} nodes, consider breaking it down",
                    recommendation="Split into sub-workflows for better maintainability",
                )
            )

        return issues

    def _check_ai_specific_issues(
        self, workflow: Dict[str, Any]
    ) -> List[WorkflowIssue]:
        """Check for AI-specific issues"""

        issues = []
        nodes = workflow.get("nodes", [])

        ai_nodes = [n for n in nodes if "@n8n/n8n-nodes-langchain" in n.get("type", "")]

        for node in ai_nodes:
            params = node.get("parameters", {})

            # Check for missing temperature settings
            if "agent" in node.get("type", "") and not params.get("options", {}).get(
                "temperature"
            ):
                issues.append(
                    WorkflowIssue(
                        type=IssueType.BEST_PRACTICE,
                        severity=IssueSeverity.LOW,
                        node_id=node.get("id"),
                        title="AI Agent Without Temperature Setting",
                        description="AI agent uses default temperature",
                        recommendation="Set appropriate temperature for consistent results",
                    )
                )

            # Check for missing max tokens
            if not params.get("options", {}).get("maxTokens"):
                issues.append(
                    WorkflowIssue(
                        type=IssueType.COST,
                        severity=IssueSeverity.MEDIUM,
                        node_id=node.get("id"),
                        title="AI Without Token Limit",
                        description="AI node has no token limit set",
                        recommendation="Set maxTokens to control costs",
                    )
                )

            # Check for missing error handling on AI nodes
            node_name = node.get("name", node.get("id"))
            connections = workflow.get("connections", {})
            if node_name in connections:
                outputs = connections[node_name].get("main", [[]])
                if len(outputs) < 2:  # No error output configured
                    issues.append(
                        WorkflowIssue(
                            type=IssueType.RELIABILITY,
                            severity=IssueSeverity.HIGH,
                            node_id=node.get("id"),
                            title="AI Node Without Error Handling",
                            description="AI node has no error output configured",
                            recommendation="Add error handling for AI failures",
                        )
                    )

        return issues

    def _contains_credentials(self, obj: Any) -> bool:
        """Check if object contains potential credentials"""

        if isinstance(obj, str):
            # Check for common credential patterns
            sensitive_patterns = [
                "password",
                "api_key",
                "apikey",
                "secret",
                "token",
                "private_key",
                "privatekey",
                "access_key",
                "accesskey",
            ]
            lower_str = obj.lower()
            return any(pattern in lower_str for pattern in sensitive_patterns)

        elif isinstance(obj, dict):
            return any(self._contains_credentials(v) for v in obj.values())

        elif isinstance(obj, list):
            return any(self._contains_credentials(item) for item in obj)

        return False

    def _find_parallel_opportunities(self, workflow: Dict[str, Any]) -> int:
        """Find operations that could be executed in parallel"""

        connections = workflow.get("connections", {})
        opportunities = 0

        # Look for nodes with multiple outputs to same target
        for node_name, outputs in connections.items():
            main_outputs = outputs.get("main", [[]])[0] if outputs.get("main") else []

            # Group by target node
            targets = {}
            for output in main_outputs:
                target = output.get("node")
                if target:
                    targets[target] = targets.get(target, 0) + 1

            # If multiple connections to same target, they might be parallelizable
            opportunities += sum(1 for count in targets.values() if count > 1)

        return opportunities

    def suggest_optimizations(
        self, workflow: Dict[str, Any], issues: List[WorkflowIssue]
    ) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions based on analysis"""

        suggestions = []

        # Group issues by type
        perf_issues = [i for i in issues if i.type == IssueType.PERFORMANCE]
        cost_issues = [i for i in issues if i.type == IssueType.COST]

        # Performance optimizations
        if perf_issues:
            suggestions.append(
                OptimizationSuggestion(
                    title="Implement Parallel Processing",
                    description="Convert sequential operations to parallel execution",
                    expected_improvement="30-50% reduction in execution time",
                    implementation_steps=[
                        "Identify independent operations",
                        "Use Split In Batches node for parallel processing",
                        "Implement proper merging of results",
                        "Test with various batch sizes",
                    ],
                    complexity="medium",
                )
            )

        # Cost optimizations
        if cost_issues:
            suggestions.append(
                OptimizationSuggestion(
                    title="Implement AI Response Caching",
                    description="Cache AI responses for similar queries",
                    expected_improvement="Up to 80% cost reduction for repeated queries",
                    implementation_steps=[
                        "Add cache check before AI calls",
                        "Implement cache storage (Redis/Supabase)",
                        "Set appropriate TTL for cached responses",
                        "Monitor cache hit rates",
                    ],
                    complexity="medium",
                )
            )

        # General optimizations
        if len(workflow.get("nodes", [])) > 15:
            suggestions.append(
                OptimizationSuggestion(
                    title="Refactor into Sub-workflows",
                    description="Break down complex workflow into manageable sub-workflows",
                    expected_improvement="Improved maintainability and reusability",
                    implementation_steps=[
                        "Identify logical groupings of nodes",
                        "Create sub-workflows for each group",
                        "Use Execute Workflow nodes to connect them",
                        "Implement proper error handling between workflows",
                    ],
                    complexity="high",
                )
            )

        return suggestions


def analyze_workflow_file(file_path: str) -> None:
    """Analyze a workflow file and print results"""

    with open(file_path, "r") as f:
        workflow = json.load(f)

    analyzer = WorkflowAnalyzer()
    issues, metrics = analyzer.analyze_workflow(workflow)
    suggestions = analyzer.suggest_optimizations(workflow, issues)

    print(f"\n📊 Workflow Analysis: {workflow.get('name', 'Unnamed')}")
    print("=" * 60)

    print(f"\n📈 Metrics:")
    print(f"  - Nodes: {metrics.node_count}")
    print(f"  - Connections: {metrics.connection_count}")
    print(f"  - Complexity Score: {metrics.complexity_score:.1f}")
    print(f"  - Est. Execution Time: {metrics.estimated_execution_time:.2f}s")
    print(f"  - Est. Cost per Run: ${metrics.estimated_cost_per_run:.4f}")
    print(f"  - AI Nodes: {metrics.ai_node_count}")

    if issues:
        print(f"\n⚠️  Issues Found ({len(issues)}):")

        # Group by severity
        for severity in IssueSeverity:
            severity_issues = [i for i in issues if i.severity == severity]
            if severity_issues:
                print(f"\n  {severity.value.upper()}:")
                for issue in severity_issues:
                    print(f"    - [{issue.type.value}] {issue.title}")
                    print(f"      {issue.description}")
                    print(f"      → {issue.recommendation}")
                    if issue.estimated_impact:
                        print(f"      Impact: {issue.estimated_impact}")

    if suggestions:
        print(f"\n💡 Optimization Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n  {i}. {suggestion.title}")
            print(f"     {suggestion.description}")
            print(f"     Expected: {suggestion.expected_improvement}")
            print(f"     Complexity: {suggestion.complexity}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        analyze_workflow_file(sys.argv[1])
    else:
        print("Usage: python workflow_analyzer.py <workflow.json>")
