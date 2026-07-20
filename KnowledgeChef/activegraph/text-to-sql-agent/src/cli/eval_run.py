"""Eval-run artifact and external scoring helpers for v11.5."""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from activegraph import Event, Graph, Runtime
from activegraph.cli.hospital_logic import sqlite_store_url

TEXT_TO_SQL_DIR = Path(__file__).resolve().parents[2]
DEFAULT_EVAL_RUNS_DIR = TEXT_TO_SQL_DIR / ".tests" / "eval-runs"
SCHEMA_VERSION = "activegraph.eval_run.v01"


class EvalRunError(ValueError):
    """Raised when eval-run artifacts are missing or invalid."""


def new_eval_run_id() -> str:
    return "eval_" + uuid.uuid4().hex[:16]


def _json_default(value: Any) -> str:
    return str(value)


class EvalRunRecorder:
    def __init__(
        self,
        *,
        eval_run_id: str,
        pack_id: str | None,
        cases_file: str | Path,
        eval_runs_dir: str | Path = DEFAULT_EVAL_RUNS_DIR,
        event_store: str | Path | None = None,
    ) -> None:
        self.eval_run_id = eval_run_id
        self.pack_id = pack_id
        self.cases_file = str(Path(cases_file))
        self.event_store = Path(event_store) if event_store is not None else None
        self.root = Path(eval_runs_dir) / eval_run_id
        self.cases_dir = self.root / "cases"
        self.events_file = self.root / "eval_events.jsonl"
        self.root.mkdir(parents=True, exist_ok=True)
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        self.graph: Graph | None = None
        self.runtime: Runtime | None = None
        if self.event_store is not None:
            self.event_store.parent.mkdir(parents=True, exist_ok=True)
            self.graph = Graph(run_id=eval_run_id)
            self.runtime = Runtime(self.graph, behaviors=[], persist_to=str(self.event_store))

    def emit(self, event_type: str, payload: dict[str, Any], *, actor: str = "eval-runner", caused_by: str | None = None) -> dict[str, Any]:
        if self.graph is not None:
            event = Event(
                id=self.graph.ids.event(),
                type=event_type,
                payload=payload,
                actor=actor,
                caused_by=caused_by,
                timestamp=self.graph.clock.now(),
            )
            self.graph.emit(event)
            event_dict = event.to_dict()
        else:
            event_dict = {
                "id": f"eval_evt_{uuid.uuid4().hex[:12]}",
                "type": event_type,
                "payload": payload,
                "actor": actor,
                "caused_by": caused_by,
                "timestamp": None,
            }
        with self.events_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event_dict, ensure_ascii=False, default=_json_default) + "\n")
        return event_dict

    def started(self, *, case_count: int) -> None:
        self.emit(
            "eval.started",
            {
                "schema_version": SCHEMA_VERSION,
                "eval_run_id": self.eval_run_id,
                "pack_id": self.pack_id,
                "cases_file": self.cases_file,
                "case_count": case_count,
                "event_store": str(self.event_store) if self.event_store is not None else None,
                "store_url": sqlite_store_url(self.event_store) if self.event_store is not None else None,
            },
        )

    def case_started(self, case: dict[str, Any]) -> None:
        self.emit(
            "eval.case_started",
            {
                "eval_run_id": self.eval_run_id,
                "case_id": case.get("id"),
                "prompt": case.get("prompt"),
                "expected_policy": _expected_policy(case),
            },
        )

    def case_completed(self, case: dict[str, Any], scored: dict[str, Any]) -> None:
        result = scored.get("result") or {}
        self.emit(
            "eval.case_completed",
            {
                "eval_run_id": self.eval_run_id,
                "case_id": case.get("id"),
                "run_id": result.get("run_id"),
                "ok": scored.get("ok"),
                "failure_summary": scored.get("failures", []),
                "sql": result.get("sql"),
                "params": result.get("params", []),
                "answer": result.get("answer"),
            },
        )

    def completed(self, *, passed: int, failed: int) -> None:
        self.emit(
            "eval.completed",
            {
                "eval_run_id": self.eval_run_id,
                "pack_id": self.pack_id,
                "passed": passed,
                "failed": failed,
                "status": "passed" if failed == 0 else "failed",
            },
        )
        if self.runtime is not None:
            self.runtime.save_state()


def _expected_policy(case: dict[str, Any]) -> dict[str, Any]:
    return {
        key: case[key]
        for key in [
            "expected_sql",
            "expected_params",
            "expected_rows",
            "expected_answer_contains",
            "expected_answer_source",
            "expected_planner_resolution",
            "forbidden_sql_operations",
        ]
        if key in case
    }


def scoring_input_for_case(case: dict[str, Any], scored: dict[str, Any]) -> dict[str, Any]:
    result = scored.get("result") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case.get("id"),
        "prompt": case.get("prompt"),
        "run_id": result.get("run_id"),
        "ok": scored.get("ok"),
        "failures": scored.get("failures", []),
        "answer": result.get("answer"),
        "answer_source": result.get("answer_source"),
        "sql": result.get("sql"),
        "params": result.get("params", []),
        "rows": result.get("rows", []),
        "planner_resolution": result.get("planner_resolution"),
        "clarification_request": result.get("clarification_request"),
        "error": result.get("error"),
        "artifacts": result.get("artifacts", {}),
        "expected_policy": _expected_policy(case),
    }


def write_case_artifacts(recorder: EvalRunRecorder, case: dict[str, Any], scored: dict[str, Any]) -> dict[str, str]:
    case_id = str(case.get("id") or "case")
    case_dir = recorder.cases_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    result = scored.get("result") or {}
    files: dict[str, str] = {}

    result_file = case_dir / "result.json"
    result_file.write_text(json.dumps(scored, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    files["result_file"] = str(result_file)

    scoring_file = case_dir / "scoring-input.json"
    scoring_file.write_text(json.dumps(scoring_input_for_case(case, scored), ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    files["scoring_input_file"] = str(scoring_file)

    artifacts = result.get("artifacts") or {}
    for source_key, target_name in [("trace_file", "trace.jsonl"), ("graph_file", "graph.json")]:
        source = artifacts.get(source_key)
        if source and Path(source).exists():
            target = case_dir / target_name
            shutil.copyfile(source, target)
            files[source_key] = str(target)
    return files


def write_eval_manifest(recorder: EvalRunRecorder, *, cases: list[dict[str, Any]], scored_cases: list[dict[str, Any]], passed: int, failed: int) -> dict[str, str]:
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "eval_run_id": recorder.eval_run_id,
        "pack_id": recorder.pack_id,
        "cases_file": recorder.cases_file,
        "case_count": len(cases),
        "event_store": str(recorder.event_store) if recorder.event_store is not None else None,
        "store_url": sqlite_store_url(recorder.event_store) if recorder.event_store is not None else None,
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "eval_run_id": recorder.eval_run_id,
        "pack_id": recorder.pack_id,
        "passed": passed,
        "failed": failed,
        "ok": failed == 0,
        "cases": [
            {
                "id": scored.get("id"),
                "ok": scored.get("ok"),
                "run_id": (scored.get("result") or {}).get("run_id"),
                "failures": scored.get("failures", []),
            }
            for scored in scored_cases
        ],
    }
    manifest_file = recorder.root / "manifest.json"
    summary_file = recorder.root / "summary.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return {
        "eval_run_dir": str(recorder.root),
        "manifest_file": str(manifest_file),
        "summary_file": str(summary_file),
        "eval_events_file": str(recorder.events_file),
    }


def export_eval_run(eval_run_id: str, *, eval_runs_dir: str | Path = DEFAULT_EVAL_RUNS_DIR, output_dir: str | Path | None = None) -> dict[str, Any]:
    source = Path(eval_runs_dir) / eval_run_id
    if not source.exists():
        raise EvalRunError(f"eval run not found: {source}")
    target_root = Path(output_dir) if output_dir is not None else source.parent / "exports"
    target = target_root / eval_run_id
    target_root.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return {
        "ok": True,
        "eval_run_id": eval_run_id,
        "source_dir": str(source),
        "export_dir": str(target),
        "manifest_file": str(target / "manifest.json"),
        "summary_file": str(target / "summary.json"),
    }


def attach_external_score(
    eval_run_id: str,
    case_id: str,
    *,
    score_file: str | Path,
    eval_runs_dir: str | Path = DEFAULT_EVAL_RUNS_DIR,
    scorer: str = "third-party",
) -> dict[str, Any]:
    root = Path(eval_runs_dir) / eval_run_id
    case_dir = root / "cases" / case_id
    if not case_dir.exists():
        raise EvalRunError(f"eval case artifact not found: {case_dir}")
    source = Path(score_file)
    if not source.exists():
        raise EvalRunError(f"score file not found: {source}")
    try:
        score_payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvalRunError(f"score file must be JSON: {source}: {exc}") from exc

    target = case_dir / "external-score.json"
    target.write_text(json.dumps(score_payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    events_file = root / "eval_events.jsonl"
    for event_type in ["eval.case_scored", "external_judgment.recorded"]:
        event = {
            "id": f"eval_evt_{uuid.uuid4().hex[:12]}",
            "type": event_type,
            "actor": scorer,
            "caused_by": None,
            "timestamp": None,
            "payload": {
                "eval_run_id": eval_run_id,
                "case_id": case_id,
                "scorer": scorer,
                "score": score_payload.get("score"),
                "rubric": score_payload.get("rubric"),
                "notes": score_payload.get("notes"),
                "external_score_file": str(target),
            },
        }
        with events_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, default=_json_default) + "\n")
    return {
        "ok": True,
        "eval_run_id": eval_run_id,
        "case_id": case_id,
        "external_score_file": str(target),
        "events_file": str(events_file),
    }