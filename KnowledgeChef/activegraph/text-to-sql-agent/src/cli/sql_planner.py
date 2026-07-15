"""Deterministic v11 SQL planner-resolution helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from activegraph.cli.hospital_logic import RuleCatalog, normalize_prompt_text


@dataclass(frozen=True)
class PlannerResolution:
    original_prompt: str
    session_resolved_prompt: str
    planner_resolved_prompt: str
    status: str
    imperfection_types: list[str] = field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[dict[str, Any]] = field(default_factory=list)
    resolution_strategy: str = "unsupported"
    selected_rule_hint: str | None = None
    sub_intents: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    llm_used: bool = False
    llm_invocation_id: str | None = None
    clarification_question: str | None = None
    clarification_options: list[str] = field(default_factory=list)
    unresolved_slots: list[str] = field(default_factory=list)

    def to_graph_data(self) -> dict[str, Any]:
        return {
            "original_prompt": self.original_prompt,
            "session_resolved_prompt": self.session_resolved_prompt,
            "planner_resolved_prompt": self.planner_resolved_prompt,
            "status": self.status,
            "imperfection_types": list(self.imperfection_types),
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "resolution_strategy": self.resolution_strategy,
            "selected_rule_hint": self.selected_rule_hint,
            "sub_intents": list(self.sub_intents),
            "evidence": list(self.evidence),
            "llm_used": self.llm_used,
            "llm_invocation_id": self.llm_invocation_id,
            "clarification_question": self.clarification_question,
            "clarification_options": list(self.clarification_options),
            "unresolved_slots": list(self.unresolved_slots),
        }


def load_planner_resolution_model(path: str | Path) -> dict[str, Any]:
    model_path = Path(path)
    data = yaml.safe_load(model_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        return {}
    model = data.get("planner_resolution_model")
    return model if isinstance(model, dict) else {}


def planner_enabled(path: str | Path) -> bool:
    return bool(load_planner_resolution_model(path))


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", normalize_prompt_text(text).lower())


def _configured_mappings(config: dict[str, Any]) -> dict[str, str]:
    detectors = config.get("imperfection_detectors") if isinstance(config.get("imperfection_detectors"), dict) else {}
    concept = detectors.get("concept_mismatch") if isinstance(detectors.get("concept_mismatch"), dict) else {}
    mappings = concept.get("mappings") if isinstance(concept.get("mappings"), dict) else {}
    return {str(key): str(value) for key, value in mappings.items()}


def _confidence_policy(config: dict[str, Any]) -> dict[str, float]:
    policy = config.get("confidence_policy") if isinstance(config.get("confidence_policy"), dict) else {}
    return {
        "auto_resolve_min": float(policy.get("auto_resolve_min", 0.80)),
        "clarification_below": float(policy.get("clarification_below", 0.70)),
    }


def _direct_match_resolution(
    *,
    prompt: str,
    original_prompt: str,
    session_resolution: dict[str, Any],
    catalog: RuleCatalog,
    config: dict[str, Any],
) -> PlannerResolution | None:
    match = catalog.match_with_bindings(prompt)
    if match is None:
        return None

    rule = match.rule
    intent = dict(rule.intent)
    imperfection_types: list[str] = []
    assumptions: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = [
        {"kind": "rule_match", "rule_id": rule.id, "eval_refs": list(rule.eval_refs)},
    ]

    if session_resolution.get("resolved"):
        imperfection_types.append("ellipsis")
        assumptions.append(
            {
                "slot": session_resolution.get("entity_type"),
                "value": session_resolution.get("entity_value"),
                "reason": f"session memory strategy {session_resolution.get('strategy')}",
            }
        )
        evidence.append({"kind": "session_resolution", **session_resolution})

    mappings = _configured_mappings(config)
    alias = intent.get("alias")
    for source, target in mappings.items():
        if source in prompt and target == intent.get("entity"):
            imperfection_types.append("concept_mismatch")
            assumptions.append(
                {
                    "slot": "entity",
                    "value": target,
                    "reason": f"'{source}' maps to schema entity '{target}'",
                }
            )

    if intent.get("filter") == "vip_customers_confirmed_orders" or "confirmed" in [str(value) for value in rule.params]:
        imperfection_types.append("implicit_constraint")
        assumptions.append(
            {
                "slot": "orders.status",
                "value": "confirmed",
                "reason": "pack policy treats sales revenue as confirmed orders only",
            }
        )

    if intent.get("filters", {}).get("status") == "예정됨":
        imperfection_types.append("implicit_constraint")
        assumptions.append(
            {
                "slot": "appointments.status",
                "value": "예정됨",
                "reason": "hospital appointment-count rule defaults to scheduled appointments",
            }
        )

    # Preserve order while removing duplicates.
    imperfection_types = list(dict.fromkeys(imperfection_types))
    assumptions = [dict(item) for item in assumptions]
    return PlannerResolution(
        original_prompt=original_prompt,
        session_resolved_prompt=prompt,
        planner_resolved_prompt=prompt,
        status="resolved",
        imperfection_types=imperfection_types,
        confidence=1.0 if not imperfection_types else 0.90,
        assumptions=assumptions,
        resolution_strategy="direct_rule_match" if not imperfection_types else "rule_match_with_assumptions",
        selected_rule_hint=rule.id,
        evidence=evidence,
    )


def _clarification(
    *,
    prompt: str,
    original_prompt: str,
    status: str,
    imperfection_types: list[str],
    confidence: float,
    question: str,
    options: list[str],
    unresolved_slots: list[str],
    strategy: str,
    evidence: list[dict[str, Any]],
    sub_intents: list[dict[str, Any]] | None = None,
) -> PlannerResolution:
    return PlannerResolution(
        original_prompt=original_prompt,
        session_resolved_prompt=prompt,
        planner_resolved_prompt=prompt,
        status=status,
        imperfection_types=imperfection_types,
        confidence=confidence,
        resolution_strategy=strategy,
        evidence=evidence,
        sub_intents=list(sub_intents or []),
        clarification_question=question,
        clarification_options=options,
        unresolved_slots=unresolved_slots,
    )


def resolve_sql_planner(
    prompt: str,
    *,
    original_prompt: str | None,
    session_resolution: dict[str, Any] | None,
    catalog: RuleCatalog,
    config: dict[str, Any],
) -> PlannerResolution:
    normalized_prompt = normalize_prompt_text(prompt)
    original = normalize_prompt_text(original_prompt or prompt)
    session = dict(session_resolution or {})

    compact = _compact(normalized_prompt)
    policy = _confidence_policy(config)
    clarification_confidence = max(0.0, min(policy["clarification_below"], 0.65))

    count_marker = bool(
        re.search(r"(몇\s*명|몇|고객\s*수|회원\s*수|총\s*수)", normalized_prompt)
    )
    list_marker = any(token in normalized_prompt for token in ["누구", "명단", "목록", "리스트", "이름"])
    if "vip" in compact and count_marker and list_marker:
        return _clarification(
            prompt=normalized_prompt,
            original_prompt=original,
            status="clarification_required",
            imperfection_types=["multi_intent"],
            confidence=0.72,
            question="VIP 고객 수와 명단을 모두 조회할까요? 현재 v11에서는 한 번에 하나의 조회로 실행해 주세요: 'VIP는 몇명' 또는 'VIP는 누구'.",
            options=["VIP는 몇명", "VIP는 누구"],
            unresolved_slots=["multi_intent.execution_order"],
            strategy="multi_intent_detected_without_orchestration",
            evidence=[{"kind": "multi_intent_markers", "prompt": normalized_prompt}],
            sub_intents=[
                {"prompt": "VIP는 몇명", "expected_rule_hint": "vip_customer_count"},
                {"prompt": "VIP는 누구", "expected_rule_hint": "vip_customer_list"},
            ],
        )

    if any(token in compact for token in ["가장많이팔린", "많이팔린", "잘팔린", "잘팔리는"]):
        return _clarification(
            prompt=normalized_prompt,
            original_prompt=original,
            status="clarification_required",
            imperfection_types=["ambiguity"],
            confidence=clarification_confidence,
            question="무엇을 기준으로 가장 많이 팔린 항목을 볼까요? 수량 기준 상품, 매출 기준 상품 중 하나를 선택해 주세요.",
            options=["수량 기준 상품", "매출 기준 상품"],
            unresolved_slots=["sales.metric", "sales.group_by"],
            strategy="ambiguous_sales_metric",
            evidence=[{"kind": "ambiguous_phrase", "phrase": "가장 많이 팔린 거"}],
        )

    if "이번달" in compact and "매출" in compact:
        return _clarification(
            prompt=normalized_prompt,
            original_prompt=original,
            status="clarification_required",
            imperfection_types=["implicit_constraint"],
            confidence=clarification_confidence,
            question="이번 달 매출의 기준 월과 주문 상태를 확인해 주세요. 예: 2026년 7월 확정 주문 매출.",
            options=["현재 월 확정 주문", "특정 월 지정", "전체 기간 확정 주문"],
            unresolved_slots=["date_range", "orders.status"],
            strategy="implicit_time_window_requires_clarification",
            evidence=[{"kind": "implicit_time_window", "phrase": "이번 달"}],
        )

    direct = _direct_match_resolution(
        prompt=normalized_prompt,
        original_prompt=original,
        session_resolution=session,
        catalog=catalog,
        config=config,
    )
    if direct is not None:
        return direct

    return PlannerResolution(
        original_prompt=original,
        session_resolved_prompt=normalized_prompt,
        planner_resolved_prompt=normalized_prompt,
        status="unsupported",
        imperfection_types=[],
        confidence=0.0,
        resolution_strategy="no_rule_or_planner_candidate",
        evidence=[{"kind": "no_match", "catalog_id": catalog.id}],
    )

