#!/usr/bin/env python3
"""Build the hospital SQLite database used by the Text-to-SQL demo.

The schema and seed rows are loaded from ``ch09_text_to_sql.py`` so the
standalone database stays aligned with the converted notebook source.
"""
from __future__ import annotations

import argparse
import importlib.util
import sqlite3
from pathlib import Path
from types import ModuleType

REPO_ACTIVEGRAPH_DIR = Path(__file__).resolve().parents[2]
TEXT_TO_SQL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_FILE = REPO_ACTIVEGRAPH_DIR / "data" / "hospital.db"
SOURCE_FILE = TEXT_TO_SQL_DIR / "ch09_text_to_sql.py"

DROP_TABLES_SQL = """
DROP TABLE IF EXISTS procedure_coverage;
DROP TABLE IF EXISTS insurance;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS medical_records;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS availability;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
"""

SEED_BLOCKS = [
    "sample_doctors",
    "sample_patients",
    "sample_availability",
    "sample_appointments",
    "sample_medical_records",
    "sample_prescriptions",
    "sample_insurance",
    "sample_procedure_coverage",
]

TABLES = [
    "doctors",
    "patients",
    "availability",
    "appointments",
    "medical_records",
    "prescriptions",
    "insurance",
    "procedure_coverage",
]

SQLITE_SIDECAR_SUFFIXES = ["", "-journal", "-wal", "-shm"]


def load_text_to_sql_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("ch09_text_to_sql", SOURCE_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {SOURCE_FILE}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remove_existing_database(db_file: Path) -> None:
    for suffix in SQLITE_SIDECAR_SUFFIXES:
        candidate = Path(f"{db_file}{suffix}")
        if candidate.exists():
            candidate.unlink()


def build_database(db_file: Path, *, reset: bool = True) -> dict[str, int]:
    module = load_text_to_sql_module()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    if reset:
        remove_existing_database(db_file)

    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = DELETE")
        if reset:
            conn.executescript(DROP_TABLES_SQL)

        conn.executescript(module.hospital_schema)
        for block_name in SEED_BLOCKS:
            conn.executescript(getattr(module, block_name))

        conn.commit()
        return row_counts(conn)


def row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in TABLES:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the hospital SQLite test database")
    parser.add_argument(
        "--db-file",
        type=Path,
        default=DEFAULT_DB_FILE,
        help=f"SQLite output path. Default: {DEFAULT_DB_FILE}",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not drop existing hospital tables before creating and seeding.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    counts = build_database(args.db_file.resolve(), reset=not args.no_reset)

    print(f"Created SQLite database: {args.db_file.resolve()}")
    for table, count in counts.items():
        print(f"{table}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
