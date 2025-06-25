"""
Lightweight telemetry client for fire-and-forget communication tracking
"""

import asyncio
import logging
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class TelemetryClient:
    """Lightweight telemetry client for tracking communications"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize telemetry client with Supabase connection"""
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        
        self._client: Optional[Client] = None
        self._enabled = bool(self.supabase_url and self.supabase_key)
        
        if not self._enabled:
            logger.info("Telemetry disabled - no Supabase credentials")
    
    @property
    def client(self) -> Optional[Client]:
        """Lazy load Supabase client"""
        if self._enabled and not self._client:
            try:
                self._client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                logger.error(f"Failed to create Supabase client: {e}")
                self._enabled = False
        return self._client
    
    async def record_a2a(
        self,
        source_team: str,
        target_team: str,
        operation: str = "send_task",
        task_description: Optional[str] = None,
        status: str = "success",
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record A2A communication telemetry"""
        if not self._enabled:
            return
        
        try:
            data = {
                "protocol": "a2a",
                "source_id": source_team,
                "source_type": "team",
                "target_id": target_team,
                "target_type": "team",
                "operation": operation,
                "status": status,
                "duration_ms": duration_ms,
                "task_description": task_description[:500] if task_description else None,
                "error_message": error_message,
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "metadata": metadata or {}
            }
            
            # Fire and forget - don't await
            asyncio.create_task(self._insert_telemetry(data))
            
        except Exception as e:
            logger.debug(f"Telemetry error (ignored): {e}")
    
    async def record_mcp(
        self,
        source_id: str,
        source_type: str = "team",
        mcp_name: str = None,
        tool_name: str = None,
        operation: str = "tool_call",
        status: str = "success",
        duration_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record MCP communication telemetry"""
        if not self._enabled:
            return
        
        try:
            data = {
                "protocol": "mcp",
                "source_id": source_id,
                "source_type": source_type,
                "target_id": mcp_name or "unknown",
                "target_type": "mcp",
                "operation": operation,
                "tool_name": tool_name,
                "status": status,
                "duration_ms": duration_ms,
                "tokens_used": tokens_used,
                "error_message": error_message,
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "metadata": metadata or {}
            }
            
            # Fire and forget
            asyncio.create_task(self._insert_telemetry(data))
            
        except Exception as e:
            logger.debug(f"Telemetry error (ignored): {e}")
    
    async def record_n8n(
        self,
        workflow_id: str,
        workflow_name: str,
        node_name: str,
        target_service: str,
        operation: str = "workflow_step",
        status: str = "success",
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record N8N workflow telemetry"""
        if not self._enabled:
            return
        
        try:
            data = {
                "protocol": "n8n",
                "source_id": workflow_id,
                "source_type": "workflow",
                "target_id": target_service,
                "target_type": "external",
                "operation": operation,
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "workflow_node": node_name,
                "status": status,
                "duration_ms": duration_ms,
                "error_message": error_message,
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "metadata": metadata or {}
            }
            
            # Fire and forget
            asyncio.create_task(self._insert_telemetry(data))
            
        except Exception as e:
            logger.debug(f"Telemetry error (ignored): {e}")
    
    async def _insert_telemetry(self, data: Dict[str, Any]):
        """Insert telemetry data to Supabase"""
        try:
            if self.client:
                # Use execute() for async operation
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.table("communication_telemetry").insert(data).execute()
                )
        except Exception as e:
            # Silently fail - telemetry should not break the application
            logger.debug(f"Failed to insert telemetry: {e}")
    
    def start_timer(self) -> float:
        """Start a timer for duration tracking"""
        return time.time()
    
    def calculate_duration_ms(self, start_time: float) -> int:
        """Calculate duration in milliseconds from start time"""
        return int((time.time() - start_time) * 1000)


# Global singleton instance
telemetry_client = TelemetryClient()


# Context manager for timing operations
class TelemetryTimer:
    """Context manager for timing operations"""
    
    def __init__(self, client: TelemetryClient = None):
        self.client = client or telemetry_client
        self.start_time = None
    
    def __enter__(self):
        self.start_time = self.client.start_timer()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @property
    def duration_ms(self) -> int:
        """Get current duration in milliseconds"""
        if self.start_time:
            return self.client.calculate_duration_ms(self.start_time)
        return 0