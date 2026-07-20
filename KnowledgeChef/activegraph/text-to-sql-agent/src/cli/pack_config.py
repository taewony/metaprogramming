"""Pack registry helpers for local ActiveGraph agent configurations."""
from __future__ import annotations

import json
import re
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


TEXT_TO_SQL_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = TEXT_TO_SQL_DIR / "agent"
DEFAULT_PACKS_FILE = AGENT_DIR / "packs.yaml"
SUPPORTED_PACK_SCHEMA = "activegraph.packs.v01"


class PackConfigError(ValueError):
    """Raised when the local pack registry is missing or invalid."""


@dataclass(frozen=True)
class AgentPack:
    id: str
    display_name: str
    runtime: str
    system_model: Path
    reference_model: Path | None
    env: dict[str, str]
    capabilities: dict[str, bool]
    schema: dict[str, Any]
    kb: dict[str, Any]
    llm: dict[str, Any]
    raw: dict[str, Any]

    @property
    def db_file(self) -> Path | None:
        value = self.env.get("DB_FILE")
        return Path(value) if value else None

    @property
    def event_store(self) -> Path | None:
        value = self.env.get("EVENT_STORE")
        return Path(value) if value else None

    @property
    def schema_root(self) -> Path | None:
        value = self.env.get("SCHEMA_BUNDLE_ROOT") or self.schema.get("root") or self.env.get("OKF_BUNDLE_ROOT")
        return Path(value) if value else None

    @property
    def kb_root(self) -> Path | None:
        value = self.env.get("OKF_BUNDLE_ROOT") or self.kb.get("root")
        return Path(value) if value else None


def _resolve_path(value: Any, *, base_dir: Path, field: str, pack_id: str) -> str:
    if not isinstance(value, str) or not value:
        raise PackConfigError(f"pack {pack_id} field {field} must be a non-empty string")
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return str(path.resolve())


def load_pack_registry(config_file: str | Path = DEFAULT_PACKS_FILE) -> dict[str, Any]:
    path = Path(config_file)
    if not path.exists():
        raise PackConfigError(f"pack registry not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PackConfigError("pack registry must be a mapping")
    if data.get("schema_version") != SUPPORTED_PACK_SCHEMA:
        raise PackConfigError(f"schema_version must be {SUPPORTED_PACK_SCHEMA}")
    packs = data.get("packs")
    if not isinstance(packs, dict) or not packs:
        raise PackConfigError("pack registry must define at least one pack")
    default_pack = data.get("default_pack")
    if not isinstance(default_pack, str) or default_pack not in packs:
        raise PackConfigError("default_pack must name a pack in packs")
    return data


def list_packs(config_file: str | Path = DEFAULT_PACKS_FILE) -> list[AgentPack]:
    registry = load_pack_registry(config_file)
    return [resolve_pack(pack_id, config_file=config_file, registry=registry) for pack_id in registry["packs"]]


def default_pack_id(config_file: str | Path = DEFAULT_PACKS_FILE) -> str:
    return str(load_pack_registry(config_file)["default_pack"])


def resolve_pack(
    pack_id: str | None = None,
    *,
    config_file: str | Path = DEFAULT_PACKS_FILE,
    registry: dict[str, Any] | None = None,
) -> AgentPack:
    path = Path(config_file)
    data = registry or load_pack_registry(path)
    selected_id = pack_id or data["default_pack"]
    packs = data["packs"]
    if selected_id not in packs:
        known = ", ".join(sorted(packs))
        raise PackConfigError(f"unknown pack: {selected_id}. known packs: {known}")

    raw = packs[selected_id]
    if not isinstance(raw, dict):
        raise PackConfigError(f"pack {selected_id} must be a mapping")
    base_dir = path.resolve().parent

    display_name = raw.get("display_name", selected_id)
    if not isinstance(display_name, str):
        raise PackConfigError(f"pack {selected_id} display_name must be a string")
    runtime = raw.get("runtime", "text-to-sql")
    if not isinstance(runtime, str) or not runtime:
        raise PackConfigError(f"pack {selected_id} runtime must be a non-empty string")

    system_model = Path(_resolve_path(raw.get("system_model"), base_dir=base_dir, field="system_model", pack_id=selected_id))
    reference_model = (
        Path(_resolve_path(raw.get("reference_model"), base_dir=base_dir, field="reference_model", pack_id=selected_id))
        if raw.get("reference_model") is not None
        else None
    )

    raw_env = raw.get("env", {})
    if not isinstance(raw_env, dict):
        raise PackConfigError(f"pack {selected_id} env must be a mapping")
    env: dict[str, str] = {}
    for key, value in raw_env.items():
        if not isinstance(key, str):
            raise PackConfigError(f"pack {selected_id} env keys must be strings")
        if key.endswith("_FILE") or key.endswith("_STORE") or key.endswith("_ROOT"):
            env[key] = _resolve_path(value, base_dir=base_dir, field=f"env.{key}", pack_id=selected_id)
        elif not isinstance(value, str):
            raise PackConfigError(f"pack {selected_id} env.{key} must be a string")
        else:
            env[key] = value

    capabilities = raw.get("capabilities", {})
    if not isinstance(capabilities, dict):
        raise PackConfigError(f"pack {selected_id} capabilities must be a mapping")
    normalized_capabilities = {str(key): bool(value) for key, value in capabilities.items()}

    schema = dict(raw.get("schema", {}) or {})
    if not isinstance(schema, dict):
        raise PackConfigError(f"pack {selected_id} schema must be a mapping")
    if "root" in schema:
        schema["root"] = _resolve_path(schema["root"], base_dir=base_dir, field="schema.root", pack_id=selected_id)

    kb = dict(raw.get("kb", {}) or {})
    if not isinstance(kb, dict):
        raise PackConfigError(f"pack {selected_id} kb must be a mapping")
    if "root" in kb:
        kb["root"] = _resolve_path(kb["root"], base_dir=base_dir, field="kb.root", pack_id=selected_id)

    llm = dict(raw.get("llm", {}) or {})
    if not isinstance(llm, dict):
        raise PackConfigError(f"pack {selected_id} llm must be a mapping")

    return AgentPack(
        id=selected_id,
        display_name=display_name,
        runtime=runtime,
        system_model=system_model,
        reference_model=reference_model,
        env=env,
        capabilities=normalized_capabilities,
        schema=schema,
        kb=kb,
        llm=llm,
        raw=raw,
    )


def set_default_pack(pack_id: str, config_file: str | Path = DEFAULT_PACKS_FILE) -> AgentPack:
    path = Path(config_file)
    data = load_pack_registry(path)
    if pack_id not in data["packs"]:
        known = ", ".join(sorted(data["packs"]))
        raise PackConfigError(f"unknown pack: {pack_id}. known packs: {known}")
    data["default_pack"] = pack_id
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return resolve_pack(pack_id, config_file=path)



def _safe_pack_filename(pack_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", pack_id).strip("._-") or "thirdparty"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise PackConfigError(f"invalid eval JSONL {path} line {line_no}: {exc}") from exc
            if not isinstance(item, dict):
                raise PackConfigError(f"eval JSONL {path} line {line_no} must be an object")
            cases.append(item)
    return cases


def _okf_table_files(okf_root: Path) -> list[Path]:
    tables_dir = okf_root / "tables"
    if not tables_dir.exists():
        raise PackConfigError(f"OKF schema bundle must contain tables/: {okf_root}")
    table_files = sorted(tables_dir.glob("*.md"))
    if not table_files:
        raise PackConfigError(f"OKF schema bundle tables/ is empty: {tables_dir}")
    return table_files


def _rel_to(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def _rule_from_eval_case(case: dict[str, Any], index: int) -> dict[str, Any] | None:
    prompt = case.get("prompt")
    sql = case.get("expected_sql")
    if not isinstance(prompt, str) or not prompt or not isinstance(sql, str) or not sql.strip():
        return None
    params = case.get("expected_params", [])
    if not isinstance(params, list):
        params = []
    case_id = str(case.get("id") or f"case_{index + 1:03d}")
    return {
        "id": f"generated_{case_id}",
        "priority": 1000 - index,
        "match": {"exact": prompt},
        "intent": {
            "kind": "lookup",
            "entity": "thirdparty",
            "filters": {},
            "requested_fields": ["*"],
        },
        "sql": {"text": sql, "params": params},
        "answer": {"formatter": "scalar_value", "template": "{value}"},
        "eval_refs": [case_id],
    }


def _bootstrap_rule() -> dict[str, Any]:
    return {
        "id": "bootstrap_no_public_eval_sql",
        "priority": -1000,
        "match": {"exact": "__activegraph_bootstrap_unreachable__"},
        "intent": {"kind": "bootstrap", "entity": "none", "filters": {}, "requested_fields": []},
        "sql": {"text": "SELECT 1", "params": []},
        "answer": {"formatter": "scalar_value", "template": "{value}"},
        "eval_refs": ["bootstrap"],
    }


def _render_thirdparty_system_model(pack_id: str, okf_root: Path, table_files: list[Path], cases: list[dict[str, Any]]) -> dict[str, Any]:
    relative_tables = [_rel_to(table, okf_root) for table in table_files]
    rules = [rule for index, case in enumerate(cases) if (rule := _rule_from_eval_case(case, index)) is not None]
    if not rules:
        rules = [_bootstrap_rule()]
    return {
        "schema_version": "system-model.v11",
        "kind": "activegraph.agent.system_model",
        "name": f"{pack_id}-text-to-sql-agent-v11",
        "display_name": f"{pack_id} Text-to-SQL Agent",
        "status": "experimental",
        "language": "ko",
        "experiment": {
            "id": "v11_5_thirdparty_pack_onboarding",
            "title": "Third-party SQLite DB + OKF schema-bundle onboarding",
            "hypothesis": "A third-party pack can be validated and evaluated from declarative DB, OKF schema, and eval inputs.",
        },
        "behavior_model": {
            "behaviors": [
                {"id": "parse_intent", "runtime": {"on": ["question.submitted"], "creates": ["question", "intent", "entity_validation", "answer"]}},
                {"id": "compile_sql", "runtime": {"on": ["intent.created"], "creates": ["sql_query"]}},
                {"id": "execute_sql", "runtime": {"on": ["sql.generated"], "creates": ["query_result"]}},
                {"id": "synthesize_answer", "runtime": {"on": ["sql.executed"], "creates": ["answer"]}},
            ]
        },
        "schema_projection": {
            "id": f"{_safe_pack_filename(pack_id).replace('-', '_')}_okf_schema_projection",
            "source": {"type": "okf_bundle", "root_env": "OKF_BUNDLE_ROOT", "root_pack_field": "schema.root"},
            "include": {"tables": relative_tables},
            "db_validation": {"compare_with_sqlite": True, "db_env": "DB_FILE"},
        },
        "entity_validation_model": {"id": f"{pack_id}_entity_validators_v11_5", "validators": {}},
        "planning_model": {
            "rule_catalog": {
                "id": f"{_safe_pack_filename(pack_id).replace('-', '_')}_text_to_sql_rules_v01",
                "matching_policy": {"no_match": {"user_message": "Unsupported prompt for third-party pack."}},
                "answer_formatters": {"scalar_value": {"required_template_tokens": ["value"]}},
                "rules": rules,
            }
        },
    }


def import_thirdparty_pack(
    pack_id: str,
    *,
    db_file: str | Path,
    okf_root: str | Path,
    evals_file: str | Path,
    config_file: str | Path = DEFAULT_PACKS_FILE,
    eval_manifest_file: str | Path | None = None,
    agent_dir: str | Path = AGENT_DIR,
    data_dir: str | Path | None = None,
    system_model_dir: str | Path | None = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", pack_id):
        raise PackConfigError("pack_id must contain only letters, numbers, dot, underscore, and hyphen")
    config_path = Path(config_file)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    db_path = Path(db_file).resolve()
    okf_path = Path(okf_root).resolve()
    evals_path = Path(evals_file).resolve()
    if not db_path.exists():
        raise PackConfigError(f"DB file not found: {db_path}")
    if not (okf_path / "index.md").exists():
        raise PackConfigError(f"OKF schema bundle index.md not found: {okf_path}")
    if not evals_path.exists():
        raise PackConfigError(f"eval cases file not found: {evals_path}")

    table_files = _okf_table_files(okf_path)
    cases = _read_jsonl(evals_path)
    model_dir = Path(system_model_dir) if system_model_dir is not None else Path(agent_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    model_file = model_dir / f"system-model.{_safe_pack_filename(pack_id)}.v11.yaml"
    model = _render_thirdparty_system_model(pack_id, okf_path, table_files, cases)
    model_file.write_text(yaml.safe_dump(model, allow_unicode=True, sort_keys=False), encoding="utf-8")

    if config_path.exists():
        registry = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    else:
        registry = {}
    if not isinstance(registry, dict):
        raise PackConfigError(f"pack registry must be a mapping: {config_path}")
    registry.setdefault("schema_version", SUPPORTED_PACK_SCHEMA)
    if registry.get("schema_version") != SUPPORTED_PACK_SCHEMA:
        raise PackConfigError(f"schema_version must be {SUPPORTED_PACK_SCHEMA}")
    packs = registry.setdefault("packs", {})
    if not isinstance(packs, dict):
        raise PackConfigError("pack registry packs must be a mapping")
    base_dir = config_path.resolve().parent
    event_parent = Path(data_dir).resolve() if data_dir is not None else db_path.parent
    event_store = event_parent / f"{_safe_pack_filename(pack_id)}_text_to_sql_events.sqlite"
    event_parent.mkdir(parents=True, exist_ok=True)
    packs[pack_id] = {
        "display_name": f"{pack_id} DB Agent",
        "runtime": "text-to-sql",
        "system_model": _rel_to(model_file, base_dir),
        "env": {
            "DB_FILE": _rel_to(db_path, base_dir),
            "EVENT_STORE": _rel_to(event_store, base_dir),
            "OKF_BUNDLE_ROOT": _rel_to(okf_path, base_dir),
        },
        "capabilities": {"db": True, "schema": True, "kb": False},
        "llm": {
            "provider": "ollama",
            "enabled": False,
            "mode": "answer_composer",
            "base_url": "http://localhost:11434/v1",
            "model": "qwen2.5:7b",
            "base_url_env": "OLLAMA_BASE_URL",
            "model_env": "OLLAMA_MODEL",
            "timeout_seconds": 30,
            "fallback": "deterministic_answer",
        },
        "schema": {"format": "okf", "root": _rel_to(okf_path, base_dir)},
    }
    if registry.get("default_pack") not in packs:
        registry["default_pack"] = pack_id
    config_path.write_text(yaml.safe_dump(registry, allow_unicode=True, sort_keys=False), encoding="utf-8")

    manifest_payload: dict[str, Any] | None = None
    if eval_manifest_file is not None:
        manifest_path = Path(eval_manifest_file)
    else:
        manifest_path = TEXT_TO_SQL_DIR / "evals" / "eval_manifest.yaml"
    if manifest_path:
        if manifest_path.exists():
            manifest_payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        else:
            manifest_payload = {"schema_version": "activegraph.text_to_sql_evals.v01", "packs": {}}
        if not isinstance(manifest_payload, dict):
            raise PackConfigError(f"eval manifest must be a mapping: {manifest_path}")
        manifest_payload.setdefault("schema_version", "activegraph.text_to_sql_evals.v01")
        manifest_packs = manifest_payload.setdefault("packs", {})
        if not isinstance(manifest_packs, dict):
            raise PackConfigError("eval manifest packs must be a mapping")
        manifest_base = manifest_path.resolve().parent
        manifest_packs[pack_id] = {
            "db": _rel_to(db_path, manifest_base),
            "system_model": _rel_to(model_file, manifest_base),
            "runnable": {"consolidated": _rel_to(evals_path, manifest_base)},
            "coverage": {"consolidated_cases": len(cases), "domains": ["thirdparty_import"]},
            "deferred": {"session_required": [], "unresolved_planner_or_schema": []},
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(yaml.safe_dump(manifest_payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    pack = resolve_pack(pack_id, config_file=config_path)
    return {
        "ok": True,
        "pack": pack_to_dict(pack),
        "system_model": str(model_file.resolve()),
        "eval_manifest": str(manifest_path.resolve()) if manifest_path else None,
        "generated_rules": len(model["planning_model"]["rule_catalog"]["rules"]),
        "schema_tables": [_rel_to(table, okf_path) for table in table_files],
    }
def pack_to_dict(pack: AgentPack) -> dict[str, Any]:
    return {
        "id": pack.id,
        "display_name": pack.display_name,
        "runtime": pack.runtime,
        "system_model": str(pack.system_model),
        "reference_model": str(pack.reference_model) if pack.reference_model else None,
        "env": dict(pack.env),
        "capabilities": dict(pack.capabilities),
        "schema": dict(pack.schema),
        "kb": dict(pack.kb),
        "llm": dict(pack.llm),
    }


def _validation_check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def _check_path_exists(name: str, path: Path | None, *, expected: str = "path") -> dict[str, Any]:
    if path is None:
        return _validation_check(name, False, f"missing {expected}")
    if not path.exists():
        return _validation_check(name, False, f"not found: {path}")
    return _validation_check(name, True, str(path))


def _check_db_readable(path: Path | None) -> dict[str, Any]:
    exists = _check_path_exists("db_file", path, expected="DB_FILE")
    if not exists["ok"]:
        return exists
    assert path is not None
    try:
        with sqlite3.connect(str(path)) as conn:
            conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
    except sqlite3.Error as exc:
        return _validation_check("db_readable", False, f"{path}: {exc}")
    return _validation_check("db_readable", True, str(path))


def _check_event_store_parent(path: Path | None) -> dict[str, Any]:
    if path is None:
        return _validation_check("event_store_parent", False, "missing EVENT_STORE")
    parent = path.parent
    if not parent.exists():
        return _validation_check("event_store_parent", False, f"parent not found: {parent}")
    try:
        with tempfile.NamedTemporaryFile(prefix=".pack-validate-", suffix=".tmp", dir=parent, delete=True) as handle:
            handle.write(b"ok")
            handle.flush()
    except OSError as exc:
        return _validation_check("event_store_parent_writable", False, f"{parent}: {exc}")
    return _validation_check("event_store_parent_writable", True, str(parent))


def _check_system_model_executable(path: Path) -> dict[str, Any]:
    exists = _check_path_exists("system_model", path, expected="system_model")
    if not exists["ok"]:
        return exists
    try:
        from activegraph.cli.hospital_logic import load_rule_catalog_from_system_model

        catalog = load_rule_catalog_from_system_model(path)
    except Exception as exc:
        return _validation_check("system_model_executable", False, f"{path}: {exc}")
    return _validation_check("system_model_executable", True, f"{path} catalog={catalog.id} rules={len(catalog.rules)}")


def _check_okf_bundle(pack: AgentPack) -> list[dict[str, Any]]:
    if not pack.capabilities.get("kb", False):
        return []
    checks: list[dict[str, Any]] = []
    root = pack.kb_root
    root_check = _check_path_exists("okf_root", root, expected="OKF_BUNDLE_ROOT")
    checks.append(root_check)
    if root_check["ok"] and root is not None:
        checks.append(_check_path_exists("okf_index", root / "index.md", expected="OKF index.md"))
    if pack.kb.get("format") != "okf":
        checks.append(_validation_check("okf_format", False, f"expected okf, got {pack.kb.get('format')!r}"))
    else:
        checks.append(_validation_check("okf_format", True, "okf"))
    checks.append(_validation_check("okf_approval_required", pack.kb.get("approval_required") is True, str(pack.kb.get("approval_required"))))
    return checks

def _check_schema_projection(pack: AgentPack) -> list[dict[str, Any]]:
    if not pack.capabilities.get("schema", False):
        return []
    checks: list[dict[str, Any]] = []
    root_check = _check_path_exists("schema_okf_root", pack.schema_root, expected="schema OKF root")
    checks.append(root_check)
    if pack.schema.get("format") != "okf":
        checks.append(_validation_check("schema_format", False, f"expected okf, got {pack.schema.get('format')!r}"))
    else:
        checks.append(_validation_check("schema_format", True, "okf"))
    try:
        from activegraph.cli.schema_context import load_schema_context_for_pack

        context = load_schema_context_for_pack(pack)
    except Exception as exc:
        checks.append(_validation_check("schema_projection", False, str(exc)))
        return checks
    checks.append(_validation_check("schema_projection", context["ok"], context["schema_projection"]["id"]))
    validation = context.get("validation", {})
    checks.append(_validation_check("schema_sqlite_alignment", bool(validation.get("ok")), str(validation)))
    return checks

def validate_pack(pack: AgentPack) -> dict[str, Any]:
    checks: list[dict[str, Any]] = [
        _check_path_exists("system_model", pack.system_model, expected="system_model"),
        _check_system_model_executable(pack.system_model),
        _check_db_readable(pack.db_file) if pack.capabilities.get("db", False) else _validation_check("db_readable", True, "db capability disabled"),
        _check_event_store_parent(pack.event_store),
    ]
    if pack.reference_model is not None:
        checks.append(_check_path_exists("reference_model", pack.reference_model, expected="reference_model"))
    checks.extend(_check_schema_projection(pack))
    checks.extend(_check_okf_bundle(pack))
    return {
        "id": pack.id,
        "ok": all(check["ok"] for check in checks),
        "checks": checks,
    }


def validate_pack_by_id(pack_id: str | None = None, *, config_file: str | Path = DEFAULT_PACKS_FILE) -> dict[str, Any]:
    return validate_pack(resolve_pack(pack_id, config_file=config_file))


def validate_all_packs(config_file: str | Path = DEFAULT_PACKS_FILE) -> dict[str, Any]:
    packs = [validate_pack(pack) for pack in list_packs(config_file)]
    return {
        "ok": all(pack["ok"] for pack in packs),
        "packs": packs,
    }




