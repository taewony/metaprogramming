# kchef/planner/compiler.py

from typing import Dict, Any, List, Optional
from copy import deepcopy

from ..schema.ir_schema import (
    KnowledgeIR, IntentType, DataStep, DocumentStep,
    Filter, FilterOperator, AggregationSpec, SortSpec, JoinSpec
)
from .playbook import Playbook


class RecipeCompiler:
    """
    Intent 분석, Concept 매칭, Playbook 결과를 종합하여 최종 Knowledge IR을 생성합니다.
    """

    def compile(self, resolved: Dict[str, Any], sub_goals: List[Dict], playbook: Playbook) -> KnowledgeIR:
        """
        Args:
            resolved: AmbiguityResolver에서 반환된 해소 결과
                     예: {"intent": IntentType.COUNT, "concepts": ["vip_customer"], "constraints": {...}}
            sub_goals: Decomposer에서 반환된 하위 목표 리스트
            playbook: 선택된 Playbook 객체

        Returns:
            KnowledgeIR: 최종 실행 계획
        """
        # 1. 기본 정보 추출
        intent = resolved.get("intent")
        if intent is None:
            raise ValueError("resolved에 'intent'가 없습니다.")

        concepts = resolved.get("concepts", [])
        constraints = resolved.get("constraints", {})

        # 2. Playbook에서 steps 템플릿을 가져와 실제 steps 생성
        # Playbook의 create_steps는 context를 받아 DataStep/DocumentStep 리스트를 반환
        context = self._build_context(resolved, sub_goals)
        steps = playbook.create_steps(context) if playbook else self._fallback_steps(intent, constraints)

        # 3. Output structure 결정
        output_structure = playbook.output_structure if playbook else {"result": "unknown"}

        # 4. Confidence 계산 (간단히: playbook confidence * 개념 매칭 수)
        confidence = playbook.confidence if playbook else 0.8
        # 개념 매칭이 많을수록 신뢰도 상승 (0.1씩 증가, 최대 1.0)
        confidence = min(1.0, confidence + 0.05 * len(concepts))

        # 5. 설명 생성
        description = self._generate_description(intent, concepts, constraints, playbook)

        # 6. 하위 의도 추출
        sub_intents = []
        if intent == IntentType.COMPOUND:
            # sub_goals에서 각각의 intent를 추출
            for sg in sub_goals:
                if "intent" in sg:
                    sub_intents.append(sg["intent"])

        # 7. 최종 IR 생성
        ir = KnowledgeIR(
            intent=intent,
            sub_intents=sub_intents if sub_intents else None,
            description=description,
            concepts=concepts,
            steps=steps,
            output_structure=output_structure,
            confidence=confidence,
            playbook_used=playbook.id if playbook else None,
            ambiguity_resolutions=resolved.get("ambiguity_resolutions")
        )

        return ir

    def _build_context(self, resolved: Dict, sub_goals: List[Dict]) -> Dict[str, Any]:
        """Playbook의 템플릿을 채우기 위한 컨텍스트를 생성합니다."""
        context = {}
        constraints = resolved.get("constraints", {})

        # constraints에서 필터 값 추출
        for key, value in constraints.items():
            context[key] = value

        # concepts에서 첫 번째 개념의 table 정보 추출 (가정: concept에 table 필드가 있음)
        concepts = resolved.get("concepts", [])
        if concepts:
            # 여기서는 간단히 첫 번째 개념을 사용
            # 실제로는 system_model에서 개념에 매핑된 테이블을 찾아야 함
            # 지금은 더미로 "customers"를 사용
            context["table"] = "customers"
            # 필터 필드와 값
            if "grade" in constraints:
                context["filter_field"] = "grade"
                context["filter_value"] = constraints["grade"]
            else:
                context["filter_field"] = "id"
                context["filter_value"] = "1"

        # 하위 목표가 있으면 첫 번째 하위 목표의 정보 사용
        if sub_goals:
            first = sub_goals[0]
            if "filters" in first:
                for k, v in first["filters"].items():
                    context[k] = v

        # 기본값
        context.setdefault("table", "customers")
        context.setdefault("limit", 10)
        context.setdefault("agg_func", "COUNT")
        context.setdefault("agg_field", "*")
        context.setdefault("order_field", "id")
        context.setdefault("time_field", "created_at")
        context.setdefault("doc_path", "documents/summary.md")

        return context

    def _fallback_steps(self, intent: IntentType, constraints: Dict) -> List[Any]:
        """Playbook이 없을 때 기본 steps를 생성합니다."""
        # 간단한 기본 DataStep 생성
        steps = []
        filters = []
        for k, v in constraints.items():
            filters.append(Filter(field=k, operator=FilterOperator.EQ, value=v))

        if intent == IntentType.COUNT:
            steps.append(DataStep(
                source="customers",
                filters=filters if filters else None,
                aggregation=AggregationSpec(function="COUNT", field="*")
            ))
        elif intent == IntentType.LIST:
            steps.append(DataStep(
                source="customers",
                filters=filters if filters else None,
                limit=100
            ))
        else:
            steps.append(DataStep(
                source="customers",
                filters=filters if filters else None
            ))
        return steps

    def _generate_description(self, intent: IntentType, concepts: List[str],
                              constraints: Dict, playbook: Optional[Playbook]) -> str:
        """사람이 읽을 수 있는 계획 설명을 생성합니다."""
        parts = []
        parts.append(f"의도: {intent.value}")
        if concepts:
            parts.append(f"관련 개념: {', '.join(concepts)}")
        if constraints:
            parts.append(f"조건: {', '.join(f'{k}={v}' for k, v in constraints.items())}")
        if playbook:
            parts.append(f"플레이북: {playbook.name} (ID: {playbook.id})")
        return " → ".join(parts)