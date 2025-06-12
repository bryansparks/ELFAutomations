"""
Memory Agent Mixin - Adds memory and learning capabilities to any agent

This mixin can be added to both CrewAI and LangGraph agents to provide:
- Automatic episode recording
- Experience-based decision making
- Learning from outcomes
- Knowledge sharing with team
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from functools import wraps

from .team_memory import TeamMemory
from .learning_system import LearningSystem


class MemoryAgentMixin:
    """
    Mixin class that adds memory and learning capabilities to agents.
    
    Usage:
        class MyAgent(BaseAgent, MemoryAgentMixin):
            def __init__(self, ...):
                super().__init__(...)
                self.init_memory(team_name)
    """
    
    def init_memory(self, team_name: str, qdrant_url: str = "http://localhost:6333"):
        """
        Initialize memory system for the agent.
        
        Args:
            team_name: Name of the team this agent belongs to
            qdrant_url: URL of Qdrant service
        """
        self.team_memory = TeamMemory(team_name, qdrant_url)
        self.learning_system = LearningSystem(self.team_memory)
        self.current_episode = None
        self.memory_logger = logging.getLogger(f"MemoryAgent.{team_name}.{getattr(self, 'role', 'agent')}")
    
    def start_episode(self, task_description: str, context: Optional[Dict[str, Any]] = None):
        """
        Start recording a new episode.
        
        Args:
            task_description: Description of the task
            context: Optional context information
        """
        self.current_episode = {
            'task_description': task_description,
            'context': context or {},
            'start_time': time.time(),
            'actions': [],
            'agent_contributions': {},
            'intermediate_results': []
        }
        
        # Check for relevant past experiences
        self._recall_relevant_experiences(task_description)
        
        # Get strategy recommendations
        self._apply_learned_strategies(task_description)
        
        self.memory_logger.info(f"Started episode: {task_description}")
    
    def record_action(self, action: str, details: Optional[Dict[str, Any]] = None):
        """
        Record an action taken during the episode.
        
        Args:
            action: Description of the action
            details: Optional additional details
        """
        if not self.current_episode:
            return
        
        action_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'agent': getattr(self, 'role', 'unknown'),
            'details': details or {}
        }
        
        self.current_episode['actions'].append(action_record)
        
        # Update agent contributions
        agent_name = getattr(self, 'role', 'unknown')
        if agent_name not in self.current_episode['agent_contributions']:
            self.current_episode['agent_contributions'][agent_name] = []
        self.current_episode['agent_contributions'][agent_name].append(action)
        
        self.memory_logger.debug(f"Recorded action: {action}")
    
    def record_intermediate_result(self, result: Any, description: str = ""):
        """
        Record an intermediate result.
        
        Args:
            result: The intermediate result
            description: Optional description
        """
        if not self.current_episode:
            return
        
        self.current_episode['intermediate_results'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'description': description,
            'result': result
        })
    
    def complete_episode(self, success: bool, result: Any = None, error: Optional[Dict[str, Any]] = None):
        """
        Complete the current episode and store it in memory.
        
        Args:
            success: Whether the task was successful
            result: Final result of the task
            error: Error information if failed
        """
        if not self.current_episode:
            return
        
        # Calculate duration
        duration = time.time() - self.current_episode['start_time']
        
        # Complete episode data
        self.current_episode.update({
            'success': success,
            'result': result,
            'error': error,
            'duration': duration,
            'end_time': datetime.utcnow().isoformat()
        })
        
        # Generate embedding (placeholder - would use real embedding model)
        embedding = self._generate_episode_embedding(self.current_episode)
        
        # Store in memory
        episode_id = self.team_memory.store_episode(self.current_episode, embedding)
        
        # Learn from the episode
        learnings = self.learning_system.learn_from_episode(self.current_episode)
        
        self.memory_logger.info(
            f"Completed episode {episode_id}: success={success}, "
            f"duration={duration:.1f}s, learnings={len(learnings)}"
        )
        
        # Reset current episode
        self.current_episode = None
    
    def _recall_relevant_experiences(self, task_description: str):
        """Recall relevant past experiences for the current task."""
        # Generate query embedding (placeholder)
        query_embedding = self._generate_text_embedding(task_description)
        
        # Recall similar episodes
        similar_episodes = self.team_memory.recall_similar_episodes(query_embedding, limit=3)
        
        if similar_episodes:
            self.memory_logger.info(f"Recalled {len(similar_episodes)} similar past episodes")
            
            # Extract useful patterns
            for episode in similar_episodes:
                if episode.get('success'):
                    self.memory_logger.info(
                        f"Similar successful approach: {episode.get('task_description')[:100]}... "
                        f"(similarity: {episode.get('similarity_score', 0):.2f})"
                    )
                    
                    # Log key actions that led to success
                    key_actions = []
                    for action in episode.get('actions', [])[:3]:
                        key_actions.append(action.get('action', ''))
                    
                    if key_actions:
                        self.memory_logger.info(f"Key actions: {', '.join(key_actions)}")
    
    def _apply_learned_strategies(self, task_description: str):
        """Apply learned strategies to the current task."""
        task_type = self.learning_system._categorize_task(task_description)
        strategy = self.learning_system.synthesize_strategy(task_type)
        
        if strategy and strategy['confidence'] > 0.7:
            self.memory_logger.info(
                f"Applying learned strategy for {task_type} tasks "
                f"(confidence: {strategy['confidence']:.2f})"
            )
            
            # Store strategy in context for agent to use
            if hasattr(self, 'context'):
                self.context['learned_strategy'] = strategy
            
            # Log key recommendations
            if strategy['key_actions']:
                self.memory_logger.info(
                    f"Recommended actions: {', '.join(strategy['key_actions'][:3])}"
                )
            
            if strategy['estimated_duration']:
                self.memory_logger.info(
                    f"Estimated duration: {strategy['estimated_duration']}s"
                )
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights for this agent."""
        metrics = self.team_memory.get_performance_metrics(days_back=30)
        recommendations = self.learning_system.recommend_improvements()
        
        insights = {
            'metrics': metrics,
            'recommendations': recommendations,
            'recent_learnings': self.team_memory.get_relevant_learnings({
                'agent': getattr(self, 'role', 'unknown')
            })[:5]
        }
        
        return insights
    
    def share_knowledge(self, insight: str, context: Dict[str, Any], confidence: float = 0.8):
        """
        Share a specific insight with the team.
        
        Args:
            insight: The insight to share
            context: Context in which this insight applies
            confidence: Confidence level (0-1)
        """
        learning = {
            'insight': insight,
            'context': context,
            'evidence': [self.current_episode['id']] if self.current_episode else [],
            'confidence': confidence,
            'shared_by': getattr(self, 'role', 'unknown')
        }
        
        learning_id = self.team_memory.store_learning(learning)
        self.memory_logger.info(f"Shared knowledge: {insight} (id: {learning_id})")
    
    def _generate_episode_embedding(self, episode: Dict[str, Any]) -> List[float]:
        """Generate embedding for an episode (placeholder)."""
        # In production, this would use a real embedding model
        # For now, return a mock embedding
        import hashlib
        text = json.dumps(episode, sort_keys=True)
        hash_obj = hashlib.sha256(text.encode())
        # Generate deterministic floats from hash
        embedding = []
        for i in range(192):  # 1536 / 8
            byte_slice = hash_obj.digest()[i % 32:(i % 32) + 1]
            value = int.from_bytes(byte_slice, 'big') / 255.0
            for _ in range(8):
                embedding.append(value)
        return embedding
    
    def _generate_text_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (placeholder)."""
        # In production, this would use a real embedding model
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        embedding = []
        for i in range(192):
            byte_slice = hash_obj.digest()[i % 32:(i % 32) + 1]
            value = int.from_bytes(byte_slice, 'big') / 255.0
            for _ in range(8):
                embedding.append(value)
        return embedding


def with_memory(func: Callable) -> Callable:
    """
    Decorator to automatically track episodes for agent methods.
    
    Usage:
        @with_memory
        def execute_task(self, task_description: str):
            # Task implementation
            return result
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if this is a MemoryAgentMixin instance
        if not hasattr(self, 'start_episode'):
            return func(self, *args, **kwargs)
        
        # Extract task description from args/kwargs
        task_description = None
        if args:
            task_description = str(args[0])
        elif 'task' in kwargs:
            task_description = str(kwargs['task'])
        elif 'task_description' in kwargs:
            task_description = str(kwargs['task_description'])
        else:
            task_description = func.__name__
        
        # Start episode
        self.start_episode(task_description)
        
        try:
            # Execute the function
            result = func(self, *args, **kwargs)
            
            # Complete episode successfully
            self.complete_episode(success=True, result=result)
            
            return result
            
        except Exception as e:
            # Complete episode with error
            error_info = {
                'type': type(e).__name__,
                'message': str(e)
            }
            self.complete_episode(success=False, error=error_info)
            raise
    
    return wrapper