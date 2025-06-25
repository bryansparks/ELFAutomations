#!/usr/bin/env python3
"""
AI Workflow Generation Demo

Demonstrates the enhanced N8N workflow factory with AI capabilities.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.n8n.context_loader import N8NContextLoader
from elf_automations.shared.n8n.workflow_analyzer import WorkflowAnalyzer
from tools.n8n_workflow_factory_v3 import AIEnhancedWorkflowFactory


async def demo_ai_customer_support():
    """Demo: AI-powered customer support workflow"""

    print("\n" + "=" * 60)
    print("🤖 Demo 1: AI Customer Support Workflow")
    print("=" * 60)

    factory = AIEnhancedWorkflowFactory(team_name="support-team")

    description = """
    Create an AI-powered customer support workflow that:
    - Monitors emails and Slack messages
    - Uses AI to understand and categorize inquiries
    - Searches knowledge base using RAG
    - Generates appropriate responses
    - Escalates complex issues to humans
    - Maintains conversation history
    """

    result = await factory.create_ai_workflow(
        description=description,
        name="AI Customer Support Agent",
        team="support-team",
        category="ai-support",
    )

    print("\n✅ Generated Workflow:")
    print(json.dumps(result["workflow"], indent=2))

    print("\n📊 Metadata:")
    print(json.dumps(result["metadata"], indent=2))

    return result["workflow"]


async def demo_document_analysis():
    """Demo: Document analysis with RAG"""

    print("\n" + "=" * 60)
    print("📄 Demo 2: Document Analysis with RAG")
    print("=" * 60)

    factory = AIEnhancedWorkflowFactory(team_name="research-team")

    description = """
    Build a document analysis workflow that:
    - Accepts PDF/Word documents via webhook
    - Extracts and chunks text content
    - Creates embeddings and stores in vector database
    - Allows semantic search queries
    - Uses AI to answer questions about the documents
    - Generates summaries and insights
    """

    result = await factory.create_ai_workflow(
        description=description,
        name="Document Analysis RAG System",
        team="research-team",
        category="ai-analysis",
    )

    print("\n✅ Generated Workflow:")
    print(f"- Nodes: {len(result['workflow']['nodes'])}")
    print(f"- AI Pattern: {result['metadata'].get('ai_pattern')}")
    print(
        f"- Includes Vector Store: {any('vectorStore' in n.get('type', '') for n in result['workflow']['nodes'])}"
    )

    return result["workflow"]


async def demo_multi_agent_research():
    """Demo: Multi-agent research team"""

    print("\n" + "=" * 60)
    print("👥 Demo 3: Multi-Agent Research Team")
    print("=" * 60)

    factory = AIEnhancedWorkflowFactory(team_name="research-team")

    description = """
    Create a multi-agent research workflow where:
    - A coordinator agent receives research requests
    - A researcher agent gathers information from multiple sources
    - An analyst agent processes and synthesizes findings
    - A writer agent creates a comprehensive report
    - All agents collaborate and share context
    - Human approval required before final publication
    """

    result = await factory.create_ai_workflow(
        description=description,
        name="Multi-Agent Research System",
        team="research-team",
        category="ai-orchestration",
    )

    print("\n✅ Generated Multi-Agent Workflow:")
    print(f"- Total Nodes: {len(result['workflow']['nodes'])}")
    print(
        f"- AI Agents: {len([n for n in result['workflow']['nodes'] if 'agent' in n.get('type', '')])}"
    )
    print(
        f"- Has Human-in-Loop: {any('wait' in n.get('type', '') for n in result['workflow']['nodes'])}"
    )

    return result["workflow"]


async def analyze_workflow(workflow):
    """Analyze a workflow for issues and optimizations"""

    print("\n" + "=" * 60)
    print("🔍 Workflow Analysis")
    print("=" * 60)

    analyzer = WorkflowAnalyzer()
    issues, metrics = analyzer.analyze_workflow(workflow)
    suggestions = analyzer.suggest_optimizations(workflow, issues)

    print(f"\n📈 Metrics:")
    print(f"  - Nodes: {metrics.node_count}")
    print(f"  - Connections: {metrics.connection_count}")
    print(f"  - Complexity Score: {metrics.complexity_score:.1f}")
    print(f"  - Est. Execution Time: {metrics.estimated_execution_time:.2f}s")
    print(f"  - Est. Cost per Run: ${metrics.estimated_cost_per_run:.4f}")
    print(f"  - AI Nodes: {metrics.ai_node_count}")

    if issues:
        print(f"\n⚠️  Issues Found ({len(issues)}):")
        for issue in issues[:5]:  # Show first 5 issues
            print(f"  - [{issue.severity.value}] {issue.title}")
            print(f"    {issue.recommendation}")

    if suggestions:
        print(f"\n💡 Optimization Suggestions:")
        for suggestion in suggestions:
            print(f"  - {suggestion.title}")
            print(f"    Expected: {suggestion.expected_improvement}")


async def demo_context_loading():
    """Demo: Context-aware workflow generation"""

    print("\n" + "=" * 60)
    print("📚 Demo 4: Context-Aware Generation")
    print("=" * 60)

    loader = N8NContextLoader()

    description = "Create a workflow for customer support with AI and knowledge base"
    context = loader.get_relevant_context(description)

    print("\n📋 Relevant Context Found:")
    print(f"- Patterns: {len(context['relevant_patterns'])}")
    print(f"- Similar Examples: {len(context['similar_examples'])}")
    print(f"- Recommended Nodes: {[n['type'] for n in context['recommended_nodes']]}")
    print(f"- Best Practices: {len(context['best_practices'])}")

    if context["warnings"]:
        print(f"\n⚠️  Warnings:")
        for warning in context["warnings"]:
            print(f"  - {warning}")


async def main():
    """Run all demos"""

    print("\n🚀 N8N AI Workflow Generation Demo")
    print("This demonstrates the enhanced workflow factory with:")
    print("- AI agent support (LangChain integration)")
    print("- RAG patterns with vector stores")
    print("- Multi-agent orchestration")
    print("- Safety controls and best practices")
    print("- Workflow analysis and optimization")

    # Run demos
    workflow1 = await demo_ai_customer_support()
    await analyze_workflow(workflow1)

    workflow2 = await demo_document_analysis()
    await analyze_workflow(workflow2)

    workflow3 = await demo_multi_agent_research()
    await analyze_workflow(workflow3)

    await demo_context_loading()

    print("\n✅ Demo Complete!")
    print("\nNext steps:")
    print("1. Deploy these workflows to N8N")
    print("2. Configure credentials for AI providers")
    print("3. Test with real data")
    print("4. Monitor performance and costs")
    print("5. Iterate based on analysis results")


if __name__ == "__main__":
    asyncio.run(main())
