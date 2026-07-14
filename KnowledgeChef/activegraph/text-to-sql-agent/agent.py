#!/usr/bin/env python3
"""Local REPL/CLI entrypoint for the copied ActiveGraph runtime.

Direct CLI usage still delegates to the original ActiveGraph Click tree:

    python agent.py text-to-sql ask "의사는 모두 몇명이야?"
    python agent.py inspect sqlite:///../data/text_to_sql_events.sqlite --run-id <run_id>

Running without arguments starts a small REPL. The REPL defaults to the
``text-to-sql`` command group so reverse-engineering the behavior/event loop is
short and repetitive:

    > help
    > ask "의사는 모두 몇명이야?"
    > inspect 0
    > mode activegraph
    > help

The wrapper keeps this checkout self-contained by putting ``./src`` before any
installed ``activegraph`` package on ``sys.path``.
"""
from __future__ import annotations

import shlex
import sys
from pathlib import Path
from typing import Sequence

AGENT_DIR = Path(__file__).resolve().parent
SRC_DIR = AGENT_DIR / "src"

src_text = str(SRC_DIR)
if sys.path[0:1] != [src_text]:
    try:
        sys.path.remove(src_text)
    except ValueError:
        pass
    sys.path.insert(0, src_text)

from activegraph.cli.main import main as activegraph_main  # noqa: E402

MODES = ("text-to-sql", "activegraph")
DEFAULT_MODE = "text-to-sql"


def _print_banner(mode: str) -> None:
    print("ActiveGraph local agent REPL")
    print(f"mode: {mode}")
    print("type `help` for commands, `mode` for modes, `exit` to quit")
    print()
    _print_help(mode, [])


def _print_modes(current_mode: str) -> None:
    print(f"current mode: {current_mode}")
    print("available modes:")
    for mode in MODES:
        marker = "*" if mode == current_mode else " "
        print(f"  {marker} {mode}")
    print("switch with: mode text-to-sql | mode activegraph")


def _run_cli(args: Sequence[str]) -> int:
    return activegraph_main(list(args))


def _mode_prefix(mode: str) -> list[str]:
    if mode == "text-to-sql":
        return ["text-to-sql"]
    if mode == "activegraph":
        return []
    raise ValueError(f"unknown mode: {mode}")


def _print_help(mode: str, args: Sequence[str]) -> int:
    prefix = _mode_prefix(mode)
    if args:
        return _run_cli([*prefix, *args, "--help"])
    return _run_cli([*prefix, "--help"])


def _parse_line(line: str) -> list[str]:
    try:
        return shlex.split(line)
    except ValueError as exc:
        print(f"parse error: {exc}")
        return []


def _handle_mode(args: Sequence[str], current_mode: str) -> str:
    if not args:
        _print_modes(current_mode)
        return current_mode

    requested = args[0].strip("'\"").lower()
    if requested not in MODES:
        print(f"unknown mode: {args[0]}")
        _print_modes(current_mode)
        return current_mode

    print(f"mode: {requested}")
    _print_help(requested, [])
    return requested


def repl() -> int:
    mode = DEFAULT_MODE
    _print_banner(mode)

    while True:
        try:
            line = input(f"{mode}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            continue

        argv = _parse_line(line)
        if not argv:
            continue

        command = argv[0].lower()
        args = argv[1:]

        if command in {"exit", "quit", "q", ":q"}:
            return 0
        if command == "mode":
            mode = _handle_mode(args, mode)
            continue
        if command == "help":
            _print_help(mode, args)
            continue

        _run_cli([*_mode_prefix(mode), *argv])


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        return _run_cli(args)
    return repl()


if __name__ == "__main__":
    raise SystemExit(main())
