#!/usr/bin/env python3
"""
Enhanced Marketing Data Analyst Agent
Generated with intelligent code enhancement
"""

import asyncio
import json
import logging
import os
import traceback

# Enhanced imports for advanced capabilities
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

import tiktoken
from crewai import Agent
from tenacity import retry, stop_after_attempt, wait_exponential

from tools.conversation_logging_system import ConversationLogger, MessageType


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
            "tasks_completed": 0,
            "avg_completion_time": 0,
            "error_rate": 0,
            "tool_usage": Counter(),
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
            memory=True,  # Enable CrewAI memory
        )

    # === SMART MEMORY MANAGEMENT ===

    def _init_smart_memory(self, max_tokens: int = 4000):
        """Initialize smart memory management"""
        self.memory_buffer: Deque[Dict[str, Any]] = deque(maxlen=50)
        self.token_counter = tiktoken.encoding_for_model("gpt-4")
        self.max_memory_tokens = max_tokens

    def _add_to_memory(self, content: Dict[str, Any]):
        """Add to memory with token management"""
        content["timestamp"] = datetime.now().isoformat()
        self.memory_buffer.append(content)
        self._trim_memory_by_tokens()

    def _trim_memory_by_tokens(self):
        """Keep memory within token limits"""
        while (
            self._count_memory_tokens() > self.max_memory_tokens
            and len(self.memory_buffer) > 1
        ):
            removed = self.memory_buffer.popleft()
            self.logger.debug(f"Trimmed memory item from {removed['timestamp']}")

    def _count_memory_tokens(self) -> int:
        """Count tokens in current memory"""
        memory_str = json.dumps(list(self.memory_buffer))
        return len(self.token_counter.encode(memory_str))

    # === ERROR RECOVERY ===

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        try:
            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )
            return result
        except Exception as e:
            self.logger.warning(f"Attempt failed: {e}")
            self.performance_metrics["error_rate"] = (
                self.performance_metrics.get("error_count", 0) + 1
            ) / (self.performance_metrics["tasks_completed"] + 1)
            raise

    def _handle_error(self, error: Exception, context: str) -> Optional[Dict[str, Any]]:
        """Intelligent error handling with recovery strategies"""
        error_type = type(error).__name__

        # Log detailed error info
        self.logger.error(f"Error in {context}: {error_type} - {str(error)}")

        # Add to memory for learning
        self._add_to_memory(
            {
                "type": "error",
                "error_type": error_type,
                "context": context,
                "message": str(error),
            }
        )

        # Log for conversation analysis
        self.log_update(
            f"Encountered {error_type} during {context}. Implementing recovery strategy.",
            metadata={"error_type": error_type, "context": context},
        )

        # Specific recovery strategies
        recovery_strategies = {
            "RateLimitError": {"retry": True, "wait": 60, "strategy": "backoff"},
            "ConnectionError": {"retry": True, "wait": 5, "strategy": "reconnect"},
            "DataError": {"retry": False, "strategy": "validate_inputs"},
            "ToolError": {"retry": True, "wait": 10, "strategy": "fallback_tool"},
        }

        return recovery_strategies.get(
            error_type, {"retry": True, "wait": 10, "strategy": "generic"}
        )

    # === PARALLEL EXECUTION ===

    async def analyze_campaigns_parallel(
        self, campaign_ids: List[str]
    ) -> Dict[str, Any]:
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
            metadata={
                "campaigns_analyzed": len(campaign_ids),
                "duration": aggregated["duration"],
            },
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

            self.performance_metrics["tasks_completed"] += len(successful)
            self.performance_metrics["avg_completion_time"] = (
                self.performance_metrics["avg_completion_time"]
                * (self.performance_metrics["tasks_completed"] - len(successful))
                + duration
            ) / self.performance_metrics["tasks_completed"]

            return results

        except Exception as e:
            self.logger.error(f"Parallel execution failed: {e}")
            return []

    # === TOOL ORCHESTRATION ===

    def _analyze_tools(self):
        """Analyze and categorize available tools"""
        self.tool_registry = {}

        for tool in self.tools:
            tool_name = getattr(tool, "name", tool.__class__.__name__)

            # Categorize tools by capability
            tool_category = self._categorize_tool(tool)

            self.tool_registry[tool_name] = {
                "tool": tool,
                "category": tool_category,
                "usage_count": 0,
                "avg_execution_time": 0,
                "success_rate": 1.0,
                "last_used": None,
            }

    def _categorize_tool(self, tool) -> str:
        """Categorize tool by its primary function"""
        tool_name = str(tool).lower()

        if any(term in tool_name for term in ["search", "query", "find"]):
            return "search"
        elif any(term in tool_name for term in ["analyze", "calculate", "compute"]):
            return "analysis"
        elif any(term in tool_name for term in ["visual", "chart", "graph"]):
            return "visualization"
        elif any(term in tool_name for term in ["report", "export", "save"]):
            return "reporting"
        else:
            return "general"

    def select_optimal_tool_sequence(self, task_description: str) -> List[str]:
        """Select optimal sequence of tools for a task"""
        # Analyze task requirements
        task_lower = task_description.lower()

        tool_sequence = []

        # Determine needed tool categories
        if "data" in task_lower or "analyze" in task_lower:
            # Start with search/retrieval
            search_tools = [
                name
                for name, info in self.tool_registry.items()
                if info["category"] == "search"
            ]
            if search_tools:
                tool_sequence.append(search_tools[0])

            # Then analysis
            analysis_tools = [
                name
                for name, info in self.tool_registry.items()
                if info["category"] == "analysis"
            ]
            if analysis_tools:
                tool_sequence.append(analysis_tools[0])

        if "visualiz" in task_lower or "chart" in task_lower:
            viz_tools = [
                name
                for name, info in self.tool_registry.items()
                if info["category"] == "visualization"
            ]
            if viz_tools:
                tool_sequence.append(viz_tools[0])

        if "report" in task_lower:
            report_tools = [
                name
                for name, info in self.tool_registry.items()
                if info["category"] == "reporting"
            ]
            if report_tools:
                tool_sequence.append(report_tools[0])

        return tool_sequence

    # === ADAPTIVE BEHAVIOR ===

    def _init_adaptive_behavior(self):
        """Initialize adaptive behavior tracking"""
        self.behavior_stats = {
            "successful_patterns": Counter(),
            "failed_patterns": Counter(),
            "tool_performance": {},
            "optimal_sequences": {},
        }

        # Load previously learned behaviors
        self._load_learned_behaviors()

    def _record_task_outcome(
        self, task_type: str, approach: str, success: bool, metrics: Dict[str, Any]
    ):
        """Record task outcome for learning"""
        pattern_key = f"{task_type}:{approach}"

        if success:
            self.behavior_stats["successful_patterns"][pattern_key] += 1
        else:
            self.behavior_stats["failed_patterns"][pattern_key] += 1

        # Update performance metrics
        if task_type not in self.behavior_stats["tool_performance"]:
            self.behavior_stats["tool_performance"][task_type] = {}

        self.behavior_stats["tool_performance"][task_type][approach] = {
            "success_rate": self._calculate_success_rate(pattern_key),
            "avg_duration": metrics.get("duration", 0),
            "last_used": datetime.now().isoformat(),
        }

        # Save learned behaviors periodically
        if self.performance_metrics["tasks_completed"] % 10 == 0:
            self._save_learned_behaviors()

    def _calculate_success_rate(self, pattern_key: str) -> float:
        """Calculate success rate for a pattern"""
        successes = self.behavior_stats["successful_patterns"].get(pattern_key, 0)
        failures = self.behavior_stats["failed_patterns"].get(pattern_key, 0)

        total = successes + failures
        return successes / total if total > 0 else 0.5

    # === MAIN EXECUTION ===

    async def execute_with_enhancement(self, task):
        """Execute task with all enhancements active"""
        task_start = datetime.now()
        task_type = self._classify_task(task)

        # Add task to memory
        self._add_to_memory(
            {"type": "task_start", "task": str(task), "task_type": task_type}
        )

        # Log task start
        self.log_update(f"Analyzing task: {str(task)[:100]}...")

        try:
            # Select optimal approach based on learned behavior
            approach = self._select_optimal_approach(task_type)

            # Execute with retry logic
            result = await self._execute_with_retry(
                self._execute_task_with_approach, task, approach
            )

            # Record success
            duration = (datetime.now() - task_start).total_seconds()
            self._record_task_outcome(
                task_type,
                approach,
                True,
                {
                    "duration": duration,
                    "result_quality": self._assess_result_quality(result),
                },
            )

            # Add result to memory
            self._add_to_memory(
                {
                    "type": "task_complete",
                    "task_type": task_type,
                    "approach": approach,
                    "duration": duration,
                    "success": True,
                }
            )

            self.log_update(f"Task completed successfully in {duration:.1f}s")

            return result

        except Exception as e:
            # Handle error with recovery
            recovery = self._handle_error(e, f"executing {task_type} task")

            if recovery and recovery.get("retry"):
                # Implement recovery strategy
                self.logger.info(
                    f"Implementing {recovery.get('strategy')} recovery strategy"
                )
                await asyncio.sleep(recovery.get("wait", 10))

                # Try alternative approach
                fallback_approach = self._get_fallback_approach(task_type, approach)
                return await self._execute_task_with_approach(task, fallback_approach)

            # Record failure
            self._record_task_outcome(task_type, approach, False, {"error": str(e)})
            raise

    def _classify_task(self, task) -> str:
        """Classify task type for adaptive behavior"""
        task_str = str(task).lower()

        if "campaign" in task_str and "performance" in task_str:
            return "campaign_analysis"
        elif "roi" in task_str or "return" in task_str:
            return "roi_analysis"
        elif "segment" in task_str or "audience" in task_str:
            return "segmentation"
        elif "trend" in task_str or "forecast" in task_str:
            return "predictive"
        else:
            return "general_analysis"

    def _select_optimal_approach(self, task_type: str) -> str:
        """Select optimal approach based on learned behavior"""
        if task_type in self.behavior_stats["tool_performance"]:
            # Sort approaches by success rate and recency
            approaches = self.behavior_stats["tool_performance"][task_type]

            scored_approaches = []
            for approach, metrics in approaches.items():
                # Score based on success rate and recency
                score = metrics["success_rate"]

                # Boost score for recently successful approaches
                if metrics.get("last_used"):
                    days_since = (
                        datetime.now() - datetime.fromisoformat(metrics["last_used"])
                    ).days
                    recency_boost = max(0, 1 - (days_since / 30))  # Decay over 30 days
                    score += recency_boost * 0.2

                scored_approaches.append((approach, score))

            # Select highest scoring approach
            scored_approaches.sort(key=lambda x: x[1], reverse=True)
            return scored_approaches[0][0]

        # Default approach
        return "comprehensive_analysis"

    # === CONVERSATION LOGGING (Enhanced) ===

    def log_analysis_insight(
        self,
        insight: str,
        confidence: float = 0.8,
        supporting_data: Optional[Dict] = None,
    ):
        """Log analytical insights with metadata"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=f"[INSIGHT] {insight}",
            message_type=MessageType.UPDATE,
            metadata={
                "confidence": confidence,
                "supporting_data": supporting_data or {},
                "methodology": self.behavior_stats.get("last_approach", "standard"),
            },
        )

        # Also add to memory for context
        self._add_to_memory(
            {
                "type": "insight",
                "content": insight,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
            }
        )


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
