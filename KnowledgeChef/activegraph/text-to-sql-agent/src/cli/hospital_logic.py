"""Shared hospital Text-to-SQL planning and formatting helpers."""
from __future__ import annotations

import encodings.cp1252
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SYSTEM_MODEL_FILE = Path(__file__).resolve().parents[2] / "agent" / "system-model.v03.yaml"
SUPPORTED_SYSTEM_MODEL_SCHEMAS = {
    "system-model.v02",
    "system-model.v03",
    "system-model.v04",
    "system-model.v05",
    "system-model.v06",
    "system-model.v11",
}


@dataclass(frozen=True)
class IntentPlan:
    intent: dict[str, Any]
    sql: str
    params: list[Any]
    answer_template: str
    rule_id: str | None = None
    answer_formatter: str | None = None
    row_template: str | None = None
    empty_template: str | None = None
    bindings: dict[str, str] | None = None
    capture_entities: dict[str, Any] | None = None


@dataclass(frozen=True)
class Rule:
    id: str
    priority: int
    declaration_order: int
    match: dict[str, Any]
    intent: dict[str, Any]
    sql: str
    params: list[Any]
    answer_template: str
    answer_formatter: str
    eval_refs: list[str]
    params_from: list[str]
    row_template: str | None = None
    empty_template: str | None = None
    captures: dict[str, Any] | None = None


@dataclass(frozen=True)
class RuleMatch:
    rule: Rule
    bindings: dict[str, str]


@dataclass(frozen=True)
class EntityValidator:
    entity: str
    adapter: str
    table: str | None = None
    column: str | None = None
    sql: str | None = None
    not_found_message_template: str | None = None


class UnsupportedPromptError(ValueError):
    """Raised when the deterministic behavior set has no prompt rule."""


class UnsafeSQLError(ValueError):
    """Raised when generated SQL violates the read-only policy."""


class RuleCatalogError(ValueError):
    """Raised when a declarative rule catalog is invalid."""


_CP1252_REVERSE = {
    char: value
    for value, char in enumerate(encodings.cp1252.decoding_table)
    if char != "\ufffe"
}

_DEFAULT_RULE_CATALOG: RuleCatalog | None = None


def _bytes_from_windows_mojibake(text: str) -> bytes | None:
    out = bytearray()
    for char in text:
        codepoint = ord(char)
        if 0xDC80 <= codepoint <= 0xDCFF:
            out.append(codepoint - 0xDC00)
        elif codepoint <= 0xFF:
            out.append(codepoint)
        elif char in _CP1252_REVERSE:
            out.append(_CP1252_REVERSE[char])
        else:
            return None
    return bytes(out)


def normalize_prompt_text(prompt: str) -> str:
    """Repair surrogate/cp1252-mojibake stdin text from Windows pipes."""
    if not any("\udc80" <= char <= "\udcff" for char in prompt):
        return prompt

    raw_bytes = _bytes_from_windows_mojibake(prompt)
    if raw_bytes is not None:
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeError:
            pass

    try:
        return prompt.encode("utf-8", "surrogateescape").decode("utf-8")
    except UnicodeError:
        return prompt


def safe_display_text(value: Any) -> str:
    return str(value).encode("utf-8", "backslashreplace").decode("utf-8")


def sqlite_store_url(path: str | Path) -> str:
    return "sqlite:///" + str(Path(path).resolve()).replace("\\", "/")


def _normalized_prompt(prompt: str) -> str:
    repaired = normalize_prompt_text(prompt)
    return re.sub(r"\s+", " ", repaired.strip()).lower()


def _compact_prompt(prompt: str) -> str:
    return re.sub(r"\s+", "", prompt)


def _string_list(value: Any, *, field: str, rule_id: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuleCatalogError(f"rule {rule_id} field {field} must be a list of strings")
    return value


def _require_dict(value: Any, *, field: str, rule_id: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuleCatalogError(f"rule {rule_id} field {field} must be a mapping")
    return value


def _replace_binding_placeholders(text: str, bindings: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in bindings:
            return bindings[name]
        return match.group(0)

    return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", replace, text)


def _apply_bindings(value: Any, bindings: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _replace_binding_placeholders(value, bindings)
    if isinstance(value, list):
        return [_apply_bindings(item, bindings) for item in value]
    if isinstance(value, dict):
        return {key: _apply_bindings(item, bindings) for key, item in value.items()}
    return value


def validate_select_sql(sql: str) -> None:
    normalized = sql.strip().lower()
    if not normalized.startswith("select "):
        raise UnsafeSQLError(f"Only SELECT SQL is allowed, got: {sql}")
    if ";" in normalized:
        raise UnsafeSQLError("SQL must be a single SELECT statement without semicolons")
    padded = f" {normalized} "
    for token in [" insert ", " update ", " delete ", " drop ", " alter ", " create ", " attach ", " detach ", " pragma "]:
        if token in padded:
            raise UnsafeSQLError(f"Unsafe SQL token found: {token.strip()}")


class RuleCatalog:
    """Declarative prompt-to-SQL rule catalog loaded from a system model."""

    def __init__(
        self,
        catalog_id: str,
        rules: list[Rule],
        no_match_message: str | None = None,
        *,
        entity_validators: dict[str, EntityValidator] | None = None,
        behavior_contracts: list[dict[str, Any]] | None = None,
    ) -> None:
        self.id = catalog_id
        self.rules = sorted(rules, key=lambda rule: (-rule.priority, rule.declaration_order))
        self.no_match_message = no_match_message or "Unsupported prompt"
        self.entity_validators = entity_validators or {}
        self.behavior_contracts = behavior_contracts or []

    @classmethod
    def from_system_model(cls, data: dict[str, Any]) -> RuleCatalog:
        schema_version = data.get("schema_version")
        if schema_version not in SUPPORTED_SYSTEM_MODEL_SCHEMAS:
            supported = ", ".join(sorted(SUPPORTED_SYSTEM_MODEL_SCHEMAS))
            raise RuleCatalogError(f"schema_version must be one of: {supported}")

        try:
            catalog_data = data["planning_model"]["rule_catalog"]
        except KeyError as exc:
            raise RuleCatalogError("missing planning_model.rule_catalog") from exc
        if not isinstance(catalog_data, dict):
            raise RuleCatalogError("planning_model.rule_catalog must be a mapping")

        catalog_id = catalog_data.get("id")
        if not isinstance(catalog_id, str) or not catalog_id:
            raise RuleCatalogError("rule catalog id is required")

        no_match = (
            catalog_data.get("matching_policy", {})
            .get("no_match", {})
            .get("user_message")
        )
        formatter_defs = catalog_data.get("answer_formatters", {})
        if not isinstance(formatter_defs, dict):
            raise RuleCatalogError("answer_formatters must be a mapping")

        raw_rules = catalog_data.get("rules")
        if not isinstance(raw_rules, list) or not raw_rules:
            raise RuleCatalogError("rule catalog must contain at least one rule")

        seen_ids: set[str] = set()
        rules: list[Rule] = []
        for index, raw_rule in enumerate(raw_rules):
            if not isinstance(raw_rule, dict):
                raise RuleCatalogError(f"rule at index {index} must be a mapping")
            rule = cls._parse_rule(raw_rule, index, formatter_defs)
            if rule.id in seen_ids:
                raise RuleCatalogError(f"duplicate rule id: {rule.id}")
            seen_ids.add(rule.id)
            rules.append(rule)

        entity_validators = cls._parse_entity_validators(data.get("entity_validation_model"))
        behavior_contracts = cls._parse_behavior_contracts(data.get("behavior_model"))

        return cls(
            catalog_id,
            rules,
            no_match_message=no_match,
            entity_validators=entity_validators,
            behavior_contracts=behavior_contracts,
        )

    @staticmethod
    def _parse_entity_validators(raw_model: Any) -> dict[str, EntityValidator]:
        if raw_model is None:
            return {}
        if not isinstance(raw_model, dict):
            raise RuleCatalogError("entity_validation_model must be a mapping")
        validators = raw_model.get("validators", {})
        if not isinstance(validators, dict):
            raise RuleCatalogError("entity_validation_model.validators must be a mapping")

        parsed: dict[str, EntityValidator] = {}
        for entity, raw_validator in validators.items():
            if not isinstance(entity, str) or not entity:
                raise RuleCatalogError("entity validator keys must be non-empty strings")
            if not isinstance(raw_validator, dict):
                raise RuleCatalogError(f"entity validator {entity} must be a mapping")
            adapter = raw_validator.get("adapter")
            if adapter != "sqlite_exists":
                raise RuleCatalogError(f"entity validator {entity} unsupported adapter: {adapter!r}")
            table = raw_validator.get("table")
            column = raw_validator.get("column")
            sql = raw_validator.get("sql")
            if sql is not None:
                if not isinstance(sql, str) or not sql.strip():
                    raise RuleCatalogError(f"entity validator {entity} sql must be a non-empty string")
                validate_select_sql(sql)
            elif not isinstance(table, str) or not isinstance(column, str):
                raise RuleCatalogError(f"entity validator {entity} must define table and column or sql")
            template = raw_validator.get("not_found_message_template")
            if template is not None and not isinstance(template, str):
                raise RuleCatalogError(f"entity validator {entity} not_found_message_template must be a string")
            parsed[entity] = EntityValidator(
                entity=entity,
                adapter=adapter,
                table=table if isinstance(table, str) else None,
                column=column if isinstance(column, str) else None,
                sql=sql if isinstance(sql, str) else None,
                not_found_message_template=template,
            )
        return parsed

    @staticmethod
    def _parse_behavior_contracts(raw_model: Any) -> list[dict[str, Any]]:
        if raw_model is None:
            return []
        if not isinstance(raw_model, dict):
            raise RuleCatalogError("behavior_model must be a mapping")
        raw_behaviors = raw_model.get("behaviors", [])
        if not isinstance(raw_behaviors, list):
            raise RuleCatalogError("behavior_model.behaviors must be a list")

        contracts: list[dict[str, Any]] = []
        for index, raw_behavior in enumerate(raw_behaviors):
            if not isinstance(raw_behavior, dict):
                raise RuleCatalogError(f"behavior at index {index} must be a mapping")
            behavior_id = raw_behavior.get("id") or raw_behavior.get("name")
            if not isinstance(behavior_id, str) or not behavior_id:
                raise RuleCatalogError(f"behavior at index {index} must define id")
            runtime = raw_behavior.get("runtime", {})
            if runtime is None:
                runtime = {}
            if not isinstance(runtime, dict):
                raise RuleCatalogError(f"behavior {behavior_id} runtime must be a mapping")
            on = runtime.get("on") if "on" in runtime else runtime.get(True, raw_behavior.get("on"))
            if on is None and raw_behavior.get("trigger"):
                on = [raw_behavior["trigger"]]
            creates = runtime.get("creates", raw_behavior.get("creates", []))
            emits = runtime.get("emits", raw_behavior.get("emits", []))
            contracts.append(
                {
                    "name": behavior_id,
                    "on": _string_list(on, field="runtime.on", rule_id=behavior_id),
                    "creates": _string_list(creates, field="runtime.creates", rule_id=behavior_id),
                    "emits": _string_list(emits, field="runtime.emits", rule_id=behavior_id),
                    "implementation": raw_behavior.get("implementation"),
                }
            )
        return contracts

    def behavior_spec(self, behavior_name: str) -> dict[str, Any] | None:
        for contract in self.behavior_contracts:
            if contract["name"] == behavior_name:
                return contract
        return None
    @staticmethod
    def _parse_rule(raw_rule: dict[str, Any], index: int, formatter_defs: dict[str, Any]) -> Rule:
        rule_id = raw_rule.get("id")
        if not isinstance(rule_id, str) or not rule_id:
            raise RuleCatalogError(f"rule at index {index} must define id")

        priority = raw_rule.get("priority")
        if not isinstance(priority, int):
            raise RuleCatalogError(f"rule {rule_id} priority must be an integer")

        match = _require_dict(raw_rule.get("match"), field="match", rule_id=rule_id)
        intent = _require_dict(raw_rule.get("intent"), field="intent", rule_id=rule_id)
        sql_data = _require_dict(raw_rule.get("sql"), field="sql", rule_id=rule_id)
        answer_data = _require_dict(raw_rule.get("answer"), field="answer", rule_id=rule_id)
        eval_refs = _string_list(raw_rule.get("eval_refs"), field="eval_refs", rule_id=rule_id)
        if not eval_refs:
            raise RuleCatalogError(f"rule {rule_id} must define at least one eval_ref")

        sql_text = sql_data.get("text")
        if not isinstance(sql_text, str) or not sql_text.strip():
            raise RuleCatalogError(f"rule {rule_id} sql.text must be a non-empty string")
        validate_select_sql(sql_text)

        params = sql_data.get("params", [])
        if params is None:
            params = []
        if not isinstance(params, list):
            raise RuleCatalogError(f"rule {rule_id} sql.params must be a list")
        params_from = _string_list(sql_data.get("params_from"), field="sql.params_from", rule_id=rule_id)
        if params and params_from:
            raise RuleCatalogError(f"rule {rule_id} cannot define both sql.params and sql.params_from")

        formatter = answer_data.get("formatter")
        if not isinstance(formatter, str) or not formatter:
            raise RuleCatalogError(f"rule {rule_id} answer.formatter is required")
        if formatter_defs and formatter not in formatter_defs:
            raise RuleCatalogError(f"rule {rule_id} uses unknown answer formatter: {formatter}")

        template = answer_data.get("template")
        if not isinstance(template, str) or not template:
            raise RuleCatalogError(f"rule {rule_id} answer.template is required")
        required_tokens = []
        formatter_def = formatter_defs.get(formatter, {}) if formatter_defs else {}
        if isinstance(formatter_def, dict):
            required_tokens = formatter_def.get("required_template_tokens", []) or []
        for token in required_tokens:
            if "{" + str(token) + "}" not in template:
                raise RuleCatalogError(f"rule {rule_id} answer.template must contain {{{token}}}")

        row_template = answer_data.get("row_template")
        if row_template is not None and not isinstance(row_template, str):
            raise RuleCatalogError(f"rule {rule_id} answer.row_template must be a string")
        empty_template = answer_data.get("empty_template")
        if empty_template is not None and not isinstance(empty_template, str):
            raise RuleCatalogError(f"rule {rule_id} answer.empty_template must be a string")

        for field in ["contains_all", "contains_any", "compact_contains_all", "compact_contains_any"]:
            _string_list(match.get(field), field=f"match.{field}", rule_id=rule_id)
        regex = match.get("compact_regex")
        if regex is not None:
            if not isinstance(regex, str):
                raise RuleCatalogError(f"rule {rule_id} match.compact_regex must be a string")
            try:
                re.compile(regex)
            except re.error as exc:
                raise RuleCatalogError(f"rule {rule_id} has invalid compact_regex: {exc}") from exc

        captures = raw_rule.get("captures")
        if captures is not None and not isinstance(captures, dict):
            raise RuleCatalogError(f"rule {rule_id} captures must be a mapping")
        capture_names = set(captures or {})
        for param_name in params_from:
            if capture_names and param_name not in capture_names:
                raise RuleCatalogError(f"rule {rule_id} sql.params_from references unknown capture: {param_name}")

        return Rule(
            id=rule_id,
            priority=priority,
            declaration_order=index,
            match=match,
            intent=dict(intent),
            sql=sql_text,
            params=list(params),
            answer_template=template,
            answer_formatter=formatter,
            eval_refs=eval_refs,
            params_from=params_from,
            row_template=row_template,
            empty_template=empty_template,
            captures=captures,
        )

    def eval_ids(self) -> list[str]:
        return sorted({eval_id for rule in self.rules for eval_id in rule.eval_refs})

    def match(self, prompt: str) -> Rule | None:
        matched = self.match_with_bindings(prompt)
        return matched.rule if matched is not None else None

    def match_with_bindings(self, prompt: str) -> RuleMatch | None:
        normalized = _normalized_prompt(prompt)
        compact = _compact_prompt(normalized)
        for rule in self.rules:
            bindings = self._match_rule(rule, normalized, compact)
            if bindings is not None:
                return RuleMatch(rule=rule, bindings=bindings)
        return None

    def plan(self, prompt: str) -> IntentPlan:
        matched = self.match_with_bindings(prompt)
        if matched is None:
            raise UnsupportedPromptError(f"Unsupported prompt for rule catalog {self.id}: {prompt}")
        rule = matched.rule
        bindings = matched.bindings
        intent = _apply_bindings(dict(rule.intent), bindings)
        intent["rule_id"] = rule.id
        if bindings:
            intent["bindings"] = dict(bindings)
        if rule.captures:
            intent["capture_entities"] = dict(rule.captures)

        if rule.params_from:
            missing = [name for name in rule.params_from if name not in bindings]
            if missing:
                raise RuleCatalogError(f"rule {rule.id} missing capture binding(s): {', '.join(missing)}")
            params = [bindings[name] for name in rule.params_from]
        else:
            params = _apply_bindings(list(rule.params), bindings)

        return IntentPlan(
            intent=intent,
            sql=rule.sql,
            params=params,
            answer_template=_replace_binding_placeholders(rule.answer_template, bindings),
            rule_id=rule.id,
            answer_formatter=rule.answer_formatter,
            row_template=_replace_binding_placeholders(rule.row_template, bindings) if rule.row_template else None,
            empty_template=_replace_binding_placeholders(rule.empty_template, bindings) if rule.empty_template else None,
            bindings=dict(bindings),
            capture_entities=dict(rule.captures or {}),
        )

    def render_answer(self, rows: list[list[Any]], plan: IntentPlan) -> str:
        return format_answer_text(rows, plan.answer_template, empty_template=plan.empty_template)

    @staticmethod
    def _match_rule(rule: Rule, normalized: str, compact: str) -> dict[str, str] | None:
        match = rule.match
        contains_all = _string_list(match.get("contains_all"), field="match.contains_all", rule_id=rule.id)
        if contains_all and not all(token.lower() in normalized for token in contains_all):
            return None

        contains_any = _string_list(match.get("contains_any"), field="match.contains_any", rule_id=rule.id)
        if contains_any and not any(token.lower() in normalized for token in contains_any):
            return None

        compact_contains_all = _string_list(
            match.get("compact_contains_all"), field="match.compact_contains_all", rule_id=rule.id
        )
        if compact_contains_all and not all(token.lower() in compact for token in compact_contains_all):
            return None

        compact_contains_any = _string_list(
            match.get("compact_contains_any"), field="match.compact_contains_any", rule_id=rule.id
        )
        if compact_contains_any and not any(token.lower() in compact for token in compact_contains_any):
            return None

        bindings: dict[str, str] = {}
        compact_regex = match.get("compact_regex")
        if compact_regex:
            regex_match = re.search(compact_regex, compact)
            if regex_match is None:
                return None
            bindings.update({key: value for key, value in regex_match.groupdict().items() if value is not None})

        for capture_name, capture_config in (rule.captures or {}).items():
            required = bool(capture_config.get("required")) if isinstance(capture_config, dict) else False
            if required and not bindings.get(capture_name):
                return None

        return bindings

    @staticmethod
    def _matches_rule(rule: Rule, normalized: str, compact: str) -> bool:
        return RuleCatalog._match_rule(rule, normalized, compact) is not None


def load_rule_catalog_from_system_model(path: str | Path = DEFAULT_SYSTEM_MODEL_FILE) -> RuleCatalog:
    try:
        import yaml
    except ImportError as exc:
        raise RuleCatalogError("PyYAML is required to load system-model YAML") from exc

    model_path = Path(path)
    print(f"[activegraph] loading system-model: {model_path}", file=sys.stderr)
    data = yaml.safe_load(model_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuleCatalogError(f"system model must be a mapping: {model_path}")
    catalog = RuleCatalog.from_system_model(data)
    print(
        f"[activegraph] loaded system-model: schema={data.get('schema_version')} catalog={catalog.id} rules={len(catalog.rules)}",
        file=sys.stderr,
    )
    return catalog


def default_rule_catalog() -> RuleCatalog:
    global _DEFAULT_RULE_CATALOG
    if _DEFAULT_RULE_CATALOG is None:
        _DEFAULT_RULE_CATALOG = load_rule_catalog_from_system_model(DEFAULT_SYSTEM_MODEL_FILE)
    return _DEFAULT_RULE_CATALOG


def deterministic_plan(prompt: str, catalog: RuleCatalog | None = None) -> IntentPlan:
    return (catalog or default_rule_catalog()).plan(prompt)



def validate_capture_entities(
    db_file: Path,
    plan: IntentPlan,
    *,
    catalog: RuleCatalog | None = None,
) -> list[dict[str, Any]]:
    """Validate captured entity bindings against the current SQLite environment."""
    validations: list[dict[str, Any]] = []
    bindings = plan.bindings or {}
    capture_entities = plan.capture_entities or {}
    if not bindings or not capture_entities:
        return validations

    entity_validators = catalog.entity_validators if catalog is not None else {}
    with sqlite3.connect(str(db_file)) as conn:
        for binding_name, config in capture_entities.items():
            if binding_name not in bindings:
                continue
            entity = config.get("entity") if isinstance(config, dict) else None
            value = bindings[binding_name]
            validator = entity_validators.get(entity) if isinstance(entity, str) else None
            if validator is not None:
                if validator.sql:
                    sql = validator.sql
                else:
                    sql = f"SELECT 1 FROM {validator.table} WHERE {validator.column} = ? LIMIT 1"
                exists = conn.execute(sql, [value]).fetchone() is not None
                source = "system_model.entity_validation_model"
            elif entity == "doctor.name":
                exists = conn.execute(
                    "SELECT 1 FROM doctors WHERE name = ? LIMIT 1",
                    [value],
                ).fetchone() is not None
                source = "legacy.doctor_name_validator"
            else:
                exists = True
                source = "implicit.valid"
            validations.append(
                {
                    "binding": binding_name,
                    "entity": entity,
                    "value": value,
                    "status": "valid" if exists else "not_found",
                    "source": source,
                }
            )
    return validations


def first_failed_entity_validation(validations: list[dict[str, Any]]) -> dict[str, Any] | None:
    for validation in validations:
        if validation.get("status") != "valid":
            return validation
    return None


def entity_validation_answer(
    validation: dict[str, Any],
    *,
    catalog: RuleCatalog | None = None,
) -> str:
    entity = validation.get("entity")
    value = validation.get("value")
    validator = catalog.entity_validators.get(entity) if catalog is not None and isinstance(entity, str) else None
    if validator is not None and validator.not_found_message_template:
        return validator.not_found_message_template.format(value=value, entity=entity)
    if entity == "doctor.name":
        return f"의사 '{value}'를 찾지 못했습니다."
    return f"'{value}' 항목을 찾지 못했습니다."
def execute_sqlite(db_file: Path, sql: str, params: list[Any]) -> list[list[Any]]:
    validate_select_sql(sql)
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.execute(sql, params)
        return [list(row) for row in cursor.fetchall()]


def format_answer_text(
    rows: list[list[Any]],
    answer_template: str,
    *,
    empty_template: str | None = None,
) -> str:
    if not rows:
        return empty_template or "조회 결과가 없습니다."
    if "{values}" in answer_template:
        values = ", ".join(" ".join(str(value) for value in row) for row in rows)
        return answer_template.format(value=rows[0][0], values=values)
    return answer_template.format(value=rows[0][0])











