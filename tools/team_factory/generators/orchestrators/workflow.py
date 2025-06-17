"""
LangGraph workflow orchestrator generator.
"""

from pathlib import Path
from typing import Any, Dict

from ...models import TeamSpecification
from ..base import BaseGenerator


class LangGraphWorkflow(BaseGenerator):
    """Generates LangGraph workflow orchestrator files."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate LangGraph workflow orchestrator.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        team_dir = Path(team_spec.name)
        workflows_dir = team_dir / "workflows"
        workflows_dir.mkdir(exist_ok=True)

        generated_files = []

        # Generate state definitions
        state_file = workflows_dir / "state_definitions.py"
        with open(state_file, "w") as f:
            f.write(self._generate_state_definitions(team_spec))
        generated_files.append(str(state_file))

        # Generate workflow
        workflow_file = workflows_dir / "team_workflow.py"
        with open(workflow_file, "w") as f:
            f.write(self._generate_workflow_content(team_spec))
        generated_files.append(str(workflow_file))

        # Generate __init__.py
        init_file = workflows_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write(self._generate_init_content())
        generated_files.append(str(init_file))

        return {"generated_files": generated_files, "errors": []}

    def _generate_state_definitions(self, team_spec: TeamSpecification) -> str:
        """Generate state definition file."""
        return f'''#!/usr/bin/env python3
"""
State definitions for {team_spec.name}
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TeamState(TypedDict):
    """Shared state for the entire team"""
    messages: Annotated[List[BaseMessage], add_messages]
    team_name: str
    current_objective: Optional[str]
    team_context: Dict[str, Any]
    agent_states: Dict[str, Dict[str, Any]]  # Individual agent states
    workflow_status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class TaskState(TypedDict):
    """State for individual tasks"""
    task_id: str
    description: str
    assigned_to: Optional[str]
    status: str  # pending, in_progress, completed, failed
    priority: str  # high, medium, low
    dependencies: List[str]
    results: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]


class CommunicationState(TypedDict):
    """State for team communications"""
    message_id: str
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    message_type: str  # proposal, challenge, decision, update
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
'''

    def _generate_workflow_content(self, team_spec: TeamSpecification) -> str:
        """Generate workflow orchestrator content."""
        # Agent imports
        agent_imports = []
        agent_inits = []

        for member in team_spec.members:
            class_name = member.role.replace(" ", "") + "Agent"
            var_name = member.role.lower().replace(" ", "_")
            agent_imports.append(f"from agents import {class_name}")
            agent_inits.append(f"        self.{var_name} = {class_name}()")

        # Workflow type based on team size
        workflow_type = "hierarchical" if len(team_spec.members) >= 5 else "sequential"

        return f'''#!/usr/bin/env python3
"""
{team_spec.name} Workflow Orchestrator
LangGraph-based team coordination
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

from workflows.state_definitions import TeamState, TaskState
{chr(10).join(agent_imports)}


class {team_spec.name.replace("-", " ").title().replace(" ", "")}Workflow:
    """
    Orchestrates the {team_spec.name} team using LangGraph

    Workflow Type: {workflow_type.title()}
    Team Size: {len(team_spec.members)}
    """

    def __init__(self, checkpoint_url: Optional[str] = None):
        self.logger = logging.getLogger("{team_spec.name}.workflow")
        self.team_name = "{team_spec.name}"

        # Initialize agents
{chr(10).join(agent_inits)}

        # Initialize checkpointer
        if checkpoint_url:
            self.checkpointer = PostgresSaver.from_conn_string(checkpoint_url)
        else:
            self.checkpointer = MemorySaver()

        # Build the workflow graph
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)

    def _build_graph(self) -> StateGraph:
        """Build the team workflow graph"""
        workflow = StateGraph(TeamState)

        # Add nodes for each phase
        workflow.add_node("initialize", self._initialize_team)
        workflow.add_node("analyze_objective", self._analyze_objective)
        workflow.add_node("plan_approach", self._plan_approach)
        workflow.add_node("execute_tasks", self._execute_tasks)
        workflow.add_node("review_progress", self._review_progress)
        workflow.add_node("finalize_results", self._finalize_results)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges based on workflow type
        if "{workflow_type}" == "hierarchical":
            # Hierarchical flow with delegation
            workflow.add_edge("initialize", "analyze_objective")
            workflow.add_edge("analyze_objective", "plan_approach")
            workflow.add_conditional_edges(
                "plan_approach",
                self._should_delegate,
                {{
                    "delegate": "execute_tasks",
                    "continue": "review_progress"
                }}
            )
            workflow.add_edge("execute_tasks", "review_progress")
            workflow.add_edge("review_progress", "finalize_results")
        else:
            # Sequential flow
            workflow.add_edge("initialize", "analyze_objective")
            workflow.add_edge("analyze_objective", "plan_approach")
            workflow.add_edge("plan_approach", "execute_tasks")
            workflow.add_edge("execute_tasks", "review_progress")
            workflow.add_edge("review_progress", "finalize_results")

        workflow.add_edge("finalize_results", END)

        return workflow

    async def _initialize_team(self, state: TeamState) -> TeamState:
        """Initialize the team state"""
        state["team_name"] = self.team_name
        state["workflow_status"] = "initialized"
        state["created_at"] = datetime.utcnow()
        state["updated_at"] = datetime.utcnow()
        state["agent_states"] = {{}}

        # Add initial system message
        if not state.get("messages"):
            state["messages"] = []

        state["messages"].append(
            SystemMessage(content=f"""
            This is the {team_spec.name} with the following members:
{chr(10).join(f"            - {member.role}: {', '.join(member.responsibilities[:2])}" for member in team_spec.members)}

            Team composition and roles have been initialized.
            """)
        )

        return state

    async def _analyze_objective(self, state: TeamState) -> TeamState:
        """Analyze the team objective"""
        # Manager analyzes the objective
        manager_agent = self.{next(m.role.lower().replace(" ", "_") for m in team_spec.members if m.is_manager)}

        analysis_prompt = HumanMessage(
            content=f"Analyze the following objective and break it down into key components: {{state.get('current_objective', 'No objective set')}}"
        )

        state["messages"].append(analysis_prompt)
        state["workflow_status"] = "analyzing"
        state["updated_at"] = datetime.utcnow()

        return state

    async def _plan_approach(self, state: TeamState) -> TeamState:
        """Plan the approach to achieve the objective"""
        state["workflow_status"] = "planning"
        state["updated_at"] = datetime.utcnow()

        # Planning logic here
        planning_prompt = HumanMessage(
            content="Based on the analysis, create an execution plan with specific tasks and assignments."
        )

        state["messages"].append(planning_prompt)

        return state

    def _should_delegate(self, state: TeamState) -> str:
        """Determine if tasks should be delegated"""
        # In hierarchical mode, always delegate
        # In sequential mode, continue to review
        return "delegate" if "{workflow_type}" == "hierarchical" else "continue"

    async def _execute_tasks(self, state: TeamState) -> TeamState:
        """Execute planned tasks"""
        state["workflow_status"] = "executing"
        state["updated_at"] = datetime.utcnow()

        # Task execution logic
        # Each agent executes their assigned tasks

        return state

    async def _review_progress(self, state: TeamState) -> TeamState:
        """Review progress and results"""
        state["workflow_status"] = "reviewing"
        state["updated_at"] = datetime.utcnow()

        review_prompt = HumanMessage(
            content="Review the execution results and provide a summary of achievements and any gaps."
        )

        state["messages"].append(review_prompt)

        return state

    async def _finalize_results(self, state: TeamState) -> TeamState:
        """Finalize and prepare results"""
        state["workflow_status"] = "completed"
        state["updated_at"] = datetime.utcnow()

        return state

    async def run(self, objective: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the workflow with a specific objective"""
        self.logger.info(f"Starting workflow for objective: {{objective[:100]}}...")

        # Initialize state
        initial_state = {{
            "messages": [],
            "current_objective": objective,
            "team_context": context or {{}},
            "agent_states": {{}},
            "workflow_status": "starting",
            "metadata": {{}}
        }}

        # Run the workflow
        config = {{"configurable": {{"thread_id": f"{{self.team_name}}-{{datetime.utcnow().isoformat()}}"}}}}
        result = await self.compiled_graph.ainvoke(initial_state, config)

        self.logger.info("Workflow completed")
        return result


# Global instance
_workflow_instance = None


def get_workflow(checkpoint_url: Optional[str] = None) -> {team_spec.name.replace("-", " ").title().replace(" ", "")}Workflow:
    """Get or create the team workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = {team_spec.name.replace("-", " ").title().replace(" ", "")}Workflow(checkpoint_url=checkpoint_url)
    return _workflow_instance


if __name__ == "__main__":
    # Example usage
    async def main():
        workflow = get_workflow()

        result = await workflow.run(
            "Develop a comprehensive marketing strategy for Q2 2024",
            context={{
                "budget": 50000,
                "target_market": "B2B SaaS",
                "team_size": {len(team_spec.members)}
            }}
        )

        print("Workflow Result:", result)

    asyncio.run(main())
'''

    def _generate_init_content(self) -> str:
        """Generate __init__.py for workflows directory."""
        return '''"""
Workflow definitions for LangGraph team orchestration.
"""

from .state_definitions import TeamState, TaskState, CommunicationState
from .team_workflow import get_workflow

__all__ = ["TeamState", "TaskState", "CommunicationState", "get_workflow"]
'''
