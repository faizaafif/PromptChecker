"""Tests for the JSON reporter."""

import json
import pytest
from pathlib import Path

from promptcheck.models import (
    EvalResult,
    ProviderResult,
    SuiteResult,
    TestResult,
)
from promptcheck.reporters import to_dict, to_json, write_report


def _make_suite_result() -> SuiteResult:
    """Helper: build a representative SuiteResult."""
    return SuiteResult(
        suite_name="test-suite",
        provider_name="mock",
        total=1,
        passed=1,
        failed=0,
        errors=0,
        duration_seconds=0.001,
        test_results=[
            TestResult(
                test_name="t1",
                prompt="hello",
                provider_result=ProviderResult(response="world"),
                eval_result=EvalResult(
                    passed=True,
                    evaluator="exact_match",
                    expected="world",
                    actual="world",
                ),
                duration_seconds=0.001,
            )
        ],
    )


class TestToDict:
    """Tests for to_dict conversion."""

    def test_returns_dict(self):
        result = to_dict(_make_suite_result())
        assert isinstance(result, dict)
        assert result["suite_name"] == "test-suite"
        assert result["total"] == 1
        assert len(result["test_results"]) == 1

    def test_nested_structure(self):
        result = to_dict(_make_suite_result())
        tr = result["test_results"][0]
        assert tr["test_name"] == "t1"
        assert tr["provider_result"]["response"] == "world"
        assert tr["eval_result"]["passed"] is True


class TestToJson:
    """Tests for JSON string serialization."""

    def test_valid_json(self):
        json_str = to_json(_make_suite_result())
        parsed = json.loads(json_str)
        assert parsed["suite_name"] == "test-suite"

    def test_unicode_support(self):
        sr = _make_suite_result()
        # Modify to include Unicode
        sr.suite_name = "tëst-süite-日本語"
        json_str = to_json(sr)
        assert "tëst-süite-日本語" in json_str


class TestWriteReport:
    """Tests for writing report files."""

    def test_writes_file(self, tmp_path):
        report_path = tmp_path / "report.json"
        result = write_report(_make_suite_result(), report_path)
        assert report_path.exists()
        content = json.loads(report_path.read_text(encoding="utf-8"))
        assert content["suite_name"] == "test-suite"

    def test_creates_parent_dirs(self, tmp_path):
        report_path = tmp_path / "nested" / "dir" / "report.json"
        write_report(_make_suite_result(), report_path)
        assert report_path.exists()

    def test_returns_resolved_path(self, tmp_path):
        report_path = tmp_path / "report.json"
        result = write_report(_make_suite_result(), report_path)
        assert result == report_path.resolve()
