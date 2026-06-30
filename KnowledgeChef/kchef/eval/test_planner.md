# `test_planner.py` 분석: 의존성 및 실행 사전 준비

## 1. 스크립트 이해

이 스크립트는 **Cognitive Compiler의 Query Planner**가 생성하는 **IR(Intermediate Representation)**의 품질을 검증하는 **TDD 테스트 스위트**입니다.

### 1.1 테스트 구조

| 구성 요소 | 설명 |
|-----------|------|
| **벤치마크 로딩** | `eval/benchmark/q*.yaml` 파일들을 읽어 테스트 케이스로 변환 |
| **`test_planner_ir_quality`** | 각 질의에 대해 Planner가 생성한 IR이 기대 IR과 일치하는지 검증 |
| **`test_ambiguity_resolution`** | 모호한 질의(ambiguity_type 있는 케이스)에 대한 해소 능력 검증 |
| **PlannerPipeline** | 시스템 모델과 SKILL.md를 기반으로 Plan(IR)을 생성하는 핵심 클래스 |
| **PlanningScorer** | 생성된 IR의 품질을 정량적으로 평가 (Intent, Source, Schema, F1) |

### 1.2 평가 지표

| 지표 | 설명 | 통과 기준 |
|------|------|-----------|
| `schema_valid` | IR이 정의된 스키마를 준수하는가 | True |
| `intent_correct` | 의도(Intent)가 일치하는가 | True |
| `source_correct` | 데이터 소스(Source)가 일치하는가 | True |
| `overall_f1` | 종합 정밀도/재현율 | ≥ 0.70 |
| `ambiguity_resolution_rate` | 모호성 해소율 | ≥ 0.80 |

---

## 2. 필요 의존성 분석

### 2.1 외부 라이브러리 (Python Packages)

```bash
pip install pytest pyyaml
```

| 패키지 | 용도 | 대체 가능성 |
|--------|------|-------------|
| `pytest` | 테스트 프레임워크 | `unittest`로 대체 가능하나 구조 변경 필요 |
| `pyyaml` | YAML 벤치마크 파일 파싱 | `json`으로 대체 가능 (벤치마크 포맷 변경 필요) |

### 2.2 프로젝트 내부 모듈 (Import 의존성)

```python
from planner.pipeline import PlannerPipeline   # ⚠️ 핵심 구현 필요
from eval.scorer import PlanningScorer         # ⚠️ 핵심 구현 필요
```

**이 모듈들은 현재 존재하지 않으므로 구현이 필수적입니다.**

---

## 3. 사전 준비 사항 (파일/디렉토리 구조)

### 3.1 필수 디렉토리 구조

```
project-root/
├── planner/
│   └── pipeline.py          # PlannerPipeline 클래스
├── eval/
│   ├── scorer.py            # PlanningScorer 클래스
│   └── benchmark/           # 테스트 데이터셋
│       ├── q001.yaml
│       ├── q002.yaml
│       └── ...
├── skills/                  # SKILL.md 파일들 (Planner가 참조)
│   ├── kdqe/
│   │   └── SKILL.md
│   └── ...
└── tests/
    └── test_planner.py      # 현재 파일
```

### 3.2 벤치마크 파일 포맷 (q001.yaml 예시)

```yaml
id: Q001
question: "VIP 고객은 몇 명이고, 누구야?"
expected_ir:
  goal: LIST_AND_COUNT
  intent: customer_query
  sources:
    - "data/customers.csv"
    - "concepts/vip_customer.md"
  constraints:
    filter: "grade = 'VIP'"
  aggregation: "count"
ambiguity_type: null  # 또는 "temporal", "semantic" 등
```

---

## 4. 핵심 컴포넌트 구현 가이드

### 4.1 PlannerPipeline 구현체

```python
# planner/pipeline.py

from typing import Dict, Any
import yaml
import glob
from pathlib import Path

class PlannerPipeline:
    """OKF 기반 Query Planner - 자연어 → IR 변환"""
    
    def __init__(self, system_model: Dict, skills_path: str):
        self.system_model = system_model  # OKF 번들의 스키마/Concept 맵
        self.skills_path = Path(skills_path)
        self.skills = self._load_skills()
    
    def _load_skills(self) -> Dict:
        """skills/ 디렉토리의 모든 SKILL.md 로드"""
        skills = {}
        for skill_file in self.skills_path.rglob("SKILL.md"):
            content = skill_file.read_text(encoding='utf-8')
            # SKILL.md 파싱 로직 (YAML frontmatter + 본문)
            skills[skill_file.parent.name] = content
        return skills
    
    def plan(self, question: str) -> 'IR':
        """
        자연어 질의 → IR 생성
        - Intent 분석
        - Symbol Resolution (index.md 탐색)
        - 실행 계획 수립
        """
        # 1. Intent 분석 (간단한 규칙 기반)
        intent = self._detect_intent(question)
        
        # 2. 관련 Concept 검색 (OKF Resolver)
        concepts = self._resolve_concepts(question)
        
        # 3. IR 생성
        ir = IR(
            goal=intent,
            sources=[c["path"] for c in concepts],
            constraints=self._extract_constraints(question),
            aggregation=self._detect_aggregation(question)
        )
        return ir
    
    def _detect_intent(self, question: str) -> str:
        """의도 탐지 (규칙 기반 또는 LLM)"""
        if "몇 명" in question or "count" in question.lower():
            return "COUNT"
        if "누구" in question or "list" in question.lower():
            return "LIST"
        if "평균" in question or "average" in question.lower():
            return "AVG"
        return "UNKNOWN"
    
    def _resolve_concepts(self, question: str) -> list:
        """OKF 번들에서 관련 Concept 검색"""
        # 실제 구현: index.md 탐색 + 키워드 매칭
        return [{"path": "concepts/vip_customer.md"}]
    
    def _extract_constraints(self, question: str) -> dict:
        """조건/필터 추출"""
        constraints = {}
        if "VIP" in question:
            constraints["filter"] = "grade = 'VIP'"
        return constraints
    
    def _detect_aggregation(self, question: str) -> str:
        """집계 함수 탐지"""
        if "합계" in question or "sum" in question.lower():
            return "sum"
        if "평균" in question or "average" in question.lower():
            return "avg"
        return None


class IR:
    """Intermediate Representation"""
    def __init__(self, goal: str, sources: list, constraints: dict, aggregation: str = None):
        self.goal = goal
        self.sources = sources
        self.constraints = constraints
        self.aggregation = aggregation
    
    def dict(self) -> dict:
        return {
            "goal": self.goal,
            "sources": self.sources,
            "constraints": self.constraints,
            "aggregation": self.aggregation
        }
```

### 4.2 PlanningScorer 구현체

```python
# eval/scorer.py

from typing import Dict, Any

class PlanningScorer:
    """IR 품질 평가기"""
    
    def __init__(self):
        self.required_fields = ["goal", "sources", "constraints"]
    
    def score(self, actual: Dict, expected: Dict) -> 'Score':
        """
        실제 IR과 기대 IR 비교
        - Schema Valid: 필수 필드 존재 여부
        - Intent Correct: goal 일치 여부
        - Source Correct: sources 포함 여부
        - Overall F1: Precision/Recall 기반 종합 점수
        """
        # 1. Schema Valid
        schema_valid = all(field in actual for field in self.required_fields)
        
        # 2. Intent Correct
        intent_correct = actual.get("goal") == expected.get("goal")
        
        # 3. Source Correct (예: expected의 모든 source가 actual에 포함)
        expected_sources = set(expected.get("sources", []))
        actual_sources = set(actual.get("sources", []))
        source_correct = expected_sources.issubset(actual_sources)
        
        # 4. Overall F1 (Precision/Recall)
        precision = len(actual_sources & expected_sources) / len(actual_sources) if actual_sources else 0
        recall = len(actual_sources & expected_sources) / len(expected_sources) if expected_sources else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # 5. Ambiguity Resolution (모호성 해소율)
        ambiguity_resolution_rate = 1.0 if intent_correct and source_correct else 0.0
        
        return Score(
            schema_valid=schema_valid,
            intent_correct=intent_correct,
            source_correct=source_correct,
            overall_f1=f1,
            ambiguity_resolution_rate=ambiguity_resolution_rate
        )


class Score:
    def __init__(self, schema_valid: bool, intent_correct: bool, source_correct: bool,
                 overall_f1: float, ambiguity_resolution_rate: float):
        self.schema_valid = schema_valid
        self.intent_correct = intent_correct
        self.source_correct = source_correct
        self.overall_f1 = overall_f1
        self.ambiguity_resolution_rate = ambiguity_resolution_rate
```

### 4.3 `load_system_model()` 함수 구현

```python
# planner/pipeline.py 에 추가

def load_system_model() -> Dict:
    """
    OKF 번들에서 시스템 모델(Schema + Concept 맵) 로드
    - index.md 파싱
    - concepts/*.md 메타데이터 수집
    - data/*.csv 스키마 추출
    """
    bundle_path = Path("okf_bundle")  # 또는 환경변수로 지정
    model = {
        "concepts": {},
        "schemas": {},
        "index": {}
    }
    
    # index.md 파싱
    index_file = bundle_path / "index.md"
    if index_file.exists():
        content = index_file.read_text(encoding='utf-8')
        # 마크다운 링크 추출
        import re
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for name, path in links:
            model["index"][name] = path
    
    # concepts/*.md 파싱
    for concept_file in (bundle_path / "concepts").glob("*.md"):
        content = concept_file.read_text(encoding='utf-8')
        # YAML frontmatter 추출
        if content.startswith("---"):
            _, fm, _ = content.split("---", 2)
            import yaml
            meta = yaml.safe_load(fm)
            model["concepts"][concept_file.stem] = meta
    
    return model
```

---

## 5. 실행 방법

### 5.1 사전 준비 체크리스트

- [ ] `planner/pipeline.py` 구현 완료
- [ ] `eval/scorer.py` 구현 완료
- [ ] `eval/benchmark/q*.yaml` 벤치마크 파일 준비 (최소 1개)
- [ ] `skills/kdqe/SKILL.md` 준비
- [ ] `okf_bundle/` OKF 번들 준비 (index.md, concepts/, data/)
- [ ] 필요한 Python 패키지 설치: `pip install pytest pyyaml`

### 5.2 테스트 실행

```bash
# 프로젝트 루트에서
pytest tests/test_planner.py -v
```

### 5.3 특정 테스트만 실행

```bash
# Q001 케이스만 실행
pytest tests/test_planner.py -k "Q001" -v

# ambiguity 테스트만 실행
pytest tests/test_planner.py -k "ambiguity" -v
```

---

## 6. 확장 및 개선 제안

| 영역 | 개선 방안 |
|------|-----------|
| **Intent Detection** | 규칙 기반 → LLM 기반으로 전환 (Gemini/Qwen) |
| **Symbol Resolution** | 단순 키워드 매칭 → index.md 트리 탐색 + 메타데이터 매칭 |
| **Scorer** | F1 외에 Hallucination Rate, Citation Recall 추가 |
| **Benchmark** | YAML → JSONL로 전환하여 대량 테스트 쿼리 관리 |

---

## 7. 최종 결론

`test_planner.py`는 **OKF 기반 Cognitive Compiler의 Planner IR 품질을 검증하는 핵심 TDD 프레임워크**입니다.

실행을 위해 필요한 것은:
1. **PlannerPipeline** 구현 (자연어→IR 변환)
2. **PlanningScorer** 구현 (IR 품질 평가)
3. **벤치마크 데이터셋** (eval/benchmark/q*.yaml)
4. **OKF 번들** (index.md + concepts/ + data/)
5. **Python 패키지**: pytest, pyyaml

이 테스트 스위트가 통과하면 Cognitive Compiler의 Planner는 **LLM/Agent Stack에 독립적인 안정적인 IR 생성 능력**을 갖추게 됩니다. 이는 KnowledgeChef 시스템의 가장 중요한 평가 기준선이 될 것입니다.