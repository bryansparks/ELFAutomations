"""
LLM wrapper with integrated quota tracking

Combines LLM fallback with quota management.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional, Union

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from ..quota import QuotaManager, UsageTracker
from .llm_wrapper import FallbackLLM

logger = logging.getLogger(__name__)

# Try to import Supabase
try:
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning(
        "Supabase not available - cost monitoring will use local storage only"
    )


class QuotaTrackedLLM(FallbackLLM):
    """LLM wrapper that tracks quota usage automatically"""

    def __init__(
        self,
        llm_factory,
        team_name: str,
        preferred_provider: str = "openai",
        preferred_model: str = "gpt-4",
        temperature: float = 0.7,
        quota_manager: Optional[QuotaManager] = None,
        supabase_client: Optional["Client"] = None,
    ):
        """
        Initialize quota-tracked LLM

        Args:
            llm_factory: LLMFactory instance
            team_name: Team name for quota tracking
            preferred_provider: Preferred LLM provider
            preferred_model: Preferred model
            temperature: Temperature setting
            quota_manager: Optional QuotaManager instance (creates one if not provided)
            supabase_client: Optional Supabase client for cost monitoring
        """
        super().__init__(
            llm_factory, team_name, preferred_provider, preferred_model, temperature
        )

        # Initialize quota manager if not provided
        if quota_manager is None:
            quota_path = Path.home() / ".elf_automations" / "quota_data"
            quota_path.mkdir(parents=True, exist_ok=True)
            self.quota_manager = QuotaManager(storage_path=quota_path)
        else:
            self.quota_manager = quota_manager

        self.usage_tracker = UsageTracker(self.quota_manager)

        # Initialize Supabase client if not provided but available
        self.supabase_client = supabase_client
        if self.supabase_client is None and SUPABASE_AVAILABLE:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if url and key:
                try:
                    self.supabase_client = create_client(url, key)
                    logger.info("Initialized Supabase client for cost monitoring")
                except Exception as e:
                    logger.warning(f"Failed to initialize Supabase client: {e}")
                    self.supabase_client = None

    def invoke(self, input: Union[str, list[BaseMessage]], **kwargs) -> Any:
        """Invoke with quota tracking"""
        # Start tracking
        request_id = self.usage_tracker.track_request(self.team_name, self.model_name)

        try:
            # Check quota before proceeding
            can_proceed, alt_model = self.quota_manager.can_make_request(
                self.team_name,
                self.model_name,
                estimated_tokens=1000,  # Conservative estimate
            )

            if not can_proceed:
                logger.error(f"Team {self.team_name} has exceeded quota")
                raise Exception(f"Quota exceeded for team {self.team_name}")

            # Use alternative model if suggested
            if alt_model and alt_model != self.model_name:
                logger.info(
                    f"Quota manager suggests using {alt_model} instead of {self.model_name}"
                )
                # Try to switch to alternative model
                for i, (provider, model, temp) in enumerate(self.models_to_try):
                    if model == alt_model:
                        self._current_index = (
                            i - 1
                        )  # Will be incremented by _get_next_llm
                        self._get_next_llm()
                        break

            # Invoke the LLM
            result = super().invoke(input, **kwargs)

            # Extract token usage
            input_tokens = 0
            output_tokens = 0

            # Try to get usage from result
            if hasattr(result, "_response") and hasattr(result._response, "usage"):
                usage = result._response.usage
                if hasattr(usage, "prompt_tokens"):
                    input_tokens = usage.prompt_tokens
                if hasattr(usage, "completion_tokens"):
                    output_tokens = usage.completion_tokens
            elif hasattr(result, "response_metadata"):
                metadata = result.response_metadata
                if "token_usage" in metadata:
                    input_tokens = metadata["token_usage"].get("prompt_tokens", 0)
                    output_tokens = metadata["token_usage"].get("completion_tokens", 0)
                elif "usage" in metadata:
                    input_tokens = metadata["usage"].get("input_tokens", 0)
                    output_tokens = metadata["usage"].get("output_tokens", 0)

            # If we couldn't get exact counts, estimate
            if input_tokens == 0 and output_tokens == 0:
                # Rough estimation: ~4 chars per token
                if isinstance(input, str):
                    input_tokens = len(input) // 4
                else:
                    input_tokens = sum(len(str(msg)) for msg in input) // 4

                if hasattr(result, "content"):
                    output_tokens = len(result.content) // 4
                else:
                    output_tokens = 100  # Default estimate

            # Update tracking
            self.usage_tracker.update_tokens(request_id, input_tokens, output_tokens)
            self.usage_tracker.complete_request(request_id)

            # Log usage
            cost = self.quota_manager.MODEL_COSTS.get(
                self.model_name, self.quota_manager.MODEL_COSTS["gpt-3.5-turbo"]
            )
            total_cost = (
                input_tokens * cost["input"] + output_tokens * cost["output"]
            ) / 1000

            logger.info(
                f"Team {self.team_name} used {self.model_name}: "
                f"{input_tokens + output_tokens} tokens (${total_cost:.4f})"
            )

            # Record to Supabase if available
            if self.supabase_client:
                self._record_to_supabase(
                    self.model_name, input_tokens, output_tokens, total_cost
                )

            return result

        except Exception as e:
            # Complete tracking even on error
            self.usage_tracker.complete_request(request_id)
            raise

    def get_usage_report(self, days: int = 7) -> dict:
        """Get usage report for this team"""
        return self.quota_manager.get_usage_report(self.team_name, days)

    def get_remaining_budget(self) -> float:
        """Get remaining budget for today"""
        import datetime

        today = datetime.datetime.now().strftime("%Y-%m-%d")

        current_usage = 0
        if self.team_name in self.quota_manager.usage_data:
            if today in self.quota_manager.usage_data[self.team_name]:
                current_usage = self.quota_manager.usage_data[self.team_name][today][
                    "total_cost"
                ]

        budget = self.quota_manager.get_team_budget(self.team_name)
        return budget - current_usage

    def _record_to_supabase(
        self, model: str, input_tokens: int, output_tokens: int, cost: float
    ):
        """Record usage to Supabase cost monitoring tables"""
        if not self.supabase_client:
            return

        try:
            # Determine provider from model name
            provider = "openai" if "gpt" in model.lower() else "anthropic"

            # Use the PostgreSQL function to record usage
            result = self.supabase_client.rpc(
                "record_api_usage",
                {
                    "p_team_name": self.team_name,
                    "p_provider": provider,
                    "p_model": model,
                    "p_input_tokens": input_tokens,
                    "p_output_tokens": output_tokens,
                    "p_cost": cost,
                },
            ).execute()

            logger.debug(f"Recorded usage to Supabase for {self.team_name}")

        except Exception as e:
            logger.error(f"Failed to record usage to Supabase: {e}")
            # Don't raise - we don't want to fail the LLM call due to monitoring issues
