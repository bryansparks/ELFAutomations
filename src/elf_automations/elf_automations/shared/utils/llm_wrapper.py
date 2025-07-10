"""
LLM Wrapper with runtime fallback support

Wraps LLM instances to handle quota errors during invoke.
"""

import logging
from typing import Any, List, Optional, Union

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class FallbackLLM:
    """Wrapper that handles quota errors with automatic fallback"""

    def __init__(
        self,
        llm_factory,
        team_name: str,
        preferred_provider: str = "openai",
        preferred_model: str = "gpt-4",
        temperature: float = 0.7,
    ):
        self.llm_factory = llm_factory
        self.team_name = team_name
        self.preferred_provider = preferred_provider
        self.preferred_model = preferred_model
        self.temperature = temperature
        self._current_llm = None
        self._current_index = -1
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize with the preferred or next available LLM"""
        # Build list of models to try
        self.models_to_try = []

        # Add preferred model first
        self.models_to_try.append(
            (self.preferred_provider, self.preferred_model, self.temperature)
        )

        # Add fallback chain
        for provider, model, default_temp in self.llm_factory.FALLBACK_CHAIN:
            if provider == self.preferred_provider and model == self.preferred_model:
                continue  # Skip duplicate
            self.models_to_try.append(
                (provider, model, self.temperature or default_temp)
            )

        # Try to get the first working LLM
        self._get_next_llm()

    def _get_next_llm(self) -> bool:
        """Get the next available LLM from the chain"""
        self._current_index += 1

        while self._current_index < len(self.models_to_try):
            provider, model, temp = self.models_to_try[self._current_index]
            try:
                self._current_llm = self.llm_factory._create_single_llm(
                    provider, model, temp
                )
                logger.info(f"Using {provider}/{model} for team {self.team_name}")
                return True
            except Exception as e:
                logger.warning(f"Failed to create {provider}/{model}: {e}")
                self._current_index += 1

        return False

    def invoke(self, input: Union[str, List[BaseMessage]], **kwargs) -> Any:
        """Invoke with automatic fallback on quota errors"""
        while self._current_llm is not None:
            try:
                return self._current_llm.invoke(input, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "quota" in error_str.lower() or "429" in error_str:
                    logger.warning(f"Quota error with current model: {e}")
                    if self._get_next_llm():
                        logger.info("Retrying with fallback model...")
                        continue
                    else:
                        raise Exception("All LLM options exhausted due to quota limits")
                else:
                    # Not a quota error, raise it
                    raise

        raise Exception("No LLM available")

    def __getattr__(self, name):
        """Proxy other attributes to the current LLM"""
        if self._current_llm:
            return getattr(self._current_llm, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    @property
    def model_name(self):
        """Return the current model name"""
        if self._current_llm and hasattr(self._current_llm, "model_name"):
            return self._current_llm.model_name
        elif self._current_llm and hasattr(self._current_llm, "model"):
            return self._current_llm.model
        else:
            # Return the current model from our tracking
            if self._current_index >= 0 and self._current_index < len(
                self.models_to_try
            ):
                _, model, _ = self.models_to_try[self._current_index]
                return model
            return "unknown"

    def bind(self, **kwargs):
        """Bind arguments to the LLM (for compatibility)"""
        if self._current_llm and hasattr(self._current_llm, "bind"):
            return self._current_llm.bind(**kwargs)
        return self

    def with_config(self, **kwargs):
        """Configure the LLM (for compatibility)"""
        if self._current_llm and hasattr(self._current_llm, "with_config"):
            return self._current_llm.with_config(**kwargs)
        return self
