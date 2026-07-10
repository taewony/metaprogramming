#!/usr/bin/env python3
"""Dependency-free TDD driver for the hospital Text-to-SQL fixture.

This defaults to a deterministic ActiveGraph behavior pipeline and keeps the older direct deterministic and optional OpenAI-compatible planner modes for comparison.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, NamedTuple

REPO_ACTIVEGRAPH_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_FILE = REPO_ACTIVEGRAPH_DIR / "data" / "hospital.db"
DEFAULT_CASES_FILE = REPO_ACTIVEGRAPH_DIR / "text-to-sql-agent" / "evals" / "hospital_cases.jsonl"
DEFAULT_OPENAI_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3:8b"
DEFAULT_OPENAI_TIMEOUT = 120.0

from hospital_activegraph_behaviors import DEFAULT_TESTS_DIR, run_text_to_sql


class QueryPlan(NamedTuple):
    sql: str
    params: list[Any] | dict[str, Any]
    answer_template: str


class UnsupportedPromptError(ValueError):
    """Raised when the deterministic starter driver has no rule for a prompt."""


class LLMPlannerError(RuntimeError):
    """Raised when an OpenAI-compatible planner response cannot be used."""


def plan_prompt(prompt: str) -> QueryPlan:
    normalized = prompt.strip()

    if "김지훈" in normalized and ("전공" in normalized or "전문" in normalized):
        return QueryPlan(
            sql="SELECT specialty FROM doctors WHERE name = ?",
            params=["김지훈"],
            answer_template="김지훈 의사의 전공은 {value}입니다.",
        )

    raise UnsupportedPromptError(f"Unsupported prompt for deterministic driver: {prompt}")


def build_llm_messages(prompt: str) -> list[dict[str, str]]:
    schema_context = """
Tables:
- doctors(doctor_id, name, specialty, hospital_name, office, phone, email)
- patients(patient_id, name, birth_date, gender, phone, email, address, insurance_number, blood_type, allergies)
- availability(doctor_id, available_date, available_time, status)
- appointments(appointment_id, patient_id, doctor_id, appointment_date, appointment_time, reason, status, notes)
- medical_records(record_id, patient_id, doctor_id, record_date, record_type, content, notes)
- prescriptions(prescription_id, patient_id, doctor_id, prescription_date, medication, dosage, frequency, duration, status, renewable)
- insurance(insurance_id, patient_id, provider, insurance_type, coverage_start, coverage_end, copay_percentage)
- procedure_coverage(insurance_id, procedure_code, procedure_name, coverage_rate, max_coverage)
""".strip()
    system = f"""You compile Korean hospital database questions into safe SQLite SELECT plans.
Return only one JSON object with exactly these keys: sql, params, answer_template.
Use parameter placeholders for user values. Do not include markdown.
Only generate read-only SELECT statements.
The answer_template must contain {{value}} for the first result value.

{schema_context}
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]


def call_openai_compatible_chat(
    messages: list[dict[str, str]],
    *,
    base_url: str,
    model: str,
    api_key: str | None = None,
    timeout: float = DEFAULT_OPENAI_TIMEOUT,
) -> str:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "stream": False,
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise LLMPlannerError(f"OpenAI-compatible request failed: {exc}") from exc

    try:
        data = json.loads(response_body)
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise LLMPlannerError(f"Unexpected OpenAI-compatible response: {response_body}") from exc


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMPlannerError(f"LLM response did not contain a JSON object: {text}")

    try:
        return json.loads(stripped[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMPlannerError(f"LLM response JSON could not be parsed: {text}") from exc


def validate_select_sql(sql: str) -> None:
    normalized = sql.strip().lower()
    if not normalized.startswith("select "):
        raise LLMPlannerError(f"Only SELECT SQL is allowed, got: {sql}")
    if ";" in normalized:
        raise LLMPlannerError("SQL must be a single SELECT statement without semicolons")
    blocked = [" insert ", " update ", " delete ", " drop ", " alter ", " create ", " attach ", " pragma "]
    padded = f" {normalized} "
    for token in blocked:
        if token in padded:
            raise LLMPlannerError(f"Unsafe SQL token found: {token.strip()}")


def plan_prompt_with_llm(
    prompt: str,
    *,
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    timeout: float = DEFAULT_OPENAI_TIMEOUT,
) -> QueryPlan:
    content = call_openai_compatible_chat(
        build_llm_messages(prompt),
        base_url=openai_base_url,
        model=model,
        api_key=api_key,
        timeout=timeout,
    )
    parsed = extract_json_object(content)
    sql = parsed.get("sql")
    params = parsed.get("params", [])
    answer_template = parsed.get("answer_template")

    if not isinstance(sql, str):
        raise LLMPlannerError("LLM plan must include string field 'sql'")
    if params is None:
        params = []
    elif isinstance(params, dict):
        pass
    elif not isinstance(params, list):
        params = [params]
    if not isinstance(answer_template, str) or "{value}" not in answer_template:
        raise LLMPlannerError("LLM plan must include answer_template containing '{value}'")

    validate_select_sql(sql)
    return QueryPlan(sql=sql, params=params, answer_template=answer_template)


def execute_query(db_file: Path, sql: str, params: list[Any] | dict[str, Any]) -> list[list[Any]]:
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.execute(sql, params)
        return [list(row) for row in cursor.fetchall()]


def synthesize_answer(plan: QueryPlan, rows: list[list[Any]]) -> str:
    if not rows:
        return "조회 결과가 없습니다."
    return plan.answer_template.format(value=rows[0][0])


def answer_prompt(
    prompt: str,
    db_file: str | Path = DEFAULT_DB_FILE,
    *,
    planner: str = "behavior",
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    openai_timeout: float = DEFAULT_OPENAI_TIMEOUT,
    tests_dir: str | Path = DEFAULT_TESTS_DIR,
) -> dict[str, Any]:
    db_path = Path(db_file)
    try:
        if planner == "behavior":
            return run_text_to_sql(prompt, db_path, tests_dir=tests_dir)
        if planner == "deterministic":
            plan = plan_prompt(prompt)
            model_name = None
        elif planner == "llm":
            model_name = model
            plan = plan_prompt_with_llm(
                prompt,
                openai_base_url=openai_base_url,
                model=model,
                api_key=api_key,
                timeout=openai_timeout,
            )
        else:
            raise ValueError(f"Unsupported planner: {planner}")

        rows = execute_query(db_path, plan.sql, plan.params)
        answer = synthesize_answer(plan, rows)
        return {
            "ok": True,
            "planner": planner,
            "model": model_name,
            "prompt": prompt,
            "sql": plan.sql,
            "params": plan.params,
            "rows": rows,
            "answer": answer,
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "planner": planner,
            "model": model if planner == "llm" else None,
            "prompt": prompt,
            "sql": None,
            "params": [],
            "rows": [],
            "answer": "",
            "error": str(exc),
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
    planner: str = "behavior",
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    openai_timeout: float = DEFAULT_OPENAI_TIMEOUT,
    tests_dir: str | Path = DEFAULT_TESTS_DIR,
) -> dict[str, Any]:
    cases = load_cases(cases_file)
    scored_cases = [
        score_case(
            case,
            answer_prompt(
                case["prompt"],
                db_file,
                planner=planner,
                openai_base_url=openai_base_url,
                model=model,
                api_key=api_key,
                openai_timeout=openai_timeout,
                tests_dir=tests_dir,
            ),
        )
        for case in cases
    ]
    passed = sum(1 for case in scored_cases if case["ok"])
    failed = len(scored_cases) - passed
    return {
        "ok": failed == 0,
        "planner": planner,
        "model": model if planner == "llm" else None,
        "passed": passed,
        "failed": failed,
        "cases": scored_cases,
    }

def print_json(payload: dict[str, Any]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def add_planner_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--planner", choices=["behavior", "deterministic", "llm"], default="behavior")
    parser.add_argument(
        "--openai-base-url",
        default=os.environ.get("OPENAI_BASE_URL", os.environ.get("OLLAMA_OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)),
        help=f"OpenAI-compatible base URL. Default: {DEFAULT_OPENAI_BASE_URL}",
    )
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--openai-timeout", type=float, default=DEFAULT_OPENAI_TIMEOUT)
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY", os.environ.get("OLLAMA_API_KEY")),
        help="Optional bearer token for OpenAI-compatible endpoints.",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hospital Text-to-SQL TDD driver")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser("ask", help="Run one prompt against the SQLite fixture")
    ask_parser.add_argument("prompt")
    ask_parser.add_argument("--db-file", type=Path, default=DEFAULT_DB_FILE)
    ask_parser.add_argument("--tests-dir", type=Path, default=DEFAULT_TESTS_DIR)
    add_planner_args(ask_parser)

    eval_parser = subparsers.add_parser("eval", help="Run JSONL eval cases against the SQLite fixture")
    eval_parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_FILE)
    eval_parser.add_argument("--db-file", type=Path, default=DEFAULT_DB_FILE)
    eval_parser.add_argument("--tests-dir", type=Path, default=DEFAULT_TESTS_DIR)
    add_planner_args(eval_parser)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "ask":
        payload = answer_prompt(
            args.prompt,
            args.db_file,
            planner=args.planner,
            openai_base_url=args.openai_base_url,
            model=args.model,
            api_key=args.api_key,
            openai_timeout=args.openai_timeout,
        )
        print_json(payload)
        return 0 if payload["ok"] else 1

    if args.command == "eval":
        payload = run_eval(
            args.cases,
            args.db_file,
            planner=args.planner,
            openai_base_url=args.openai_base_url,
            model=args.model,
            api_key=args.api_key,
            openai_timeout=args.openai_timeout,
        )
        print_json(payload)
        return 0 if payload["ok"] else 1

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())







