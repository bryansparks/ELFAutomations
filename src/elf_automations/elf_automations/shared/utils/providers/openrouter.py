"""
OpenRouter.ai Chat Model Provider

Provides intelligent routing to 100+ models based on:
- Cost optimization
- Speed requirements
- Quality needs
- Availability
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chat_models.base import BaseChatModel
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class ChatOpenRouter(BaseChatModel):
    """OpenRouter chat model implementation for intelligent model routing"""

    model: str = "auto"
    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.7
    preferences: Dict[str, Any] = {}
    timeout: int = 30
    max_retries: int = 3

    def __init__(self, **kwargs):
        """Initialize ChatOpenRouter with configuration"""
        super().__init__(**kwargs)

        # Set API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenRouter API key not provided. "
                    "Set OPENROUTER_API_KEY environment variable or pass api_key parameter."
                )

        # Set default preferences
        self.preferences = self.preferences or {
            "max_cost_per_token": 0.0001,
            "prefer_faster": False,
            "quality_threshold": 0.8,
            "prefer_local": False,
            "fallback_to_cloud": True,
        }

        # Initialize HTTP client
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/bryansparks/ELFAutomations",
                "X-Title": "ElfAutomations",
            },
            timeout=self.timeout,
        )

    @property
    def _llm_type(self) -> str:
        """Return identifier of LLM type"""
        return "openrouter"

    def _convert_messages_to_openrouter_format(
        self, messages: List[BaseMessage]
    ) -> List[Dict[str, str]]:
        """Convert LangChain messages to OpenRouter format"""
        openrouter_messages = []

        for message in messages:
            if isinstance(message, SystemMessage):
                openrouter_messages.append(
                    {"role": "system", "content": message.content}
                )
            elif isinstance(message, HumanMessage):
                openrouter_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                openrouter_messages.append(
                    {"role": "assistant", "content": message.content}
                )
            else:
                # Handle other message types
                openrouter_messages.append(
                    {"role": "user", "content": str(message.content)}
                )

        return openrouter_messages

    def _create_chat_request(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Create OpenRouter chat completion request"""
        # Build base request
        request_data = {
            "messages": self._convert_messages_to_openrouter_format(messages),
            "temperature": kwargs.get("temperature", self.temperature),
        }

        # Add model selection
        if self.model == "auto":
            # Let OpenRouter choose based on preferences
            request_data["route"] = "auto"
            request_data["models"] = self._get_preferred_models()
        else:
            # Use specific model
            request_data["model"] = self.model

        # Add stop sequences if provided
        if stop:
            request_data["stop"] = stop

        # Add preferences for auto routing
        if self.model == "auto":
            request_data["preferences"] = self.preferences

        # Add any additional kwargs
        request_data.update(kwargs)

        return request_data

    def _get_preferred_models(self) -> List[str]:
        """Get list of preferred models based on preferences"""
        models = []

        # Add models based on preferences
        if self.preferences.get("prefer_local", False):
            # These would be custom local model endpoints
            models.extend(
                ["local/llama3-8b", "local/mistral-7b", "local/codellama-13b"]
            )

        # Add cloud models by cost/quality preference
        if self.preferences.get("max_cost_per_token", 1.0) < 0.001:
            # Low cost models
            models.extend(
                [
                    "openai/gpt-3.5-turbo",
                    "anthropic/claude-3-haiku",
                    "google/gemini-flash-1.5",
                    "meta-llama/llama-3-8b-instruct",
                ]
            )
        else:
            # Higher quality models
            models.extend(
                [
                    "openai/gpt-4-turbo",
                    "anthropic/claude-3-opus",
                    "google/gemini-pro-1.5",
                    "openai/gpt-4",
                ]
            )

        # Speed preference
        if self.preferences.get("prefer_faster", False):
            # Prioritize faster models
            models = [
                m for m in models if "turbo" in m or "flash" in m or "haiku" in m
            ] + models

        return models

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> AIMessage:
        """Generate chat completion via OpenRouter"""
        # Create request
        request_data = self._create_chat_request(messages, stop, **kwargs)

        # Log routing decision
        logger.info(
            f"OpenRouter request - Model: {self.model}, "
            f"Preferences: {self.preferences}"
        )

        # Make API call with retries
        for attempt in range(self.max_retries):
            try:
                response = self._client.post("/chat/completions", json=request_data)
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    logger.warning(
                        f"Rate limit hit, attempt {attempt + 1}/{self.max_retries}"
                    )
                    if attempt < self.max_retries - 1:
                        import time

                        time.sleep(2**attempt)  # Exponential backoff
                        continue
                raise
            except Exception as e:
                logger.error(f"OpenRouter API error: {e}")
                raise

        # Parse response
        result = response.json()

        # Extract model used (for logging)
        model_used = result.get("model", "unknown")
        logger.info(f"OpenRouter selected model: {model_used}")

        # Extract message content
        content = result["choices"][0]["message"]["content"]

        # Create AI message with metadata
        ai_message = AIMessage(
            content=content,
            additional_kwargs={
                "model_used": model_used,
                "usage": result.get("usage", {}),
                "openrouter_metadata": {
                    "model": model_used,
                    "routing_reason": result.get("routing_reason"),
                    "cost": result.get("usage", {}).get("total_cost", 0),
                },
            },
        )

        return ai_message

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> AIMessage:
        """Async generation - not implemented yet"""
        raise NotImplementedError("Async generation not yet implemented for OpenRouter")

    def get_num_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

    def __del__(self):
        """Cleanup HTTP client on deletion"""
        if hasattr(self, "_client"):
            self._client.close()


class ChatLocalModel(BaseChatModel):
    """Local model chat implementation for on-premise SLMs"""

    model: str
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    timeout: int = 60

    def __init__(self, **kwargs):
        """Initialize local model connection"""
        super().__init__(**kwargs)

        # Set base URL from environment if not provided
        if not self.base_url:
            self.base_url = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434")

        # Initialize HTTP client
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

        # Verify connection
        try:
            response = self._client.get("/api/tags")
            if response.status_code == 200:
                available_models = [
                    m["name"] for m in response.json().get("models", [])
                ]
                if self.model not in available_models:
                    logger.warning(
                        f"Model {self.model} not found in local models. "
                        f"Available: {available_models}"
                    )
        except Exception as e:
            logger.warning(f"Could not verify local model server: {e}")

    @property
    def _llm_type(self) -> str:
        """Return identifier of LLM type"""
        return "local_model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> AIMessage:
        """Generate response from local model"""
        # Convert messages to prompt (Ollama format)
        prompt = self._messages_to_prompt(messages)

        # Create request
        request_data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": False,
        }

        if stop:
            request_data["stop"] = stop

        # Make API call
        try:
            response = self._client.post("/api/generate", json=request_data)
            response.raise_for_status()
            result = response.json()

            return AIMessage(
                content=result["response"],
                additional_kwargs={
                    "model_used": self.model,
                    "local_model_metadata": {
                        "total_duration": result.get("total_duration"),
                        "load_duration": result.get("load_duration"),
                        "eval_count": result.get("eval_count"),
                    },
                },
            )
        except Exception as e:
            logger.error(f"Local model error: {e}")
            raise

    def _messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Convert messages to a single prompt string"""
        prompt_parts = []

        for message in messages:
            if isinstance(message, SystemMessage):
                prompt_parts.append(f"System: {message.content}")
            elif isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")

        # Add final prompt indicator
        prompt_parts.append("Assistant:")

        return "\n\n".join(prompt_parts)

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> AIMessage:
        """Async generation - not implemented yet"""
        raise NotImplementedError(
            "Async generation not yet implemented for local models"
        )

    def get_num_tokens(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // 4

    def __del__(self):
        """Cleanup HTTP client"""
        if hasattr(self, "_client"):
            self._client.close()
