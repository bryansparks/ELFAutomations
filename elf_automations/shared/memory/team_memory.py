"""
Team Memory System - Provides memory and learning capabilities for all teams

This module integrates with both Qdrant (vector storage) and Supabase (structured storage)
to provide teams with:
- Short-term working memory
- Long-term knowledge storage
- Experience replay and learning
- Pattern recognition and improvement
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
import hashlib

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning("Qdrant client not available. Using mock implementation.")

from ..utils.supabase_client import get_supabase_client


class TeamMemory:
    """
    Memory system for AI teams providing both vector and structured storage.
    
    Features:
    - Episode memory: Store complete task executions
    - Semantic search: Find similar past experiences
    - Pattern learning: Identify successful strategies
    - Performance tracking: Monitor improvement over time
    - Knowledge sharing: Share learnings between team members
    """
    
    def __init__(self, team_name: str, qdrant_url: str = "http://localhost:6333", 
                 collection_name: Optional[str] = None):
        """
        Initialize team memory system.
        
        Args:
            team_name: Name of the team
            qdrant_url: URL of Qdrant service
            collection_name: Optional custom collection name
        """
        self.team_name = team_name
        self.collection_name = collection_name or f"{team_name}_memories"
        self.logger = logging.getLogger(f"TeamMemory.{team_name}")
        
        # Initialize Qdrant for vector storage
        if QDRANT_AVAILABLE:
            try:
                self.qdrant = QdrantClient(url=qdrant_url)
                self._ensure_collection()
                self.logger.info(f"Connected to Qdrant at {qdrant_url}")
            except Exception as e:
                self.logger.error(f"Failed to connect to Qdrant: {e}")
                self.qdrant = None
        else:
            from .mock_qdrant import MockQdrantClient
            self.qdrant = MockQdrantClient()
            self.logger.info("Using mock Qdrant client")
        
        # Initialize Supabase for structured storage
        try:
            self.supabase = get_supabase_client()
            self.logger.info("Connected to Supabase")
        except Exception as e:
            self.logger.error(f"Failed to connect to Supabase: {e}")
            self.supabase = None
    
    def _ensure_collection(self):
        """Ensure the Qdrant collection exists."""
        if not self.qdrant:
            return
            
        try:
            collections = self.qdrant.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
                self.logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to ensure collection: {e}")
    
    def store_episode(self, episode: Dict[str, Any], embedding: List[float]) -> str:
        """
        Store a complete task episode in memory.
        
        Args:
            episode: Complete episode data including:
                - task_description: What was requested
                - context: Initial context
                - actions: List of actions taken
                - result: Final outcome
                - success: Boolean success indicator
                - duration: Time taken
                - agent_contributions: Who did what
            embedding: Vector embedding of the episode
            
        Returns:
            Episode ID
        """
        episode_id = str(uuid4())
        timestamp = datetime.utcnow()
        
        # Add metadata
        episode['id'] = episode_id
        episode['team_name'] = self.team_name
        episode['timestamp'] = timestamp.isoformat()
        
        # Store in Qdrant (vector storage)
        if self.qdrant:
            try:
                self.qdrant.upsert(
                    collection_name=self.collection_name,
                    points=[
                        PointStruct(
                            id=episode_id,
                            vector=embedding,
                            payload=episode
                        )
                    ]
                )
                self.logger.info(f"Stored episode {episode_id} in Qdrant")
            except Exception as e:
                self.logger.error(f"Failed to store in Qdrant: {e}")
        
        # Store in Supabase (structured storage)
        if self.supabase:
            try:
                # Get team_id from team name
                team_result = self.supabase.table('teams').select('id').eq('name', self.team_name).execute()
                team_id = team_result.data[0]['id'] if team_result.data else None
                
                self.supabase.table('memory_entries').insert({
                    'id': episode_id,
                    'team_id': team_id,
                    'agent_name': episode.get('primary_agent', 'team'),
                    'entry_type': 'experience',
                    'title': episode.get('task_description', '')[:500],
                    'content': json.dumps({
                        'task_description': episode.get('task_description'),
                        'success': episode.get('success', False),
                        'duration': episode.get('duration'),
                        'result': episode.get('result', {}),
                        'agent_contributions': episode.get('agent_contributions', {}),
                        'actions': episode.get('actions', [])
                    }),
                    'context': episode.get('context', {}),
                    'tags': self._extract_tags(episode),
                    'vector_id': episode_id,
                    'collection_name': self.collection_name,
                    'importance_score': 0.8 if episode.get('success') else 0.5,
                    'created_at': timestamp.isoformat()
                }).execute()
                self.logger.info(f"Stored episode {episode_id} in Supabase")
            except Exception as e:
                self.logger.error(f"Failed to store in Supabase: {e}")
        
        return episode_id
    
    def _extract_tags(self, episode: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from an episode."""
        tags = []
        
        # Add success/failure tag
        tags.append('success' if episode.get('success') else 'failure')
        
        # Extract task type
        task_desc = episode.get('task_description', '').lower()
        if 'create' in task_desc:
            tags.append('creation')
        if 'fix' in task_desc or 'debug' in task_desc:
            tags.append('debugging')
        if 'analyze' in task_desc:
            tags.append('analysis')
        if 'deploy' in task_desc:
            tags.append('deployment')
        
        # Add participating agents as tags
        for agent in episode.get('agent_contributions', {}).keys():
            tags.append(f'agent:{agent}')
        
        return tags
    
    def recall_similar_episodes(self, query_embedding: List[float], 
                              limit: int = 5, 
                              min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Recall similar past episodes based on semantic similarity.
        
        Args:
            query_embedding: Embedding of current task
            limit: Maximum number of episodes to return
            min_score: Minimum similarity score
            
        Returns:
            List of similar episodes with scores
        """
        if not self.qdrant:
            return []
        
        try:
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=min_score
            )
            
            episodes = []
            for result in results:
                episode = result.payload.copy()
                episode['similarity_score'] = result.score
                episodes.append(episode)
            
            self.logger.info(f"Recalled {len(episodes)} similar episodes")
            return episodes
            
        except Exception as e:
            self.logger.error(f"Failed to recall episodes: {e}")
            return []
    
    def get_successful_patterns(self, task_type: Optional[str] = None, 
                              days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Identify patterns from successful past episodes.
        
        Args:
            task_type: Optional filter by task type
            days_back: How many days of history to analyze
            
        Returns:
            List of successful patterns with statistics
        """
        if not self.supabase:
            return []
        
        try:
            since_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            
            # Get team_id
            team_result = self.supabase.table('teams').select('id').eq('name', self.team_name).execute()
            team_id = team_result.data[0]['id'] if team_result.data else None
            
            if not team_id:
                return []
            
            # Query successful episodes
            query = self.supabase.table('memory_entries').select('*').eq(
                'team_id', team_id
            ).eq('entry_type', 'experience').contains('tags', ['success']).gte('created_at', since_date)
            
            if task_type:
                query = query.ilike('title', f'%{task_type}%')
            
            result = query.execute()
            episodes = []
            
            # Parse content JSON
            for entry in result.data:
                content = json.loads(entry['content'])
                episodes.append({
                    'id': entry['id'],
                    'task_description': content.get('task_description'),
                    'success': content.get('success'),
                    'duration_seconds': content.get('duration'),
                    'agent_contributions': content.get('agent_contributions', {})
                })
            
            # Analyze patterns
            patterns = self._analyze_patterns(episodes)
            
            self.logger.info(f"Identified {len(patterns)} successful patterns")
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to get patterns: {e}")
            return []
    
    def _analyze_patterns(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze episodes to identify common successful patterns."""
        patterns = {}
        
        for episode in episodes:
            # Extract agent contributions
            contributions = json.loads(episode.get('agent_contributions', '{}'))
            
            for agent, actions in contributions.items():
                if agent not in patterns:
                    patterns[agent] = {
                        'agent': agent,
                        'successful_actions': {},
                        'total_successes': 0
                    }
                
                patterns[agent]['total_successes'] += 1
                
                # Count action frequencies
                for action in actions:
                    action_key = self._normalize_action(action)
                    if action_key not in patterns[agent]['successful_actions']:
                        patterns[agent]['successful_actions'][action_key] = 0
                    patterns[agent]['successful_actions'][action_key] += 1
        
        # Convert to list and sort by effectiveness
        pattern_list = []
        for agent, data in patterns.items():
            # Get top actions
            top_actions = sorted(
                data['successful_actions'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            pattern_list.append({
                'agent': agent,
                'total_successes': data['total_successes'],
                'top_actions': [
                    {'action': action, 'frequency': freq}
                    for action, freq in top_actions
                ]
            })
        
        return sorted(pattern_list, key=lambda x: x['total_successes'], reverse=True)
    
    def _normalize_action(self, action: str) -> str:
        """Normalize action descriptions for pattern matching."""
        # Simple normalization - can be enhanced
        return action.lower().strip()
    
    def store_learning(self, learning: Dict[str, Any]) -> str:
        """
        Store a specific learning or insight.
        
        Args:
            learning: Learning data including:
                - insight: Key insight learned
                - context: When this applies
                - evidence: Supporting episodes
                - confidence: Confidence level
                
        Returns:
            Learning ID
        """
        learning_id = str(uuid4())
        timestamp = datetime.utcnow()
        
        if self.supabase:
            try:
                # Get team_id
                team_result = self.supabase.table('teams').select('id').eq('name', self.team_name).execute()
                team_id = team_result.data[0]['id'] if team_result.data else None
                
                # Determine pattern type
                pattern_type = 'insight'
                if 'success' in learning.get('insight', '').lower():
                    pattern_type = 'success'
                elif 'fail' in learning.get('insight', '').lower():
                    pattern_type = 'failure'
                elif 'optim' in learning.get('insight', '').lower():
                    pattern_type = 'optimization'
                
                self.supabase.table('learning_patterns').insert({
                    'id': learning_id,
                    'pattern_type': pattern_type,
                    'category': learning.get('context', {}).get('task_type', 'general'),
                    'title': learning.get('insight', '')[:500],
                    'description': learning.get('description', ''),
                    'conditions': learning.get('context', {}),
                    'actions': learning.get('actions', {}),
                    'outcomes': learning.get('outcomes', {'learned': True}),
                    'recommendations': learning.get('recommendations', {}),
                    'confidence_score': learning.get('confidence', 0.5),
                    'supporting_memories': learning.get('evidence', []),
                    'discovered_by_team': team_id,
                    'created_at': timestamp.isoformat()
                }).execute()
                
                self.logger.info(f"Stored learning {learning_id}")
            except Exception as e:
                self.logger.error(f"Failed to store learning: {e}")
        
        return learning_id
    
    def get_relevant_learnings(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve learnings relevant to current context.
        
        Args:
            context: Current task context
            
        Returns:
            List of relevant learnings
        """
        if not self.supabase:
            return []
        
        try:
            # Get team_id
            team_result = self.supabase.table('teams').select('id').eq('name', self.team_name).execute()
            team_id = team_result.data[0]['id'] if team_result.data else None
            
            if not team_id:
                return []
            
            # For now, simple retrieval - can be enhanced with semantic search
            result = self.supabase.table('learning_patterns').select('*').eq(
                'discovered_by_team', team_id
            ).gte('confidence_score', 0.7).execute()
            
            learnings = result.data
            
            # Filter by context relevance (simple keyword matching for now)
            relevant = []
            context_str = json.dumps(context).lower()
            
            for learning in learnings:
                learning_context = json.dumps(learning.get('context', {})).lower()
                # Check for context overlap
                if any(word in context_str for word in learning_context.split()):
                    relevant.append(learning)
            
            self.logger.info(f"Found {len(relevant)} relevant learnings")
            return relevant
            
        except Exception as e:
            self.logger.error(f"Failed to get learnings: {e}")
            return []
    
    def consolidate_memories(self, older_than_days: int = 90):
        """
        Consolidate old memories into compressed learnings.
        
        Args:
            older_than_days: Consolidate memories older than this
        """
        if not self.supabase:
            return
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=older_than_days)).isoformat()
            
            # Get team_id
            team_result = self.supabase.table('teams').select('id').eq('name', self.team_name).execute()
            team_id = team_result.data[0]['id'] if team_result.data else None
            
            if not team_id:
                return
            
            # Get old episodes
            result = self.supabase.table('memory_entries').select('*').eq(
                'team_id', team_id
            ).eq('entry_type', 'experience').lt('created_at', cutoff_date).execute()
            
            old_episodes = result.data
            
            if not old_episodes:
                return
            
            # Group by task type and analyze
            task_groups = {}
            for entry in old_episodes:
                content = json.loads(entry['content'])
                task_type = self._extract_task_type(content.get('task_description', ''))
                if task_type not in task_groups:
                    task_groups[task_type] = []
                task_groups[task_type].append({
                    'id': entry['id'],
                    'success': content.get('success', False),
                    'task_description': content.get('task_description', '')
                })
            
            # Create consolidated learnings
            for task_type, episodes in task_groups.items():
                success_rate = sum(1 for e in episodes if e['success']) / len(episodes)
                
                if success_rate > 0.7:  # High success rate
                    patterns = self._analyze_patterns(
                        [e for e in episodes if e['success']]
                    )
                    
                    learning = {
                        'insight': f"Effective approach for {task_type} tasks",
                        'context': {'task_type': task_type},
                        'evidence': [e['id'] for e in episodes[:5]],  # Sample IDs
                        'confidence': success_rate
                    }
                    
                    self.store_learning(learning)
            
            self.logger.info(f"Consolidated {len(old_episodes)} old memories")
            
        except Exception as e:
            self.logger.error(f"Failed to consolidate memories: {e}")
    
    def _extract_task_type(self, task_description: str) -> str:
        """Extract task type from description."""
        # Simple extraction - can be enhanced
        words = task_description.lower().split()
        if 'create' in words:
            return 'creation'
        elif 'analyze' in words:
            return 'analysis'
        elif 'fix' in words or 'debug' in words:
            return 'debugging'
        elif 'design' in words:
            return 'design'
        else:
            return 'general'
    
    def get_performance_metrics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get team performance metrics over time.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Performance metrics including trends
        """
        if not self.supabase:
            return {}
        
        try:
            since_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            
            # Get team_id
            team_result = self.supabase.table('teams').select('id').eq('name', self.team_name).execute()
            team_id = team_result.data[0]['id'] if team_result.data else None
            
            if not team_id:
                return {}
            
            result = self.supabase.table('memory_entries').select('*').eq(
                'team_id', team_id
            ).eq('entry_type', 'experience').gte('created_at', since_date).execute()
            
            episodes = result.data
            
            if not episodes:
                return {}
            
            # Parse episodes and calculate metrics
            parsed_episodes = []
            for entry in episodes:
                content = json.loads(entry['content'])
                parsed_episodes.append({
                    'success': content.get('success', False),
                    'duration_seconds': content.get('duration', 0),
                    'created_at': entry['created_at']
                })
            
            total = len(parsed_episodes)
            successful = sum(1 for e in parsed_episodes if e['success'])
            
            # Average duration
            durations = [e['duration_seconds'] for e in parsed_episodes if e['duration_seconds']]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Success rate by week
            weekly_stats = {}
            for episode in parsed_episodes:
                week = datetime.fromisoformat(
                    episode['created_at'].replace('Z', '+00:00')
                ).isocalendar()[1]
                
                if week not in weekly_stats:
                    weekly_stats[week] = {'total': 0, 'successful': 0}
                
                weekly_stats[week]['total'] += 1
                if episode['success']:
                    weekly_stats[week]['successful'] += 1
            
            # Calculate trend
            weeks = sorted(weekly_stats.keys())
            if len(weeks) > 1:
                early_success_rate = (
                    weekly_stats[weeks[0]]['successful'] / 
                    weekly_stats[weeks[0]]['total']
                )
                recent_success_rate = (
                    weekly_stats[weeks[-1]]['successful'] / 
                    weekly_stats[weeks[-1]]['total']
                )
                improvement = recent_success_rate - early_success_rate
            else:
                improvement = 0
            
            metrics = {
                'total_episodes': total,
                'success_rate': successful / total if total > 0 else 0,
                'average_duration_seconds': avg_duration,
                'improvement_trend': improvement,
                'weekly_performance': weekly_stats
            }
            
            self.logger.info(f"Calculated performance metrics: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return {}