"""Evaluator interface and built-in evaluators for PromptCheck."""

from __future__ import annotations

import re
from typing import Any

from promptcheck.models import EvalResult


def evaluate(evaluator: str, expected: Any, actual: str) -> EvalResult:
    """Dispatch to the correct evaluator by name.

    Raises:
        ValueError: If the evaluator name is unknown.
    """
    if evaluator == "exact_match":
        return _exact_match(expected, actual)
    if evaluator == "contains":
        return _contains(expected, actual)
    if evaluator == "starts_with":
        return _starts_with(expected, actual)
    if evaluator == "regex_match":
        return _regex_match(expected, actual)

    raise ValueError(f"Unknown evaluator: '{evaluator}'")


def _exact_match(expected: Any, actual: str) -> EvalResult:
    """Pass if the actual response exactly equals the expected value."""
    expected_str = str(expected)
    passed = actual == expected_str
    message = "" if passed else f"Expected exactly '{expected_str}', got '{actual}'."
    return EvalResult(
        passed=passed,
        evaluator="exact_match",
        expected=expected_str,
        actual=actual,
        message=message,
    )


def _contains(expected: Any, actual: str) -> EvalResult:
    """Pass if the expected value appears anywhere in the actual response."""
    expected_str = str(expected)
    passed = expected_str in actual
    message = "" if passed else f"Expected '{expected_str}' to be contained in '{actual}'."
    return EvalResult(
        passed=passed,
        evaluator="contains",
        expected=expected_str,
        actual=actual,
        message=message,
    )


def _starts_with(expected: Any, actual: str) -> EvalResult:
    """Pass if the actual response starts with the expected value."""
    expected_str = str(expected)
    passed = actual.startswith(expected_str)
    message = "" if passed else f"Expected response to start with '{expected_str}', got '{actual}'."
    return EvalResult(
        passed=passed,
        evaluator="starts_with",
        expected=expected_str,
        actual=actual,
        message=message,
    )


def _regex_match(expected: Any, actual: str) -> EvalResult:
    """Pass if the expected regex pattern matches anywhere in the actual response.

    Raises:
        ValueError: If the expected value is not a valid regex pattern.
    """
    pattern_str = str(expected)
    try:
        match = re.search(pattern_str, actual)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern '{pattern_str}': {exc}") from exc

    passed = match is not None
    message = "" if passed else f"Pattern '{pattern_str}' did not match '{actual}'."
    return EvalResult(
        passed=passed,
        evaluator="regex_match",
        expected=pattern_str,
        actual=actual,
        message=message,
    )
