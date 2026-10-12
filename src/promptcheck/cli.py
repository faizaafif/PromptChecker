"""Command-line interface for PromptCheck."""

from __future__ import annotations

import argparse

from promptcheck.config import load_suite


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="promptcheck",
        description="Run repeatable prompt tests against model providers.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run a YAML prompt test suite (not implemented yet).",
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
            print(f"Unexpected error: {exc}")
            return 1

        print("Loaded suite:", suite.suite_name)
        print("Tests:", len(suite.tests))
        return 0

    parser.print_help()
    return 0
