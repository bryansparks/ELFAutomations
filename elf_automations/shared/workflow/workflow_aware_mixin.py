"""
Workflow-Aware Mixin for Teams

This mixin allows any team to participate in workflow orchestration.
Teams that include this mixin can:
- Check for assigned workflow tasks
- Claim and execute tasks
- Report results back to workflows
- Handle workflow-specific error cases
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..mcp.client import MCPClient
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WorkflowAwareMixin:
    """
    Mixin to make teams workflow-aware.

    Add this to any team agent to enable workflow participation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow_client = None
        self.workflow_handlers = {}
        self.workflow_check_interval = 30  # seconds
        self._workflow_task = None

    async def initialize_workflow_client(self):
        """Initialize connection to workflow engine MCP."""
        try:
            self.workflow_client = MCPClient("workflow-engine")
            await self.workflow_client.connect()
            logger.info(f"Team {self.team_id} connected to workflow engine")
        except Exception as e:
            logger.error(f"Failed to connect to workflow engine: {e}")
            # Continue without workflow support
            self.workflow_client = None

    def register_workflow_handler(self, action: str, handler: Callable):
        """
        Register a handler for a specific workflow action.

        Args:
            action: The workflow action name (e.g., 'validate_customer_data')
            handler: Async function that handles the action
        """
        self.workflow_handlers[action] = handler
        logger.info(f"Registered workflow handler for action: {action}")

    async def start_workflow_monitoring(self):
        """Start monitoring for workflow tasks."""
        if not self.workflow_client:
            await self.initialize_workflow_client()

        if self.workflow_client:
            self._workflow_task = asyncio.create_task(self._workflow_monitor_loop())
            logger.info(f"Started workflow monitoring for team {self.team_id}")

    async def stop_workflow_monitoring(self):
        """Stop monitoring for workflow tasks."""
        if self._workflow_task:
            self._workflow_task.cancel()
            try:
                await self._workflow_task
            except asyncio.CancelledError:
                pass
            logger.info(f"Stopped workflow monitoring for team {self.team_id}")

    async def _workflow_monitor_loop(self):
        """Main loop for checking workflow tasks."""
        while True:
            try:
                await self.check_workflow_tasks()
                await asyncio.sleep(self.workflow_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in workflow monitor loop: {e}")
                await asyncio.sleep(self.workflow_check_interval)

    async def check_workflow_tasks(self) -> List[Dict]:
        """Check for assigned workflow tasks."""
        if not self.workflow_client:
            return []

        try:
            # Get pending tasks for this team
            response = await self.workflow_client.call_tool(
                "get_team_tasks",
                {
                    "team_id": self.team_id,
                    "status": "pending",
                    "limit": 5,  # Process up to 5 tasks at once
                },
            )

            tasks = response.get("tasks", [])

            if tasks:
                logger.info(
                    f"Found {len(tasks)} workflow tasks for team {self.team_id}"
                )

                # Process each task
                for task in tasks:
                    await self.process_workflow_task(task)

            return tasks

        except Exception as e:
            logger.error(f"Error checking workflow tasks: {e}")
            return []

    async def process_workflow_task(self, task: Dict):
        """Process a single workflow task."""
        task_id = task["id"]
        action = task["task_type"]

        logger.info(f"Processing workflow task {task_id}: {action}")

        # Check if we have a handler for this action
        if action not in self.workflow_handlers:
            logger.warning(f"No handler registered for action: {action}")
            await self.decline_task(task_id, f"No handler for action: {action}")
            return

        try:
            # Claim the task
            claimed = await self.claim_workflow_task(task_id)
            if not claimed:
                logger.info(f"Could not claim task {task_id} (already claimed?)")
                return

            # Execute the handler
            handler = self.workflow_handlers[action]
            result = await handler(task["input_data"])

            # Report success
            await self.complete_workflow_task(task_id, result)
            logger.info(f"Completed workflow task {task_id}")

        except Exception as e:
            logger.error(f"Error processing workflow task {task_id}: {e}")
            await self.fail_workflow_task(task_id, str(e))

    async def claim_workflow_task(self, task_id: str) -> bool:
        """Claim a workflow task."""
        try:
            response = await self.workflow_client.call_tool(
                "claim_task",
                {
                    "task_id": task_id,
                    "team_id": self.team_id,
                    "agent_id": getattr(self, "agent_id", self.team_id),
                },
            )
            return response.get("claimed", False)
        except Exception as e:
            logger.error(f"Error claiming task {task_id}: {e}")
            return False

    async def complete_workflow_task(self, task_id: str, output: Any):
        """Mark a workflow task as completed with output."""
        try:
            await self.workflow_client.call_tool(
                "complete_task",
                {
                    "task_id": task_id,
                    "output": output,
                    "completed_by": getattr(self, "agent_id", self.team_id),
                },
            )
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            raise

    async def fail_workflow_task(self, task_id: str, error: str):
        """Mark a workflow task as failed."""
        try:
            await self.workflow_client.call_tool(
                "fail_task",
                {
                    "task_id": task_id,
                    "error": error,
                    "failed_by": getattr(self, "agent_id", self.team_id),
                },
            )
        except Exception as e:
            logger.error(f"Error failing task {task_id}: {e}")

    async def decline_task(self, task_id: str, reason: str):
        """Decline a task that we can't handle."""
        try:
            await self.workflow_client.call_tool(
                "decline_task",
                {
                    "task_id": task_id,
                    "reason": reason,
                    "declined_by": getattr(self, "agent_id", self.team_id),
                },
            )
        except Exception as e:
            logger.error(f"Error declining task {task_id}: {e}")

    async def start_workflow(self, workflow_name: str, inputs: Dict) -> Optional[str]:
        """
        Start a new workflow instance.

        Teams can trigger workflows when they identify the need for
        complex multi-team coordination.
        """
        if not self.workflow_client:
            logger.error("Workflow client not initialized")
            return None

        try:
            response = await self.workflow_client.call_tool(
                "start_workflow",
                {
                    "workflow_name": workflow_name,
                    "inputs": inputs,
                    "triggered_by": self.team_id,
                },
            )

            instance_id = response.get("instance_id")
            logger.info(f"Started workflow {workflow_name}: {instance_id}")
            return instance_id

        except Exception as e:
            logger.error(f"Error starting workflow {workflow_name}: {e}")
            return None

    async def get_workflow_status(self, instance_id: str) -> Optional[Dict]:
        """Check the status of a workflow instance."""
        if not self.workflow_client:
            return None

        try:
            response = await self.workflow_client.call_tool(
                "get_instance_status", {"instance_id": instance_id}
            )
            return response
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return None


# Example of how a team would use this mixin
class WorkflowAwareTeamExample:
    """Example team that can participate in workflows."""

    def __init__(self):
        self.team_id = "example-team"
        # Initialize mixin
        WorkflowAwareMixin.__init__(self)

        # Register handlers for workflow actions
        self.register_workflow_handler("validate_data", self.handle_validate_data)
        self.register_workflow_handler("process_order", self.handle_process_order)

    async def handle_validate_data(self, input_data: Dict) -> Dict:
        """Handle data validation workflow task."""
        # Perform validation logic
        is_valid = self._validate(input_data)

        return {
            "is_valid": is_valid,
            "validation_errors": [] if is_valid else ["Invalid format"],
            "validated_at": datetime.utcnow().isoformat(),
        }

    async def handle_process_order(self, input_data: Dict) -> Dict:
        """Handle order processing workflow task."""
        order_id = input_data.get("order_id")

        # Process the order
        result = await self._process_order(order_id)

        return {
            "order_id": order_id,
            "status": "processed",
            "tracking_number": result.get("tracking_number"),
            "estimated_delivery": result.get("delivery_date"),
        }

    def _validate(self, data: Dict) -> bool:
        """Validation logic."""
        return "required_field" in data

    async def _process_order(self, order_id: str) -> Dict:
        """Order processing logic."""
        # Simulate processing
        await asyncio.sleep(1)
        return {"tracking_number": f"TRK-{order_id}", "delivery_date": "2025-01-25"}
