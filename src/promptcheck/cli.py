"""Command-line interface for PromptCheck."""

from __future__ import annotations

import argparse

from promptcheck.config import load_suite
from promptcheck.runner import run_suite


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="promptcheck",
        description="Run repeatable prompt tests against model providers.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run a YAML prompt test suite.",
    )
    run_parser.add_argument("suite", help="Path to a YAML suite file.")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the PromptCheck CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            suite = load_suite(args.suite)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}")
            return 2
        except Exception as exc:  # pragma: no cover
            print(f"Unexpected error loading suite: {exc}")
            return 1

        try:
            result = run_suite(suite)
        except Exception as exc:
            print(f"Error running suite: {exc}")
            return 1

        # Print summary
        print(f"Suite: {result.suite_name}")
        print(f"Provider: {result.provider_name}")
        print(f"Total: {result.total}  "
              f"Passed: {result.passed}  "
              f"Failed: {result.failed}  "
              f"Errors: {result.errors}")
        print(f"Duration: {result.duration_seconds:.4f}s")

        for tr in result.test_results:
            status = "ERROR"
            if tr.error:
                status = "ERROR"
            elif tr.eval_result and tr.eval_result.passed:
                status = "PASS"
            else:
                status = "FAIL"
            detail = ""
            if tr.error:
                detail = f" - {tr.error}"
            elif tr.eval_result and tr.eval_result.message:
                detail = f" - {tr.eval_result.message}"
            print(f"  [{status}] {tr.test_name}{detail}")

        # Exit code: 0 if all passed, 1 if any failed or errored
        if result.failed > 0 or result.errors > 0:
            return 1
        return 0

    parser.print_help()
    return 0
