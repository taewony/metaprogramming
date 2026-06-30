# kchef/planner/concept_matcher.py

from typing import Dict, List, Optional, Set, Tuple, Any
import re
from pathlib import Path
from collections import defaultdict


class ConceptMatcher:
    """
    OKF 번들 내 Concept 파일들을 자연어 질의와 매칭합니다.
    - 개념명, 별칭(aliases), 태그(tags) 기반 키워드 매칭
    - 향후 임베딩 기반 매칭으로 확장 가능
    """

    def __init__(self, system_model: Dict):
        """
        Args:
            system_model: load_system_model()이 반환한 OKF 번들의 개념 맵.
                         예: {
                            "concepts": {
                                "vip_customer": {
                                    "type": "BusinessRule",
                                    "title": "VIP 고객",
                                    "aliases": ["우수 고객", "상위 고객"],
                                    "tags": ["segmentation", "vip"],
                                    "path": "concepts/vip_customer.md"
                                },
                                ...
                            }
                         }
        """
        self.system_model = system_model
        self.concepts = system_model.get("concepts", {})
        self._build_index()

    def _build_index(self) -> None:
        """검색을 위한 키워드 인덱스 구축"""
        self.keyword_to_concepts: Dict[str, Set[str]] = defaultdict(set)
        self.concept_metadata: Dict[str, Dict] = {}

        for concept_id, meta in self.concepts.items():
            # 개념명, 별칭, 태그를 모두 키워드로 등록
            keywords = set()
            # title
            title = meta.get("title", concept_id)
            keywords.update(self._tokenize(title))
            # aliases (있으면)
            aliases = meta.get("aliases", [])
            for alias in aliases:
                keywords.update(self._tokenize(alias))
            # tags
            tags = meta.get("tags", [])
            for tag in tags:
                keywords.update(self._tokenize(tag))
            # concept_id 자체도 키워드로 등록 (스네이크 케이스를 분리)
            keywords.update(self._tokenize(concept_id.replace("_", " ")))

            # 인덱스에 등록
            for kw in keywords:
                if kw:  # 빈 문자열 제외
                    self.keyword_to_concepts[kw].add(concept_id)

            self.concept_metadata[concept_id] = {
                "id": concept_id,
                "title": title,
                "type": meta.get("type", "Unknown"),
                "path": meta.get("path", f"concepts/{concept_id}.md"),
                "tags": tags,
                "aliases": aliases,
                "raw": meta,
            }

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """텍스트를 소문자화하고, 구두점 제거 후 단어 분리"""
        if not text:
            return set()
        # 알파벳/숫자/한글만 남기고 공백으로 치환 (간단한 버전)
        clean = re.sub(r'[^a-zA-Z0-9가-힣\s]', ' ', text.lower())
        return set(clean.split())

    def match(self, query: str, top_k: Any = 5, *args, **kwargs) -> List[Dict]:
        """
        주어진 질의와 관련된 Concept들을 검색하여 점수와 함께 반환.

        Args:
            query: 사용자 질의 문자열
            top_k: 반환할 최대 Concept 수 (호출부 오류 대비 Any 타입으로 수용 후 방어 처리)
        """
        # [수정됨] 호출부에서 IntentResult 등 숫자가 아닌 객체를 잘못 넘길 경우에 대한 방어 로직
        if not isinstance(top_k, (int, float)):
            safe_top_k = 5
        else:
            safe_top_k = int(top_k)

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 각 Concept에 대해 키워드 중복 개수 계산
        scores = defaultdict(int)
        for token in query_tokens:
            for concept_id in self.keyword_to_concepts.get(token, []):
                scores[concept_id] += 1

        # 점수 기준 정렬
        sorted_concepts = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 상위 k개 반환 (안전하게 변환된 safe_top_k 사용)
        results = []
        for concept_id, score in sorted_concepts[:safe_top_k]:
            meta = self.concept_metadata.get(concept_id, {})
            # 점수 정규화 (최대 점수로 나누기)
            max_score = sorted_concepts[0][1] if sorted_concepts else 1
            norm_score = score / max_score if max_score > 0 else 0.0
            results.append({
                "concept_id": concept_id,
                "score": norm_score,
                "metadata": meta
            })

        return results

    def resolve_path(self, concept_id: str) -> Optional[str]:
        """Concept ID로부터 파일 경로를 반환"""
        meta = self.concept_metadata.get(concept_id)
        return meta.get("path") if meta else None

    def get_concept_by_id(self, concept_id: str) -> Optional[Dict]:
        """Concept ID로 전체 메타데이터 반환"""
        return self.concept_metadata.get(concept_id)

    def get_all_concepts(self) -> List[Dict]:
        """모든 Concept 메타데이터 리스트 반환"""
        return list(self.concept_metadata.values())

    def match_with_context(self, query: str, context_tags: List[str] = None, top_k: Any = 5, *args, **kwargs) -> List[Dict]:
        """
        컨텍스트 태그가 주어지면 해당 태그에 속하는 Concept에 가중치를 부여하여 매칭.
        """
        # [수정됨] 마찬가지로 방어 로직 추가
        if not isinstance(top_k, (int, float)):
            safe_top_k = 5
        else:
            safe_top_k = int(top_k)

        # 기본 매칭 (안전하게 변환된 값의 2배수 요청)
        base_results = self.match(query, top_k=safe_top_k * 2)

        # 태그 기반 가중치 적용
        if context_tags:
            for res in base_results:
                meta = res["metadata"]
                tags = meta.get("tags", [])
                if any(tag in context_tags for tag in tags):
                    res["score"] = min(1.0, res["score"] + 0.2)  # 가중치 부스트

        # 재정렬
        sorted_results = sorted(base_results, key=lambda x: x["score"], reverse=True)
        return sorted_results[:safe_top_k]