# ir_schema.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Literal
from enum import Enum

class IntentType(str, Enum):
    COUNT = "COUNT"
    LIST = "LIST"
    AGGREGATE = "AGGREGATE"
    TOPK = "TOPK"
    EXISTENCE = "EXISTENCE"
    COMPARE = "COMPARE"
    TREND = "TREND"
    SUMMARIZE = "SUMMARIZE"
    COMPOUND = "COMPOUND"

class FilterOperator(str, Enum):
    EQ = "="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    IN = "IN"
    LIKE = "LIKE"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"

class Filter(BaseModel):
    field: str
    operator: FilterOperator
    value: Union[str, int, float, List[str], None] = None

class JoinSpec(BaseModel):
    with_resource: str
    on: str                                  # e.g. "customers.id=orders.customer_id"
    type: Literal["INNER", "LEFT", "RIGHT"] = "INNER"

class SortSpec(BaseModel):
    field: str
    direction: Literal["ASC", "DESC"] = "ASC"

class AggregationSpec(BaseModel):
    function: Literal["COUNT", "SUM", "AVG", "MIN", "MAX", "COUNT_DISTINCT"]
    field: str

class DataStep(BaseModel):
    type: Literal["data"] = "data"
    source: str                              # 테이블 또는 파일 경로
    filters: Optional[List[Filter]] = None
    join: Optional[JoinSpec] = None
    group_by: Optional[List[str]] = None
    order_by: Optional[List[SortSpec]] = None
    limit: Optional[int] = None
    projections: Optional[List[str]] = None
    aggregation: Optional[AggregationSpec] = None

class DocumentStep(BaseModel):
    type: Literal["document"] = "document"
    source: str                              # 문서 경로
    operation: Literal["extract", "summarize", "find"] = "extract"
    query: Optional[str] = None              # 문서 내 검색/요약 질의
    extract_sections: Optional[List[str]] = None
    output_format: Literal["text", "bullet_points", "table"] = "text"

class AmbiguityResolution(BaseModel):
    """모호성 해소 과정의 기록"""
    element: str                             # 모호했던 요소
    candidates: List[str]                    # 후보 해석들
    selected: str                            # 선택된 해석
    method: Literal["default", "schema_driven", "confidence", "clarification"]
    confidence: float                        # 해소 신뢰도 (0.0 ~ 1.0)
    rationale: str                           # 선택 이유

class KnowledgeIR(BaseModel):
    """Planner가 생성하는 Knowledge Intermediate Representation"""
    intent: IntentType
    sub_intents: Optional[List[IntentType]] = None    # COMPOUND인 경우
    description: str                                   # 사람이 읽을 수 있는 계획 설명
    concepts: List[str]                                # 관련 도메인 Concepts
    steps: List[Union[DataStep, DocumentStep]]         # 실행 단계
    output_structure: Dict[str, str]                   # 결과 구조
    ambiguity_resolutions: Optional[List[AmbiguityResolution]] = None
    confidence: float = Field(ge=0.0, le=1.0)          # 전체 계획 신뢰도
    playbook_used: Optional[str] = None                # 사용된 Playbook ID