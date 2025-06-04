#!/usr/bin/env python3
"""
Virtual AI Company Platform - Web Dashboard

A Flask-based web interface to monitor and interact with the Virtual AI Company Platform.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import structlog
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Import our components
sys.path.append(str(Path(__file__).parent.parent))

from mcp_servers.business_tools import BusinessToolsServer
from agents.executive.chief_ai_agent import ChiefAIAgent

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

# Load environment
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Global business tools instance
business_tools = None


async def get_business_tools():
    """Get or initialize business tools."""
    global business_tools
    if business_tools is None:
        business_tools = BusinessToolsServer()
        await business_tools.start()
    return business_tools


@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    """Get system status."""
    try:
        # Check Supabase connection
        supabase_status = {
            'url': os.getenv('SUPABASE_URL', 'Not configured'),
            'connected': bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY')),
            'project_id': os.getenv('SUPABASE_PROJECT_ID', 'Not configured')
        }
        
        # Check environment
        env_status = {
            'supabase_configured': bool(os.getenv('SUPABASE_URL')),
            'anthropic_configured': bool(os.getenv('ANTHROPIC_API_KEY')),
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        }
        
        return jsonify({
            'status': 'operational',
            'timestamp': datetime.now().isoformat(),
            'supabase': supabase_status,
            'environment': env_status,
            'services': {
                'business_tools': 'operational',
                'ai_agents': 'operational',
                'database': 'operational'
            }
        })
    except Exception as e:
        logger.error("Status check failed", error=str(e))
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/metrics')
def api_metrics():
    """Get business metrics."""
    async def _get_metrics():
        try:
            tools = await get_business_tools()
            
            if not tools.supabase_client:
                return {'error': 'Supabase not connected'}
            
            # Get table counts
            metrics = {}
            
            tables = ['customers', 'leads', 'tasks', 'business_metrics', 'agent_activities']
            for table in tables:
                try:
                    result = tools.supabase_client.table(table).select('id', count='exact').execute()
                    metrics[f'{table}_count'] = result.count if result.count is not None else 0
                except Exception as e:
                    metrics[f'{table}_count'] = 0
                    logger.warning(f"Failed to count {table}", error=str(e))
            
            # Get lead quality metrics
            try:
                leads_result = tools.supabase_client.table('leads').select('*').execute()
                if leads_result.data:
                    scores = [lead.get('score', 0) for lead in leads_result.data if lead.get('score')]
                    high_quality = [lead for lead in leads_result.data if lead.get('score', 0) > 80]
                    
                    metrics['average_lead_score'] = sum(scores) / len(scores) if scores else 0
                    metrics['high_quality_leads'] = len(high_quality)
                    metrics['lead_quality_rate'] = (len(high_quality) / len(leads_result.data)) * 100 if leads_result.data else 0
                else:
                    metrics.update({
                        'average_lead_score': 0,
                        'high_quality_leads': 0,
                        'lead_quality_rate': 0
                    })
            except Exception as e:
                logger.warning("Failed to get lead metrics", error=str(e))
                metrics.update({
                    'average_lead_score': 0,
                    'high_quality_leads': 0,
                    'lead_quality_rate': 0
                })
            
            # Get task completion metrics
            try:
                tasks_result = tools.supabase_client.table('tasks').select('*').execute()
                if tasks_result.data:
                    completed = [task for task in tasks_result.data if task.get('status') == 'completed']
                    pending = [task for task in tasks_result.data if task.get('status') == 'pending']
                    
                    metrics['completed_tasks'] = len(completed)
                    metrics['pending_tasks'] = len(pending)
                    metrics['task_completion_rate'] = (len(completed) / len(tasks_result.data)) * 100 if tasks_result.data else 0
                else:
                    metrics.update({
                        'completed_tasks': 0,
                        'pending_tasks': 0,
                        'task_completion_rate': 0
                    })
            except Exception as e:
                logger.warning("Failed to get task metrics", error=str(e))
                metrics.update({
                    'completed_tasks': 0,
                    'pending_tasks': 0,
                    'task_completion_rate': 0
                })
            
            return metrics
            
        except Exception as e:
            logger.error("Metrics collection failed", error=str(e))
            return {'error': str(e)}
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_get_metrics())
        return jsonify(result)
    finally:
        loop.close()


@app.route('/api/agents')
def api_agents():
    """Get agent information."""
    agents = [
        {
            'id': 'chief-ai-agent',
            'name': 'Chief AI Agent',
            'type': 'executive',
            'department': 'executive',
            'status': 'active',
            'last_activity': datetime.now().isoformat()
        }
    ]
    
    return jsonify({'agents': agents})


@app.route('/api/agents/analyze', methods=['POST'])
def api_agent_analyze():
    """Request AI agent analysis."""
    async def _run_analysis():
        try:
            data = request.get_json()
            prompt = data.get('prompt', 'Provide a business status analysis.')
            
            # Initialize Chief AI Agent
            chief_agent = ChiefAIAgent()
            
            # Run analysis
            result = await chief_agent.think(prompt)
            
            return {
                'analysis': result,
                'timestamp': datetime.now().isoformat(),
                'agent': 'chief-ai-agent'
            }
            
        except Exception as e:
            logger.error("Agent analysis failed", error=str(e))
            return {'error': str(e)}
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run_analysis())
        return jsonify(result)
    finally:
        loop.close()


@app.route('/api/database/tables')
def api_database_tables():
    """Get database table information."""
    async def _get_tables():
        try:
            tools = await get_business_tools()
            
            if not tools.supabase_client:
                return {'error': 'Supabase not connected'}
            
            tables_info = []
            tables = ['customers', 'leads', 'tasks', 'business_metrics', 'agent_activities']
            
            for table in tables:
                try:
                    # Get count
                    count_result = tools.supabase_client.table(table).select('id', count='exact').execute()
                    count = count_result.count if count_result.count is not None else 0
                    
                    # Get sample data
                    sample_result = tools.supabase_client.table(table).select('*').limit(3).execute()
                    sample_data = sample_result.data if sample_result.data else []
                    
                    tables_info.append({
                        'name': table,
                        'count': count,
                        'sample_data': sample_data
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get info for table {table}", error=str(e))
                    tables_info.append({
                        'name': table,
                        'count': 0,
                        'sample_data': [],
                        'error': str(e)
                    })
            
            return {'tables': tables_info}
            
        except Exception as e:
            logger.error("Database tables query failed", error=str(e))
            return {'error': str(e)}
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_get_tables())
        return jsonify(result)
    finally:
        loop.close()


if __name__ == '__main__':
    logger.info("Starting Virtual AI Company Platform Dashboard")
    logger.info(f"Supabase URL: {os.getenv('SUPABASE_URL', 'Not configured')}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8080)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
