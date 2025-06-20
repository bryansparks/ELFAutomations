#!/usr/bin/env python3
"""
N8N Workflow Factory V2

Enhanced AI-powered workflow generator with template support and intelligent node selection.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.utils.llm_factory import LLMFactory
from elf_automations.shared.n8n import N8NClient, WorkflowCategory, WorkflowTriggerType
from elf_automations.shared.n8n.templates import WorkflowTemplates, get_template, list_templates
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class EnhancedWorkflowFactory:
    """Enhanced factory with template matching and intelligent generation"""
    
    def __init__(self):
        self.llm = LLMFactory.create_llm(
            preferred_provider="anthropic",
            preferred_model="claude-3-sonnet-20240229",
            temperature=0.1,
            enable_fallback=True
        )
        
        # Initialize Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        else:
            raise ValueError("Supabase credentials not found")
        
        # Node type mapping
        self.node_types = {
            "webhook": "n8n-nodes-base.webhook",
            "schedule": "n8n-nodes-base.scheduleTrigger",
            "http": "n8n-nodes-base.httpRequest",
            "database": "n8n-nodes-base.postgres",
            "transform": "n8n-nodes-base.code",
            "filter": "n8n-nodes-base.if",
            "switch": "n8n-nodes-base.switch",
            "merge": "n8n-nodes-base.merge",
            "slack": "n8n-nodes-base.slack",
            "email": "n8n-nodes-base.emailSend",
            "wait": "n8n-nodes-base.wait",
            "respond": "n8n-nodes-base.respondToWebhook",
            "set": "n8n-nodes-base.set",
            "function": "n8n-nodes-base.functionItem"
        }
    
    def analyze_and_match_template(self, description: str) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        """Analyze description and try to match with existing template"""
        
        prompt = f"""Analyze this workflow description and determine if it matches any standard patterns:

Description: {description}

Available template categories and types:
- data-pipeline: etl (extract, transform, load operations)
- integration: crm-sync (syncing between systems)
- approval: multi-step (approval workflows with escalation)
- automation: report-generator (scheduled reports)

Also extract:
1. Trigger type and configuration
2. Main operations and their sequence
3. Data sources and destinations
4. Business rules or conditions
5. Notification requirements

Return as JSON:
{{
    "matches_template": true/false,
    "template_category": "category or null",
    "template_name": "name or null",
    "customizations_needed": ["list of required customizations"],
    "workflow_analysis": {{
        "trigger": {{"type": "webhook/schedule/manual", "config": {{}}}},
        "operations": ["operation1", "operation2"],
        "data_sources": ["source1", "source2"],
        "data_destinations": ["dest1", "dest2"],
        "conditions": ["condition1"],
        "notifications": ["slack", "email"]
    }}
}}
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                if analysis.get("matches_template"):
                    return (
                        analysis.get("template_category"),
                        analysis.get("template_name"),
                        analysis.get("workflow_analysis", {})
                    )
                else:
                    return (None, None, analysis.get("workflow_analysis", {}))
        except:
            pass
        
        return (None, None, {})
    
    def customize_template(self, 
                         template: Dict[str, Any], 
                         analysis: Dict[str, Any],
                         name: str) -> Dict[str, Any]:
        """Customize a template based on analysis"""
        
        workflow = template.copy()
        workflow["name"] = name
        
        # Update trigger configuration
        if "trigger" in analysis:
            trigger_config = analysis["trigger"]
            for node in workflow["nodes"]:
                if node["id"] == "schedule" and trigger_config["type"] == "schedule":
                    # Update schedule configuration
                    if "cron" in trigger_config.get("config", {}):
                        node["parameters"]["rule"] = {
                            "cronExpression": trigger_config["config"]["cron"]
                        }
                elif node["id"] == "webhook" and trigger_config["type"] == "webhook":
                    # Update webhook path
                    node["parameters"]["path"] = name.lower().replace(" ", "-")
        
        return workflow
    
    def generate_custom_workflow(self, 
                               analysis: Dict[str, Any],
                               name: str) -> Dict[str, Any]:
        """Generate a custom workflow when no template matches"""
        
        nodes = []
        connections = {}
        
        # Generate trigger node
        trigger_type = analysis.get("trigger", {}).get("type", "webhook")
        trigger_node = self._create_trigger_node(trigger_type, analysis.get("trigger", {}))
        nodes.append(trigger_node)
        
        # Generate operation nodes
        prev_node = trigger_node["name"]
        x_position = 450
        
        for i, operation in enumerate(analysis.get("operations", [])):
            node = self._create_operation_node(operation, i, x_position)
            nodes.append(node)
            
            # Create connection
            if prev_node not in connections:
                connections[prev_node] = {"main": [[]]}
            connections[prev_node]["main"][0].append({
                "node": node["name"],
                "type": "main",
                "index": 0
            })
            
            prev_node = node["name"]
            x_position += 200
        
        # Add notification nodes if needed
        for notification in analysis.get("notifications", []):
            node = self._create_notification_node(notification, x_position)
            nodes.append(node)
            
            if prev_node not in connections:
                connections[prev_node] = {"main": [[]]}
            connections[prev_node]["main"][0].append({
                "node": node["name"],
                "type": "main",
                "index": 0
            })
            
            x_position += 200
        
        return {
            "name": name,
            "nodes": nodes,
            "connections": connections,
            "active": False,
            "settings": {
                "saveDataSuccessExecution": "all",
                "saveManualExecutions": True,
                "saveExecutionProgress": True
            }
        }
    
    def _create_trigger_node(self, trigger_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a trigger node based on type"""
        
        if trigger_type == "schedule":
            return {
                "id": "trigger",
                "name": "Schedule Trigger",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "rule": config.get("config", {
                        "interval": [{"field": "hours", "intervalValue": 1}]
                    })
                }
            }
        else:  # Default to webhook
            return {
                "id": "trigger",
                "name": "Webhook Trigger",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "httpMethod": "POST",
                    "path": "webhook",
                    "responseMode": "responseNode"
                }
            }
    
    def _create_operation_node(self, operation: str, index: int, x_position: int) -> Dict[str, Any]:
        """Create an operation node based on description"""
        
        operation_lower = operation.lower()
        
        # Determine node type based on operation
        if any(word in operation_lower for word in ["fetch", "get", "retrieve", "pull"]):
            return {
                "id": f"operation_{index}",
                "name": f"Fetch Data",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4,
                "position": [x_position, 300],
                "parameters": {
                    "method": "GET",
                    "url": "https://api.example.com/data"
                }
            }
        elif any(word in operation_lower for word in ["store", "save", "insert", "update"]):
            return {
                "id": f"operation_{index}",
                "name": f"Store Data",
                "type": "n8n-nodes-base.postgres",
                "typeVersion": 2.3,
                "position": [x_position, 300],
                "parameters": {
                    "operation": "insert",
                    "table": "data_table"
                }
            }
        elif any(word in operation_lower for word in ["transform", "process", "calculate"]):
            return {
                "id": f"operation_{index}",
                "name": f"Process Data",
                "type": "n8n-nodes-base.code",
                "typeVersion": 1,
                "position": [x_position, 300],
                "parameters": {
                    "jsCode": "// Process data\nreturn items;"
                }
            }
        else:
            return {
                "id": f"operation_{index}",
                "name": operation,
                "type": "n8n-nodes-base.set",
                "typeVersion": 2,
                "position": [x_position, 300],
                "parameters": {}
            }
    
    def _create_notification_node(self, notification_type: str, x_position: int) -> Dict[str, Any]:
        """Create a notification node"""
        
        if "slack" in notification_type.lower():
            return {
                "id": "notify_slack",
                "name": "Send to Slack",
                "type": "n8n-nodes-base.slack",
                "typeVersion": 2.1,
                "position": [x_position, 300],
                "parameters": {
                    "operation": "post",
                    "channel": "#notifications",
                    "text": "Workflow completed"
                }
            }
        else:  # Default to email
            return {
                "id": "notify_email",
                "name": "Send Email",
                "type": "n8n-nodes-base.emailSend",
                "typeVersion": 2.1,
                "position": [x_position, 300],
                "parameters": {
                    "sendTo": "notifications@example.com",
                    "subject": "Workflow Notification",
                    "message": "Workflow completed successfully"
                }
            }
    
    async def create_workflow(self,
                            description: str,
                            name: str,
                            team: str,
                            category: str = "automation",
                            force_custom: bool = False) -> Dict[str, Any]:
        """Create workflow using templates when possible"""
        
        print(f"\n🤖 Analyzing requirements: {description}")
        
        # Try to match with template
        template_category, template_name, analysis = self.analyze_and_match_template(description)
        
        workflow = None
        
        if template_category and template_name and not force_custom:
            print(f"✓ Matched template: {template_category}/{template_name}")
            
            # Get and customize template
            template = get_template(template_category, template_name)
            workflow = self.customize_template(template, analysis, name)
            
            print("✓ Template customized")
        else:
            print("⚡ Generating custom workflow")
            workflow = self.generate_custom_workflow(analysis, name)
        
        # Update webhook path if needed
        for node in workflow["nodes"]:
            if node.get("type") == "n8n-nodes-base.webhook":
                node["parameters"]["path"] = name.lower().replace(" ", "-")
        
        return {
            "workflow": workflow,
            "metadata": {
                "description": description,
                "team": team,
                "category": category,
                "template_used": f"{template_category}/{template_name}" if template_category else None,
                "trigger_type": analysis.get("trigger", {}).get("type", "unknown"),
                "created_at": datetime.utcnow().isoformat()
            }
        }
    
    async def generate_workflow_batch(self, 
                                    descriptions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Generate multiple workflows in batch"""
        
        workflows = []
        
        for desc in descriptions:
            workflow = await self.create_workflow(
                description=desc["description"],
                name=desc["name"],
                team=desc["team"],
                category=desc.get("category", "automation")
            )
            workflows.append(workflow)
        
        return workflows


def main():
    """Enhanced CLI with template support"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced N8N Workflow Factory')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create workflow command
    create_parser = subparsers.add_parser('create', help='Create a workflow')
    create_parser.add_argument('description', help='Natural language workflow description')
    create_parser.add_argument('--name', required=True, help='Workflow name')
    create_parser.add_argument('--team', required=True, help='Owner team')
    create_parser.add_argument('--category', default='automation',
                             choices=['data-pipeline', 'integration', 'automation', 'notification', 'approval'])
    create_parser.add_argument('--force-custom', action='store_true', 
                             help='Force custom generation instead of using templates')
    create_parser.add_argument('--output', help='Output file path')
    
    # List templates command
    list_parser = subparsers.add_parser('list-templates', help='List available templates')
    
    # Show template command
    show_parser = subparsers.add_parser('show-template', help='Show a specific template')
    show_parser.add_argument('category', help='Template category')
    show_parser.add_argument('name', help='Template name')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        factory = EnhancedWorkflowFactory()
        
        # Create workflow
        workflow_data = asyncio.run(factory.create_workflow(
            description=args.description,
            name=args.name,
            team=args.team,
            category=args.category,
            force_custom=args.force_custom
        ))
        
        # Display workflow
        print("\n📋 Generated Workflow:")
        print("=" * 80)
        print(json.dumps(workflow_data["workflow"], indent=2))
        print("=" * 80)
        
        # Save if output specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(workflow_data["workflow"], f, indent=2)
            print(f"\n✓ Saved to: {args.output}")
        
        print("\n📊 Metadata:")
        for key, value in workflow_data["metadata"].items():
            print(f"  {key}: {value}")
    
    elif args.command == 'list-templates':
        templates = list_templates()
        print("\n📚 Available Templates:")
        print("=" * 40)
        for category, names in templates.items():
            print(f"\n{category}:")
            for name in names:
                print(f"  - {name}")
    
    elif args.command == 'show-template':
        try:
            template = get_template(args.category, args.name)
            print(f"\n📋 Template: {args.category}/{args.name}")
            print("=" * 80)
            print(json.dumps(template, indent=2))
        except ValueError as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()