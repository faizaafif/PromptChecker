"""Mock provider for PromptCheck.

Returns deterministic responses from a pre-configured mapping.
This is a test double — it does NOT call any AI model.
"""

from __future__ import annotations

from typing import Any

from promptcheck.models import ProviderResult
from promptcheck.providers import BaseProvider


class MockProvider(BaseProvider):
    """Looks up the prompt in a static response mapping.

    Config example (from YAML):
        config:
          responses:
            hello: "Hello world"
    """

    def __init__(self, config: dict[str, Any]) -> None:
        responses = config.get("responses")
        if not isinstance(responses, dict):
            raise ValueError(
                "MockProvider requires 'responses' mapping in config."
            )
        self._responses: dict[str, str] = responses

    def send(self, prompt: str) -> ProviderResult:
        """Return the pre-configured response for the prompt.

        If the prompt is not in the mapping, returns a ProviderResult
        with an error instead of raising an exception.
        """
        if prompt in self._responses:
            return ProviderResult(response=self._responses[prompt])

        return ProviderResult(
            response="",
            error=f"MockProvider: no response configured for prompt '{prompt}'",
        )
