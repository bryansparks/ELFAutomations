"""
LLM Providers for ElfAutomations

Available providers:
- OpenRouter: Intelligent routing to 100+ models
- Local: Direct connection to local SLMs
"""

from .openrouter import ChatLocalModel, ChatOpenRouter

__all__ = ["ChatOpenRouter", "ChatLocalModel"]
