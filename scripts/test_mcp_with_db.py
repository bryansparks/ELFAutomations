#!/usr/bin/env python3
"""
Test MCP Server with Real Database

Tests the Business Tools MCP Server with actual database connectivity.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import structlog
from dotenv import load_dotenv

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
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def test_mcp_server_with_database():
    """Test MCP server with real database operations."""
    logger.info("🧪 Testing MCP Server with Database")
    logger.info("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if database is available
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set - cannot test with database")
        return False
    
    try:
        # Create and start MCP server
        server = BusinessToolsServer()
        await server.start()
        
        logger.info("✅ Business Tools MCP Server started")
        
        # Test 1: List available tools
        logger.info("\n📋 Testing: List Available Tools")
        tools = server.get_tools()
        logger.info(f"Found {len(tools)} tools")
        
        for tool in tools[:3]:  # Show first 3
            logger.info(f"  - {tool.name}: {tool.description}")
        
        # Test 2: List available resources
        logger.info("\n📋 Testing: List Available Resources")
        resources = server.get_resources()
        logger.info(f"Found {len(resources)} resources")
        
        for resource in resources:
            logger.info(f"  - {resource.uri}: {resource.description}")
        
        # Test 3: Read customers resource
        logger.info("\n📖 Testing: Read Customers Resource")
        try:
            customers_data = await server.read_resource("business://customers")
            logger.info("Customers resource read successfully", 
                       data_type=type(customers_data).__name__,
                       preview=str(customers_data)[:200] + "..." if len(str(customers_data)) > 200 else str(customers_data))
        except Exception as e:
            logger.error("Failed to read customers resource", error=str(e))
        
        # Test 4: Create a new customer using MCP tool
        logger.info("\n🔧 Testing: Create Customer Tool")
        try:
            create_result = await server.call_tool(
                "create_customer",
                {
                    "name": "Test Customer",
                    "email": "test@example.com",
                    "company": "Test Corp",
                    "phone": "+1-555-0123"
                }
            )
            logger.info("Customer created successfully", result=create_result)
        except Exception as e:
            logger.error("Failed to create customer", error=str(e))
        
        # Test 5: Get customer by ID
        logger.info("\n🔍 Testing: Get Customer Tool")
        try:
            get_result = await server.call_tool("get_customer", {"customer_id": 1})
            logger.info("Customer retrieved successfully", result=get_result)
        except Exception as e:
            logger.error("Failed to get customer", error=str(e))
        
        # Test 6: Create a task
        logger.info("\n📝 Testing: Create Task Tool")
        try:
            task_result = await server.call_tool(
                "create_task",
                {
                    "title": "Test MCP Integration",
                    "description": "Verify that MCP server can create tasks",
                    "assignee": "test-agent-001",
                    "priority": "high"
                }
            )
            logger.info("Task created successfully", result=task_result)
        except Exception as e:
            logger.error("Failed to create task", error=str(e))
        
        # Test 7: Get business metrics
        logger.info("\n📊 Testing: Get Business Metrics Tool")
        try:
            metrics_result = await server.call_tool(
                "get_business_metrics",
                {"metric_type": "financial"}
            )
            logger.info("Business metrics retrieved successfully", result=metrics_result)
        except Exception as e:
            logger.error("Failed to get business metrics", error=str(e))
        
        # Stop the server
        await server.stop()
        logger.info("✅ MCP Server stopped")
        
        logger.info("\n🎉 MCP Server database integration test completed!")
        return True
        
    except Exception as e:
        logger.error("MCP Server test failed", error=str(e))
        return False


async def main():
    """Main test function."""
    success = await test_mcp_server_with_database()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
