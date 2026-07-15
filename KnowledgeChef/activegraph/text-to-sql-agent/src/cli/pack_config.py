"""Pack registry helpers for local ActiveGraph agent configurations."""
from __future__ import annotations

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




