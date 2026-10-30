"""JSON reporter for PromptCheck."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from promptcheck.models import ComparisonResult, SuiteResult


def to_dict(result: SuiteResult | ComparisonResult) -> dict:
    """Convert a SuiteResult or ComparisonResult to a plain dictionary."""
    return asdict(result)


def to_json(result: SuiteResult | ComparisonResult, indent: int = 2) -> str:
    """Serialize a result to a JSON string."""
    return json.dumps(to_dict(result), indent=indent, ensure_ascii=False)


def write_report(
    result: SuiteResult | ComparisonResult,
    path: str | Path,
) -> Path:
    """Write a JSON report to the given file path.

    Creates parent directories if they don't exist.

    Returns:
        The resolved Path to the written report file.
    """
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(to_json(result), encoding="utf-8")
    return report_path.resolve()
