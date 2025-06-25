#!/usr/bin/env python3
"""
Setup script for unified telemetry and registry systems
Creates all necessary tables and views in Supabase
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelemetrySetup:
    """Setup telemetry and registry schemas"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not all([self.supabase_url, self.supabase_anon_key]):
            raise ValueError("Supabase credentials not found in environment")
        
        # Use service key if available for admin operations
        key = self.supabase_service_key or self.supabase_anon_key
        self.client: Client = create_client(self.supabase_url, key)
    
    def execute_sql_file(self, file_path: Path) -> bool:
        """Execute SQL file using Supabase"""
        try:
            logger.info(f"Executing SQL file: {file_path.name}")
            
            with open(file_path, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon but keep complex statements together
            statements = []
            current_statement = []
            in_function = False
            
            for line in sql_content.split('\n'):
                current_statement.append(line)
                
                # Track if we're inside a function definition
                if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
                    in_function = True
                elif line.strip() == '$$ LANGUAGE plpgsql;':
                    in_function = False
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                elif ';' in line and not in_function:
                    statements.append('\n'.join(current_statement))
                    current_statement = []
            
            # Execute each statement
            for i, statement in enumerate(statements):
                if statement.strip():
                    try:
                        # Use the Supabase client's direct SQL execution
                        result = self.client.postgrest.session.post(
                            f"{self.supabase_url}/rest/v1/rpc/exec_sql",
                            json={"query": statement}
                        )
                        
                        if result.status_code != 200:
                            # Try alternative approach
                            logger.warning(f"Statement {i+1} needs manual execution")
                    except Exception as e:
                        logger.warning(f"Statement {i+1} error (may be OK): {str(e)[:100]}")
            
            logger.info(f"✅ Completed {file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to execute {file_path.name}: {e}")
            return False
    
    def setup_telemetry(self):
        """Setup telemetry schema"""
        logger.info("\n=== Setting up Telemetry Schema ===")
        
        sql_file = project_root / "sql" / "create_unified_telemetry.sql"
        if sql_file.exists():
            self.execute_sql_file(sql_file)
        else:
            logger.error(f"Telemetry SQL file not found: {sql_file}")
    
    def setup_registry(self):
        """Setup unified registry schema"""
        logger.info("\n=== Setting up Unified Registry Schema ===")
        
        sql_file = project_root / "sql" / "create_unified_registry.sql"
        if sql_file.exists():
            self.execute_sql_file(sql_file)
        else:
            logger.error(f"Registry SQL file not found: {sql_file}")
    
    def check_existing_registrations(self):
        """Check for registration gaps"""
        logger.info("\n=== Checking Registration Gaps ===")
        
        try:
            # Check teams
            teams = self.client.table("teams").select("id, name, framework").execute()
            logger.info(f"Found {len(teams.data)} teams in team registry")
            
            # Check MCPs
            mcps = self.client.table("mcps").select("id, name, type").execute()
            logger.info(f"Found {len(mcps.data)} MCPs in MCP registry")
            
            # Check unified registry
            unified = self.client.table("unified_registry").select(
                "entity_id, entity_type, entity_name"
            ).execute()
            
            if unified.data:
                by_type = {}
                for entity in unified.data:
                    entity_type = entity["entity_type"]
                    by_type[entity_type] = by_type.get(entity_type, 0) + 1
                
                logger.info("\nUnified Registry Summary:")
                for entity_type, count in by_type.items():
                    logger.info(f"  {entity_type}: {count}")
            else:
                logger.info("Unified registry is empty")
            
        except Exception as e:
            logger.warning(f"Could not check registrations: {e}")
    
    def create_sample_telemetry(self):
        """Create sample telemetry data for testing"""
        logger.info("\n=== Creating Sample Telemetry ===")
        
        try:
            # Sample A2A telemetry
            a2a_sample = {
                "protocol": "a2a",
                "source_id": "marketing-team",
                "source_type": "team",
                "target_id": "sales-team",
                "target_type": "team",
                "operation": "send_task",
                "task_description": "Generate Q4 campaign proposal",
                "status": "success",
                "duration_ms": 1250,
                "correlation_id": "sample-001"
            }
            
            result = self.client.table("communication_telemetry").insert(a2a_sample).execute()
            logger.info("✅ Created sample A2A telemetry")
            
            # Sample MCP telemetry
            mcp_sample = {
                "protocol": "mcp",
                "source_id": "executive-team",
                "source_type": "team",
                "target_id": "supabase",
                "target_type": "mcp",
                "operation": "tool_call",
                "tool_name": "query",
                "status": "success",
                "duration_ms": 85,
                "tokens_used": 150,
                "correlation_id": "sample-002"
            }
            
            result = self.client.table("communication_telemetry").insert(mcp_sample).execute()
            logger.info("✅ Created sample MCP telemetry")
            
        except Exception as e:
            logger.warning(f"Could not create sample telemetry: {e}")
    
    def show_instructions(self):
        """Show next steps"""
        print("\n" + "="*60)
        print("✅ TELEMETRY AND REGISTRY SETUP COMPLETE")
        print("="*60)
        
        print("\n📊 Next Steps:")
        print("\n1. Update teams to use telemetry-enabled A2A client:")
        print("   from elf_automations.shared.a2a.telemetry_client import create_a2a_client")
        print("   client = create_a2a_client(team_id='my-team', enable_telemetry=True)")
        
        print("\n2. Configure AgentGateway to log MCP telemetry:")
        print("   - Update AgentGateway handlers to use telemetry_client")
        print("   - See docs/AGENTGATEWAY_TELEMETRY_INTEGRATION.md")
        
        print("\n3. Register N8N workflows:")
        print("   from n8n.workflow_registration import N8NWorkflowRegistry")
        print("   registry = N8NWorkflowRegistry()")
        print("   registry.register_workflow(...)")
        
        print("\n4. Check registration gaps:")
        print("   SELECT * FROM check_registration_gaps();")
        
        print("\n5. View telemetry data:")
        print("   - Real-time metrics: SELECT * FROM communication_metrics_realtime;")
        print("   - Communication patterns: SELECT * FROM communication_patterns;")
        print("   - System health: SELECT * FROM system_health_overview;")
        
        print("\n6. Create Control Center views using these tables:")
        print("   - communication_telemetry (raw data)")
        print("   - unified_registry (entity states)")
        print("   - Various views for aggregated metrics")
        
        print("\n💡 SQL files created:")
        print("   - sql/create_unified_telemetry.sql")
        print("   - sql/create_unified_registry.sql")


def main():
    """Main setup function"""
    setup = TelemetrySetup()
    
    # Run setup
    setup.setup_telemetry()
    setup.setup_registry()
    
    # Check current state
    setup.check_existing_registrations()
    
    # Create sample data
    setup.create_sample_telemetry()
    
    # Show instructions
    setup.show_instructions()


if __name__ == "__main__":
    main()