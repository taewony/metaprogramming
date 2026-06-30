# kchef/planner/decomposer.py

from typing import List, Dict, Optional, Tuple, Set
import re
from enum import Enum
from dataclasses import dataclass, field

from kchef.schema.ir_schema import IntentType


@dataclass
class DecomposedQuery:
    """
    분해된 질의 결과를 담는 데이터 클래스
    """
    original_question: str
    is_compound: bool
    sub_queries: List[Dict] = field(default_factory=list)
    # sub_queries 예: [
    #   {"text": "VIP 고객은 몇 명이야?", "intent": "COUNT", "filters": {"grade": "VIP"}},
    #   {"text": "VIP 고객은 누구야?", "intent": "LIST", "filters": {"grade": "VIP"}}
    # ]
    overall_intent: Optional[IntentType] = None
    ambiguity_type: Optional[str] = None

class GoalDecomposer:
    """
    복합 질문을 분해하고 각 하위 질문의 의도를 추론합니다.
    규칙 기반(정규표현식) + 간단한 키워드 분석을 사용합니다.
    (이전 QuestionDecomposer와 동일한 기능)
    """

    # 의도별 키워드 패턴
    INTENT_PATTERNS = {
        IntentType.COUNT: r"(몇\s*명|얼마나|몇\s*개|몇\s*건|count|number of|how many)",
        IntentType.LIST: r"(누구|목록|리스트|나열|보여줘|알려줘|list|show me)",
        IntentType.AGGREGATE: r"(평균|합계|총|최대|최소|가장|많이|적게|average|sum|total|max|min)",
        IntentType.TOPK: r"(상위|top|best|최고|가장\s*많은)",
        IntentType.EXISTENCE: r"(있는가?|존재|있어\?|exist)",
        IntentType.COMPARE: r"(비교|대비|vs|보다|차이)",
        IntentType.TREND: r"(추이|변화|증가|감소|추세|trend|change)",
        IntentType.SUMMARIZE: r"(요약|정리|개요|summary)",
    }

    # 복합 질문을 분리하는 접속사/구분자 패턴
    COMPOUND_SEPARATORS = [
        r"\s*,\s*",                 # 쉼표
        r"\s*이고\s*",               # 이고
        r"\s*하고\s*",               # 하고
        r"\s*와\s*",                 # 와
        r"\s*및\s*",                 # 및
        r"\s*그리고\s*",             # 그리고
        r"\s*또는\s*",               # 또는
        r"\s*,\s*그리고\s*",         # , 그리고
        r"\s*;\s*",                 # 세미콜론
        r"\s*\.\s*",                # 마침표
        r"\s*\?\s*",                # 물음표 (질문 분리)
        r"\s*또\s*",                 # 또
        r"\s*다음\s*",               # 다음
        r"\s*그 다음\s*",            # 그 다음
    ]
    COMPOUND_PATTERN = re.compile("|".join(COMPOUND_SEPARATORS))

    def __init__(self, concept_matcher=None):
        """
        Args:
            concept_matcher: 선택적 ConceptMatcher 인스턴스 (개체명 인식에 활용 가능)
        """
        self.concept_matcher = concept_matcher

    def decompose(self, question: str) -> DecomposedQuery:
        """
        질문을 분석하여 DecomposedQuery 객체를 반환합니다.

        Args:
            question: 사용자 질문 문자열

        Returns:
            DecomposedQuery: 분해 결과
        """
        question = question.strip()
        if not question:
            return DecomposedQuery(original_question=question, is_compound=False)

        # 1. 복합 질문인지 확인 및 분리
        sub_texts = self._split_compound(question)
        is_compound = len(sub_texts) > 1

        # 2. 각 하위 텍스트에 대해 의도 추론
        sub_queries = []
        for text in sub_texts:
            intent = self._detect_intent(text)
            filters = self._extract_filters(text)
            sub_queries.append({
                "text": text,
                "intent": intent,
                "filters": filters
            })

        # 3. 전체 의도 결정 (복합이면 COMPOUND, 아니면 첫 번째 의도)
        if is_compound:
            overall_intent = IntentType.COMPOUND
        else:
            overall_intent = sub_queries[0]["intent"] if sub_queries else None

        # 4. 모호성 유형 탐지 (간단한 예: 시간, 개체 참조 등)
        ambiguity_type = self._detect_ambiguity(question)

        return DecomposedQuery(
            original_question=question,
            is_compound=is_compound,
            sub_queries=sub_queries,
            overall_intent=overall_intent,
            ambiguity_type=ambiguity_type
        )

    def _split_compound(self, question: str) -> List[str]:
        """
        복합 질문을 하위 질문들로 분리합니다.
        구분자 패턴을 기준으로 나누고, 빈 문자열을 제거합니다.
        """
        parts = re.split(self.COMPOUND_PATTERN, question)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) <= 1:
            return [question]
        # 각 부분이 의미 있는 길이인지 확인
        validated = [p for p in parts if len(p) > 2]
        return validated if validated else [question]

    def _detect_intent(self, text: str) -> IntentType:
        """
        텍스트에서 의도를 탐지합니다.
        우선순위: COUNT > LIST > AGGREGATE > TOPK > COMPARE > TREND > SUMMARIZE > EXISTENCE
        """
        text_lower = text.lower()
        priority_order = [
            IntentType.COUNT,
            IntentType.LIST,
            IntentType.AGGREGATE,
            IntentType.TOPK,
            IntentType.COMPARE,
            IntentType.TREND,
            IntentType.SUMMARIZE,
            IntentType.EXISTENCE,
        ]
        for intent in priority_order:
            pattern = self.INTENT_PATTERNS.get(intent)
            if pattern and re.search(pattern, text_lower):
                return intent
        return IntentType.LIST

    def _extract_filters(self, text: str) -> Dict[str, str]:
        """
        텍스트에서 명시적인 필터 조건을 추출합니다.
        """
        filters = {}
        if re.search(r"VIP|우수|상위", text, re.IGNORECASE):
            filters["grade"] = "VIP"
        year_match = re.search(r"(20\d{2})", text)
        if year_match:
            filters["year"] = year_match.group(1)
        if re.search(r"최근\s*3\s*개월|last\s*3\s*months", text, re.IGNORECASE):
            filters["period"] = "last_3_months"
        return filters

    def _detect_ambiguity(self, question: str) -> Optional[str]:
        """
        모호성 유형을 간단히 탐지합니다.
        """
        if re.search(r"올해|작년|last\s*year|this\s*year", question, re.IGNORECASE):
            if not re.search(r"202\d", question):
                return "temporal"
        if re.search(r"그\s*회사|그\s*제품|그\s*고객|that\s+company|that\s+product", question, re.IGNORECASE):
            return "reference"
        return None

    def decompose_with_context(self, question: str, context: Dict = None) -> DecomposedQuery:
        """
        컨텍스트 정보를 활용한 분해 (현재는 동일).
        """
        return self.decompose(question)


# 하위 호환성을 위해 QuestionDecomposer 별칭 제공
QuestionDecomposer = GoalDecomposer