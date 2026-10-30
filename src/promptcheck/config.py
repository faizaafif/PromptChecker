"""YAML suite loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SuiteConfig:
    """Validated minimal suite configuration."""

    suite_name: str
    provider: dict[str, Any]
    tests: list[dict[str, Any]]


@dataclass(frozen=True)
class ComparisonConfig:
    """Validated configuration for a multi-provider comparison suite."""

    suite_name: str
    providers: list[dict[str, Any]]
    tests: list[dict[str, Any]]


def load_suite(path: str | Path) -> SuiteConfig:
    """Load and validate a YAML suite file.

    Raises:
        FileNotFoundError: If the suite path does not exist.
        ValueError: If the YAML is empty or fails validation.
        yaml.YAMLError: If the YAML is invalid.
    """
    suite_path = Path(path)
    if not suite_path.is_file():
        raise FileNotFoundError(f"Suite file not found: {suite_path}")

    raw = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    if raw is None:
        raise ValueError("Suite file is empty.")
    if not isinstance(raw, dict):
        raise ValueError("Suite root must be a mapping (YAML dictionary).")

    suite_name = _require_str(raw, "suite_name")
    provider = _require_dict(raw, "provider")
    tests = _require_list(raw, "tests")
    _validate_tests(tests)

    return SuiteConfig(suite_name=suite_name, provider=provider, tests=tests)


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{key}' must be a non-empty string.")
    return value


def _require_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"'{key}' must be a mapping (YAML dictionary).")
    return value


def _require_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"'{key}' must be a non-empty list.")
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"'{key}[{index}]' must be a mapping.")
    return value


def _validate_tests(tests: list[dict[str, Any]]) -> None:
    for index, test in enumerate(tests, start=1):
        _require_str(test, "name")
        _require_str(test, "prompt")
        expect = _require_dict(test, "expect")
        _require_str(expect, "evaluator")
        if "value" not in expect:
            raise ValueError(f"tests[{index}].expect.value is required.")


def _validate_providers(providers: list[dict[str, Any]]) -> None:
    """Validate that each provider in the list has a 'name' string."""
    for index, prov in enumerate(providers, start=1):
        if not isinstance(prov, dict):
            raise ValueError(f"providers[{index}] must be a mapping.")
        name = prov.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"providers[{index}].name must be a non-empty string."
            )


def load_comparison(path: str | Path) -> ComparisonConfig:
    """Load and validate a multi-provider comparison YAML suite.

    The YAML must have a 'providers' key (list of at least 2 providers)
    instead of a single 'provider' key.

    Raises:
        FileNotFoundError: If the suite path does not exist.
        ValueError: If the YAML is empty or fails validation.
        yaml.YAMLError: If the YAML is invalid.
    """
    suite_path = Path(path)
    if not suite_path.is_file():
        raise FileNotFoundError(f"Suite file not found: {suite_path}")

    raw = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    if raw is None:
        raise ValueError("Suite file is empty.")
    if not isinstance(raw, dict):
        raise ValueError("Suite root must be a mapping (YAML dictionary).")

    suite_name = _require_str(raw, "suite_name")

    providers = raw.get("providers")
    if not isinstance(providers, list) or len(providers) < 2:
        raise ValueError(
            "'providers' must be a list with at least 2 providers."
        )
    _validate_providers(providers)

    tests = _require_list(raw, "tests")
    _validate_tests(tests)

    return ComparisonConfig(
        suite_name=suite_name,
        providers=providers,
        tests=tests,
    )
