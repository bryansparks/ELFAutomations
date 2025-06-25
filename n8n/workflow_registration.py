"""
N8N Workflow Registration System
Ensures all N8N workflows are registered in the unified registry
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class N8NWorkflowRegistry:
    """Manages N8N workflow registration and state tracking"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize registry with Supabase connection"""
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials required for workflow registry")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def register_workflow(
        self,
        workflow_id: str,
        workflow_name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        webhook_url: Optional[str] = None,
        schedule: Optional[str] = None,
        created_by: str = "n8n",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register an N8N workflow in the unified registry
        
        Args:
            workflow_id: Unique workflow identifier from N8N
            workflow_name: Human-readable workflow name
            description: Workflow description
            tags: Categorization tags
            nodes: List of nodes in the workflow
            webhook_url: Webhook endpoint if applicable
            schedule: Cron schedule if applicable
            created_by: User or system that created the workflow
            metadata: Additional workflow metadata
        
        Returns:
            Registration result
        """
        try:
            # Extract capabilities from nodes
            capabilities = self._extract_capabilities(nodes) if nodes else []
            
            # Build metadata
            workflow_metadata = {
                "description": description,
                "node_count": len(nodes) if nodes else 0,
                "node_types": list(set(node.get("type") for node in (nodes or []))),
                "has_webhook": bool(webhook_url),
                "has_schedule": bool(schedule),
                "schedule": schedule,
                **(metadata or {})
            }
            
            # Register in unified registry
            registry_data = {
                "entity_id": workflow_id,
                "entity_type": "n8n_workflow",
                "entity_name": workflow_name,
                "display_name": workflow_name,
                "registered_by": created_by,
                "registration_source": "n8n",
                "current_state": "registered",
                "health_status": "unknown",
                "endpoint_url": webhook_url,
                "deployment_type": "n8n",
                "capabilities": capabilities,
                "tags": tags or [],
                "metadata": workflow_metadata
            }
            
            # Check if already exists
            existing = self.client.table("unified_registry").select("*").eq(
                "entity_id", workflow_id
            ).eq("entity_type", "n8n_workflow").execute()
            
            if existing.data:
                # Update existing
                result = self.client.table("unified_registry").update(registry_data).eq(
                    "entity_id", workflow_id
                ).eq("entity_type", "n8n_workflow").execute()
                action = "updated"
            else:
                # Insert new
                result = self.client.table("unified_registry").insert(registry_data).execute()
                action = "registered"
            
            # Log registration audit
            audit_data = {
                "entity_id": workflow_id,
                "entity_type": "n8n_workflow",
                "action": action,
                "action_by": created_by,
                "details": {
                    "workflow_name": workflow_name,
                    "capabilities": capabilities,
                    "node_count": len(nodes) if nodes else 0
                }
            }
            self.client.table("registration_audit").insert(audit_data).execute()
            
            logger.info(f"Workflow {workflow_name} ({workflow_id}) {action} successfully")
            return {"status": "success", "action": action, "workflow_id": workflow_id}
            
        except Exception as e:
            logger.error(f"Failed to register workflow {workflow_name}: {e}")
            return {"status": "error", "error": str(e)}
    
    def update_workflow_state(
        self,
        workflow_id: str,
        state: str,
        health_status: Optional[str] = None,
        reason: Optional[str] = None,
        updated_by: str = "system"
    ) -> bool:
        """Update workflow state and health status"""
        try:
            # Call the database function
            result = self.client.rpc(
                "update_entity_state",
                {
                    "p_entity_id": workflow_id,
                    "p_entity_type": "n8n_workflow",
                    "p_new_state": state,
                    "p_health_status": health_status,
                    "p_updated_by": updated_by,
                    "p_reason": reason
                }
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update workflow state: {e}")
            return False
    
    def record_workflow_activity(
        self,
        workflow_id: str,
        is_error: bool = False
    ):
        """Record workflow execution activity"""
        try:
            self.client.rpc(
                "record_entity_activity",
                {
                    "p_entity_id": workflow_id,
                    "p_entity_type": "n8n_workflow",
                    "p_is_error": is_error
                }
            ).execute()
        except Exception as e:
            logger.debug(f"Failed to record workflow activity: {e}")
    
    def get_workflow_info(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow registration info"""
        try:
            result = self.client.table("unified_registry").select("*").eq(
                "entity_id", workflow_id
            ).eq("entity_type", "n8n_workflow").execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get workflow info: {e}")
            return None
    
    def list_workflows(
        self,
        tags: Optional[List[str]] = None,
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List registered workflows with optional filters"""
        try:
            query = self.client.table("unified_registry").select("*").eq(
                "entity_type", "n8n_workflow"
            )
            
            if state:
                query = query.eq("current_state", state)
            
            if tags:
                # Filter by tags (contains any of the specified tags)
                query = query.contains("tags", tags)
            
            query = query.limit(limit).order("last_updated", desc=True)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []
    
    def _extract_capabilities(self, nodes: List[Dict[str, Any]]) -> List[str]:
        """Extract capabilities from workflow nodes"""
        capabilities = set()
        
        for node in nodes:
            node_type = node.get("type", "")
            
            # Map node types to capabilities
            if "http" in node_type.lower():
                capabilities.add("http_request")
            elif "webhook" in node_type.lower():
                capabilities.add("webhook_trigger")
            elif "database" in node_type.lower() or "postgres" in node_type.lower():
                capabilities.add("database_access")
            elif "email" in node_type.lower():
                capabilities.add("email_send")
            elif "slack" in node_type.lower():
                capabilities.add("slack_integration")
            elif "schedule" in node_type.lower() or "cron" in node_type.lower():
                capabilities.add("scheduled_execution")
            elif "function" in node_type.lower() or "code" in node_type.lower():
                capabilities.add("custom_code")
            elif "ai" in node_type.lower() or "openai" in node_type.lower():
                capabilities.add("ai_integration")
            
            # Check for specific integrations
            if node.get("parameters", {}).get("operation"):
                capabilities.add(f"{node_type}_{node['parameters']['operation']}")
        
        return list(capabilities)


# N8N Webhook handler for auto-registration
class N8NWebhookHandler:
    """Handles N8N webhook events for workflow registration"""
    
    def __init__(self, registry: N8NWorkflowRegistry):
        self.registry = registry
    
    async def handle_workflow_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle N8N workflow events (create, update, delete, execute)
        
        Expected event format:
        {
            "event": "workflow.created" | "workflow.updated" | "workflow.deleted" | "workflow.executed",
            "workflow": {
                "id": "...",
                "name": "...",
                "nodes": [...],
                "settings": {...}
            },
            "execution": {...}  // For execution events
        }
        """
        event_type = event_data.get("event", "")
        workflow_data = event_data.get("workflow", {})
        
        if not workflow_data.get("id"):
            return {"status": "error", "error": "No workflow ID provided"}
        
        workflow_id = workflow_data["id"]
        workflow_name = workflow_data.get("name", f"Workflow {workflow_id}")
        
        try:
            if event_type in ["workflow.created", "workflow.updated"]:
                # Register or update workflow
                result = self.registry.register_workflow(
                    workflow_id=workflow_id,
                    workflow_name=workflow_name,
                    nodes=workflow_data.get("nodes", []),
                    tags=workflow_data.get("tags", []),
                    metadata=workflow_data.get("settings", {})
                )
                
                # Set active state
                self.registry.update_workflow_state(
                    workflow_id=workflow_id,
                    state="active",
                    health_status="healthy",
                    reason=f"Workflow {event_type.split('.')[1]}"
                )
                
                return result
                
            elif event_type == "workflow.deleted":
                # Mark as deleted
                self.registry.update_workflow_state(
                    workflow_id=workflow_id,
                    state="deleted",
                    health_status="none",
                    reason="Workflow deleted from N8N"
                )
                return {"status": "success", "action": "deleted"}
                
            elif event_type == "workflow.executed":
                # Record activity
                execution_data = event_data.get("execution", {})
                is_error = execution_data.get("status") == "error"
                
                self.registry.record_workflow_activity(
                    workflow_id=workflow_id,
                    is_error=is_error
                )
                
                # Update health based on execution
                if is_error:
                    self.registry.update_workflow_state(
                        workflow_id=workflow_id,
                        state="active",
                        health_status="degraded",
                        reason=f"Execution error: {execution_data.get('error', 'Unknown')}"
                    )
                else:
                    self.registry.update_workflow_state(
                        workflow_id=workflow_id,
                        state="active",
                        health_status="healthy",
                        reason="Successful execution"
                    )
                
                return {"status": "success", "action": "activity_recorded"}
                
            else:
                return {"status": "error", "error": f"Unknown event type: {event_type}"}
                
        except Exception as e:
            logger.error(f"Failed to handle N8N event: {e}")
            return {"status": "error", "error": str(e)}