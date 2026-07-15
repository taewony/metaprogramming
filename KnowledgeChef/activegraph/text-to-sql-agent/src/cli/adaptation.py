"""Event-log adaptation analysis for Text-to-SQL behavior runs.

v09 keeps adaptation explicit: the analyzer proposes eval/model changes from
recorded evidence, but it does not edit source, YAML, or eval files directly.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from activegraph import Runtime

from activegraph.cli.hospital_logic import sqlite_store_url
from activegraph.cli.text_to_sql import DEFAULT_TESTS_DIR, resolve_run_selector

DEFAULT_ADAPTATION_DIR = DEFAULT_TESTS_DIR.parent / "adaptations"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_hash(payload: dict[str, Any], *, prefix: str) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return f"{prefix}_" + hashlib.sha256(encoded).hexdigest()[:16]


def _event_dict(event: Any) -> dict[str, Any]:
    return event.to_dict() if hasattr(event, "to_dict") else dict(event)


def _question_prompts(events: list[Any]) -> dict[str, str]:
    prompts: dict[str, str] = {}
    for event in events:
        if event.type == "question.submitted":
            prompts[event.id] = str(event.payload.get("prompt", ""))
    return prompts


def _first_prompt(events: list[Any]) -> str:
    for event in events:
        if event.type == "question.submitted":
            return str(event.payload.get("prompt", ""))
    return ""


def _classify_events(events: list[Any], *, run_id: str) -> list[dict[str, Any]]:
    prompts_by_event_id = _question_prompts(events)
    fallback_prompt = _first_prompt(events)
    classifications: list[dict[str, Any]] = []

    for event in events:
        if event.type == "behavior.failed":
            payload = event.payload
            exception_type = str(payload.get("exception_type") or "")
            triggering_event_id = str(payload.get("event_id") or "")
            prompt = prompts_by_event_id.get(triggering_event_id, fallback_prompt)
            if exception_type == "UnsupportedPromptError":
                kind = "unsupported_prompt"
                severity = "medium"
            else:
                kind = "behavior_exception"
                severity = "high"
            classifications.append(
                {
                    "kind": kind,
                    "severity": severity,
                    "run_id": run_id,
                    "event_id": event.id,
                    "triggering_event_id": triggering_event_id,
                    "behavior": payload.get("behavior"),
                    "exception_type": exception_type,
                    "message": payload.get("message"),
                    "prompt": prompt,
                }
            )
        elif event.type == "entity.validation_failed":
            classifications.append(
                {
                    "kind": "validation_miss",
                    "severity": "low",
                    "run_id": run_id,
                    "event_id": event.id,
                    "prompt": fallback_prompt,
                    "message": "Entity validation failed before SQL execution.",
                }
            )
        elif event.type == "llm.fallback_used":
            classifications.append(
                {
                    "kind": "llm_fallback",
                    "severity": "low",
                    "run_id": run_id,
                    "event_id": event.id,
                    "prompt": fallback_prompt,
                    "message": event.payload.get("error"),
                }
            )
        elif event.type in {"user.correction_submitted", "answer.corrected", "correction.submitted"}:
            classifications.append(
                {
                    "kind": "user_correction",
                    "severity": "medium",
                    "run_id": run_id,
                    "event_id": event.id,
                    "prompt": str(event.payload.get("prompt") or fallback_prompt),
                    "message": event.payload.get("correction") or event.payload.get("message"),
                }
            )

    if len(events) >= 40:
        classifications.append(
            {
                "kind": "slow_path",
                "severity": "low",
                "run_id": run_id,
                "event_id": events[-1].id if events else None,
                "prompt": fallback_prompt,
                "message": f"Run emitted {len(events)} events; inspect for unnecessary behavior churn.",
            }
        )
    return classifications


def _draft_eval_case(classification: dict[str, Any], *, pack_id: str | None) -> dict[str, Any]:
    prompt = classification.get("prompt") or ""
    return {
        "id": _stable_hash({"prompt": prompt, "kind": classification.get("kind")}, prefix="v09_eval"),
        "source": "v09_adaptation_loop",
        "pack_id": pack_id,
        "prompt": prompt,
        "expected_behavior": "pending_human_decision",
        "expected_sql": None,
        "expected_params": [],
        "expected_answer_contains": [],
        "evidence_run_id": classification.get("run_id"),
        "evidence_event_id": classification.get("event_id"),
    }


def _proposal_for_classification(
    classification: dict[str, Any],
    *,
    pack_id: str | None,
    system_model_file: str | Path | None,
) -> dict[str, Any]:
    proposal_seed = {
        "kind": classification.get("kind"),
        "prompt": classification.get("prompt"),
        "run_id": classification.get("run_id"),
        "event_id": classification.get("event_id"),
        "system_model_file": str(system_model_file) if system_model_file else None,
    }
    proposal_id = _stable_hash(proposal_seed, prefix="adapt")
    kind = classification.get("kind")
    if kind == "user_correction":
        target = {
            "kind": "eval_case.behavior_expectation",
            "file": None,
            "operation": "convert_correction_to_regression_case",
        }
        proposed_change = "Turn the user correction into an explicit eval expectation before changing behavior."
    elif kind == "unsupported_prompt":
        target = {
            "kind": "system_model.rule_catalog",
            "file": str(system_model_file) if system_model_file else None,
            "operation": "add_rule_or_alias_after_eval",
        }
        proposed_change = "Add a deterministic rule, alias, or planner-resolution behavior only after a failing eval case captures this prompt."
    elif kind == "validation_miss":
        target = {
            "kind": "system_model.entity_validation_model",
            "file": str(system_model_file) if system_model_file else None,
            "operation": "review_validator_or_entity_dictionary",
        }
        proposed_change = "Review entity validation coverage and decide whether the entity should be accepted, clarified, or rejected."
    elif kind == "llm_fallback":
        target = {"kind": "llm_adapter", "file": None, "operation": "inspect_provider_or_timeout"}
        proposed_change = "Inspect LLM adapter availability, timeout, and fallback policy before changing deterministic behavior."
    else:
        target = {"kind": "runtime.behavior", "file": None, "operation": "inspect_exception"}
        proposed_change = "Inspect the behavior exception and add the narrowest regression test before runtime changes."

    return {
        "id": proposal_id,
        "type": "behavior_adaptation_proposal",
        "schema_version": "activegraph.adaptation_proposal.v01",
        "status": "proposed",
        "classification": kind,
        "pack_id": pack_id,
        "created_at": _utc_now(),
        "target": target,
        "evidence": {
            "run_id": classification.get("run_id"),
            "event_id": classification.get("event_id"),
            "triggering_event_id": classification.get("triggering_event_id"),
            "prompt": classification.get("prompt"),
            "exception_type": classification.get("exception_type"),
            "message": classification.get("message"),
        },
        "proposed_change": proposed_change,
        "draft_eval_case": _draft_eval_case(classification, pack_id=pack_id),
        "validation_plan": [
            "add eval case that reproduces the observed prompt/failure",
            "apply the smallest system-model or behavior change that satisfies the eval",
            "run focused Text-to-SQL TDD tests",
            "run pack validate for the affected pack",
            "inspect the repaired run and compare it with the evidence run",
        ],
        "auto_apply": False,
    }


def _summary(classifications: list[dict[str, Any]], proposals: list[dict[str, Any]]) -> dict[str, Any]:
    def count(kind: str) -> int:
        return sum(1 for item in classifications if item.get("kind") == kind)

    return {
        "classification_count": len(classifications),
        "proposal_count": len(proposals),
        "unsupported_prompts": count("unsupported_prompt"),
        "behavior_exceptions": count("behavior_exception"),
        "slow_paths": count("slow_path"),
        "validation_misses": count("validation_miss"),
        "llm_fallbacks": count("llm_fallback"),
        "user_corrections": count("user_correction"),
    }


def _artifact_graph(analysis: dict[str, Any]) -> dict[str, Any]:
    analysis_obj_id = "adaptation_analysis#1"
    objects = [
        {
            "id": analysis_obj_id,
            "type": "adaptation_analysis",
            "data": {
                "source_run_id": analysis["source_run_id"],
                "event_store": analysis["event_store"],
                "summary": analysis["summary"],
            },
        }
    ]
    relations: list[dict[str, Any]] = []
    events = [
        {
            "id": "adapt_evt_001",
            "type": "adaptation.analysis_created",
            "payload": {"source_run_id": analysis["source_run_id"], "proposal_count": len(analysis["proposals"])},
            "actor": "activegraph.v09_adaptation_loop",
            "timestamp": analysis["created_at"],
        }
    ]
    for index, proposal in enumerate(analysis["proposals"], start=1):
        object_id = f"adaptation_proposal#{index}"
        objects.append({"id": object_id, "type": "adaptation_proposal", "data": proposal})
        relations.append({"source": object_id, "type": "derived_from", "target": analysis_obj_id})
        events.append(
            {
                "id": f"adapt_evt_{index + 1:03d}",
                "type": "adaptation.proposal_created",
                "payload": {"proposal_id": proposal["id"], "classification": proposal["classification"]},
                "actor": "activegraph.v09_adaptation_loop",
                "timestamp": analysis["created_at"],
            }
        )
    return {"objects": objects, "relations": relations, "events": events}


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_artifacts(analysis: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    run_dir = output_dir / analysis["source_run_id"]
    proposal_dir = run_dir / "proposals"
    proposal_dir.mkdir(parents=True, exist_ok=True)

    analysis_file = run_dir / "analysis.json"
    graph_file = run_dir / "adaptation_graph.json"
    event_file = run_dir / "adaptation_events.jsonl"

    proposal_files: list[str] = []
    for proposal in analysis["proposals"]:
        proposal_file = proposal_dir / f"{proposal['id']}.json"
        _write_json(proposal_file, proposal)
        proposal_files.append(str(proposal_file))

    artifact_graph = _artifact_graph(analysis)
    _write_json(graph_file, {"source_run_id": analysis["source_run_id"], **artifact_graph})
    with event_file.open("w", encoding="utf-8") as handle:
        for event in artifact_graph["events"]:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    analysis_with_artifacts = dict(analysis)
    analysis_with_artifacts["artifacts"] = {
        "analysis_file": str(analysis_file),
        "proposal_files": proposal_files,
        "event_file": str(event_file),
        "graph_file": str(graph_file),
    }
    _write_json(analysis_file, analysis_with_artifacts)
    return analysis_with_artifacts["artifacts"]


def analyze_text_to_sql_adaptation(
    event_store: str | Path,
    *,
    run_selector: str | None = "0",
    output_dir: str | Path = DEFAULT_ADAPTATION_DIR,
    pack_id: str | None = None,
    system_model_file: str | Path | None = None,
) -> dict[str, Any]:
    store_path = Path(event_store)
    chosen_run_id = resolve_run_selector(run_selector, store_path)
    runtime = Runtime.load(str(store_path), run_id=chosen_run_id)
    events = list(runtime.graph.events)
    classifications = _classify_events(events, run_id=chosen_run_id)
    proposals = [
        _proposal_for_classification(item, pack_id=pack_id, system_model_file=system_model_file)
        for item in classifications
        if item.get("kind") in {"unsupported_prompt", "validation_miss", "behavior_exception", "llm_fallback", "slow_path", "user_correction"}
    ]
    analysis = {
        "ok": True,
        "analysis_type": "activegraph.adaptation_analysis.v01",
        "created_at": _utc_now(),
        "event_store": str(store_path),
        "store_url": sqlite_store_url(store_path),
        "source_run_id": chosen_run_id,
        "run_selector": run_selector if run_selector is not None else "0",
        "pack_id": pack_id,
        "system_model_file": str(system_model_file) if system_model_file else None,
        "summary": _summary(classifications, proposals),
        "classifications": classifications,
        "proposals": proposals,
        "artifacts": {},
    }
    analysis["artifacts"] = _write_artifacts(analysis, Path(output_dir))
    return analysis


def accept_adaptation_proposal(
    proposal_file: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    source_path = Path(proposal_file)
    proposal = json.loads(source_path.read_text(encoding="utf-8"))
    target_dir = Path(output_dir) if output_dir is not None else source_path.parent / "accepted"
    target_dir.mkdir(parents=True, exist_ok=True)

    eval_case = dict(proposal.get("draft_eval_case") or {})
    eval_case["accepted_proposal_id"] = proposal.get("id")
    eval_case["acceptance_status"] = "accepted"
    eval_case_file = target_dir / f"{proposal['id']}.eval.jsonl"
    eval_case_file.write_text(json.dumps(eval_case, ensure_ascii=False) + "\n", encoding="utf-8")

    patch_hint = {
        "schema_version": "activegraph.system_model_patch_hint.v01",
        "proposal_id": proposal.get("id"),
        "target": proposal.get("target"),
        "evidence": proposal.get("evidence"),
        "proposed_change": proposal.get("proposed_change"),
        "validation_plan": proposal.get("validation_plan"),
        "auto_apply": False,
    }
    patch_hint_file = target_dir / f"{proposal['id']}.system-model.patch-hint.yaml"
    patch_hint_file.write_text(json.dumps(patch_hint, ensure_ascii=False, indent=2), encoding="utf-8")

    acceptance = {
        "ok": True,
        "schema_version": "activegraph.adaptation_acceptance.v01",
        "status": "accepted",
        "accepted_at": _utc_now(),
        "proposal_id": proposal.get("id"),
        "source_proposal_file": str(source_path),
        "generated_artifacts": {
            "eval_case_file": str(eval_case_file),
            "system_model_patch_hint_file": str(patch_hint_file),
        },
    }
    _write_json(target_dir / f"{proposal['id']}.acceptance.json", acceptance)
    return acceptance

