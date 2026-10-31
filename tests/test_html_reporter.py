"""Tests for the HTML reporter."""

from pathlib import Path

import pytest
import yaml

from promptcheck.config import load_comparison, load_suite
from promptcheck.html_reporter import (
    comparison_to_html,
    suite_to_html,
    to_html,
    write_html_report,
)
from promptcheck.models import (
    ComparisonResult,
    EvalResult,
    ProviderResult,
    SuiteResult,
    TestResult,
)
from promptcheck.runner import run_comparison, run_suite


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(tmp_path: Path, data: dict, name: str = "suite.yaml") -> Path:
    p = tmp_path / name
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


def _make_suite_result() -> SuiteResult:
    """Build a small SuiteResult by hand for unit tests."""
    return SuiteResult(
        suite_name="html-test",
        provider_name="mock",
        total=2,
        passed=1,
        failed=1,
        errors=0,
        duration_seconds=0.0042,
        test_results=[
            TestResult(
                test_name="pass-test",
                prompt="hi",
                provider_result=ProviderResult(response="Hello"),
                eval_result=EvalResult(
                    passed=True,
                    evaluator="exact_match",
                    expected="Hello",
                    actual="Hello",
                    message="Match.",
                ),
                duration_seconds=0.001,
            ),
            TestResult(
                test_name="fail-test",
                prompt="bye",
                provider_result=ProviderResult(response="See ya"),
                eval_result=EvalResult(
                    passed=False,
                    evaluator="exact_match",
                    expected="Goodbye",
                    actual="See ya",
                    message="No match.",
                ),
                duration_seconds=0.002,
            ),
        ],
    )


COMPARE_YAML = {
    "suite_name": "html-compare",
    "providers": [
        {"name": "mock", "config": {"responses": {"hi": "Hello"}}},
        {"name": "mock", "config": {"responses": {"hi": "Hey"}}},
    ],
    "tests": [
        {
            "name": "greet",
            "prompt": "hi",
            "expect": {"evaluator": "exact_match", "value": "Hello"},
        },
    ],
}

SINGLE_YAML = {
    "suite_name": "html-single",
    "provider": {"name": "mock", "config": {"responses": {"hi": "Hello"}}},
    "tests": [
        {
            "name": "greet",
            "prompt": "hi",
            "expect": {"evaluator": "exact_match", "value": "Hello"},
        },
    ],
}


# ---------------------------------------------------------------------------
# suite_to_html tests
# ---------------------------------------------------------------------------

class TestSuiteToHtml:
    """Tests for single-provider HTML report generation."""

    def test_contains_doctype(self):
        result = _make_suite_result()
        html = suite_to_html(result)
        assert html.startswith("<!DOCTYPE html>")

    def test_contains_suite_name(self):
        result = _make_suite_result()
        html = suite_to_html(result)
        assert "html-test" in html

    def test_contains_pass_and_fail_badges(self):
        result = _make_suite_result()
        html = suite_to_html(result)
        assert "badge-pass" in html
        assert "badge-fail" in html

    def test_contains_test_names(self):
        result = _make_suite_result()
        html = suite_to_html(result)
        assert "pass-test" in html
        assert "fail-test" in html

    def test_contains_summary_stats(self):
        result = _make_suite_result()
        html = suite_to_html(result)
        assert "Total:" in html
        assert "Passed:" in html
        assert "Failed:" in html

    def test_escapes_html_in_prompt(self):
        """Ensure HTML special chars in prompts are escaped."""
        sr = SuiteResult(
            suite_name="escape-test",
            provider_name="mock",
            total=1,
            passed=1,
            test_results=[
                TestResult(
                    test_name="xss",
                    prompt="<script>alert('xss')</script>",
                    provider_result=ProviderResult(response="safe"),
                    eval_result=EvalResult(
                        passed=True,
                        evaluator="contains",
                        expected="safe",
                        actual="safe",
                    ),
                    duration_seconds=0.001,
                ),
            ],
        )
        html = suite_to_html(sr)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


# ---------------------------------------------------------------------------
# comparison_to_html tests
# ---------------------------------------------------------------------------

class TestComparisonToHtml:
    """Tests for multi-provider HTML report generation."""

    def test_contains_both_providers(self, tmp_path):
        path = _write_yaml(tmp_path, COMPARE_YAML)
        cfg = load_comparison(path)
        result = run_comparison(cfg)
        html = comparison_to_html(result)
        assert "Provider: mock" in html
        assert "Comparison Report" in html

    def test_contains_provider_count(self, tmp_path):
        path = _write_yaml(tmp_path, COMPARE_YAML)
        cfg = load_comparison(path)
        result = run_comparison(cfg)
        html = comparison_to_html(result)
        assert "Providers: 2" in html

    def test_shows_pass_and_fail(self, tmp_path):
        path = _write_yaml(tmp_path, COMPARE_YAML)
        cfg = load_comparison(path)
        result = run_comparison(cfg)
        html = comparison_to_html(result)
        # First mock: "Hello" == "Hello" → PASS
        assert "badge-pass" in html
        # Second mock: "Hey" != "Hello" → FAIL
        assert "badge-fail" in html


# ---------------------------------------------------------------------------
# to_html dispatch tests
# ---------------------------------------------------------------------------

class TestToHtmlDispatch:
    """Tests for the to_html() dispatch function."""

    def test_dispatches_suite_result(self):
        result = _make_suite_result()
        html = to_html(result)
        assert "PromptCheck Report" in html
        assert "Comparison" not in html

    def test_dispatches_comparison_result(self, tmp_path):
        path = _write_yaml(tmp_path, COMPARE_YAML)
        cfg = load_comparison(path)
        result = run_comparison(cfg)
        html = to_html(result)
        assert "Comparison Report" in html


# ---------------------------------------------------------------------------
# write_html_report tests
# ---------------------------------------------------------------------------

class TestWriteHtmlReport:
    """Tests for writing HTML reports to disk."""

    def test_writes_file(self, tmp_path):
        result = _make_suite_result()
        out = tmp_path / "report.html"
        returned = write_html_report(result, out)
        assert returned.exists()
        content = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_creates_parent_dirs(self, tmp_path):
        result = _make_suite_result()
        out = tmp_path / "deep" / "nested" / "report.html"
        returned = write_html_report(result, out)
        assert returned.exists()

    def test_comparison_report_file(self, tmp_path):
        path = _write_yaml(tmp_path, COMPARE_YAML)
        cfg = load_comparison(path)
        result = run_comparison(cfg)
        out = tmp_path / "comp.html"
        write_html_report(result, out)
        content = out.read_text(encoding="utf-8")
        assert "Comparison Report" in content


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

class TestHtmlCLI:
    """Tests for --html flag on run and compare commands."""

    def test_run_html_flag(self, tmp_path, capsys):
        from promptcheck.cli import main

        suite_path = _write_yaml(tmp_path, SINGLE_YAML)
        html_path = tmp_path / "out.html"
        exit_code = main(["run", str(suite_path), "--html", str(html_path)])

        assert exit_code == 0
        assert html_path.exists()
        output = capsys.readouterr().out
        assert "HTML report written to:" in output

    def test_compare_html_flag(self, tmp_path, capsys):
        from promptcheck.cli import main

        suite_path = _write_yaml(tmp_path, COMPARE_YAML)
        html_path = tmp_path / "comp.html"
        exit_code = main(["compare", str(suite_path), "--html", str(html_path)])

        # exit_code is 1 because second provider fails exact_match
        assert html_path.exists()
        content = html_path.read_text(encoding="utf-8")
        assert "Comparison Report" in content

    def test_run_both_flags(self, tmp_path, capsys):
        """--report and --html can be used together."""
        from promptcheck.cli import main

        suite_path = _write_yaml(tmp_path, SINGLE_YAML)
        json_path = tmp_path / "report.json"
        html_path = tmp_path / "report.html"
        exit_code = main([
            "run", str(suite_path),
            "--report", str(json_path),
            "--html", str(html_path),
        ])

        assert exit_code == 0
        assert json_path.exists()
        assert html_path.exists()


# ---------------------------------------------------------------------------
# Error test result rendering
# ---------------------------------------------------------------------------

class TestErrorRendering:
    """Test that error results render correctly in HTML."""

    def test_error_badge_in_html(self):
        sr = SuiteResult(
            suite_name="error-test",
            provider_name="mock",
            total=1,
            errors=1,
            test_results=[
                TestResult(
                    test_name="broken",
                    prompt="x",
                    provider_result=ProviderResult(response="", error="boom"),
                    eval_result=None,
                    duration_seconds=0.001,
                    error="Provider error: boom",
                ),
            ],
        )
        html = suite_to_html(sr)
        assert "badge-error" in html
        assert "Provider error: boom" in html
