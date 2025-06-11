"""
LLM Factory with automatic fallback support

Handles quota limits by falling back to alternative models.
"""

import logging
import os
from typing import Optional, Union

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from ..quota import QuotaManager
from .llm_with_quota import QuotaTrackedLLM
from .llm_wrapper import FallbackLLM

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLMs with fallback support"""

    # Model hierarchy for fallbacks
    FALLBACK_CHAIN = [
        ("openai", "gpt-4", 0.7),
        ("openai", "gpt-3.5-turbo", 0.5),
        ("anthropic", "claude-3-opus-20240229", 0.7),
        ("anthropic", "claude-3-sonnet-20240229", 0.5),
        ("anthropic", "claude-3-haiku-20240307", 0.3),
    ]

    @classmethod
    def create_llm(
        cls,
        preferred_provider: str = "openai",
        preferred_model: str = "gpt-4",
        temperature: float = 0.7,
        team_name: Optional[str] = None,
        enable_fallback: bool = True,
    ) -> Union[ChatOpenAI, ChatAnthropic, FallbackLLM]:
        """
        Create an LLM with automatic fallback on quota errors

        Args:
            preferred_provider: Preferred LLM provider
            preferred_model: Preferred model name
            temperature: Temperature for generation
            team_name: Team name for logging
            enable_fallback: Whether to enable runtime fallback (default: True)

        Returns:
            Configured LLM instance (with fallback wrapper if enabled)
        """
        if enable_fallback:
            # Return wrapper that handles runtime quota errors
            return FallbackLLM(
                llm_factory=cls,
                team_name=team_name or "unknown",
                preferred_provider=preferred_provider,
                preferred_model=preferred_model,
                temperature=temperature,
            )

        # Original behavior - try to create without runtime fallback
        try:
            return cls._create_single_llm(
                preferred_provider, preferred_model, temperature
            )
        except Exception as e:
            logger.warning(
                f"Failed to create {preferred_provider}/{preferred_model}: {e}"
            )

        # Try fallback chain
        for provider, model, default_temp in cls.FALLBACK_CHAIN:
            if provider == preferred_provider and model == preferred_model:
                continue  # Skip the one we already tried

            try:
                logger.info(f"Falling back to {provider}/{model} for team {team_name}")
                return cls._create_single_llm(
                    provider, model, temperature or default_temp
                )
            except Exception as e:
                logger.warning(f"Fallback {provider}/{model} also failed: {e}")
                continue

        raise Exception(
            "All LLM options exhausted. No API keys available or all quotas exceeded."
        )

    @classmethod
    def _create_single_llm(cls, provider: str, model: str, temperature: float):
        """Create a single LLM instance"""
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            return ChatOpenAI(
                model=model, temperature=temperature, openai_api_key=api_key
            )
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return ChatAnthropic(
                model=model, temperature=temperature, anthropic_api_key=api_key
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    @classmethod
    def create_with_quota_tracking(
        cls,
        team_name: str,
        preferred_provider: str = "openai",
        preferred_model: str = "gpt-4",
        temperature: float = 0.7,
        quota_manager: Optional[QuotaManager] = None,
        enable_fallback: bool = True,
        supabase_client: Optional["Client"] = None,
    ) -> QuotaTrackedLLM:
        """
        Create LLM with integrated quota tracking and fallback

        This combines:
        1. Automatic fallback on quota errors (OpenAI -> Anthropic)
        2. Quota tracking and budget enforcement
        3. Usage reporting and cost monitoring
        4. Supabase integration for centralized monitoring

        Args:
            team_name: Team name for quota tracking
            preferred_provider: Preferred LLM provider
            preferred_model: Preferred model
            temperature: Temperature setting
            quota_manager: Optional QuotaManager instance
            enable_fallback: Whether to enable runtime fallback
            supabase_client: Optional Supabase client for cost monitoring

        Returns:
            QuotaTrackedLLM instance with full tracking
        """
        if not enable_fallback:
            # If fallback disabled, just create a regular LLM with quota wrapper
            llm = cls.create_llm(
                preferred_provider=preferred_provider,
                preferred_model=preferred_model,
                temperature=temperature,
                team_name=team_name,
                enable_fallback=False,
            )
            # Wrap in quota tracker
            # This is a simplified version - in production would need proper wrapping
            logger.warning("Quota tracking without fallback not fully implemented")
            return llm

        # Return quota-tracked LLM with fallback
        return QuotaTrackedLLM(
            llm_factory=cls,
            team_name=team_name,
            preferred_provider=preferred_provider,
            preferred_model=preferred_model,
            temperature=temperature,
            quota_manager=quota_manager,
            supabase_client=supabase_client,
        )
