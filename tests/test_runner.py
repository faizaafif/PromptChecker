"""Tests for the runner."""

import pytest
import tempfile
from pathlib import Path

from promptcheck.config import load_suite, SuiteConfig
from promptcheck.runner import run_suite, parse_test_cases


def _make_suite(responses: dict, tests: list) -> SuiteConfig:
    """Helper: build a SuiteConfig without touching YAML."""
    return SuiteConfig(
        suite_name="test",
        provider={"name": "mock", "config": {"responses": responses}},
        tests=tests,
    )


class TestRunSuiteHappyPath:
    """Test runner with passing tests."""

    def test_single_passing_test(self):
        suite = _make_suite(
            responses={"hi": "hello"},
            tests=[{
                "name": "t1",
                "prompt": "hi",
                "expect": {"evaluator": "exact_match", "value": "hello"},
            }],
        )
        result = run_suite(suite)
        assert result.total == 1
        assert result.passed == 1
        assert result.failed == 0
        assert result.errors == 0
        assert result.duration_seconds >= 0
        assert len(result.test_results) == 1

    def test_multiple_passing_tests(self):
        suite = _make_suite(
            responses={"a": "alpha", "b": "beta"},
            tests=[
                {"name": "t1", "prompt": "a", "expect": {"evaluator": "exact_match", "value": "alpha"}},
                {"name": "t2", "prompt": "b", "expect": {"evaluator": "contains", "value": "bet"}},
            ],
        )
        result = run_suite(suite)
        assert result.total == 2
        assert result.passed == 2


class TestRunSuiteFailures:
    """Test runner with failing and erroring tests."""

    def test_failing_test(self):
        suite = _make_suite(
            responses={"hi": "hello"},
            tests=[{
                "name": "t1",
                "prompt": "hi",
                "expect": {"evaluator": "exact_match", "value": "wrong"},
            }],
        )
        result = run_suite(suite)
        assert result.passed == 0
        assert result.failed == 1

    def test_missing_mock_response_is_error(self):
        suite = _make_suite(
            responses={},
            tests=[{
                "name": "t1",
                "prompt": "missing",
                "expect": {"evaluator": "exact_match", "value": "anything"},
            }],
        )
        result = run_suite(suite)
        assert result.errors == 1
        assert result.passed == 0

    def test_suite_continues_after_error(self):
        suite = _make_suite(
            responses={"b": "beta"},
            tests=[
                {"name": "t1", "prompt": "missing", "expect": {"evaluator": "exact_match", "value": "x"}},
                {"name": "t2", "prompt": "b", "expect": {"evaluator": "exact_match", "value": "beta"}},
            ],
        )
        result = run_suite(suite)
        assert result.total == 2
        assert result.errors == 1
        assert result.passed == 1

    def test_unknown_provider_raises(self):
        suite = SuiteConfig(
            suite_name="bad",
            provider={"name": "nonexistent", "config": {}},
            tests=[{"name": "t1", "prompt": "x", "expect": {"evaluator": "exact_match", "value": "y"}}],
        )
        with pytest.raises(ValueError, match="Unknown provider"):
            run_suite(suite)


class TestParseTestCases:
    """Test the raw-dict-to-TestCase converter."""

    def test_parses_correctly(self):
        raw = [{"name": "t1", "prompt": "p", "expect": {"evaluator": "exact_match", "value": "v"}}]
        cases = parse_test_cases(raw)
        assert len(cases) == 1
        assert cases[0].name == "t1"
        assert cases[0].prompt == "p"
        assert cases[0].evaluator == "exact_match"
        assert cases[0].expected_value == "v"
