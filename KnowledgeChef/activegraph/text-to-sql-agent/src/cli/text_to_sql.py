"""Text-to-SQL commands backed by local ActiveGraph behaviors."""
from __future__ import annotations

import hashlib
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
    DEFAULT_SYSTEM_MODEL_FILE,
    deterministic_plan,
    entity_validation_answer,
    execute_sqlite,
    first_failed_entity_validation,
    format_answer_text,
    load_rule_catalog_from_system_model,
    normalize_prompt_text,
    safe_display_text,
    sqlite_store_url,
    validate_capture_entities,
    validate_select_sql,
)
from activegraph.cli.full_context import assemble_full_context
from activegraph.cli.llm_answer import LLMAnswerComposerError, compose_answer_with_llm, resolve_llm_config
from activegraph.cli.pack_config import PackConfigError, resolve_pack
from activegraph.cli.sql_planner import load_planner_resolution_model, resolve_sql_planner
from activegraph.cli.session_memory import (
    DEFAULT_SESSION_STORE_DIR,
    append_session_turn,
    load_session_state,
    project_session_graph_before_run,
    resolve_prompt_from_session,
    save_session_state,
)

TEXT_TO_SQL_DIR = Path(__file__).resolve().parents[2]
REPO_ACTIVEGRAPH_DIR = TEXT_TO_SQL_DIR.parent
DEFAULT_DB_FILE = REPO_ACTIVEGRAPH_DIR / "data" / "hospital.db"
DEFAULT_CASES_FILE = TEXT_TO_SQL_DIR / "evals" / "hospital_cases.jsonl"
DEFAULT_EVAL_MANIFEST_FILE = TEXT_TO_SQL_DIR / "evals" / "eval_manifest.yaml"
DEFAULT_TESTS_DIR = TEXT_TO_SQL_DIR / ".tests" / "runs"
DEFAULT_EVENT_STORE_FILE = REPO_ACTIVEGRAPH_DIR / "data" / "text_to_sql_events.sqlite"


def _selected_pack(ctx: click.Context, pack_id: str | None = None):
    root_obj = ctx.find_root().obj or {}
    group_obj = ctx.obj or {}
    selected = pack_id or group_obj.get("pack_id") or root_obj.get("pack_id")
    try:
        return resolve_pack(selected)
    except PackConfigError as exc:
        raise click.ClickException(str(exc)) from exc


def _resolve_pack_paths(
    ctx: click.Context,
    *,
    db_file: Path | None,
    event_store: Path | None,
    pack_id: str | None = None,
) -> tuple[Path, Path, Path, Any]:
    pack = _selected_pack(ctx, pack_id)
    resolved_db = Path(db_file) if db_file is not None else pack.db_file or DEFAULT_DB_FILE
    resolved_event_store = Path(event_store) if event_store is not None else pack.event_store or DEFAULT_EVENT_STORE_FILE
    return resolved_db, resolved_event_store, pack.system_model, pack


def _default_eval_cases_file_for_pack(pack: Any) -> Path:
    """Return the consolidated eval file for the selected DB pack."""
    if DEFAULT_EVAL_MANIFEST_FILE.exists():
        try:
            import yaml

            manifest = yaml.safe_load(DEFAULT_EVAL_MANIFEST_FILE.read_text(encoding="utf-8"))
        except Exception:
            manifest = None
        pack_entry = manifest.get("packs", {}).get(pack.id) if isinstance(manifest, dict) else None
        runnable = pack_entry.get("runnable", {}) if isinstance(pack_entry, dict) else {}
        filename = runnable.get("consolidated") or runnable.get("canonical")
        if isinstance(filename, str) and filename:
            return DEFAULT_EVAL_MANIFEST_FILE.parent / filename

    db_name = (pack.db_file.name if pack.db_file is not None else "").lower()
    if db_name == "techshop.db":
        return TEXT_TO_SQL_DIR / "evals" / "techshop_cases.jsonl"
    if db_name == "hospital.db":
        return TEXT_TO_SQL_DIR / "evals" / "hospital_consolidated_cases.jsonl"
    return DEFAULT_CASES_FILE


def _hash_context_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _ensure_utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass



def make_hospital_behaviors(
    db_file: Path,
    *,
    system_model_file: str | Path = DEFAULT_SYSTEM_MODEL_FILE,
    pack: Any | None = None,
    event_store: str | Path | None = None,
    llm_config: dict[str, Any] | None = None,
) -> list[Behavior]:
    db_path = Path(db_file)
    system_model_path = Path(system_model_file)
    catalog = load_rule_catalog_from_system_model(system_model_file)
    resolved_llm_config = dict(llm_config or resolve_llm_config(pack))

    def behavior_contract(name: str, *, default_on: list[str], default_creates: list[str]) -> dict[str, Any]:
        declared = catalog.behavior_spec(name) or {}
        return {
            "on": list(declared.get("on") or default_on),
            "creates": list(declared.get("creates") or default_creates),
        }

    planner_model = load_planner_resolution_model(system_model_path)
    planner_enabled = bool(planner_model)

    def create_question_projection(event: Event, graph: Any) -> tuple[Any, Any | None]:
        prompt = event.payload["prompt"]
        question = graph.add_object(
            "question",
            {
                "text": prompt,
                "original_text": event.payload.get("original_prompt", prompt),
                "language": event.payload.get("language", "ko"),
                "session_id": event.payload.get("session_id"),
            },
        )
        session_obj = None
        session_id = event.payload.get("session_id")
        if session_id:
            session_obj = graph.add_object(
                "session",
                {
                    "session_id": session_id,
                    "scope": "session_memory",
                },
            )
            graph.add_relation(question.id, session_obj.id, "belongs_to_session")
            resolution = event.payload.get("session_resolution") or {}
            if resolution.get("resolved"):
                resolution_obj = graph.add_object("session_resolution", resolution)
                graph.add_relation(resolution_obj.id, question.id, "resolves_question")
                graph.add_relation(resolution_obj.id, session_obj.id, "uses_session")
        return question, session_obj

    def resolve_sql_planner_behavior(event: Event, graph: Any, ctx: Any) -> None:
        question, session_obj = create_question_projection(event, graph)
        resolution = resolve_sql_planner(
            event.payload["prompt"],
            original_prompt=event.payload.get("original_prompt", event.payload["prompt"]),
            session_resolution=event.payload.get("session_resolution") or {},
            catalog=catalog,
            config=planner_model,
        )
        planner_obj = graph.add_object("planner_resolution", resolution.to_graph_data())
        graph.add_relation(planner_obj.id, question.id, "derived_from")
        if session_obj is not None:
            graph.add_relation(planner_obj.id, session_obj.id, "uses_session")
        for assumption in resolution.assumptions:
            rationale = graph.add_object(
                "decision_rationale",
                {
                    "behavior": "resolve_sql_planner",
                    "decision": resolution.resolution_strategy,
                    "confidence": resolution.confidence,
                    "evidence": [assumption],
                    "alternatives": resolution.clarification_options,
                },
            )
            graph.add_relation(rationale.id, planner_obj.id, "derived_from")
            graph.add_relation(planner_obj.id, rationale.id, "assumes")

        if resolution.status == "resolved":
            graph.emit(
                "planner.resolved",
                {
                    "question_id": question.id,
                    "planner_resolution_id": planner_obj.id,
                    "prompt": resolution.planner_resolved_prompt,
                    "original_prompt": resolution.original_prompt,
                    "language": event.payload.get("language", "ko"),
                    "session_id": event.payload.get("session_id"),
                    "session_resolution": event.payload.get("session_resolution") or {},
                    "selected_rule_hint": resolution.selected_rule_hint,
                },
            )
            return

        if resolution.status == "clarification_required":
            clarification = graph.add_object(
                "clarification_request",
                {
                    "question": resolution.clarification_question,
                    "reason": resolution.resolution_strategy,
                    "options": resolution.clarification_options,
                    "unresolved_slots": resolution.unresolved_slots,
                    "source_prompt": resolution.original_prompt,
                },
            )
            graph.add_relation(clarification.id, planner_obj.id, "derived_from")
            graph.emit(
                "clarification.required",
                {
                    "question_id": question.id,
                    "planner_resolution_id": planner_obj.id,
                    "clarification_request_id": clarification.id,
                },
            )
            return

        graph.emit(
            "planner.unsupported",
            {
                "question_id": question.id,
                "planner_resolution_id": planner_obj.id,
                "prompt": resolution.original_prompt,
                "reason": resolution.resolution_strategy,
            },
        )
        from activegraph.cli.hospital_logic import UnsupportedPromptError

        raise UnsupportedPromptError(f"Unsupported prompt for rule catalog {catalog.id}: {resolution.original_prompt}")

    def request_clarification(event: Event, graph: Any, ctx: Any) -> None:
        clarification = graph.get_object(event.payload["clarification_request_id"])
        if clarification is None:
            raise KeyError(f"Unknown clarification_request object: {event.payload['clarification_request_id']}")
        answer = graph.add_object(
            "answer",
            {
                "text": clarification.data.get("question") or "질문을 조금 더 구체화해 주세요.",
                "citations": [clarification.id],
                "source": "clarification",
                "deterministic_text": clarification.data.get("question") or "질문을 조금 더 구체화해 주세요.",
                "llm_invocation_id": None,
                "llm_error": None,
            },
        )
        graph.add_relation(answer.id, clarification.id, "derived_from")
        graph.emit(
            "answer.created",
            {
                "question_id": event.payload["question_id"],
                "planner_resolution_id": event.payload["planner_resolution_id"],
                "clarification_request_id": clarification.id,
                "answer_id": answer.id,
                "source": "clarification",
            },
        )

    def parse_intent(event: Event, graph: Any, ctx: Any) -> None:
        prompt = event.payload["prompt"]
        plan = deterministic_plan(prompt, catalog=catalog)
        if planner_enabled:
            question = graph.get_object(event.payload["question_id"])
            if question is None:
                raise KeyError(f"Unknown question object: {event.payload['question_id']}")
            planner_resolution_id = event.payload.get("planner_resolution_id")
        else:
            question, _session_obj = create_question_projection(event, graph)
            planner_resolution_id = None
        intent = graph.add_object("intent", plan.intent)
        graph.add_relation(intent.id, question.id, "derived_from")
        if planner_resolution_id:
            graph.add_relation(intent.id, planner_resolution_id, "derived_from")
        validations = validate_capture_entities(db_path, plan, catalog=catalog)
        failed_validation = first_failed_entity_validation(validations)
        if failed_validation is not None:
            entity_validation = graph.add_object("entity_validation", failed_validation)
            graph.add_relation(entity_validation.id, intent.id, "validates")
            answer = graph.add_object(
                "answer",
                {
                    "text": entity_validation_answer(failed_validation, catalog=catalog),
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
                    "planner_resolution_id": planner_resolution_id,
                },
            )
            graph.emit(
                "answer.created",
                {
                    "question_id": question.id,
                    "answer_id": answer.id,
                    "entity_validation_id": entity_validation.id,
                    "planner_resolution_id": planner_resolution_id,
                },
            )
            return
        graph.emit(
            "intent.created",
            {
                "question_id": question.id,
                "intent_id": intent.id,
                "planner_resolution_id": planner_resolution_id,
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
        deterministic_text = format_answer_text(rows, sql_query.data["answer_template"])
        text = deterministic_text
        answer_source = "deterministic"
        citations = [event.payload["query_result_id"]]
        llm_invocation_id = None
        llm_error = None

        question = graph.get_object(event.payload["question_id"])
        prompt = question.data.get("text", "") if question is not None else ""
        if resolved_llm_config.get("enabled"):
            full_context = (
                assemble_full_context(
                    pack,
                    prompt,
                    db_file=db_path,
                    event_store=event_store,
                    system_model_file=system_model_path,
                )
                if pack is not None
                else {}
            )
            composition_context = {
                "context_type": "activegraph.answer_composition.v01",
                "full_context": full_context,
                "sql": sql_query.data["sql"],
                "params": list(sql_query.data.get("params", [])),
                "rows": rows,
                "deterministic_answer": deterministic_text,
                "answer_template": sql_query.data["answer_template"],
            }
            context_hash = _hash_context_payload(composition_context)
            llm_invocation = graph.add_object(
                "llm_invocation",
                {
                    "provider": resolved_llm_config.get("provider"),
                    "model": resolved_llm_config.get("model"),
                    "mode": resolved_llm_config.get("mode"),
                    "status": "requested",
                    "context_hash": context_hash,
                },
            )
            llm_invocation_id = llm_invocation.id
            citations.append(llm_invocation.id)
            graph.add_relation(llm_invocation.id, event.payload["query_result_id"], "composes_from")
            graph.emit(
                "llm.invocation_requested",
                {
                    "question_id": event.payload["question_id"],
                    "query_result_id": event.payload["query_result_id"],
                    "llm_invocation_id": llm_invocation.id,
                    "provider": resolved_llm_config.get("provider"),
                    "model": resolved_llm_config.get("model"),
                    "context_hash": context_hash,
                },
            )
            try:
                composition = compose_answer_with_llm(composition_context, resolved_llm_config)
                text = composition.answer
                answer_source = "llm"
                graph.patch_object(
                    llm_invocation.id,
                    {
                        "status": "completed",
                        "latency_ms": composition.latency_ms,
                        "raw_response": composition.raw_response,
                    },
                )
                graph.emit(
                    "llm.response_received",
                    {
                        "question_id": event.payload["question_id"],
                        "llm_invocation_id": llm_invocation.id,
                        "latency_ms": composition.latency_ms,
                    },
                )
                if composition.rationale:
                    rationale = graph.add_object(
                        "decision_rationale",
                        {
                            "text": composition.rationale,
                            "source": "llm_answer_composer",
                        },
                    )
                    graph.add_relation(rationale.id, llm_invocation.id, "derived_from")
            except LLMAnswerComposerError as exc:
                llm_error = safe_display_text(str(exc))
                graph.patch_object(llm_invocation.id, {"status": "failed", "error": llm_error})
                graph.emit(
                    "llm.fallback_used",
                    {
                        "question_id": event.payload["question_id"],
                        "llm_invocation_id": llm_invocation.id,
                        "fallback": resolved_llm_config.get("fallback"),
                        "error": llm_error,
                    },
                )

        answer = graph.add_object(
            "answer",
            {
                "text": text,
                "citations": citations,
                "source": answer_source,
                "deterministic_text": deterministic_text,
                "llm_invocation_id": llm_invocation_id,
                "llm_error": llm_error,
            },
        )
        graph.add_relation(answer.id, event.payload["query_result_id"], "derived_from")
        if llm_invocation_id is not None:
            graph.add_relation(answer.id, llm_invocation_id, "composed_by")
        graph.emit(
            "answer.created",
            {
                "question_id": event.payload["question_id"],
                "sql_query_id": event.payload["sql_query_id"],
                "query_result_id": event.payload["query_result_id"],
                "answer_id": answer.id,
                "source": answer_source,
                "llm_invocation_id": llm_invocation_id,
            },
        )

    resolve_contract = behavior_contract(
        "resolve_sql_planner",
        default_on=["question.submitted"],
        default_creates=["question", "planner_resolution", "decision_rationale", "clarification_request"],
    )
    parse_contract = behavior_contract(
        "parse_intent",
        default_on=["planner.resolved"] if planner_enabled else ["question.submitted"],
        default_creates=["intent", "entity_validation", "answer"] if planner_enabled else ["question", "intent", "entity_validation", "answer"],
    )
    if planner_enabled and parse_contract["on"] == ["question.submitted"]:
        parse_contract["on"] = ["planner.resolved"]
    if planner_enabled and "question" in parse_contract["creates"]:
        parse_contract["creates"] = [item for item in parse_contract["creates"] if item != "question"]
    clarification_contract = behavior_contract(
        "request_clarification",
        default_on=["clarification.required"],
        default_creates=["answer"],
    )
    compile_contract = behavior_contract(
        "compile_sql",
        default_on=["intent.created"],
        default_creates=["sql_query"],
    )
    execute_contract = behavior_contract(
        "execute_sql",
        default_on=["sql.generated"],
        default_creates=["query_result"],
    )
    synthesize_contract = behavior_contract(
        "synthesize_answer",
        default_on=["sql.executed"],
        default_creates=["answer"],
    )

    behaviors: list[Behavior] = []
    if planner_enabled:
        behaviors.append(
            Behavior(
                name="resolve_sql_planner",
                fn=resolve_sql_planner_behavior,
                on=resolve_contract["on"],
                creates=resolve_contract["creates"],
            )
        )
    behaviors.append(
        Behavior(
            name="parse_intent",
            fn=parse_intent,
            on=parse_contract["on"],
            creates=parse_contract["creates"],
        )
    )
    behaviors.extend(
        [
            Behavior(
                name="compile_sql",
                fn=compile_sql,
                on=compile_contract["on"],
                creates=compile_contract["creates"],
            ),
            Behavior(
                name="execute_sql",
                fn=execute_sql,
                on=execute_contract["on"],
                creates=execute_contract["creates"],
            ),
            Behavior(
                name="synthesize_answer",
                fn=synthesize_answer,
                on=synthesize_contract["on"],
                creates=synthesize_contract["creates"],
            ),
        ]
    )
    if planner_enabled:
        behaviors.append(
            Behavior(
                name="request_clarification",
                fn=request_clarification,
                on=clarification_contract["on"],
                creates=clarification_contract["creates"],
            )
        )
    return behaviors

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
    system_model_file: str | Path = DEFAULT_SYSTEM_MODEL_FILE,
    pack: Any | None = None,
    llm_enabled: bool | None = None,
    ollama_base_url: str | None = None,
    ollama_model: str | None = None,
    llm_timeout: float | None = None,
    llm_config: dict[str, Any] | None = None,
    session_id: str | None = None,
    session_store_dir: str | Path = DEFAULT_SESSION_STORE_DIR,
    pack_id: str | None = None,
) -> dict[str, Any]:
    original_prompt = normalize_prompt_text(prompt)
    session_state = load_session_state(session_id, pack_id=pack_id or getattr(pack, "id", None), session_store_dir=session_store_dir)
    session_resolution = resolve_prompt_from_session(original_prompt, session_state)
    prompt = normalize_prompt_text(session_resolution.resolved_prompt)
    db_path = Path(db_file)
    system_model_path = Path(system_model_file)
    event_store_path = Path(event_store) if event_store is not None else None
    resolved_llm_config = dict(
        llm_config
        or resolve_llm_config(
            pack,
            enabled_override=llm_enabled,
            base_url_override=ollama_base_url,
            model_override=ollama_model,
            timeout_override=llm_timeout,
        )
    )
    if event_store_path is not None:
        event_store_path.parent.mkdir(parents=True, exist_ok=True)

    graph = Graph()
    runtime = Runtime(
        graph,
        behaviors=make_hospital_behaviors(db_path, system_model_file=system_model_path, pack=pack, event_store=event_store_path, llm_config=resolved_llm_config),
        budget={"max_events": 100, "max_behavior_calls": 20},
        persist_to=str(event_store_path) if event_store_path is not None else None,
    )

    question_event = Event(
        id=graph.ids.event(),
        type="question.submitted",
        payload={"prompt": prompt, "original_prompt": original_prompt, "language": "ko", "session_id": session_id, "session_resolution": session_resolution.to_dict()},
        actor="user",
        timestamp=graph.clock.now(),
    )
    graph.emit(question_event)
    runtime.run_until_idle()
    if event_store_path is not None:
        runtime.save_state()

    answer = latest_object(graph, "answer")
    intent = latest_object(graph, "intent")
    sql_query = latest_object(graph, "sql_query")
    query_result = latest_object(graph, "query_result")
    llm_invocation = latest_object(graph, "llm_invocation")
    planner_resolution = latest_object(graph, "planner_resolution")
    clarification_request = latest_object(graph, "clarification_request")
    failures = [event for event in graph.events if event.type == "behavior.failed"]

    artifacts = write_run_artifacts(graph, Path(tests_dir)) if write_artifacts else {}
    ok = answer is not None and not failures
    rows = query_result.data.get("rows", []) if query_result else []
    answer_text = answer.data["text"] if answer else ""
    session_file = None
    if session_state.get("enabled"):
        session_state = append_session_turn(
            session_state,
            run_id=graph.run_id,
            prompt=original_prompt,
            resolved_prompt=prompt,
            resolution=session_resolution.to_dict(),
            ok=ok,
            intent=intent.data if intent else None,
            sql=sql_query.data["sql"] if sql_query else None,
            params=sql_query.data.get("params", []) if sql_query else [],
            rows=rows,
            answer=answer_text,
        )
        session_file = save_session_state(session_state, session_store_dir=session_store_dir)

    return {
        "ok": ok,
        "planner": "behavior",
        "model": None,
        "prompt": original_prompt,
        "resolved_prompt": prompt,
        "run_id": graph.run_id,
        "event_store": str(event_store_path) if event_store_path is not None else None,
        "store_url": sqlite_store_url(event_store_path) if event_store_path is not None else None,
        "system_model": str(system_model_path),
        "sql": sql_query.data["sql"] if sql_query else None,
        "params": sql_query.data.get("params", []) if sql_query else [],
        "rows": rows,
        "planner_resolution": planner_resolution.data if planner_resolution else None,
        "clarification_request": clarification_request.data if clarification_request else None,
        "answer": answer_text,
        "answer_source": answer.data.get("source") if answer else None,
        "deterministic_answer": answer.data.get("deterministic_text") if answer else None,
        "llm": {
            "enabled": bool(resolved_llm_config.get("enabled")),
            "provider": resolved_llm_config.get("provider"),
            "model": resolved_llm_config.get("model"),
            "mode": resolved_llm_config.get("mode"),
            "invocation_id": llm_invocation.id if llm_invocation else None,
            "status": llm_invocation.data.get("status") if llm_invocation else None,
            "error": answer.data.get("llm_error") if answer else None,
        },
        "error": safe_display_text(failures[-1].payload.get("message")) if failures else None,
        "events": len(graph.events),
        "objects": len(graph.all_objects()),
        "session": {
            "enabled": bool(session_state.get("enabled")),
            "session_id": session_id,
            "session_file": str(session_file) if session_file is not None else session_state.get("session_file"),
            "turn_count": session_state.get("turn_count", 0),
            "resolution": session_resolution.to_dict(),
            "last_entities": session_state.get("last_entities", {}),
            "last_filters": session_state.get("last_filters", {}),
            "memory_boundaries": session_state.get("memory_boundaries", {}),
        },
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

    if "expected_answer_source" in case and result.get("answer_source") != case["expected_answer_source"]:
        failures.append(f"answer_source expected {case['expected_answer_source']!r}, got {result.get('answer_source')!r}")

    planner_expect = case.get("expected_planner_resolution")
    if isinstance(planner_expect, dict):
        planner_actual = result.get("planner_resolution") or {}
        if "status" in planner_expect and planner_actual.get("status") != planner_expect["status"]:
            failures.append(f"planner status expected {planner_expect['status']!r}, got {planner_actual.get('status')!r}")
        for expected_type in planner_expect.get("imperfection_types", []):
            if expected_type not in planner_actual.get("imperfection_types", []):
                failures.append(f"planner imperfection type missing: {expected_type!r}")
        if "selected_rule_hint" in planner_expect and planner_actual.get("selected_rule_hint") != planner_expect["selected_rule_hint"]:
            failures.append(f"planner selected_rule_hint expected {planner_expect['selected_rule_hint']!r}, got {planner_actual.get('selected_rule_hint')!r}")

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
    system_model_file: str | Path = DEFAULT_SYSTEM_MODEL_FILE,
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
                system_model_file=system_model_file,
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
        "system_model": str(Path(system_model_file)),
        "cases_file": str(Path(cases_file)),
        "passed": passed,
        "failed": failed,
        "cases": scored_cases,
    }


def behavior_specs(
    db_file: str | Path = DEFAULT_DB_FILE,
    *,
    system_model_file: str | Path = DEFAULT_SYSTEM_MODEL_FILE,
) -> list[dict[str, Any]]:
    return [
        {
            "name": behavior.name,
            "on": list(behavior.on),
            "creates": list(behavior.creates),
            "where": behavior.where,
            "pattern": behavior.pattern,
            "activate_after": behavior.activate_after,
        }
        for behavior in make_hospital_behaviors(Path(db_file), system_model_file=system_model_file)
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
    system_model_file: str | Path = DEFAULT_SYSTEM_MODEL_FILE,
    pack_id: str | None = None,
    session_store_dir: str | Path = DEFAULT_SESSION_STORE_DIR,
) -> dict[str, Any]:
    store_path = Path(event_store)
    if not store_path.exists():
        raise FileNotFoundError(f"event store does not exist: {store_path}")

    chosen_run_id = resolve_run_selector(run_selector, store_path)

    runtime = Runtime.load(str(store_path), run_id=chosen_run_id)
    graph = runtime.graph
    events = list(graph.events)
    failures = [event.to_dict() for event in events if event.type == "behavior.failed"]
    session_id = None
    for obj in graph.objects(type="question"):
        if obj.data.get("session_id"):
            session_id = obj.data.get("session_id")
            break
    before_graph = {"objects": [], "relations": []}
    before_scope = "empty_run_graph"
    session_file = None
    if session_id:
        session_state = load_session_state(
            str(session_id),
            pack_id=pack_id,
            session_store_dir=session_store_dir,
        )
        session_file = session_state.get("session_file")
        before_graph = project_session_graph_before_run(session_state, chosen_run_id)
        before_scope = "session_memory_before_run"

    return {
        "run_id": chosen_run_id,
        "run_selector": run_selector if run_selector is not None else "0",
        "event_store": str(store_path),
        "store_url": sqlite_store_url(store_path),
        "before": {
            "graph_scope": before_scope,
            "session_id": session_id,
            "session_file": session_file,
            "objects": before_graph.get("objects", []),
            "relations": before_graph.get("relations", []),
            "behaviors": behavior_specs(db_file, system_model_file=system_model_file),
        },
        "after": {
            "graph_scope": "run_graph_after_replay",
            "session_id": session_id,
            "event_count": len(events),
            "object_count": len(graph.all_objects()),
            "relation_count": len(graph.all_relations()),
            "objects": [obj.to_dict() for obj in graph.all_objects()],
            "relations": [rel.to_dict() for rel in graph.all_relations()],
        },
        "recent_events": [event_summary(event) for event in events[-tail:]],
        "failures": failures,
    }

def _run_record_to_dict(record: Any) -> dict[str, Any]:
    return {
        "run_id": record.run_id,
        "parent_run_id": record.parent_run_id,
        "forked_at_event_id": record.forked_at_event_id,
        "label": record.label,
        "created_at": record.created_at,
        "goal": record.goal,
        "frame_id": record.frame_id,
    }


def _event_store_snapshot(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "store_url": None, "exists": False, "initialized": False, "runs": []}
    store_path = Path(path)
    payload: dict[str, Any] = {
        "path": str(store_path),
        "store_url": sqlite_store_url(store_path),
        "exists": store_path.exists(),
        "initialized": False,
        "runs": [],
    }
    if not store_path.exists() or store_path.stat().st_size == 0:
        return payload
    try:
        with sqlite3.connect(str(store_path)) as conn:
            tables = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            if not {"runs", "events"}.issubset(tables):
                payload["error"] = "event store schema is not initialized"
                return payload
            payload["initialized"] = True
            event_counts = {
                row[0]: {"event_count": int(row[1]), "last_seq": row[2]}
                for row in conn.execute("SELECT run_id, COUNT(*), MAX(seq) FROM events GROUP BY run_id").fetchall()
            }
            rows = conn.execute(
                """
                SELECT run_id, parent_run_id, forked_at_event_id, label, created_at, goal, frame_id
                FROM runs
                ORDER BY created_at DESC
                """
            ).fetchall()
            payload["runs"] = [
                {
                    "run_id": row[0],
                    "parent_run_id": row[1],
                    "forked_at_event_id": row[2],
                    "label": row[3],
                    "created_at": row[4],
                    "goal": row[5],
                    "frame_id": row[6],
                    **event_counts.get(row[0], {"event_count": 0, "last_seq": None}),
                }
                for row in rows
            ]
    except sqlite3.Error as exc:
        payload["error"] = str(exc)
    return payload


def _system_model_snapshot(path: Path) -> dict[str, Any]:
    import yaml

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        data = {}
    experiment = data.get("experiment") if isinstance(data.get("experiment"), dict) else {}
    planning_model = data.get("planning_model") if isinstance(data.get("planning_model"), dict) else {}
    rule_catalog = planning_model.get("rule_catalog") if isinstance(planning_model.get("rule_catalog"), dict) else {}
    rules = rule_catalog.get("rules") if isinstance(rule_catalog.get("rules"), list) else []
    schema_projection = data.get("schema_projection") if isinstance(data.get("schema_projection"), dict) else {}
    behavior_model = data.get("behavior_model") if isinstance(data.get("behavior_model"), dict) else {}
    behaviors = behavior_model.get("behaviors") if isinstance(behavior_model.get("behaviors"), list) else []
    entity_validation = data.get("entity_validation_model") if isinstance(data.get("entity_validation_model"), dict) else {}
    validators = entity_validation.get("validators") if isinstance(entity_validation.get("validators"), dict) else {}
    return {
        "path": str(Path(path)),
        "schema_version": data.get("schema_version"),
        "kind": data.get("kind"),
        "name": data.get("name"),
        "display_name": data.get("display_name"),
        "experiment_id": experiment.get("id"),
        "rule_catalog_id": rule_catalog.get("id"),
        "rule_count": len(rules),
        "schema_projection_id": schema_projection.get("id"),
        "behavior_contract_count": len(behaviors),
        "entity_validation_model_id": entity_validation.get("id"),
        "entity_validator_count": len(validators),
    }


def activegraph_event_log_capabilities() -> list[dict[str, str]]:
    return [
        {
            "command": "inspect",
            "purpose": "Load a run from an event store and inspect status, events, behavior registry, packs, memos, or search matches.",
        },
        {
            "command": "replay",
            "purpose": "Rebuild graph state from a recorded event log without firing behaviors.",
        },
        {
            "command": "fork",
            "purpose": "Branch a historical run at a selected event for repair, re-recording, or alternate continuation.",
        },
        {
            "command": "diff",
            "purpose": "Compare two rebuilt run graphs structurally after replay/fork/repair experiments.",
        },
        {
            "command": "export-trace",
            "purpose": "Export recorded event traces as text or JSONL for external review or adaptation loops.",
        },
    ]


def world_model_snapshot(
    pack: Any,
    *,
    db_file: str | Path,
    event_store: str | Path | None,
    system_model_file: str | Path,
) -> dict[str, Any]:
    from activegraph.cli.pack_config import pack_to_dict
    from activegraph.cli.schema_context import load_schema_context_for_pack

    system_model_path = Path(system_model_file)
    schema_context = load_schema_context_for_pack(pack)
    graph_projection = schema_context.get("graph_projection", {})
    graph_objects = graph_projection.get("objects", [])
    graph_relations = graph_projection.get("relations", [])
    return {
        "ok": bool(schema_context.get("ok")),
        "snapshot_type": "activegraph.world_model.v01",
        "pack": pack_to_dict(pack),
        "system_model": _system_model_snapshot(system_model_path),
        "db": {"path": str(Path(db_file)), "exists": Path(db_file).exists()},
        "schema_context": {
            "ok": bool(schema_context.get("ok")),
            "projection_id": schema_context.get("schema_projection", {}).get("id"),
            "table_names": [table["name"] for table in schema_context.get("tables", [])],
            "validation": schema_context.get("validation"),
            "graph_projection": {
                "object_count": len(graph_objects),
                "relation_count": len(graph_relations),
                "objects": graph_objects,
                "relations": graph_relations,
            },
        },
        "behaviors": behavior_specs(db_file, system_model_file=system_model_path),
        "event_store": _event_store_snapshot(Path(event_store) if event_store is not None else None),
        "activegraph_event_log_capabilities": activegraph_event_log_capabilities(),
        "repair_loop": [
            "inspect the failing run or focused event",
            "replay to rebuild the graph from the event log",
            "fork at the divergence or decision event",
            "change pack/system-model/behavior configuration",
            "diff original and repaired run graphs",
            "export-trace for adaptation or regression cases",
        ],
    }

def echo_full_context(payload: dict[str, Any], *, as_json: bool) -> None:
    _ensure_utf8_stdout()
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    click.echo(f"context: {payload['context_type']}")
    click.echo(f"pack: {payload['pack']['id']}")
    click.echo(f"prompt: {payload['user_prompt']['text']}")
    click.echo(f"system_model: {payload['system_model']['path']}")
    click.echo(f"schema_projection: {payload['schema_context']['projection_id']}")
    click.echo(f"tables: {', '.join(table['name'] for table in payload['schema_context']['tables'])}")
    planned = payload.get('planned_intent') or {}
    click.echo(f"planned_rule: {planned.get('rule_id')}")
    if planned.get("sql"):
        click.echo(f"planned_sql: {planned['sql']}")
    trace = payload['world_state']['recent_event_trace']
    click.echo(f"recent_trace: run_id={trace.get('run_id')} events={len(trace.get('events') or [])}")
    click.echo(f"llm_required: {str(payload['llm_contract']['dependency_required_for_current_path']).lower()}")
def echo_world_model_snapshot(payload: dict[str, Any], *, as_json: bool) -> None:
    _ensure_utf8_stdout()
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    click.echo(f"snapshot: {payload['snapshot_type']}")
    click.echo(f"pack: {payload['pack']['id']}")
    click.echo(f"system_model: {payload['system_model']['path']}")
    click.echo(f"schema_projection: {payload['schema_context']['projection_id']}")
    click.echo(f"tables: {', '.join(payload['schema_context']['table_names'])}")
    click.echo(
        "graph_projection: "
        f"objects={payload['schema_context']['graph_projection']['object_count']} "
        f"relations={payload['schema_context']['graph_projection']['relation_count']}"
    )
    click.echo(f"behaviors: {', '.join(behavior['name'] for behavior in payload['behaviors'])}")
    event_store = payload["event_store"]
    click.echo(f"event_store: {event_store['path']} initialized={str(event_store['initialized']).lower()} runs={len(event_store['runs'])}")
    click.echo("event-log tools: inspect, replay, fork, diff, export-trace")
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

def _relation_source(relation: dict[str, Any]) -> str:
    return str(relation.get("source") or relation.get("from") or "")


def _relation_target(relation: dict[str, Any]) -> str:
    return str(relation.get("target") or relation.get("to") or "")


def _echo_graph_snapshot(snapshot: dict[str, Any]) -> None:
    objects = list(snapshot.get("objects") or [])
    relations = list(snapshot.get("relations") or [])
    if snapshot.get("graph_scope"):
        click.echo(f"  graph_scope: {snapshot['graph_scope']}")
    if snapshot.get("session_id"):
        click.echo(f"  session_id: {snapshot['session_id']}")
    event_count = snapshot.get("event_count")
    object_count = snapshot.get("object_count", len(objects))
    relation_count = snapshot.get("relation_count", len(relations))
    event_text = str(event_count) if event_count is not None else "-"
    click.echo(f"  events={event_text} objects={object_count} relations={relation_count}")

    click.echo("  objects:")
    if objects:
        id_width = max(14, *(len(str(obj.get("id", ""))) for obj in objects))
        type_width = max(12, *(len(str(obj.get("type", ""))) for obj in objects))
        for obj in objects:
            obj_id = str(obj.get("id", ""))
            obj_type = str(obj.get("type", ""))
            data = json.dumps(obj.get("data", {}), ensure_ascii=False)
            click.echo(f"    {obj_id:<{id_width}} {obj_type:<{type_width}} {data}")
    else:
        click.echo("    []")

    click.echo("  relations:")
    if relations:
        source_width = max(1, *(len(_relation_source(rel)) for rel in relations))
        for rel in relations:
            source = _relation_source(rel)
            target = _relation_target(rel)
            click.echo(f"    {source:<{source_width}} -[{rel['type']}]-> {target}")
    else:
        click.echo("    []")


def echo_inspect_run(payload: dict[str, Any], *, as_json: bool) -> None:
    _ensure_utf8_stdout()
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo(f"run_id: {payload['run_id']}")
    click.echo(f"store: {payload['store_url']}")

    click.echo("before ask:")
    _echo_graph_snapshot(payload["before"])
    click.echo("  behaviors:")
    for behavior in payload["before"]["behaviors"]:
        on = ",".join(behavior["on"]) or "(pattern-only)"
        creates = ",".join(behavior["creates"]) or "-"
        click.echo(f"    {behavior['name']:18s} on={on:20s} creates={creates}")

    click.echo("after ask:")
    _echo_graph_snapshot(payload["after"])

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
@click.option("--pack", "pack_id", default=None, help="Agent pack id from agent/packs.yaml.")
@click.pass_context
def cmd_text_to_sql(ctx: click.Context, pack_id: str | None) -> None:
    """Text-to-SQL behavior commands bound to the selected agent pack."""
    ctx.ensure_object(dict)
    if pack_id is not None:
        ctx.obj["pack_id"] = pack_id

@cmd_text_to_sql.command("ask")
@click.argument("prompt")
@click.option("--db-file", type=click.Path(path_type=Path), default=None, help="Override DB file from selected pack.")
@click.option("--tests-dir", type=click.Path(path_type=Path), default=DEFAULT_TESTS_DIR, show_default=True)
@click.option("--event-store", type=click.Path(path_type=Path), default=None, help="Override event store from selected pack.")
@click.option("--session-id", default=None, help="Session id for v10 multi-turn memory.")
@click.option("--session-store-dir", type=click.Path(path_type=Path), default=DEFAULT_SESSION_STORE_DIR, show_default=True)
@click.option("--llm", "llm_enabled", is_flag=True, help="Enable optional Ollama answer composition for this ask.")
@click.option("--ollama-base-url", default=None, help="Override Ollama OpenAI-compatible base URL.")
@click.option("--ollama-model", default=None, help="Override Ollama model name.")
@click.option("--llm-timeout", type=float, default=None, help="Override LLM timeout in seconds.")
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
@click.pass_context
def cmd_ask(
    ctx: click.Context,
    prompt: str,
    db_file: Path | None,
    tests_dir: Path,
    event_store: Path | None,
    session_id: str | None,
    session_store_dir: Path,
    llm_enabled: bool,
    ollama_base_url: str | None,
    ollama_model: str | None,
    llm_timeout: float | None,
    as_json: bool,
) -> None:
    """Ask one Korean database question."""
    db_file, event_store, system_model_file, pack = _resolve_pack_paths(ctx, db_file=db_file, event_store=event_store)
    payload = run_text_to_sql(
        prompt,
        db_file,
        tests_dir=tests_dir,
        event_store=event_store,
        system_model_file=system_model_file,
        pack=pack,
        llm_enabled=True if llm_enabled else None,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        llm_timeout=llm_timeout,
        session_id=session_id,
        session_store_dir=session_store_dir,
        pack_id=pack.id,
    )
    echo_result(payload, as_json=as_json)
    if not payload["ok"]:
        raise SystemExit(1)

@cmd_text_to_sql.command("eval")
@click.option("--cases", "cases_file", type=click.Path(path_type=Path), default=None, help="Override eval JSONL cases file. Defaults to the selected pack consolidated eval.")
@click.option("--db-file", type=click.Path(path_type=Path), default=None, help="Override DB file from selected pack.")
@click.option("--tests-dir", type=click.Path(path_type=Path), default=DEFAULT_TESTS_DIR, show_default=True)
@click.option("--event-store", type=click.Path(path_type=Path), default=None, help="Override event store from selected pack.")
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
@click.pass_context
def cmd_eval(
    ctx: click.Context,
    cases_file: Path | None,
    db_file: Path | None,
    tests_dir: Path,
    event_store: Path | None,
    as_json: bool,
) -> None:
    """Run JSONL Text-to-SQL behavior eval cases."""
    db_file, event_store, system_model_file, pack = _resolve_pack_paths(ctx, db_file=db_file, event_store=event_store)
    resolved_cases_file = cases_file or _default_eval_cases_file_for_pack(pack)
    payload = run_eval(
        resolved_cases_file,
        db_file,
        tests_dir=tests_dir,
        event_store=event_store,
        system_model_file=system_model_file,
    )
    echo_eval(payload, as_json=as_json)
    if not payload["ok"]:
        raise SystemExit(1)


def _cmd_inspect_impl(
    run_selector: str | None,
    event_store: Path,
    db_file: Path,
    tail: int,
    as_json: bool,
    *,
    system_model_file: str | Path = DEFAULT_SYSTEM_MODEL_FILE,
    pack_id: str | None = None,
    session_store_dir: str | Path = DEFAULT_SESSION_STORE_DIR,
) -> None:
    try:
        payload = inspect_text_to_sql_run(
            run_selector,
            event_store=event_store,
            db_file=db_file,
            tail=tail,
            system_model_file=system_model_file,
            pack_id=pack_id,
            session_store_dir=session_store_dir,
        )
    except (FileNotFoundError, IndexError) as exc:
        raise click.ClickException(str(exc)) from exc
    echo_inspect_run(payload, as_json=as_json)


@cmd_text_to_sql.command("inspect", context_settings={"ignore_unknown_options": True})
@click.argument("run_selector", required=False)
@click.option("--event-store", type=click.Path(path_type=Path), default=None, help="Override event store from selected pack.")
@click.option("--db-file", type=click.Path(path_type=Path), default=None, help="Override DB file from selected pack.")
@click.option("--tail", type=int, default=50, show_default=True, help="Number of recent events to show.")
@click.option("--session-store-dir", type=click.Path(path_type=Path), default=DEFAULT_SESSION_STORE_DIR, show_default=True)
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
@click.pass_context
def cmd_inspect(
    ctx: click.Context,
    run_selector: str | None,
    event_store: Path | None,
    db_file: Path | None,
    tail: int,
    session_store_dir: Path,
    as_json: bool,
) -> None:
    """Inspect a persisted Text-to-SQL run. Select 0, -1, -2, or a run id."""
    db_file, event_store, system_model_file, pack = _resolve_pack_paths(ctx, db_file=db_file, event_store=event_store)
    _cmd_inspect_impl(
        run_selector,
        event_store,
        db_file,
        tail,
        as_json,
        system_model_file=system_model_file,
        pack_id=pack.id,
        session_store_dir=session_store_dir,
    )


@cmd_text_to_sql.command("inspect-run", hidden=True, context_settings={"ignore_unknown_options": True})
@click.argument("run_selector", required=False)
@click.option("--event-store", type=click.Path(path_type=Path), default=None, help="Override event store from selected pack.")
@click.option("--db-file", type=click.Path(path_type=Path), default=None, help="Override DB file from selected pack.")
@click.option("--tail", type=int, default=50, show_default=True, help="Number of recent events to show.")
@click.option("--session-store-dir", type=click.Path(path_type=Path), default=DEFAULT_SESSION_STORE_DIR, show_default=True)
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
@click.pass_context
def cmd_inspect_run(
    ctx: click.Context,
    run_selector: str | None,
    event_store: Path | None,
    db_file: Path | None,
    tail: int,
    session_store_dir: Path,
    as_json: bool,
) -> None:
    """Compatibility alias for inspect."""
    db_file, event_store, system_model_file, pack = _resolve_pack_paths(ctx, db_file=db_file, event_store=event_store)
    _cmd_inspect_impl(
        run_selector,
        event_store,
        db_file,
        tail,
        as_json,
        system_model_file=system_model_file,
        pack_id=pack.id,
        session_store_dir=session_store_dir,
    )


def echo_adaptation_analysis(payload: dict[str, Any], *, as_json: bool) -> None:
    _ensure_utf8_stdout()
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    click.echo(f"adaptation_analysis: {payload['analysis_type']}")
    click.echo(f"source_run_id: {payload['source_run_id']}")
    click.echo(f"event_store: {payload['event_store']}")
    summary = payload["summary"]
    click.echo(
        "summary: "
        f"proposals={summary['proposal_count']} "
        f"unsupported={summary['unsupported_prompts']} "
        f"validation_misses={summary['validation_misses']} "
        f"llm_fallbacks={summary['llm_fallbacks']}"
    )
    for proposal in payload["proposals"]:
        evidence = proposal.get("evidence") or {}
        click.echo(f"proposal: {proposal['id']} classification={proposal['classification']} status={proposal['status']}")
        if evidence.get("prompt"):
            click.echo(f"  prompt: {evidence['prompt']}")
        click.echo(f"  target: {proposal['target']['kind']}")
    artifacts = payload.get("artifacts") or {}
    if artifacts.get("analysis_file"):
        click.echo(f"analysis_file: {artifacts['analysis_file']}")


def echo_adaptation_acceptance(payload: dict[str, Any], *, as_json: bool) -> None:
    _ensure_utf8_stdout()
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    click.echo(f"accepted: {payload['proposal_id']}")
    artifacts = payload.get("generated_artifacts") or {}
    for name, path in artifacts.items():
        click.echo(f"{name}: {path}")


@cmd_text_to_sql.command("adapt")
@click.argument("run_selector", required=False)
@click.option("--event-store", type=click.Path(path_type=Path), default=None, help="Override event store from selected pack.")
@click.option("--db-file", type=click.Path(path_type=Path), default=None, help="Override DB file from selected pack.")
@click.option("--output-dir", type=click.Path(path_type=Path), default=None, help="Directory for adaptation analysis/proposal artifacts.")
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
@click.pass_context
def cmd_adapt(
    ctx: click.Context,
    run_selector: str | None,
    event_store: Path | None,
    db_file: Path | None,
    output_dir: Path | None,
    as_json: bool,
) -> None:
    """Analyze a persisted run and write v09 adaptation proposal artifacts."""
    db_file, event_store, system_model_file, pack = _resolve_pack_paths(ctx, db_file=db_file, event_store=event_store)
    from activegraph.cli.adaptation import DEFAULT_ADAPTATION_DIR, analyze_text_to_sql_adaptation

    try:
        payload = analyze_text_to_sql_adaptation(
            event_store,
            run_selector=run_selector or "0",
            output_dir=output_dir or DEFAULT_ADAPTATION_DIR,
            pack_id=pack.id,
            system_model_file=system_model_file,
        )
    except (FileNotFoundError, IndexError) as exc:
        raise click.ClickException(str(exc)) from exc
    echo_adaptation_analysis(payload, as_json=as_json)


@cmd_text_to_sql.command("adapt-accept")
@click.argument("proposal_file", type=click.Path(path_type=Path))
@click.option("--output-dir", type=click.Path(path_type=Path), default=None, help="Directory for accepted eval/patch-hint artifacts.")
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
def cmd_adapt_accept(proposal_file: Path, output_dir: Path | None, as_json: bool) -> None:
    """Accept one adaptation proposal and generate draft eval/patch artifacts."""
    from activegraph.cli.adaptation import accept_adaptation_proposal

    payload = accept_adaptation_proposal(proposal_file, output_dir=output_dir)
    echo_adaptation_acceptance(payload, as_json=as_json)
@cmd_text_to_sql.command("context")
@click.argument("prompt")
@click.option("--db-file", type=click.Path(path_type=Path), default=None, help="Override DB file from selected pack.")
@click.option("--event-store", type=click.Path(path_type=Path), default=None, help="Override event store from selected pack.")
@click.option("--session-id", default=None, help="Session id for v10 multi-turn memory.")
@click.option("--session-store-dir", type=click.Path(path_type=Path), default=DEFAULT_SESSION_STORE_DIR, show_default=True)
@click.option("--run", "run_selector", default="0", show_default=True, help="Recent event trace run selector: 0, -1, -2, or run id.")
@click.option("--tail", type=int, default=8, show_default=True, help="Number of recent events to include.")
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
@click.pass_context
def cmd_context(
    ctx: click.Context,
    prompt: str,
    db_file: Path | None,
    event_store: Path | None,
    session_id: str | None,
    session_store_dir: Path,
    run_selector: str,
    tail: int,
    as_json: bool,
) -> None:
    """Assemble the deterministic Full Context for one prompt without executing SQL."""
    db_file, event_store, system_model_file, pack = _resolve_pack_paths(ctx, db_file=db_file, event_store=event_store)
    payload = assemble_full_context(
        pack,
        prompt,
        db_file=db_file,
        event_store=event_store,
        system_model_file=system_model_file,
        run_selector=run_selector,
        tail=tail,
        session_id=session_id,
        session_store_dir=session_store_dir,
    )
    echo_full_context(payload, as_json=as_json)
    if not payload["ok"]:
        raise SystemExit(1)
@cmd_text_to_sql.command("snapshot")
@click.option("--db-file", type=click.Path(path_type=Path), default=None, help="Override DB file from selected pack.")
@click.option("--event-store", type=click.Path(path_type=Path), default=None, help="Override event store from selected pack.")
@click.option("--json", "as_json", is_flag=True, help="Print the full JSON payload.")
@click.pass_context
def cmd_snapshot(ctx: click.Context, db_file: Path | None, event_store: Path | None, as_json: bool) -> None:
    """Print the selected pack's current world-model snapshot."""
    db_file, event_store, system_model_file, pack = _resolve_pack_paths(ctx, db_file=db_file, event_store=event_store)
    payload = world_model_snapshot(
        pack,
        db_file=db_file,
        event_store=event_store,
        system_model_file=system_model_file,
    )
    echo_world_model_snapshot(payload, as_json=as_json)
    if not payload["ok"]:
        raise SystemExit(1)
@cmd_text_to_sql.command("repl")
@click.option("--db-file", type=click.Path(path_type=Path), default=None, help="Override DB file from selected pack.")
@click.option("--tests-dir", type=click.Path(path_type=Path), default=DEFAULT_TESTS_DIR, show_default=True)
@click.option("--event-store", type=click.Path(path_type=Path), default=None, help="Override event store from selected pack.")
@click.option("--session-id", default=None, help="Session id for v10 multi-turn memory; defaults to a pack-scoped REPL session.")
@click.option("--session-store-dir", type=click.Path(path_type=Path), default=DEFAULT_SESSION_STORE_DIR, show_default=True)
@click.pass_context
def cmd_repl(ctx: click.Context, db_file: Path | None, tests_dir: Path, event_store: Path | None, session_id: str | None, session_store_dir: Path) -> None:
    """Start an interactive Text-to-SQL REPL."""
    db_file, event_store, system_model_file, pack = _resolve_pack_paths(ctx, db_file=db_file, event_store=event_store)
    _ensure_utf8_stdout()
    session_id = session_id or f"{pack.id}-repl"
    click.echo(f"{pack.id} Text-to-SQL REPL. Type exit or quit to leave. session={session_id}")
    while True:
        try:
            prompt = input(f"{pack.id}> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo()
            return
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit", "q", ":q"}:
            return
        payload = run_text_to_sql(
            prompt,
            db_file,
            tests_dir=tests_dir,
            event_store=event_store,
            system_model_file=system_model_file,
            pack=pack,
            session_id=session_id,
            session_store_dir=session_store_dir,
            pack_id=pack.id,
        )
        echo_result(payload, as_json=False)








































