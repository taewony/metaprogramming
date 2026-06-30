# kchef/planner/playbook.py

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import re

from ..schema.ir_schema import KnowledgeIR, IntentType, DataStep, DocumentStep, Filter, FilterOperator


@dataclass
class Playbook:
    """
    하나의 Playbook을 정의합니다.
    Playbook은 특정 의도(Intent)와 도메인 개념에 대해 미리 정의된 실행 단계 템플릿입니다.
    """
    id: str
    name: str
    description: str
    intent: IntentType
    required_concepts: List[str] = field(default_factory=list)  # 필요 개념 타입/태그
    steps_template: List[Dict[str, Any]] = field(default_factory=list)  # IR의 steps를 생성하기 위한 템플릿
    output_structure: Dict[str, str] = field(default_factory=dict)  # 결과 구조 정의
    confidence: float = 1.0

    def create_steps(self, context: Dict[str, Any]) -> List[Any]:
        """
        컨텍스트(개념 경로, 필터 값 등)를 바탕으로 실제 DataStep/DocumentStep 객체 리스트를 생성합니다.
        """
        steps = []
        for template in self.steps_template:
            step_type = template.get("type")
            if step_type == "data":
                # 템플릿에 placeholders가 있으면 context로 치환
                source = template.get("source", "").format(**context)
                filters = []
                for f in template.get("filters", []):
                    # field도 포맷팅될 수 있도록 수정
                    field_name = f.get("field")
                    if isinstance(field_name, str) and "{" in field_name:
                        try:
                            field_name = field_name.format(**context)
                        except KeyError:
                            pass # context에 값이 없을 경우 대비

                    op = FilterOperator(f.get("operator", "="))
                    
                    value = f.get("value")
                    if isinstance(value, str) and "{" in value:
                        try:
                            value = value.format(**context)
                        except KeyError:
                            pass
                            
                    filters.append(Filter(field=field_name, operator=op, value=value))
                    
                steps.append(DataStep(
                    source=source,
                    filters=filters if filters else None,
                    join=template.get("join"),
                    group_by=template.get("group_by"),
                    order_by=template.get("order_by"),
                    limit=template.get("limit"),
                    projections=template.get("projections"),
                    aggregation=template.get("aggregation")
                ))
            elif step_type == "document":
                source = template.get("source", "").format(**context)
                steps.append(DocumentStep(
                    source=source,
                    operation=template.get("operation", "extract"),
                    query=template.get("query"),
                    extract_sections=template.get("extract_sections"),
                    output_format=template.get("output_format", "text")
                ))
            else:
                raise ValueError(f"Unknown step type: {step_type}")
        return steps


class PlaybookRegistry:
    """
    Playbook을 등록하고, 질의에 가장 적합한 Playbook을 선택합니다.
    """

    def __init__(self):
        self.playbooks: Dict[str, Playbook] = {}
        self._load_default_playbooks()

    def register(self, playbook: Playbook) -> None:
        """Playbook 등록"""
        self.playbooks[playbook.id] = playbook

    def get(self, playbook_id: str) -> Optional[Playbook]:
        """ID로 Playbook 조회"""
        return self.playbooks.get(playbook_id)

    def select(self, intent: IntentType, concepts: List[str], filters: Dict = None) -> Optional[Playbook]:
        """
        의도와 개념 목록에 기반하여 최적의 Playbook을 선택합니다.
        - 우선순위: intent 매칭 + required_concepts 매칭 수
        """
        if filters is None:
            filters = {}

        candidates = []
        for pb in self.playbooks.values():
            # 의도가 일치해야 함
            if pb.intent != intent:
                continue
            # required_concepts가 없으면 항상 매칭
            if not pb.required_concepts:
                candidates.append((pb, 0))
                continue
            # concepts 목록 중 required_concepts와 매칭되는 개수 계산
            match_count = sum(1 for req in pb.required_concepts if req in concepts)
            if match_count > 0:
                candidates.append((pb, match_count))

        if not candidates:
            return None

        # 매칭 수 기준 내림차순 정렬
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _load_default_playbooks(self):
        """기본 Playbook을 등록합니다."""
        # 1. COUNT Playbook
        self.register(Playbook(
            id="count_entity",
            name="Count Entities",
            description="주어진 조건에 맞는 개체 수를 집계합니다.",
            intent=IntentType.COUNT,
            required_concepts=[],
            steps_template=[
                {
                    "type": "data",
                    "source": "{table}",
                    "filters": [{"field": "{filter_field}", "operator": "=", "value": "{filter_value}"}],
                    "aggregation": {"function": "COUNT", "field": "*"}
                }
            ],
            output_structure={"count": "int"}
        ))

        # 2. LIST Playbook
        self.register(Playbook(
            id="list_entities",
            name="List Entities",
            description="주어진 조건에 맞는 개체 목록을 조회합니다.",
            intent=IntentType.LIST,
            required_concepts=[],
            steps_template=[
                {
                    "type": "data",
                    "source": "{table}",
                    "filters": [{"field": "{filter_field}", "operator": "=", "value": "{filter_value}"}],
                    "projections": ["*"],
                    "limit": 100
                }
            ],
            output_structure={"items": "list"}
        ))

        # 3. FILTER_AND_LIST (테스트에서 사용되는 Playbook)
        self.register(Playbook(
            id="filter_and_list",
            name="Filter and List",
            description="조건에 맞는 개체를 필터링하고 목록을 반환합니다.",
            intent=IntentType.COMPOUND,  # 복합 의도지만 필터+목록에 사용
            required_concepts=["filter", "list"],
            steps_template=[
                {
                    "type": "data",
                    "source": "{table}",
                    "filters": [{"field": "{filter_field}", "operator": "=", "value": "{filter_value}"}],
                    "projections": ["*"]
                }
            ],
            output_structure={"items": "list", "count": "int"}
        ))

        # 4. AGGREGATE Playbook
        self.register(Playbook(
            id="aggregate_entity",
            name="Aggregate Entity",
            description="개체의 특정 필드에 대해 집계(SUM, AVG 등)를 수행합니다.",
            intent=IntentType.AGGREGATE,
            required_concepts=[],
            steps_template=[
                {
                    "type": "data",
                    "source": "{table}",
                    "filters": [{"field": "{filter_field}", "operator": "=", "value": "{filter_value}"}],
                    "aggregation": {"function": "{agg_func}", "field": "{agg_field}"}
                }
            ],
            output_structure={"result": "float"}
        ))

        # 5. TOPK Playbook
        self.register(Playbook(
            id="topk_entities",
            name="Top-K Entities",
            description="주어진 기준으로 상위 K개 개체를 조회합니다.",
            intent=IntentType.TOPK,
            required_concepts=[],
            steps_template=[
                {
                    "type": "data",
                    "source": "{table}",
                    "filters": [{"field": "{filter_field}", "operator": "=", "value": "{filter_value}"}],
                    "order_by": [{"field": "{order_field}", "direction": "DESC"}],
                    "limit": "{limit}"
                }
            ],
            output_structure={"items": "list"}
        ))

        # 6. COMPARE Playbook
        self.register(Playbook(
            id="compare_entities",
            name="Compare Entities",
            description="두 그룹의 개체를 비교합니다.",
            intent=IntentType.COMPARE,
            required_concepts=[],
            steps_template=[
                {
                    "type": "data",
                    "source": "{table1}",
                    "filters": [{"field": "{filter_field}", "operator": "=", "value": "{filter_value1}"}],
                    "aggregation": {"function": "{agg_func}", "field": "{agg_field}"}
                },
                {
                    "type": "data",
                    "source": "{table2}",
                    "filters": [{"field": "{filter_field}", "operator": "=", "value": "{filter_value2}"}],
                    "aggregation": {"function": "{agg_func}", "field": "{agg_field}"}
                }
            ],
            output_structure={"comparison": "dict"}
        ))

        # 7. SUMMARIZE Playbook (문서 요약)
        self.register(Playbook(
            id="summarize_document",
            name="Summarize Document",
            description="문서를 요약합니다.",
            intent=IntentType.SUMMARIZE,
            required_concepts=["document"],
            steps_template=[
                {
                    "type": "document",
                    "source": "{doc_path}",
                    "operation": "summarize",
                    "output_format": "text"
                }
            ],
            output_structure={"summary": "string"}
        ))

        # 8. TREND Playbook (간단 추세)
        self.register(Playbook(
            id="trend_over_time",
            name="Trend Over Time",
            description="시간에 따른 추세를 조회합니다.",
            intent=IntentType.TREND,
            required_concepts=[],
            steps_template=[
                {
                    "type": "data",
                    "source": "{table}",
                    "group_by": ["{time_field}"],
                    "aggregation": {"function": "{agg_func}", "field": "{agg_field}"},
                    "order_by": [{"field": "{time_field}", "direction": "ASC"}]
                }
            ],
            output_structure={"trend": "list"}
        ))

    def select_with_context(self, intent: IntentType, concepts: List[str], filters: Dict = None,
                            ambiguity_resolutions: List = None) -> Optional[Playbook]:
        """
        컨텍스트(모호성 해소 결과 등)를 고려하여 Playbook을 선택합니다.
        현재는 기본 select와 동일합니다.
        """
        return self.select(intent, concepts, filters)

class PlaybookEngine:
    """
    Playbook 선택 및 대안 검색을 담당하는 엔진.
    """
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self.registry = PlaybookRegistry()
        # skills_dir에서 추가 Playbook을 로드할 수도 있음 (향후 확장)

    def select(self, intent: IntentType, concepts: List[str], filters: Dict = None) -> Optional[Playbook]:
        """주어진 의도와 개념에 가장 적합한 Playbook을 반환합니다."""
        return self.registry.select(intent, concepts, filters)

    def select_alternative(self, intent: IntentType, concepts: List[str],
                           exclude: List[str] = None, filters: Dict = None) -> Optional[Playbook]:
        """
        제외 목록을 고려하여 두 번째로 적합한 Playbook을 반환합니다.
        """
        if exclude is None:
            exclude = []
        candidates = []
        for pb in self.registry.playbooks.values():
            if pb.id in exclude:
                continue
            if pb.intent != intent:
                continue
            # 매칭 점수 계산 (registry.select와 동일한 로직)
            if not pb.required_concepts:
                score = 0
            else:
                score = sum(1 for req in pb.required_concepts if req in concepts)
            candidates.append((pb, score))
        if not candidates:
            return None
        # 점수 기준 내림차순 정렬
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0] if candidates else None
        
# 하위 호환성을 위한 별칭
PlaybookSelector = PlaybookRegistry