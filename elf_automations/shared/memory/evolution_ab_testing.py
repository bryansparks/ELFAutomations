"""
A/B Testing Framework for Agent Evolution

This module provides controlled testing of evolved agents vs base agents
to measure the impact of prompt and behavioral evolutions.
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4
from dataclasses import dataclass

from supabase import Client

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ABTestResult:
    """Results from an A/B test."""
    test_id: str
    control_group: str  # Base agent
    treatment_group: str  # Evolved agent
    control_metrics: Dict[str, float]
    treatment_metrics: Dict[str, float]
    statistical_significance: float
    recommendation: str
    confidence_level: float


class EvolutionABTesting:
    """Manages A/B testing for agent evolutions."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure A/B testing tables exist."""
        # Table creation handled by SQL migrations
        pass
    
    def create_ab_test(
        self,
        team_id: str,
        agent_role: str,
        evolution_id: str,
        test_duration_hours: int = 48,
        traffic_split: float = 0.5
    ) -> str:
        """
        Create a new A/B test for an agent evolution.
        
        Args:
            team_id: The team ID
            agent_role: The agent role being tested
            evolution_id: The evolution to test
            test_duration_hours: How long to run the test
            traffic_split: Percentage of traffic for treatment group (0-1)
            
        Returns:
            Test ID
        """
        test_id = str(uuid4())
        
        try:
            # Get the evolution details
            evolution = self._get_evolution(evolution_id)
            if not evolution:
                raise ValueError(f"Evolution {evolution_id} not found")
            
            # Create test record
            test_data = {
                'id': test_id,
                'team_id': team_id,
                'agent_role': agent_role,
                'evolution_id': evolution_id,
                'status': 'active',
                'traffic_split': traffic_split,
                'start_time': datetime.utcnow().isoformat(),
                'end_time': (datetime.utcnow() + timedelta(hours=test_duration_hours)).isoformat(),
                'control_config': evolution['original_version'],
                'treatment_config': evolution['evolved_version'],
                'metrics': {
                    'control': {'requests': 0, 'successes': 0, 'errors': 0, 'duration_sum': 0},
                    'treatment': {'requests': 0, 'successes': 0, 'errors': 0, 'duration_sum': 0}
                }
            }
            
            self.supabase.table('ab_tests').insert(test_data).execute()
            
            logger.info(f"Created A/B test {test_id} for {agent_role} evolution")
            return test_id
            
        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            raise
    
    def should_use_treatment(self, test_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if a request should use the treatment (evolved) version.
        
        Args:
            test_id: The test ID
            
        Returns:
            Tuple of (use_treatment, test_config)
        """
        try:
            # Get test configuration
            result = self.supabase.table('ab_tests').select('*').eq(
                'id', test_id
            ).eq('status', 'active').execute()
            
            if not result.data:
                return False, {}
            
            test = result.data[0]
            
            # Check if test is still active
            if datetime.fromisoformat(test['end_time']) < datetime.utcnow():
                # Test has ended, finalize it
                self._finalize_test(test_id)
                return False, {}
            
            # Random assignment based on traffic split
            use_treatment = random.random() < test['traffic_split']
            
            return use_treatment, {
                'test_id': test_id,
                'group': 'treatment' if use_treatment else 'control',
                'config': test['treatment_config'] if use_treatment else test['control_config']
            }
            
        except Exception as e:
            logger.error(f"Error in A/B test assignment: {e}")
            return False, {}
    
    def record_test_result(
        self,
        test_id: str,
        group: str,
        success: bool,
        duration_seconds: float,
        error: Optional[str] = None
    ):
        """
        Record the result of a test execution.
        
        Args:
            test_id: The test ID
            group: 'control' or 'treatment'
            success: Whether the task succeeded
            duration_seconds: Task duration
            error: Error message if failed
        """
        try:
            # Get current test
            result = self.supabase.table('ab_tests').select('metrics').eq(
                'id', test_id
            ).execute()
            
            if not result.data:
                logger.error(f"Test {test_id} not found")
                return
            
            metrics = result.data[0]['metrics']
            
            # Update metrics
            group_metrics = metrics[group]
            group_metrics['requests'] += 1
            if success:
                group_metrics['successes'] += 1
            else:
                group_metrics['errors'] += 1
            group_metrics['duration_sum'] += duration_seconds
            
            # Save updated metrics
            self.supabase.table('ab_tests').update({
                'metrics': metrics,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', test_id).execute()
            
            # Also record individual result for detailed analysis
            self.supabase.table('ab_test_results').insert({
                'id': str(uuid4()),
                'test_id': test_id,
                'group_name': group,
                'success': success,
                'duration_seconds': duration_seconds,
                'error': error,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Failed to record test result: {e}")
    
    def get_test_results(self, test_id: str) -> ABTestResult:
        """
        Get current results of an A/B test.
        
        Args:
            test_id: The test ID
            
        Returns:
            ABTestResult with metrics and recommendation
        """
        try:
            # Get test data
            result = self.supabase.table('ab_tests').select('*').eq(
                'id', test_id
            ).execute()
            
            if not result.data:
                raise ValueError(f"Test {test_id} not found")
            
            test = result.data[0]
            metrics = test['metrics']
            
            # Calculate success rates
            control_metrics = self._calculate_metrics(metrics['control'])
            treatment_metrics = self._calculate_metrics(metrics['treatment'])
            
            # Calculate statistical significance
            significance = self._calculate_significance(
                control_metrics, treatment_metrics
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                control_metrics, treatment_metrics, significance
            )
            
            return ABTestResult(
                test_id=test_id,
                control_group='base_agent',
                treatment_group='evolved_agent',
                control_metrics=control_metrics,
                treatment_metrics=treatment_metrics,
                statistical_significance=significance,
                recommendation=recommendation,
                confidence_level=self._calculate_confidence(metrics)
            )
            
        except Exception as e:
            logger.error(f"Failed to get test results: {e}")
            raise
    
    def _calculate_metrics(self, group_data: Dict) -> Dict[str, float]:
        """Calculate metrics from raw group data."""
        requests = group_data['requests']
        if requests == 0:
            return {
                'success_rate': 0.0,
                'error_rate': 0.0,
                'avg_duration': 0.0,
                'sample_size': 0
            }
        
        return {
            'success_rate': group_data['successes'] / requests,
            'error_rate': group_data['errors'] / requests,
            'avg_duration': group_data['duration_sum'] / requests,
            'sample_size': requests
        }
    
    def _calculate_significance(
        self,
        control: Dict[str, float],
        treatment: Dict[str, float]
    ) -> float:
        """
        Calculate statistical significance using z-test for proportions.
        
        Returns significance level (0-1, where >0.95 is significant)
        """
        n1 = control['sample_size']
        n2 = treatment['sample_size']
        
        if n1 < 30 or n2 < 30:
            # Not enough samples
            return 0.0
        
        p1 = control['success_rate']
        p2 = treatment['success_rate']
        
        # Pooled proportion
        p_pool = ((p1 * n1) + (p2 * n2)) / (n1 + n2)
        
        # Standard error
        se = (p_pool * (1 - p_pool) * (1/n1 + 1/n2)) ** 0.5
        
        if se == 0:
            return 0.0
        
        # Z-score
        z = (p2 - p1) / se
        
        # Convert to significance (simplified)
        # In real implementation, use scipy.stats for proper p-value
        if abs(z) > 1.96:  # 95% confidence
            return 0.95
        elif abs(z) > 1.645:  # 90% confidence
            return 0.90
        else:
            return abs(z) / 1.96 * 0.95
    
    def _generate_recommendation(
        self,
        control: Dict[str, float],
        treatment: Dict[str, float],
        significance: float
    ) -> str:
        """Generate recommendation based on test results."""
        if control['sample_size'] < 30 or treatment['sample_size'] < 30:
            return "Continue testing - insufficient data"
        
        success_diff = treatment['success_rate'] - control['success_rate']
        duration_diff = treatment['avg_duration'] - control['avg_duration']
        
        if significance < 0.90:
            return "No significant difference - continue monitoring"
        
        if success_diff > 0.05 and duration_diff < control['avg_duration'] * 0.2:
            return "Strong positive impact - recommend applying evolution"
        elif success_diff > 0.02:
            return "Moderate positive impact - consider applying evolution"
        elif success_diff < -0.05:
            return "Negative impact - do not apply evolution"
        else:
            return "Minimal impact - evolution may not be necessary"
    
    def _calculate_confidence(self, metrics: Dict) -> float:
        """Calculate confidence level based on sample size."""
        total_samples = (metrics['control']['requests'] + 
                        metrics['treatment']['requests'])
        
        if total_samples >= 1000:
            return 0.99
        elif total_samples >= 500:
            return 0.95
        elif total_samples >= 100:
            return 0.90
        elif total_samples >= 50:
            return 0.80
        else:
            return total_samples / 50 * 0.80
    
    def _finalize_test(self, test_id: str):
        """Finalize a completed test."""
        try:
            # Get final results
            results = self.get_test_results(test_id)
            
            # Update test status
            self.supabase.table('ab_tests').update({
                'status': 'completed',
                'final_recommendation': results.recommendation,
                'completed_at': datetime.utcnow().isoformat()
            }).eq('id', test_id).execute()
            
            # If evolution was successful, update its performance delta
            if 'positive impact' in results.recommendation.lower():
                test_data = self.supabase.table('ab_tests').select(
                    'evolution_id'
                ).eq('id', test_id).execute()
                
                if test_data.data:
                    evolution_id = test_data.data[0]['evolution_id']
                    performance_delta = (
                        results.treatment_metrics['success_rate'] - 
                        results.control_metrics['success_rate']
                    )
                    
                    self.supabase.table('agent_evolutions').update({
                        'performance_delta': performance_delta,
                        'applied_at': datetime.utcnow().isoformat(),
                        'test_metrics': {
                            'control': results.control_metrics,
                            'treatment': results.treatment_metrics,
                            'significance': results.statistical_significance
                        }
                    }).eq('id', evolution_id).execute()
            
            logger.info(f"Finalized A/B test {test_id}: {results.recommendation}")
            
        except Exception as e:
            logger.error(f"Failed to finalize test: {e}")
    
    def _get_evolution(self, evolution_id: str) -> Optional[Dict]:
        """Get evolution details."""
        try:
            result = self.supabase.table('agent_evolutions').select('*').eq(
                'id', evolution_id
            ).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get evolution: {e}")
            return None
    
    def get_active_tests(self, team_id: str) -> List[Dict]:
        """Get all active A/B tests for a team."""
        try:
            result = self.supabase.table('ab_tests').select('*').eq(
                'team_id', team_id
            ).eq('status', 'active').execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get active tests: {e}")
            return []