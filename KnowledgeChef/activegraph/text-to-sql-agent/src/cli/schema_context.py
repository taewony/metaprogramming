"""Schema context projection from OKF bundles declared by system-model files."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml


class SchemaContextError(ValueError):
    """Raised when an OKF schema projection cannot be loaded."""


def _load_yaml_file(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise SchemaContextError(f"YAML file must be a mapping: {path}")
    return data


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        raise SchemaContextError(f"OKF table file missing YAML frontmatter: {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SchemaContextError(f"OKF table file has invalid YAML frontmatter: {path}")
    data = yaml.safe_load(parts[1])
    if not isinstance(data, dict):
        raise SchemaContextError(f"OKF frontmatter must be a mapping: {path}")
    return data


def _load_okf_table(path: Path) -> dict[str, Any]:
    data = _frontmatter(path)
    table_name = data.get("table")
    columns = data.get("columns")
    if not isinstance(table_name, str) or not table_name:
        raise SchemaContextError(f"OKF table file must define table: {path}")
    if not isinstance(columns, list) or not columns:
        raise SchemaContextError(f"OKF table file must define columns: {path}")

    normalized_columns: list[dict[str, Any]] = []
    for column in columns:
        if not isinstance(column, dict):
            raise SchemaContextError(f"OKF column entries must be mappings: {path}")
        name = column.get("name")
        column_type = column.get("type")
        if not isinstance(name, str) or not isinstance(column_type, str):
            raise SchemaContextError(f"OKF columns must define name and type: {path}")
        normalized_columns.append(dict(column))

    return {
        "name": table_name,
        "title": data.get("title") or table_name,
        "description": data.get("description") or "",
        "columns": normalized_columns,
        "foreign_keys": list(data.get("foreign_keys") or []),
        "source": str(path),
    }


def _sqlite_schema(db_file: Path) -> dict[str, dict[str, Any]]:
    if not db_file.exists():
        raise SchemaContextError(f"DB file not found: {db_file}")
    schema: dict[str, dict[str, Any]] = {}
    with sqlite3.connect(str(db_file)) as conn:
        conn.row_factory = sqlite3.Row
        tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for table in tables:
            columns = []
            for row in conn.execute(f"PRAGMA table_info({table})"):
                columns.append(
                    {
                        "name": row["name"],
                        "type": row["type"],
                        "not_null": bool(row["notnull"]),
                        "primary_key": bool(row["pk"]),
                    }
                )
            schema[table] = {"name": table, "columns": columns}
    return schema


def _validate_against_sqlite(tables: list[dict[str, Any]], db_file: Path | None) -> dict[str, Any]:
    if db_file is None:
        return {"ok": False, "error": "missing DB_FILE"}
    db_schema = _sqlite_schema(db_file)
    okf_by_name = {table["name"]: table for table in tables}
    missing_in_okf = sorted(set(db_schema) - set(okf_by_name))
    missing_in_db = sorted(set(okf_by_name) - set(db_schema))
    column_mismatches: list[dict[str, Any]] = []
    for table_name in sorted(set(db_schema) & set(okf_by_name)):
        db_columns = {column["name"] for column in db_schema[table_name]["columns"]}
        okf_columns = {column["name"] for column in okf_by_name[table_name]["columns"]}
        missing_columns_in_okf = sorted(db_columns - okf_columns)
        missing_columns_in_db = sorted(okf_columns - db_columns)
        if missing_columns_in_okf or missing_columns_in_db:
            column_mismatches.append(
                {
                    "table": table_name,
                    "missing_columns_in_okf": missing_columns_in_okf,
                    "missing_columns_in_db": missing_columns_in_db,
                }
            )
    return {
        "ok": not missing_in_okf and not missing_in_db and not column_mismatches,
        "missing_tables_in_okf": missing_in_okf,
        "missing_tables_in_db": missing_in_db,
        "column_mismatches": column_mismatches,
    }


def _graph_projection(projection_id: str, tables: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    objects: list[dict[str, Any]] = [
        {"id": f"schema:{projection_id}", "type": "db.schema_context", "data": {"projection_id": projection_id}}
    ]
    relations: list[dict[str, Any]] = []
    for table in tables:
        table_id = f"table:{table['name']}"
        objects.append({"id": table_id, "type": "db.table", "data": {"name": table["name"], "title": table["title"]}})
        relations.append({"from": f"schema:{projection_id}", "type": "schema.has_table", "to": table_id})
        for column in table["columns"]:
            column_id = f"column:{table['name']}.{column['name']}"
            objects.append(
                {
                    "id": column_id,
                    "type": "db.column",
                    "data": {"table": table["name"], "name": column["name"], "sql_type": column["type"]},
                }
            )
            relations.append({"from": table_id, "type": "table.has_column", "to": column_id})
        for fk in table.get("foreign_keys", []):
            if isinstance(fk, dict) and fk.get("column") and fk.get("references"):
                relations.append(
                    {
                        "from": f"column:{table['name']}.{fk['column']}",
                        "type": "column.references",
                        "to": f"column:{fk['references']}",
                    }
                )
    return {"objects": objects, "relations": relations}


def load_schema_context_for_pack(pack: Any) -> dict[str, Any]:
    model = _load_yaml_file(Path(pack.system_model))
    projection = model.get("schema_projection")
    if not isinstance(projection, dict):
        raise SchemaContextError(f"system model missing schema_projection: {pack.system_model}")
    projection_id = projection.get("id")
    if not isinstance(projection_id, str) or not projection_id:
        raise SchemaContextError("schema_projection.id is required")
    source = projection.get("source")
    if not isinstance(source, dict) or source.get("type") != "okf_bundle":
        raise SchemaContextError("schema_projection.source.type must be okf_bundle")
    include = projection.get("include")
    table_paths = include.get("tables") if isinstance(include, dict) else None
    if not isinstance(table_paths, list) or not table_paths:
        raise SchemaContextError("schema_projection.include.tables must list OKF table files")
    root = pack.schema_root
    if root is None:
        raise SchemaContextError("pack does not define schema root")
    root = Path(root)
    tables = [_load_okf_table(root / str(relative_path)) for relative_path in table_paths]
    validation = _validate_against_sqlite(tables, pack.db_file) if projection.get("db_validation", {}).get("compare_with_sqlite", True) else {"ok": True}
    graph_projection = _graph_projection(projection_id, tables)
    return {
        "ok": bool(validation.get("ok")),
        "pack_id": pack.id,
        "system_model": str(pack.system_model),
        "okf_root": str(root),
        "schema_projection": projection,
        "tables": tables,
        "validation": validation,
        "graph_projection": graph_projection,
    }
