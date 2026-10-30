"""Tests for the multi-provider comparison feature."""

import json
from pathlib import Path

import pytest
import yaml

from promptcheck.config import ComparisonConfig, load_comparison
from promptcheck.models import ComparisonResult, SuiteResult
from promptcheck.reporters import to_dict, to_json, write_report
from promptcheck.runner import run_comparison


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _write_yaml(tmp_path: Path, data: dict, filename: str = "suite.yaml") -> Path:
    """Write a dict as YAML to a temp file and return its path."""
    p = tmp_path / filename
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


VALID_COMPARISON = {
    "suite_name": "compare-test",
    "providers": [
        {"name": "mock", "config": {"responses": {"hi": "Hello"}}},
        {"name": "mock", "config": {"responses": {"hi": "Hey there"}}},
    ],
    "tests": [
        {
            "name": "greeting",
            "prompt": "hi",
            "expect": {"evaluator": "contains", "value": "He"},
        },
    ],
}


# ---------------------------------------------------------------------------
# Config loading tests
# ---------------------------------------------------------------------------

class TestLoadComparison:
    """Tests for load_comparison() validation."""

    def test_valid_comparison(self, tmp_path):
        path = _write_yaml(tmp_path, VALID_COMPARISON)
        cfg = load_comparison(path)
        assert isinstance(cfg, ComparisonConfig)
        assert cfg.suite_name == "compare-test"
        assert len(cfg.providers) == 2
        assert len(cfg.tests) == 1

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_comparison("nonexistent.yaml")

    def test_missing_providers_key(self, tmp_path):
        data = {**VALID_COMPARISON, "providers": None}
        path = _write_yaml(tmp_path, data)
        with pytest.raises(ValueError, match="providers"):
            load_comparison(path)

    def test_single_provider_rejected(self, tmp_path):
        data = {
            **VALID_COMPARISON,
            "providers": [
                {"name": "mock", "config": {"responses": {"hi": "Hello"}}},
            ],
        }
        path = _write_yaml(tmp_path, data)
        with pytest.raises(ValueError, match="at least 2"):
            load_comparison(path)

    def test_provider_missing_name(self, tmp_path):
        data = {
            **VALID_COMPARISON,
            "providers": [
                {"config": {}},
                {"name": "mock", "config": {}},
            ],
        }
        path = _write_yaml(tmp_path, data)
        with pytest.raises(ValueError, match="name"):
            load_comparison(path)

    def test_empty_suite_name(self, tmp_path):
        data = {**VALID_COMPARISON, "suite_name": ""}
        path = _write_yaml(tmp_path, data)
        with pytest.raises(ValueError, match="suite_name"):
            load_comparison(path)


# ---------------------------------------------------------------------------
# Runner tests
# ---------------------------------------------------------------------------

class TestRunComparison:
    """Tests for run_comparison()."""

    def test_runs_all_providers(self, tmp_path):
        path = _write_yaml(tmp_path, VALID_COMPARISON)
        cfg = load_comparison(path)
        result = run_comparison(cfg)

        assert isinstance(result, ComparisonResult)
        assert result.suite_name == "compare-test"
        assert result.provider_count == 2
        assert len(result.suite_results) == 2
        assert result.total_duration_seconds > 0

    def test_each_provider_gets_own_suite_result(self, tmp_path):
        path = _write_yaml(tmp_path, VALID_COMPARISON)
        cfg = load_comparison(path)
        result = run_comparison(cfg)

        for sr in result.suite_results:
            assert isinstance(sr, SuiteResult)
            assert sr.suite_name == "compare-test"
            assert sr.total == 1

    def test_both_providers_pass_contains(self, tmp_path):
        """Both mock providers return something containing 'He'."""
        path = _write_yaml(tmp_path, VALID_COMPARISON)
        cfg = load_comparison(path)
        result = run_comparison(cfg)

        for sr in result.suite_results:
            assert sr.passed == 1
            assert sr.failed == 0
            assert sr.errors == 0

    def test_one_provider_fails(self, tmp_path):
        data = {
            "suite_name": "partial-fail",
            "providers": [
                {"name": "mock", "config": {"responses": {"hi": "Hello"}}},
                {"name": "mock", "config": {"responses": {"hi": "Yo"}}},
            ],
            "tests": [
                {
                    "name": "check",
                    "prompt": "hi",
                    "expect": {"evaluator": "exact_match", "value": "Hello"},
                },
            ],
        }
        path = _write_yaml(tmp_path, data)
        cfg = load_comparison(path)
        result = run_comparison(cfg)

        # First provider: exact match passes
        assert result.suite_results[0].passed == 1
        # Second provider: exact match fails ("Yo" != "Hello")
        assert result.suite_results[1].failed == 1


# ---------------------------------------------------------------------------
# Reporter tests
# ---------------------------------------------------------------------------

class TestComparisonReporter:
    """Tests for ComparisonResult serialization."""

    def test_to_dict(self, tmp_path):
        path = _write_yaml(tmp_path, VALID_COMPARISON)
        cfg = load_comparison(path)
        result = run_comparison(cfg)
        d = to_dict(result)

        assert d["suite_name"] == "compare-test"
        assert d["provider_count"] == 2
        assert len(d["suite_results"]) == 2

    def test_to_json_roundtrip(self, tmp_path):
        path = _write_yaml(tmp_path, VALID_COMPARISON)
        cfg = load_comparison(path)
        result = run_comparison(cfg)
        j = to_json(result)
        parsed = json.loads(j)

        assert parsed["suite_name"] == "compare-test"
        assert len(parsed["suite_results"]) == 2

    def test_write_report(self, tmp_path):
        path = _write_yaml(tmp_path, VALID_COMPARISON)
        cfg = load_comparison(path)
        result = run_comparison(cfg)

        report_path = write_report(result, tmp_path / "report.json")
        assert report_path.exists()
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["provider_count"] == 2


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

class TestCompareCLI:
    """Tests for the 'compare' CLI subcommand."""

    def test_compare_success(self, tmp_path, capsys):
        from promptcheck.cli import main

        path = _write_yaml(tmp_path, VALID_COMPARISON)
        exit_code = main(["compare", str(path)])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "compare-test" in output
        assert "Providers compared: 2" in output
        assert "[PASS]" in output

    def test_compare_with_report(self, tmp_path, capsys):
        from promptcheck.cli import main

        suite_path = _write_yaml(tmp_path, VALID_COMPARISON)
        report_path = tmp_path / "comp-report.json"
        exit_code = main(["compare", str(suite_path), "--report", str(report_path)])

        assert exit_code == 0
        assert report_path.exists()
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["provider_count"] == 2

    def test_compare_missing_file(self, capsys):
        from promptcheck.cli import main

        exit_code = main(["compare", "nonexistent.yaml"])
        assert exit_code == 2

    def test_compare_returns_1_on_failure(self, tmp_path, capsys):
        from promptcheck.cli import main

        data = {
            "suite_name": "fail-test",
            "providers": [
                {"name": "mock", "config": {"responses": {"x": "a"}}},
                {"name": "mock", "config": {"responses": {"x": "b"}}},
            ],
            "tests": [
                {
                    "name": "strict",
                    "prompt": "x",
                    "expect": {"evaluator": "exact_match", "value": "a"},
                },
            ],
        }
        path = _write_yaml(tmp_path, data)
        exit_code = main(["compare", str(path)])
        assert exit_code == 1
