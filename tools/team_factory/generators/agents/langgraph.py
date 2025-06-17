"""
LangGraph agent generator.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ...models import TeamMember, TeamSpecification
from ..base import BaseGenerator


class LangGraphAgentGenerator(BaseGenerator):
    """Generates LangGraph agent files."""

    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate LangGraph agent files.

        Args:
            team_spec: Team specification

        Returns:
            Generation results
        """
        generated_files = []
        errors = []
        
        # Create agents directory
        team_dir = Path(team_spec.name)
        agents_dir = team_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate __init__.py
        init_path = agents_dir / "__init__.py"
        with open(init_path, "w") as f:
            f.write(self._generate_init_content(team_spec))
        generated_files.append(str(init_path))
        
        # Generate individual agent files
        for member in team_spec.members:
            agent_file = self._generate_agent_file(member, team_spec, agents_dir)
            generated_files.append(str(agent_file))
        
        return {
            "generated_files": generated_files,
            "errors": errors,
        }
    
    def _generate_init_content(self, team_spec: TeamSpecification) -> str:
        """Generate __init__.py content."""
        imports = []
        exports = []
        
        for member in team_spec.members:
            class_name = member.role.replace(" ", "") + "Agent"
            filename = member.filename.replace(".py", "")
            imports.append(f"from .{filename} import {class_name}")
            exports.append(f'"{class_name}"')
        
        return "\n".join(imports) + "\n\n__all__ = [" + ", ".join(exports) + "]\n"
    
    def _generate_agent_file(
        self, member: TeamMember, team_spec: TeamSpecification, agents_dir: Path
    ) -> Path:
        """Generate individual agent file."""
        agent_content = self._generate_agent_content(member, team_spec)
        
        agent_file = agents_dir / member.filename
        with open(agent_file, "w") as f:
            f.write(agent_content)
        
        return agent_file
    
    def _generate_agent_content(self, member: TeamMember, team_spec: TeamSpecification) -> str:
        """Generate agent implementation content."""
        class_name = member.role.replace(" ", "") + "Agent"
        is_manager = member.is_manager
        
        # LLM imports based on provider
        llm_import = self._get_llm_import(team_spec.llm_provider)
        llm_init = self._get_llm_init(team_spec.llm_provider, team_spec.llm_model)
        
        # A2A imports for managers
        a2a_imports = ""
        a2a_methods = ""
        if is_manager:
            a2a_imports = self._get_a2a_imports()
            a2a_methods = self._get_a2a_methods()
        
        # Get the template
        template = self._get_agent_template()
        
        # Build the agent content by replacing placeholders
        content = template
        
        # Replace basic placeholders
        content = content.replace("{member.role}", member.role)
        content = content.replace("{team_spec.name}", team_spec.name)
        content = content.replace("{class_name}", class_name)
        content = content.replace("{llm_import}", llm_import)
        content = content.replace("{a2a_imports}", a2a_imports)
        content = content.replace("{llm_init}", llm_init)
        content = content.replace("{a2a_methods}", a2a_methods)
        content = content.replace("{team_spec.department}", team_spec.department)
        
        # Handle responsibilities
        responsibilities = "\n".join(f"    - {r}" for r in member.responsibilities)
        content = content.replace("{chr(10).join(f\"    - {r}\" for r in member.responsibilities)}", responsibilities)
        
        # Handle skills
        skills = ", ".join(member.skills)
        content = content.replace("{', '.join(member.skills)}", skills)
        
        # Handle manages teams
        manages_teams_str = str(member.manages_teams)
        content = content.replace("{member.manages_teams}", manages_teams_str)
        
        # Handle manages teams list
        manages_teams_list = ", ".join(member.manages_teams) if member.manages_teams else ""
        
        # Handle system prompt
        if member.system_prompt:
            content = content.replace("{member.system_prompt}", member.system_prompt)
        else:
            system_prompt = self._generate_system_prompt(member, team_spec)
            content = content.replace("{member.system_prompt}", system_prompt)
        
        # Handle conditional sections for managers
        if is_manager:
            # Remove the conditional markers
            content = content.replace("{{% if is_manager %}}", "")
            content = content.replace("{{% endif %}}", "")
            content = content.replace("{{% else %}}", "REMOVE_ELSE_BLOCK")
            
            # Remove else blocks
            while "REMOVE_ELSE_BLOCK" in content:
                start = content.find("REMOVE_ELSE_BLOCK")
                end = content.find("{{% endif %}}", start)
                if end != -1:
                    content = content[:start] + content[end:]
                else:
                    content = content.replace("REMOVE_ELSE_BLOCK", "")
        else:
            # Remove manager-only sections
            while "{{% if is_manager %}}" in content:
                start = content.find("{{% if is_manager %}}")
                # Find matching endif
                end = content.find("{{% endif %}}", start)
                if end != -1:
                    # Check for else block
                    else_pos = content.find("{{% else %}}", start)
                    if else_pos != -1 and else_pos < end:
                        # Keep else block content
                        content = content[:start] + content[else_pos+12:end] + content[end+13:]
                    else:
                        # Remove entire if block
                        content = content[:start] + content[end+13:]
                else:
                    break
        
        # Handle optional manages teams section
        if member.manages_teams:
            manages_teams_section = f'\n    Manages Teams: {manages_teams_list}'
            content = content.replace(' + (f"""\n    Manages Teams: {\', \'.join(member.manages_teams)}""" if member.manages_teams else "") + f"""', manages_teams_section + '\n')
        else:
            content = content.replace(' + (f"""\n    Manages Teams: {\', \'.join(member.manages_teams)}""" if member.manages_teams else "") + f"""', '\n')
        
        return content
    
    def _get_llm_import(self, provider: str) -> str:
        """Get LLM import statement."""
        if provider == "OpenAI":
            return "\nfrom langchain_openai import ChatOpenAI"
        elif provider == "Anthropic":
            return "\nfrom langchain_anthropic import ChatAnthropic"
        return ""
    
    def _get_llm_init(self, provider: str, model: str) -> str:
        """Get LLM initialization code."""
        if provider == "OpenAI":
            return f'ChatOpenAI(model="{model}", temperature=0.7)'
        elif provider == "Anthropic":
            return f'ChatAnthropic(model="{model}", temperature=0.7)'
        return 'None  # Configure LLM'
    
    def _get_a2a_imports(self) -> str:
        """Get A2A imports for managers."""
        return """
from agents.distributed.a2a.client import A2AClientManager
from agents.distributed.a2a.messages import TaskRequest, TaskResponse
from datetime import datetime
import json"""
    
    def _get_a2a_methods(self) -> str:
        """Get A2A methods for managers."""
        return """
    def _init_a2a_client(self):
        \"\"\"Initialize A2A client for inter-team communication\"\"\"
        try:
            self.a2a_client = A2AClientManager(
                agent_id=self.agent_id,
                agent_name=self.name,
                capabilities=[
                    f"Manage {team}" for team in self.manages_teams
                ] + [
                    "Delegate tasks",
                    "Monitor progress",
                    "Provide updates"
                ]
            )
            self.logger.info(f"A2A client initialized for {self.role}")
        except Exception as e:
            self.logger.error(f"Failed to initialize A2A client: {e}")
            self.a2a_client = None

    async def delegate_task(self, team: str, task_description: str, 
                          success_criteria: List[str], deadline: Optional[str] = None) -> str:
        \"\"\"Delegate a task to a subordinate team\"\"\"
        if not self.a2a_client:
            self.logger.error("A2A client not initialized")
            return "Failed to delegate: A2A client not available"
        
        request = TaskRequest(
            from_agent=self.agent_id,
            to_agent=f"{team}-manager",
            task_type="delegation",
            task_description=task_description,
            context={
                "success_criteria": success_criteria,
                "deadline": deadline,
                "requesting_team": self.team_name,
                "priority": "normal"
            },
            timeout=3600  # 1 hour default
        )
        
        response = await self.a2a_client.send_task_request(request)
        return response.result if response else "Failed to delegate task"

    async def check_team_status(self, team: str) -> Dict[str, Any]:
        \"\"\"Check status of a subordinate team\"\"\"
        if not self.a2a_client:
            return {"error": "A2A client not initialized"}
        
        request = TaskRequest(
            from_agent=self.agent_id,
            to_agent=f"{team}-manager",
            task_type="status_check",
            task_description="Provide current team status and progress",
            context={"requesting_agent": self.role},
            timeout=300  # 5 minutes
        )
        
        response = await self.a2a_client.send_task_request(request)
        return response.context if response else {"error": "No response from team"}"""
    
    def _build_template(self, member: TeamMember, team_spec: TeamSpecification, is_manager: bool) -> str:
        """Build the agent template with conditional logic already resolved."""
        # This method is no longer used but kept for compatibility
        return self._generate_agent_content(member, team_spec)
    
    def _get_agent_template(self) -> str:
        """Get the complete agent template."""
        return '''#!/usr/bin/env python3
"""
{member.role} Agent for {team_spec.name}
Generated by Team Factory

LangGraph-based agent implementation with state management and workflow orchestration.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, TypedDict, Annotated
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from tools.conversation_logging_system import ConversationLogger, MessageType
from elf_automations.shared.memory import TeamMemory, LearningSystem, MemoryAgentMixin, with_memory
{llm_import}{a2a_imports}

from agents.langgraph_base import LangGraphBaseAgent, LangGraphAgentState


class {class_name}State(TypedDict):
    """State specific to {member.role}"""
    messages: Annotated[List[BaseMessage], add_messages]
    agent_id: str
    current_task: Optional[str]
    task_context: Dict[str, Any]
    available_tools: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    error_count: int
    last_activity: datetime
    metadata: Dict[str, Any]
    # Agent-specific state
    manages_teams: List[str]
    pending_a2a_requests: Dict[str, Any]


class {class_name}(LangGraphBaseAgent, MemoryAgentMixin):
    """
    {member.role} implementation using LangGraph

    Responsibilities:
{chr(10).join(f"    - {r}" for r in member.responsibilities)}

    Skills: {', '.join(member.skills)}
    """ + (f"""
    Manages Teams: {', '.join(member.manages_teams)}""" if member.manages_teams else "") + f"""
    """

    def __init__(self,
                 agent_id: Optional[str] = None,
                 gateway_url: str = "http://agentgateway-service:3000",
                 gateway_api_key: Optional[str] = None):

        # Generate unique agent ID if not provided
        if not agent_id:
            agent_id = f"{team_spec.name}-{member.role.lower().replace(' ', '-')}-{{uuid4().hex[:8]}}"

        super().__init__(
            agent_id=agent_id,
            name="{member.role}",
            department="{team_spec.department}",
            system_prompt="""{member.system_prompt}""",
            gateway_url=gateway_url,
            gateway_api_key=gateway_api_key
        )

        self.logger = logging.getLogger(f"{team_spec.name}.{member.role}")
        self.role = "{member.role}"
        self.manages_teams = {member.manages_teams}
        self.pending_a2a_requests = {{}}

        # Initialize conversation logger
        self.conversation_logger = ConversationLogger("{team_spec.name}")
        self.team_name = "{team_spec.name}"

        # Initialize custom LLM
        self.llm = {llm_init}

        # Initialize memory system
        self.init_memory("{team_spec.name}")
        self.logger.info("Memory system initialized for {member.role}")

        # Initialize A2A client if this is a manager
        if self.manages_teams:
            self._init_a2a_client()

        # Override base graph with custom workflow
        self._initialize_custom_workflow()

    def _initialize_custom_workflow(self):
        """Initialize the custom workflow for this agent"""
        # Create the state graph
        workflow = StateGraph({class_name}State)

        # Add nodes specific to this agent's responsibilities
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("analyze_task", self._analyze_task_node)
        workflow.add_node("plan_execution", self._plan_execution_node)
        {{% if is_manager %}}
        workflow.add_node("delegate_tasks", self._delegate_tasks_node)
        {{% endif %}}
        workflow.add_node("execute_task", self._execute_task_node)
        workflow.add_node("review_results", self._review_results_node)
        workflow.add_node("finalize", self._finalize_node)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges
        workflow.add_edge("initialize", "analyze_task")
        workflow.add_edge("analyze_task", "plan_execution")
        {{% if is_manager %}}
        workflow.add_conditional_edges(
            "plan_execution",
            self._should_delegate,
            {{
                "delegate": "delegate_tasks",
                "execute": "execute_task"
            }}
        )
        workflow.add_edge("delegate_tasks", "review_results")
        {{% else %}}
        workflow.add_edge("plan_execution", "execute_task")
        {{% endif %}}
        workflow.add_edge("execute_task", "review_results")
        workflow.add_edge("review_results", "finalize")
        workflow.add_edge("finalize", END)

        # Compile the graph
        self.graph = workflow
        self.compiled_graph = workflow.compile(checkpointer=self.checkpointer)

        self.logger.info("Custom workflow initialized for {member.role}")

    async def _initialize_node(self, state: {class_name}State) -> {class_name}State:
        """Initialize the agent state"""
        state["agent_id"] = self.agent_id
        state["manages_teams"] = self.manages_teams
        state["pending_a2a_requests"] = {{}}
        state["last_activity"] = datetime.utcnow()
        return state

    async def _analyze_task_node(self, state: {class_name}State) -> {class_name}State:
        """Analyze the incoming task and determine approach"""
        messages = state.get("messages", [])

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=self.system_prompt))

        # Check for relevant past experiences
        task_description = state.get('current_task', 'No specific task')

        # Get relevant learnings from memory
        relevant_learnings = []
        if hasattr(self, 'team_memory') and self.team_memory:
            learnings = self.team_memory.get_relevant_learnings({
                'task_type': self.learning_system._categorize_task(task_description),
                'agent': self.role
            })
            if learnings:
                relevant_learnings = learnings[:3]  # Top 3 most relevant

        # Create analysis prompt with memory context
        memory_context = ""
        if relevant_learnings:
            memory_context = "\n\nBased on past experiences:\n"
            for learning in relevant_learnings:
                memory_context += f"- {{learning.get('title', learning.get('insight', ''))}}\n"

        analysis_prompt = HumanMessage(content=f"""
        Analyze this task and determine the best approach:

        Task: {{state.get('current_task', 'No specific task')}}
        Context: {{state.get('task_context', {{}})}}
        {memory_context}

        Consider:
        1. What are the key objectives?
        2. What resources or information do we need?
        3. What are the success criteria?
        {{% if is_manager %}}
        4. Should this be delegated to subordinate teams?
        {{% endif %}}
        """)

        messages.append(analysis_prompt)

        # Get LLM analysis
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        state["messages"] = messages
        state["last_activity"] = datetime.utcnow()

        return state

    async def _plan_execution_node(self, state: {class_name}State) -> {class_name}State:
        """Plan the execution strategy"""
        messages = state["messages"]

        planning_prompt = HumanMessage(content="""
        Based on your analysis, create a detailed execution plan.
        Include specific steps, dependencies, and expected outcomes.
        """)

        messages.append(planning_prompt)
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        state["messages"] = messages
        return state
    
    {{% if is_manager %}}
    def _should_delegate(self, state: {class_name}State) -> str:
        """Determine if task should be delegated to subordinate teams"""
        # Parse the last message to check if delegation is recommended
        messages = state["messages"]
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                content = last_message.content.lower()
                if any(team in content for team in self.manages_teams):
                    return "delegate"
        return "execute"

    async def _delegate_tasks_node(self, state: {class_name}State) -> {class_name}State:
        """Delegate tasks to subordinate teams via A2A"""
        messages = state["messages"]

        delegation_prompt = HumanMessage(content=f"""
        You manage these teams: {{', '.join(self.manages_teams)}}

        For any tasks that should be delegated, specify:
        1. Which team should handle it
        2. Clear task description
        3. Success criteria (list of measurable outcomes)
        4. Deadline (if applicable)
        5. Any relevant context

        Format your response as structured delegation requests.
        """)

        messages.append(delegation_prompt)
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        # In a real implementation, parse the response and send A2A requests
        # This is a placeholder for the actual delegation logic

        state["messages"] = messages
        return state
{a2a_methods}
    {{% endif %}}

    async def _execute_task_node(self, state: {class_name}State) -> {class_name}State:
        """Execute the task directly"""
        messages = state["messages"]

        # Start memory episode
        task_description = state.get('current_task', 'Unknown task')
        self.start_episode(task_description, state.get('task_context', {{}}))

        # Record planning action
        self.record_action("Started task execution", {{
            'task': task_description,
            'context': state.get('task_context', {{}})
        }})

        execution_prompt = HumanMessage(content="""
        Execute the planned approach. Use available tools as needed.
        Provide detailed results and any issues encountered.
        """)

        messages.append(execution_prompt)
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        # Record execution action
        self.record_action("Executed task", {{
            'response': response.content[:500]  # First 500 chars
        }})

        state["messages"] = messages
        return state

    async def _review_results_node(self, state: {class_name}State) -> {class_name}State:
        """Review and validate results"""
        messages = state["messages"]

        review_prompt = HumanMessage(content="""
        Review the execution results:
        1. Were the objectives met?
        2. Are there any issues or gaps?
        3. What are the key outcomes?
        4. Any recommendations for next steps?
        """)

        messages.append(review_prompt)
        response = await self.llm.ainvoke(messages)
        messages.append(response)

        state["messages"] = messages
        return state

    async def _finalize_node(self, state: {class_name}State) -> {class_name}State:
        """Finalize the task and prepare response"""
        state["last_activity"] = datetime.utcnow()

        # Log task completion
        self.logger.info(f"Task completed by {member.role}")

        # Complete memory episode
        if self.current_episode:
            # Determine success based on review results
            messages = state.get("messages", [])
            success = True  # Default to success
            result_summary = None

            # Look for success indicators in the last few messages
            for msg in messages[-3:]:
                if isinstance(msg, AIMessage):
                    content = msg.content.lower()
                    if 'failed' in content or 'error' in content or 'issue' in content:
                        success = False
                    if 'completed' in content or 'success' in content:
                        result_summary = msg.content[:500]

            # Complete the episode
            self.complete_episode(
                success=success,
                result={{
                    'final_state': state.get('workflow_status', 'completed'),
                    'summary': result_summary
                }}
            )

            # Get performance insights periodically
            if hasattr(self, '_task_count'):
                self._task_count += 1
            else:
                self._task_count = 1

            if self._task_count % 10 == 0:  # Every 10 tasks
                insights = self.get_performance_insights()
                if insights.get('recommendations'):
                    self.logger.info(f"Performance insights: {{insights['recommendations'][0]}}")

        return state

    async def _startup_tasks(self) -> None:
        """Agent-specific startup tasks"""
        self.logger.info(f"Starting {member.role} agent")
        # Add any specific startup logic here

    async def _shutdown_tasks(self) -> None:
        """Agent-specific shutdown tasks"""
        self.logger.info(f"Shutting down {member.role} agent")
        # Add any specific shutdown logic here

    async def _cleanup_resources(self) -> None:
        """Agent-specific resource cleanup"""
        self.logger.info(f"Cleaning up resources for {member.role} agent")
        # Add any specific cleanup logic here

    def log_communication(self, message: str, to_agent: Optional[str] = None):
        """Log internal team communications naturally"""
        if to_agent:
            self.logger.info(f"[{member.role} → {{to_agent}}]: {{message}}")
        else:
            self.logger.info(f"[{member.role}]: {{message}}")

    def log_proposal(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a proposal message with rich context"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.PROPOSAL,
            to_agent=to_agent,
            metadata=metadata
        )
        self.log_communication(f"[PROPOSAL] {{message}}", to_agent)

    def log_challenge(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a challenge/skeptical message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.CHALLENGE,
            to_agent=to_agent,
            metadata=metadata
        )
        self.log_communication(f"[CHALLENGE] {{message}}", to_agent)

    def log_decision(self, message: str, **metadata):
        """Log a decision message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.DECISION,
            metadata=metadata
        )
        self.log_communication(f"[DECISION] {{message}}")

    def log_update(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a general update message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.UPDATE,
            to_agent=to_agent,
            metadata=metadata
        )
        self.log_communication(message, to_agent)

    async def process_message_with_logging(self, state: Dict, message: BaseMessage) -> Dict:
        """Process a message and log the conversation"""

        # Extract sender info from message metadata
        sender = message.additional_kwargs.get('sender', self.name)
        message_type = message.additional_kwargs.get('type', MessageType.UPDATE)

        # Log the message
        self.conversation_logger.log_message(
            agent_name=sender,
            message=message.content,
            message_type=message_type,
            metadata={{
                'state_id': state.get('agent_id'),
                'task': state.get('current_task')
            }}
        )

        return state
'''
    
    def _generate_system_prompt(self, member: TeamMember, team_spec: TeamSpecification) -> str:
        """Generate system prompt for the agent."""
        prompt = f"You are the {member.role} for {team_spec.name}. "
        prompt += f"Your responsibilities include: {', '.join(member.responsibilities)}. "
        
        if member.personality:
            prompt += f"You have a {member.personality} personality. "
        
        if member.is_manager:
            prompt += "As a manager, you coordinate team efforts and make key decisions. "
        
        return prompt
