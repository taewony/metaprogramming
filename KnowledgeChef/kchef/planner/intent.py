# kchef/planner/intent.py
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class IntentResult:
    primary: str              # 주 Intent (COUNT, LIST, AGGREGATE, ...)
    sub_intents: List[str]    # 복합 의도의 하위 Intent
    confidence: float
    evidence: List[str]       # 판단 근거 키워드

class IntentRecognizer:
    """규칙 기반 + LLM fallback Intent 인식기"""

    # PATTERN.md에서 로드되는 규칙
    PATTERNS = {
        "COUNT":     [r"몇\s*명", r"몇\s*개", r"수는?", r"총\s*수"],
        "LIST":      [r"누구", r"알려줘", r"목록", r"보여줘", r"어떤"],
        "AGGREGATE": [r"총\s*금액", r"평균", r"합계", r"합산", r"얼마"],
        "TOPK":      [r"가장", r"최고", r"최다", r"제일", r"1위"],
        "EXISTENCE": [r"있나", r"있어", r"없는", r"없나"],
        "COMPARE":   [r"대비", r"비교", r"차이"],
        "TREND":     [r"추세", r"증가", r"감소", r"변화"],
        "SUMMARIZE": [r"요약", r"성과", r"정리해"],
    }

    def __init__(self, skills_dir: str):
        # TODO: PATTERN.md 파싱하여 동적 로딩
        pass

    def recognize(self, question: str) -> IntentResult:
        matched = {}
        for intent, patterns in self.PATTERNS.items():
            for pat in patterns:
                if re.search(pat, question):
                    matched.setdefault(intent, []).append(pat)

        if len(matched) == 0:
            # LLM fallback
            return self._llm_fallback(question)
        elif len(matched) == 1:
            intent = list(matched.keys())[0]
            return IntentResult(
                primary=intent,
                sub_intents=[],
                confidence=0.95,
                evidence=matched[intent]
            )
        else:
            # 복합 의도
            intents = list(matched.keys())
            return IntentResult(
                primary="COMPOUND",
                sub_intents=intents,
                confidence=0.90,
                evidence=[v for vs in matched.values() for v in vs]
            )

    def _llm_fallback(self, question: str) -> IntentResult:
        # LLM을 활용한 fallback 로직
        raise NotImplementedError("LLM fallback 미구현")