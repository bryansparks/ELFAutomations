"""
Core state machine implementation for resource lifecycle management
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class StateDefinition:
    """Definition of a single state"""

    name: str
    description: str
    is_terminal: bool = False
    is_error: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StateTransition:
    """Definition of a state transition"""

    from_state: str
    to_state: str
    name: str
    description: str
    validator: Optional[Callable] = None
    on_transition: Optional[Callable] = None
    required_metadata: List[str] = None

    def __post_init__(self):
        if self.required_metadata is None:
            self.required_metadata = []


class StateMachine:
    """
    Generic state machine for managing resource lifecycles
    """

    def __init__(self, name: str, initial_state: str):
        self.name = name
        self.states: Dict[str, StateDefinition] = {}
        self.transitions: Dict[str, List[StateTransition]] = {}
        self.initial_state = initial_state
        self._current_state = initial_state
        self._state_history: List[tuple] = []

    def add_state(self, state: StateDefinition):
        """Add a state to the machine"""
        self.states[state.name] = state
        if state.name not in self.transitions:
            self.transitions[state.name] = []

    def add_transition(self, transition: StateTransition):
        """Add a transition between states"""
        if transition.from_state not in self.states:
            raise ValueError(f"From state '{transition.from_state}' not defined")
        if transition.to_state not in self.states:
            raise ValueError(f"To state '{transition.to_state}' not defined")

        if transition.from_state not in self.transitions:
            self.transitions[transition.from_state] = []
        self.transitions[transition.from_state].append(transition)

    @property
    def current_state(self) -> str:
        """Get current state name"""
        return self._current_state

    @property
    def current_state_def(self) -> StateDefinition:
        """Get current state definition"""
        return self.states[self._current_state]

    def can_transition_to(self, to_state: str) -> bool:
        """Check if transition to given state is allowed"""
        if self._current_state not in self.transitions:
            return False

        return any(
            t.to_state == to_state for t in self.transitions[self._current_state]
        )

    def get_available_transitions(self) -> List[StateTransition]:
        """Get all available transitions from current state"""
        return self.transitions.get(self._current_state, [])

    def validate_transition(
        self, to_state: str, metadata: Dict[str, Any] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if transition is allowed and metadata is correct
        Returns: (is_valid, error_message)
        """
        if not self.can_transition_to(to_state):
            return (
                False,
                f"Transition from '{self._current_state}' to '{to_state}' not allowed",
            )

        # Find the transition
        transition = next(
            (
                t
                for t in self.transitions[self._current_state]
                if t.to_state == to_state
            ),
            None,
        )

        if not transition:
            return False, "Transition not found"

        # Check required metadata
        if metadata is None:
            metadata = {}

        for required in transition.required_metadata:
            if required not in metadata:
                return False, f"Required metadata '{required}' not provided"

        # Run custom validator if provided
        if transition.validator:
            try:
                result = transition.validator(self._current_state, to_state, metadata)
                if result is not True:
                    return False, str(result) if result else "Validation failed"
            except Exception as e:
                return False, f"Validator error: {str(e)}"

        return True, None

    def transition_to(
        self,
        to_state: str,
        metadata: Dict[str, Any] = None,
        transitioned_by: str = "system",
    ) -> tuple[bool, Optional[str]]:
        """
        Execute transition to new state
        Returns: (success, error_message)
        """
        # Validate transition
        is_valid, error = self.validate_transition(to_state, metadata)
        if not is_valid:
            logger.error(f"State transition failed: {error}")
            return False, error

        # Find the transition
        transition = next(
            (
                t
                for t in self.transitions[self._current_state]
                if t.to_state == to_state
            ),
            None,
        )

        # Record history
        self._state_history.append(
            {
                "from_state": self._current_state,
                "to_state": to_state,
                "timestamp": datetime.utcnow(),
                "transitioned_by": transitioned_by,
                "metadata": metadata,
            }
        )

        # Execute transition callback if provided
        if transition.on_transition:
            try:
                transition.on_transition(self._current_state, to_state, metadata)
            except Exception as e:
                logger.error(f"Transition callback error: {str(e)}")
                # Continue with transition even if callback fails

        # Update state
        old_state = self._current_state
        self._current_state = to_state

        logger.info(f"State transitioned from '{old_state}' to '{to_state}'")
        return True, None

    def get_state_history(self) -> List[dict]:
        """Get state transition history"""
        return self._state_history.copy()

    def reset(self):
        """Reset to initial state"""
        self._current_state = self.initial_state
        self._state_history = []

    def to_dict(self) -> Dict[str, Any]:
        """Export state machine configuration"""
        return {
            "name": self.name,
            "initial_state": self.initial_state,
            "current_state": self._current_state,
            "states": {
                name: {
                    "description": state.description,
                    "is_terminal": state.is_terminal,
                    "is_error": state.is_error,
                    "metadata": state.metadata,
                }
                for name, state in self.states.items()
            },
            "transitions": {
                from_state: [
                    {
                        "to_state": t.to_state,
                        "name": t.name,
                        "description": t.description,
                        "required_metadata": t.required_metadata,
                    }
                    for t in transitions
                ]
                for from_state, transitions in self.transitions.items()
            },
        }


def create_workflow_state_machine() -> StateMachine:
    """Create state machine for N8N workflows"""
    sm = StateMachine("workflow_lifecycle", "created")

    # Define states
    states = [
        StateDefinition("created", "Workflow created but not registered"),
        StateDefinition("registered", "Workflow registered in system"),
        StateDefinition("validating", "Workflow being validated"),
        StateDefinition("validated", "Workflow passed validation"),
        StateDefinition(
            "failed_validation", "Workflow failed validation", is_error=True
        ),
        StateDefinition("deploying", "Workflow being deployed to N8N"),
        StateDefinition("deployed", "Workflow deployed but not active"),
        StateDefinition("active", "Workflow active and callable"),
        StateDefinition("inactive", "Workflow deployed but disabled"),
        StateDefinition("archived", "Workflow archived", is_terminal=True),
        StateDefinition("error", "Workflow in error state", is_error=True),
    ]

    for state in states:
        sm.add_state(state)

    # Define transitions
    transitions = [
        StateTransition(
            "created", "registered", "register", "Register workflow in system"
        ),
        StateTransition(
            "registered", "validating", "start_validation", "Begin validation process"
        ),
        StateTransition(
            "validating", "validated", "validation_passed", "Validation successful"
        ),
        StateTransition(
            "validating", "failed_validation", "validation_failed", "Validation failed"
        ),
        StateTransition(
            "failed_validation", "validating", "retry_validation", "Retry validation"
        ),
        StateTransition(
            "validated", "deploying", "start_deployment", "Begin deployment"
        ),
        StateTransition(
            "deploying", "deployed", "deployment_complete", "Deployment successful"
        ),
        StateTransition("deploying", "error", "deployment_failed", "Deployment failed"),
        StateTransition("deployed", "active", "activate", "Activate workflow"),
        StateTransition("active", "inactive", "deactivate", "Deactivate workflow"),
        StateTransition("inactive", "active", "reactivate", "Reactivate workflow"),
        StateTransition("active", "archived", "archive", "Archive workflow"),
        StateTransition("inactive", "archived", "archive", "Archive workflow"),
        StateTransition("error", "registered", "reset", "Reset to registered state"),
    ]

    for transition in transitions:
        sm.add_transition(transition)

    return sm


def create_mcp_state_machine() -> StateMachine:
    """Create state machine for MCP servers/clients"""
    sm = StateMachine("mcp_lifecycle", "created")

    # Define states
    states = [
        StateDefinition("created", "MCP created but not registered"),
        StateDefinition("registered", "MCP registered with AgentGateway"),
        StateDefinition("building", "Docker image being built"),
        StateDefinition("built", "Docker image ready"),
        StateDefinition("deploying", "Being deployed to K8s"),
        StateDefinition("deployed", "Running in K8s"),
        StateDefinition("health_checking", "Running health checks"),
        StateDefinition("available", "Available for connections"),
        StateDefinition("active", "Active and serving requests"),
        StateDefinition("inactive", "Deployed but not serving"),
        StateDefinition("failed", "Deployment or health check failed", is_error=True),
        StateDefinition("archived", "Archived", is_terminal=True),
    ]

    for state in states:
        sm.add_state(state)

    # Define transitions
    transitions = [
        StateTransition(
            "created", "registered", "register", "Register with AgentGateway"
        ),
        StateTransition("registered", "building", "start_build", "Start Docker build"),
        StateTransition("building", "built", "build_complete", "Build successful"),
        StateTransition("building", "failed", "build_failed", "Build failed"),
        StateTransition(
            "built", "deploying", "start_deployment", "Begin K8s deployment"
        ),
        StateTransition(
            "deploying", "deployed", "deployment_complete", "Deployment successful"
        ),
        StateTransition(
            "deploying", "failed", "deployment_failed", "Deployment failed"
        ),
        StateTransition(
            "deployed", "health_checking", "start_health_check", "Begin health checks"
        ),
        StateTransition(
            "health_checking", "available", "health_check_passed", "Health check passed"
        ),
        StateTransition(
            "health_checking", "failed", "health_check_failed", "Health check failed"
        ),
        StateTransition("available", "active", "activate", "Activate MCP"),
        StateTransition("active", "inactive", "deactivate", "Deactivate MCP"),
        StateTransition("inactive", "active", "reactivate", "Reactivate MCP"),
        StateTransition("failed", "registered", "reset", "Reset to registered"),
        StateTransition("active", "archived", "archive", "Archive MCP"),
        StateTransition("inactive", "archived", "archive", "Archive MCP"),
    ]

    for transition in transitions:
        sm.add_transition(transition)

    return sm


def create_team_state_machine() -> StateMachine:
    """Create state machine for Teams"""
    sm = StateMachine("team_lifecycle", "created")

    # Define states
    states = [
        StateDefinition("created", "Team created via factory"),
        StateDefinition("registered", "Team registered in registry"),
        StateDefinition("building", "Building team container"),
        StateDefinition("built", "Container image ready"),
        StateDefinition("deploying", "Deploying to K8s"),
        StateDefinition("deployed", "Running in K8s"),
        StateDefinition("awaiting_dependencies", "Waiting for dependencies"),
        StateDefinition("active", "Active and operational"),
        StateDefinition("scaling", "Scaling operations in progress"),
        StateDefinition("inactive", "Deployed but not active"),
        StateDefinition("failed", "Deployment failed", is_error=True),
        StateDefinition("archived", "Archived", is_terminal=True),
    ]

    for state in states:
        sm.add_state(state)

    # Define transitions
    transitions = [
        StateTransition(
            "created", "registered", "register", "Register in team registry"
        ),
        StateTransition(
            "registered", "building", "start_build", "Start container build"
        ),
        StateTransition("building", "built", "build_complete", "Build successful"),
        StateTransition("building", "failed", "build_failed", "Build failed"),
        StateTransition("built", "deploying", "start_deployment", "Begin deployment"),
        StateTransition(
            "deploying", "deployed", "deployment_complete", "Deployment successful"
        ),
        StateTransition(
            "deploying", "failed", "deployment_failed", "Deployment failed"
        ),
        StateTransition(
            "deployed",
            "awaiting_dependencies",
            "check_dependencies",
            "Dependencies not ready",
        ),
        StateTransition("deployed", "active", "activate", "Activate team"),
        StateTransition(
            "awaiting_dependencies",
            "active",
            "dependencies_satisfied",
            "All dependencies ready",
        ),
        StateTransition(
            "active", "scaling", "start_scaling", "Begin scaling operation"
        ),
        StateTransition("scaling", "active", "scaling_complete", "Scaling complete"),
        StateTransition("active", "inactive", "deactivate", "Deactivate team"),
        StateTransition("inactive", "active", "reactivate", "Reactivate team"),
        StateTransition("failed", "registered", "reset", "Reset to registered"),
        StateTransition("active", "archived", "archive", "Archive team"),
        StateTransition("inactive", "archived", "archive", "Archive team"),
    ]

    for transition in transitions:
        sm.add_transition(transition)

    return sm
