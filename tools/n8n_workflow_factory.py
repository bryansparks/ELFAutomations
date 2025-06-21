#!/usr/bin/env python3
"""
N8N Workflow Factory

AI-powered workflow generator that creates n8n workflows from natural language descriptions.
Produces JSON that can be imported into n8n and automatically registers workflows.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import Client, create_client

from elf_automations.shared.n8n import N8NClient, WorkflowCategory, WorkflowTriggerType
from elf_automations.shared.utils.llm_factory import LLMFactory

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class WorkflowPattern:
    """Base patterns for common workflow types"""

    @staticmethod
    def webhook_process_respond():
        """Basic webhook → process → respond pattern"""
        return {
            "nodes": [
                {
                    "id": "webhook",
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {
                        "httpMethod": "POST",
                        "path": "{{PATH}}",
                        "responseMode": "responseNode",
                    },
                },
                {
                    "id": "process",
                    "name": "Process Data",
                    "type": "n8n-nodes-base.set",
                    "typeVersion": 2,
                    "position": [450, 300],
                    "parameters": {},
                },
                {
                    "id": "respond",
                    "name": "Respond",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1,
                    "position": [650, 300],
                    "parameters": {},
                },
            ],
            "connections": {
                "Webhook": {
                    "main": [[{"node": "Process Data", "type": "main", "index": 0}]]
                },
                "Process Data": {
                    "main": [[{"node": "Respond", "type": "main", "index": 0}]]
                },
            },
        }

    @staticmethod
    def schedule_fetch_store():
        """Schedule → fetch data → store pattern"""
        return {
            "nodes": [
                {
                    "id": "schedule",
                    "name": "Schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {
                        "rule": {"interval": [{"field": "hours", "intervalValue": 1}]}
                    },
                },
                {
                    "id": "fetch",
                    "name": "Fetch Data",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 4,
                    "position": [450, 300],
                    "parameters": {"method": "GET", "url": "{{URL}}"},
                },
                {
                    "id": "store",
                    "name": "Store Data",
                    "type": "n8n-nodes-base.postgres",
                    "typeVersion": 2,
                    "position": [650, 300],
                    "parameters": {"operation": "insert"},
                },
            ],
            "connections": {
                "Schedule": {
                    "main": [[{"node": "Fetch Data", "type": "main", "index": 0}]]
                },
                "Fetch Data": {
                    "main": [[{"node": "Store Data", "type": "main", "index": 0}]]
                },
            },
        }


class N8NWorkflowFactory:
    """Factory for generating n8n workflows from descriptions"""

    def __init__(self):
        self.llm = LLMFactory.create_llm(
            preferred_provider="anthropic",
            preferred_model="claude-3-sonnet-20240229",
            temperature=0.1,
            enable_fallback=True,
        )

        # Initialize Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        else:
            raise ValueError("Supabase credentials not found")

        self.patterns = {
            "webhook": WorkflowPattern.webhook_process_respond(),
            "schedule": WorkflowPattern.schedule_fetch_store(),
        }

    def analyze_requirements(self, description: str) -> Dict[str, Any]:
        """Use LLM to analyze workflow requirements"""

        prompt = f"""Analyze this workflow requirement and extract key information:

Description: {description}

Extract:
1. Trigger type (webhook, schedule, manual, event)
2. If schedule, the cron expression or interval
3. Main operations (fetch data, process, store, notify, etc.)
4. Data sources/destinations
5. Any conditions or branching logic
6. Error handling needs

Return as JSON with these fields:
- trigger_type: string
- schedule_config: object (if applicable)
- operations: array of operation descriptions
- data_sources: array
- data_destinations: array
- conditions: array
- error_handling: boolean
"""

        response = self.llm.invoke(prompt)

        # Parse the response
        try:
            # Extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        # Fallback analysis
        return {
            "trigger_type": "webhook"
            if "webhook" in description.lower()
            else "schedule",
            "operations": ["process"],
            "data_sources": [],
            "data_destinations": [],
        }

    def select_nodes(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select appropriate n8n nodes based on requirements"""

        nodes = []

        # Add trigger node
        if requirements["trigger_type"] == "webhook":
            nodes.append(
                {
                    "id": "trigger",
                    "name": "Webhook Trigger",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [250, 300],
                }
            )
        elif requirements["trigger_type"] == "schedule":
            nodes.append(
                {
                    "id": "trigger",
                    "name": "Schedule Trigger",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1,
                    "position": [250, 300],
                }
            )

        # Add operation nodes based on requirements
        x_position = 450
        for i, operation in enumerate(requirements.get("operations", [])):
            if "fetch" in operation.lower():
                nodes.append(
                    {
                        "id": f"operation_{i}",
                        "name": "Fetch Data",
                        "type": "n8n-nodes-base.httpRequest",
                        "typeVersion": 4,
                        "position": [x_position, 300],
                    }
                )
            elif "store" in operation.lower() or "save" in operation.lower():
                nodes.append(
                    {
                        "id": f"operation_{i}",
                        "name": "Store Data",
                        "type": "n8n-nodes-base.postgres",
                        "typeVersion": 2,
                        "position": [x_position, 300],
                    }
                )
            elif "notify" in operation.lower() or "slack" in operation.lower():
                nodes.append(
                    {
                        "id": f"operation_{i}",
                        "name": "Send Notification",
                        "type": "n8n-nodes-base.slack",
                        "typeVersion": 2,
                        "position": [x_position, 300],
                    }
                )
            else:
                nodes.append(
                    {
                        "id": f"operation_{i}",
                        "name": "Process Data",
                        "type": "n8n-nodes-base.set",
                        "typeVersion": 2,
                        "position": [x_position, 300],
                    }
                )
            x_position += 200

        return nodes

    def generate_connections(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate connections between nodes"""

        connections = {}

        for i in range(len(nodes) - 1):
            current_node = nodes[i]["name"]
            next_node = nodes[i + 1]["name"]

            if current_node not in connections:
                connections[current_node] = {"main": [[]]}

            connections[current_node]["main"][0].append(
                {"node": next_node, "type": "main", "index": 0}
            )

        return connections

    def create_workflow(
        self, description: str, name: str, team: str, category: str = "automation"
    ) -> Dict[str, Any]:
        """Create a complete workflow from description"""

        print(f"Analyzing workflow requirements: {description}")

        # Analyze requirements
        requirements = self.analyze_requirements(description)

        # Select nodes
        nodes = self.select_nodes(requirements)

        # Generate connections
        connections = self.generate_connections(nodes)

        # Create workflow JSON
        workflow = {
            "name": name,
            "nodes": nodes,
            "connections": connections,
            "active": False,
            "settings": {
                "saveDataSuccessExecution": "all",
                "saveManualExecutions": True,
                "saveExecutionProgress": True,
            },
            "tags": [team, category],
        }

        # Add parameters based on requirements
        self._configure_nodes(workflow, requirements)

        return {
            "workflow": workflow,
            "metadata": {
                "description": description,
                "team": team,
                "category": category,
                "trigger_type": requirements["trigger_type"],
                "created_at": datetime.utcnow().isoformat(),
            },
        }

    def _configure_nodes(self, workflow: Dict[str, Any], requirements: Dict[str, Any]):
        """Configure node parameters based on requirements"""

        for node in workflow["nodes"]:
            if node["type"] == "n8n-nodes-base.webhook":
                node["parameters"] = {
                    "httpMethod": "POST",
                    "path": workflow["name"].lower().replace(" ", "-"),
                    "responseMode": "responseNode",
                    "options": {},
                }

            elif node["type"] == "n8n-nodes-base.scheduleTrigger":
                schedule_config = requirements.get("schedule_config", {})
                node["parameters"] = {
                    "rule": {"interval": [{"field": "hours", "intervalValue": 1}]}
                }

            elif node["type"] == "n8n-nodes-base.httpRequest":
                node["parameters"] = {
                    "method": "GET",
                    "url": "https://api.example.com/data",
                    "authentication": "none",
                    "options": {},
                }

    async def deploy_workflow(
        self, workflow_data: Dict[str, Any], n8n_workflow_id: Optional[str] = None
    ) -> str:
        """Deploy workflow to n8n and register in system"""

        metadata = workflow_data["metadata"]
        workflow = workflow_data["workflow"]

        # Generate webhook URL if needed
        webhook_url = None
        if metadata["trigger_type"] == "webhook":
            path = workflow["name"].lower().replace(" ", "-")
            webhook_url = f"http://n8n.n8n.svc.cluster.local:5678/webhook/{path}"

        # Register in our system
        registration = {
            "name": workflow["name"],
            "description": metadata["description"],
            "category": metadata["category"],
            "owner_team": metadata["team"],
            "n8n_workflow_id": n8n_workflow_id or "pending",
            "trigger_type": metadata["trigger_type"],
            "webhook_url": webhook_url,
            "input_schema": {},
            "output_schema": {},
            "is_active": False,
            "metadata": metadata,
        }

        result = self.supabase.table("n8n_workflows").insert(registration).execute()

        if result.data:
            workflow_id = result.data[0]["id"]
            print(f"✓ Workflow registered: {workflow_id}")

            # Save workflow JSON to file
            workflows_dir = Path(__file__).parent.parent / "workflows" / "generated"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                f"{workflow['name'].lower().replace(' ', '_')}_{workflow_id}.json"
            )
            filepath = workflows_dir / filename

            with open(filepath, "w") as f:
                json.dump(workflow, f, indent=2)

            print(f"✓ Workflow saved to: {filepath}")
            print("\nNext steps:")
            print(f"1. Import {filepath} into n8n")
            print("2. Note the n8n workflow ID")
            print(
                f"3. Update registration: python scripts/n8n_workflow_manager.py update '{workflow['name']}' --workflow-id [ID]"
            )

            return str(workflow_id)

        raise Exception("Failed to register workflow")


def main():
    """CLI interface for workflow factory"""

    import argparse

    parser = argparse.ArgumentParser(description="N8N Workflow Factory")
    parser.add_argument("description", help="Natural language workflow description")
    parser.add_argument("--name", required=True, help="Workflow name")
    parser.add_argument("--team", required=True, help="Owner team")
    parser.add_argument(
        "--category",
        default="automation",
        choices=[
            "data-pipeline",
            "integration",
            "automation",
            "notification",
            "approval",
        ],
    )
    parser.add_argument(
        "--deploy", action="store_true", help="Deploy and register workflow"
    )

    args = parser.parse_args()

    factory = N8NWorkflowFactory()

    # Create workflow
    workflow_data = factory.create_workflow(
        description=args.description,
        name=args.name,
        team=args.team,
        category=args.category,
    )

    # Display workflow
    print("\nGenerated Workflow:")
    print("=" * 80)
    print(json.dumps(workflow_data["workflow"], indent=2))
    print("=" * 80)

    # Deploy if requested
    if args.deploy:
        asyncio.run(factory.deploy_workflow(workflow_data))


if __name__ == "__main__":
    main()
