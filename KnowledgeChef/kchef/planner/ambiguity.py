# kchef/planner/ambiguity.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from kchef.schema.ir_schema import AmbiguityResolution

@dataclass
class ResolvedQuery:
    """모호성이 해소된 질의 구조"""
    intent: str
    concepts: List[str]
    constraints: Dict[str, str]
    projections: List[str]
    ambiguity_log: List[AmbiguityResolution] = field(default_factory=list)

class AmbiguityResolver:
    """
    생략형·중의적 표현을 명시적으로 해소한다.

    해소 우선순위:
    1. AMBIGUITY.md 규칙 (기본값)
    2. 스키마 기반 추론 (유일 후보)
    3. Confidence 기반 선택 (복수 후보, 최고 > 0.8)
    4. 사용자 되묻기 (복수 후보, 최고 < 0.8)
    """

    # AMBIGUITY.md에서 로드되는 규칙
    DEFAULT_RULES = {
        # 시간 표현
        "이번 달": {"resolve_to": "current_month", "method": "default"},
        "올해":    {"resolve_to": "current_year",  "method": "default"},
        "최근":    {"resolve_to": "last_7_days",   "method": "default"},

        # 비즈니스 용어
        "매출":    {"resolve_to": "status_not_cancelled", "method": "default"},
        "팔린":    {"resolve_to": "SUM(quantity)",        "method": "default"},
        "비싼":    {"resolve_to": "price_DESC",           "method": "default"},

        # 엔터티 기본 매핑
        "거":      {"resolve_to": "Product", "method": "default"},  # "비싼 거" → 상품
    }

    def __init__(self, skills_dir: str):
        # TODO: AMBIGUITY.md 파싱하여 동적 로딩
        pass

    def resolve(self, question: str, intent, concepts, context=None) -> ResolvedQuery:
        ambiguity_log = []

        # 1. 시간 표현 해소
        constraints = {}
        for temporal_key in ["이번 달", "올해", "최근"]:
            if temporal_key in question:
                rule = self.DEFAULT_RULES[temporal_key]
                constraints["temporal"] = rule["resolve_to"]
                ambiguity_log.append(AmbiguityResolution(
                    element=temporal_key,
                    candidates=[rule["resolve_to"], "전체 기간"],
                    selected=rule["resolve_to"],
                    method="default",
                    confidence=0.95,
                    rationale=f"AMBIGUITY.md 규칙: '{temporal_key}' → {rule['resolve_to']}"
                ))

        # 2. 생략된 목적어 복원
        # TODO: "가장 비싼 거" → "가장 비싼 상품"

        # 3. 중의적 비즈니스 용어 해소
        for term, rule in self.DEFAULT_RULES.items():
            if term in question and term not in ["이번 달", "올해", "최근"]:
                ambiguity_log.append(AmbiguityResolution(
                    element=term,
                    candidates=[rule["resolve_to"], "alternative"],
                    selected=rule["resolve_to"],
                    method=rule["method"],
                    confidence=0.90,
                    rationale=f"AMBIGUITY.md 규칙 적용"
                ))

        return ResolvedQuery(
            intent=intent.primary,
            concepts=[c.name for c in concepts] if hasattr(concepts[0], 'name') else concepts,
            constraints=constraints,
            projections=[],  # 이후 Playbook에서 결정
            ambiguity_log=ambiguity_log
        )