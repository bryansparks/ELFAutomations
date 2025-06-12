"""
Evolved Agent Loader - Integrates prompt evolution into agent initialization

This module provides the bridge between the prompt evolution system and
agent creation, ensuring agents start with their evolved capabilities.
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

from supabase import Client

from .prompt_evolution import PromptEvolution
from ..utils.logging import get_logger
from ..utils.llm_factory import LLMFactory

logger = get_logger(__name__)


@dataclass
class EvolvedAgentConfig:
    """Configuration for an evolved agent."""
    role: str
    base_prompt: str
    evolved_prompt: str
    evolution_confidence: float
    personality_traits: Dict[str, Any]
    learned_strategies: list
    workflow_modifications: Dict[str, Any]
    tool_preferences: list


class EvolvedAgentLoader:
    """Loads agents with their evolved configurations."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.prompt_evolution = PromptEvolution(supabase_client)
    
    def load_evolved_agent_config(
        self,
        team_id: str,
        agent_role: str,
        base_config: Dict[str, Any],
        task_type: Optional[str] = None
    ) -> EvolvedAgentConfig:
        """
        Load an evolved configuration for an agent.
        
        Args:
            team_id: The team ID
            agent_role: The agent's role
            base_config: Base configuration including prompt, traits, etc.
            task_type: Optional task type for context
            
        Returns:
            EvolvedAgentConfig with all enhancements applied
        """
        # Extract base components
        base_prompt = base_config.get('backstory', '')
        personality_traits = base_config.get('personality_traits', {})
        
        # Get evolved prompt
        evolved_prompt = self.prompt_evolution.get_evolved_prompt(
            team_id=team_id,
            agent_role=agent_role,
            base_prompt=base_prompt,
            task_type=task_type
        )
        
        # Get evolved personality traits
        evolved_traits = self._evolve_personality_traits(
            team_id, agent_role, personality_traits
        )
        
        # Get learned strategies
        strategies = self._get_agent_strategies(team_id, agent_role)
        
        # Get workflow modifications
        workflow_mods = self._get_workflow_modifications(team_id, agent_role)
        
        # Get tool preferences based on success rates
        tool_prefs = self._get_tool_preferences(team_id, agent_role)
        
        # Calculate overall evolution confidence
        confidence = self._calculate_evolution_confidence(
            evolved_prompt != base_prompt,
            evolved_traits != personality_traits,
            bool(strategies),
            bool(workflow_mods)
        )
        
        return EvolvedAgentConfig(
            role=agent_role,
            base_prompt=base_prompt,
            evolved_prompt=evolved_prompt,
            evolution_confidence=confidence,
            personality_traits=evolved_traits,
            learned_strategies=strategies,
            workflow_modifications=workflow_mods,
            tool_preferences=tool_prefs
        )
    
    def _evolve_personality_traits(
        self,
        team_id: str,
        agent_role: str,
        base_traits: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evolve personality traits based on successful patterns."""
        evolved_traits = base_traits.copy()
        
        try:
            # Query for trait-related learnings
            result = self.supabase.table('team_learnings').select(
                'pattern, context, success_rate'
            ).eq(
                'team_id', team_id
            ).contains(
                'context', {'role': agent_role, 'trait_impact': True}
            ).gte(
                'confidence_score', 0.85
            ).execute()
            
            if result.data:
                for learning in result.data:
                    context = learning.get('context', {})
                    trait_name = context.get('trait_name')
                    trait_modifier = context.get('trait_modifier')
                    
                    if trait_name and trait_modifier:
                        # Apply trait evolution
                        if trait_name not in evolved_traits:
                            evolved_traits[trait_name] = trait_modifier
                            logger.info(f"Added evolved trait '{trait_name}' to {agent_role}")
                        else:
                            # Enhance existing trait
                            evolved_traits[trait_name] = self._merge_trait_modifiers(
                                evolved_traits[trait_name], trait_modifier
                            )
            
            # Add success-based trait adjustments
            if 'skeptic' in evolved_traits:
                # If skeptic trait has led to catching many issues
                issue_catch_rate = self._get_metric(team_id, agent_role, 'issue_catch_rate')
                if issue_catch_rate > 0.8:
                    evolved_traits['skeptic'] = evolved_traits.get('skeptic', '') + \
                        "\nFocus especially on edge cases and error conditions (80%+ issue catch rate)."
            
            return evolved_traits
            
        except Exception as e:
            logger.error(f"Error evolving personality traits: {e}")
            return base_traits
    
    def _get_agent_strategies(
        self,
        team_id: str,
        agent_role: str
    ) -> list:
        """Get proven strategies for this agent."""
        try:
            result = self.supabase.table('team_learnings').select(
                'pattern, context, success_rate, usage_count'
            ).eq(
                'team_id', team_id
            ).contains(
                'context', {'role': agent_role}
            ).gte(
                'success_rate', 0.85
            ).order(
                'success_rate', desc=True
            ).limit(10).execute()
            
            strategies = []
            if result.data:
                for learning in result.data:
                    strategy = {
                        'pattern': learning['pattern'],
                        'success_rate': learning['success_rate'],
                        'usage_count': learning['usage_count'],
                        'context': learning.get('context', {})
                    }
                    strategies.append(strategy)
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting agent strategies: {e}")
            return []
    
    def _get_workflow_modifications(
        self,
        team_id: str,
        agent_role: str
    ) -> Dict[str, Any]:
        """Get workflow modifications for this agent."""
        try:
            # Check for workflow evolutions
            result = self.supabase.table('agent_evolutions').select(
                'evolved_version'
            ).eq(
                'team_id', team_id
            ).eq(
                'agent_role', agent_role
            ).eq(
                'evolution_type', 'workflow'
            ).order(
                'created_at', desc=True
            ).limit(1).execute()
            
            if result.data:
                import json
                return json.loads(result.data[0]['evolved_version'])
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting workflow modifications: {e}")
            return {}
    
    def _get_tool_preferences(
        self,
        team_id: str,
        agent_role: str
    ) -> list:
        """Get tool preferences based on success rates."""
        try:
            # Query tool usage patterns
            result = self.supabase.table('team_learnings').select(
                'pattern, context, success_rate'
            ).eq(
                'team_id', team_id
            ).contains(
                'context', {'role': agent_role, 'tool_usage': True}
            ).gte(
                'success_rate', 0.8
            ).order(
                'success_rate', desc=True
            ).execute()
            
            tool_prefs = []
            if result.data:
                for learning in result.data:
                    tool_name = learning.get('context', {}).get('tool_name')
                    if tool_name:
                        tool_prefs.append({
                            'tool': tool_name,
                            'success_rate': learning['success_rate'],
                            'preferred_for': learning.get('context', {}).get('task_types', [])
                        })
            
            return tool_prefs
            
        except Exception as e:
            logger.error(f"Error getting tool preferences: {e}")
            return []
    
    def _merge_trait_modifiers(self, existing: str, new: str) -> str:
        """Merge trait modifiers intelligently."""
        if not existing:
            return new
        if not new:
            return existing
        
        # Combine without duplication
        if new in existing:
            return existing
        
        return f"{existing}\n{new}"
    
    def _get_metric(
        self,
        team_id: str,
        agent_role: str,
        metric_name: str
    ) -> float:
        """Get a specific metric for an agent."""
        try:
            # This would query actual metrics from the memory system
            # For now, return a placeholder
            return 0.0
        except Exception as e:
            logger.error(f"Error getting metric: {e}")
            return 0.0
    
    def _calculate_evolution_confidence(
        self,
        has_evolved_prompt: bool,
        has_evolved_traits: bool,
        has_strategies: bool,
        has_workflow_mods: bool
    ) -> float:
        """Calculate overall evolution confidence."""
        factors = [
            has_evolved_prompt,
            has_evolved_traits,
            has_strategies,
            has_workflow_mods
        ]
        
        return sum(factors) / len(factors)
    
    def apply_evolution_to_agent(
        self,
        agent: Any,
        evolved_config: EvolvedAgentConfig
    ) -> Any:
        """
        Apply evolved configuration to an agent instance.
        
        Args:
            agent: The base agent instance
            evolved_config: The evolved configuration
            
        Returns:
            The evolved agent
        """
        # Update backstory/prompt
        if hasattr(agent, 'backstory'):
            agent.backstory = evolved_config.evolved_prompt
        
        # Apply learned strategies as additional context
        if evolved_config.learned_strategies:
            strategy_context = self._format_strategies_for_agent(
                evolved_config.learned_strategies
            )
            if hasattr(agent, 'context'):
                agent.context = agent.context or {}
                agent.context['learned_strategies'] = strategy_context
        
        # Apply tool preferences
        if evolved_config.tool_preferences and hasattr(agent, 'tools'):
            agent.tools = self._reorder_tools_by_preference(
                agent.tools,
                evolved_config.tool_preferences
            )
        
        logger.info(
            f"Applied evolution to {evolved_config.role} "
            f"(confidence: {evolved_config.evolution_confidence:.2f})"
        )
        
        return agent
    
    def _format_strategies_for_agent(self, strategies: list) -> str:
        """Format strategies for agent context."""
        if not strategies:
            return ""
        
        formatted = "Proven strategies from experience:\n"
        for i, strategy in enumerate(strategies[:5], 1):
            formatted += f"{i}. {strategy['pattern']} ({strategy['success_rate']:.0%} success)\n"
        
        return formatted
    
    def _reorder_tools_by_preference(
        self,
        tools: list,
        preferences: list
    ) -> list:
        """Reorder tools based on preferences."""
        if not preferences:
            return tools
        
        # Create preference map
        pref_map = {pref['tool']: pref['success_rate'] for pref in preferences}
        
        # Sort tools by preference
        def tool_score(tool):
            tool_name = getattr(tool, 'name', str(tool))
            return pref_map.get(tool_name, 0.5)
        
        return sorted(tools, key=tool_score, reverse=True)