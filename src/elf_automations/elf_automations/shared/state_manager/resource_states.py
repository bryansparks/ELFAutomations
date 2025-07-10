"""
Resource-specific state managers that integrate with Supabase
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from supabase import Client

from .state_machine import (
    StateMachine,
    create_mcp_state_machine,
    create_team_state_machine,
    create_workflow_state_machine,
)

logger = logging.getLogger(__name__)


class ResourceStateManager(ABC):
    """
    Base class for managing resource states with Supabase integration
    """

    def __init__(self, supabase_client: Client, resource_type: str):
        self.supabase = supabase_client
        self.resource_type = resource_type
        self.state_machine = self._create_state_machine()

    @abstractmethod
    def _create_state_machine(self) -> StateMachine:
        """Create the appropriate state machine for this resource type"""
        pass

    def get_current_state(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get current state from database"""
        try:
            result = (
                self.supabase.table("resource_states")
                .select("*")
                .eq("resource_type", self.resource_type)
                .eq("resource_id", resource_id)
                .single()
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(
                f"Error getting state for {self.resource_type} {resource_id}: {str(e)}"
            )
            return None

    def transition_state(
        self,
        resource_id: str,
        resource_name: str,
        to_state: str,
        reason: str,
        transitioned_by: str,
        metadata: Dict[str, Any] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Transition resource to new state
        Returns: (success, error_message)
        """
        # Get current state
        current_state_data = self.get_current_state(resource_id)
        if current_state_data:
            self.state_machine._current_state = current_state_data["current_state"]

        # Validate transition
        is_valid, error = self.state_machine.validate_transition(to_state, metadata)
        if not is_valid:
            return False, error

        # Call Supabase function to transition state
        try:
            result = self.supabase.rpc(
                "transition_resource_state",
                {
                    "p_resource_type": self.resource_type,
                    "p_resource_id": resource_id,
                    "p_resource_name": resource_name,
                    "p_new_state": to_state,
                    "p_reason": reason,
                    "p_transitioned_by": transitioned_by,
                    "p_metadata": json.dumps(metadata) if metadata else "{}",
                },
            ).execute()

            # Update local state machine
            self.state_machine.transition_to(to_state, metadata, transitioned_by)

            return True, None
        except Exception as e:
            error_msg = f"Failed to transition state: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_state_history(
        self, resource_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get state transition history for a resource"""
        try:
            result = (
                self.supabase.table("state_transitions")
                .select("*")
                .eq("resource_type", self.resource_type)
                .eq("resource_id", resource_id)
                .order("transitioned_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return []

    def get_resources_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Get all resources in a specific state"""
        try:
            result = (
                self.supabase.table("resource_states")
                .select("*")
                .eq("resource_type", self.resource_type)
                .eq("current_state", state)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting resources by state: {str(e)}")
            return []

    def check_deployment_requirements(self, resource_id: str) -> Dict[str, Any]:
        """Check if all deployment requirements are satisfied"""
        try:
            result = self.supabase.rpc(
                "check_deployment_requirements",
                {"p_resource_type": self.resource_type, "p_resource_id": resource_id},
            ).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return {
                "all_satisfied": False,
                "pending_count": 0,
                "failed_count": 0,
                "requirements": [],
            }
        except Exception as e:
            logger.error(f"Error checking requirements: {str(e)}")
            return {
                "all_satisfied": False,
                "pending_count": 0,
                "failed_count": 0,
                "requirements": [],
                "error": str(e),
            }

    def add_deployment_requirement(
        self,
        resource_id: str,
        requirement_type: str,
        requirement_name: str,
        details: Dict[str, Any] = None,
    ) -> bool:
        """Add a deployment requirement for a resource"""
        try:
            self.supabase.table("deployment_requirements").insert(
                {
                    "resource_type": self.resource_type,
                    "resource_id": resource_id,
                    "requirement_type": requirement_type,
                    "requirement_name": requirement_name,
                    "requirement_details": details or {},
                }
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error adding requirement: {str(e)}")
            return False

    def update_requirement_status(
        self,
        resource_id: str,
        requirement_name: str,
        status: str,
        details: Dict[str, Any] = None,
    ) -> bool:
        """Update status of a deployment requirement"""
        try:
            update_data = {
                "requirement_status": status,
                "checked_at": datetime.utcnow().isoformat(),
            }

            if status == "satisfied":
                update_data["satisfied_at"] = datetime.utcnow().isoformat()

            if details:
                update_data["requirement_details"] = details

            self.supabase.table("deployment_requirements").update(update_data).eq(
                "resource_type", self.resource_type
            ).eq("resource_id", resource_id).eq(
                "requirement_name", requirement_name
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating requirement: {str(e)}")
            return False


class WorkflowStateManager(ResourceStateManager):
    """State manager for N8N workflows"""

    def __init__(self, supabase_client: Client):
        super().__init__(supabase_client, "workflow")

    def _create_state_machine(self) -> StateMachine:
        return create_workflow_state_machine()

    def register_workflow(
        self,
        workflow_id: str,
        workflow_name: str,
        owner_team: str,
        transitioned_by: str,
    ) -> Tuple[bool, Optional[str]]:
        """Register a new workflow"""
        return self.transition_state(
            workflow_id,
            workflow_name,
            "registered",
            f"Workflow registered by {owner_team}",
            transitioned_by,
            {"owner_team": owner_team},
        )

    def start_validation(
        self, workflow_id: str, workflow_name: str, validator: str
    ) -> Tuple[bool, Optional[str]]:
        """Start workflow validation"""
        return self.transition_state(
            workflow_id,
            workflow_name,
            "validating",
            "Starting validation process",
            validator,
        )

    def complete_validation(
        self,
        workflow_id: str,
        workflow_name: str,
        success: bool,
        validation_report: Dict[str, Any],
        validator: str,
    ) -> Tuple[bool, Optional[str]]:
        """Complete workflow validation"""
        to_state = "validated" if success else "failed_validation"
        return self.transition_state(
            workflow_id,
            workflow_name,
            to_state,
            "Validation completed",
            validator,
            {"validation_report": validation_report},
        )

    def deploy_workflow(
        self, workflow_id: str, workflow_name: str, n8n_id: str, deployer: str
    ) -> Tuple[bool, Optional[str]]:
        """Deploy workflow to N8N"""
        # First transition to deploying
        success, error = self.transition_state(
            workflow_id,
            workflow_name,
            "deploying",
            "Starting deployment to N8N",
            deployer,
            {"n8n_id": n8n_id},
        )

        if not success:
            return success, error

        # Simulate deployment completion (in real implementation, this would be async)
        return self.transition_state(
            workflow_id,
            workflow_name,
            "deployed",
            "Deployment completed successfully",
            deployer,
            {"n8n_id": n8n_id, "deployment_timestamp": datetime.utcnow().isoformat()},
        )

    def activate_workflow(
        self, workflow_id: str, workflow_name: str, activator: str
    ) -> Tuple[bool, Optional[str]]:
        """Activate a deployed workflow"""
        return self.transition_state(
            workflow_id, workflow_name, "active", "Workflow activated", activator
        )


class MCPStateManager(ResourceStateManager):
    """State manager for MCP servers and clients"""

    def __init__(self, supabase_client: Client):
        super().__init__(supabase_client, "mcp_server")

    def _create_state_machine(self) -> StateMachine:
        return create_mcp_state_machine()

    def register_mcp(
        self, mcp_id: str, mcp_name: str, mcp_type: str, category: str, registrar: str
    ) -> Tuple[bool, Optional[str]]:
        """Register a new MCP server/client"""
        # First add to MCP registry
        try:
            self.supabase.table("mcp_registry").insert(
                {
                    "id": mcp_id,
                    "name": mcp_name,
                    "display_name": mcp_name.replace("-", " ").title(),
                    "mcp_type": mcp_type,
                    "category": category,
                    "created_by": registrar,
                }
            ).execute()
        except Exception as e:
            return False, f"Failed to add to registry: {str(e)}"

        # Then transition state
        return self.transition_state(
            mcp_id,
            mcp_name,
            "registered",
            f"MCP {mcp_type} registered",
            registrar,
            {"mcp_type": mcp_type, "category": category},
        )

    def build_image(
        self, mcp_id: str, mcp_name: str, builder: str
    ) -> Tuple[bool, Optional[str]]:
        """Start building Docker image"""
        return self.transition_state(
            mcp_id, mcp_name, "building", "Starting Docker build", builder
        )

    def complete_build(
        self, mcp_id: str, mcp_name: str, success: bool, image_tag: str, builder: str
    ) -> Tuple[bool, Optional[str]]:
        """Complete Docker build"""
        if success:
            return self.transition_state(
                mcp_id,
                mcp_name,
                "built",
                "Docker build completed",
                builder,
                {"image_tag": image_tag},
            )
        else:
            return self.transition_state(
                mcp_id, mcp_name, "failed", "Docker build failed", builder
            )

    def health_check(
        self, mcp_id: str, mcp_name: str, checker: str
    ) -> Tuple[bool, Optional[str]]:
        """Run health check on deployed MCP"""
        return self.transition_state(
            mcp_id, mcp_name, "health_checking", "Running health checks", checker
        )

    def complete_health_check(
        self,
        mcp_id: str,
        mcp_name: str,
        success: bool,
        health_report: Dict[str, Any],
        checker: str,
    ) -> Tuple[bool, Optional[str]]:
        """Complete health check"""
        if success:
            return self.transition_state(
                mcp_id,
                mcp_name,
                "available",
                "Health check passed",
                checker,
                {"health_report": health_report},
            )
        else:
            return self.transition_state(
                mcp_id,
                mcp_name,
                "failed",
                "Health check failed",
                checker,
                {"health_report": health_report},
            )


class TeamStateManager(ResourceStateManager):
    """State manager for Teams"""

    def __init__(self, supabase_client: Client):
        super().__init__(supabase_client, "team")

    def _create_state_machine(self) -> StateMachine:
        return create_team_state_machine()

    def register_team(
        self,
        team_id: str,
        team_name: str,
        department: str,
        framework: str,
        registrar: str,
    ) -> Tuple[bool, Optional[str]]:
        """Register a new team"""
        return self.transition_state(
            team_id,
            team_name,
            "registered",
            f"Team registered in {department} department",
            registrar,
            {"department": department, "framework": framework},
        )

    def check_team_dependencies(
        self, team_id: str, team_name: str, dependencies: List[str], checker: str
    ) -> Tuple[bool, Optional[str]]:
        """Check if team dependencies are satisfied"""
        # Add requirements for each dependency
        for dep in dependencies:
            self.add_deployment_requirement(
                team_id, "dependency", dep, {"type": "team_dependency"}
            )

        # Check current status
        req_status = self.check_deployment_requirements(team_id)

        if req_status["all_satisfied"]:
            return self.transition_state(
                team_id,
                team_name,
                "active",
                "All dependencies satisfied",
                checker,
                {"dependencies": dependencies},
            )
        else:
            return self.transition_state(
                team_id,
                team_name,
                "awaiting_dependencies",
                f"{req_status['pending_count']} dependencies pending",
                checker,
                {"dependencies": dependencies, "requirements": req_status},
            )

    def scale_team(
        self, team_id: str, team_name: str, replicas: int, scaler: str
    ) -> Tuple[bool, Optional[str]]:
        """Scale team deployment"""
        return self.transition_state(
            team_id,
            team_name,
            "scaling",
            f"Scaling to {replicas} replicas",
            scaler,
            {"target_replicas": replicas},
        )

    def complete_scaling(
        self,
        team_id: str,
        team_name: str,
        success: bool,
        actual_replicas: int,
        scaler: str,
    ) -> Tuple[bool, Optional[str]]:
        """Complete scaling operation"""
        if success:
            return self.transition_state(
                team_id,
                team_name,
                "active",
                f"Scaled to {actual_replicas} replicas",
                scaler,
                {"replicas": actual_replicas},
            )
        else:
            return self.transition_state(
                team_id,
                team_name,
                "active",
                "Scaling failed, remaining at current replicas",
                scaler,
            )
