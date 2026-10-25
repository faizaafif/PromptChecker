"""Tests for the Ollama provider (mocked HTTP)."""

import pytest
import requests as real_requests
from unittest.mock import patch, MagicMock

from promptcheck.providers import BaseProvider
from promptcheck.providers.ollama import OllamaProvider


def _patch_exception_classes(mock_requests):
    """Set real exception classes on the mocked requests module."""
    mock_requests.ConnectionError = real_requests.ConnectionError
    mock_requests.Timeout = real_requests.Timeout
    mock_requests.RequestException = real_requests.RequestException


class TestOllamaProviderInit:
    """Tests for OllamaProvider initialization."""

    def test_valid_config(self):
        provider = OllamaProvider({"model": "llama3.2"})
        assert provider._model == "llama3.2"
        assert provider._base_url == "http://localhost:11434"
        assert provider._timeout == 30

    def test_custom_base_url_and_timeout(self):
        provider = OllamaProvider({
            "model": "llama3.2",
            "base_url": "http://myhost:1234",
            "timeout": 60,
        })
        assert provider._base_url == "http://myhost:1234"
        assert provider._timeout == 60

    def test_missing_model_raises(self):
        with pytest.raises(ValueError, match="requires a 'model' string"):
            OllamaProvider({})

    def test_empty_model_raises(self):
        with pytest.raises(ValueError, match="requires a 'model' string"):
            OllamaProvider({"model": ""})


class TestOllamaProviderSend:
    """Tests for OllamaProvider.send() with mocked HTTP."""

    @patch("promptcheck.providers.ollama.requests")
    def test_successful_response(self, mock_requests):
        _patch_exception_classes(mock_requests)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Hello from Ollama"}
        mock_requests.post.return_value = mock_resp

        provider = OllamaProvider({"model": "llama3.2"})
        result = provider.send("hi")

        assert result.response == "Hello from Ollama"
        assert result.error is None
        mock_requests.post.assert_called_once()

    @patch("promptcheck.providers.ollama.requests")
    def test_connection_error(self, mock_requests):
        _patch_exception_classes(mock_requests)
        mock_requests.post.side_effect = real_requests.ConnectionError()

        provider = OllamaProvider({"model": "llama3.2"})
        result = provider.send("hi")

        assert result.response == ""
        assert "Could not connect" in result.error

    @patch("promptcheck.providers.ollama.requests")
    def test_timeout_error(self, mock_requests):
        _patch_exception_classes(mock_requests)
        mock_requests.post.side_effect = real_requests.Timeout()

        provider = OllamaProvider({"model": "llama3.2"})
        result = provider.send("hi")

        assert result.response == ""
        assert "timed out" in result.error

    @patch("promptcheck.providers.ollama.requests")
    def test_http_error_status(self, mock_requests):
        _patch_exception_classes(mock_requests)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_requests.post.return_value = mock_resp

        provider = OllamaProvider({"model": "llama3.2"})
        result = provider.send("hi")

        assert result.response == ""
        assert "HTTP 500" in result.error

    @patch("promptcheck.providers.ollama.requests")
    def test_invalid_json_response(self, mock_requests):
        _patch_exception_classes(mock_requests)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("bad json")
        mock_requests.post.return_value = mock_resp

        provider = OllamaProvider({"model": "llama3.2"})
        result = provider.send("hi")

        assert result.response == ""
        assert "invalid JSON" in result.error

    @patch("promptcheck.providers.ollama.requests")
    def test_missing_response_field(self, mock_requests):
        _patch_exception_classes(mock_requests)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"other": "data"}
        mock_requests.post.return_value = mock_resp

        provider = OllamaProvider({"model": "llama3.2"})
        result = provider.send("hi")

        # Empty string is returned when "response" key is missing
        assert result.response == ""


class TestOllamaFactory:
    """Test that the factory creates OllamaProvider."""

    def test_create_ollama(self):
        provider = BaseProvider.create("ollama", {"model": "llama3.2"})
        assert isinstance(provider, OllamaProvider)
