"""
Project-Aware Agent Mixin

Adds project management capabilities to agents, enabling them to:
- Find and claim appropriate work
- Track task progress
- Coordinate with other teams
- Handle dependencies and blockers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod

from ..a2a.project_messages import (
    ProjectCoordinator,
    ProgressUpdateMessage,
    BlockerReportedMessage,
    DependencyCompleteMessage,
    HelpRequestedMessage
)
from ..mcp.client import MCPClient


class ProjectAwareMixin(ABC):
    """
    Mixin that adds project management capabilities to agents.
    
    This mixin should be added to agent classes to enable autonomous
    project coordination.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Project management state
        self.current_task: Optional[Dict] = None
        self.current_project: Optional[Dict] = None
        self.task_start_time: Optional[datetime] = None
        self.work_check_interval: int = 300  # 5 minutes
        self.is_working: bool = False
        
        # MCP client for project management
        self.project_mcp: Optional[MCPClient] = None
        
        # Logger
        self.project_logger = logging.getLogger(f"{self.__class__.__name__}.ProjectAware")
    
    @abstractmethod
    def get_team_id(self) -> str:
        """Get the team ID for this agent."""
        pass
    
    @abstractmethod
    def get_team_skills(self) -> List[str]:
        """Get the skills this team possesses."""
        pass
    
    @abstractmethod
    def get_available_capacity(self) -> float:
        """Get available capacity in hours."""
        pass
    
    @abstractmethod
    async def send_a2a_message(self, message: Any) -> bool:
        """Send an A2A message to another team."""
        pass
    
    async def initialize_project_management(self, project_mcp_url: str):
        """Initialize project management capabilities."""
        try:
            self.project_mcp = MCPClient(project_mcp_url)
            await self.project_mcp.connect()
            self.project_logger.info("Project management initialized")
            
            # Start autonomous work-finding loop
            asyncio.create_task(self._autonomous_work_loop())
            
        except Exception as e:
            self.project_logger.error(f"Failed to initialize project management: {e}")
    
    async def _autonomous_work_loop(self):
        """Continuously check for and claim appropriate work."""
        while True:
            try:
                if not self.is_working and self.get_available_capacity() > 0:
                    await self.find_and_claim_work()
                
                await asyncio.sleep(self.work_check_interval)
                
            except Exception as e:
                self.project_logger.error(f"Error in work loop: {e}")
                await asyncio.sleep(60)  # Wait a minute on error
    
    async def find_and_claim_work(self) -> bool:
        """Find available work matching our skills and claim it."""
        try:
            # Find available tasks
            result = await self.project_mcp.call_tool(
                "find_available_work",
                {
                    "team_id": self.get_team_id(),
                    "skills": self.get_team_skills(),
                    "capacity_hours": self.get_available_capacity()
                }
            )
            
            if not result.get('success') or not result.get('available_tasks'):
                return False
            
            # Prioritize tasks
            tasks = result['available_tasks']
            best_task = self._select_best_task(tasks)
            
            if not best_task:
                return False
            
            # Try to claim the task
            claim_result = await self.project_mcp.call_tool(
                "assign_task",
                {
                    "task_id": best_task['id'],
                    "team_id": self.get_team_id()
                }
            )
            
            if claim_result.get('success'):
                self.current_task = best_task
                self.is_working = True
                self.task_start_time = datetime.utcnow()
                
                self.project_logger.info(
                    f"Claimed task: {best_task['title']} "
                    f"(Project: {best_task['project_name']})"
                )
                
                # Start working on the task
                asyncio.create_task(self._execute_task(best_task))
                return True
            
            return False
            
        except Exception as e:
            self.project_logger.error(f"Error finding work: {e}")
            return False
    
    def _select_best_task(self, tasks: List[Dict]) -> Optional[Dict]:
        """Select the best task based on priority, urgency, and skill match."""
        if not tasks:
            return None
        
        # Score each task
        scored_tasks = []
        for task in tasks:
            score = 0
            
            # Urgency score
            if task.get('urgency') == 'urgent':
                score += 100
            elif task.get('urgency') == 'soon':
                score += 50
            
            # Project priority score
            priority_scores = {'critical': 80, 'high': 60, 'medium': 40, 'low': 20}
            score += priority_scores.get(task.get('project_priority', 'medium'), 40)
            
            # Skill match score
            required_skills = set(task.get('required_skills', []))
            team_skills = set(self.get_team_skills())
            if required_skills:
                match_ratio = len(required_skills & team_skills) / len(required_skills)
                score += match_ratio * 50
            
            # Complexity match (prefer tasks we can handle)
            complexity_scores = {'trivial': 10, 'easy': 20, 'medium': 30, 'hard': 20, 'expert': 10}
            score += complexity_scores.get(task.get('complexity', 'medium'), 30)
            
            scored_tasks.append((score, task))
        
        # Return highest scoring task
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        return scored_tasks[0][1]
    
    async def _execute_task(self, task: Dict):
        """Execute the assigned task."""
        try:
            # Update status to in_progress
            await self.update_task_progress(
                status="in_progress",
                progress=0,
                notes=f"Starting work on {task['title']}"
            )
            
            # This is where the actual task execution would happen
            # For now, we'll simulate it
            await self._perform_task_work(task)
            
        except Exception as e:
            self.project_logger.error(f"Error executing task: {e}")
            await self.report_task_blocker(
                f"Encountered error: {str(e)}",
                severity="high"
            )
    
    @abstractmethod
    async def _perform_task_work(self, task: Dict):
        """
        Perform the actual work for a task.
        
        This should be implemented by the concrete agent class.
        """
        pass
    
    async def update_task_progress(
        self,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update progress on the current task."""
        if not self.current_task:
            return False
        
        try:
            # Calculate hours worked
            hours_worked = 0
            if self.task_start_time:
                elapsed = datetime.utcnow() - self.task_start_time
                hours_worked = elapsed.total_seconds() / 3600
            
            # Update task in project management system
            update_data = {
                "task_id": self.current_task['id'],
                "hours_worked": hours_worked
            }
            
            if status:
                update_data["status"] = status
            if progress is not None:
                update_data["progress_percentage"] = progress
            if notes:
                update_data["notes"] = notes
            
            result = await self.project_mcp.call_tool(
                "update_task_status",
                update_data
            )
            
            if result.get('success'):
                # Send progress update to project owner
                if self.current_task.get('project_id'):
                    await self._send_progress_update(status, progress, hours_worked, notes)
                
                # If task is complete, clear current task
                if status == "completed":
                    await self._handle_task_completion()
                
                return True
            
            return False
            
        except Exception as e:
            self.project_logger.error(f"Error updating progress: {e}")
            return False
    
    async def report_task_blocker(
        self,
        blocker_description: str,
        severity: str = "medium",
        needs_help_from: Optional[str] = None
    ) -> bool:
        """Report a blocker on the current task."""
        if not self.current_task:
            return False
        
        try:
            # Report blocker in project system
            result = await self.project_mcp.call_tool(
                "report_blocker",
                {
                    "task_id": self.current_task['id'],
                    "blocker_description": blocker_description,
                    "needs_help_from": needs_help_from
                }
            )
            
            if result.get('success'):
                # Notify relevant teams
                await self._send_blocker_notification(
                    blocker_description,
                    severity,
                    needs_help_from
                )
                return True
            
            return False
            
        except Exception as e:
            self.project_logger.error(f"Error reporting blocker: {e}")
            return False
    
    async def request_help(
        self,
        help_type: str,
        description: str,
        required_skills: List[str],
        urgency: str = "normal"
    ) -> bool:
        """Request help from another team."""
        if not self.current_task:
            return False
        
        try:
            # Find teams with required skills
            # This would query the team registry for matching teams
            
            # For now, send to project owner
            if self.current_task.get('project_id'):
                message = ProjectCoordinator.create_help_request(
                    task_id=self.current_task['id'],
                    project_id=self.current_task['project_id'],
                    help_type=help_type,
                    description=description,
                    required_skills=required_skills,
                    sender=self.get_team_id(),
                    recipient="project-owner",  # Would be determined dynamically
                    urgency=urgency
                )
                
                await self.send_a2a_message(message)
                return True
            
            return False
            
        except Exception as e:
            self.project_logger.error(f"Error requesting help: {e}")
            return False
    
    async def _handle_task_completion(self):
        """Handle task completion and check for dependent tasks."""
        try:
            # Check if any tasks were waiting for this one
            # This would query for dependent tasks and notify their owners
            
            # Clear current task
            completed_task = self.current_task
            self.current_task = None
            self.is_working = False
            self.task_start_time = None
            
            self.project_logger.info(f"Completed task: {completed_task['title']}")
            
            # Look for next task immediately
            await self.find_and_claim_work()
            
        except Exception as e:
            self.project_logger.error(f"Error handling task completion: {e}")
    
    async def _send_progress_update(
        self,
        status: Optional[str],
        progress: Optional[float],
        hours_worked: float,
        notes: Optional[str]
    ):
        """Send progress update via A2A."""
        if not self.current_task:
            return
        
        message = ProjectCoordinator.create_progress_update(
            task_id=self.current_task['id'],
            project_id=self.current_task.get('project_id', ''),
            status=status or self.current_task.get('status', 'in_progress'),
            progress=progress or 0,
            hours_worked=hours_worked,
            sender=self.get_team_id(),
            recipient="project-owner",  # Would be determined dynamically
            notes=notes
        )
        
        await self.send_a2a_message(message)
    
    async def _send_blocker_notification(
        self,
        blocker_description: str,
        severity: str,
        needs_help_from: Optional[str]
    ):
        """Send blocker notification via A2A."""
        if not self.current_task:
            return
        
        message = ProjectCoordinator.create_blocker_report(
            task_id=self.current_task['id'],
            task_title=self.current_task.get('title', ''),
            project_id=self.current_task.get('project_id', ''),
            blocker_description=blocker_description,
            severity=severity,
            sender=self.get_team_id(),
            recipient=needs_help_from or "project-owner",
            needs_help_from=needs_help_from
        )
        
        await self.send_a2a_message(message)
    
    def get_current_workload(self) -> Dict[str, Any]:
        """Get current workload information."""
        return {
            "is_working": self.is_working,
            "current_task": self.current_task,
            "task_start_time": self.task_start_time.isoformat() if self.task_start_time else None,
            "available_capacity": self.get_available_capacity()
        }