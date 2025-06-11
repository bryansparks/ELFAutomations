#!/usr/bin/env python3
"""
Agent Code Enhancement System
Uses LLM to generate sophisticated, capability-rich agent implementations
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openai
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


@dataclass
class AgentCapability:
    """Represents a specific capability an agent should have"""

    name: str
    description: str
    required_imports: List[str]
    code_snippet: str
    integration_point: str  # where in the agent class this goes


class AgentCodeEnhancer:
    """
    Enhances agent code generation using LLM analysis and patterns
    """

    def __init__(self):
        self.console = console

        # Repository of proven agent patterns
        self.capability_patterns = self._load_capability_patterns()

        # Best practices for agent implementation
        self.best_practices = {
            "error_handling": "Robust error handling with graceful degradation",
            "async_operations": "Async/await for non-blocking operations",
            "state_management": "Clean state tracking and recovery",
            "tool_integration": "Efficient tool usage patterns",
            "memory_optimization": "Smart memory/context management",
            "collaboration": "Effective inter-agent communication",
            "observability": "Comprehensive logging and metrics",
        }

    def _load_capability_patterns(self) -> Dict[str, AgentCapability]:
        """Load proven patterns for agent capabilities"""

        patterns = {
            "smart_memory": AgentCapability(
                name="Smart Memory Management",
                description="Intelligently manages conversation context and memory",
                required_imports=[
                    "from collections import deque",
                    "from typing import Deque",
                    "import tiktoken",
                ],
                code_snippet='''
    def _init_smart_memory(self, max_tokens: int = 4000):
        """Initialize smart memory management"""
        self.memory_buffer: Deque[Dict[str, Any]] = deque(maxlen=50)
        self.token_counter = tiktoken.encoding_for_model("gpt-4")
        self.max_memory_tokens = max_tokens

    def _add_to_memory(self, content: Dict[str, Any]):
        """Add to memory with token management"""
        self.memory_buffer.append(content)
        self._trim_memory_by_tokens()

    def _trim_memory_by_tokens(self):
        """Keep memory within token limits"""
        while self._count_memory_tokens() > self.max_memory_tokens and len(self.memory_buffer) > 1:
            self.memory_buffer.popleft()

    def _count_memory_tokens(self) -> int:
        """Count tokens in current memory"""
        memory_str = json.dumps(list(self.memory_buffer))
        return len(self.token_counter.encode(memory_str))

    def _get_relevant_memory(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve most relevant memories for query"""
        # Simple recency-based retrieval, could be enhanced with embeddings
        return list(self.memory_buffer)[-k:]
''',
                integration_point="__init__",
            ),
            "error_recovery": AgentCapability(
                name="Advanced Error Recovery",
                description="Sophisticated error handling with retry strategies",
                required_imports=[
                    "from tenacity import retry, stop_after_attempt, wait_exponential",
                    "import traceback",
                ],
                code_snippet='''
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Attempt failed: {e}")
            raise

    def _handle_error(self, error: Exception, context: str) -> Optional[Any]:
        """Intelligent error handling with recovery strategies"""
        error_type = type(error).__name__

        # Log detailed error info
        self.logger.error(f"Error in {context}: {error_type} - {str(error)}")
        self.logger.debug(f"Traceback: {traceback.format_exc()}")

        # Log for conversation analysis
        self.log_update(
            f"Encountered {error_type} during {context}. Attempting recovery...",
            metadata={"error_type": error_type, "context": context}
        )

        # Specific recovery strategies
        if error_type == "RateLimitError":
            self.logger.info("Rate limit hit, backing off...")
            return {"retry": True, "wait": 60}
        elif error_type == "ConnectionError":
            self.logger.info("Connection failed, checking alternate routes...")
            return {"retry": True, "wait": 5}
        else:
            # Generic recovery
            return {"retry": True, "wait": 10}
''',
                integration_point="methods",
            ),
            "parallel_execution": AgentCapability(
                name="Parallel Task Execution",
                description="Execute multiple operations concurrently",
                required_imports=[
                    "import asyncio",
                    "from concurrent.futures import ThreadPoolExecutor",
                    "from typing import Coroutine",
                ],
                code_snippet='''
    async def _execute_parallel_tasks(self, tasks: List[Coroutine]) -> List[Any]:
        """Execute multiple async tasks in parallel"""
        self.log_update(f"Executing {len(tasks)} tasks in parallel")

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful = [r for r in results if not isinstance(r, Exception)]
            failed = [r for r in results if isinstance(r, Exception)]

            if failed:
                self.log_update(f"Completed with {len(failed)} failures",
                              metadata={"failures": len(failed), "successes": len(successful)})

            return results

        except Exception as e:
            self.logger.error(f"Parallel execution failed: {e}")
            return []

    def _batch_process(self, items: List[Any], processor_func, batch_size: int = 5):
        """Process items in batches for efficiency"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = [processor_func(item) for item in batch]

            # Execute batch
            batch_results = asyncio.run(self._execute_parallel_tasks(batch_tasks))
            results.extend(batch_results)

        return results
''',
                integration_point="methods",
            ),
            "tool_orchestration": AgentCapability(
                name="Intelligent Tool Orchestration",
                description="Smart tool selection and chaining",
                required_imports=["from typing import Callable", "import inspect"],
                code_snippet='''
    def _analyze_tools(self):
        """Analyze available tools and their capabilities"""
        self.tool_registry = {}

        for tool in self.tools:
            # Extract tool metadata
            tool_name = getattr(tool, 'name', tool.__class__.__name__)
            tool_desc = getattr(tool, 'description', inspect.getdoc(tool))

            self.tool_registry[tool_name] = {
                'tool': tool,
                'description': tool_desc,
                'usage_count': 0,
                'avg_execution_time': 0,
                'success_rate': 1.0
            }

    def _select_best_tool(self, task_description: str) -> Optional[Any]:
        """Select most appropriate tool for task"""
        # Could be enhanced with embeddings for semantic matching
        best_tool = None
        best_score = 0

        for tool_name, tool_info in self.tool_registry.items():
            # Simple keyword matching (could use LLM)
            score = self._calculate_tool_relevance(task_description, tool_info['description'])

            # Adjust score based on performance
            score *= tool_info['success_rate']

            if score > best_score:
                best_score = score
                best_tool = tool_info['tool']

        return best_tool

    def _chain_tools(self, tool_sequence: List[str], initial_input: Any) -> Any:
        """Execute tools in sequence, passing output to next"""
        result = initial_input

        for tool_name in tool_sequence:
            if tool_name in self.tool_registry:
                tool = self.tool_registry[tool_name]['tool']
                self.log_update(f"Executing tool: {tool_name}")

                try:
                    result = tool.run(result)
                    self.tool_registry[tool_name]['usage_count'] += 1
                except Exception as e:
                    self.logger.error(f"Tool {tool_name} failed: {e}")
                    break

        return result
''',
                integration_point="__init__",
            ),
            "adaptive_behavior": AgentCapability(
                name="Adaptive Behavior",
                description="Learn and adapt from interactions",
                required_imports=["from collections import Counter", "import pickle"],
                code_snippet='''
    def _init_adaptive_behavior(self):
        """Initialize adaptive behavior tracking"""
        self.behavior_stats = {
            'successful_patterns': Counter(),
            'failed_patterns': Counter(),
            'peer_preferences': {},
            'task_performance': {}
        }
        self._load_learned_behaviors()

    def _record_interaction_outcome(self, action: str, context: Dict, success: bool):
        """Record outcome of interactions for learning"""
        pattern = f"{action}:{context.get('task_type', 'unknown')}"

        if success:
            self.behavior_stats['successful_patterns'][pattern] += 1
        else:
            self.behavior_stats['failed_patterns'][pattern] += 1

        # Adjust future behavior based on success rates
        self._update_behavior_weights()

    def _update_behavior_weights(self):
        """Update behavior preferences based on outcomes"""
        for pattern in self.behavior_stats['successful_patterns']:
            success_count = self.behavior_stats['successful_patterns'][pattern]
            fail_count = self.behavior_stats['failed_patterns'].get(pattern, 0)

            if success_count + fail_count > 5:  # Minimum sample size
                success_rate = success_count / (success_count + fail_count)

                # Store learned preference
                action, task_type = pattern.split(':', 1)
                if task_type not in self.behavior_stats['task_performance']:
                    self.behavior_stats['task_performance'][task_type] = {}

                self.behavior_stats['task_performance'][task_type][action] = success_rate

    def _choose_action(self, available_actions: List[str], task_type: str) -> str:
        """Choose action based on learned preferences"""
        if task_type in self.behavior_stats['task_performance']:
            # Sort actions by historical success rate
            scored_actions = []
            for action in available_actions:
                score = self.behavior_stats['task_performance'][task_type].get(action, 0.5)
                scored_actions.append((action, score))

            scored_actions.sort(key=lambda x: x[1], reverse=True)
            return scored_actions[0][0]

        # Default to first available action
        return available_actions[0]

    def _save_learned_behaviors(self):
        """Persist learned behaviors"""
        try:
            with open(f"learned_behaviors/{self.team_name}_{self.role}.pkl", 'wb') as f:
                pickle.dump(self.behavior_stats, f)
        except Exception as e:
            self.logger.warning(f"Could not save learned behaviors: {e}")
''',
                integration_point="__init__",
            ),
            "context_awareness": AgentCapability(
                name="Enhanced Context Awareness",
                description="Sophisticated understanding of task and team context",
                required_imports=[
                    "from datetime import datetime, timedelta",
                    "from typing import Set",
                ],
                code_snippet='''
    def _analyze_context(self, task: Any) -> Dict[str, Any]:
        """Analyze comprehensive task and team context"""
        context = {
            'timestamp': datetime.now(),
            'task_description': str(task),
            'team_members_available': self._check_team_availability(),
            'recent_decisions': self._get_recent_decisions(minutes=30),
            'current_workload': self._assess_workload(),
            'external_factors': self._check_external_context()
        }

        # Enhance context with semantic analysis
        context['task_urgency'] = self._assess_urgency(str(task))
        context['required_expertise'] = self._identify_required_skills(str(task))

        return context

    def _check_team_availability(self) -> Set[str]:
        """Check which team members are currently available"""
        available = set()

        # Check recent activity
        recent_logs = self.conversation_logger.get_recent_conversations(limit=20)

        for log in recent_logs:
            if (datetime.now() - datetime.fromisoformat(log['timestamp'])).seconds < 300:
                available.add(log['agent_name'])

        return available

    def _assess_urgency(self, task_description: str) -> str:
        """Assess task urgency from description"""
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'emergency']
        high_keywords = ['important', 'priority', 'soon', 'today']

        task_lower = task_description.lower()

        if any(keyword in task_lower for keyword in urgent_keywords):
            return 'urgent'
        elif any(keyword in task_lower for keyword in high_keywords):
            return 'high'
        else:
            return 'normal'

    def _make_context_aware_decision(self, options: List[str], context: Dict) -> str:
        """Make decisions considering full context"""
        if context['task_urgency'] == 'urgent':
            # Prefer fast options
            return self._select_fastest_option(options)
        elif len(context['team_members_available']) < 2:
            # Prefer autonomous options
            return self._select_most_autonomous_option(options)
        else:
            # Normal decision making
            return self._select_best_option(options, context)
''',
                integration_point="methods",
            ),
        }

        return patterns

    def analyze_agent_requirements(
        self,
        agent_role: str,
        team_purpose: str,
        responsibilities: List[str],
        team_members: List[Dict],
    ) -> Dict[str, Any]:
        """
        Analyze what capabilities an agent needs based on role and team context
        """
        self.console.print(
            f"\n[bold cyan]🔍 Analyzing requirements for {agent_role}[/bold cyan]"
        )

        # Use LLM to analyze requirements
        analysis_prompt = f"""
        Analyze what capabilities and code patterns would make this agent most effective:

        Role: {agent_role}
        Team Purpose: {team_purpose}
        Responsibilities: {', '.join(responsibilities)}
        Team Size: {len(team_members)} members

        Consider:
        1. What types of tasks will this agent handle?
        2. What error conditions might occur?
        3. What tools/APIs might they need to use?
        4. How much autonomy vs collaboration is needed?
        5. What performance optimizations would help?

        Recommend specific capabilities from:
        - Smart memory management
        - Advanced error recovery
        - Parallel task execution
        - Intelligent tool orchestration
        - Adaptive behavior learning
        - Enhanced context awareness

        Format: JSON with reasoning
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in agent architecture and capabilities.",
                    },
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.7,
            )

            # Parse response
            result = json.loads(response.choices[0].message.content)

            return result

        except Exception as e:
            self.console.print(
                f"[yellow]Using default capability analysis: {e}[/yellow]"
            )

            # Fallback analysis based on role
            return self._default_capability_analysis(agent_role, responsibilities)

    def _default_capability_analysis(
        self, agent_role: str, responsibilities: List[str]
    ) -> Dict[str, Any]:
        """Fallback capability analysis based on role patterns"""

        role_lower = agent_role.lower()
        capabilities = []

        # Manager roles need coordination capabilities
        if any(term in role_lower for term in ["manager", "lead", "director"]):
            capabilities.extend(
                ["context_awareness", "parallel_execution", "adaptive_behavior"]
            )

        # Analyst roles need data processing
        if any(term in role_lower for term in ["analyst", "data", "research"]):
            capabilities.extend(["smart_memory", "tool_orchestration"])

        # Skeptic roles need thorough analysis
        if "skeptic" in role_lower or "critic" in role_lower:
            capabilities.extend(["context_awareness", "error_recovery"])

        # Technical roles need robust execution
        if any(term in role_lower for term in ["engineer", "developer", "technical"]):
            capabilities.extend(
                ["error_recovery", "parallel_execution", "tool_orchestration"]
            )

        # Creative roles need flexibility
        if any(term in role_lower for term in ["creative", "content", "design"]):
            capabilities.extend(["adaptive_behavior", "smart_memory"])

        # Default capabilities for all agents
        if not capabilities:
            capabilities = ["error_recovery", "context_awareness"]

        return {
            "recommended_capabilities": capabilities,
            "reasoning": f"Based on role '{agent_role}', recommended capabilities for optimal performance",
        }

    def generate_enhanced_agent_code(
        self, agent_spec: Dict, capabilities: List[str], framework: str = "crewai"
    ) -> str:
        """
        Generate enhanced agent code with selected capabilities
        """

        # Collect all required imports
        all_imports = set()

        # Collect initialization code
        init_additions = []

        # Collect method additions
        method_additions = []

        # Process each capability
        for cap_name in capabilities:
            if cap_name in self.capability_patterns:
                capability = self.capability_patterns[cap_name]

                # Add imports
                all_imports.update(capability.required_imports)

                # Add code based on integration point
                if capability.integration_point == "__init__":
                    init_additions.append(capability.code_snippet)
                elif capability.integration_point == "methods":
                    method_additions.append(capability.code_snippet)

        # Generate enhanced code structure
        enhanced_code = self._build_enhanced_agent_code(
            agent_spec, list(all_imports), init_additions, method_additions, framework
        )

        return enhanced_code

    def _build_enhanced_agent_code(
        self,
        agent_spec: Dict,
        imports: List[str],
        init_additions: List[str],
        method_additions: List[str],
        framework: str,
    ) -> str:
        """Build the complete enhanced agent code"""

        # This would integrate with existing agent template
        # For now, showing the enhancement structure

        enhancements = {
            "additional_imports": "\n".join(imports),
            "init_additions": "\n".join(init_additions),
            "method_additions": "\n".join(method_additions),
        }

        return enhancements

    def review_generated_code(
        self, code: str, agent_role: str
    ) -> Tuple[str, List[str]]:
        """
        Use LLM to review and improve generated code
        """
        review_prompt = f"""
        Review this agent code for the role '{agent_role}' and suggest improvements:

        {code[:2000]}  # First 2000 chars for context

        Check for:
        1. Error handling completeness
        2. Performance optimization opportunities
        3. Better abstraction patterns
        4. Missing edge cases
        5. Security considerations

        Provide:
        1. Improved code snippets
        2. List of potential issues
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer."},
                    {"role": "user", "content": review_prompt},
                ],
                temperature=0.3,
            )

            # Parse improvements
            review_result = response.choices[0].message.content

            return review_result, []

        except Exception as e:
            return code, [f"Review failed: {str(e)}"]


def demonstrate_code_enhancement():
    """Demonstrate enhanced code generation"""

    enhancer = AgentCodeEnhancer()

    # Example agent specification
    agent_spec = {
        "role": "Marketing Data Analyst",
        "team": "marketing-team",
        "responsibilities": [
            "Analyze campaign performance data",
            "Generate insights and recommendations",
            "Create data visualizations",
        ],
    }

    console.print(
        Panel(
            f"[bold]Agent:[/bold] {agent_spec['role']}\n"
            f"[bold]Team:[/bold] {agent_spec['team']}\n"
            f"[bold]Responsibilities:[/bold]\n"
            + "\n".join(f"  • {r}" for r in agent_spec["responsibilities"]),
            title="Agent Specification",
            border_style="blue",
        )
    )

    # Analyze requirements
    analysis = enhancer._default_capability_analysis(
        agent_spec["role"], agent_spec["responsibilities"]
    )

    console.print(f"\n[bold]Recommended Capabilities:[/bold]")
    for cap in analysis["recommended_capabilities"]:
        console.print(f"  ✓ {cap}")

    # Show example enhancement
    console.print("\n[bold]Example Code Enhancement:[/bold]")

    example_capability = enhancer.capability_patterns["smart_memory"]

    syntax = Syntax(
        example_capability.code_snippet, "python", theme="monokai", line_numbers=True
    )

    console.print(
        Panel(
            syntax,
            title=f"Enhancement: {example_capability.name}",
            border_style="green",
        )
    )

    console.print(
        "\n[bold green]✨ This agent will have advanced memory management for better context retention![/bold green]"
    )


if __name__ == "__main__":
    demonstrate_code_enhancement()
