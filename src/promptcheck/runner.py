"""Runner: coordinates test execution, timing, and result collection."""

from __future__ import annotations

import time
from typing import Any

from promptcheck.config import SuiteConfig
from promptcheck.evaluators import evaluate
from promptcheck.models import (
    EvalResult,
    ProviderResult,
    SuiteResult,
    TestCase,
    TestResult,
)
from promptcheck.providers import BaseProvider


def parse_test_cases(raw_tests: list[dict[str, Any]]) -> list[TestCase]:
    """Convert raw YAML test dicts into TestCase objects."""
    cases = []
    for t in raw_tests:
        cases.append(
            TestCase(
                name=t["name"],
                prompt=t["prompt"],
                evaluator=t["expect"]["evaluator"],
                expected_value=t["expect"]["value"],
            )
        )
    return cases


def run_suite(suite: SuiteConfig) -> SuiteResult:
    """Run all tests in a suite and return the aggregated result.

    Steps for each test:
    1. Send the prompt to the provider.
    2. If the provider returned an error, record it and skip evaluation.
    3. Evaluate the response against the expected value.
    4. Record timing for each test.

    The suite continues even if one test fails or errors.
    """
    provider_name = suite.provider.get("name", "unknown")
    provider_config = suite.provider.get("config", {})
    provider = BaseProvider.create(provider_name, provider_config)

    test_cases = parse_test_cases(suite.tests)

    result = SuiteResult(
        suite_name=suite.suite_name,
        provider_name=provider_name,
        total=len(test_cases),
    )

    suite_start = time.monotonic()

    for case in test_cases:
        test_result = _run_single_test(case, provider)
        result.test_results.append(test_result)

        if test_result.error:
            result.errors += 1
        elif test_result.eval_result and test_result.eval_result.passed:
            result.passed += 1
        else:
            result.failed += 1

    result.duration_seconds = round(time.monotonic() - suite_start, 6)

    return result


def _run_single_test(case: TestCase, provider: BaseProvider) -> TestResult:
    """Run one test case: send prompt, evaluate, measure time."""
    start = time.monotonic()

    try:
        provider_result = provider.send(case.prompt)
    except Exception as exc:
        duration = round(time.monotonic() - start, 6)
        return TestResult(
            test_name=case.name,
            prompt=case.prompt,
            provider_result=ProviderResult(response="", error=str(exc)),
            eval_result=None,
            duration_seconds=duration,
            error=f"Provider error: {exc}",
        )

    # If the provider returned an error, skip evaluation.
    if provider_result.error:
        duration = round(time.monotonic() - start, 6)
        return TestResult(
            test_name=case.name,
            prompt=case.prompt,
            provider_result=provider_result,
            eval_result=None,
            duration_seconds=duration,
            error=provider_result.error,
        )

    # Evaluate the response.
    try:
        eval_result = evaluate(
            case.evaluator, case.expected_value, provider_result.response
        )
    except Exception as exc:
        duration = round(time.monotonic() - start, 6)
        return TestResult(
            test_name=case.name,
            prompt=case.prompt,
            provider_result=provider_result,
            eval_result=None,
            duration_seconds=duration,
            error=f"Evaluator error: {exc}",
        )

    duration = round(time.monotonic() - start, 6)
    return TestResult(
        test_name=case.name,
        prompt=case.prompt,
        provider_result=provider_result,
        eval_result=eval_result,
        duration_seconds=duration,
    )
