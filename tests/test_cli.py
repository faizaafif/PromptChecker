"""Tests for the CLI."""

import pytest

from promptcheck.cli import main


class TestCLIRun:
    """Test the 'run' subcommand via main()."""

    def test_valid_suite_returns_zero(self, tmp_path):
        suite = tmp_path / "suite.yaml"
        suite.write_text("""
suite_name: "cli-test"
provider:
  name: "mock"
  config:
    responses:
      hi: "hello"
tests:
  - name: "t1"
    prompt: "hi"
    expect:
      evaluator: "exact_match"
      value: "hello"
""", encoding="utf-8")
        exit_code = main(["run", str(suite)])
        assert exit_code == 0

    def test_failing_test_returns_one(self, tmp_path):
        suite = tmp_path / "suite.yaml"
        suite.write_text("""
suite_name: "cli-fail"
provider:
  name: "mock"
  config:
    responses:
      hi: "hello"
tests:
  - name: "t1"
    prompt: "hi"
    expect:
      evaluator: "exact_match"
      value: "wrong"
""", encoding="utf-8")
        exit_code = main(["run", str(suite)])
        assert exit_code == 1

    def test_missing_file_returns_two(self):
        exit_code = main(["run", "nonexistent.yaml"])
        assert exit_code == 2

    def test_report_flag_writes_json(self, tmp_path):
        suite = tmp_path / "suite.yaml"
        suite.write_text("""
suite_name: "report-test"
provider:
  name: "mock"
  config:
    responses:
      hi: "hello"
tests:
  - name: "t1"
    prompt: "hi"
    expect:
      evaluator: "exact_match"
      value: "hello"
""", encoding="utf-8")
        report = tmp_path / "report.json"
        exit_code = main(["run", str(suite), "--report", str(report)])
        assert exit_code == 0
        assert report.exists()


class TestCLINoCommand:
    """Test CLI behavior with no subcommand."""

    def test_no_args_returns_zero(self):
        exit_code = main([])
        assert exit_code == 0
