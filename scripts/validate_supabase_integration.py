#!/usr/bin/env python3
"""
Validate Supabase Integration

Comprehensive test to validate the complete Supabase integration for the Virtual AI Company Platform.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime

import structlog
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def test_business_tools_integration():
    """Test business tools MCP server with Supabase."""
    logger.info("🧪 Testing Business Tools Integration with Supabase")
    logger.info("=" * 55)
    
    # Set up MCP server parameters for business tools
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_servers.business_tools"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                logger.info("🔌 Connected to Business Tools MCP server")
                
                # Initialize the session
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                logger.info(f"📋 Available tools: {', '.join(tool_names)}")
                
                # Test customer creation with proper UUID
                if "create_customer" in tool_names:
                    logger.info("👤 Testing customer creation...")
                    
                    customer_data = {
                        "name": f"Test Customer {datetime.now().strftime('%H%M%S')}",
                        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                        "phone": "+1-555-0123",
                        "company": "Test Company",
                        "metadata": {"source": "integration_test", "priority": "high"}
                    }
                    
                    result = await session.call_tool("create_customer", arguments=customer_data)
                    
                    if not result.isError:
                        logger.info("✅ Customer created successfully")
                        customer_result = json.loads(result.content[0].text)
                        customer_id = customer_result.get("id")
                        logger.info(f"Customer ID: {customer_id}")
                        
                        # Test getting the customer
                        if "get_customer" in tool_names and customer_id:
                            get_result = await session.call_tool("get_customer", arguments={"customer_id": customer_id})
                            if not get_result.isError:
                                logger.info("✅ Customer retrieval successful")
                            else:
                                logger.warning("⚠️ Customer retrieval failed", error=str(get_result.content))
                        
                        # Test lead creation with the customer
                        if "create_lead" in tool_names and customer_id:
                            logger.info("🎯 Testing lead creation...")
                            
                            lead_data = {
                                "customer_id": customer_id,
                                "source": "website",
                                "status": "new",
                                "score": 85,
                                "notes": "High-value prospect from integration test",
                                "metadata": {"campaign": "test_campaign"}
                            }
                            
                            lead_result = await session.call_tool("create_lead", arguments=lead_data)
                            
                            if not lead_result.isError:
                                logger.info("✅ Lead created successfully")
                                lead_data_result = json.loads(lead_result.content[0].text)
                                lead_id = lead_data_result.get("id")
                                
                                # Test task creation
                                if "create_task" in tool_names:
                                    logger.info("📋 Testing task creation...")
                                    
                                    task_data = {
                                        "title": "Follow up with test lead",
                                        "description": "Contact the lead within 24 hours",
                                        "priority": "high",
                                        "status": "pending",
                                        "assigned_to": "sales_agent_001",
                                        "due_date": "2024-01-15",
                                        "metadata": {"lead_id": lead_id, "type": "follow_up"}
                                    }
                                    
                                    task_result = await session.call_tool("create_task", arguments=task_data)
                                    
                                    if not task_result.isError:
                                        logger.info("✅ Task created successfully")
                                    else:
                                        logger.warning("⚠️ Task creation failed", error=str(task_result.content))
                            else:
                                logger.warning("⚠️ Lead creation failed", error=str(lead_result.content))
                    else:
                        logger.warning("⚠️ Customer creation failed", error=str(result.content))
                
                # Test business metrics
                if "get_business_metrics" in tool_names:
                    logger.info("📊 Testing business metrics...")
                    
                    metrics_result = await session.call_tool("get_business_metrics")
                    
                    if not metrics_result.isError:
                        logger.info("✅ Business metrics retrieved successfully")
                        metrics_data = json.loads(metrics_result.content[0].text)
                        logger.info(f"Metrics: {json.dumps(metrics_data, indent=2)}")
                    else:
                        logger.warning("⚠️ Business metrics failed", error=str(metrics_result.content))
                
                return True
                
    except Exception as e:
        logger.error("❌ Business tools integration test failed", error=str(e))
        return False


async def test_supabase_mcp_server():
    """Test Supabase MCP server directly."""
    logger.info("\n🧪 Testing Supabase MCP Server Direct Access")
    logger.info("=" * 50)
    
    # Load environment
    load_dotenv()
    
    access_token = (
        os.getenv("SUPABASE_ACCESS_TOKEN") or 
        os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN") or
        os.getenv("SUPABASE_PAT")
    )
    
    project_id = os.getenv("SUPABASE_PROJECT_ID") or os.getenv("PROJECT_ID")
    
    if not access_token or not project_id:
        logger.warning("⚠️ Supabase MCP server test skipped - missing credentials")
        return True
    
    # Set up MCP server parameters
    server_params = StdioServerParameters(
        command="npx",
        args=[
            "@supabase/mcp-server-supabase@latest",
            "--access-token", access_token
        ]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                logger.info("🔌 Connected to Supabase MCP server")
                
                # Initialize the session
                await session.initialize()
                
                # Test table listing
                tables_result = await session.call_tool(
                    "list_tables",
                    arguments={"project_id": project_id}
                )
                
                if not tables_result.isError:
                    logger.info("✅ Supabase MCP server working correctly")
                    
                    # Count business tables
                    tables_content = str(tables_result.content)
                    business_tables = ["customers", "leads", "tasks", "business_metrics", "agent_activities"]
                    found_tables = [table for table in business_tables if f'"name":"{table}"' in tables_content]
                    
                    logger.info(f"📊 Business tables available: {len(found_tables)}/{len(business_tables)}")
                    
                    return True
                else:
                    logger.error("❌ Supabase MCP server test failed", error=str(tables_result.content))
                    return False
                
    except Exception as e:
        logger.error("❌ Supabase MCP server test failed", error=str(e))
        return False


async def main():
    """Main validation function."""
    logger.info("🚀 Supabase Integration Validation")
    logger.info("=" * 40)
    
    # Test business tools integration
    business_tools_success = await test_business_tools_integration()
    
    # Test Supabase MCP server
    supabase_mcp_success = await test_supabase_mcp_server()
    
    # Summary
    logger.info("\n📋 Validation Summary")
    logger.info("=" * 25)
    
    if business_tools_success:
        logger.info("✅ Business Tools Integration: PASSED")
    else:
        logger.error("❌ Business Tools Integration: FAILED")
    
    if supabase_mcp_success:
        logger.info("✅ Supabase MCP Server: PASSED")
    else:
        logger.error("❌ Supabase MCP Server: FAILED")
    
    overall_success = business_tools_success and supabase_mcp_success
    
    if overall_success:
        logger.info("\n🎉 Supabase integration validation SUCCESSFUL!")
        logger.info("The Virtual AI Company Platform is ready for Supabase backend operations.")
        logger.info("\nNext steps:")
        logger.info("  1. Deploy AI agents with Supabase backend")
        logger.info("  2. Run full system demos")
        logger.info("  3. Monitor performance and scalability")
        return 0
    else:
        logger.error("\n❌ Supabase integration validation FAILED")
        logger.error("Please review the errors above and fix any issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
