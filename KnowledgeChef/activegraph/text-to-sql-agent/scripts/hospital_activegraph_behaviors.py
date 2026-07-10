#!/usr/bin/env python3
"""Behavior-backed Text-to-SQL runner for the hospital fixture.

This module uses the local ActiveGraph runtime from ``../src`` and keeps the
first implementation deterministic so CLI/eval tests can run without LLMs.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
TEXT_TO_SQL_DIR = SCRIPT_DIR.parent
REPO_ACTIVEGRAPH_DIR = TEXT_TO_SQL_DIR.parent
RUNTIME_SRC_DIR = TEXT_TO_SQL_DIR / "src"
DEFAULT_DB_FILE = REPO_ACTIVEGRAPH_DIR / "data" / "hospital.db"
DEFAULT_TESTS_DIR = TEXT_TO_SQL_DIR / ".tests" / "runs"

if str(RUNTIME_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SRC_DIR))

from activegraph import Event, Graph, Runtime  # noqa: E402
from activegraph.behaviors.base import Behavior  # noqa: E402


@dataclass(frozen=True)
class IntentPlan:
    intent: dict[str, Any]
    sql: str
    params: list[Any]
    answer_template: str


class UnsupportedPromptError(ValueError):
    """Raised when the deterministic behavior set has no prompt rule."""


class UnsafeSQLError(ValueError):
    """Raised when generated SQL violates the read-only policy."""


def deterministic_plan(prompt: str) -> IntentPlan:
    normalized = re.sub(r"\s+", " ", prompt.strip())

    if "김지훈" in normalized and ("전공" in normalized or "전문" in normalized):
        return IntentPlan(
            intent={
                "kind": "lookup",
                "entity": "doctor",
                "filters": {"name": "김지훈"},
                "requested_fields": ["specialty"],
            },
            sql="SELECT specialty FROM doctors WHERE name = ?",
            params=["김지훈"],
            answer_template="김지훈 의사의 전공은 {value}입니다.",
        )

    doctor_count_markers = [
        "의사는 모두 몇명이야",
        "의사는 모두 몇 명이야",
        "의사 모두 몇명이야",
        "의사 모두 몇 명이야",
        "의사 몇명",
        "의사 몇 명",
    ]
    if any(marker in normalized for marker in doctor_count_markers):
        return IntentPlan(
            intent={
                "kind": "count",
                "entity": "doctor",
                "filters": {},
                "requested_fields": ["count"],
            },
            sql="SELECT COUNT(*) FROM doctors",
            params=[],
            answer_template="의사는 모두 {value}명입니다.",
        )

    raise UnsupportedPromptError(f"Unsupported prompt for deterministic behaviors: {prompt}")


def validate_select_sql(sql: str) -> None:
    normalized = sql.strip().lower()
    if not normalized.startswith("select "):
        raise UnsafeSQLError(f"Only SELECT SQL is allowed, got: {sql}")
    if ";" in normalized:
        raise UnsafeSQLError("SQL must be a single SELECT statement without semicolons")
    padded = f" {normalized} "
    for token in [" insert ", " update ", " delete ", " drop ", " alter ", " create ", " attach ", " pragma "]:
        if token in padded:
            raise UnsafeSQLError(f"Unsafe SQL token found: {token.strip()}")


def execute_sqlite(db_file: Path, sql: str, params: list[Any]) -> list[list[Any]]:
    validate_select_sql(sql)
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.execute(sql, params)
        return [list(row) for row in cursor.fetchall()]


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
        if rows:
            text = sql_query.data["answer_template"].format(value=rows[0][0])
        else:
            text = "조회 결과가 없습니다."
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
            creates=["question", "intent"],
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


def event_to_dict(event: Event) -> dict[str, Any]:
    return event.to_dict()


def object_to_dict(obj: Any) -> dict[str, Any]:
    return obj.to_dict()


def write_run_artifacts(graph: Graph, tests_dir: Path) -> dict[str, str]:
    run_dir = tests_dir / graph.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    trace_file = run_dir / "trace.jsonl"
    graph_file = run_dir / "graph.json"

    with trace_file.open("w", encoding="utf-8") as handle:
        for event in graph.events:
            handle.write(json.dumps(event_to_dict(event), ensure_ascii=False) + "\n")

    graph_payload = {
        "run_id": graph.run_id,
        "objects": [object_to_dict(obj) for obj in graph.all_objects()],
        "relations": [rel.to_dict() for rel in graph.all_relations()],
    }
    graph_file.write_text(json.dumps(graph_payload, ensure_ascii=False, indent=2), encoding="utf-8")

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
    write_artifacts: bool = True,
) -> dict[str, Any]:
    db_path = Path(db_file)
    graph = Graph()
    runtime = Runtime(
        graph,
        behaviors=make_hospital_behaviors(db_path),
        budget={"max_events": 100, "max_behavior_calls": 20},
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
        "sql": sql_query.data["sql"] if sql_query else None,
        "params": sql_query.data.get("params", []) if sql_query else [],
        "rows": query_result.data.get("rows", []) if query_result else [],
        "answer": answer.data["text"] if answer else "",
        "error": failures[-1].payload.get("message") if failures else None,
        "events": len(graph.events),
        "objects": len(graph.all_objects()),
        "artifacts": artifacts,
    }
