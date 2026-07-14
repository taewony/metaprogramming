"""Text-to-SQL commands backed by local ActiveGraph behaviors."""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

import click

from activegraph import Event, Graph, Runtime
from activegraph.behaviors.base import Behavior
from activegraph.cli.hospital_logic import (
    deterministic_plan,
    entity_validation_answer,
    execute_sqlite,
    first_failed_entity_validation,
    format_answer_text,
    normalize_prompt_text,
    safe_display_text,
    sqlite_store_url,
    validate_capture_entities,
    validate_select_sql,
)
TEXT_TO_SQL_DIR = Path(__file__).resolve().parents[2]
REPO_ACTIVEGRAPH_DIR = TEXT_TO_SQL_DIR.parent
DEFAULT_DB_FILE = REPO_ACTIVEGRAPH_DIR / "data" / "hospital.db"
DEFAULT_CASES_FILE = TEXT_TO_SQL_DIR / "evals" / "hospital_cases.jsonl"
DEFAULT_TESTS_DIR = TEXT_TO_SQL_DIR / ".tests" / "runs"
DEFAULT_EVENT_STORE_FILE = REPO_ACTIVEGRAPH_DIR / "data" / "text_to_sql_events.sqlite"

def _ensure_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass



def make_hospital_behaviors(db_file: Path) -> list[Behavior]:
    db_path = Path(db_file)

    def parse_intent(event: Event, graph: Any, ctx: Any) -> None:
        prompt = event.payload["prompt"]
        plan = deterministic_plan(prompt)
        question = graph.add_object(
            "question",
            {
                "text": prompt,
                "language": event.payload.get("language", "ko"),
            },
        )
        intent = graph.add_object("intent", plan.intent)
        graph.add_relation(intent.id, question.id, "derived_from")
        validations = validate_capture_entities(db_path, plan)
        failed_validation = first_failed_entity_validation(validations)
        if failed_validation is not None:
            entity_validation = graph.add_object("entity_validation", failed_validation)
            graph.add_relation(entity_validation.id, intent.id, "validates")
            answer = graph.add_object(
                "answer",
                {
                    "text": entity_validation_answer(failed_validation),
                    "citations": [entity_validation.id],
                },
            )
            graph.add_relation(answer.id, entity_validation.id, "derived_from")
            graph.emit(
                "entity.validation_failed",
                {
                    "question_id": question.id,
                    "intent_id": intent.id,
                    "entity_validation_id": entity_validation.id,
                    "answer_id": answer.id,
                },
            )
            graph.emit(
                "answer.created",
                {
                    "question_id": question.id,
                    "answer_id": answer.id,
                    "entity_validation_id": entity_validation.id,
                },
            )
            return
        graph.emit(
            "intent.created",
            {
                "question_id": question.id,
                "intent_id": intent.id,
                "sql": plan.sql,
                "params": plan.params,
                "answer_template": plan.answer_template,
            },
        )

    def compile_sql(event: Event, graph: Any, ctx: Any) -> None:
        sql = event.payload["sql"]
        params = list(event.payload.get("params", []))
        validate_select_sql(sql)
        sql_query = graph.add_object(
            "sql_query",
            {
                "sql": sql,
                "params": params,
                "statement_type": "SELECT",
                "status": "draft",
                "answer_template": event.payload["answer_template"],
            },
        )
        graph.add_relation(sql_query.id, event.payload["intent_id"], "derived_from")
        graph.emit(
            "sql.generated",
            {
                "question_id": event.payload["question_id"],
                "intent_id": event.payload["intent_id"],
                "sql_query_id": sql_query.id,
            },
        )

    def execute_sql(event: Event, graph: Any, ctx: Any) -> None:
        sql_query = graph.get_object(event.payload["sql_query_id"])
        if sql_query is None:
            raise KeyError(f"Unknown sql_query object: {event.payload['sql_query_id']}")
        rows = execute_sqlite(
            db_path,
            sql_query.data["sql"],
            list(sql_query.data.get("params", [])),
        )
        query_result = graph.add_object(
            "query_result",
            {
                "rows": rows,
                "row_count": len(rows),
            },
        )
        graph.add_relation(sql_query.id, query_result.id, "executed_as")
        graph.patch_object(sql_query.id, {"status": "executed"})
        graph.emit(
            "sql.executed",
            {
                "question_id": event.payload["question_id"],
                "sql_query_id": sql_query.id,
                "query_result_id": query_result.id,
            },
        )

    def synthesize_answer(event: Event, graph: Any, ctx: Any) -> None:
        sql_query = graph.get_object(event.payload["sql_query_id"])
        query_result = graph.get_object(event.payload["query_result_id"])
        if sql_query is None:
            raise KeyError(f"Unknown sql_query object: {event.payload['sql_query_id']}")
        if query_result is None:
            raise KeyError(f"Unknown query_result object: {event.payload['query_result_id']}")

        rows = query_result.data.get("rows", [])
        text = format_answer_text(rows, sql_query.data["answer_template"])
        answer = graph.add_object(
            "answer",
            {
                "text": text,
                "citations": [event.payload["query_result_id"]],
            },
        )
        graph.add_relation(answer.id, event.payload["query_result_id"], "derived_from")
        graph.emit(
            "answer.created",
            {
                "question_id": event.payload["question_id"],
                "sql_query_id": event.payload["sql_query_id"],
                "query_result_id": event.payload["query_result_id"],
                "answer_id": answer.id,
            },
        )

    return [
        Behavior(
            name="parse_intent",
            fn=parse_intent,
            on=["question.submitted"],
            creates=["question", "intent", "entity_validation", "answer"],
        ),
        Behavior(
            name="compile_sql",
            fn=compile_sql,
            on=["intent.created"],
            creates=["sql_query"],
        ),
        Behavior(
            name="execute_sql",
            fn=execute_sql,
            on=["sql.generated"],
            creates=["query_result"],
        ),
        Behavior(
            name="synthesize_answer",
            fn=synthesize_answer,
            on=["sql.executed"],
            creates=["answer"],
        ),
    ]


def write_run_artifacts(graph: Graph, tests_dir: Path) -> dict[str, str]:
    run_dir = tests_dir / graph.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    trace_file = run_dir / "trace.jsonl"
    graph_file = run_dir / "graph.json"

    with trace_file.open("w", encoding="utf-8", errors="backslashreplace") as handle:
        for event in graph.events:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    graph_payload = {
        "run_id": graph.run_id,
        "objects": [obj.to_dict() for obj in graph.all_objects()],
        "relations": [rel.to_dict() for rel in graph.all_relations()],
    }
    graph_file.write_text(json.dumps(graph_payload, ensure_ascii=False, indent=2), encoding="utf-8", errors="backslashreplace")

    return {
        "run_dir": str(run_dir),
        "trace_file": str(trace_file),
        "graph_file": str(graph_file),
    }


def latest_object(graph: Graph, object_type: str) -> Any | None:
    matches = graph.objects(type=object_type)
    return matches[-1] if matches else None


def run_text_to_sql(
    prompt: str,
    db_file: str | Path = DEFAULT_DB_FILE,
    *,
    tests_dir: str | Path = DEFAULT_TESTS_DIR,
    event_store: str | Path | None = DEFAULT_EVENT_STORE_FILE,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    prompt = normalize_prompt_text(prompt)
    db_path = Path(db_file)
    event_store_path = Path(event_store) if event_store is not None else None
    if event_store_path is not None:
        event_store_path.parent.mkdir(parents=True, exist_ok=True)

    graph = Graph()
    runtime = Runtime(
        graph,
        behaviors=make_hospital_behaviors(db_path),
        budget={"max_events": 100, "max_behavior_calls": 20},
        persist_to=str(event_store_path) if event_store_path is not None else None,
    )

    question_event = Event(
        id=graph.ids.event(),
        type="question.submitted",
        payload={"prompt": prompt, "language": "ko"},
        actor="user",
        timestamp=graph.clock.now(),
    )
    graph.emit(question_event)
    runtime.run_until_idle()
    if event_store_path is not None:
        runtime.save_state()

    answer = latest_object(graph, "answer")
    sql_query = latest_object(graph, "sql_query")
    query_result = latest_object(graph, "query_result")
    failures = [event for event in graph.events if event.type == "behavior.failed"]

    artifacts = write_run_artifacts(graph, Path(tests_dir)) if write_artifacts else {}
    ok = answer is not None and not failures

    return {
        "ok": ok,
        "planner": "behavior",
        "model": None,
        "prompt": prompt,
        "run_id": graph.run_id,
        "event_store": str(event_store_path) if event_store_path is not None else None,
        "store_url": sqlite_store_url(event_store_path) if event_store_path is not None else None,
        "sql": sql_query.data["sql"] if sql_query else None,
        "params": sql_query.data.get("params", []) if sql_query else [],
        "rows": query_result.data.get("rows", []) if query_result else [],
        "answer": answer.data["text"] if answer else "",
        "error": safe_display_text(failures[-1].payload.get("message")) if failures else None,
        "events": len(graph.events),
        "objects": len(graph.all_objects()),
        "artifacts": artifacts,
    }

def load_cases(cases_file: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with cases_file.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                cases.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL in {cases_file} line {line_no}: {exc}") from exc
    return cases


def score_case(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []

    if not result["ok"]:
        failures.append(f"driver error: {result['error']}")
    if "expected_sql" in case and result["sql"] != case["expected_sql"]:
        failures.append(f"sql expected {case['expected_sql']!r}, got {result['sql']!r}")
    if "expected_params" in case and result["params"] != case["expected_params"]:
        failures.append(f"params expected {case['expected_params']!r}, got {result['params']!r}")
    if "expected_rows" in case and result["rows"] != case["expected_rows"]:
        failures.append(f"rows expected {case['expected_rows']!r}, got {result['rows']!r}")

    for expected_text in case.get("expected_answer_contains", []):
        if expected_text not in result["answer"]:
            failures.append(f"answer missing {expected_text!r}")

    return {
        "id": case.get("id"),
        "ok": not failures,
        "failures": failures,
        "result": result,
    }


def run_eval(
    cases_file: Path = DEFAULT_CASES_FILE,
    db_file: str | Path = DEFAULT_DB_FILE,
    *,
    tests_dir: str | Path = DEFAULT_TESTS_DIR,
    event_store: str | Path | None = DEFAULT_EVENT_STORE_FILE,
) -> dict[str, Any]:
    cases = load_cases(cases_file)
    scored_cases = [
        score_case(
            case,
            run_text_to_sql(
                case["prompt"],
                db_file,
                tests_dir=tests_dir,
                event_store=event_store,
            ),
        )
        for case in cases
    ]
    passed = sum(1 for case in scored_cases if case["ok"])
    failed = len(scored_cases) - passed
    return {
        "ok": failed == 0,
        "planner": "behavior",
        "model": None,
        "event_store": str(Path(event_store)) if event_store is not None else None,
        "store_url": sqlite_store_url(event_store) if event_store is not None else None,
        "passed": passed,
        "failed": failed,
        "cases": scored_cases,
    }

def behavior_specs(db_file: str | Path = DEFAULT_DB_FILE) -> list[dict[str, Any]]:
    return [
        {
            "name": behavior.name,
            "on": list(behavior.on),
            "creates": list(behavior.creates),
            "where": behavior.where,
            "pattern": behavior.pattern,
            "activate_after": behavior.activate_after,
        }
        for behavior in make_hospital_behaviors(Path(db_file))
    ]


def event_summary(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "type": event.type,
        "actor": event.actor,
        "caused_by": event.caused_by,
        "timestamp": event.timestamp,
    }


def run_ids_by_recency(event_store: str | Path) -> list[str]:
    store_path = Path(event_store)
    with sqlite3.connect(str(store_path)) as conn:
        rows = conn.execute(
            """
            SELECT runs.run_id
            FROM runs
            LEFT JOIN (
                SELECT run_id, MAX(seq) AS last_seq FROM events GROUP BY run_id
            ) e ON e.run_id = runs.run_id
            ORDER BY e.last_seq IS NULL, e.last_seq DESC, runs.created_at DESC
            """
        ).fetchall()
    return [str(row[0]) for row in rows]


def resolve_run_selector(selector: str | None, event_store: str | Path) -> str:
    if selector is None or selector == "" or selector == "0":
        offset = 0
    elif re.fullmatch(r"-\d+", selector):
        offset = abs(int(selector))
    else:
        return selector

    run_ids = run_ids_by_recency(event_store)
    if not run_ids:
        raise FileNotFoundError(f"no runs found in event store: {event_store}")
    if offset >= len(run_ids):
        raise IndexError(
            f"run selector {selector!r} is out of range; store has {len(run_ids)} run(s)"
        )
    return run_ids[offset]

def inspect_text_to_sql_run(
    run_selector: str | None = None,
    *,
    event_store: str | Path = DEFAULT_EVENT_STORE_FILE,
    db_file: str | Path = DEFAULT_DB_FILE,
    tail: int = 50,
) -> dict[str, Any]:
    store_path = Path(event_store)
    if not store_path.exists():
        raise FileNotFoundError(f"event store does not exist: {store_path}")

    chosen_run_id = resolve_run_selector(run_selector, store_path)

    runtime = Runtime.load(str(store_path), run_id=chosen_run_id)
    graph = runtime.graph
    events = list(graph.events)
    failures = [event.to_dict() for event in events if event.type == "behavior.failed"]

    return {
        "run_id": chosen_run_id,
        "run_selector": run_selector if run_selector is not None else "0",
        "event_store": str(store_path),
        "store_url": sqlite_store_url(store_path),
        "before": {
            "objects": [],
            "relations": [],
            "behaviors": behavior_specs(db_file),
        },
        "after": {
            "event_count": len(events),
            "object_count": len(graph.all_objects()),
            "relation_count": len(graph.all_relations()),
            "objects": [obj.to_dict() for obj in graph.all_objects()],
            "relations": [rel.to_dict() for rel in graph.all_relations()],
        },
        "recent_events": [event_summary(event) for event in events[-tail:]],
        "failures": failures,
    }

def echo_result(payload: dict[str, Any], *, as_json: bool) -> None:
    _ensure_utf8_stdout()
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if not payload["ok"]:
        click.echo(f"error: {payload.get('error')}")
        if payload.get("run_id"):
            click.echo(f"run_id: {payload['run_id']}")
        if payload.get("store_url"):
            click.echo(f"store: {payload['store_url']}")
        return

    click.echo(f"answer: {payload['answer']}")
    click.echo(f"sql: {payload['sql']}")
    click.echo(f"rows: {json.dumps(payload['rows'], ensure_ascii=False)}")
    click.echo(f"run_id: {payload['run_id']}")
    if payload.get("store_url"):
        click.echo(f"store: {payload['store_url']}")
    artifacts = payload.get("artifacts") or {}
    if artifacts.get("trace_file"):
        click.echo(f"trace: {artifacts['trace_file']}")

def echo_eval(payload: dict[str, Any], *, as_json: bool) -> None:
    _ensure_utf8_stdout()
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo(f"summary: {payload['passed']} passed, {payload['failed']} failed")
    for case in payload["cases"]:
        status = "ok" if case["ok"] else "failed"
        click.echo(f"  {status:6s} {case['id']}")
        for failure in case["failures"]:
            click.echo(f"    {failure}")

def echo_inspect_run(payload: dict[str, Any], *, as_json: bool) -> None:
    _ensure_utf8_stdout()
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo(f"run_id: {payload['run_id']}")
    click.echo(f"store: {payload['store_url']}")

    click.echo("before ask:")
    click.echo("  objects: []")
    click.echo("  relations: []")
    click.echo("  behaviors:")
    for behavior in payload["before"]["behaviors"]:
        on = ",".join(behavior["on"]) or "(pattern-only)"
        creates = ",".join(behavior["creates"]) or "-"
        click.echo(f"    {behavior['name']:18s} on={on:20s} creates={creates}")

    after = payload["after"]
    click.echo("after ask:")
    click.echo(
        f"  events={after['event_count']} objects={after['object_count']} relations={after['relation_count']}"
    )
    click.echo("  objects:")
    for obj in after["objects"]:
        data = json.dumps(obj.get("data", {}), ensure_ascii=False)
        click.echo(f"    {obj['id']:14s} {obj['type']:12s} {data}")
    click.echo("  relations:")
    for rel in after["relations"]:
        click.echo(f"    {rel['source']} -[{rel['type']}]-> {rel['target']}")

    if payload["failures"]:
        click.echo("failures:")
        for failure in payload["failures"]:
            click.echo(json.dumps(failure, ensure_ascii=False))
    else:
        click.echo("failures: none")

    click.echo(f"recent events (last {len(payload['recent_events'])}):")
    for event in payload["recent_events"]:
        actor = event.get("actor") or "-"
        caused_by = event.get("caused_by") or "-"
        click.echo(f"  {event['id']:8s} {event['type']:20s} actor={actor:16s} caused_by={caused_by}")

@click.group("text-to-sql")
def cmd_text_to_sql() -> None:
    """Hospital Text-to-SQL behavior commands."""


@cmd_text_to_sql.command("ask")
@click.argument("prompt")
@click.option("--db-file", type=click.Path(path_type=Path), default=DEFAULT_DB_FILE, show_default=True)
@click.option("--tests-dir", type=click.Path(path_type=Path), default=DEFAULT_TESTS_DIR, show_default=True)
@click.option("--event-store", type=click.Path(path_type=Path), default=DEFAULT_EVENT_STORE_FILE, show_default=True)
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
def cmd_ask(prompt: str, db_file: Path, tests_dir: Path, event_store: Path, as_json: bool) -> None:
    """Ask one Korean hospital database question."""
    payload = run_text_to_sql(prompt, db_file, tests_dir=tests_dir, event_store=event_store)
    echo_result(payload, as_json=as_json)
    if not payload["ok"]:
        raise SystemExit(1)


@cmd_text_to_sql.command("eval")
@click.option("--cases", "cases_file", type=click.Path(path_type=Path), default=DEFAULT_CASES_FILE, show_default=True)
@click.option("--db-file", type=click.Path(path_type=Path), default=DEFAULT_DB_FILE, show_default=True)
@click.option("--tests-dir", type=click.Path(path_type=Path), default=DEFAULT_TESTS_DIR, show_default=True)
@click.option("--event-store", type=click.Path(path_type=Path), default=DEFAULT_EVENT_STORE_FILE, show_default=True)
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
def cmd_eval(cases_file: Path, db_file: Path, tests_dir: Path, event_store: Path, as_json: bool) -> None:
    """Run JSONL Text-to-SQL behavior eval cases."""
    payload = run_eval(cases_file, db_file, tests_dir=tests_dir, event_store=event_store)
    echo_eval(payload, as_json=as_json)
    if not payload["ok"]:
        raise SystemExit(1)


def _cmd_inspect_impl(run_selector: str | None, event_store: Path, db_file: Path, tail: int, as_json: bool) -> None:
    try:
        payload = inspect_text_to_sql_run(run_selector, event_store=event_store, db_file=db_file, tail=tail)
    except (FileNotFoundError, IndexError) as exc:
        raise click.ClickException(str(exc)) from exc
    echo_inspect_run(payload, as_json=as_json)


@cmd_text_to_sql.command("inspect", context_settings={"ignore_unknown_options": True})
@click.argument("run_selector", required=False)
@click.option("--event-store", type=click.Path(path_type=Path), default=DEFAULT_EVENT_STORE_FILE, show_default=True)
@click.option("--db-file", type=click.Path(path_type=Path), default=DEFAULT_DB_FILE, show_default=True)
@click.option("--tail", type=int, default=50, show_default=True, help="Number of recent events to show.")
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
def cmd_inspect(run_selector: str | None, event_store: Path, db_file: Path, tail: int, as_json: bool) -> None:
    """Inspect a persisted Text-to-SQL run. Select 0, -1, -2, or a run id."""
    _cmd_inspect_impl(run_selector, event_store, db_file, tail, as_json)


@cmd_text_to_sql.command("inspect-run", hidden=True, context_settings={"ignore_unknown_options": True})
@click.argument("run_selector", required=False)
@click.option("--event-store", type=click.Path(path_type=Path), default=DEFAULT_EVENT_STORE_FILE, show_default=True)
@click.option("--db-file", type=click.Path(path_type=Path), default=DEFAULT_DB_FILE, show_default=True)
@click.option("--tail", type=int, default=50, show_default=True, help="Number of recent events to show.")
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
def cmd_inspect_run(run_selector: str | None, event_store: Path, db_file: Path, tail: int, as_json: bool) -> None:
    """Compatibility alias for inspect."""
    _cmd_inspect_impl(run_selector, event_store, db_file, tail, as_json)


@cmd_text_to_sql.command("repl")
@click.option("--db-file", type=click.Path(path_type=Path), default=DEFAULT_DB_FILE, show_default=True)
@click.option("--tests-dir", type=click.Path(path_type=Path), default=DEFAULT_TESTS_DIR, show_default=True)
@click.option("--event-store", type=click.Path(path_type=Path), default=DEFAULT_EVENT_STORE_FILE, show_default=True)
def cmd_repl(db_file: Path, tests_dir: Path, event_store: Path) -> None:
    """Start an interactive hospital Text-to-SQL REPL."""
    _ensure_utf8_stdout()
    click.echo("hospital Text-to-SQL REPL. Type exit or quit to leave.")
    while True:
        try:
            prompt = input("hospital> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo()
            return
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit", "q", ":q"}:
            return
        payload = run_text_to_sql(prompt, db_file, tests_dir=tests_dir, event_store=event_store)
        echo_result(payload, as_json=False)







