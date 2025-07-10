"""
Usage Tracker for detailed API usage monitoring
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class UsageTracker:
    """Tracks detailed usage metrics for monitoring and optimization"""

    def __init__(self, quota_manager):
        self.quota_manager = quota_manager
        self.active_requests = {}

    def track_request(self, team: str, model: str, request_id: Optional[str] = None):
        """Start tracking a request"""
        if not request_id:
            request_id = f"{team}_{model}_{int(time.time() * 1000)}"

        self.active_requests[request_id] = {
            "team": team,
            "model": model,
            "start_time": time.time(),
            "input_tokens": 0,
            "output_tokens": 0,
        }

        return request_id

    def update_tokens(self, request_id: str, input_tokens: int, output_tokens: int):
        """Update token counts for a request"""
        if request_id in self.active_requests:
            self.active_requests[request_id]["input_tokens"] = input_tokens
            self.active_requests[request_id]["output_tokens"] = output_tokens

    def complete_request(self, request_id: str) -> Dict[str, Any]:
        """Complete tracking for a request"""
        if request_id not in self.active_requests:
            return {}

        request_data = self.active_requests.pop(request_id)
        request_data["duration"] = time.time() - request_data["start_time"]

        # Track in quota manager
        cost = self.quota_manager.track_usage(
            request_data["team"],
            request_data["model"],
            request_data["input_tokens"],
            request_data["output_tokens"],
        )

        request_data["cost"] = cost

        logger.info(
            f"Request {request_id}: {request_data['input_tokens'] + request_data['output_tokens']} tokens, "
            f"${cost:.4f}, {request_data['duration']:.2f}s"
        )

        return request_data


def track_llm_usage(quota_manager, team: str):
    """Decorator to track LLM usage for a function"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracker = UsageTracker(quota_manager)
            model = kwargs.get("model", "gpt-3.5-turbo")

            # Check if can make request
            can_proceed, alt_model = quota_manager.can_make_request(team, model)
            if not can_proceed:
                raise Exception(f"Team {team} has exceeded quota")

            if alt_model:
                logger.warning(f"Switching from {model} to {alt_model} due to quota")
                kwargs["model"] = alt_model

            # Track request
            request_id = tracker.track_request(team, kwargs.get("model", model))

            try:
                result = await func(*args, **kwargs)

                # Extract token usage if available
                if hasattr(result, "usage"):
                    tracker.update_tokens(
                        request_id,
                        result.usage.prompt_tokens,
                        result.usage.completion_tokens,
                    )

                tracker.complete_request(request_id)
                return result

            except Exception as e:
                tracker.complete_request(request_id)
                raise e

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracker = UsageTracker(quota_manager)
            model = kwargs.get("model", "gpt-3.5-turbo")

            # Check if can make request
            can_proceed, alt_model = quota_manager.can_make_request(team, model)
            if not can_proceed:
                raise Exception(f"Team {team} has exceeded quota")

            if alt_model:
                logger.warning(f"Switching from {model} to {alt_model} due to quota")
                kwargs["model"] = alt_model

            # Track request
            request_id = tracker.track_request(team, kwargs.get("model", model))

            try:
                result = func(*args, **kwargs)

                # Extract token usage if available
                if hasattr(result, "usage"):
                    tracker.update_tokens(
                        request_id,
                        result.usage.prompt_tokens,
                        result.usage.completion_tokens,
                    )

                tracker.complete_request(request_id)
                return result

            except Exception as e:
                tracker.complete_request(request_id)
                raise e

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
