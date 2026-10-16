"""Tests for the YAML config loader."""

import pytest
import tempfile
from pathlib import Path

from promptcheck.config import load_suite


def _write_yaml(tmp_path: Path, content: str) -> Path:
    """Helper: write YAML content to a temp file and return its path."""
    suite_file = tmp_path / "suite.yaml"
    suite_file.write_text(content, encoding="utf-8")
    return suite_file


class TestLoadSuiteHappyPath:
    """Test that valid YAML loads correctly."""

    def test_minimal_valid_suite(self, tmp_path):
        path = _write_yaml(tmp_path, """
suite_name: "test-suite"
provider:
  name: "mock"
  config:
    responses:
      hello: "world"
tests:
  - name: "t1"
    prompt: "hello"
    expect:
      evaluator: "exact_match"
      value: "world"
""")
        suite = load_suite(path)
        assert suite.suite_name == "test-suite"
        assert suite.provider["name"] == "mock"
        assert len(suite.tests) == 1
        assert suite.tests[0]["name"] == "t1"

    def test_multiple_tests(self, tmp_path):
        path = _write_yaml(tmp_path, """
suite_name: "multi"
provider:
  name: "mock"
  config:
    responses:
      a: "alpha"
      b: "beta"
tests:
  - name: "t1"
    prompt: "a"
    expect:
      evaluator: "exact_match"
      value: "alpha"
  - name: "t2"
    prompt: "b"
    expect:
      evaluator: "contains"
      value: "bet"
""")
        suite = load_suite(path)
        assert len(suite.tests) == 2


class TestLoadSuiteErrors:
    """Test that invalid YAML produces clear errors."""

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Suite file not found"):
            load_suite("nonexistent.yaml")

    def test_empty_file(self, tmp_path):
        path = _write_yaml(tmp_path, "")
        with pytest.raises(ValueError, match="Suite file is empty"):
            load_suite(path)

    def test_not_a_dict(self, tmp_path):
        path = _write_yaml(tmp_path, "- item1\n- item2")
        with pytest.raises(ValueError, match="Suite root must be a mapping"):
            load_suite(path)

    def test_missing_suite_name(self, tmp_path):
        path = _write_yaml(tmp_path, """
provider:
  name: "mock"
tests:
  - name: "t1"
    prompt: "hello"
    expect:
      evaluator: "exact_match"
      value: "world"
""")
        with pytest.raises(ValueError, match="'suite_name' must be a non-empty string"):
            load_suite(path)

    def test_missing_provider(self, tmp_path):
        path = _write_yaml(tmp_path, """
suite_name: "s"
tests:
  - name: "t1"
    prompt: "hello"
    expect:
      evaluator: "exact_match"
      value: "world"
""")
        with pytest.raises(ValueError, match="'provider' must be a mapping"):
            load_suite(path)

    def test_missing_tests(self, tmp_path):
        path = _write_yaml(tmp_path, """
suite_name: "s"
provider:
  name: "mock"
""")
        with pytest.raises(ValueError, match="'tests' must be a non-empty list"):
            load_suite(path)

    def test_empty_tests_list(self, tmp_path):
        path = _write_yaml(tmp_path, """
suite_name: "s"
provider:
  name: "mock"
tests: []
""")
        with pytest.raises(ValueError, match="'tests' must be a non-empty list"):
            load_suite(path)

    def test_test_missing_name(self, tmp_path):
        path = _write_yaml(tmp_path, """
suite_name: "s"
provider:
  name: "mock"
tests:
  - prompt: "hello"
    expect:
      evaluator: "exact_match"
      value: "world"
""")
        with pytest.raises(ValueError, match="'name' must be a non-empty string"):
            load_suite(path)

    def test_test_missing_expect(self, tmp_path):
        path = _write_yaml(tmp_path, """
suite_name: "s"
provider:
  name: "mock"
tests:
  - name: "t1"
    prompt: "hello"
""")
        with pytest.raises(ValueError, match="'expect' must be a mapping"):
            load_suite(path)

    def test_test_missing_expect_value(self, tmp_path):
        path = _write_yaml(tmp_path, """
suite_name: "s"
provider:
  name: "mock"
tests:
  - name: "t1"
    prompt: "hello"
    expect:
      evaluator: "exact_match"
""")
        with pytest.raises(ValueError, match="expect.value is required"):
            load_suite(path)
