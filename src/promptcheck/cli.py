"""Command-line interface for PromptCheck."""

from __future__ import annotations

import argparse

from promptcheck.config import load_comparison, load_suite
from promptcheck.html_reporter import write_html_report
from promptcheck.reporters import write_report
from promptcheck.runner import run_comparison, run_suite


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
    run_parser.add_argument(
        "--report",
        default=None,
        help="Path to write a JSON report file.",
    )
    run_parser.add_argument(
        "--html",
        default=None,
        help="Path to write an HTML report file.",
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="Run the same tests against multiple providers.",
    )
    compare_parser.add_argument("suite", help="Path to a comparison YAML file.")
    compare_parser.add_argument(
        "--report",
        default=None,
        help="Path to write a JSON comparison report.",
    )
    compare_parser.add_argument(
        "--html",
        default=None,
        help="Path to write an HTML comparison report.",
    )

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

        # Write JSON report if requested
        if args.report:
            try:
                report_path = write_report(result, args.report)
                print(f"Report written to: {report_path}")
            except Exception as exc:
                print(f"Error writing report: {exc}")
                return 1

        # Write HTML report if requested
        if args.html:
            try:
                html_path = write_html_report(result, args.html)
                print(f"HTML report written to: {html_path}")
            except Exception as exc:
                print(f"Error writing HTML report: {exc}")
                return 1

        # Exit code: 0 if all passed, 1 if any failed or errored
        if result.failed > 0 or result.errors > 0:
            return 1
        return 0

    if args.command == "compare":
        try:
            comparison = load_comparison(args.suite)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}")
            return 2
        except Exception as exc:  # pragma: no cover
            print(f"Unexpected error loading suite: {exc}")
            return 1

        try:
            comp_result = run_comparison(comparison)
        except Exception as exc:
            print(f"Error running comparison: {exc}")
            return 1

        # Print comparison summary
        print(f"Suite: {comp_result.suite_name}")
        print(f"Providers compared: {comp_result.provider_count}")
        print(f"Total duration: {comp_result.total_duration_seconds:.4f}s")
        print()

        any_failures = False
        for sr in comp_result.suite_results:
            print(f"--- Provider: {sr.provider_name} ---")
            print(f"  Total: {sr.total}  "
                  f"Passed: {sr.passed}  "
                  f"Failed: {sr.failed}  "
                  f"Errors: {sr.errors}")
            for tr in sr.test_results:
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
            print()
            if sr.failed > 0 or sr.errors > 0:
                any_failures = True

        # Write JSON report if requested
        if args.report:
            try:
                report_path = write_report(comp_result, args.report)
                print(f"Report written to: {report_path}")
            except Exception as exc:
                print(f"Error writing report: {exc}")
                return 1

        # Write HTML report if requested
        if args.html:
            try:
                html_path = write_html_report(comp_result, args.html)
                print(f"HTML report written to: {html_path}")
            except Exception as exc:
                print(f"Error writing HTML report: {exc}")
                return 1

        return 1 if any_failures else 0

    parser.print_help()
    return 0
