"""
Cost Monitoring System for ElfAutomations

Provides real-time cost analytics, alerts, and reporting.
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CostAlert:
    """Cost alert data"""

    timestamp: str
    level: AlertLevel
    team: str
    message: str
    details: Dict[str, Any]


@dataclass
class CostMetrics:
    """Cost metrics for analysis"""

    total_cost: float
    token_count: int
    request_count: int
    avg_cost_per_request: float
    avg_tokens_per_request: float
    most_expensive_model: str
    cheapest_model: str
    cost_by_model: Dict[str, float]
    cost_by_hour: Dict[int, float]
    peak_usage_hour: int


class CostMonitor:
    """Advanced cost monitoring and analytics"""

    def __init__(
        self,
        storage_path: Path = Path("cost_monitoring"),
        alert_webhook: Optional[str] = None,
        supabase_client=None,
    ):
        """
        Initialize cost monitor

        Args:
            storage_path: Where to store monitoring data
            alert_webhook: Optional webhook URL for alerts
            supabase_client: Optional Supabase client for persistence
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.alert_webhook = alert_webhook
        self.supabase = supabase_client
        self.alerts: List[CostAlert] = []
        self._load_alerts()

    def _load_alerts(self):
        """Load existing alerts"""
        alerts_file = self.storage_path / "alerts.json"
        if alerts_file.exists():
            with open(alerts_file, "r") as f:
                data = json.load(f)
                self.alerts = [CostAlert(**alert) for alert in data]

    def _save_alerts(self):
        """Save alerts to storage"""
        alerts_file = self.storage_path / "alerts.json"
        with open(alerts_file, "w") as f:
            json.dump(
                [asdict(alert) for alert in self.alerts[-100:]],  # Keep last 100
                f,
                indent=2,
            )

    async def analyze_costs(self, quota_manager) -> Dict[str, CostMetrics]:
        """Analyze costs across all teams"""
        metrics = {}
        today = datetime.now().strftime("%Y-%m-%d")

        for team in self._get_all_teams(quota_manager):
            if team == "budgets":
                continue

            # Initialize metrics
            total_cost = 0
            token_count = 0
            request_count = 0
            cost_by_model = defaultdict(float)
            cost_by_hour = defaultdict(float)

            # Analyze today's data
            if team in quota_manager.usage_data:
                if today in quota_manager.usage_data[team]:
                    daily_data = quota_manager.usage_data[team][today]
                    total_cost = daily_data.get("total_cost", 0)
                    token_count = daily_data.get("token_count", 0)

                    # Model breakdown
                    if "models" in daily_data:
                        for model, data in daily_data["models"].items():
                            cost_by_model[model] = data.get("cost", 0)
                            request_count += data.get("calls", 0)

                    # Hourly breakdown (would need timestamp data)
                    # For now, simulate with current hour
                    current_hour = datetime.now().hour
                    cost_by_hour[current_hour] = total_cost

            # Calculate metrics
            avg_cost = total_cost / request_count if request_count > 0 else 0
            avg_tokens = token_count / request_count if request_count > 0 else 0

            most_expensive = (
                max(cost_by_model.items(), key=lambda x: x[1])[0]
                if cost_by_model
                else "N/A"
            )
            cheapest = (
                min(cost_by_model.items(), key=lambda x: x[1])[0]
                if cost_by_model
                else "N/A"
            )
            peak_hour = (
                max(cost_by_hour.items(), key=lambda x: x[1])[0] if cost_by_hour else 0
            )

            metrics[team] = CostMetrics(
                total_cost=total_cost,
                token_count=token_count,
                request_count=request_count,
                avg_cost_per_request=avg_cost,
                avg_tokens_per_request=avg_tokens,
                most_expensive_model=most_expensive,
                cheapest_model=cheapest,
                cost_by_model=dict(cost_by_model),
                cost_by_hour=dict(cost_by_hour),
                peak_usage_hour=peak_hour,
            )

            # Check for alerts
            await self._check_alerts(team, metrics[team], quota_manager)

        return metrics

    async def _check_alerts(self, team: str, metrics: CostMetrics, quota_manager):
        """Check and create alerts based on metrics"""
        budget = quota_manager.get_team_budget(team)

        # Critical: Over budget
        if metrics.total_cost > budget:
            await self._create_alert(
                AlertLevel.CRITICAL,
                team,
                f"Team {team} is OVER BUDGET",
                {
                    "budget": budget,
                    "spent": metrics.total_cost,
                    "overage": metrics.total_cost - budget,
                },
            )

        # Warning: Near budget
        elif metrics.total_cost > budget * 0.8:
            await self._create_alert(
                AlertLevel.WARNING,
                team,
                f"Team {team} approaching budget limit",
                {
                    "budget": budget,
                    "spent": metrics.total_cost,
                    "percentage": (metrics.total_cost / budget) * 100,
                },
            )

        # Info: High cost per request
        if metrics.avg_cost_per_request > 0.10:  # $0.10 per request
            await self._create_alert(
                AlertLevel.INFO,
                team,
                f"High average cost per request for {team}",
                {"avg_cost": metrics.avg_cost_per_request, "threshold": 0.10},
            )

    async def _create_alert(
        self, level: AlertLevel, team: str, message: str, details: Dict
    ):
        """Create and send alert"""
        alert = CostAlert(
            timestamp=datetime.now().isoformat(),
            level=level,
            team=team,
            message=message,
            details=details,
        )

        self.alerts.append(alert)
        self._save_alerts()

        # Send webhook if configured
        if self.alert_webhook:
            await self._send_webhook(alert)

        # Log to Supabase if available
        if self.supabase:
            await self._log_to_supabase(alert)

        logger.warning(f"COST ALERT [{level.value}] {team}: {message}")

    async def _send_webhook(self, alert: CostAlert):
        """Send alert to webhook"""
        # Implementation would use aiohttp to POST to webhook
        pass

    async def _log_to_supabase(self, alert: CostAlert):
        """Log alert to Supabase"""
        if self.supabase:
            try:
                self.supabase.table("cost_alerts").insert(
                    {
                        "timestamp": alert.timestamp,
                        "level": alert.level.value,
                        "team": alert.team,
                        "message": alert.message,
                        "details": alert.details,
                    }
                ).execute()
            except Exception as e:
                logger.error(f"Failed to log alert to Supabase: {e}")

    def _get_all_teams(self, quota_manager) -> List[str]:
        """Get all teams from quota manager"""
        teams = set()
        for key, value in quota_manager.usage_data.items():
            if key != "budgets" and isinstance(value, dict):
                teams.add(key)
        return list(teams)

    def generate_cost_report(
        self,
        quota_manager,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive cost report"""
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        report = {
            "period": {"start": start_date, "end": end_date},
            "teams": {},
            "summary": {
                "total_cost": 0,
                "total_tokens": 0,
                "total_requests": 0,
                "teams_over_budget": 0,
                "cost_by_model": defaultdict(float),
                "cost_by_team": {},
                "daily_trend": {},
            },
        }

        # Analyze each team
        for team in self._get_all_teams(quota_manager):
            if team == "budgets":
                continue

            team_data = {
                "budget": quota_manager.get_team_budget(team),
                "days": {},
                "total_cost": 0,
                "total_tokens": 0,
                "models_used": set(),
            }

            # Iterate through date range
            current = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            while current <= end:
                date_str = current.strftime("%Y-%m-%d")

                if team in quota_manager.usage_data:
                    if date_str in quota_manager.usage_data[team]:
                        daily = quota_manager.usage_data[team][date_str]
                        team_data["days"][date_str] = daily
                        team_data["total_cost"] += daily.get("total_cost", 0)
                        team_data["total_tokens"] += daily.get("token_count", 0)

                        if "models" in daily:
                            team_data["models_used"].update(daily["models"].keys())
                            for model, data in daily["models"].items():
                                report["summary"]["cost_by_model"][model] += data.get(
                                    "cost", 0
                                )

                current += timedelta(days=1)

            # Convert set to list for JSON serialization
            team_data["models_used"] = list(team_data["models_used"])

            # Check if over budget
            avg_daily = team_data["total_cost"] / (
                (end - datetime.strptime(start_date, "%Y-%m-%d")).days + 1
            )
            if avg_daily > team_data["budget"]:
                report["summary"]["teams_over_budget"] += 1

            report["teams"][team] = team_data
            report["summary"]["total_cost"] += team_data["total_cost"]
            report["summary"]["total_tokens"] += team_data["total_tokens"]
            report["summary"]["cost_by_team"][team] = team_data["total_cost"]

        # Calculate daily trends
        current = datetime.strptime(start_date, "%Y-%m-%d")
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            daily_total = 0

            for team in report["teams"]:
                if date_str in report["teams"][team]["days"]:
                    daily_total += report["teams"][team]["days"][date_str].get(
                        "total_cost", 0
                    )

            report["summary"]["daily_trend"][date_str] = daily_total
            current += timedelta(days=1)

        # Convert defaultdict to dict
        report["summary"]["cost_by_model"] = dict(report["summary"]["cost_by_model"])

        return report

    def export_report(self, report: Dict[str, Any], format: str = "json") -> Path:
        """Export report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            file_path = self.storage_path / f"cost_report_{timestamp}.json"
            with open(file_path, "w") as f:
                json.dump(report, f, indent=2)

        elif format == "csv":
            import csv

            file_path = self.storage_path / f"cost_report_{timestamp}.csv"

            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Team", "Date", "Cost", "Tokens", "Model", "Requests"])

                for team, data in report["teams"].items():
                    for date, daily in data["days"].items():
                        for model, model_data in daily.get("models", {}).items():
                            writer.writerow(
                                [
                                    team,
                                    date,
                                    model_data.get("cost", 0),
                                    daily.get("token_count", 0),
                                    model,
                                    model_data.get("calls", 0),
                                ]
                            )

        logger.info(f"Report exported to {file_path}")
        return file_path

    def get_cost_predictions(
        self, quota_manager, team: str, days_ahead: int = 7
    ) -> Dict[str, float]:
        """Predict future costs based on trends"""
        # Get last 30 days of data
        history = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if (
                team in quota_manager.usage_data
                and date in quota_manager.usage_data[team]
            ):
                history.append(
                    quota_manager.usage_data[team][date].get("total_cost", 0)
                )

        if not history:
            return {}

        # Simple moving average prediction
        avg_daily = sum(history) / len(history)

        predictions = {}
        for i in range(1, days_ahead + 1):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            # Add some variance based on day of week
            day_of_week = (datetime.now() + timedelta(days=i)).weekday()
            if day_of_week in [5, 6]:  # Weekend
                predictions[date] = avg_daily * 0.7
            else:  # Weekday
                predictions[date] = avg_daily * 1.1

        return predictions
