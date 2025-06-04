#!/usr/bin/env python3
"""
Check Existing Tables in Supabase

Check what tables currently exist in the Supabase database.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def check_existing_tables():
    """Check existing tables in Supabase."""
    print("🔍 Checking Existing Tables in Supabase")
    print("=" * 45)
    
    # Load environment
    load_dotenv()
    
    # Get configuration
    access_token = (
        os.getenv("SUPABASE_ACCESS_TOKEN") or 
        os.getenv("SUPABASE_PERSONAL_ACCESS_TOKEN") or
        os.getenv("SUPABASE_PAT")
    )
    
    project_id = os.getenv("SUPABASE_PROJECT_ID") or os.getenv("PROJECT_ID")
    
    if not access_token or not project_id:
        print("❌ Missing access token or project ID")
        return False
    
    print(f"✅ Project ID: {project_id}")
    
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
                print("🔌 Connected to Supabase MCP server")
                
                # Initialize the session
                await session.initialize()
                
                # List all tables
                print("\n📋 Listing all tables...")
                
                tables_result = await session.call_tool(
                    "list_tables",
                    arguments={"project_id": project_id}
                )
                
                if not tables_result.isError:
                    tables_content = str(tables_result.content)
                    print("✅ Tables found:")
                    print(tables_content)
                    
                    # Check for business tables
                    business_tables = ["customers", "leads", "tasks", "business_metrics", "agent_activities"]
                    found_tables = []
                    
                    for table in business_tables:
                        if f'"name":"{table}"' in tables_content:
                            found_tables.append(table)
                    
                    print(f"\n📊 Business tables found: {len(found_tables)}/{len(business_tables)}")
                    for table in found_tables:
                        print(f"  ✅ {table}")
                    
                    missing_tables = [table for table in business_tables if table not in found_tables]
                    if missing_tables:
                        print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
                    
                    # Test a simple query on customers table
                    if "customers" in found_tables:
                        print("\n🔍 Testing customers table...")
                        
                        query_result = await session.call_tool(
                            "execute_sql",
                            arguments={
                                "project_id": project_id,
                                "query": "SELECT COUNT(*) as customer_count FROM customers;"
                            }
                        )
                        
                        if not query_result.isError:
                            print("✅ Customers table query successful:")
                            print(str(query_result.content))
                        else:
                            print("❌ Customers table query failed:")
                            print(str(query_result.content)[:200])
                    
                else:
                    print("❌ Failed to list tables:")
                    print(str(tables_result.content)[:300])
                    return False
                
                return True
                
    except Exception as e:
        print(f"❌ Failed to check tables: {str(e)}")
        return False

async def main():
    """Main function."""
    success = await check_existing_tables()
    
    if success:
        print("\n🎉 Table check completed!")
    else:
        print("\n❌ Table check failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
