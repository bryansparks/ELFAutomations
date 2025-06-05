#!/usr/bin/env python3
"""
Standalone Chief AI Agent runner for Kubernetes deployment.
This script runs the Chief AI Agent using CrewAI framework without 
dependencies on the distributed agent infrastructure.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/app')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import CrewAI components
try:
    from crewai import Agent, Task, Crew
    logger.info("✅ CrewAI imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import CrewAI: {e}")
    sys.exit(1)

# Health check endpoints
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agent_id": os.getenv("AGENT_ID", "chief-ai-agent"),
                "role": os.getenv("AGENT_ROLE", "Chief Executive Officer")
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/ready':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "ready",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default HTTP logging
        pass


class ChiefAIAgentStandalone:
    """Standalone Chief AI Agent implementation."""
    
    def __init__(self):
        self.agent_id = os.getenv("AGENT_ID", "chief-ai-agent")
        self.role = os.getenv("AGENT_ROLE", "Chief Executive Officer")
        self.department = os.getenv("DEPARTMENT", "executive")
        self.health_port = int(os.getenv("HEALTH_PORT", "8091"))
        
        # Create the CrewAI agent
        self.agent = Agent(
            role="Chief AI Agent - Executive Leadership",
            goal="""Provide strategic leadership, coordinate departments, optimize company 
                    performance, and ensure business objectives are met across all divisions""",
            backstory="""You are the Chief AI Agent, the executive leader of a Virtual AI Company Platform. 
                        You have extensive experience in strategic planning, organizational leadership, 
                        and business optimization. You work with a distributed team of specialized AI agents, 
                        each focused on their department's objectives.""",
            verbose=True,
            allow_delegation=True
        )
        
        logger.info(f"✅ Chief AI Agent created: {self.agent.role}")
        
        # Start health check server
        self.start_health_server()
    
    def start_health_server(self):
        """Start HTTP server for health checks."""
        try:
            self.health_server = HTTPServer(('0.0.0.0', self.health_port), HealthCheckHandler)
            self.health_thread = threading.Thread(target=self.health_server.serve_forever, daemon=True)
            self.health_thread.start()
            logger.info(f"✅ Health check server started on port {self.health_port}")
        except Exception as e:
            logger.error(f"❌ Failed to start health server: {e}")
    
    def create_strategic_task(self) -> Task:
        """Create a strategic planning task for the Chief AI Agent."""
        return Task(
            description="""Analyze the current business environment and provide strategic guidance.
                          
                          Consider:
                          - Market conditions and competitive landscape
                          - Department performance and coordination needs
                          - Resource allocation optimization
                          - Risk assessment and mitigation strategies
                          - Growth opportunities and strategic initiatives
                          
                          Provide actionable recommendations with clear next steps.""",
            agent=self.agent,
            expected_output="Strategic analysis with specific recommendations and action items"
        )
    
    async def run_continuous_operations(self):
        """Run continuous operations for the Chief AI Agent."""
        logger.info("🚀 Starting Chief AI Agent continuous operations")
        
        operation_count = 0
        
        while True:
            try:
                operation_count += 1
                logger.info(f"🔄 Starting operation cycle #{operation_count}")
                
                # Create and execute strategic planning task
                strategic_task = self.create_strategic_task()
                crew = Crew(
                    agents=[self.agent],
                    tasks=[strategic_task],
                    verbose=True
                )
                
                # Execute the crew
                result = crew.kickoff()
                
                logger.info(f"✅ Operation cycle #{operation_count} completed")
                logger.info(f"📊 Result summary: {str(result)[:200]}...")
                
                # Wait before next cycle (30 minutes)
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error(f"❌ Error in operation cycle #{operation_count}: {e}")
                # Wait 5 minutes before retrying on error
                await asyncio.sleep(300)
    
    def run(self):
        """Run the Chief AI Agent."""
        logger.info("🚀 Starting Chief AI Agent Standalone")
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info(f"Role: {self.role}")
        logger.info(f"Department: {self.department}")
        
        try:
            # Run continuous operations
            asyncio.run(self.run_continuous_operations())
        except KeyboardInterrupt:
            logger.info("👋 Chief AI Agent shutting down gracefully")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    agent = ChiefAIAgentStandalone()
    agent.run()
