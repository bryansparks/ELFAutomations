#!/usr/bin/env python3
"""
Integration guide for adding code enhancement to team factory
Shows how to modify agent generation to include sophisticated capabilities
"""

import textwrap
from pathlib import Path


def create_enhanced_agent_template():
    """Create template showing how enhanced agents look"""

    enhanced_agent_example = '''#!/usr/bin/env python3
"""
Enhanced Marketing Data Analyst Agent
Generated with intelligent code enhancement
"""

from crewai import Agent
from typing import Optional, List, Dict, Any, Deque
import logging
import os
from datetime import datetime
from tools.conversation_logging_system import ConversationLogger, MessageType

# Enhanced imports for advanced capabilities
from collections import deque, Counter
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
import json


class MarketingDataAnalystAgent:
    """
    Enhanced Marketing Data Analyst with advanced capabilities:
    - Smart memory management with token counting
    - Robust error recovery with retry strategies
    - Parallel data processing for performance
    - Adaptive behavior based on task success
    """

    def __init__(self, tools: Optional[List] = None):
        self.logger = logging.getLogger("marketing-team.Marketing Data Analyst")
        self.tools = tools or []
        self.role = "Marketing Data Analyst"
        self.team_name = "marketing-team"

        # Standard agent setup
        self.agent = self._create_agent()
        self.conversation_logger = ConversationLogger(self.team_name)

        # === ENHANCED CAPABILITIES ===

        # Smart Memory Management
        self._init_smart_memory(max_tokens=4000)

        # Tool Orchestration
        self._analyze_tools()

        # Adaptive Behavior
        self._init_adaptive_behavior()

        # Performance Tracking
        self.performance_metrics = {
            'tasks_completed': 0,
            'avg_completion_time': 0,
            'error_rate': 0,
            'tool_usage': Counter()
        }

    def _create_agent(self) -> Agent:
        """Create the CrewAI agent with enhanced configuration"""
        from langchain_openai import ChatOpenAI

        return Agent(
            role=self.role,
            goal="Analyze marketing data to provide actionable insights that drive campaign success",
            backstory="""You are an expert Marketing Data Analyst with deep expertise in:
            - Statistical analysis and data visualization
            - Campaign performance optimization
            - Predictive modeling for customer behavior
            - ROI analysis and budget optimization

            You approach every analysis with rigor, always backing insights with data.""",
            tools=self.tools,
            llm=ChatOpenAI(model="gpt-4", temperature=0.7),
            verbose=True,
            max_iter=5,  # Prevent infinite loops
            memory=True   # Enable CrewAI memory
        )

    # === SMART MEMORY MANAGEMENT ===

    def _init_smart_memory(self, max_tokens: int = 4000):
        """Initialize smart memory management"""
        self.memory_buffer: Deque[Dict[str, Any]] = deque(maxlen=50)
        self.token_counter = tiktoken.encoding_for_model("gpt-4")
        self.max_memory_tokens = max_tokens

    def _add_to_memory(self, content: Dict[str, Any]):
        """Add to memory with token management"""
        content['timestamp'] = datetime.now().isoformat()
        self.memory_buffer.append(content)
        self._trim_memory_by_tokens()

    def _trim_memory_by_tokens(self):
        """Keep memory within token limits"""
        while self._count_memory_tokens() > self.max_memory_tokens and len(self.memory_buffer) > 1:
            removed = self.memory_buffer.popleft()
            self.logger.debug(f"Trimmed memory item from {removed['timestamp']}")

    def _count_memory_tokens(self) -> int:
        """Count tokens in current memory"""
        memory_str = json.dumps(list(self.memory_buffer))
        return len(self.token_counter.encode(memory_str))

    # === ERROR RECOVERY ===

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            return result
        except Exception as e:
            self.logger.warning(f"Attempt failed: {e}")
            self.performance_metrics['error_rate'] = (
                self.performance_metrics.get('error_count', 0) + 1
            ) / (self.performance_metrics['tasks_completed'] + 1)
            raise

    def _handle_error(self, error: Exception, context: str) -> Optional[Dict[str, Any]]:
        """Intelligent error handling with recovery strategies"""
        error_type = type(error).__name__

        # Log detailed error info
        self.logger.error(f"Error in {context}: {error_type} - {str(error)}")

        # Add to memory for learning
        self._add_to_memory({
            'type': 'error',
            'error_type': error_type,
            'context': context,
            'message': str(error)
        })

        # Log for conversation analysis
        self.log_update(
            f"Encountered {error_type} during {context}. Implementing recovery strategy.",
            metadata={"error_type": error_type, "context": context}
        )

        # Specific recovery strategies
        recovery_strategies = {
            "RateLimitError": {"retry": True, "wait": 60, "strategy": "backoff"},
            "ConnectionError": {"retry": True, "wait": 5, "strategy": "reconnect"},
            "DataError": {"retry": False, "strategy": "validate_inputs"},
            "ToolError": {"retry": True, "wait": 10, "strategy": "fallback_tool"}
        }

        return recovery_strategies.get(error_type, {"retry": True, "wait": 10, "strategy": "generic"})

    # === PARALLEL EXECUTION ===

    async def analyze_campaigns_parallel(self, campaign_ids: List[str]) -> Dict[str, Any]:
        """Analyze multiple campaigns in parallel for efficiency"""
        self.log_update(f"Starting parallel analysis of {len(campaign_ids)} campaigns")

        # Create analysis tasks
        tasks = [self._analyze_single_campaign(cid) for cid in campaign_ids]

        # Execute in parallel
        results = await self._execute_parallel_tasks(tasks)

        # Aggregate results
        aggregated = self._aggregate_campaign_results(results)

        self.log_update(
            f"Completed parallel analysis. Success rate: {aggregated['success_rate']:.1%}",
            metadata={"campaigns_analyzed": len(campaign_ids), "duration": aggregated['duration']}
        )

        return aggregated

    async def _execute_parallel_tasks(self, tasks: List) -> List[Any]:
        """Execute multiple async tasks in parallel with monitoring"""
        start_time = datetime.now()

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Track performance
            duration = (datetime.now() - start_time).total_seconds()
            successful = [r for r in results if not isinstance(r, Exception)]

            self.performance_metrics['tasks_completed'] += len(successful)
            self.performance_metrics['avg_completion_time'] = (
                (self.performance_metrics['avg_completion_time'] *
                 (self.performance_metrics['tasks_completed'] - len(successful)) +
                 duration) / self.performance_metrics['tasks_completed']
            )

            return results

        except Exception as e:
            self.logger.error(f"Parallel execution failed: {e}")
            return []

    # === TOOL ORCHESTRATION ===

    def _analyze_tools(self):
        """Analyze and categorize available tools"""
        self.tool_registry = {}

        for tool in self.tools:
            tool_name = getattr(tool, 'name', tool.__class__.__name__)

            # Categorize tools by capability
            tool_category = self._categorize_tool(tool)

            self.tool_registry[tool_name] = {
                'tool': tool,
                'category': tool_category,
                'usage_count': 0,
                'avg_execution_time': 0,
                'success_rate': 1.0,
                'last_used': None
            }

    def _categorize_tool(self, tool) -> str:
        """Categorize tool by its primary function"""
        tool_name = str(tool).lower()

        if any(term in tool_name for term in ['search', 'query', 'find']):
            return 'search'
        elif any(term in tool_name for term in ['analyze', 'calculate', 'compute']):
            return 'analysis'
        elif any(term in tool_name for term in ['visual', 'chart', 'graph']):
            return 'visualization'
        elif any(term in tool_name for term in ['report', 'export', 'save']):
            return 'reporting'
        else:
            return 'general'

    def select_optimal_tool_sequence(self, task_description: str) -> List[str]:
        """Select optimal sequence of tools for a task"""
        # Analyze task requirements
        task_lower = task_description.lower()

        tool_sequence = []

        # Determine needed tool categories
        if 'data' in task_lower or 'analyze' in task_lower:
            # Start with search/retrieval
            search_tools = [name for name, info in self.tool_registry.items()
                          if info['category'] == 'search']
            if search_tools:
                tool_sequence.append(search_tools[0])

            # Then analysis
            analysis_tools = [name for name, info in self.tool_registry.items()
                            if info['category'] == 'analysis']
            if analysis_tools:
                tool_sequence.append(analysis_tools[0])

        if 'visualiz' in task_lower or 'chart' in task_lower:
            viz_tools = [name for name, info in self.tool_registry.items()
                        if info['category'] == 'visualization']
            if viz_tools:
                tool_sequence.append(viz_tools[0])

        if 'report' in task_lower:
            report_tools = [name for name, info in self.tool_registry.items()
                          if info['category'] == 'reporting']
            if report_tools:
                tool_sequence.append(report_tools[0])

        return tool_sequence

    # === ADAPTIVE BEHAVIOR ===

    def _init_adaptive_behavior(self):
        """Initialize adaptive behavior tracking"""
        self.behavior_stats = {
            'successful_patterns': Counter(),
            'failed_patterns': Counter(),
            'tool_performance': {},
            'optimal_sequences': {}
        }

        # Load previously learned behaviors
        self._load_learned_behaviors()

    def _record_task_outcome(self, task_type: str, approach: str,
                           success: bool, metrics: Dict[str, Any]):
        """Record task outcome for learning"""
        pattern_key = f"{task_type}:{approach}"

        if success:
            self.behavior_stats['successful_patterns'][pattern_key] += 1
        else:
            self.behavior_stats['failed_patterns'][pattern_key] += 1

        # Update performance metrics
        if task_type not in self.behavior_stats['tool_performance']:
            self.behavior_stats['tool_performance'][task_type] = {}

        self.behavior_stats['tool_performance'][task_type][approach] = {
            'success_rate': self._calculate_success_rate(pattern_key),
            'avg_duration': metrics.get('duration', 0),
            'last_used': datetime.now().isoformat()
        }

        # Save learned behaviors periodically
        if self.performance_metrics['tasks_completed'] % 10 == 0:
            self._save_learned_behaviors()

    def _calculate_success_rate(self, pattern_key: str) -> float:
        """Calculate success rate for a pattern"""
        successes = self.behavior_stats['successful_patterns'].get(pattern_key, 0)
        failures = self.behavior_stats['failed_patterns'].get(pattern_key, 0)

        total = successes + failures
        return successes / total if total > 0 else 0.5

    # === MAIN EXECUTION ===

    async def execute_with_enhancement(self, task):
        """Execute task with all enhancements active"""
        task_start = datetime.now()
        task_type = self._classify_task(task)

        # Add task to memory
        self._add_to_memory({
            'type': 'task_start',
            'task': str(task),
            'task_type': task_type
        })

        # Log task start
        self.log_update(f"Analyzing task: {str(task)[:100]}...")

        try:
            # Select optimal approach based on learned behavior
            approach = self._select_optimal_approach(task_type)

            # Execute with retry logic
            result = await self._execute_with_retry(
                self._execute_task_with_approach,
                task, approach
            )

            # Record success
            duration = (datetime.now() - task_start).total_seconds()
            self._record_task_outcome(
                task_type, approach, True,
                {'duration': duration, 'result_quality': self._assess_result_quality(result)}
            )

            # Add result to memory
            self._add_to_memory({
                'type': 'task_complete',
                'task_type': task_type,
                'approach': approach,
                'duration': duration,
                'success': True
            })

            self.log_update(f"Task completed successfully in {duration:.1f}s")

            return result

        except Exception as e:
            # Handle error with recovery
            recovery = self._handle_error(e, f"executing {task_type} task")

            if recovery and recovery.get('retry'):
                # Implement recovery strategy
                self.logger.info(f"Implementing {recovery.get('strategy')} recovery strategy")
                await asyncio.sleep(recovery.get('wait', 10))

                # Try alternative approach
                fallback_approach = self._get_fallback_approach(task_type, approach)
                return await self._execute_task_with_approach(task, fallback_approach)

            # Record failure
            self._record_task_outcome(task_type, approach, False, {'error': str(e)})
            raise

    def _classify_task(self, task) -> str:
        """Classify task type for adaptive behavior"""
        task_str = str(task).lower()

        if 'campaign' in task_str and 'performance' in task_str:
            return 'campaign_analysis'
        elif 'roi' in task_str or 'return' in task_str:
            return 'roi_analysis'
        elif 'segment' in task_str or 'audience' in task_str:
            return 'segmentation'
        elif 'trend' in task_str or 'forecast' in task_str:
            return 'predictive'
        else:
            return 'general_analysis'

    def _select_optimal_approach(self, task_type: str) -> str:
        """Select optimal approach based on learned behavior"""
        if task_type in self.behavior_stats['tool_performance']:
            # Sort approaches by success rate and recency
            approaches = self.behavior_stats['tool_performance'][task_type]

            scored_approaches = []
            for approach, metrics in approaches.items():
                # Score based on success rate and recency
                score = metrics['success_rate']

                # Boost score for recently successful approaches
                if metrics.get('last_used'):
                    days_since = (datetime.now() - datetime.fromisoformat(metrics['last_used'])).days
                    recency_boost = max(0, 1 - (days_since / 30))  # Decay over 30 days
                    score += recency_boost * 0.2

                scored_approaches.append((approach, score))

            # Select highest scoring approach
            scored_approaches.sort(key=lambda x: x[1], reverse=True)
            return scored_approaches[0][0]

        # Default approach
        return 'comprehensive_analysis'

    # === CONVERSATION LOGGING (Enhanced) ===

    def log_analysis_insight(self, insight: str, confidence: float = 0.8,
                           supporting_data: Optional[Dict] = None):
        """Log analytical insights with metadata"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=f"[INSIGHT] {insight}",
            message_type=MessageType.UPDATE,
            metadata={
                'confidence': confidence,
                'supporting_data': supporting_data or {},
                'methodology': self.behavior_stats.get('last_approach', 'standard')
            }
        )

        # Also add to memory for context
        self._add_to_memory({
            'type': 'insight',
            'content': insight,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })


# Example usage
if __name__ == "__main__":
    # Create enhanced agent
    analyst = MarketingDataAnalystAgent(tools=[])

    # Demonstrate capabilities
    print("Enhanced Marketing Data Analyst Agent")
    print("Capabilities:")
    print("- Smart memory management with token limits")
    print("- Parallel campaign analysis")
    print("- Adaptive behavior based on success patterns")
    print("- Robust error recovery")
    print("- Intelligent tool orchestration")
'''

    return enhanced_agent_example


def show_integration_steps():
    """Show how to integrate code enhancement into team factory"""

    integration_guide = """
    INTEGRATION STEPS FOR TEAM FACTORY:

    1. Add agent_code_enhancer import to team_factory.py:
       from agent_code_enhancer import AgentCodeEnhancer

    2. Initialize enhancer in TeamFactory.__init__:
       self.code_enhancer = AgentCodeEnhancer()

    3. In _generate_crewai_agents method, before writing agent file:

       # Analyze agent requirements
       capabilities = self.code_enhancer.analyze_agent_requirements(
           agent_role=member.role,
           team_purpose=team_spec.purpose,
           responsibilities=member.responsibilities,
           team_members=[m.__dict__ for m in team_spec.members]
       )

       # Get recommended capabilities
       recommended = capabilities.get('recommended_capabilities', [])

       # Generate enhancements
       enhancements = self.code_enhancer.generate_enhanced_agent_code(
           agent_spec={
               'role': member.role,
               'team': team_spec.name,
               'responsibilities': member.responsibilities
           },
           capabilities=recommended,
           framework='crewai'
       )

       # Insert enhancements into agent_content
       # Add imports after existing imports
       agent_content = agent_content.replace(
           'from tools.conversation_logging_system import ConversationLogger, MessageType',
           f'from tools.conversation_logging_system import ConversationLogger, MessageType\\n{enhancements["additional_imports"]}'
       )

       # Add init enhancements
       init_marker = 'self.conversation_logger = ConversationLogger("{team_spec.name}")'
       agent_content = agent_content.replace(
           init_marker,
           f'{init_marker}\\n{enhancements["init_additions"]}'
       )

       # Add method enhancements before closing class
       agent_content = agent_content.replace(
           'return state\\n\'\'\'',
           f'return state\\n{enhancements["method_additions"]}\\n\'\'\''
       )

    4. Optional: Add user prompt for capability selection:

       if Confirm.ask("\\nWould you like to enhance agents with advanced capabilities?"):
           self.console.print("\\n[bold]Available Enhancements:[/bold]")
           self.console.print("1. Smart Memory Management - Token-aware context")
           self.console.print("2. Error Recovery - Robust retry strategies")
           self.console.print("3. Parallel Execution - Concurrent task processing")
           self.console.print("4. Tool Orchestration - Intelligent tool selection")
           self.console.print("5. Adaptive Behavior - Learn from outcomes")
           self.console.print("6. Context Awareness - Sophisticated decision making")

           selected = Prompt.ask("Select capabilities (comma-separated numbers, or 'all')")
    """

    return integration_guide


def create_capability_selector():
    """Create interactive capability selector for team factory"""

    selector_code = '''
def select_agent_capabilities(self, member: TeamMember, team_spec: TeamSpecification) -> List[str]:
    """Interactive selection of agent capabilities"""

    self.console.print(f"\\n[bold cyan]🚀 Enhancing {member.role}[/bold cyan]")

    # Get recommendations
    analysis = self.code_enhancer.analyze_agent_requirements(
        agent_role=member.role,
        team_purpose=team_spec.purpose,
        responsibilities=member.responsibilities,
        team_members=[m.__dict__ for m in team_spec.members]
    )

    recommended = analysis.get('recommended_capabilities', [])

    # Display recommendations
    self.console.print("\\n[bold]Recommended Capabilities:[/bold]")
    for cap in recommended:
        self.console.print(f"  ✓ {cap}")

    # Allow customization
    if Confirm.ask("\\nAccept recommendations?", default=True):
        return recommended
    else:
        # Show all options
        all_capabilities = [
            "smart_memory",
            "error_recovery",
            "parallel_execution",
            "tool_orchestration",
            "adaptive_behavior",
            "context_awareness"
        ]

        selected = []
        for cap in all_capabilities:
            if Confirm.ask(f"Include {cap}?", default=cap in recommended):
                selected.append(cap)

        return selected
'''

    return selector_code


if __name__ == "__main__":
    print("=" * 60)
    print("CODE ENHANCEMENT INTEGRATION GUIDE")
    print("=" * 60)

    # Show enhanced agent example
    enhanced_example = create_enhanced_agent_template()

    # Save example
    with open("example_enhanced_agent.py", "w") as f:
        f.write(enhanced_example)

    print("\n✅ Created: example_enhanced_agent.py")
    print("   This shows a fully enhanced agent with all capabilities")

    # Show integration steps
    print("\n" + show_integration_steps())

    # Show capability selector
    print("\nCAPABILITY SELECTOR CODE:")
    print("-" * 40)
    print(create_capability_selector())

    print("\n🚀 KEY BENEFITS:")
    print("1. Agents start with production-ready error handling")
    print("2. Built-in performance optimizations")
    print("3. Learning capabilities from day one")
    print("4. Consistent quality across all agents")
    print("5. Best practices baked into the code")

    print("\n✨ With code enhancement, your agents are born sophisticated!")
