"""Provider interface for PromptCheck."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from promptcheck.models import ProviderResult


class BaseProvider(ABC):
    """Abstract base class that every provider must implement.

    A provider receives a prompt string and returns a ProviderResult.
    """

    @abstractmethod
    def send(self, prompt: str) -> ProviderResult:
        """Send a prompt and return a ProviderResult."""

    @staticmethod
    def create(name: str, config: dict[str, Any]) -> "BaseProvider":
        """Factory: create a provider by name.

        Raises:
            ValueError: If the provider name is unknown.
        """
        if name == "mock":
            from promptcheck.providers.mock import MockProvider

            return MockProvider(config)

        if name == "ollama":
            from promptcheck.providers.ollama import OllamaProvider

            return OllamaProvider(config)

        raise ValueError(f"Unknown provider: '{name}'")
