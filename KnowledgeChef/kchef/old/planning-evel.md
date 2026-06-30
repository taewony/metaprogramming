```
Metal/Cognitive rhearsal/planning 역할이 kchef agent의 핵심인데,

아래와 같은 정형 data 질의와 추가적으로 비정형 문서에 대한 질의가 들어 올 때, 어떻게 planning만을 따로 떼어서 구현하고, 시험하고 평가할지 체계적으로 가이드해줘.

## 사용자 query prompt samples 10개 + expected answers

| # | 사용자 질문 | 예상 SQL | 예상 답변 |
|---|------------|----------|-----------|
| 1 | "VIP 고객은 몇 명이고, 누구야?" | `SELECT id, name, email, point_balance FROM customers WHERE grade='VIP'` | VIP 고객은 5명입니다: 정민호(ID:4, 포인트 45,000), 오세훈(ID:8, 28,000), 강태영(ID:12, 32,000), 문창호(ID:16, 51,000), 황미소(ID:20, 39,000) |
| 2 | "가장 비싼 상품 3개 알려줘" | `SELECT name, brand, price FROM products ORDER BY price DESC LIMIT 3` | 1. 삼성 비스포크 냉장고 (2,150,000원), 2. 애플 아이폰 15 프로 (1,550,000원), 3. LG 그램 16인치 (1,520,000원) |
| 3 | "김민지 고객님의 총 주문 금액은?" | `SELECT SUM(o.total_amount) FROM orders o JOIN customers c ON o.customer_id=c.id WHERE c.name='김민지' AND o.status='confirmed'` | 김민지 고객님의 총 주문 금액은 2,490,000원입니다 (3건 주문). |
| 4 | "가장 많이 팔린 상품은?" | `SELECT p.name, SUM(oi.quantity) AS total_sold FROM order_items oi JOIN products p ON oi.product_id=p.id GROUP BY p.id ORDER BY total_sold DESC LIMIT 1` | 로지텍 MX 마스터 3S가 총 6개 판매되어 가장 많이 팔렸습니다. |
| 5 | "이번 달(6월) 매출은 얼마야?" | `SELECT SUM(total_amount) FROM orders WHERE strftime('%Y-%m', ordered_at)='2024-06' AND status='confirmed'` | 2024년 6월 매출은 5,180,000원입니다. |
| 6 | "리뷰가 없는 상품이 있나?" | `SELECT p.name FROM products p LEFT JOIN reviews r ON p.id=r.product_id WHERE r.id IS NULL` | 샤오미 미밴드 9, 구글 픽셀 8a 등 5개 상품에 아직 리뷰가 없습니다. |
| 7 | "실버 등급 고객 중 가장 많이 주문한 사람은?" | `SELECT c.name, COUNT(o.id) AS order_count FROM customers c JOIN orders o ON c.id=o.customer_id WHERE c.grade='SILVER' AND o.status='confirmed' GROUP BY c.id ORDER BY order_count DESC LIMIT 1` | 이현우 고객님이 2건 주문으로 실버 등급 중 가장 많이 주문했습니다. |
| 8 | "전체 평균 주문 금액은?" | `SELECT AVG(total_amount) FROM orders WHERE status='confirmed'` | 전체 평균 주문 금액은 823,333원입니다. |
| 9 | "취소된 주문이 있나? 몇 건?" | `SELECT COUNT(*) FROM orders WHERE status='cancelled'` | 취소된 주문은 총 2건입니다. |
| 10 | "애플 제품 중 재고가 50개 이상인 것 알려줘" | `SELECT name, stock_qty FROM products WHERE brand='Apple' AND stock_qty >= 50` | 애플 아이폰 15 프로 (85개)가 재고 50개 이상입니다. |
```
## Cognitive Compiler의 ‘Mental Rehearsal’ 단계를 분리하여 구현·시험·평가하는 방법

이 가이드는 **Cognitive Compiler(Planner)**의 **계획 수립 능력**만을 완전히 분리하여 테스트하고 평가하는 체계를 제공합니다.  
실행 엔진(Knowledge VM) 없이, Planner가 올바른 **Knowledge IR**을 생성하는지 검증하는 것이 목표입니다.

---

## 1. 핵심 원칙: Planner는 ‘계획’만, Executor는 ‘실행’만

- **Planner (Cognitive Compiler)**는 자연어 질문과 스키마 정보(index.md)를 입력받아 **Knowledge IR**을 출력하는 **순수 함수**로 취급합니다.
- **Executor (Knowledge VM)**는 Knowledge IR을 입력받아 실제 데이터/문서를 조회하고 가공하여 최종 응답을 생성합니다.
- Planner를 테스트할 때는 **모든 데이터 액세스 도구를 모의(Mock)** 하거나, **스키마를 컨텍스트로 직접 제공**하여 실제 파일 I/O 없이 순수 계획 능력만 평가합니다.

---

## 2. Knowledge IR 명세: 정형 질의와 비정형 문서 질의를 위한 공통 표현

Planner의 출력은 항상 아래의 JSON 스키마를 따릅니다.  
이 중간 표현은 SQL도, Python 코드도 아닌, **OKF 지식 탐색을 위한 추상적 계획**입니다.

```python
# ir_schema.py (Pydantic)
from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, Field

class Filter(BaseModel):
    field: str
    operator: Literal["=", ">", "<", ">=", "<=", "IN", "LIKE"]
    value: Union[str, int, float, List[str]]

class DataStep(BaseModel):
    type: Literal["data"]
    source: str  # 데이터 파일 경로 (예: "data/customers.csv")
    filters: Optional[List[Filter]] = None
    join: Optional[Dict[str, str]] = None  # {"with": "data/orders.csv", "on": "customers.id=orders.customer_id"}
    group_by: Optional[List[str]] = None
    order_by: Optional[List[Dict[str, str]]] = None  # [{"field": "point_balance", "dir": "desc"}]
    limit: Optional[int] = None
    projections: Optional[List[str]] = None  # 가져올 컬럼
    aggregation: Optional[Dict[str, str]] = None  # {"function": "COUNT", "field": "id"}

class DocumentStep(BaseModel):
    type: Literal["document"]
    source: str  # 문서 경로 (예: "documents/prd/cap01_prd.docx")
    extract_sections: Optional[List[str]] = None  # 추출할 섹션 제목
    query: Optional[str] = None  # 문서에 대한 자연어 질문 (의미적 필터)
    operation: Literal["extract", "summarize", "find"] = "extract"
    output_format: Literal["text", "bullet_points", "table"] = "text"

class KnowledgeIR(BaseModel):
    goal: Literal["QUERY", "AGGREGATE", "SUMMARIZE", "COMPARE", "TREND", "FACT_CHECK"]
    description: str  # 사람이 이해하기 위한 설명
    steps: List[Union[DataStep, DocumentStep]]  # 순차 실행 단계
    output_structure: Dict[str, str]  # 답변 형식 {"headline": "string", "details": "list", "metrics": "dict"}
    confidence_rationale: Optional[str] = None  # Planner가 자신감을 가진 이유 (옵션)
```

이 IR은 **어떤 데이터에 어떤 연산을 적용할지**를 선언적으로 담고 있습니다.  
Executor는 이 IR을 받아 실제 SQL, Pandas 로직, 문서 파서 등으로 변환합니다.

---

## 3. 테스트 데이터셋: 질문-스키마-기대 IR

Planner를 테스트하려면 **질문 + 사용 가능한 데이터 스키마 + 정답 IR**이 세트로 필요합니다.  
스키마는 **OKF 번들의 index.md** 또는 그 요약본으로 제공됩니다.

### 3.1 정형 데이터 질의 샘플 (사용자 제공 10개 예시 활용)

| 질문 ID | 사용자 질문 | 스키마 (index.md 일부) | 예상 Knowledge IR (요약) |
|--------|------------|------------------------|---------------------------|
| Q01 | VIP 고객은 몇 명이고, 누구야? | customers(id, name, email, grade, point_balance) | `{ goal: "QUERY", steps: [{type:"data", source:"customers", filters:[{field:"grade",op:"=",value:"VIP"}], projections:["id","name","email","point_balance"]}] }` |
| Q02 | 가장 비싼 상품 3개 알려줘 | products(id, name, brand, price, stock_qty) | `{ goal: "QUERY", steps: [{type:"data", source:"products", order_by:[{field:"price",dir:"desc"}], limit:3, projections:["name","brand","price"]}] }` |
| Q03 | 김민지 고객님의 총 주문 금액은? | customers(id, name, ...), orders(id, customer_id, total_amount, status, ordered_at) | `{ goal: "AGGREGATE", steps: [{type:"data", source:"customers", filters:[{field:"name",op:"=",value:"김민지"}], projections:["id"]}, {type:"data", source:"orders", filters:[{field:"status",op:"=",value:"confirmed"}], join:{with:"customers",on:"..."}, aggregation:{function:"SUM",field:"total_amount"}}] }` |
| ... | ... | ... | ... |
| Q10 | 애플 제품 중 재고가 50개 이상인 것 알려줘 | products | `{ goal: "QUERY", steps: [{type:"data", source:"products", filters:[{field:"brand",op:"=",value:"Apple"}, {field:"stock_qty",op:">=",value:50}], projections:["name","stock_qty"]}] }` |

### 3.2 비정형 문서 질의 예시

| 질문 ID | 사용자 질문 | 스키마 (문서 메타데이터) | 예상 Knowledge IR |
|--------|------------|--------------------------|-------------------|
| Q11 | "2026-1학기 AI 캡스톤 프로젝트의 주요 성과를 요약해줘" | semester/2026-1/index.md → 프로젝트 목록 → project/ai_capstone/index.md → 문서 목록 (final_report.pptx) | `{ goal: "SUMMARIZE", steps: [{type:"document", source:"documents/2026-1/ai_capstone_report.pptx", operation:"summarize", query:"주요 성과", output_format:"bullet_points"}] }` |
| Q12 | "작년 동기 대비 올해 매출 증가율을 보여줘" | sales_2025.csv, sales_2026.csv | `{ goal: "TREND", steps: [{type:"data", source:"data/sales_2025.csv", ...}, {type:"data", source:"data/sales_2026.csv", ...}, {type:"data", operation:"CALCULATE", formula:"(2026_sum - 2025_sum)/2025_sum"}] }` |

---

## 4. Planner Agent 구현: 스키마 기반 순수 계획 함수

Planner는 LLM을 이용하여 구현합니다. **실제 데이터 접근 없이** 스키마 정보만으로 IR을 생성하도록 설계합니다.

### 4.1 Planner 프롬프트 (SKILL.md 기반)

```markdown
# Skill: Knowledge IR Planner (Mental Rehearsal Only)

## Role
You are a **Cognitive Planner** that converts a natural language question into a Knowledge IR.  
You have **read-only access** to the **symbol table (index.md)** of the OKF bundle.  
You must **not** access any actual data files.  
Your output is a JSON object that strictly follows the Knowledge IR schema.

## Available schema information (provided in the prompt)
{INDEX_CONTENT}

## Steps
1. Analyze the question: extract intent (goal), entities, filters, aggregations, and desired output structure.
2. Map the intent to the relevant data sources and documents listed in the schema.
3. For data steps, specify filters, joins, projections, and aggregations based on the schema fields.
4. For document steps, specify the document path and the operation (extract/summarize) with any sub-questions.
5. Assemble the steps into a single Knowledge IR JSON.

## Output format
Return ONLY the JSON, no other text.
{
  "goal": "...",
  "description": "...",
  "steps": [ ... ],
  "output_structure": { ... }
}
```

### 4.2 Python Skeleton: Planner with Mock Schema

```python
# planner.py
import json
from typing import Dict
import openai  # 혹은 다른 LLM 클라이언트

class Planner:
    def __init__(self, llm_client):
        self.llm = llm_client
        with open("SKILL.md") as f:
            self.base_prompt = f.read()

    def plan(self, question: str, schema_context: str) -> dict:
        """
        schema_context: OKF index.md의 관련 부분 텍스트 (또는 구조화된 JSON)
        """
        prompt = self.base_prompt.replace("{INDEX_CONTENT}", schema_context)
        prompt += f"\n\nUser Question: {question}\nKnowledge IR:"

        response = self.llm.generate(prompt)  # JSON 문자열
        ir = json.loads(response)
        return ir
```

실제 운용 환경에서는 Planner가 `read_index()` 도구를 호출하며 점진적으로 스키마를 수집할 수 있지만,  
**테스트 환경**에서는 `schema_context`를 미리 준비하여 Planner에 직접 주입합니다.  
이 방식으로 Planner의 **탐색 능력이 아니라, 스키마 해석 및 계획 능력만 격리하여 평가**할 수 있습니다.

---

## 5. 평가 프레임워크: 정답 IR 비교를 통한 자동 채점

Planner의 출력 IR과 예상 IR을 구조적으로 비교하여 점수를 산출합니다.  
이 평가는 **실행기 없이 0.1초 이내에 완료**되며, CI에 통합 가능합니다.

### 5.1 평가 지표

| 지표 | 설명 | 산출 방법 |
|------|------|-----------|
| **Goal Accuracy** | `ir.goal`이 정답과 일치하는가? | 정확히 일치 (0/1) |
| **Step Count Accuracy** | 단계 수가 일치하는가? | ±0 |
| **Data Source Precision/Recall** | 올바른 데이터 소스(파일 경로)가 포함되었는가? | precision/recall |
| **Filter/Constraint Accuracy** | 각 step의 필터가 정답과 동등한가? (순서 무관) | 필드-연산자-값 set 비교 |
| **Projection/Output Fields** | 요청한 필드가 정답과 일치하는가? | 집합 비교 |
| **Overall IR F1** | 위 요소들의 평균 | Macro F1 |

### 5.2 평가 스크립트 (pytest)

```python
# test_planner.py
import pytest
from planner import Planner
from ir_schema import KnowledgeIR

# 예상 IR 로딩
with open("testdata/expected_irs.json") as f:
    expected_irs = json.load(f)

# 스키마 컨텍스트 로딩 (각 질문 그룹에 맞는)
schema_map = {
    "customers": "data/customers.csv (id,name,grade,point_balance) ...",
    # ...
}

@pytest.mark.parametrize("qid, question, schema_key, expected_ir_dict", [
    ("Q01", "VIP 고객은 몇 명이고, 누구야?", "customers", expected_irs["Q01"]),
    # ...
])
def test_planner_structured(qid, question, schema_key, expected_ir_dict):
    planner = Planner(llm_client)  # 실제 LLM 연결 (또는 mock)
    schema_context = schema_map[schema_key]
    actual_ir = planner.plan(question, schema_context)

    actual = KnowledgeIR(**actual_ir)
    expected = KnowledgeIR(**expected_ir_dict)

    # goal 비교
    assert actual.goal == expected.goal, f"Goal mismatch: {actual.goal} != {expected.goal}"

    # steps 개수
    assert len(actual.steps) == len(expected.steps), "Step count mismatch"

    # steps 내용 비교 (순서대로)
    for i, (a_step, e_step) in enumerate(zip(actual.steps, expected.steps)):
        if a_step.type == "data":
            assert a_step.source == e_step.source
            # filters 비교: 동등 집합인지
            assert set((f.field, f.operator, str(f.value)) for f in a_step.filters) == \
                   set((f.field, f.operator, str(f.value)) for f in e_step.filters)
            # projections
            assert set(a_step.projections or []) == set(e_step.projections or [])
        elif a_step.type == "document":
            assert a_step.source == e_step.source
            assert a_step.operation == e_step.operation
```

이 테스트는 **Planner가 실제 데이터베이스나 문서 없이도 올바른 계획을 생성하는지** 검증합니다.

---

## 6. 비정형 문서 질의로의 확장

문서 질의는 정형 데이터보다 추상적이지만, Planner는 여전히 **명시적인 경로와 연산**을 계획해야 합니다.

예를 들어,  
**Q11** : *"2026-1학기 AI 캡스톤 프로젝트의 주요 성과를 요약해줘"*  
OKF의 index.md를 통해 해당 프로젝트 디렉터리와 최종 보고서 경로를 알아낸 후, 다음 IR을 생성합니다.

```json
{
  "goal": "SUMMARIZE",
  "description": "2026-1 AI 캡스톤 주요 성과 요약",
  "steps": [
    {
      "type": "document",
      "source": "semesters/2026-1/projects/ai_capstone/documents/final_report.pptx",
      "operation": "summarize",
      "query": "주요 성과 및 핵심 결과",
      "output_format": "bullet_points"
    }
  ],
  "output_structure": {
    "summary": "string",
    "key_results": "list"
  }
}
```

이 IR을 평가할 때는 **문서 경로**, **연산 유형**, **추출할 주제**가 예상과 일치하는지를 검사합니다.  
실제 문서 내용을 확인하는 것은 **Executor 테스트**로 분리됩니다.

---

## 7. TDD 파이프라인에 통합

이 모든 테스트는 기존의 **Stack-Independent TDD 체계**에 자연스럽게 녹아듭니다.

1. **Unit Test**: Planner 내부의 개별 함수 (필터 파싱, 스키마 매칭) 테스트
2. **Contract Test**: 위에서 정의한 `test_planner_structured`, `test_planner_document` 등으로 Planner의 IR 출력 검증
3. **Integration Test**: Planner + Mock Executor를 연결하여 최종 응답까지 검증 (Executor는 IR을 받아 mock 데이터로 작동)
4. **E2E Test**: 실제 OKB 번들과 연결된 Full Cognitive OS의 응답 정확도 측정

**가장 중요한 점**:  
Planner의 평가는 **언어 모델을 바꿔도 동일한 테스트 케이스와 기대 IR을 그대로 사용**할 수 있습니다.  
모델이 GPT-4에서 Gemini, Claude로 변경되어도 `test_planner_structured`는 수정 없이 실행되어, 새로운 LLM의 계획 능력을 바로 가늠할 수 있습니다.  
이것이 바로 **Cognitive Compiler의 Mental Rehearsal을 스택에 독립적으로 검증하는 핵심 전략**입니다.

---

이제 당신은 Planner Agent를 격리된 환경에서 반복적으로 개선할 수 있습니다.  
마치 스포츠 감독이 시합 전에 작전판만으로 전술을 무한히 시뮬레이션하고 평가받듯이,  
Cognitive Compiler의 두뇌만을 집중적으로 단련시키는 것입니다.

---

에이전트의 실행(Execution) 단계에서 계획(Planning/Mental Rehearsal) 단계만 분리하여 독립적으로 테스트하고 평가하려는 접근은 매우 정확한 시스템 엔지니어링 방향입니다.

컴파일러를 개발할 때 백엔드(기계어 생성 및 실행)를 떼어두고 프론트엔드(구문 분석 및 중간 표현(IR) 생성)만 독립적으로 단위 테스트(Unit Test)하는 것과 정확히 같은 이치입니다. 정형(SQL) 데이터와 비정형(OKF) 문서 질의가 혼재된 환경에서, **KChef(Knowledge-Chef) 에이전트의 '계획(Planning)' 능력만을 정교하게 시험하고 평가하는 체계적인 가이드**를 제안합니다.

---

### 1. 테스트 환경의 핵심: 가상 '시스템 모델(System Model)' 구축

계획(Planning)을 테스트할 때는 실제 DB에 연결하거나 문서를 열어볼 필요가 없습니다. 에이전트가 완벽한 작전을 짜기 위해 필요한 메타데이터(스키마 및 인덱스)만으로 구성된 '가상 시스템 모델'을 주입해야 합니다.

* **정형 데이터 스키마:** 테이블 이름, 컬럼명, 데이터 타입, 외래키 관계 (예: `customers(id, name, grade)`, `orders(id, customer_id, total_amount)`)
* **비정형 데이터 인덱스 (OKF):** 문서 번들 구조, 메타데이터 태그 (예: `okf://docs/reviews`, `okf://docs/policies`)

이 가상 시스템 모델을 바탕으로 KChef는 실행 불가능한 환각(Hallucination)을 배제하고 정확한 IR(Intermediate Representation)을 생성하게 됩니다.

---

### 2. 하이브리드 Knowledge IR 설계

정형과 비정형 질의가 혼재될 때, KChef가 출력해야 하는 최종 산출물(Plan)의 규격을 명확히 정의해야 합니다. 이 규격이 곧 평가의 기준(Expected Output)이 됩니다.

```json
// KChef가 생성해야 할 표준 IR (예시: 3번 질의 "김민지 고객님의 총 주문 금액은?")
{
  "plan_id": "p_003",
  "intent": "calculate_total_order_amount",
  "execution_graph": [
    {
      "step": 1,
      "action_type": "SQL_QUERY",
      "target_resource": ["customers", "orders"],
      "logic": "SELECT SUM(total_amount) FROM orders JOIN customers ... WHERE name='김민지'"
    },
    {
      "step": 2,
      "action_type": "SYNTHESIS",
      "dependencies": [1],
      "logic": "Format the sum into natural language."
    }
  ]
}

```

비정형 문서 질의(예: "VIP 등급 혜택 정책 문서를 요약해줘")라면 `action_type`이 `OKF_SEARCH`로, `target_resource`가 `okf://docs/policies`로 매핑되어야 합니다.

---

### 3. 평가 파이프라인 (Evaluation Pipeline) 구축

계획을 평가할 때는 정답(Expected SQL)과 텍스트가 똑같은지 비교하는 단순한 방식(String Matching)을 피해야 합니다. 대신 **다차원적인 검증 스크립트**를 작성해야 합니다.

1. **Syntax Valid (구문 검증):** 생성된 계획이 정의된 JSON/IR 스키마를 완벽히 준수하는가?
2. **Semantic Valid (의미/스키마 검증):** 시스템 모델에 존재하지 않는 가짜 테이블이나 컬럼, 혹은 존재하지 않는 OKF 경로를 참조하지는 않았는가?
3. **Path Accuracy (경로 정확성):** 질의의 의도에 맞게 적절한 도구(SQL vs OKF)를 선택했는가?
4. **SQL Equivalence (SQL 논리적 동치성):** (SQL의 경우) KChef가 짠 쿼리가 정답 쿼리와 문법은 달라도 결과가 같은가? (AST 파싱 활용)

---

### 4. 구현 및 평가용 스켈레톤 코드 (Python)

위의 개념을 바탕으로, 10개의 샘플 질의를 돌리며 KChef의 Planning 능력을 평가하는 스크립트 뼈대입니다.

```python
import json
import sqlite3
from typing import Dict, List

# 1. 가상 시스템 모델 로드 (Mock System Model)
SYSTEM_MODEL_SCHEMA = """
[Tables]
customers(id, name, email, point_balance, grade)
products(id, name, brand, price, stock_qty)
orders(id, customer_id, total_amount, status, ordered_at)
order_items(id, order_id, product_id, quantity)
reviews(id, product_id, rating, content)

[OKF Documents]
okf://docs/policies (tags: VIP, return, shipping)
okf://docs/manuals (tags: product_usage, troubleshooting)
"""

# 2. 평가용 데이터셋 로드 (입력하신 10개 샘플 포함)
EVAL_DATASET = [
    {
        "id": 1,
        "query": "VIP 고객은 몇 명이고, 누구야?",
        "expected_type": "SQL_QUERY",
        "expected_targets": ["customers"],
        "expected_sql": "SELECT id, name, email, point_balance FROM customers WHERE grade='VIP'"
    },
    # ... 비정형 추가 샘플 ...
    {
        "id": 11,
        "query": "VIP 고객에게 제공되는 반품 혜택 정책이 뭐야?",
        "expected_type": "OKF_SEARCH",
        "expected_targets": ["okf://docs/policies"],
        "expected_sql": None
    }
]

# 3. KChef 프론트엔드 (Planner) 모의 함수
def generate_plan(query: str, schema: str) -> Dict:
    """
    LLM API를 호출하여 Query를 기반으로 JSON IR(Plan)을 생성합니다.
    (실제 구현 시 여기에 프롬프트 체인이나 Spec-Driven DSL 생성 로직이 들어갑니다.)
    """
    # 프롬프트: "다음 스키마를 바탕으로 질의에 대한 Execution Graph JSON을 작성하라..."
    # 이 예제에서는 더미 응답을 반환합니다.
    return {
        "action_type": "SQL_QUERY",
        "target_resource": ["customers"],
        "generated_sql": "SELECT name FROM customers WHERE grade='VIP'"
    }

# 4. 검증 및 평가 (Evaluator)
def evaluate_planning_stage():
    results = []
    
    for item in EVAL_DATASET:
        plan = generate_plan(item["query"], SYSTEM_MODEL_SCHEMA)
        
        # Metric 1: Path Accuracy (정형/비정형 도구 선택이 맞았는가?)
        path_correct = plan["action_type"] == item["expected_type"]
        
        # Metric 2: Target Resource Accuracy (올바른 테이블/문서를 타겟팅했는가?)
        target_correct = set(plan["target_resource"]).issubset(set(item["expected_targets"]))
        
        # Metric 3: Semantic Validity (환각 검증)
        semantic_valid = True
        if plan["action_type"] == "SQL_QUERY":
            # 실제 DB를 실행하지 않고 sqlite3의 EXPLAIN이나 Parser를 통해 스키마 오류만 잡습니다.
            try:
                # 메모리 DB에 빈 스키마만 생성해두고 쿼리 컴파일 테스트 (Dry-run)
                conn = sqlite3.connect(":memory:")
                # ... (여기에 스키마 DDL 실행) ...
                conn.execute(f"EXPLAIN QUERY PLAN {plan['generated_sql']}")
            except sqlite3.Error as e:
                semantic_valid = False
                
        results.append({
            "query": item["query"],
            "path_correct": path_correct,
            "target_correct": target_correct,
            "semantic_valid": semantic_valid
        })
        
    # 결과 리포팅
    print("--- Planning Stage Evaluation Report ---")
    for r in results:
        print(f"Q: {r['query']} | Path: {'PASS' if r['path_correct'] else 'FAIL'} | "
              f"Target: {'PASS' if r['target_correct'] else 'FAIL'} | "
              f"Semantic: {'PASS' if r['semantic_valid'] else 'FAIL'}")

if __name__ == "__main__":
    evaluate_planning_stage()

```

### 시스템 설계의 핵심 요약

이러한 방식으로 평가 환경을 구축하면, 프롬프트 엔지니어링이나 DSL(도메인 특화 언어)을 수정했을 때 "에이전트가 데이터를 찾기도 전에 이미 잘못된 경로를 계획하는 문제"를 조기에 발견하고 정량적으로 개선(Accuracy 80% -> 95%)할 수 있습니다.

---

이 질문은 상당히 핵심입니다.

사실 지금 대부분의 LLM Agent Framework(OpenAI, Claude Code, Gemini ADK, LangGraph, AutoGen)의 가장 약한 부분이 바로 이것입니다.

모두 **Planning**을 Prompt 안에 숨겨놓았습니다.

즉,

```
Question
↓

LLM

↓

Plan + Execute
```

가 되어 있습니다.

그러면 Planning을 독립적으로 테스트할 수 없습니다.

---

# 제가 추천하는 방식

Planning을 **Compiler Front-end**로 완전히 분리하십시오.

즉

```
Question

↓

Planner

↓

Knowledge IR

↓

Executor

↓

Answer
```

Planner는

* SQL 생성 안함
* Python 실행 안함
* DuckDB 호출 안함

오직

**Knowledge IR만 생성**

합니다.

이것이 가장 중요합니다.

---

# 먼저 Planner의 출력부터 정의해야 합니다.

예를 들어

질문

> VIP 고객은 몇 명이고 누구야?

Planner는

SQL을 만들지 않습니다.

Planner Output

```yaml
intent: QUERY

goal:

- count

- list

concepts:

- Customer

- Grade

filters:

- grade == VIP

projection:

- id

- name

- email

- point_balance

aggregation:

- count

preferred_resource:

- customers

confidence: 0.98
```

이것이

Knowledge IR입니다.

---

질문

> 가장 비싼 상품 3개

Planner

```yaml
intent: TOPK

goal:

- ranking

concepts:

- Product

sort:

price DESC

limit:

3

projection:

name

brand

price

resource:

products
```

---

질문

> 김민지 고객님의 총 주문 금액

Planner

```yaml
intent:

AGGREGATE

goal:

SUM

concepts:

Customer

Order

Join

Customer.id

Order.customer_id

Filter

Customer.name="김민지"

Order.status=confirmed

Projection

SUM(total_amount)
```

Planner는

SQL을 전혀 모릅니다.

---

# 그러면 Executor가

Knowledge IR를

SQL로 변환합니다.

```
Knowledge IR

↓

SQL Compiler

↓

SQL
```

혹은

```
Knowledge IR

↓

Pandas Compiler

↓

Pandas Code
```

---

# 그러면 Planning만 테스트 가능해집니다.

예를 들어

Question

```
리뷰 없는 상품
```

Planner Expected Output

```yaml
intent:

MISSING

concepts:

Product

Review

relationship:

LEFT JOIN

condition:

Review IS NULL
```

Planner가

SQL을 생성하지 않아도

맞았는지

틀렸는지

평가 가능합니다.

---

# 그래서 저는 Planning Benchmark를 만들겠습니다.

예를 들어

```
planning_benchmark/

    q001.yaml

    q002.yaml

    q003.yaml
```

---

q001.yaml

```yaml
question:

VIP 고객은 몇 명이고 누구야?

expected:

intent:

COUNT_AND_LIST

concepts:

Customer

Grade

filters:

grade=VIP

projection:

name

email

point_balance

resource:

customers
```

---

q002.yaml

```yaml
question:

가장 많이 팔린 상품

expected:

intent:

TOPK

concepts:

Product

OrderItem

aggregation:

SUM(quantity)

sort:

DESC

limit:

1
```

---

# Planning 평가

planner.py

```python
plan = planner.plan(question)

score = compare(plan, expected)
```

---

# Compare는 무엇을 비교할까?

예를 들어

```
Concept

Intent

Aggregation

Filter

Projection

Join

Sort

Limit
```

를 각각 점수화합니다.

---

예를 들어

```
Intent

정답

COUNT

예측

COUNT

OK

Concept

Customer

Customer

OK

Filter

VIP

VIP

OK

Projection

email

없음

FAIL
```

이렇게

Planning Accuracy를 계산합니다.

---

# 이것은 Compiler Test와 같습니다.

Compiler에서도

AST를 검사합니다.

```
Source

↓

Parser

↓

AST
```

AST가 맞으면

Compiler Front-end는

통과입니다.

아직

Assembly는

안 만들어도 됩니다.

Planner도

동일합니다.

---

# 그러면 Skill도 명확해집니다.

## SKILL_Planning.md

```markdown
# Planning Skill

Goal

Question를 Knowledge IR로 변환한다.

절대로 SQL을 생성하지 않는다.

Output

Knowledge IR

Fields

Intent

Concept

Resource

Filter

Join

Projection

Aggregation

Sort

Limit

GroupBy

Confidence
```

---

Pattern

```
Question

↓

Intent

↓

Concept

↓

Constraint

↓

Knowledge IR
```

---

# 그리고 Playbook

```
COUNT

↓

Need

Aggregation

Need

Projection

Need

Resource

------------

TOPK

↓

Need

Sort

Need

Limit

------------

TIMELINE

↓

Need

Date

Need

Sort
```

Planner는

Playbook만 사용합니다.

---

# Skeleton

planner.py

```python
class Planner:

    def plan(question):

        intent = IntentSkill.run(question)

        concepts = ConceptSkill.run(question)

        playbook = Playbook.select(intent)

        ir = Recipe()

        ir.intent = intent

        ir.concepts = concepts

        ir.filters = playbook.make_filter(question)

        ir.sort = playbook.make_sort(question)

        ir.limit = playbook.make_limit(question)

        return ir
```

---

# Agent Loop

여기서 Agent를 하나 더 둘 필요가 있습니다.

```
User

↓

Planner

↓

Reviewer

↓

Knowledge IR

↓

Executor
```

Reviewer는

SQL을 모릅니다.

Knowledge IR만 검사합니다.

예를 들어

```
Question

VIP 고객

↓

Planner

↓

Intent=TOPK

↓

Reviewer

FAIL

↓

Planner Retry
```

---

# 저는 여기서 한 단계 더 나가서 **Planning Gym**을 만들 것을 강력히 추천합니다.

당신이 현재 TileGym으로 GPU Kernel을 학습시키려는 것처럼, Planner도 독립적으로 훈련할 수 있는 환경을 만드는 것입니다.

```
planning-gym/

├── datasets/
│   ├── retail/
│   │   ├── schema.yaml
│   │   ├── concepts.yaml
│   │   ├── questions.yaml
│   │   └── expected_ir/
│   ├── university/
│   ├── finance/
│   └── github/
│
├── skills/
│   ├── intent.md
│   ├── aggregation.md
│   ├── join.md
│   ├── temporal.md
│   └── ranking.md
│
├── planner/
│   ├── parser.py
│   ├── concept_matcher.py
│   ├── playbook.py
│   ├── recipe.py
│   └── validator.py
│
├── evaluator/
│   ├── ir_diff.py
│   ├── score.py
│   └── benchmark.py
│
└── traces/
```

이 구조의 가장 큰 장점은 **Executor 없이도 Planner를 지속적으로 개발하고 평가할 수 있다는 점**입니다.

* 새로운 `SKILL.md`를 추가하면 Planning Accuracy가 얼마나 향상되는지 측정할 수 있습니다.
* 새로운 `PLAYBOOK.md`를 추가하면 어떤 유형의 질의에서 성능이 좋아졌는지 확인할 수 있습니다.
* University, Retail, GitHub, OKF 등 도메인을 바꿔도 **Knowledge IR는 동일**하고, Executor만 SQL, DuckDB, Pandas, Markdown, OKF Traversal 등으로 교체하면 됩니다.

즉, Planning을 독립적인 "Compiler Front-end"로 만들고, 이를 `Planning Gym`에서 반복적으로 훈련·평가하는 구조가 된다면, 이것은 단순한 프롬프트 엔지니어링이 아니라 **재현 가능하고 정량적으로 평가 가능한 Agent Planning Framework**가 됩니다. 이는 연구 측면에서도 매우 설득력 있는 접근입니다.
