#!/usr/bin/env python3
"""
Telemetry patch for n8n_workflow_factory_v3.py
Adds telemetry and unified registry integration to the N8N workflow factory
"""

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elf_automations.shared.telemetry import telemetry_client


def patch_n8n_workflow_factory():
    """Patch the N8N workflow factory to add telemetry and registration"""

    # Import the N8N workflow factory
    try:
        from n8n_workflow_factory_v3 import AIEnhancedWorkflowFactory
    except ImportError:
        print("Error: Could not import N8N workflow factory v3")
        return False

    # Store original methods
    original_create_ai_workflow = AIEnhancedWorkflowFactory.create_ai_workflow
    original_generate_ai_workflow_nodes = (
        AIEnhancedWorkflowFactory.generate_ai_workflow_nodes
    )
    original_create_from_template = (
        AIEnhancedWorkflowFactory.create_from_template_with_ai
    )

    async def create_ai_workflow_with_telemetry(
        self,
        description: str,
        name: str,
        team: str,
        category: str = "ai-automation",
        force_pattern: str = None,
    ) -> Dict[str, Any]:
        """Enhanced create_ai_workflow with telemetry"""
        start_time = telemetry_client.start_timer()
        workflow_id = f"wf-{name.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        correlation_id = str(uuid.uuid4())

        try:
            # Call original method
            result = await original_create_ai_workflow(
                self, description, name, team, category, force_pattern
            )

            # Extract workflow details
            workflow = result.get("workflow", {})
            metadata = result.get("metadata", {})
            node_count = len(workflow.get("nodes", []))

            # Extract node types
            node_types = [
                node.get("type", "unknown") for node in workflow.get("nodes", [])
            ]
            ai_nodes = [nt for nt in node_types if "@n8n/n8n-nodes-langchain" in nt]

            # Record success telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_n8n(
                workflow_id="n8n-factory-v3",
                workflow_name="N8N AI Workflow Factory",
                node_name="create_ai_workflow",
                target_service="n8n",
                operation="create_workflow",
                status="success",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    "workflow_id": workflow_id,
                    "workflow_name": name,
                    "team": team,
                    "category": category,
                    "ai_pattern": metadata.get("ai_pattern"),
                    "is_ai_powered": metadata.get("is_ai_powered", False),
                    "node_count": node_count,
                    "ai_node_count": len(ai_nodes),
                    "node_types": list(set(node_types))[:10],  # First 10 unique types
                },
            )

            # Register in unified registry if Supabase is available
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
                try:
                    from supabase import create_client

                    client = create_client(
                        os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY")
                    )

                    # Extract capabilities from workflow
                    capabilities = self._extract_workflow_capabilities(workflow)

                    # Register workflow in unified registry
                    registry_data = {
                        "p_entity_id": workflow_id,
                        "p_entity_type": "n8n_workflow",
                        "p_entity_name": name,
                        "p_registered_by": "n8n_workflow_factory_v3",
                        "p_metadata": {
                            "description": description,
                            "team": team,
                            "category": category,
                            "ai_pattern": metadata.get("ai_pattern"),
                            "is_ai_powered": metadata.get("is_ai_powered", False),
                            "node_count": node_count,
                            "ai_node_count": len(ai_nodes),
                            "created_at": metadata.get(
                                "created_at", datetime.utcnow().isoformat()
                            ),
                        },
                        "p_capabilities": capabilities[:20],  # Limit to 20 capabilities
                        "p_endpoint_url": f"http://n8n:5678/webhook/{workflow_id}",
                        "p_parent_entity_id": f"team-{team}" if team else None,
                    }

                    client.rpc("register_entity", registry_data).execute()

                    # Update state to created
                    client.rpc(
                        "update_entity_state",
                        {
                            "p_entity_id": workflow_id,
                            "p_entity_type": "n8n_workflow",
                            "p_new_state": "created",
                            "p_health_status": "unknown",
                            "p_updated_by": "n8n_workflow_factory_v3",
                            "p_reason": "Workflow created successfully",
                        },
                    ).execute()

                except Exception as e:
                    print(
                        f"Warning: Could not register workflow in unified registry: {e}"
                    )

            # Add workflow_id to result
            result["workflow_id"] = workflow_id
            return result

        except Exception as e:
            # Record error telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_n8n(
                workflow_id="n8n-factory-v3",
                workflow_name="N8N AI Workflow Factory",
                node_name="create_ai_workflow",
                target_service="n8n",
                operation="create_workflow",
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata={
                    "workflow_name": name,
                    "team": team,
                    "category": category,
                },
            )
            raise

    def generate_ai_workflow_nodes_with_telemetry(self, pattern, config, name):
        """Enhanced generate_ai_workflow_nodes with telemetry"""
        start_time = telemetry_client.start_timer()
        correlation_id = str(uuid.uuid4())

        try:
            # Call original method
            result = original_generate_ai_workflow_nodes(self, pattern, config, name)

            # Record node generation telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            telemetry_client.record_n8n(
                workflow_id="n8n-factory-v3",
                workflow_name="N8N AI Workflow Factory",
                node_name="generate_nodes",
                target_service="n8n",
                operation="generate_ai_nodes",
                status="success",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    "pattern": pattern.name if pattern else "none",
                    "node_count": len(result.get("nodes", [])),
                    "has_memory": pattern.requires_memory if pattern else False,
                    "has_vector_store": bool(pattern.vector_stores)
                    if pattern
                    else False,
                    "agent_count": len(pattern.agent_types) if pattern else 0,
                },
            )

            return result

        except Exception as e:
            # Record error telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            telemetry_client.record_n8n(
                workflow_id="n8n-factory-v3",
                workflow_name="N8N AI Workflow Factory",
                node_name="generate_nodes",
                target_service="n8n",
                operation="generate_ai_nodes",
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata={
                    "pattern": pattern.name if pattern else "none",
                },
            )
            raise

    async def create_from_template_with_telemetry(
        self, template_name: str, customization_prompt: str, name: str, team: str
    ) -> Dict[str, Any]:
        """Enhanced create_from_template_with_ai with telemetry"""
        start_time = telemetry_client.start_timer()
        workflow_id = f"wf-{name.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        correlation_id = str(uuid.uuid4())

        try:
            # Call original method
            result = await original_create_from_template(
                self, template_name, customization_prompt, name, team
            )

            # Record success telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_n8n(
                workflow_id="n8n-factory-v3",
                workflow_name="N8N AI Workflow Factory",
                node_name="create_from_template",
                target_service="n8n",
                operation="customize_template",
                status="success",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    "workflow_id": workflow_id,
                    "workflow_name": name,
                    "template": template_name,
                    "team": team,
                    "customization_length": len(customization_prompt),
                },
            )

            # Register if successful
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
                try:
                    from supabase import create_client

                    client = create_client(
                        os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY")
                    )

                    # Register workflow
                    registry_data = {
                        "p_entity_id": workflow_id,
                        "p_entity_type": "n8n_workflow",
                        "p_entity_name": name,
                        "p_registered_by": "n8n_workflow_factory_v3",
                        "p_metadata": {
                            "base_template": template_name,
                            "customization": customization_prompt[
                                :200
                            ],  # First 200 chars
                            "team": team,
                            "created_at": result.get("metadata", {}).get(
                                "created_at", datetime.utcnow().isoformat()
                            ),
                        },
                        "p_capabilities": [
                            f"template:{template_name}",
                            "ai-customized",
                        ],
                        "p_endpoint_url": f"http://n8n:5678/webhook/{workflow_id}",
                    }

                    client.rpc("register_entity", registry_data).execute()

                except Exception as e:
                    print(f"Warning: Could not register template workflow: {e}")

            result["workflow_id"] = workflow_id
            return result

        except Exception as e:
            # Record error telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_n8n(
                workflow_id="n8n-factory-v3",
                workflow_name="N8N AI Workflow Factory",
                node_name="create_from_template",
                target_service="n8n",
                operation="customize_template",
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata={
                    "template": template_name,
                    "team": team,
                },
            )
            raise

    def _extract_workflow_capabilities(self, workflow: Dict[str, Any]) -> List[str]:
        """Extract capabilities from workflow nodes"""
        capabilities = []

        for node in workflow.get("nodes", []):
            node_type = node.get("type", "")

            # Standard capabilities
            if "webhook" in node_type:
                capabilities.append("webhook_trigger")
            elif "schedule" in node_type:
                capabilities.append("scheduled_execution")
            elif "http" in node_type:
                capabilities.append("http_requests")
            elif "database" in node_type or "postgres" in node_type:
                capabilities.append("database_operations")
            elif "supabase" in node_type:
                capabilities.append("supabase_integration")
            elif "slack" in node_type:
                capabilities.append("slack_messaging")
            elif "email" in node_type:
                capabilities.append("email_sending")

            # AI capabilities
            if "@n8n/n8n-nodes-langchain" in node_type:
                if "agent" in node_type:
                    capabilities.append("ai_agent")
                elif "vector" in node_type:
                    capabilities.append("vector_search")
                elif "memory" in node_type:
                    capabilities.append("conversation_memory")
                elif "chain" in node_type:
                    capabilities.append("llm_chain")
                elif "embeddings" in node_type:
                    capabilities.append("text_embeddings")

        # Remove duplicates
        return list(set(capabilities))

    # Patch the methods
    AIEnhancedWorkflowFactory.create_ai_workflow = create_ai_workflow_with_telemetry
    AIEnhancedWorkflowFactory.generate_ai_workflow_nodes = (
        generate_ai_workflow_nodes_with_telemetry
    )
    AIEnhancedWorkflowFactory.create_from_template_with_ai = (
        create_from_template_with_telemetry
    )
    AIEnhancedWorkflowFactory._extract_workflow_capabilities = (
        _extract_workflow_capabilities
    )

    print("✅ N8N workflow factory v3 patched with telemetry and registration")
    return True


def add_telemetry_to_workflow_nodes():
    """Add telemetry tracking to generated workflow nodes"""

    webhook_telemetry_node = {
        "name": "Telemetry Logger",
        "type": "n8n-nodes-base.code",
        "typeVersion": 1,
        "parameters": {
            "jsCode": """// Log workflow execution telemetry
const workflowId = $workflow.id;
const workflowName = $workflow.name;
const executionId = $execution.id;
const nodeCount = Object.keys($workflow.nodes).length;

// Send telemetry (would be sent to Supabase in production)
const telemetryData = {
    workflow_id: workflowId,
    workflow_name: workflowName,
    execution_id: executionId,
    timestamp: new Date().toISOString(),
    trigger_type: 'webhook',
    node_count: nodeCount,
    status: 'started'
};

// In production, this would send to Supabase
console.log('Workflow telemetry:', telemetryData);

return [{json: telemetryData}];"""
        },
        "position": [100, 100],
    }

    error_telemetry_node = {
        "name": "Error Telemetry",
        "type": "n8n-nodes-base.code",
        "typeVersion": 1,
        "parameters": {
            "jsCode": """// Log workflow error telemetry
const error = $input.item.json.error || 'Unknown error';
const workflowId = $workflow.id;
const failedNode = $input.item.json.failedNode || 'unknown';

// Send error telemetry
const errorTelemetry = {
    workflow_id: workflowId,
    workflow_name: $workflow.name,
    execution_id: $execution.id,
    timestamp: new Date().toISOString(),
    error_message: error,
    failed_node: failedNode,
    status: 'error'
};

// In production, this would send to Supabase
console.error('Workflow error telemetry:', errorTelemetry);

return [{json: errorTelemetry}];"""
        },
        "position": [500, 500],
    }

    print("📝 Telemetry nodes configured for workflows")
    return {
        "webhook_telemetry": webhook_telemetry_node,
        "error_telemetry": error_telemetry_node,
    }


if __name__ == "__main__":
    print("🔧 Patching N8N Workflow Factory V3 with Telemetry...")

    # Patch the factory
    if patch_n8n_workflow_factory():
        print("\n📋 N8N Workflow Factory V3 Telemetry Integration Complete!")
        print("\nFeatures added:")
        print("  - Telemetry tracking for AI workflow creation")
        print("  - Telemetry tracking for node generation")
        print("  - Telemetry tracking for template customization")
        print("  - Automatic registration in unified registry")
        print("  - Workflow capability extraction")
        print("  - Parent-child relationships (workflow → team)")
        print("  - Workflow execution telemetry nodes")

        print("\n🔄 Next steps:")
        print("  1. Import this patch in n8n_workflow_factory_v3.py")
        print("  2. Generated workflows will include telemetry nodes")
        print("  3. All workflow creation will be tracked")
        print("  4. Workflows auto-register with capabilities")
        print("  5. Set up N8N webhook for runtime telemetry")
    else:
        print("❌ Failed to patch N8N workflow factory")
