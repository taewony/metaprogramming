```
우리는 '자연어 기반 데이터 조회/응답' 서비스를 만들기 위해 OKF 기반의 지식베이스를 구축하기로 했고,
먼저 상용/범용 Coding Agent 및 agentic-stack과 같은 오픈소스 repo을 이용해 구현해 나가다가,
어느 시점에 전용/local Agent로 전환해 다음을 개발하려고 해.
OKF 기반 "Cognitive Compiler" 에서 "Cognitive Knowledge Operating System"까지.

이러 개발 착수 전에 정밀한 TDD 및 평가체계를 설계해 두고 싶어.
LLM 및 agent stack을 바꾸거나 교체해도 TDD 및 평가체계는 그대로 유지 가능해야 해.
전문가인 당신이 이 작업을 신중하게 진행해줘. project 성패가 달려 있다고 생각해.
```
이 평가 설계 문서는 단순한 테스트 목록이 아닙니다.  
LLM·Agent Stack이 바뀌어도 절대 무너지지 않을 **"OKF Cognitive Compiler/CKOS의 정밀한 검증 계약서"**입니다.  
이 평가체계가 곧 프로젝트의 명세(Spec)이며, 품질의 유일한 기준선입니다.

---

# 'OKF 기반 Cognitive Knowledge Operating System'을 위한 TDD 및 평가 체계 설계

**문서 상태**: DRAFT v1.0  
**대상 시스템**: OKF Bundle, Cognitive Compiler, Knowledge VM, KnowledgeChef(CKOS)  
**원칙**: 평가는 LLM/AI 스택에 종속되지 않으며, **오직 입력과 출력의 규약(Contract)만 검증**한다.

---

## 0. 왜 평가가 먼저인가 – "계약 우선 설계" (Contract-First)

LLM Agent의 최대 함정은 **비결정성**입니다.  
동일한 질문에도 내부 추론 경로가 달라지기 때문에, "이번에 잘 됐다"라는 느낌으로는 제품을 만들 수 없습니다.  
우리는 Agent를 **결정론적 소프트웨어처럼 다루는 법**을 확립해야 합니다. 그 방법이 아래 3가지입니다.

1.  **계약(Contract)의 명문화**: 평가 지표를 먼저 정의하면, 그 지표를 통과하는 것이 곧 시스템이 해야 할 일이 됩니다. (Specification by Metrics)
2.  **인터페이스 검증 (Black-box)**: Agent 내부의 Prompt, Tool, LLM 모델 종류를 모른 채, "입력(Question) → 출력(Answer, Recipe, Traces)" 만으로 평가합니다. 스택 교체 시 이 평가는 그대로 재사용됩니다.
3.  **결정적 구성 요소의 분리**: System Under Test (SUT)에서 결정적인 부분(파일 I/O, CSV 병합, 링크 계산)은 100% 단위 테스트하고, 비결정적인 부분(자연어 요약, Recipe 생성)은 통계적 평가로 접근합니다.

---

## 1. 평가 프레임워크 핵심 원칙

| 원칙 | 설명 | 위반 시 리스크 |
| :--- | :--- | :--- |
| **P1. Stack Independence** | 테스트 코드는 `gemini-2.5-pro`, `gpt-4o`, `ollama/llama3` 등 **특정 모델을 직접 호출하지 않는다.** 대신 SUT의 API 엔드포인트(`/ask`, `/merge`)를 호출하거나 Agent Runner 인터페이스를 사용한다. | 모델 변경 시 모든 테스트 폐기 |
| **P2. Contractual Precision** | "학생 수를 반환한다"가 아니라 `response.summary.total_students == 42`와 같이 **구조화된 출력을 검증**한다. 답변은 Markdown이 아닌 JSON, YAML, 또는 Pydantic Model로 받는다. | 자유 형식 답변은 파싱 불가 |
| **P3. Data Provenance (인용)** | Agent의 답변은 OKF 내 원본 데이터(CSV 행, index.md 섹션)를 가리키는 **인용(Citation)**을 포함해야 한다. 평가 시 인용의 정확성을 검증한다. | 환각을 감지하지 못함 |
| **P4. Hierarchical Failure Analysis** | `"보고서 생성 실패"`가 아니라 `"IR Generation 단계에서 semester_id 필터 누락"`처럼 **Recipe 중간 표현(IR) 단계별 실패 모드를 구분**한다. | 디버깅 불가 |
| **P5. Reproducible Test Sets** | 모든 질문은 Ground Truth가 포함된 **불변 데이터셋**에서 나온다. 랜덤하게 생성하지 않는다. | 추적 불가능한 오류 |

---

## 2. Cognitive Compiler 평가 체계 (질의/응답)

**대상**: 사용자 질문 → Cognitive Compiler (Recipe 생성) → Knowledge VM (실행) → 답변  

### 2.1 테스트 데이터셋 설계

파일: `tests/datasets/okf_queries.jsonl`
```json
{
  "query_id": "Q001",
  "question": "2026년 1학기 캡스톤 프로젝트의 총 참가 학생 수는?",
  "ground_truth": {
    "expected_answer": {
      "total_students": 42,
      "projects_count": 5
    },
    "expected_ir": {
      "goal": "COUNT_STUDENTS",
      "constraints": {"semester_id": "2026-1", "project_type": "capstone"},
      "traversal": ["semesters/2026-1/index.md", "projects_capstone.csv", "project_participation.csv"],
      "aggregation": "count(distinct student_id)"
    },
    "citation_sources": [
      "data/2026-1/project_participation.csv",
      "data/2026-1/projects_capstone.csv"
    ]
  }
}
```

**데이터셋 커버리지 설계**:
- **단순 집계 (20%)**: 학생 수, 프로젝트 수, 예산 합계 등
- **필터/검색 (30%)**: 특정 학과, 특정 날짜 범위, 특정 상태(진행 중) 등
- **문서 요약 (20%)**: "프로젝트 X의 최종 보고서 요약"
- **멀티 홉 (20%)**: "AI 경진대회 참가 학생들의 평균 학점" (참여 테이블 + 학생 정보 + 성적 테이블 조인)
- **경계/부정 질문 (10%)**: "2025년 1학기에는 프로젝트가 있었나요?" (없는 데이터 질의)

### 2.2 평가 지표 (Metrics)

이 지표는 `pytest` 플러그인 또는 평가 스크립트로 자동 측정됩니다.

#### A. 답변 정확도 (Answer Accuracy) – *핵심 지표*
- **정의**: 구조화된 답변(JSON) 내의 각 필드가 Ground Truth와 일치하는 비율.
- **측정**: 필드별 `assert response_json['total_students'] == gt['total_students']`
- **목표**: 98% 이상

#### B. Recipe/IR 정확도 (Plan Accuracy)
- **정의**: Compiler가 생성한 IR이 Expected IR과 일치하는 정도.
- **측정**:
  - `goal`, `constraints`는 정확히 일치해야 함.
  - `traversal`은 **필수 경로 포함 여부** (순서 무관)로 측정. (Precision/Recall)
- **목표**: Precision 95%, Recall 100%

#### C. 환각률 (Hallucination Rate)
- **정의**: 답변에 OKF 번들 외부의 정보가 포함된 비율. (Answer / Citation 없음)
- **탐지**: 답변 텍스트를 분해하여 각 문장의 출처가 인용으로 OKF 내에 존재하는지 LLM Critic이 판별. (Critic은 평가 전용 소형 모델로, Ground Truth 인용 목록과 비교)
- **목표**: 0%

#### D. 탐색 효율성 (Traversal Efficiency)
- **정의**: 정답을 찾기 위해 Agent가 열어본 총 index.md 및 데이터 파일 수.
- **측정**: 실행 트레이스 분석.
- **목표**: 계층적 index.md로 인해 RAG 방식 대비 파일 I/O 50% 감소.

#### E. 인용 정밀도/재현율 (Citation F1)
- **정의**: Agent가 제공한 출처가 실제 정답 도출에 사용된 올바른 데이터인지.
- **정밀도**: Agent가 인용한 출처 중 실제 정답과 관련된 비율.
- **재현율**: 실제 정답에 필요한 모든 출처를 Agent가 인용했는지.

### 2.3 TDD 사이클

1.  **RED**: `tests/test_compiler.py::test_simple_count` 작성 → 실행 → 실패.
2.  **GREEN**: **OKF 번들**에 필요한 CSV와 index.md를 수동 생성. SUT(컴파일러)의 Prompt/Recipe를 수정하지 않음. **순수하게 데이터만 보강**하여 테스트가 통과하도록 함. (데이터가 명세를 만족시킴)
3.  **REFACTOR**: 중복되는 OKF 구조를 정리하고, 더 간결한 index.md 포맷으로 변경.
4.  **확장**: Recipe 로직이 필요하면, `expected_ir`를 수정하여 새로운 RED 테스트를 만든 후, SUT의 Planner 모듈을 수정하여 GREEN으로.

---

## 3. CKOS (KnowledgeChef) 평가 체계

**대상**: Ingredient Builder, Snowball Merger, Deduplicator, Link Manager

### 3.1 정밀 단위 테스트 (결정적)
CKOS의 핵심 로직은 순수 함수로 분리하여 100% 단위 테스트합니다.

#### A. `StructureHarmonizer`
- **테스트**: `merge_concepts(concept_a: str, concept_b: str) -> str`
  - 입력: 두 개의 concept markdown 파일.
  - 검증: 합쳐진 markdown에 두 파일의 모든 필드와 관계가 포함되었는지. (리스트 비교)
- **테스트**: `merge_directories(dir_a, dir_b) -> OKFStructure`
  - 입력: 두 Ingredient의 디렉터리 트리.
  - 검증: 충돌 해결 정책(동명 파일 시 내용 합치기/스킵)에 따라 올바른 파일 개수와 경로를 가졌는지.

#### B. `Deduplicator`
- **테스트**: `find_duplicate_concepts(concepts: List[str]) -> List[Tuple[str, str, float]]`
  - 50개의 concept에 대해 3쌍의 유사도를 0.85, 0.60, 0.30으로 미리 설정하고, 임계값 0.8 → 1쌍 반환하는지 검증.
- **테스트**: `remove_duplicate_rows(csv_path_a, csv_path_b, key_column) -> int`
  - Mock CSV 파일 제공, 중복 행 수 반환 검증.

#### C. `LinkIntegrityChecker`
- **테스트**: `find_broken_links(root_dir: str) -> List[BrokenLink]`
  - 깨진 링크 3개가 있는 mock OKF 번들을 만들고, 정확히 3개를 찾아내고, 각각의 `suggest_fix`가 올바른 새 경로를 반환하는지 검증.

### 3.2 통합 시나리오 테스트 (Snowball Merge)
**시나리오 S1: 2개의 Ingredient를 병합하여 1개의 Snowball 만들기**

1.  **Initial State**: `tests/fixtures/ingredient_1` (컴공과), `ingredient_2` (전자과). 각각 projects.csv, index.md 보유.
2.  **Action**: `knowledgechef merge --ingredients ing1, ing2 --output snowball_1`
3.  **검증 (Assertions)**:
    - **디렉터리 구조**: `snowball_1/concepts/project.md`가 존재해야 함.
    - **데이터 무결성**: `snowball_1/data/projects.csv`의 행 수 == `ing1 행 수 + ing2 행 수`.
    - **메타데이터**: `snowball_1/index.md`에 "Last merged: ...", "Source ingredients: ..." 정보가 자동 생성되었는지.
    - **중복 제거**: 만약 두 Ingredient에 동일한 학생이 있다면, `project_participation.csv`에 중복 없이 1번만 존재.
    - **링크 무결성**: `snowball_1` 내부에서 `grep`으로 깨진 링크 개수가 0.

### 3.3 지식베이스 품질 지표 (통합 완료 후)
- **Concept Coverage**: 전체 번들에서 orphan 리소스(어떤 concept에도 속하지 않은 데이터 파일)가 없는지.
- **Index Freshness**: 모든 디렉터리에 index.md가 존재하는지. (스크립트 검증)
- **Symbol Resolution Time**: 특정 개념(예: "Student")을 찾는 데 걸리는 평균 index.md 탐색 깊이.

---

## 4. 스택 독립적 테스트 인프라 구축 (Python)

### 4.1 디렉터리 구조
```
project-root/
├── okf_bundle/               # 개발용 OKF 번들 (실제 데이터)
├── src/                      # Cognitive Compiler, CKOS 코드
│   ├── compiler/
│   └── ckos/
├── tests/
│   ├── fixtures/             # 불변 테스트 데이터
│   │   ├── ingredients/      # 작은 OKF 조각들
│   │   ├── queries.jsonl     # 질문-정답 데이터셋
│   │   └── golden_okf/       # 정답 OKF 구조
│   ├── contracts/            # Pydantic 모델 (답변, IR, 인용 형식 정의)
│   ├── unit/                 # 결정적 함수 단위 테스트
│   ├── integration/          # 통합 테스트 (Compiler + VM, Merger)
│   └── evaluation/           # 비결정적 평가 스크립트 (LLM Critic 사용)
├── ci/
│   └── run_eval.sh           # CI 파이프라인 스크립트
└── Makefile
```

### 4.2 계약(Contract) 정의 – Pydantic 스키마
이 스키마가 모든 Agent의 출력을 규율합니다. 스키마만 통과하면 어떤 LLM을 쓰든 무방합니다.

```python
# tests/contracts/compiler_output.py
from pydantic import BaseModel, Field
from typing import List, Optional

class KnowledgeIR(BaseModel):
    goal: str = Field(..., description="e.g., 'COUNT', 'LIST', 'SUMMARIZE'")
    constraints: dict = Field(default_factory=dict)
    traversal: List[str] = Field(..., description="Ordered list of index.md/data paths")
    aggregation: Optional[str] = None

class AnswerOutput(BaseModel):
    result: dict = Field(..., description="Structured answer data")
    summary: str = Field(..., description="Natural language summary")
    citations: List[str] = Field(..., description="List of OKF paths referenced")
    ir: KnowledgeIR = Field(..., description="The IR that generated this answer")
```

### 4.3 추상화된 Agent Runner
테스트는 이 인터페이스를 통해서만 SUT를 호출합니다. 내부 LLM은 완전히 감춰집니다.

```python
# tests/runner.py
from abc import ABC, abstractmethod
class CognitiveCompilerRunner(ABC):
    @abstractmethod
    def ask(self, question: str) -> AnswerOutput:
        """SUT에 질문하고 파싱된 구조체를 반환해야 함."""
        pass

# 프로덕션 구현체 (Gemini 사용)
class ProductionCompilerRunner(CognitiveCompilerRunner):
    def ask(self, question: str) -> AnswerOutput:
        raw = self.gemini_agent.run(question)
        return AnswerOutput.parse_raw(raw)

# 로컬 테스트용 모의 구현체
class MockCompilerRunner(CognitiveCompilerRunner):
    def ask(self, question: str) -> AnswerOutput:
        # 미리 준비된 fixture 반환
        ...
```

### 4.4 평가 스크립트 예시

```python
# tests/evaluation/test_query_accuracy.py
import json
from tests.runner import CognitiveCompilerRunner

def test_student_count_accuracy(runner: CognitiveCompilerRunner):
    """계약 기반 평가: Q001"""
    with open("tests/fixtures/queries.jsonl") as f:
        queries = [json.loads(line) for line in f]
    q = queries[0]  # Q001
    output = runner.ask(q['question'])

    # 1. 답변 정확도 (계약 검증)
    assert output.result['total_students'] == q['ground_truth']['expected_answer']['total_students']

    # 2. IR 정확도
    assert output.ir.goal == q['ground_truth']['expected_ir']['goal']

    # 3. 인용 검증
    for src in q['ground_truth']['citation_sources']:
        assert any(src in cit for cit in output.citations), f"Missing citation: {src}"

    # 4. 환각 체크 (LLM Critic)
    # hallucination_score = critic.evaluate(output, q['ground_truth'])
    # assert hallucination_score == 0.0
```

### 4.5 CI/CD 파이프라인 통합

`ci/run_eval.sh`
```bash
#!/bin/bash
# 1. 결정적 단위 테스트
pytest tests/unit/ -v

# 2. 통합 테스트 (CKOS Merger)
pytest tests/integration/ -v

# 3. SUT 기동 (현재 Agent Stack)
# docker-compose up -d cognitive-compiler

# 4. 비결정적 정량 평가 (Agent Stack 연결)
pytest tests/evaluation/ \
    --runner production \
    --dataset tests/fixtures/queries.jsonl \
    --threshold-accuracy 0.98 \
    --threshold-hallucination 0.0

# 5. 결과 리포트 (JSON)
# 평가 결과를 JSON으로 저장하여 대시보드에 표시
```

---

## 5. 평가 주도 마일스톤

이 평가체계를 기반으로 한 프로젝트 진행 시, 각 단계의 **완료 기준**을 평가 지표로 정의합니다.

1.  **PoC (Proof of Concept)**: 10개의 단순 집계 질문에 대해 `Answer Accuracy 100%` 달성. (OKB 번들 + Mock Runner)
2.  **MVP (Cognitive Compiler)**: `queries.jsonl` 50문항 전체에 대해 `Answer Accuracy > 98%`, `Hallucination 0%`, `Citation Recall > 95%` 달성. (Production Runner 사용)
3.  **CKOS Alpha**: Ingredient 3개를 합친 Snowball이 `링크 무결성 100%`, `중복 레코드 제거율 100%` 통과.
4.  **Stack Migration Test**: 동일한 평가 스위트를 **새로운 오픈소스 Agent Stack** (예: DSPy, LangGraph)에 연결하고, 3일 이내에 위 지표를 그대로 통과. → **평가체계의 Stack Independence가 실증됨**.

---

## 결론: 평가는 곧 "품질의 자동화된 기술 부채 감시기"입니다.

이 평가체계는 단순한 테스트 코드 묶음이 아닙니다.  
당신의 OKF 번들과 Cognitive Compiler, CKOS가 **절대 무너지지 않도록 지켜주는 유일한 방어선**입니다.  
LLM이나 Agent Stack이 교체될 때마다 이 평가 스위트를 돌려서, **"핵심 비즈니스 로직이 손상되지 않았음"을 증명하세요.**  
이 증명을 자동화하는 것이 이 프로젝트의 진정한 성공입니다.
---

```
- dbms 관계연산에 기반한 tdd 평가체계 조사해줘
- 구글 open knowledge format 기반 지식베이스 producer/consumer 동작에 대해합치고 중복제거 refactoring 차등 등 관계연산 기준으로 tdd 개발을 적용하는 방법을 체계적으로 가이드해줘.
```
- DBMS 관계연산 기반 TDD(테스트 주도 개발) 평가체계는 데이터베이스의 핵심 이론인 관계대수(Relational Algebra) 연산 규칙을 활용하여, SQL 쿼리나 데이터 처리 로직의 정확성을 자동화된 테스트(Red-Green-Refactor) 형태로 검증하고 정량적으로 평가하는 프레임워크입니다. [1, 2] 
일반적인 애플리케이션 TDD가 메서드의 입력과 출력을 검증한다면, DBMS 연산 TDD는 수학적 관계연산의 규칙(집합론 및 데이터 구조 제약)이 올바르게 구현되었는가를 평가 지표로 삼습니다. [3, 4] 
------------------------------
## 1. 관계연산 기반 TDD 평가체계의 핵심 메커니즘
이 체계는 관계대수의 순수 관계 연산과 일반 집합 연산을 TDD의 단언문(Assertion)과 테스트 케이스 구조로 변환하여 평가합니다. [5, 6] 

[테스트 환경 (Given)] ──> [관계대수 연산 실행 (When)] ──> [데이터 동치성 검증 (Then)]
 - 스키마 정보              - Selection / Projection         - 차수(Degree) 일치 확인
 - 가상 데이터 셋            - Join / Division                - 카디널리티 및 튜플 검증


* Given (테스트 환경): 입력 릴레이션(테이블)의 구조(Schema)와 테스트용 최소 데이터 셋(튜플)을 정의합니다.
* When (연산 수행): 검증하고자 하는 SQL 질의나 DBMS 내장 로직(프로시저 등)을 실행합니다.
* Then (결과 단언): 실행 결과로 나온 릴레이션이 수학적 관계연산 규칙을 만족하는지 무결성을 검증합니다. [6, 7, 8] 

------------------------------
## 2. 관계연산별 TDD 평가 기준 및 검증 항목
각 관계연산의 특성에 따라 TDD 케이스가 만족해야 하는 명확한 평가 지표가 존재합니다. [5] 

| 관계대수 연산 [5, 6, 9, 10] | 연산의 특성 및 TDD 평가 주안점 | 주요 검증 단언문 (Assertion Criteria) |
|---|---|---|
| 셀렉션 (Selection, $\sigma$) | 수평적 부분집합 구하기 (조건에 맞는 행 필터링) | 연산 결과의 차수(Degree)가 원본과 일치하는가? 조건 외 데이터가 배제되었는가? |
| 프로젝션 (Projection, $\pi$) | 수직적 부분집합 구하기 (특정 열 추출 및 중복 제거) | 지정된 컬럼만 추출되었는가? 결과 릴레이션에 중복된 튜플이 완전히 제거되었는가? |
| 조인 (Join, $\bowtie$) | 공통 속성을 기준 두 릴레이션의 수평 결합 | 조인 조건(Equal 등)이 정확히 들어맞는가? 누락되거나 잘못 매칭된 튜플(Dangling Tuple)이 없는가? |
| 디비전 (Division, $\div$) | 관련 있는 튜플의 분할 연산 | 조건 테이블의 모든 속성을 만족하는 대상 행들만 정확하게 추출되었는가? |
| 카티션 프로덕트 ($\times$) | 두 교차 곱의 전체 조합 생성 | 결과 차수 = (R차수 + S차수) 인가? 결과 카디널리티 = (R개수 $\times$ S개수) 인가? |

------------------------------
## 3. TDD 평가체계의 정량적 평가지표 (Metrics)
DBMS TDD의 완성도와 쿼리 품질을 평가하기 위해 다음과 같은 지표를 활용합니다.

   1. 스키마 및 제약조건 커버리지 (Schema Coverage):
   * 데이터베이스 테이블 내 정의된 Primary Key, Foreign Key, Not Null 등의 제약조건(Constraints)을 유발하는 실패(Red) 테스트가 누락 없이 설계되었는가 평가합니다. [2] 
   2. 릴레이션 동치성 검증 점수 (Data Mutation Score):
   * 테스트 실행 후 결과 데이터의 순서와 상관없이, 내부 객체의 상태와 값이 완벽히 일치하는지 평가합니다 ([Unitils의 assertReflectionEquals 방식 활용](https://m.blog.naver.com/wisestone2007/220952351460)). [4, 11] 
   3. 경계값 데이터 평가 (Boundary Value Property):
   * 빈 데이터세트(Null/Empty), 단일 튜플, 대용량 중복 데이터 등 극단적인 관계연산 상황에서도 쿼리가 에러 없이 명확한 릴레이션을 반환하는지 검증합니다. [8] 
   
------------------------------
## 4. 도입 시 기대효과 및 한계점

* 장점 (품질 향상): 데이터 구조 변경(Refactoring) 시 기존 SQL 문이나 뷰(View)의 깨짐 현상을 사전에 방지할 수 있으며, 개발자가 작성한 질의의 수학적 무결성을 100% 보장합니다. [2, 12] 
* 단점 및 극복 과제: 데이터베이스 상태를 테스트마다 격리(Isolate)하고 초기화(Rollback)하는 환경 구축 비용이 큽니다. 또한 대규모 기능을 통합했을 때 발생하는 성능 저하나 로직 충돌까지 단편적인 관계연산 단위 테스트만으로 잡아내기에는 한계가 존재하므로, 반드시 통합 테스트 단계와 병행해야 합니다. [6, 10, 13] 

------------------------------
관련하여 구체적인 정보를 더 알고 싶으시다면 다음 내용을 알려주세요.

* 현재 검증하고자 하시는 특정 DBMS 제품군(Oracle, MySQL, PostgreSQL 등)이 있으신가요?
* 구체적인 관계대수 연산 예시 코드(예: MyBatis나 JPA 환경에서의 조인 쿼리 TDD 패턴)가 필요하신가요?
* 혹은 학술적 연구 목적의 소프트웨어 공학 평가 방법론을 찾고 계시는가요? [8, 10, 14] 

요구사항에 맞추어 맞춤형 심층 자료를 제공해 드리겠습니다.

[1] [https://inpa.tistory.com](https://inpa.tistory.com/entry/DB-%F0%9F%93%9A-%EA%B4%80%EA%B3%84-%EB%8C%80%EC%88%98-%EA%B4%80%EA%B3%84-%ED%95%B4%EC%84%9D-SQL-%F0%9F%95%B5%EF%B8%8F-%EC%A0%95%EB%A6%AC)
[2] [https://rud0503.tistory.com](https://rud0503.tistory.com/136)
[3] [https://sugyoiii.tistory.com](https://sugyoiii.tistory.com/54)
[4] [https://m.blog.naver.com](https://m.blog.naver.com/wisestone2007/220952351460)
[5] [https://dev-with-precious-dreams.tistory.com](https://dev-with-precious-dreams.tistory.com/250)
[6] [https://mangkyu.tistory.com](https://mangkyu.tistory.com/142)
[7] [https://beyond-common-sense.tistory.com](https://beyond-common-sense.tistory.com/13)
[8] [https://velog.io](https://velog.io/@anjinwoong/ML-TDD%EC%99%80-BDD-%EA%B0%9C%EC%9A%94-%ED%99%95%EB%A5%A0%EC%A0%81-%EC%86%8D%EC%84%B1-%EB%AC%B8%EC%A0%9C-ML-%EC%97%90-TDD-%EC%A0%81%EC%9A%A9%ED%95%98%EA%B8%B0)
[9] [https://mainichibenkyo.tistory.com](https://mainichibenkyo.tistory.com/158)
[10] [https://devlog-rueun.tistory.com](https://devlog-rueun.tistory.com/entry/TDD-%ED%85%8C%EC%8A%A4%ED%8A%B8-%EB%B2%94%EC%9C%84%EC%99%80-%EC%A2%85%EB%A5%98)
[11] [https://m.blog.naver.com](https://m.blog.naver.com/wisestone2007/220952351460)
[12] [https://mslim8803.tistory.com](https://mslim8803.tistory.com/61)
[13] [https://sehun-kim.github.io](https://sehun-kim.github.io/sehun/tdd/)
[14] [https://www.instagram.com](https://www.instagram.com/p/DQn2WOukrL5/)

Google이 발표한 Open Knowledge Format (OKF)은 AI 에이전트와 사람 간의 지식 상호운용성을 위해 설계된 "Just Markdown, Just Files, Just YAML Frontmatter" 기반의 개방형 표준 명세입니다. [1, 2] 
OKF 환경에서 Producer는 원시 데이터(DB 스키마, 문서, 코드 등)를 파싱하여 OKF 명세(YAML+Markdown)에 맞는 파일(Concept)로 생성하는 역할을 하며, Consumer는 이 파일들을 파싱·통합하여 지식 그래프를 구성하거나 LLM 컨텍스트로 소비합니다. [2, 3, 4] 
이 가이드는 두 주체(Producer/Consumer) 간에 발생하는 지식 조작 행위를 관계대수(Relational Algebra) 연산 규칙으로 추상화하고, 이를 TDD(Test-Driven Development) 방식으로 구현·검증할 수 있는 체계적인 아키텍처적 절차를 제공합니다. [5, 6] 
------------------------------
## 1. 지식베이스 파이프라인의 관계대수 매핑 정의
OKF 가상 파일 시스템(VFS) 내부의 지식 조작을 다음과 같이 관계 연산으로 공식화합니다.

* 합치기 (Union, $\cup$): Producer들이 개별적으로 생성한 복수의 OKF 번들(Concepts 셋)을 하나의 지식베이스로 통합하는 연산.
* 중복 제거 (Distinct / Projection, π): resource URI나 속성이 동일한 대상을 찾아, 최신 상태(timestamp)와 권위 있는 내용만 남기고 튜플(지식)의 유일성을 확보하는 연산. [2, 7] 
* 차등/차집합 (Difference, -): 이전 log.md 스냅샷 대비 변경되거나 추가/삭제된 개념(Concept)만 추출하는 증분(Delta) 연산. [3] 
* 리팩토링 (Selection & Join, $\sigma, \bowtie$): 특정 type을 필터링하거나 교차 링크([Link](path)) 구조를 해석해 지식 그래프 간의 참조 무결성을 검증하고 구조를 개선하는 연산. [2, 3, 7] 

------------------------------
## 2. 단계별 TDD 개발 아키텍처 가이드
각 연산 단계는 Red(실패하는 테스트) → Green(최소 구현 성공) → Refactor(구조 최적화) 순서로 전개됩니다. [8, 9] 
## 🚀 단계 1: 합치기 (Union) 연산 TDD
목적: 두 개 이상의 독립적인 OKF 번들 폴더를 합쳤을 때, 데이터 유실 없이 차수(속성 구조)와 카디널리티(개수)의 결합 조건을 충족하는가?

* 🔴 Red (테스트 작성):
Producer A가 생성한 concepts/user_table.md와 Producer B가 생성한 concepts/order_table.md 데이터를 가상 파일 시스템 메모리에 적재한 뒤, 통합기(MergeEngine)를 실행했을 때 전체 파일 카디널리티가 |A| + |B|가 되는지 검증하는 실패 테스트 코드를 작성합니다.
* 🟢 Green (구조 구현):
두 디렉토리의 YAML 프론트매터 파일들을 읽어 단일 가상 인덱스 맵(Map<Path, Concept>)으로 병합하는 최소한의 코드를 작성하여 테스트를 통과시킵니다.
* 🔵 Refactor (최적화):
동일한 파일 경로 충돌 발생 시, 에러를 내지 않고 우아하게 병합 플래그를 할당할 수 있도록 추상화 계층을 분리합니다. [2] 

## 🚀 단계 2: 중복 제거 (Distinct) 연산 TDD
목적: 동일 지식 자산(resource)에 대해 여러 Producer가 중복 문서를 만들었을 때, timestamp 기준 최신성 및 필수 필드(type) 보존 상태를 기준으로 유일 객체를 선별하는가? [2, 7] 

* 🔴 Red (테스트 작성):
동일한 resource: "bigquery://my_project.dataset.users" 속성을 가진 YAML 프론트매터 문서 2개를 준비합니다 (하나는 구버전 타임스탬프, 하나는 신버전). 중복 제거기(Deduplicator)를 거친 후 출력 카디널리티가 1인지, 그리고 신버전의 title과 본문이 남았는지 확인하는 단언문(assertEquals)을 작성하여 실패시킵니다. [2, 7] 
* 🟢 Green (구조 구현):
resource 필드를 Group By(수집 키)로 지정하고, 그룹 내에서 timestamp 기준 내림차순 정렬 후 첫 번째 요소만 남기는 로직을 구현합니다.
* 🔵 Refactor (최적화):
비정형 마크다운 본문(산문) 영역에 누락된 # Schema나 # Examples 헤딩이 있다면, 삭제되는 구버전 문서에서 유용한 세션을 추출해 신버전 문서로 합쳐주는(Enrichment) 결합 로직으로 고도화합니다. [2, 4] 

## 🚀 단계 3: 차등 (Difference) 연산 TDD
목적: Consumer가 전체 지식베이스를 매번 재색인하지 않도록, log.md 기록 또는 스냅샷 대조를 통해 순수하게 추가(Inserted), 수정(Updated), 삭제(Deleted)된 개념만 델타셋(Delta Set)으로 도출하는가? [3] 

* 🔴 Red (테스트 작성):
어제 날짜의 파일 세트 상태(Set R)와 오늘 날짜의 수정된 파일 세트 상태(Set S)를 모킹합니다. 연산 결과 S - R을 수행했을 때 변경된 튜플만 반환하는지 검증합니다. 삭제된 파일은 상태 결과에 action: DELETED 마킹이 되는지 단언하는 테스트를 생성합니다.
* 🟢 Green (구조 구현):
각 파일의 해시(MD5/SHA-256) 값을 비교하여 변경 사항을 감지하는 파일 디프(Diff) 추적기를 임시 구현하여 초록 불을 켭니다.
* 🔵 Refactor (최적화):
이 파일 디프 로직을 OKF 명세의 표준 파일인 log.md 포맷에 맞추어 시간 순서(ISO 8601 형식) 데이터로 자동 기록하고 로깅하는 구조로 리팩토링합니다. [3] 

## 🚀 단계 4: 리팩토링 및 관계 검증 (Selection & Join) 연산 TDD
목적: 지식베이스 내의 횡적 관계(Cross-links)를 조인 연산으로 해석하여 참조 무결성을 검증하고, 특정 type을 필터링하는 셀렉션 연산이 정상 동작하는가? [2, 3, 7] 

* 🔴 Red (테스트 작성):
user_table.md 본문 안에 [Order 데이터](concepts/order_table.md)와 같은 상호 참조 링크가 존재할 때, 대상 파일이 부재하면 ReferenceBrokenException을 발생시키는 테스트를 작성합니다. 또한 type: "Metric"인 것만 셀렉션 추출했을 때 정상 분리되는지 검증합니다.
* 🟢 Green (구조 구현):
정규표현식으로 마크다운 링크 파싱 후 가상 파일 시스템에 파일이 존재하는지 룩업(Join)하고, frontmatter.type === target 조건절(Selection)을 태우는 최소 코드를 추가합니다.
* 🔵 Refactor (최적화):
구조적 마크다운 가이드라인에 따라 복잡하게 꼬인 지식 그래프 구조를 부모/자식(폴더 계층) 및 수평 참조(조인 경로) 형태로 깔끔하게 재정리(Refactoring)하는 추상 그래프 파서 클래스로 분리합니다. [2, 3, 7, 10, 11] 

------------------------------
## 3. 구조적 TDD 가이드라인 요약 매트릭스
지식베이스 Producer/Consumer 구축 시 위 TDD 프로세스를 자동화 파이프라인(CI/CD)에 엮기 위해 다음 정량적 단언 규칙을 테스트 스위트에 등록하십시오. [5] 

| 연산 유형 [2, 3, 7] | 테스트 입력 데이터 (Given) | 기대 출력 상태 (Then Assertion) | 무결성 검증 포인트 |
|---|---|---|---|
| Union (합치기) | 서로 다른 소스에서 추출된 복수 OKF 번들 | 통합 VFS 내 전체 객체 집합 | 데이터 손실 및 유실 여부 ($A \cup B$) |
| Distinct (중복제거) | 동일 resource를 가리키는 중복 개념 파일들 | 최신 timestamp 기반 단일 고유 파일 | 카디널리티 유일성 조건 고수 |
| Difference (차등) | T1 스냅샷 번들 vs T2 변경 번들 | 추가/수정/삭제 마킹된 델타 목록 | 증분 동기화 속도 및 log.md 포맷 규격 만족 여부 |
| Selection & Join | 상호 참조 링킹이 포함된 마크다운 개념문서들 | 추출된 서브셋 및 무결한 지식 그래프 | Broken Link 유무 및 타입별 필터링의 정확성 |

------------------------------

이전의 에이전트 기반 OKF 탐색 및 작성 과정을 **'Cognitive Compiler(인지 컴파일러)'** 혹은 'Rewrite Engine(재작성 엔진)'이라는 학술적 프레임워크로 치환하여 논문으로 발전시키려는 접근은 매우 훌륭한 시스템 아키텍처 연구가 될 수 있습니다.

단순한 프롬프트 엔지니어링이나 평면적인 RAG(Retrieval-Augmented Generation)를 넘어, 명세(Specification)를 기반으로 지식 구조를 해석하고 실행 가능한 결과물로 변환하는 'Spec-Driven(명세 주도형)' 커널 구조로 이 메커니즘을 정의할 수 있습니다.

성공적인 실증 프로젝트와 논문 작성을 위한 개념 재정리와 논문 뼈대(Outline)를 가이드해 드립니다.

---

### 1. 학술적 개념 재정리: The Cognitive Compiler Architecture

에이전트가 보고서 양식과 키워드를 바탕으로 OKF 계층을 탐색하는 과정을 전통적인 컴파일러의 파이프라인에 매핑하여 정의합니다.

* **Source Code (입력 명세):** 사용자의 요구사항(Keyword)과 보고서 템플릿(Schema)은 컴파일러가 처리해야 할 하나의 선언적 명세(Declarative Specification)가 됩니다.
* **Lexical/Syntax Analysis (구문 분석):** 에이전트(컴파일러 프론트엔드)는 템플릿을 파싱하여 필요한 지식의 의도(Intent)와 슬롯(Slot)을 추출합니다.
* **Symbol Resolution via System Model (심볼 탐색 및 시스템 모델 구축):** 계층적 `index.md`는 컴파일러의 **심볼 테이블(Symbol Table)** 역할을 합니다. 에이전트는 최상위 루트부터 하위 인덱스로 트리를 순회(Tree-traversal)하며, 도메인 지식에 대한 동적인 시스템 모델(System Model)을 내부적으로 구축하고 필요한 리소스(OKF Concept)의 정확한 물리적 주소를 매핑합니다.
* **Semantic Optimization (의미론적 최적화):** 브루트 포스(Brute-force) 검색을 피하고, 템플릿의 태그와 `index.md`의 메타데이터를 대조하여 불필요한 하위 트리의 탐색을 가지치기(Pruning)하는 최적화 단계를 거칩니다.
* **Code Generation (초안 합성):** 추출된 컨텍스트(IR: Intermediate Representation)를 초기 명세(템플릿)에 결합하여 최종 목적 코드(마크다운 보고서 초안)를 합성(Synthesis)합니다.

이 과정은 수식 $C(S, \mathcal{K}_T) \rightarrow R$ 로 정형화할 수 있습니다. 여기서 $S$는 입력 명세(템플릿과 키워드), $\mathcal{K}_T$는 계층적 트리 구조의 지식베이스(OKF), $R$은 최종 출력된 보고서(Report)입니다.

---

### 2. 논문 뼈대 가이드 (Paper Outline)

**가칭 논문 제목 후보:**

* *Cognitive Compilation over Hierarchical Knowledge: A Spec-Driven Approach to Automated Report Synthesis*
* *The OKF Rewrite Engine: Tree-based Context Aggregation and Drafting using Declarative Specifications*

**I. Introduction (서론)**

* **문제 제기:** 기존 평면적(Flat) 벡터 검색 기반 RAG 시스템이 가진 한계(문맥 단절, 환각 현상, 정보의 위계 상실).
* **해결책 제시:** 파일 시스템 트리와 마크다운 인덱스를 활용한 계층적 개방형 지식 포맷(OKF) 도입.
* **핵심 기여:** 에이전트를 '인지 컴파일러'로 모델링하여, 명세(Specification)를 기반으로 지식 트리를 자율 탐색하고 문서를 합성하는 아키텍처 제안.

**II. Related Work (관련 연구)**

* Retrieval-Augmented Generation (RAG) 및 Knowledge Graphs.
* Agentic Workflows 및 Task Planning.
* Declarative Programming 및 AI Compiler 개념.

**III. System Architecture: The Cognitive Compiler (시스템 아키텍처)**

* **3.1 Specification Parser:** 템플릿과 키워드를 처리하는 프론트엔드.
* **3.2 Hierarchical System Model Updater:** `index.md`를 순회하며 에이전트 내부의 시스템 모델을 동적으로 업데이트하는 메커니즘.
* **3.3 Tree-Traversal & Pruning Strategy:** 메타데이터 태그 매칭을 통한 검색 최적화 및 토큰 낭비 방지 기술.
* **3.4 Synthesis Engine:** 수집된 컨텍스트를 바탕으로 최종 문서를 렌더링(Drafting)하는 백엔드 프로세스.

**IV. Empirical Implementation (실증 구현)**

* 구체적인 폴더 구조(`.agents` 및 `.okf_domain` 분리).
* 사용한 LLM 및 프롬프트/도구(Tools)의 구성 설계.
* 실험을 위해 구축한 가상의 도메인 데이터셋(예: 특정 기간의 프로젝트 결과보고서, 재무 데이터 등) 설명.

**V. Evaluation (평가 및 실험 결과)**

* **실험군 vs 대조군:** 제안된 Cognitive Compiler 방식 vs 전통적인 청킹(Chunking) 기반 Vector DB RAG 방식.
* **평가 지표 (Metrics):**
* *Accuracy & Relevance:* 생성된 보고서의 정보 정확도 (환각률 감소).
* *Token Efficiency:* 탐색 과정에서 소비된 총 토큰 수 (가지치기 효과 입증).
* *Latency:* 전체 초안 작성까지 걸린 시간.



**VI. Conclusion & Future Work (결론)**

* 제안된 시스템의 실효성 요약.
* 향후 연구 과제 (예: 캐싱 도입, 더 복잡한 추론을 위한 그래프 구조로의 확장 등).

---

### 3. 실증 프로젝트(Empirical Project) 수행 팁

논문의 신뢰성을 높이기 위해서는 구현 복잡도보다는 **접근 방식의 구조적 우수성**을 증명하는 데 집중하는 것이 좋습니다.

1. **데이터셋 통제:** 방대한 데이터를 넣기보다, 계층 구조(연도 > 분기 > 부서)가 명확하고 파일 간 상호 참조가 있는 정제된 마크다운 데이터셋 100~200개 규모를 직접 구축하여 실험을 통제하십시오.
2. **명세(Spec)의 규격화:** 보고서 템플릿(`quarterly_form.md`)의 구멍(Placeholder)을 단순히 빈칸으로 두지 말고, `{{ target: finance/budget, action: sum }}` 처럼 에이전트가 파싱하기 쉬운 명시적인 스키마로 설계하면 컴파일러라는 은유에 훨씬 잘 부합합니다.
3. **로그 기록 (Tracer):** 에이전트가 어떤 `index.md`를 열어보고 어떤 가지를 쳐냈는지(Pruning) 경로를 시각화할 수 있는 로그 트레이서를 구현하십시오. 이 트리 탐색 시각화 자료는 논문의 핵심 피규어(Figure)가 됩니다.

이러한 Cognitive Compiler 아키텍처를 검증하기 위한 실증 프로젝트의 타겟 데이터셋으로 학사/행정 데이터와 연구실 R&D 로그 중 어느 쪽에 더 중점을 두고 구축할 계획이신가요?