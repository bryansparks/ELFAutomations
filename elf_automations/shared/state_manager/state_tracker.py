"""
State tracker for monitoring and querying resource states
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from supabase import Client

logger = logging.getLogger(__name__)


class StateTracker:
    """
    Tracks and queries resource states across all resource types
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_resource_overview(self) -> Dict[str, Any]:
        """Get overview of all resources by type and state"""
        try:
            result = (
                self.supabase.table("resource_state_overview").select("*").execute()
            )

            overview = {}
            for row in result.data:
                resource_type = row["resource_type"]
                if resource_type not in overview:
                    overview[resource_type] = {}
                overview[resource_type][row["current_state"]] = {
                    "count": row["count"],
                    "last_transition": row["last_transition"],
                }

            return overview
        except Exception as e:
            logger.error(f"Error getting resource overview: {str(e)}")
            return {}

    def get_resources_awaiting_action(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get resources that need attention"""
        try:
            result = (
                self.supabase.table("resources_awaiting_action")
                .select("*")
                .limit(limit)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting resources awaiting action: {str(e)}")
            return []

    def get_recent_transitions(
        self, hours: int = 24, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent state transitions"""
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            result = (
                self.supabase.table("state_transitions")
                .select("*")
                .gte("transitioned_at", since)
                .order("transitioned_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting recent transitions: {str(e)}")
            return []

    def get_failed_resources(self) -> List[Dict[str, Any]]:
        """Get all resources in failed states"""
        try:
            result = (
                self.supabase.table("resource_states")
                .select("*")
                .in_("current_state", ["failed", "failed_validation", "error"])
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting failed resources: {str(e)}")
            return []

    def get_workflow_pipeline_status(self) -> List[Dict[str, Any]]:
        """Get workflow deployment pipeline status"""
        try:
            result = (
                self.supabase.table("workflow_deployment_pipeline")
                .select("*")
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting workflow pipeline: {str(e)}")
            return []

    def get_mcp_deployment_status(self) -> List[Dict[str, Any]]:
        """Get MCP deployment status"""
        try:
            result = self.supabase.table("mcp_deployment_status").select("*").execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting MCP status: {str(e)}")
            return []

    def get_resource_details(
        self, resource_type: str, resource_id: str
    ) -> Dict[str, Any]:
        """Get detailed information about a specific resource"""
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "current_state": None,
            "history": [],
            "requirements": None,
        }

        try:
            # Get current state
            state_result = (
                self.supabase.table("resource_states")
                .select("*")
                .eq("resource_type", resource_type)
                .eq("resource_id", resource_id)
                .single()
                .execute()
            )
            details["current_state"] = state_result.data

            # Get transition history
            history_result = (
                self.supabase.table("state_transitions")
                .select("*")
                .eq("resource_type", resource_type)
                .eq("resource_id", resource_id)
                .order("transitioned_at", desc=True)
                .limit(20)
                .execute()
            )
            details["history"] = history_result.data

            # Get deployment requirements
            req_result = (
                self.supabase.table("deployment_requirements")
                .select("*")
                .eq("resource_type", resource_type)
                .eq("resource_id", resource_id)
                .execute()
            )
            details["requirements"] = req_result.data

            # Get resource-specific details
            if resource_type == "workflow":
                workflow_result = (
                    self.supabase.table("workflows")
                    .select("*")
                    .eq("id", resource_id)
                    .single()
                    .execute()
                )
                details["workflow"] = workflow_result.data
            elif resource_type == "mcp_server":
                mcp_result = (
                    self.supabase.table("mcp_registry")
                    .select("*")
                    .eq("id", resource_id)
                    .single()
                    .execute()
                )
                details["mcp"] = mcp_result.data
            elif resource_type == "team":
                team_result = (
                    self.supabase.table("teams")
                    .select("*")
                    .eq("id", resource_id)
                    .single()
                    .execute()
                )
                details["team"] = team_result.data

        except Exception as e:
            logger.error(f"Error getting resource details: {str(e)}")

        return details

    def search_resources(
        self,
        query: str,
        resource_type: Optional[str] = None,
        states: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for resources by name or metadata"""
        try:
            query_builder = self.supabase.table("resource_states").select("*")

            if resource_type:
                query_builder = query_builder.eq("resource_type", resource_type)

            if states:
                query_builder = query_builder.in_("current_state", states)

            # Search in resource name
            query_builder = query_builder.ilike("resource_name", f"%{query}%")

            result = query_builder.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error searching resources: {str(e)}")
            return []

    def get_state_statistics(
        self, resource_type: Optional[str] = None, days: int = 7
    ) -> Dict[str, Any]:
        """Get statistics about state transitions"""
        stats = {
            "total_transitions": 0,
            "failed_transitions": 0,
            "most_common_transitions": [],
            "average_time_in_state": {},
        }

        try:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()

            query_builder = (
                self.supabase.table("state_transitions")
                .select("*")
                .gte("transitioned_at", since)
            )

            if resource_type:
                query_builder = query_builder.eq("resource_type", resource_type)

            result = query_builder.execute()
            transitions = result.data

            stats["total_transitions"] = len(transitions)
            stats["failed_transitions"] = len(
                [t for t in transitions if not t.get("success", True)]
            )

            # Calculate most common transitions
            transition_counts = {}
            for t in transitions:
                key = f"{t['from_state']} → {t['to_state']}"
                transition_counts[key] = transition_counts.get(key, 0) + 1

            stats["most_common_transitions"] = sorted(
                [{"transition": k, "count": v} for k, v in transition_counts.items()],
                key=lambda x: x["count"],
                reverse=True,
            )[:10]

        except Exception as e:
            logger.error(f"Error getting state statistics: {str(e)}")

        return stats

    def get_deployment_readiness(self) -> Dict[str, Any]:
        """Get summary of resources ready for deployment"""
        readiness = {
            "workflows": {"ready": 0, "blocked": 0, "details": []},
            "mcp_servers": {"ready": 0, "blocked": 0, "details": []},
            "teams": {"ready": 0, "blocked": 0, "details": []},
        }

        try:
            # Check workflows
            workflows = (
                self.supabase.table("resource_states")
                .select("*")
                .eq("resource_type", "workflow")
                .in_("current_state", ["validated", "deployed"])
                .execute()
            )

            for w in workflows.data:
                if w["current_state"] == "validated":
                    readiness["workflows"]["ready"] += 1
                    readiness["workflows"]["details"].append(
                        {
                            "id": w["resource_id"],
                            "name": w["resource_name"],
                            "state": "ready_to_deploy",
                        }
                    )

            # Check MCPs
            mcps = (
                self.supabase.table("resource_states")
                .select("*")
                .eq("resource_type", "mcp_server")
                .in_("current_state", ["built", "deployed"])
                .execute()
            )

            for m in mcps.data:
                if m["current_state"] == "built":
                    readiness["mcp_servers"]["ready"] += 1
                    readiness["mcp_servers"]["details"].append(
                        {
                            "id": m["resource_id"],
                            "name": m["resource_name"],
                            "state": "ready_to_deploy",
                        }
                    )

            # Check teams
            teams = (
                self.supabase.table("resource_states")
                .select("*")
                .eq("resource_type", "team")
                .in_("current_state", ["built", "deployed", "awaiting_dependencies"])
                .execute()
            )

            for t in teams.data:
                if t["current_state"] == "built":
                    readiness["teams"]["ready"] += 1
                    readiness["teams"]["details"].append(
                        {
                            "id": t["resource_id"],
                            "name": t["resource_name"],
                            "state": "ready_to_deploy",
                        }
                    )
                elif t["current_state"] == "awaiting_dependencies":
                    readiness["teams"]["blocked"] += 1
                    readiness["teams"]["details"].append(
                        {
                            "id": t["resource_id"],
                            "name": t["resource_name"],
                            "state": "blocked_by_dependencies",
                        }
                    )

        except Exception as e:
            logger.error(f"Error getting deployment readiness: {str(e)}")

        return readiness
