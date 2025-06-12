"""
Agent lifecycle management for distributed agents.
Handles startup, shutdown, and graceful termination.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from enum import Enum
from typing import Callable, List, Optional


class LifecycleState(Enum):
    """Agent lifecycle states."""

    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class AgentLifecycleMixin:
    """
    Mixin class providing lifecycle management for distributed agents.
    Handles graceful startup, shutdown, and signal handling.
    """

    def __init__(self):
        """Initialize lifecycle management."""
        self.lifecycle_state = LifecycleState.INITIALIZING
        self.lifecycle_callbacks: Dict[LifecycleState, List[Callable]] = {
            state: [] for state in LifecycleState
        }

        # Shutdown handling
        self.shutdown_timeout = 30  # seconds
        self.shutdown_event = asyncio.Event()
        self.graceful_shutdown = True

        # Signal handlers
        self._setup_signal_handlers()

        self.logger = logging.getLogger(f"{self.__class__.__name__}.lifecycle")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            # Handle SIGTERM (Kubernetes sends this for pod termination)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Handle SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, self._signal_handler)

            self.logger.debug("Signal handlers configured")
        except Exception as e:
            self.logger.warning(f"Could not setup signal handlers: {e}")

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name}, initiating graceful shutdown")

        # Set shutdown event
        if not self.shutdown_event.is_set():
            self.shutdown_event.set()

            # Schedule shutdown coroutine
            asyncio.create_task(self._graceful_shutdown())

    async def start_lifecycle(self) -> None:
        """Start the agent lifecycle."""
        try:
            self.logger.info("Starting agent lifecycle")
            self._set_lifecycle_state(LifecycleState.STARTING)

            # Execute startup callbacks
            await self._execute_callbacks(LifecycleState.STARTING)

            self._set_lifecycle_state(LifecycleState.RUNNING)
            await self._execute_callbacks(LifecycleState.RUNNING)

            self.logger.info("Agent lifecycle started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start lifecycle: {e}")
            self._set_lifecycle_state(LifecycleState.ERROR)
            raise

    async def stop_lifecycle(self) -> None:
        """Stop the agent lifecycle."""
        try:
            self.logger.info("Stopping agent lifecycle")
            self._set_lifecycle_state(LifecycleState.STOPPING)

            # Execute stopping callbacks
            await self._execute_callbacks(LifecycleState.STOPPING)

            self._set_lifecycle_state(LifecycleState.STOPPED)
            await self._execute_callbacks(LifecycleState.STOPPED)

            self.logger.info("Agent lifecycle stopped successfully")

        except Exception as e:
            self.logger.error(f"Failed to stop lifecycle: {e}")
            self._set_lifecycle_state(LifecycleState.ERROR)
            raise

    async def _graceful_shutdown(self) -> None:
        """Perform graceful shutdown."""
        try:
            self.logger.info("Starting graceful shutdown")

            # Wait for shutdown timeout or manual stop
            try:
                await asyncio.wait_for(
                    self._wait_for_shutdown_complete(), timeout=self.shutdown_timeout
                )
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Graceful shutdown timeout ({self.shutdown_timeout}s), forcing exit"
                )
                self.graceful_shutdown = False

            # Stop the agent
            if hasattr(self, "stop"):
                await self.stop()

            self.logger.info("Graceful shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")
        finally:
            # Exit the process
            sys.exit(0)

    async def _wait_for_shutdown_complete(self) -> None:
        """Wait for shutdown to complete."""
        # This can be overridden by subclasses to implement custom shutdown logic
        await asyncio.sleep(1)  # Basic implementation

    def _set_lifecycle_state(self, state: LifecycleState) -> None:
        """Set the lifecycle state and log the transition."""
        old_state = getattr(self, "lifecycle_state", None)
        self.lifecycle_state = state

        if old_state != state:
            self.logger.info(f"Lifecycle state changed: {old_state} -> {state}")

    async def _execute_callbacks(self, state: LifecycleState) -> None:
        """Execute callbacks for a specific lifecycle state."""
        callbacks = self.lifecycle_callbacks.get(state, [])

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                self.logger.error(f"Lifecycle callback failed for state {state}: {e}")

    def add_lifecycle_callback(self, state: LifecycleState, callback: Callable) -> None:
        """Add a callback for a specific lifecycle state."""
        if state not in self.lifecycle_callbacks:
            self.lifecycle_callbacks[state] = []

        self.lifecycle_callbacks[state].append(callback)
        self.logger.debug(f"Added lifecycle callback for state: {state}")

    def remove_lifecycle_callback(
        self, state: LifecycleState, callback: Callable
    ) -> None:
        """Remove a callback for a specific lifecycle state."""
        if state in self.lifecycle_callbacks:
            try:
                self.lifecycle_callbacks[state].remove(callback)
                self.logger.debug(f"Removed lifecycle callback for state: {state}")
            except ValueError:
                self.logger.warning(f"Callback not found for state: {state}")

    def get_lifecycle_info(self) -> dict:
        """Get current lifecycle information."""
        return {
            "state": self.lifecycle_state.value,
            "shutdown_requested": self.shutdown_event.is_set(),
            "graceful_shutdown": self.graceful_shutdown,
            "shutdown_timeout": self.shutdown_timeout,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def is_running(self) -> bool:
        """Check if agent is in running state."""
        return self.lifecycle_state == LifecycleState.RUNNING

    def is_stopping(self) -> bool:
        """Check if agent is stopping."""
        return self.lifecycle_state == LifecycleState.STOPPING

    def is_stopped(self) -> bool:
        """Check if agent is stopped."""
        return self.lifecycle_state == LifecycleState.STOPPED

    def request_shutdown(self) -> None:
        """Request graceful shutdown."""
        if not self.shutdown_event.is_set():
            self.logger.info("Shutdown requested")
            self.shutdown_event.set()
            asyncio.create_task(self._graceful_shutdown())
