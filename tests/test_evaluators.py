"""Tests for evaluators."""

import pytest

from promptcheck.evaluators import evaluate
from promptcheck.models import EvalResult


class TestExactMatch:
    """Tests for the exact_match evaluator."""

    def test_pass_when_equal(self):
        result = evaluate("exact_match", "hello", "hello")
        assert result.passed is True
        assert result.evaluator == "exact_match"
        assert result.message == ""

    def test_fail_when_different(self):
        result = evaluate("exact_match", "hello", "world")
        assert result.passed is False
        assert "Expected exactly" in result.message

    def test_case_sensitive(self):
        result = evaluate("exact_match", "Hello", "hello")
        assert result.passed is False

    def test_empty_strings_match(self):
        result = evaluate("exact_match", "", "")
        assert result.passed is True

    def test_whitespace_matters(self):
        result = evaluate("exact_match", "hello ", "hello")
        assert result.passed is False

    def test_numeric_expected_cast_to_str(self):
        result = evaluate("exact_match", 42, "42")
        assert result.passed is True


class TestContains:
    """Tests for the contains evaluator."""

    def test_pass_when_substring(self):
        result = evaluate("contains", "world", "hello world")
        assert result.passed is True
        assert result.message == ""

    def test_fail_when_not_substring(self):
        result = evaluate("contains", "xyz", "hello world")
        assert result.passed is False
        assert "to be contained in" in result.message

    def test_case_sensitive(self):
        result = evaluate("contains", "Hello", "hello world")
        assert result.passed is False

    def test_full_match_passes(self):
        result = evaluate("contains", "hello", "hello")
        assert result.passed is True

    def test_empty_expected_always_passes(self):
        result = evaluate("contains", "", "anything")
        assert result.passed is True


class TestUnknownEvaluator:
    """Test that unknown evaluators raise ValueError."""

    def test_unknown_evaluator(self):
        with pytest.raises(ValueError, match="Unknown evaluator"):
            evaluate("nonexistent", "a", "b")
