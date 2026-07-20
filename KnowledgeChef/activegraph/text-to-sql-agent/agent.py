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
DEFAULT_REPL_SESSION_ID = "agent-repl-default"

def _ensure_utf8_stdio() -> None:
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
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
    print("pack commands are always available: pack list | pack current | pack inspect <id> | pack schema <id> | pack validate <id> | pack import <id> | pack use <id>")

def _print_shell_help(mode: str) -> None:
    print("REPL shell commands:")
    print("  help                       show this shell guide and current mode commands")
    print("  help <command>             show command-specific help for the current mode")
    print("  mode                       list shell modes")
    print("  mode text-to-sql           use Text-to-SQL shortcuts: ask, eval, inspect, context, snapshot, repl")
    print("  ask --llm <prompt>         enable optional Ollama answer composition with deterministic fallback")
    print("  mode activegraph           use the original ActiveGraph CLI command tree")
    print("  pack list                  list configured agent packs")
    print("  pack current               show the selected default pack")
    print("  pack inspect <pack-id>     inspect pack DB/system-model/OKF bindings")
    print("  pack schema <pack-id>      project DB schema from the pack OKF bundle")
    print("  pack validate [pack-id]    validate pack files, DB, event store, and schema projection")
    print("  pack import <pack-id>      register third-party DB + OKF schema bundle + eval cases")
    print("  eval-run export <id>       export a v11.5 eval-run artifact bundle")
    print("  eval-run attach-score <id> <case-id> --score-file score.json")
    print("  pack use <pack-id>         change the default pack in packs.yaml")
    print("  exit                       leave the REPL")
    print()
    if mode == "text-to-sql":
        print("Current mode: text-to-sql")
        print("  Commands are forwarded as: text-to-sql <command>")
        print("  Example: ask \"의사는 모두 몇명이야?\"")
        print("  Example: ask --llm \"VIP 고객 총매출액\"")
        print("  Example: pack schema techshop-db")
        print("  Switch to original ActiveGraph shell with: mode activegraph")
    else:
        print("Current mode: activegraph")
        print("  Commands are forwarded to the original ActiveGraph CLI without a prefix.")
        print("  Example: inspect sqlite:///activegraph/data/text_to_sql_events.sqlite --run-id <run_id>")
        print("  Example: text-to-sql ask \"의사는 모두 몇명이야?\"")
        print("  Switch back with: mode text-to-sql")
    print()
    print("Delegated command help:")
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
    _print_shell_help(mode)
    return _run_cli([*prefix, "--help"])


def _parse_line(line: str) -> list[str]:
    try:
        return shlex.split(line)
    except ValueError as exc:
        print(f"parse error: {exc}")
        return []

def _has_option(argv: Sequence[str], *names: str) -> bool:
    return any(arg == name or any(arg.startswith(name + "=") for name in names) for arg in argv for name in names)


def _with_default_text_to_sql_session(mode: str, argv: Sequence[str]) -> list[str]:
    out = list(argv)
    if mode != "text-to-sql" or not out:
        return out
    command = out[0]
    if command not in {"ask", "context"}:
        return out
    if _has_option(out, "--session-id"):
        return out
    return [command, "--session-id", DEFAULT_REPL_SESSION_ID, *out[1:]]


def _run_repl_command(args: Sequence[str]) -> None:
    try:
        _run_cli(args)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        if code not in (0, None):
            print(f"command exited with status {code}")


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
    _ensure_utf8_stdio()
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
            if args and args[0] == "pack":
                _run_repl_command(["pack", *args[1:], "--help"])
            else:
                _print_help(mode, args)
            continue
        if command == "pack":
            _run_repl_command(["pack", *args])
            continue

        forwarded = _with_default_text_to_sql_session(mode, argv)
        _run_repl_command([*_mode_prefix(mode), *forwarded])


def main(argv: Sequence[str] | None = None) -> int:
    _ensure_utf8_stdio()
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        return _run_cli(args)
    return repl()


if __name__ == "__main__":
    raise SystemExit(main())









