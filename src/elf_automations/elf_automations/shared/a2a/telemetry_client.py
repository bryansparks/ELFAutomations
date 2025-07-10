"""
Enhanced A2A Client with integrated telemetry support
This wraps the existing A2A client to add lightweight telemetry
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from ..telemetry import telemetry_client
from .client import A2AClient


class A2AClientWithTelemetry(A2AClient):
    """A2A Client with integrated telemetry support"""

    def __init__(
        self,
        team_id: str,
        team_endpoint: str = "http://localhost:8090",
        timeout: int = 300,
        gateway_url: Optional[str] = None,
        use_gateway: bool = True,
        enable_telemetry: bool = True,
    ):
        """Initialize A2A client with telemetry support"""
        super().__init__(team_id, team_endpoint, timeout, gateway_url, use_gateway)
        self.enable_telemetry = enable_telemetry

    async def send_task(
        self,
        target_team: str,
        task_description: str,
        context: Dict[str, Any] = None,
        deadline_seconds: int = 3600,
        required_capabilities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send a task with telemetry tracking"""
        if not self.enable_telemetry:
            return await super().send_task(
                target_team,
                task_description,
                context,
                deadline_seconds,
                required_capabilities,
            )

        # Generate correlation ID for tracing
        correlation_id = str(uuid.uuid4())
        start_time = telemetry_client.start_timer()

        # Track telemetry data
        telemetry_metadata = {
            "capabilities_required": required_capabilities,
            "has_context": bool(context),
            "deadline_seconds": deadline_seconds,
            "via_gateway": self.use_gateway and bool(self.gateway_url),
        }

        try:
            # Call parent method
            result = await super().send_task(
                target_team,
                task_description,
                context,
                deadline_seconds,
                required_capabilities,
            )

            # Record success telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_a2a(
                source_team=self.team_id,
                target_team=target_team or "capability-based",
                operation="send_task",
                task_description=task_description,
                status="success",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata=telemetry_metadata,
            )

            return result

        except Exception as e:
            # Record error telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_a2a(
                source_team=self.team_id,
                target_team=target_team or "capability-based",
                operation="send_task",
                task_description=task_description,
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata=telemetry_metadata,
            )
            raise

    async def discover_teams(
        self, capability: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Discover teams with telemetry tracking"""
        if not self.enable_telemetry:
            return await super().discover_teams(capability)

        start_time = telemetry_client.start_timer()
        correlation_id = str(uuid.uuid4())

        try:
            result = await super().discover_teams(capability)

            # Record discovery telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_a2a(
                source_team=self.team_id,
                target_team="gateway",
                operation="discover_teams",
                status="success",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata={"capability_filter": capability, "teams_found": len(result)},
            )

            return result

        except Exception as e:
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_a2a(
                source_team=self.team_id,
                target_team="gateway",
                operation="discover_teams",
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata={"capability_filter": capability},
            )
            raise

    async def get_capabilities(
        self, target_team: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get capabilities with telemetry tracking"""
        if not self.enable_telemetry:
            return await super().get_capabilities(target_team)

        start_time = telemetry_client.start_timer()
        correlation_id = str(uuid.uuid4())

        try:
            result = await super().get_capabilities(target_team)

            # Record capability query telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_a2a(
                source_team=self.team_id,
                target_team=target_team or "gateway",
                operation="get_capabilities",
                status="success",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata={"target_specified": bool(target_team)},
            )

            return result

        except Exception as e:
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            await telemetry_client.record_a2a(
                source_team=self.team_id,
                target_team=target_team or "gateway",
                operation="get_capabilities",
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata={"target_specified": bool(target_team)},
            )
            raise


# Factory function to create A2A client with telemetry
def create_a2a_client(
    team_id: str,
    team_endpoint: str = "http://localhost:8090",
    timeout: int = 300,
    gateway_url: Optional[str] = None,
    use_gateway: bool = True,
    enable_telemetry: bool = True,
) -> A2AClient:
    """
    Create an A2A client with optional telemetry support

    Args:
        team_id: ID of the team using this client
        team_endpoint: Base URL of this team's A2A server
        timeout: Request timeout in seconds
        gateway_url: URL of the A2A Gateway (optional)
        use_gateway: Whether to route through gateway
        enable_telemetry: Whether to enable telemetry tracking

    Returns:
        A2AClient instance (with or without telemetry)
    """
    if enable_telemetry:
        return A2AClientWithTelemetry(
            team_id=team_id,
            team_endpoint=team_endpoint,
            timeout=timeout,
            gateway_url=gateway_url,
            use_gateway=use_gateway,
            enable_telemetry=True,
        )
    else:
        return A2AClient(
            team_id=team_id,
            team_endpoint=team_endpoint,
            timeout=timeout,
            gateway_url=gateway_url,
            use_gateway=use_gateway,
        )
