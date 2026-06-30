#!/usr/bin/env python3
"""KnowledgeChef CLI scaffold.

The PRD defines a phased command-line surface for OKF producer/consumer
and merger workflows. This module wires the command tree and the agent
loop entrypoint now, but keeps the behavior intentionally minimal: the
commands expose help text and dry-run scaffolding so the interface can be
filled in incrementally without changing the shape of the CLI later.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

DEFAULT_DB_PATH = Path("data/techshop.db")
DEFAULT_BUNDLE_PATH = Path("okf_bundle")


def _add_common_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--bundle",
        type=Path,
        default=DEFAULT_BUNDLE_PATH,
        help="Path to the OKF bundle root.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to the TechShop SQLite database.",
    )


def _build_init_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "init",
        help="Initialize a new OKF bundle.",
        description="Create an empty OKF bundle scaffold at the target path.",
    )
    parser.add_argument("path", type=Path, help="Destination path for the bundle.")
    parser.add_argument(
        "--template",
        choices=("empty", "techshop"),
        default="empty",
        help="Bundle template to use.",
    )
    parser.set_defaults(func=_handle_stub)
    return parser


def _build_add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "add",
        help="Add a source into the bundle.",
        description="Register a new ingredient source for later OKF compilation.",
    )
    parser.add_argument("source", type=str, help="Source file, directory, or URL to ingest.")
    parser.set_defaults(func=_handle_stub)
    return parser


def _build_merge_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "merge",
        help="Merge two bundles.",
        description="Combine two OKF bundles into a merged result.",
    )
    parser.add_argument("src", type=Path, help="Source bundle path.")
    parser.add_argument("dest", type=Path, help="Destination bundle path.")
    parser.set_defaults(func=_handle_stub)
    return parser


def _build_dedupe_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "dedupe",
        help="Remove duplicate concepts or rows.",
        description="Deduplicate bundle content and keep the latest canonical entries.",
    )
    parser.add_argument("path", type=Path, help="Bundle path to deduplicate.")
    parser.set_defaults(func=_handle_stub)
    return parser


def _build_diff_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "diff",
        help="Show bundle differences.",
        description="Compute the delta between two bundle states.",
    )
    parser.add_argument("old", type=Path, help="Older bundle or snapshot path.")
    parser.add_argument("new", type=Path, help="Newer bundle or snapshot path.")
    parser.set_defaults(func=_handle_stub)
    return parser


def _build_validate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "validate",
        help="Validate a bundle.",
        description="Check link integrity and OKF spec compliance for a bundle.",
    )
    parser.add_argument("path", type=Path, help="Bundle path to validate.")
    parser.set_defaults(func=_handle_stub)
    return parser


def _build_index_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "index",
        help="Regenerate index.md.",
        description="Rebuild the bundle index from the current OKF tree.",
    )
    parser.add_argument("path", type=Path, help="Bundle path whose index should be regenerated.")
    parser.set_defaults(func=_handle_stub)
    return parser


def _build_query_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "query",
        help="Ask a natural-language question.",
        description="Run the consumer pipeline against the TechShop database or OKF bundle.",
    )
    parser.add_argument("question", nargs="+", help="Natural-language question to answer.")
    _add_common_paths(parser)
    parser.set_defaults(func=_handle_query)
    return parser


def _build_loop_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "loop",
        help="Run the agent loop scaffold.",
        description="Execute the cognitive compiler / mental rehearsal / execution loop scaffold.",
        aliases=("agent-loop",),
    )
    parser.add_argument("question", nargs="+", help="User question to compile into an agent plan.")
    _add_common_paths(parser)
    parser.set_defaults(func=_handle_loop)
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kchef",
        description="KnowledgeChef command line interface.",
        epilog="Planned commands: init, add, merge, dedupe, diff, validate, index, query, loop.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    _build_init_parser(subparsers)
    _build_add_parser(subparsers)
    _build_merge_parser(subparsers)
    _build_dedupe_parser(subparsers)
    _build_diff_parser(subparsers)
    _build_validate_parser(subparsers)
    _build_index_parser(subparsers)
    _build_query_parser(subparsers)
    _build_loop_parser(subparsers)
    return parser


def cognitive_knowledge_os_loop(user_query: str, *, bundle_path: Path = DEFAULT_BUNDLE_PATH, db_path: Path = DEFAULT_DB_PATH) -> int:
    """Dry-run scaffold for the KnowledgeChef agent loop."""
    normalized = " ".join(user_query.split()).strip()
    if not normalized:
        print("error: question is required", file=sys.stderr)
        return 2

    print("KnowledgeChef agent loop scaffold")
    print(f"- bundle: {bundle_path}")
    print(f"- db: {db_path}")
    print(f"- question: {normalized}")
    print()
    print("Planned phases:")
    print("1. Intent analysis")
    print("2. Symbol resolution")
    print("3. IR generation")
    print("4. Execution planning")
    print("5. Response synthesis")
    return 0


def _handle_stub(args: argparse.Namespace) -> int:
    command = getattr(args, "command", "command")
    print(f"{command}: scaffold only. Use --help for command details.")
    return 0


def _handle_query(args: argparse.Namespace) -> int:
    return cognitive_knowledge_os_loop(
        " ".join(args.question),
        bundle_path=args.bundle,
        db_path=args.db,
    )


def _handle_loop(args: argparse.Namespace) -> int:
    return cognitive_knowledge_os_loop(
        " ".join(args.question),
        bundle_path=args.bundle,
        db_path=args.db,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    handler: Callable[[argparse.Namespace], int] = getattr(args, "func", _handle_stub)
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
