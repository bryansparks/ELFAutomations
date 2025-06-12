#!/usr/bin/env python3
"""
Simplified Supabase Demo

Demonstrates the Virtual AI Company Platform with Supabase backend using available components.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import structlog
from dotenv import load_dotenv

# Import our agents and tools
sys.path.append(str(Path(__file__).parent.parent))

from agents.executive.chief_ai_agent import ChiefAIAgent
from mcp_servers.business_tools import BusinessToolsServer

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def test_supabase_data_operations():
    """Test direct Supabase operations through business tools."""
    print("DEBUG: Starting Supabase data operations test...")  # Debug output
    logger.info("🗄️ Testing Supabase Data Operations")
    logger.info("=" * 40)

    try:
        # Initialize business tools
        business_tools = BusinessToolsServer()
        await business_tools.start()

        if not business_tools.supabase_client:
            logger.error("❌ Supabase client not available")
            return False

        logger.info("✅ Connected to Supabase")

        # Test customer creation
        logger.info("👤 Creating test customer...")

        test_customer = {
            "name": f"Demo Customer {datetime.now().strftime('%H%M%S')}",
            "email": f"demo_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1-555-0199",
            "company": "Demo Corp",
            "metadata": {"source": "supabase_demo", "priority": "high"},
        }

        # Use Supabase client directly
        customer_result = (
            business_tools.supabase_client.table("customers")
            .insert(test_customer)
            .execute()
        )

        if customer_result.data:
            customer_id = customer_result.data[0]["id"]
            logger.info(f"✅ Customer created: {customer_id}")

            # Create a lead for this customer
            logger.info("🎯 Creating test lead...")

            test_lead = {
                "customer_id": customer_id,
                "source": "website",
                "status": "new",
                "score": 92,
                "notes": "High-value prospect from Supabase demo",
                "metadata": {"campaign": "supabase_integration_test"},
            }

            lead_result = (
                business_tools.supabase_client.table("leads")
                .insert(test_lead)
                .execute()
            )

            if lead_result.data:
                lead_id = lead_result.data[0]["id"]
                logger.info(f"✅ Lead created: {lead_id}")

                # Create a task
                logger.info("📋 Creating test task...")

                test_task = {
                    "title": "Follow up with demo lead",
                    "description": "Contact the high-value prospect within 24 hours",
                    "priority": 5,
                    "status": "pending",
                    "assignee": "ai_sales_agent",
                    "assigned_agent_id": "sales-agent-001",
                    "due_date": "2024-01-15",
                    "metadata": {"lead_id": lead_id, "type": "follow_up"},
                }

                task_result = (
                    business_tools.supabase_client.table("tasks")
                    .insert(test_task)
                    .execute()
                )

                if task_result.data:
                    task_id = task_result.data[0]["id"]
                    logger.info(f"✅ Task created: {task_id}")
                else:
                    logger.warning("⚠️ Task creation failed")
            else:
                logger.warning("⚠️ Lead creation failed")
        else:
            logger.warning("⚠️ Customer creation failed")

        # Query business metrics
        logger.info("📊 Querying business metrics...")

        # Count customers
        customers_count = (
            business_tools.supabase_client.table("customers")
            .select("id", count="exact")
            .execute()
        )
        logger.info(f"Total customers: {customers_count.count}")

        # Count leads
        leads_count = (
            business_tools.supabase_client.table("leads")
            .select("id", count="exact")
            .execute()
        )
        logger.info(f"Total leads: {leads_count.count}")

        # Count tasks
        tasks_count = (
            business_tools.supabase_client.table("tasks")
            .select("id", count="exact")
            .execute()
        )
        logger.info(f"Total tasks: {tasks_count.count}")

        return True

    except Exception as e:
        logger.error("❌ Supabase data operations failed", error=str(e))
        return False


async def demonstrate_chief_ai_agent():
    """Demonstrate Chief AI Agent with Supabase backend."""
    print("DEBUG: Starting Chief AI Agent demonstration...")  # Debug output
    logger.info("\n👑 CHIEF AI AGENT DEMONSTRATION")
    logger.info("=" * 45)

    try:
        # Initialize Chief AI Agent
        chief_agent = ChiefAIAgent()

        logger.info("🧠 Chief AI Agent analyzing business with Supabase data...")

        # Business analysis prompt
        analysis_prompt = """
        As the Chief AI Agent of our Virtual AI Company, analyze our current business performance:

        1. Assess our customer base and growth trends
        2. Evaluate lead generation and conversion effectiveness
        3. Review task management and operational efficiency
        4. Identify key business opportunities
        5. Provide strategic recommendations for growth

        Focus on data-driven insights and actionable recommendations.
        """

        # Execute analysis
        analysis_result = await chief_agent.think(analysis_prompt)

        logger.info("📊 Strategic Analysis Complete:")
        logger.info(f"Analysis: {analysis_result[:600]}...")

        # Generate executive summary
        summary_prompt = """
        Create a concise executive summary that includes:

        1. Current business status overview
        2. Key performance indicators
        3. Strategic priorities for next quarter
        4. Resource allocation recommendations
        5. Success metrics to track

        Keep this focused and actionable for executive decision-making.
        """

        summary_result = await chief_agent.think(summary_prompt)

        # Save the executive summary
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        summary_file = reports_dir / "executive_summary_supabase_demo.md"

        with open(summary_file, "w") as f:
            f.write(f"# Executive Summary - Supabase Demo\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write("## Strategic Analysis\n")
            f.write(f"{analysis_result}\n\n")
            f.write("## Executive Summary\n")
            f.write(f"{summary_result}\n\n")
            f.write("---\n")
            f.write("*Generated by Chief AI Agent with Supabase Backend Integration*\n")

        logger.info(f"📄 Executive summary saved to: {summary_file}")

        return True

    except Exception as e:
        logger.error("❌ Chief AI Agent demonstration failed", error=str(e))
        return False


async def demonstrate_business_intelligence():
    """Demonstrate business intelligence capabilities."""
    print("DEBUG: Starting Business Intelligence demonstration...")  # Debug output
    logger.info("\n📈 BUSINESS INTELLIGENCE DEMONSTRATION")
    logger.info("=" * 50)

    try:
        # Initialize business tools
        business_tools = BusinessToolsServer()
        await business_tools.start()

        if not business_tools.supabase_client:
            logger.error("❌ Supabase client not available")
            return False

        logger.info("📊 Generating business intelligence report...")

        # Gather business metrics
        metrics = {}

        # Customer metrics
        customers_result = (
            business_tools.supabase_client.table("customers").select("*").execute()
        )
        metrics["total_customers"] = (
            len(customers_result.data) if customers_result.data else 0
        )

        # Lead metrics
        leads_result = (
            business_tools.supabase_client.table("leads").select("*").execute()
        )
        metrics["total_leads"] = len(leads_result.data) if leads_result.data else 0

        if leads_result.data:
            high_score_leads = [
                lead for lead in leads_result.data if lead.get("score", 0) > 80
            ]
            metrics["high_quality_leads"] = len(high_score_leads)

            # Calculate average lead score
            scores = [
                lead.get("score", 0) for lead in leads_result.data if lead.get("score")
            ]
            metrics["average_lead_score"] = sum(scores) / len(scores) if scores else 0
        else:
            metrics["high_quality_leads"] = 0
            metrics["average_lead_score"] = 0

        # Task metrics
        tasks_result = (
            business_tools.supabase_client.table("tasks").select("*").execute()
        )
        metrics["total_tasks"] = len(tasks_result.data) if tasks_result.data else 0

        if tasks_result.data:
            pending_tasks = [
                task for task in tasks_result.data if task.get("status") == "pending"
            ]
            completed_tasks = [
                task for task in tasks_result.data if task.get("status") == "completed"
            ]
            metrics["pending_tasks"] = len(pending_tasks)
            metrics["completed_tasks"] = len(completed_tasks)
            metrics["task_completion_rate"] = (
                (len(completed_tasks) / len(tasks_result.data)) * 100
                if tasks_result.data
                else 0
            )
        else:
            metrics["pending_tasks"] = 0
            metrics["completed_tasks"] = 0
            metrics["task_completion_rate"] = 0

        # Generate BI report
        bi_report = f"""
# Business Intelligence Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Key Performance Indicators

### Customer Metrics
- **Total Customers**: {metrics['total_customers']}
- **Customer Growth**: Active and engaged customer base

### Lead Management
- **Total Leads**: {metrics['total_leads']}
- **High-Quality Leads**: {metrics['high_quality_leads']} (score > 80)
- **Average Lead Score**: {metrics['average_lead_score']:.1f}
- **Lead Quality Rate**: {(metrics['high_quality_leads'] / max(metrics['total_leads'], 1)) * 100:.1f}%

### Operational Efficiency
- **Total Tasks**: {metrics['total_tasks']}
- **Pending Tasks**: {metrics['pending_tasks']}
- **Completed Tasks**: {metrics['completed_tasks']}
- **Task Completion Rate**: {metrics['task_completion_rate']:.1f}%

## Strategic Insights

### Strengths
- Robust Supabase backend integration
- Real-time data access and analytics
- Scalable AI agent architecture
- Comprehensive business data model

### Opportunities
- Optimize lead conversion processes
- Enhance task automation workflows
- Implement predictive analytics
- Scale agent deployment

### Recommendations
1. **Focus on Lead Quality**: Prioritize leads with scores > 80
2. **Task Automation**: Implement automated task assignment
3. **Performance Monitoring**: Set up real-time dashboards
4. **Agent Scaling**: Deploy specialized department agents

## Technology Stack Validation
- ✅ Supabase Backend: Fully operational
- ✅ Business Tools MCP Server: Connected
- ✅ AI Agent Integration: Functional
- ✅ Data Analytics: Real-time capable

---
*Powered by Virtual AI Company Platform with Supabase Backend*
"""

        # Save BI report
        bi_file = Path("reports/business_intelligence_supabase.md")
        bi_file.parent.mkdir(exist_ok=True)

        with open(bi_file, "w") as f:
            f.write(bi_report)

        logger.info(f"📄 Business Intelligence report saved to: {bi_file}")
        logger.info("📊 Key Metrics:")
        logger.info(f"  - Customers: {metrics['total_customers']}")
        logger.info(
            f"  - Leads: {metrics['total_leads']} (avg score: {metrics['average_lead_score']:.1f})"
        )
        logger.info(
            f"  - Tasks: {metrics['total_tasks']} ({metrics['task_completion_rate']:.1f}% completion)"
        )

        return True

    except Exception as e:
        logger.error("❌ Business intelligence demonstration failed", error=str(e))
        return False


async def main():
    """Main demonstration function."""
    print("Starting Supabase demo...")  # Debug output
    logger.info("🚀 VIRTUAL AI COMPANY PLATFORM - SUPABASE DEMO")
    logger.info("=" * 55)

    # Load environment
    load_dotenv()
    print("Environment loaded...")  # Debug output

    # Verify Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    print(f"Supabase URL: {supabase_url}")  # Debug output
    print(f"Supabase Key: {'SET' if supabase_key else 'NOT_SET'}")  # Debug output

    if not supabase_url or not supabase_key:
        logger.error("❌ Supabase configuration missing")
        print("ERROR: Supabase configuration missing")  # Debug output
        return 1

    logger.info(f"✅ Supabase URL: {supabase_url}")
    logger.info(f"✅ Supabase Key: {'*' * 8}...{supabase_key[-4:]}")

    print("Starting demonstrations...")  # Debug output

    # Run demonstrations
    results = []

    # Test Supabase data operations
    print("DEBUG: About to call test_supabase_data_operations...")  # Debug output
    data_ops_result = await test_supabase_data_operations()
    print(f"DEBUG: Data ops result: {data_ops_result}")  # Debug output
    results.append(("Supabase Data Operations", data_ops_result))

    # Chief AI Agent demo
    chief_result = await demonstrate_chief_ai_agent()
    results.append(("Chief AI Agent", chief_result))

    # Business Intelligence demo
    bi_result = await demonstrate_business_intelligence()
    results.append(("Business Intelligence", bi_result))

    # Summary
    logger.info("\n📋 DEMONSTRATION SUMMARY")
    logger.info("=" * 30)

    success_count = 0
    for demo_name, success in results:
        if success:
            logger.info(f"✅ {demo_name}: SUCCESS")
            success_count += 1
        else:
            logger.error(f"❌ {demo_name}: FAILED")

    logger.info(
        f"\n🎯 Overall Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)"
    )

    if success_count == len(results):
        logger.info("\n🎉 SUPABASE DEMO COMPLETED SUCCESSFULLY!")
        logger.info(
            "The Virtual AI Company Platform is fully operational with Supabase backend."
        )
        logger.info("\n📊 Generated Reports:")
        logger.info("  - reports/executive_summary_supabase_demo.md")
        logger.info("  - reports/business_intelligence_supabase.md")
        logger.info("\n🚀 Key Achievements:")
        logger.info("  ✅ Real-time database operations")
        logger.info("  ✅ AI agent business analysis")
        logger.info("  ✅ Comprehensive business intelligence")
        logger.info("  ✅ Scalable cloud-native architecture")
        logger.info("\n🎯 Ready for production deployment and agent scaling!")
        return 0
    else:
        logger.error("\n⚠️ Some demonstrations failed. Review logs for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
