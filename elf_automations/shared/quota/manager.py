"""
Quota Manager for API usage tracking and limits

Prevents teams from exhausting API quotas by:
- Tracking usage per team
- Enforcing budgets
- Providing fallback options
- Alerting on high usage
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class QuotaManager:
    """Manages API quotas and usage tracking"""

    # Model costs per 1K tokens (approximate)
    MODEL_COSTS = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    }

    def __init__(
        self,
        storage_path: Path = Path("quota_data"),
        default_daily_budget: float = 10.0,
        warning_threshold: float = 0.8,
    ):
        """
        Initialize quota manager

        Args:
            storage_path: Where to store usage data
            default_daily_budget: Default daily budget per team in USD
            warning_threshold: Warn when usage exceeds this fraction of budget
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)
        self.default_daily_budget = default_daily_budget
        self.warning_threshold = warning_threshold
        self._load_usage_data()

    def _load_usage_data(self):
        """Load usage data from storage"""
        usage_file = self.storage_path / "usage.json"
        if usage_file.exists():
            with open(usage_file, "r") as f:
                self.usage_data = json.load(f)
        else:
            self.usage_data = {}

    def _save_usage_data(self):
        """Save usage data to storage"""
        usage_file = self.storage_path / "usage.json"
        with open(usage_file, "w") as f:
            json.dump(self.usage_data, f, indent=2)

    def track_usage(
        self, team: str, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Track API usage for a team

        Returns:
            Cost of this usage in USD
        """
        # Calculate cost
        model_cost = self.MODEL_COSTS.get(model, self.MODEL_COSTS["gpt-3.5-turbo"])
        cost = (
            input_tokens * model_cost["input"] + output_tokens * model_cost["output"]
        ) / 1000

        # Initialize team data if needed
        today = datetime.now().strftime("%Y-%m-%d")
        if team not in self.usage_data:
            self.usage_data[team] = {}
        if today not in self.usage_data[team]:
            self.usage_data[team][today] = {
                "total_cost": 0,
                "models": {},
                "token_count": 0,
            }

        # Update usage
        daily_data = self.usage_data[team][today]
        daily_data["total_cost"] += cost
        daily_data["token_count"] += input_tokens + output_tokens

        if model not in daily_data["models"]:
            daily_data["models"][model] = {"cost": 0, "calls": 0}
        daily_data["models"][model]["cost"] += cost
        daily_data["models"][model]["calls"] += 1

        # Check if warning needed
        if (
            daily_data["total_cost"]
            > self.default_daily_budget * self.warning_threshold
        ):
            logger.warning(
                f"Team {team} has used ${daily_data['total_cost']:.2f} "
                f"of ${self.default_daily_budget:.2f} daily budget"
            )

        self._save_usage_data()
        return cost

    def can_make_request(
        self, team: str, model: str, estimated_tokens: int = 1000
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if team can make a request

        Returns:
            (can_make_request, alternative_model_if_needed)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        current_usage = 0

        if team in self.usage_data and today in self.usage_data[team]:
            current_usage = self.usage_data[team][today]["total_cost"]

        # Estimate cost
        model_cost = self.MODEL_COSTS.get(model, self.MODEL_COSTS["gpt-3.5-turbo"])
        estimated_cost = (estimated_tokens * model_cost["output"]) / 1000

        if current_usage + estimated_cost <= self.default_daily_budget:
            return True, None

        # Try cheaper alternatives
        if model == "gpt-4":
            return True, "gpt-3.5-turbo"
        elif model == "claude-3-opus":
            return True, "claude-3-haiku"

        return False, None

    def get_usage_report(self, team: str, days: int = 7) -> Dict:
        """Get usage report for a team"""
        report = {
            "team": team,
            "period": f"Last {days} days",
            "daily_budget": self.default_daily_budget,
            "days": {},
        }

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if team in self.usage_data and date in self.usage_data[team]:
                report["days"][date] = self.usage_data[team][date]
            else:
                report["days"][date] = {"total_cost": 0, "models": {}, "token_count": 0}

        report["total_cost"] = sum(day["total_cost"] for day in report["days"].values())
        report["average_daily"] = report["total_cost"] / days

        return report

    def set_team_budget(self, team: str, daily_budget: float):
        """Set custom budget for a team"""
        if "budgets" not in self.usage_data:
            self.usage_data["budgets"] = {}
        self.usage_data["budgets"][team] = daily_budget
        self._save_usage_data()

    def get_team_budget(self, team: str) -> float:
        """Get budget for a team"""
        if "budgets" in self.usage_data and team in self.usage_data["budgets"]:
            return self.usage_data["budgets"][team]
        return self.default_daily_budget
