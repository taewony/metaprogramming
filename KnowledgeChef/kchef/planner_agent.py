#!/usr/bin/env python3
"""Standalone KnowledgeChef planner agent.

This module implements the planner front-end described in
`planner_design_document.md`. It is intentionally executor-free: the
planner only compiles a question into Knowledge IR and performs a dry-run
validation pass.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path("data/techshop.db")
DEFAULT_SKILLS_DIR = Path("kchef")


@dataclass
class IntentResult:
    primary: str
    sub_intents: list[str]
    confidence: float
    evidence: list[str]


@dataclass
class AmbiguityResolution:
    element: str
    candidates: list[str]
    selected: str
    method: str
    confidence: float
    rationale: str


@dataclass
class ResolvedQuery:
    intent: str
    concepts: list[str]
    constraints: dict[str, str]
    projections: list[str]
    ambiguity_log: list[AmbiguityResolution] = field(default_factory=list)


@dataclass
class KnowledgeStep:
    type: str
    source: str
    filters: list[dict[str, Any]] | None = None
    join: dict[str, Any] | None = None
    group_by: list[str] | None = None
    order_by: list[dict[str, Any]] | None = None
    limit: int | None = None
    projections: list[str] | None = None
    aggregation: dict[str, Any] | None = None


@dataclass
class KnowledgeIR:
    intent: str
    sub_intents: list[str] | None
    description: str
    concepts: list[str]
    steps: list[KnowledgeStep]
    output_structure: dict[str, str]
    ambiguity_resolutions: list[AmbiguityResolution] | None
    confidence: float
    playbook_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "sub_intents": self.sub_intents,
            "description": self.description,
            "concepts": self.concepts,
            "steps": [step.__dict__ for step in self.steps],
            "output_structure": self.output_structure,
            "ambiguity_resolutions": [item.__dict__ for item in self.ambiguity_resolutions or []],
            "confidence": self.confidence,
            "playbook_used": self.playbook_used,
        }


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str]


class IntentRecognizer:
    PATTERNS = {
        "COUNT": [r"몇\s*명", r"몇\s*개", r"수는?", r"총\s*수"],
        "LIST": [r"누구", r"알려줘", r"목록", r"보여줘", r"어떤"],
        "AGGREGATE": [r"총\s*금액", r"평균", r"합계", r"합산", r"얼마"],
        "TOPK": [r"가장", r"최고", r"최다", r"제일", r"1위"],
        "EXISTENCE": [r"있나", r"있어", r"없는", r"없나"],
        "COMPARE": [r"대비", r"비교", r"차이"],
        "TREND": [r"추세", r"증가", r"감소", r"변화"],
        "SUMMARIZE": [r"요약", r"성과", r"정리해"],
    }

    def recognize(self, question: str) -> IntentResult:
        matched: dict[str, list[str]] = {}
        for intent, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question):
                    matched.setdefault(intent, []).append(pattern)

        if not matched:
            return IntentResult(primary="SUMMARIZE", sub_intents=[], confidence=0.5, evidence=[])
        if len(matched) == 1:
            intent = next(iter(matched))
            return IntentResult(primary=intent, sub_intents=[], confidence=0.95, evidence=matched[intent])
        intents = list(matched)
        evidence = [item for patterns in matched.values() for item in patterns]
        return IntentResult(primary="COMPOUND", sub_intents=intents, confidence=0.9, evidence=evidence)


class ConceptMatcher:
    CONCEPT_RULES = {
        "customer": (r"고객|VIP|회원|사람", "Customer", "customers"),
        "product": (r"상품|제품|비싼|팔린|거", "Product", "products"),
        "order": (r"주문|매출|구매|판매", "Order", "orders"),
        "order_item": (r"주문\s*상세|수량|단가|소계", "OrderItem", "order_items"),
        "grade": (r"VIP|GOLD|SILVER|BRONZE|등급", "Grade", "customers"),
        "revenue": (r"매출|금액|총\s*금액", "Revenue", "orders"),
    }

    def __init__(self, system_model: dict[str, Any]):
        self.system_model = system_model

    def match(self, question: str, intent: IntentResult) -> list[str]:
        concepts: list[str] = []
        for _, (pattern, concept, _) in self.CONCEPT_RULES.items():
            if re.search(pattern, question):
                concepts.append(concept)
        if not concepts:
            if intent.primary in {"COUNT", "LIST", "COMPOUND"}:
                concepts.append("Customer")
        return list(dict.fromkeys(concepts))


class AmbiguityResolver:
    DEFAULT_RULES = {
        "이번 달": {"resolve_to": "current_month", "method": "default"},
        "올해": {"resolve_to": "current_year", "method": "default"},
        "최근": {"resolve_to": "last_7_days", "method": "default"},
        "매출": {"resolve_to": "status_not_cancelled", "method": "default"},
        "팔린": {"resolve_to": "SUM(quantity)", "method": "default"},
        "비싼": {"resolve_to": "price_DESC", "method": "default"},
        "거": {"resolve_to": "Product", "method": "default"},
    }

    def resolve(self, question: str, intent: IntentResult, concepts: list[str], context: dict[str, Any] | None = None) -> ResolvedQuery:
        constraints: dict[str, str] = {}
        ambiguity_log: list[AmbiguityResolution] = []

        for token in ("이번 달", "올해", "최근"):
            if token in question:
                rule = self.DEFAULT_RULES[token]
                constraints["temporal"] = rule["resolve_to"]
                ambiguity_log.append(
                    AmbiguityResolution(
                        element=token,
                        candidates=[rule["resolve_to"], "전체 기간"],
                        selected=rule["resolve_to"],
                        method="default",
                        confidence=0.95,
                        rationale=f"AMBIGUITY.md 규칙: '{token}' → {rule['resolve_to']}",
                    )
                )

        for token, rule in self.DEFAULT_RULES.items():
            if token in question and token not in {"이번 달", "올해", "최근"}:
                ambiguity_log.append(
                    AmbiguityResolution(
                        element=token,
                        candidates=[rule["resolve_to"], "alternative"],
                        selected=rule["resolve_to"],
                        method=rule["method"],
                        confidence=0.9,
                        rationale="AMBIGUITY.md 규칙 적용",
                    )
                )

        if context and context.get("error"):
            constraints["error_context"] = str(context["error"])

        projections = ["id", "name", "email"]
        if "Customer" in concepts:
            projections.append("point_balance")

        return ResolvedQuery(
            intent=intent.primary,
            concepts=concepts,
            constraints=constraints,
            projections=list(dict.fromkeys(projections)),
            ambiguity_log=ambiguity_log,
        )


class GoalDecomposer:
    def decompose(self, intent: str, concepts: list[str], constraints: dict[str, str]) -> list[dict[str, Any]]:
        if intent != "COMPOUND":
            return [{"name": intent, "concepts": concepts, "constraints": constraints}]
        sub_goals = []
        if "COUNT" in concepts or "Customer" in concepts:
            sub_goals.append({"name": "COUNT", "concepts": concepts, "constraints": constraints})
        sub_goals.append({"name": "LIST", "concepts": concepts, "constraints": constraints})
        return sub_goals


class PlaybookEngine:
    def select(self, intent: str, concepts: list[str]) -> dict[str, str]:
        if intent == "COMPOUND":
            return {"id": "FILTER_AND_LIST", "strategy": "sqlite"}
        if intent == "COUNT":
            return {"id": "FILTER_AND_COUNT", "strategy": "sqlite"}
        if intent == "TOPK":
            return {"id": "RANK_AND_LIMIT", "strategy": "sqlite"}
        if intent == "AGGREGATE":
            return {"id": "TEMPORAL_AGGREGATE", "strategy": "sqlite"}
        return {"id": "DIRECT_LOOKUP", "strategy": "sqlite"}

    def select_alternative(self, intent: str, concepts: list[str], exclude: list[str] | None = None) -> dict[str, str]:
        exclude = exclude or []
        candidate = self.select(intent, concepts)
        if candidate["id"] not in exclude:
            return candidate
        return {"id": "DIRECT_LOOKUP", "strategy": "sqlite"}


class MentalSimulator:
    def __init__(self, system_model: dict[str, Any]):
        self.system_model = system_model

    def validate(self, ir: KnowledgeIR) -> ValidationResult:
        errors: list[str] = []
        tables = set(self.system_model.get("tables", {}))
        if not tables:
            tables = {"customers", "products", "orders", "order_items"}

        for step in ir.steps:
            if step.source not in tables:
                errors.append(f"unknown source: {step.source}")
            if step.projections and step.source == "customers":
                missing = [field for field in step.projections if field not in self.system_model.get("tables", {}).get("customers", [])]
                if missing:
                    errors.append(f"unknown projection(s) for customers: {', '.join(missing)}")
        return ValidationResult(passed=not errors, errors=errors)


class RecipeCompiler:
    def compile(self, resolved: ResolvedQuery, sub_goals: list[dict[str, Any]], playbook: dict[str, str]) -> KnowledgeIR:
        steps: list[KnowledgeStep] = []
        if resolved.intent in {"COUNT", "LIST", "COMPOUND"}:
            steps.append(
                KnowledgeStep(
                    type="data",
                    source="customers",
                    filters=[{"field": "grade", "operator": "=", "value": "VIP"}],
                    projections=resolved.projections,
                )
            )
        elif resolved.intent == "AGGREGATE":
            steps.append(
                KnowledgeStep(
                    type="data",
                    source="orders",
                    filters=[{"field": "status", "operator": "!=", "value": "cancelled"}],
                    aggregation={"function": "SUM", "field": "total_amount"},
                )
            )
        else:
            steps.append(KnowledgeStep(type="data", source="customers", projections=resolved.projections))

        output_structure = {"count": "integer", "list": "array<{id, name, email, point_balance}>"}
        if resolved.intent == "AGGREGATE":
            output_structure = {"total_revenue": "number", "period": "string"}

        return KnowledgeIR(
            intent=resolved.intent,
            sub_intents=[goal["name"] for goal in sub_goals] if resolved.intent == "COMPOUND" else None,
            description=self._describe(resolved, sub_goals),
            concepts=resolved.concepts,
            steps=steps,
            output_structure=output_structure,
            ambiguity_resolutions=resolved.ambiguity_log,
            confidence=self._confidence(resolved),
            playbook_used=playbook["id"],
        )

    def _describe(self, resolved: ResolvedQuery, sub_goals: list[dict[str, Any]]) -> str:
        if resolved.intent == "COMPOUND":
            return "복합 의도를 분해해 고객 수와 목록을 조회한다"
        if resolved.intent == "COUNT":
            return "대상을 집계하여 개수를 계산한다"
        if resolved.intent == "AGGREGATE":
            return "확정 상태 기준 매출 합계를 계산한다"
        return "자연어 질의를 Knowledge IR로 변환한다"

    def _confidence(self, resolved: ResolvedQuery) -> float:
        base = 0.9
        if resolved.ambiguity_log:
            base = min(0.99, base + 0.05)
        return base


class PlannerPipeline:
    def __init__(self, system_model: dict[str, Any], skills_dir: str | Path, llm_client: Any | None = None):
        self.system_model = system_model
        self.skills_dir = Path(skills_dir)
        self.intent_recognizer = IntentRecognizer()
        self.concept_matcher = ConceptMatcher(system_model)
        self.ambiguity_resolver = AmbiguityResolver()
        self.decomposer = GoalDecomposer()
        self.playbook_engine = PlaybookEngine()
        self.simulator = MentalSimulator(system_model)
        self.compiler = RecipeCompiler()
        self.llm = llm_client

    def plan(self, question: str, context: dict[str, Any] | None = None) -> KnowledgeIR:
        intent = self.intent_recognizer.recognize(question)
        concepts = self.concept_matcher.match(question, intent)
        resolved = self.ambiguity_resolver.resolve(question=question, intent=intent, concepts=concepts, context=context)
        sub_goals = self.decomposer.decompose(intent=resolved.intent, concepts=resolved.concepts, constraints=resolved.constraints)
        playbook = self.playbook_engine.select(intent=resolved.intent, concepts=resolved.concepts)
        ir = self.compiler.compile(resolved=resolved, sub_goals=sub_goals, playbook=playbook)
        validation = self.simulator.validate(ir)
        if not validation.passed:
            raise PlanningError("; ".join(validation.errors))
        return ir


class PlanningError(RuntimeError):
    pass


class CognitiveOS:
    MAX_RETRIES = 2

    def __init__(self, system_model: dict[str, Any], skills_dir: str | Path, db_path: str | Path | None = None):
        self.planner = PlannerPipeline(system_model, skills_dir)
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.traces: list[dict[str, Any]] = []

    def ask(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ir = self.planner.plan(question, context)
        trace = {"question": question, "ir": ir.to_dict(), "success": True}
        self.traces.append(trace)
        return trace


def load_system_model(db_path: Path) -> dict[str, Any]:
    tables: dict[str, list[str]] = {
        "customers": [],
        "products": [],
        "orders": [],
        "order_items": [],
    }
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            for table in tables:
                cursor = conn.execute(f"PRAGMA table_info({table})")
                tables[table] = [row[1] for row in cursor.fetchall()]
    return {"tables": tables}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="planner-agent", description="Standalone KnowledgeChef planner agent.")
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    plan = subparsers.add_parser("plan", help="Compile a question into Knowledge IR.")
    plan.add_argument("question", nargs="+", help="Natural-language question to plan.")
    plan.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the TechShop SQLite database.")
    plan.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR, help="Path to the planner skills directory.")
    plan.add_argument("--json", action="store_true", help="Print Knowledge IR as JSON.")
    plan.set_defaults(func=_handle_plan)

    ask = subparsers.add_parser("ask", help="Alias for plan.")
    ask.add_argument("question", nargs="+", help="Natural-language question to plan.")
    ask.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the TechShop SQLite database.")
    ask.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR, help="Path to the planner skills directory.")
    ask.add_argument("--json", action="store_true", help="Print Knowledge IR as JSON.")
    ask.set_defaults(func=_handle_plan)

    doctor = subparsers.add_parser("doctor", help="Inspect the planner environment.")
    doctor.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the TechShop SQLite database.")
    doctor.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR, help="Path to the planner skills directory.")
    doctor.set_defaults(func=_handle_doctor)

    loop = subparsers.add_parser("loop", help="Run the planner loop scaffold.")
    loop.add_argument("question", nargs="+", help="Natural-language question to plan.")
    loop.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the TechShop SQLite database.")
    loop.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR, help="Path to the planner skills directory.")
    loop.add_argument("--json", action="store_true", help="Print Knowledge IR as JSON.")
    loop.set_defaults(func=_handle_plan)

    return parser


def _handle_plan(args: argparse.Namespace) -> int:
    system_model = load_system_model(args.db)
    planner = PlannerPipeline(system_model, args.skills_dir)
    question = " ".join(args.question).strip()
    if not question:
        print("error: question is required", file=sys.stderr)
        return 2

    ir = planner.plan(question)
    if args.json:
        print(json.dumps(ir.to_dict(), ensure_ascii=False, indent=2))
        return 0

    print("[Planner] Generated IR")
    print(f"- intent: {ir.intent}")
    if ir.sub_intents:
        print(f"- sub_intents: {', '.join(ir.sub_intents)}")
    print(f"- description: {ir.description}")
    print(f"- concepts: {', '.join(ir.concepts)}")
    if ir.ambiguity_resolutions:
        for item in ir.ambiguity_resolutions:
            print(f"- resolved: {item.element} -> {item.selected} ({item.method})")
    print(f"- playbook: {ir.playbook_used}")
    return 0


def _handle_doctor(args: argparse.Namespace) -> int:
    system_model = load_system_model(args.db)
    db_state = "present" if args.db.exists() else "missing"
    skills_state = "present" if args.skills_dir.exists() else "missing"
    print(f"db: {args.db} ({db_state})")
    print(f"skills: {args.skills_dir} ({skills_state})")
    print("tables:")
    for name, columns in system_model["tables"].items():
        columns_text = ", ".join(columns) if columns else "(unread)"
        print(f"- {name}: {columns_text}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
