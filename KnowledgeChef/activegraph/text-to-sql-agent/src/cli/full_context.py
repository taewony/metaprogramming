"""Full Context assembly for pack-selected Text-to-SQL runs."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from activegraph.cli.hospital_logic import RuleCatalogError, load_rule_catalog_from_system_model, normalize_prompt_text
from activegraph.cli.llm_answer import resolve_llm_config
from activegraph.cli.pack_config import pack_to_dict
from activegraph.cli.schema_context import load_schema_context_for_pack
from activegraph.cli.session_memory import (
    DEFAULT_SESSION_STORE_DIR,
    load_session_state,
    memory_boundaries,
    resolve_prompt_from_session,
)

TEXT_TO_SQL_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = TEXT_TO_SQL_DIR / "agent"
DEFAULT_INSTRUCTIONS_FILE = AGENT_DIR / "instructions.md"


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def _system_prompt(path: Path = DEFAULT_INSTRUCTIONS_FILE) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    return {
        "source": str(path),
        "is_empty": not bool(text.strip()),
        "text": text.strip(),
    }


def _system_model_slice(path: Path) -> dict[str, Any]:
    data = _read_yaml(path)
    planning_model = data.get("planning_model") if isinstance(data.get("planning_model"), dict) else {}
    rule_catalog = planning_model.get("rule_catalog") if isinstance(planning_model.get("rule_catalog"), dict) else {}
    rules = rule_catalog.get("rules") if isinstance(rule_catalog.get("rules"), list) else []
    behavior_model = data.get("behavior_model") if isinstance(data.get("behavior_model"), dict) else {}
    behaviors = behavior_model.get("behaviors") if isinstance(behavior_model.get("behaviors"), list) else []
    entity_validation = data.get("entity_validation_model") if isinstance(data.get("entity_validation_model"), dict) else {}
    schema_projection = data.get("schema_projection") if isinstance(data.get("schema_projection"), dict) else {}
    full_context_model = data.get("full_context_model") if isinstance(data.get("full_context_model"), dict) else {}

    return {
        "path": str(path),
        "schema_version": data.get("schema_version"),
        "name": data.get("name"),
        "display_name": data.get("display_name"),
        "experiment_id": (data.get("experiment") or {}).get("id") if isinstance(data.get("experiment"), dict) else None,
        "schema_projection_id": schema_projection.get("id"),
        "full_context_model": {
            "id": full_context_model.get("id"),
            "components": list(full_context_model.get("components") or []),
            "llm_dependency": full_context_model.get("llm_dependency") or {},
        },
        "rule_catalog": {
            "id": rule_catalog.get("id"),
            "version": rule_catalog.get("version"),
            "rule_count": len(rules),
            "rules": [
                {
                    "id": rule.get("id"),
                    "priority": rule.get("priority"),
                    "description": rule.get("description"),
                    "eval_refs": list(rule.get("eval_refs") or []),
                }
                for rule in rules
                if isinstance(rule, dict)
            ],
        },
        "behaviors": [
            {
                "id": behavior.get("id"),
                "implementation": behavior.get("implementation"),
                "runtime": behavior.get("runtime") or {},
            }
            for behavior in behaviors
            if isinstance(behavior, dict)
        ],
        "entity_validation_model": {
            "id": entity_validation.get("id"),
            "validator_count": len(entity_validation.get("validators") or {}) if isinstance(entity_validation.get("validators"), dict) else 0,
            "validators": list((entity_validation.get("validators") or {}).keys()) if isinstance(entity_validation.get("validators"), dict) else [],
        },
    }


def _schema_slice(schema_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(schema_context.get("ok")),
        "projection_id": schema_context.get("schema_projection", {}).get("id"),
        "validation": schema_context.get("validation"),
        "tables": [
            {
                "name": table.get("name"),
                "description": table.get("description"),
                "columns": [
                    {
                        "name": column.get("name"),
                        "type": column.get("type"),
                        "description": column.get("description"),
                    }
                    for column in table.get("columns", [])
                    if isinstance(column, dict)
                ],
            }
            for table in schema_context.get("tables", [])
            if isinstance(table, dict)
        ],
    }


def _run_ids_by_recency(event_store: Path) -> list[str]:
    if not event_store.exists() or event_store.stat().st_size == 0:
        return []
    try:
        with sqlite3.connect(str(event_store)) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
            if not {"runs", "events"}.issubset(tables):
                return []
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
    except sqlite3.Error:
        return []


def _resolve_run_selector(selector: str | None, event_store: Path) -> str | None:
    run_ids = _run_ids_by_recency(event_store)
    if not run_ids:
        return None
    if selector is None or selector == "" or selector == "0":
        return run_ids[0]
    if selector.startswith("-") and selector[1:].isdigit():
        offset = abs(int(selector))
        return run_ids[offset] if offset < len(run_ids) else None
    return selector


def _recent_event_trace(event_store: Path | None, *, run_selector: str | None, tail: int) -> dict[str, Any]:
    if event_store is None:
        return {"event_store": None, "run_id": None, "events": []}
    store_path = Path(event_store)
    run_id = _resolve_run_selector(run_selector, store_path)
    if run_id is None:
        return {"event_store": str(store_path), "run_id": None, "events": []}
    try:
        with sqlite3.connect(str(store_path)) as conn:
            rows = conn.execute(
                """
                SELECT id, type, actor, caused_by, timestamp, payload
                FROM events
                WHERE run_id = ?
                ORDER BY seq DESC
                LIMIT ?
                """,
                [run_id, tail],
            ).fetchall()
    except sqlite3.Error as exc:
        return {"event_store": str(store_path), "run_id": run_id, "events": [], "error": str(exc)}

    events = []
    for row in reversed(rows):
        try:
            payload = json.loads(row[5])
        except json.JSONDecodeError:
            payload = {}
        events.append(
            {
                "id": row[0],
                "type": row[1],
                "actor": row[2],
                "caused_by": row[3],
                "timestamp": row[4],
                "payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
            }
        )
    return {"event_store": str(store_path), "run_id": run_id, "events": events}


def _planned_intent(prompt: str, system_model_file: Path) -> dict[str, Any]:
    try:
        catalog = load_rule_catalog_from_system_model(system_model_file)
        plan = catalog.plan(prompt)
    except (RuleCatalogError, ValueError) as exc:
        return {"ok": False, "error": str(exc), "rule_id": None}
    return {
        "ok": True,
        "rule_id": plan.rule_id,
        "intent": plan.intent,
        "sql": plan.sql,
        "params": plan.params,
        "answer_template": plan.answer_template,
    }


def assemble_full_context(
    pack: Any,
    prompt: str,
    *,
    db_file: str | Path | None = None,
    event_store: str | Path | None = None,
    system_model_file: str | Path | None = None,
    instructions_file: str | Path = DEFAULT_INSTRUCTIONS_FILE,
    run_selector: str | None = "0",
    tail: int = 8,
    session_id: str | None = None,
    session_store_dir: str | Path = DEFAULT_SESSION_STORE_DIR,
) -> dict[str, Any]:
    original_prompt = normalize_prompt_text(prompt)
    session_state = load_session_state(session_id, pack_id=getattr(pack, "id", None), session_store_dir=session_store_dir)
    session_resolution = resolve_prompt_from_session(original_prompt, session_state)
    prompt = normalize_prompt_text(session_resolution.resolved_prompt)
    db_path = Path(db_file) if db_file is not None else pack.db_file
    event_store_path = Path(event_store) if event_store is not None else pack.event_store
    system_model_path = Path(system_model_file) if system_model_file is not None else pack.system_model
    schema_context = load_schema_context_for_pack(pack)
    llm_config = resolve_llm_config(pack)
    boundaries = memory_boundaries(
        session_id=session_id,
        session_file=session_state.get("session_file"),
        pack_kb_root=getattr(pack, "kb_root", None),
    )
    return {
        "ok": bool(schema_context.get("ok")),
        "context_type": "activegraph.full_context.v01",
        "assembly": {
            "mode": "deterministic",
            "llm_adapter": {"provider": llm_config["provider"], "model": llm_config["model"], "enabled": llm_config["enabled"]} if llm_config["enabled"] else None,
            "replay_safe": True,
            "run_selector": run_selector,
            "event_tail": tail,
        },
        "pack": pack_to_dict(pack),
        "user_prompt": {"text": original_prompt, "language": "ko"},
        "resolved_prompt": {"text": prompt, "changed": prompt != original_prompt},
        "system_prompt": _system_prompt(Path(instructions_file)),
        "system_model": _system_model_slice(system_model_path),
        "schema_context": _schema_slice(schema_context),
        "world_state": {
            "db": {"path": str(db_path) if db_path is not None else None, "exists": bool(db_path and db_path.exists())},
            "recent_event_trace": _recent_event_trace(event_store_path, run_selector=run_selector, tail=tail),
        },
        "session_context": {
            "enabled": bool(session_state.get("enabled")),
            "session_id": session_id,
            "session_file": session_state.get("session_file"),
            "turn_count": session_state.get("turn_count", 0),
            "last_entities": session_state.get("last_entities", {}),
            "last_filters": session_state.get("last_filters", {}),
            "resolution": session_resolution.to_dict(),
            "resolved_prompt": prompt,
            "graph": session_state.get("graph", {"objects": [], "relations": []}),
        },
        "memory_boundaries": boundaries,
        "planned_intent": _planned_intent(prompt, system_model_path),
        "kb_context": {
            "enabled": bool(pack.capabilities.get("kb", False)),
            "root": str(pack.kb_root) if pack.kb_root else None,
            "snippets": [],
            "write_policy": "approval-gated" if pack.kb.get("approval_required") else "disabled",
        },
        "llm_contract": {
            "dependency_required_for_current_path": False,
            "adapter_injection_point": "v06.llm_adapter",
            "provider": llm_config["provider"],
            "model": llm_config["model"],
            "enabled_by_pack": llm_config["enabled"],
            "mode": llm_config["mode"],
            "fallback": llm_config["fallback"],
            "records_to_graph_objects": ["llm_invocation", "decision_rationale"],
        },
    }
