"""Tests for the mock provider."""

import pytest

from promptcheck.providers import BaseProvider
from promptcheck.providers.mock import MockProvider


class TestMockProvider:
    """Tests for MockProvider."""

    def test_returns_configured_response(self):
        provider = MockProvider({"responses": {"hi": "hello"}})
        result = provider.send("hi")
        assert result.response == "hello"
        assert result.error is None

    def test_missing_prompt_returns_error(self):
        provider = MockProvider({"responses": {"hi": "hello"}})
        result = provider.send("unknown")
        assert result.response == ""
        assert result.error is not None
        assert "no response configured" in result.error

    def test_empty_responses_always_errors(self):
        provider = MockProvider({"responses": {}})
        result = provider.send("anything")
        assert result.error is not None

    def test_invalid_config_raises(self):
        with pytest.raises(ValueError, match="requires 'responses' mapping"):
            MockProvider({"wrong_key": "value"})

    def test_missing_config_raises(self):
        with pytest.raises(ValueError, match="requires 'responses' mapping"):
            MockProvider({})


class TestBaseProviderFactory:
    """Tests for BaseProvider.create()."""

    def test_create_mock(self):
        provider = BaseProvider.create("mock", {"responses": {"a": "b"}})
        assert isinstance(provider, MockProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            BaseProvider.create("nonexistent", {})
