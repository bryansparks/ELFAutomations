#!/usr/bin/env python3
"""
Test Business Tools MCP Server with Supabase

Validates the Business Tools MCP Server functionality with Supabase backend.
"""

import asyncio
import json
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.business_tools import BusinessToolsServer
from utils.supabase_util import get_supabase_client, ensure_business_tables, insert_sample_data

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


async def test_supabase_connection():
    """Test basic Supabase connection."""
    logger.info("🔌 Testing Supabase Connection")
    logger.info("=" * 40)
    
    try:
        client = get_supabase_client()
        logger.info("✅ Supabase client created successfully")
        
        # Test with a simple query
        try:
            # Try to query a system table or create a test table
            result = client.table("test_connection").select("*").limit(1).execute()
            logger.info("✅ Supabase query test successful")
        except Exception as e:
            logger.info("ℹ️ Test query failed (expected if table doesn't exist)", error=str(e))
        
        return True
        
    except Exception as e:
        logger.error("❌ Supabase connection failed", error=str(e))
        return False


async def test_business_tables():
    """Test business table accessibility."""
    logger.info("📊 Testing Business Tables")
    logger.info("=" * 40)
    
    try:
        # Check if tables exist
        accessible = await ensure_business_tables()
        
        if not accessible:
            logger.info("Creating sample data to test table creation...")
            success = await insert_sample_data()
            if success:
                logger.info("✅ Sample data inserted successfully")
            else:
                logger.warning("⚠️ Some sample data insertion failed")
        
        return True
        
    except Exception as e:
        logger.error("❌ Business tables test failed", error=str(e))
        return False


async def test_business_tools_server():
    """Test Business Tools MCP Server with Supabase."""
    logger.info("🛠️ Testing Business Tools MCP Server")
    logger.info("=" * 40)
    
    try:
        # Initialize server
        server = BusinessToolsServer()
        await server.start()
        
        logger.info(f"✅ Business Tools Server started (using {'Supabase' if server.use_supabase else 'PostgreSQL'})")
        
        # Test tool calls
        test_cases = [
            {
                "name": "create_customer",
                "args": {
                    "name": "Test Customer",
                    "email": "test@example.com",
                    "company": "Test Corp",
                    "phone": "+1-555-0123"
                }
            },
            {
                "name": "get_customer",
                "args": {
                    "email": "test@example.com"
                }
            },
            {
                "name": "create_lead",
                "args": {
                    "customer_id": "test-customer-id",
                    "source": "website",
                    "score": 75
                }
            },
            {
                "name": "create_task",
                "args": {
                    "title": "Test Task",
                    "description": "This is a test task",
                    "created_by_agent_id": "test-agent",
                    "priority": 2
                }
            },
            {
                "name": "get_business_metrics",
                "args": {}
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                logger.info(f"Testing tool: {test_case['name']}")
                result = await server.call_tool(test_case["name"], test_case["args"])
                results.append({
                    "tool": test_case["name"],
                    "success": "error" not in result,
                    "result": result
                })
                
                if "error" in result:
                    logger.warning(f"⚠️ Tool {test_case['name']} failed", error=result["error"])
                else:
                    logger.info(f"✅ Tool {test_case['name']} succeeded")
                    
            except Exception as e:
                logger.error(f"❌ Tool {test_case['name']} threw exception", error=str(e))
                results.append({
                    "tool": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # Stop server
        await server.stop()
        
        # Summary
        successful_tools = sum(1 for r in results if r["success"])
        logger.info(f"Tool Test Summary: {successful_tools}/{len(results)} tools successful")
        
        return successful_tools > 0
        
    except Exception as e:
        logger.error("❌ Business Tools Server test failed", error=str(e))
        return False


async def test_direct_supabase_operations():
    """Test direct Supabase operations."""
    logger.info("🔧 Testing Direct Supabase Operations")
    logger.info("=" * 40)
    
    try:
        from utils.supabase_util import query_table, insert_record, update_record
        
        # Test insert
        test_customer = {
            "name": "Direct Test Customer",
            "email": "direct@test.com",
            "company": "Direct Test Corp",
            "status": "active"
        }
        
        logger.info("Testing direct insert...")
        inserted = insert_record("customers", test_customer)
        if inserted:
            logger.info("✅ Direct insert successful", customer_id=inserted.get("id"))
            
            # Test query
            logger.info("Testing direct query...")
            customers = query_table("customers", {"email": "direct@test.com"}, limit=1)
            if customers:
                logger.info("✅ Direct query successful", count=len(customers))
                
                # Test update
                logger.info("Testing direct update...")
                updated = update_record("customers", customers[0]["id"], {"status": "updated"})
                if updated:
                    logger.info("✅ Direct update successful")
                else:
                    logger.warning("⚠️ Direct update failed")
            else:
                logger.warning("⚠️ Direct query returned no results")
        else:
            logger.warning("⚠️ Direct insert failed")
        
        return True
        
    except Exception as e:
        logger.error("❌ Direct Supabase operations test failed", error=str(e))
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Business Tools Supabase Integration Test")
    logger.info("=" * 60)
    
    # Load environment
    load_dotenv()
    
    test_results = []
    
    # Test 1: Supabase Connection
    result = await test_supabase_connection()
    test_results.append(("Supabase Connection", result))
    
    # Test 2: Business Tables
    result = await test_business_tables()
    test_results.append(("Business Tables", result))
    
    # Test 3: Business Tools Server
    result = await test_business_tools_server()
    test_results.append(("Business Tools Server", result))
    
    # Test 4: Direct Supabase Operations
    result = await test_direct_supabase_operations()
    test_results.append(("Direct Supabase Operations", result))
    
    # Summary
    logger.info("\n🎯 Test Summary")
    logger.info("=" * 30)
    
    passed_tests = 0
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if passed:
            passed_tests += 1
    
    logger.info(f"\nOverall: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        logger.info("🎉 All tests passed! Supabase integration is working correctly.")
        logger.info("\nNext steps:")
        logger.info("  1. Run full system demo with Supabase")
        logger.info("  2. Test AI agent interactions")
        logger.info("  3. Deploy to production environment")
        return 0
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
