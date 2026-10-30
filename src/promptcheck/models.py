"""Data models for PromptCheck."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TestCase:
    """A single prompt test case parsed from a YAML suite."""

    name: str
    prompt: str
    evaluator: str
    expected_value: Any


@dataclass(frozen=True)
class ProviderResult:
    """The response returned by a provider for a single prompt."""

    response: str
    error: str | None = None


@dataclass(frozen=True)
class EvalResult:
    """The outcome of evaluating a provider response against expectations."""

    passed: bool
    evaluator: str
    expected: Any
    actual: str
    message: str = ""


@dataclass(frozen=True)
class TestResult:
    """The combined result of running and evaluating one test case."""

    test_name: str
    prompt: str
    provider_result: ProviderResult
    eval_result: EvalResult | None
    duration_seconds: float
    error: str | None = None


@dataclass
class SuiteResult:
    """The aggregated result of running an entire test suite."""

    suite_name: str
    provider_name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    test_results: list[TestResult] = field(default_factory=list)


@dataclass
class ComparisonResult:
    """The result of running the same tests against multiple providers."""

    suite_name: str
    provider_count: int = 0
    total_duration_seconds: float = 0.0
    suite_results: list[SuiteResult] = field(default_factory=list)
