"""Ollama provider for PromptCheck.

Sends prompts to a local Ollama instance via its REST API.
This is a real model provider — it requires Ollama to be running locally.
"""

from __future__ import annotations

from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

from promptcheck.models import ProviderResult
from promptcheck.providers import BaseProvider

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_TIMEOUT = 30


class OllamaProvider(BaseProvider):
    """Sends prompts to a local Ollama instance.

    Config example (from YAML):
        provider:
          name: "ollama"
          config:
            model: "llama3.2"
            base_url: "http://localhost:11434"
            timeout: 30
    """

    def __init__(self, config: dict[str, Any]) -> None:
        if requests is None:
            raise ImportError(
                "The 'requests' package is required for the Ollama provider. "
                "Install it with: pip install requests"
            )

        model = config.get("model")
        if not isinstance(model, str) or not model.strip():
            raise ValueError(
                "OllamaProvider requires a 'model' string in config "
                "(e.g. 'llama3.2')."
            )

        self._model: str = model
        self._base_url: str = config.get("base_url", _DEFAULT_BASE_URL)
        self._timeout: int = config.get("timeout", _DEFAULT_TIMEOUT)

    def send(self, prompt: str) -> ProviderResult:
        """Send a prompt to Ollama and return the response.

        Returns a ProviderResult with an error (not an exception) if:
        - Ollama is not running (connection error).
        - The HTTP response is not 200.
        - The response body is missing the expected field.
        """
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            resp = requests.post(url, json=payload, timeout=self._timeout)
        except requests.ConnectionError:
            return ProviderResult(
                response="",
                error=(
                    f"Could not connect to Ollama at {self._base_url}. "
                    "Is Ollama running?"
                ),
            )
        except requests.Timeout:
            return ProviderResult(
                response="",
                error=f"Ollama request timed out after {self._timeout}s.",
            )
        except requests.RequestException as exc:
            return ProviderResult(
                response="",
                error=f"Ollama request failed: {exc}",
            )

        if resp.status_code != 200:
            return ProviderResult(
                response="",
                error=(
                    f"Ollama returned HTTP {resp.status_code}: "
                    f"{resp.text[:200]}"
                ),
            )

        try:
            body = resp.json()
        except ValueError:
            return ProviderResult(
                response="",
                error="Ollama returned invalid JSON.",
            )

        response_text = body.get("response", "")
        if not isinstance(response_text, str):
            return ProviderResult(
                response="",
                error="Ollama response missing 'response' field.",
            )

        return ProviderResult(response=response_text)
