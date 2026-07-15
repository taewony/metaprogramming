"""Session-scoped graph memory for Text-to-SQL multi-turn runs.

The v10 store is deliberately local and explicit: each session is a small JSON
projection under `.tests/sessions`, while immutable run evidence stays in the
SQLite event store.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEXT_TO_SQL_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SESSION_STORE_DIR = TEXT_TO_SQL_DIR / ".tests" / "sessions"
DEFAULT_ADAPTATION_ARTIFACT_DIR = TEXT_TO_SQL_DIR / ".tests" / "adaptations"


@dataclass(frozen=True)
class SessionResolution:
    original_prompt: str
    resolved_prompt: str
    resolved: bool
    strategy: str
    entity_type: str | None = None
    entity_value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_prompt": self.original_prompt,
            "resolved_prompt": self.resolved_prompt,
            "resolved": self.resolved,
            "strategy": self.strategy,
            "entity_type": self.entity_type,
            "entity_value": self.entity_value,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return safe or "default"


def session_file_path(
    session_id: str,
    *,
    pack_id: str | None = None,
    session_store_dir: str | Path = DEFAULT_SESSION_STORE_DIR,
) -> Path:
    root = Path(session_store_dir)
    if pack_id:
        root = root / _safe_id(pack_id)
    return root / f"{_safe_id(session_id)}.json"


def memory_boundaries(
    *,
    session_id: str | None = None,
    session_file: str | Path | None = None,
    pack_kb_root: str | Path | None = None,
) -> dict[str, Any]:
    return {
        "current_run": {
            "kind": "ephemeral_graph",
            "description": "Graph() objects and relations created for the currently executing run.",
        },
        "session_memory": {
            "kind": "local_json_graph",
            "session_id": session_id,
            "path": str(session_file) if session_file is not None else None,
            "description": "Conversation-scoped graph projection used for deterministic multi-turn resolution.",
        },
        "pack_kb": {
            "kind": "okf_bundle_or_disabled",
            "path": str(pack_kb_root) if pack_kb_root is not None else None,
            "description": "Pack-scoped external knowledge; not mutated by DB query session memory.",
        },
        "long_term_adaptation": {
            "kind": "adaptation_artifacts",
            "path": str(DEFAULT_ADAPTATION_ARTIFACT_DIR),
            "description": "Event-log adaptation proposals and accepted draft artifacts, outside session memory.",
        },
    }


def _empty_state(session_id: str, *, pack_id: str | None, session_file: Path) -> dict[str, Any]:
    return {
        "schema_version": "activegraph.session_memory.v01",
        "session_id": session_id,
        "pack_id": pack_id,
        "created_at": _utc_now(),
        "updated_at": None,
        "turn_count": 0,
        "turns": [],
        "last_entities": {},
        "last_filters": {},
        "unresolved_references": [],
        "graph": {"objects": [], "relations": []},
        "memory_boundaries": memory_boundaries(session_id=session_id, session_file=session_file),
    }


def load_session_state(
    session_id: str | None,
    *,
    pack_id: str | None = None,
    session_store_dir: str | Path = DEFAULT_SESSION_STORE_DIR,
) -> dict[str, Any]:
    if not session_id:
        return {
            "schema_version": "activegraph.session_memory.v01",
            "enabled": False,
            "session_id": None,
            "pack_id": pack_id,
            "turn_count": 0,
            "turns": [],
            "last_entities": {},
            "last_filters": {},
            "unresolved_references": [],
            "graph": {"objects": [], "relations": []},
            "memory_boundaries": memory_boundaries(),
        }
    path = session_file_path(session_id, pack_id=pack_id, session_store_dir=session_store_dir)
    if not path.exists():
        state = _empty_state(session_id, pack_id=pack_id, session_file=path)
    else:
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = _empty_state(session_id, pack_id=pack_id, session_file=path)
    state["enabled"] = True
    state["session_file"] = str(path)
    state["turn_count"] = len(state.get("turns") or [])
    state.setdefault("last_entities", {})
    state.setdefault("last_filters", {})
    state.setdefault("unresolved_references", [])
    state.setdefault("graph", {"objects": [], "relations": []})
    state["memory_boundaries"] = memory_boundaries(session_id=session_id, session_file=path)
    return state


def save_session_state(
    state: dict[str, Any],
    *,
    session_store_dir: str | Path = DEFAULT_SESSION_STORE_DIR,
) -> Path | None:
    session_id = state.get("session_id")
    if not session_id:
        return None
    pack_id = state.get("pack_id")
    path = session_file_path(str(session_id), pack_id=pack_id, session_store_dir=session_store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = dict(state)
    state["updated_at"] = _utc_now()
    state["turn_count"] = len(state.get("turns") or [])
    state["session_file"] = str(path)
    state["memory_boundaries"] = memory_boundaries(session_id=str(session_id), session_file=path)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def resolve_prompt_from_session(prompt: str, state: dict[str, Any]) -> SessionResolution:
    prompt = str(prompt).strip()
    if not state.get("enabled"):
        return SessionResolution(prompt, prompt, False, "disabled")

    last_entities = state.get("last_entities") or {}
    doctor_name = last_entities.get("doctor.name")
    if doctor_name and ("그 의사" in prompt or "그의사" in prompt):
        resolved = prompt.replace("그 의사", f"{doctor_name} 의사").replace("그의사", f"{doctor_name}의사")
        return SessionResolution(prompt, resolved, True, "doctor_anaphora", "doctor.name", doctor_name)

    customer_grade = last_entities.get("customer.grade")
    compact = re.sub(r"\s+", "", prompt.lower())
    if customer_grade == "VIP" and "vip" not in compact and "몇" in prompt and any(token in prompt for token in ["명", "고객", "회원"]):
        return SessionResolution(prompt, f"VIP {prompt}", True, "vip_ellipsis", "customer.grade", "VIP")

    return SessionResolution(prompt, prompt, False, "none")


def extract_entities_from_intent(intent: dict[str, Any] | None, params: list[Any] | None = None) -> dict[str, str]:
    if not isinstance(intent, dict):
        return {}
    entities: dict[str, str] = {}
    rule_id = str(intent.get("rule_id") or "")
    filters = intent.get("filters") if isinstance(intent.get("filters"), dict) else {}
    if isinstance(filters, dict) and filters.get("name") and (rule_id.startswith("doctor_") or intent.get("entity") == "doctors"):
        entities["doctor.name"] = str(filters["name"])
    if intent.get("filter") == "vip" or intent.get("filter") == "vip_customers_confirmed_orders":
        entities["customer.grade"] = "VIP"
    for value in params or []:
        if value == "VIP":
            entities["customer.grade"] = "VIP"
    return entities


def _graph_from_turns(turns: list[dict[str, Any]], *, session_id: str) -> dict[str, list[dict[str, Any]]]:
    objects: list[dict[str, Any]] = [
        {"id": f"session:{session_id}", "type": "session", "data": {"session_id": session_id}}
    ]
    relations: list[dict[str, Any]] = []
    for index, turn in enumerate(turns, start=1):
        turn_id = f"turn:{index}"
        objects.append(
            {
                "id": turn_id,
                "type": "session_turn",
                "data": {
                    "run_id": turn.get("run_id"),
                    "prompt": turn.get("prompt"),
                    "resolved_prompt": turn.get("resolved_prompt"),
                    "ok": turn.get("ok"),
                    "rule_id": (turn.get("intent") or {}).get("rule_id"),
                },
            }
        )
        relations.append({"source": turn_id, "type": "belongs_to_session", "target": f"session:{session_id}"})
        for entity_type, entity_value in (turn.get("entities") or {}).items():
            entity_id = f"entity:{entity_type}:{entity_value}"
            objects.append({"id": entity_id, "type": "entity", "data": {"entity_type": entity_type, "value": entity_value}})
            relations.append({"source": turn_id, "type": "mentions", "target": entity_id})
    deduped: dict[str, dict[str, Any]] = {}
    for obj in objects:
        deduped[obj["id"]] = obj
    return {"objects": list(deduped.values()), "relations": relations}


def project_session_graph_before_run(state: dict[str, Any], run_id: str | None) -> dict[str, list[dict[str, Any]]]:
    """Return the session graph that existed before ``run_id`` was appended."""
    if not state.get("enabled"):
        return {"objects": [], "relations": []}
    turns = list(state.get("turns") or [])
    if run_id:
        before: list[dict[str, Any]] = []
        for turn in turns:
            if turn.get("run_id") == run_id:
                break
            before.append(turn)
        turns = before
    return _graph_from_turns(turns, session_id=str(state.get("session_id"))) if turns else _graph_from_turns([], session_id=str(state.get("session_id")))

def append_session_turn(
    state: dict[str, Any],
    *,
    run_id: str,
    prompt: str,
    resolved_prompt: str,
    resolution: dict[str, Any],
    ok: bool,
    intent: dict[str, Any] | None,
    sql: str | None,
    params: list[Any],
    rows: list[list[Any]],
    answer: str,
) -> dict[str, Any]:
    if not state.get("enabled"):
        return state
    turns = list(state.get("turns") or [])
    entities = extract_entities_from_intent(intent, params)
    turn = {
        "turn_id": len(turns) + 1,
        "run_id": run_id,
        "created_at": _utc_now(),
        "prompt": prompt,
        "resolved_prompt": resolved_prompt,
        "resolution": resolution,
        "ok": ok,
        "intent": intent or {},
        "entities": entities,
        "filters": (intent or {}).get("filters") or {"filter": (intent or {}).get("filter")} if intent else {},
        "sql": sql,
        "params": params,
        "rows": rows,
        "answer": answer,
    }
    turns.append(turn)
    state = dict(state)
    state["turns"] = turns
    state["turn_count"] = len(turns)
    state["updated_at"] = _utc_now()
    last_entities = dict(state.get("last_entities") or {})
    last_entities.update(entities)
    state["last_entities"] = last_entities
    if intent:
        last_filters = dict(state.get("last_filters") or {})
        for key, value in ((intent.get("filters") if isinstance(intent.get("filters"), dict) else {}) or {}).items():
            last_filters[key] = value
        if intent.get("filter"):
            last_filters["filter"] = intent.get("filter")
        state["last_filters"] = last_filters
    if resolution.get("resolved") is False and any(token in prompt for token in ["그", "이전", "그럼"]):
        unresolved = list(state.get("unresolved_references") or [])
        unresolved.append({"prompt": prompt, "run_id": run_id, "created_at": _utc_now()})
        state["unresolved_references"] = unresolved
    state["graph"] = _graph_from_turns(turns, session_id=str(state.get("session_id")))
    return state

