#!/usr/bin/env python3
"""Verify the hospital SQLite database fixture."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

REPO_ACTIVEGRAPH_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_FILE = REPO_ACTIVEGRAPH_DIR / "data" / "hospital.db"

EXPECTED_COUNTS = {
    "doctors": 5,
    "patients": 5,
    "availability": 10,
    "appointments": 5,
    "medical_records": 5,
    "prescriptions": 5,
    "insurance": 5,
    "procedure_coverage": 5,
}


def verify_database(db_file: Path) -> None:
    if not db_file.exists():
        raise FileNotFoundError(f"Database file does not exist: {db_file}")

    with sqlite3.connect(str(db_file)) as conn:
        for table, expected in EXPECTED_COUNTS.items():
            actual = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if actual != expected:
                raise AssertionError(f"{table}: expected {expected}, got {actual}")

        doctor = conn.execute(
            "SELECT name, specialty FROM doctors WHERE doctor_id = ?",
            ("D001",),
        ).fetchone()
        if doctor != ("김지훈", "내과"):
            raise AssertionError(f"Unexpected D001 doctor row: {doctor!r}")

        scheduled_count = conn.execute(
            "SELECT COUNT(*) FROM appointments WHERE status = ?",
            ("예정됨",),
        ).fetchone()[0]
        if scheduled_count != 2:
            raise AssertionError(f"Expected 2 scheduled appointments, got {scheduled_count}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the hospital SQLite test database")
    parser.add_argument(
        "--db-file",
        type=Path,
        default=DEFAULT_DB_FILE,
        help=f"SQLite database path. Default: {DEFAULT_DB_FILE}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    verify_database(args.db_file.resolve())
    print(f"Verified SQLite database: {args.db_file.resolve()}")
    for table, expected in EXPECTED_COUNTS.items():
        print(f"{table}: {expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
