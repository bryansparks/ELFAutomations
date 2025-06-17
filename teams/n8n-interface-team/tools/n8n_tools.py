"""
N8N workflow integration tools for the n8n-interface team.
"""

from typing import Any, Dict, List, Optional
from langchain.tools import tool
import logging
import requests
import json
from datetime import datetime
from elf_automations.shared.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


@tool
def trigger_n8n_workflow(
    workflow_id: str,
    webhook_path: str,
    payload: Dict[str, Any],
    n8n_base_url: str = None
) -> Dict[str, Any]:
    """
    Trigger an n8n workflow via webhook.
    
    Args:
        workflow_id: The n8n workflow ID
        webhook_path: The webhook path configured in n8n
        payload: Data to send to the workflow
        n8n_base_url: Base URL of n8n instance (from env if not provided)
    
    Returns:
        Dict containing execution_id and status
    """
    try:
        if not n8n_base_url:
            import os
            n8n_base_url = os.getenv("N8N_BASE_URL", "http://n8n:5678")
        
        # Construct webhook URL
        webhook_url = f"{n8n_base_url}/webhook/{webhook_path}"
        
        # Trigger workflow
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        
        # Log execution to Supabase
        supabase = get_supabase_client()
        execution_record = {
            "workflow_id": workflow_id,
            "webhook_path": webhook_path,
            "payload": payload,
            "status": "triggered",
            "triggered_at": datetime.utcnow().isoformat(),
            "response_data": response.json() if response.text else {}
        }
        
        supabase.table("workflow_executions").insert(execution_record).execute()
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "status": "triggered",
            "response": response.json() if response.text else {"message": "Workflow triggered"}
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to trigger workflow {workflow_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "workflow_id": workflow_id
        }


@tool
def check_workflow_execution_status(execution_id: str) -> Dict[str, Any]:
    """
    Check the status of a workflow execution.
    
    Args:
        execution_id: The execution ID from n8n
    
    Returns:
        Dict containing execution status and results
    """
    try:
        # Query Supabase for execution status
        supabase = get_supabase_client()
        result = supabase.table("workflow_executions").select("*").eq("execution_id", execution_id).execute()
        
        if result.data:
            return {
                "success": True,
                "execution": result.data[0]
            }
        else:
            return {
                "success": False,
                "error": "Execution not found"
            }
            
    except Exception as e:
        logger.error(f"Failed to check execution status: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def list_available_workflows() -> List[Dict[str, Any]]:
    """
    List all available n8n workflows from the registry.
    
    Returns:
        List of workflow definitions with their schemas
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("workflow_registry").select("*").eq("active", True).execute()
        
        workflows = []
        for workflow in result.data:
            workflows.append({
                "id": workflow["workflow_id"],
                "name": workflow["name"],
                "description": workflow["description"],
                "webhook_path": workflow["webhook_path"],
                "input_schema": workflow["input_schema"],
                "output_schema": workflow["output_schema"],
                "tags": workflow.get("tags", [])
            })
        
        return workflows
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        return []


@tool
def validate_workflow_input(
    workflow_id: str,
    input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate input data against a workflow's schema.
    
    Args:
        workflow_id: The workflow ID to validate against
        input_data: The data to validate
    
    Returns:
        Dict with validation results
    """
    try:
        # Get workflow schema from registry
        supabase = get_supabase_client()
        result = supabase.table("workflow_registry").select("input_schema").eq("workflow_id", workflow_id).execute()
        
        if not result.data:
            return {
                "valid": False,
                "errors": ["Workflow not found in registry"]
            }
        
        schema = result.data[0]["input_schema"]
        
        # Basic validation (can be enhanced with jsonschema)
        errors = []
        required_fields = schema.get("required", [])
        
        for field in required_fields:
            if field not in input_data:
                errors.append(f"Missing required field: {field}")
        
        # Type validation
        properties = schema.get("properties", {})
        for field, value in input_data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type:
                    actual_type = type(value).__name__
                    type_map = {
                        "string": "str",
                        "number": "float",
                        "integer": "int",
                        "boolean": "bool",
                        "object": "dict",
                        "array": "list"
                    }
                    if type_map.get(expected_type) != actual_type:
                        errors.append(f"Field '{field}' should be {expected_type}, got {actual_type}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Failed to validate input: {e}")
        return {
            "valid": False,
            "errors": [str(e)]
        }


@tool
def update_workflow_registry(
    workflow_id: str,
    name: str,
    description: str,
    webhook_path: str,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any] = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    Update or create a workflow entry in the registry.
    
    Args:
        workflow_id: Unique workflow identifier
        name: Human-readable workflow name
        description: What the workflow does
        webhook_path: The webhook path to trigger it
        input_schema: JSON schema for input validation
        output_schema: JSON schema for output (optional)
        tags: Tags for categorization
    
    Returns:
        Dict with update status
    """
    try:
        supabase = get_supabase_client()
        
        workflow_data = {
            "workflow_id": workflow_id,
            "name": name,
            "description": description,
            "webhook_path": webhook_path,
            "input_schema": input_schema,
            "output_schema": output_schema or {},
            "tags": tags or [],
            "active": True,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Upsert the workflow
        result = supabase.table("workflow_registry").upsert(workflow_data).execute()
        
        return {
            "success": True,
            "workflow": result.data[0] if result.data else workflow_data
        }
        
    except Exception as e:
        logger.error(f"Failed to update registry: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def record_workflow_error(
    workflow_id: str,
    execution_id: str,
    error_type: str,
    error_message: str,
    retry_count: int = 0
) -> Dict[str, Any]:
    """
    Record a workflow execution error for tracking and analysis.
    
    Args:
        workflow_id: The workflow that failed
        execution_id: The execution that failed
        error_type: Type of error (validation, execution, timeout, etc.)
        error_message: Detailed error message
        retry_count: Number of retries attempted
    
    Returns:
        Dict with recording status
    """
    try:
        supabase = get_supabase_client()
        
        error_record = {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": retry_count,
            "occurred_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("workflow_errors").insert(error_record).execute()
        
        # Update execution status
        supabase.table("workflow_executions").update({
            "status": "failed",
            "error": error_message,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("execution_id", execution_id).execute()
        
        return {
            "success": True,
            "error_recorded": True
        }
        
    except Exception as e:
        logger.error(f"Failed to record error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Export all tools
n8n_tools = [
    trigger_n8n_workflow,
    check_workflow_execution_status,
    list_available_workflows,
    validate_workflow_input,
    update_workflow_registry,
    record_workflow_error
]