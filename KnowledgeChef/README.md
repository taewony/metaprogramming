# KChef (Knowledge and Data Query Engine)

> A Cognive Knowledge Operating System(CKOS) for Structured Data, Documents, and Agentic Semantic Query Execution

KChef는 **OpenKB**를 핵심 지식 엔진으로 활용하여 사용자의 자연어 질문을 해석하고, OKF(Open Knowledge Format) 기반의 지식 카탈로그와 SQLite 데이터베이스를 통합적으로 조회하는 시스템입니다.

---

## Why KChef?

대부분의 AI 시스템은 다음 두 가지 중 하나에 속합니다:

1. **Text-to-SQL** — 자연어를 SQL로 변환하지만 비즈니스 의미를 이해하지 못함
2. **RAG (Retrieval-Augmented Generation)** — 문서를 검색하지만 정형 데이터와 연결하지 못함

사용자가 묻습니다:

> "올해 VIP 고객 성장률이 어떻게 되나요?"

하지만 데이터베이스는 오직 다음만 알고 있습니다:

```sql
customers.total_purchase > 1000000
```

**누락된 계층은 의미(Semantics)입니다.**

KChef는 OKF(Open Knowledge Format)와 OpenKB를 기반으로 한 **의미 계층(Semantic Layer)** 을 도입하여 이 문제를 해결합니다.

```
User Question
      ↓
   OpenKB (OKF Wiki)
      ↓
Query Planner (확장)
      ↓
SQLite + 문서 검색
      ↓
     Answer
```

---

## Architecture Overview

```mermaid
flowchart TD
    USER["User"]
    OKB["OpenKB Engine"]
    CAT["OKF Knowledge Catalog"]
    PLAN["Query Planner (확장)"]
    SQL["SQL Agent"]
    RAG["RAG Agent"]
    SYN["Response Synthesizer"]
    DB[("SQLite")]
    VDB[("Vector DB")]

    USER --> OKB
    OKB --> CAT
    CAT --> PLAN
    PLAN --> SQL
    PLAN --> RAG
    SQL --> DB
    RAG --> VDB
    SQL --> SYN
    RAG --> SYN
    SYN --> USER
```

### OpenKB를 통한 OKF 기반 지식 계층

OpenKB는 **OKF(Open Knowledge Format)를 공식 지원**하는 오픈소스 CLI 도구로, 문서를 LLM으로 컴파일해 구조화되고 상호 연결된 위키 스타일의 지식 베이스를 구축합니다.

```bash
# OpenKB 초기화
$ openkb init

# 문서 추가 (자동 OKF 변환)
$ openkb add docs/sales_report.pdf

# 질의
$ openkb query "VIP 고객 정의가 무엇인가요?"

# 문서 수정 시 위키 다시 컴파일
$ openkb recompile

```

---

## Core Concepts

### 1. OKF Knowledge Catalog (OpenKB 기반)

OpenKB가 생성하는 `wiki/` 디렉토리는 OKF 명세를 준수합니다:

```
wiki/
├── index.md                      # 루트 페이지 (OKF 번들)
├── concepts/
│   ├── vip_customer.md           # type: BusinessRule
│   ├── active_customer.md        # type: BusinessRule
│   └── churn_risk.md             # type: BusinessRule
├── entities/
│   ├── customer.md               # type: Entity
│   ├── order.md                  # type: Entity
│   └── product.md                # type: Entity
├── metrics/
│   ├── monthly_sales.md          # type: Metric
│   └── retention_rate.md         # type: Metric
└── glossary.md                   # type: Glossary
```

**예시: VIP 고객 정의 (`concepts/vip_customer.md`)**

```yaml
---
type: BusinessRule
title: VIP 고객 정의
description: 연간 총 구매 금액이 100만원을 초과하는 고객
tags: [segmentation, vip, kpi]
---
# VIP 고객

## 정의
`total_purchase > 1000000`

## SQL 매핑
```sql
WHERE total_purchase > 1000000
```

## 관련 엔티티
- [Customer](/entities/customer.md)
- [Order](/entities/order.md)

## 관련 메트릭
- [VIP 고객 수](/metrics/retention.md)
- [VIP 매출 비중](/metrics/sales.md)
```

### 2. 확장된 Query Planner

OpenKB의 `query` 기능을 확장하여 **SQLite 데이터 조회**를 통합합니다:

```yaml
plan:
  - step: openkb_query
    action: "VIP 고객 정의 조회"
    output: vip_definition
  - step: resolve_sql
    action: "SQL 변환"
    mapping: "total_purchase > 1000000"
  - step: execute_sql
    target: sqlite:///data/ecommerce.db
    query: "SELECT COUNT(*) FROM customers WHERE total_purchase > 1000000"
  - step: synthesize
    action: "OpenKB 답변에 SQL 결과 통합"
```

### 3. Multi-Hop Query Execution

복잡한 질문은 여러 단계의 추론이 필요합니다:

**질문:**
> "올해 VIP 고객 성장률을 작년과 비교해줘"

**실행 계획:**

1. OpenKB에서 VIP 정의 조회 → `total_purchase > 1000000`
2. SQLite 2025년 VIP 고객 수 조회
3. SQLite 2026년 VIP 고객 수 조회
4. 성장률 계산
5. OpenKB 답변 스타일로 결과 합성

---

## System Architecture (상세)

```mermaid
flowchart TD
    subgraph Client
        UI["Web Dashboard"]
        CLI["CLI"]
    end

    subgraph OpenKB_Core
        OKB["OpenKB Engine"]
        WIKI["OKF Wiki Store"]
        COMP["Document Compiler"]
        INDEX["PageIndex"]
    end

    subgraph KChef_Extension
        PLAN["Query Planner (확장)"]
        SQL["SQL Agent"]
        RAG["RAG Agent"]
        SYN["Response Synthesizer"]
    end

    subgraph Storage
        DB[("SQLite")]
        VDB[("Vector DB")]
    end

    UI --> OKB
    CLI --> OKB
    OKB --> WIKI
    OKB --> PLAN
    PLAN --> SQL
    PLAN --> RAG
    SQL --> DB
    RAG --> VDB
    SQL --> SYN
    RAG --> SYN
    COMP --> WIKI
    INDEX --> WIKI
```

---

## Query Flow (OpenKB + SQLite 통합)

```mermaid
sequenceDiagram
    actor User
    participant OKB as OpenKB
    participant Plan as Query Planner
    participant SQL as SQL Agent
    participant Syn as Synthesizer

    User->>OKB: "VIP 고객의 평균 구매액은?"
    OKB->>Plan: 질의 + OKF 컨텍스트 전달
    Plan->>OKB: VIP 정의 조회 (openkb query)
    OKB-->>Plan: "total_purchase > 1000000"
    Plan->>SQL: SQL 생성 요청
    SQL->>SQL: SELECT AVG(total_purchase) ...
    SQL->>DB: SQL 실행
    DB-->>SQL: 결과 (1,253,000)
    SQL-->>Plan: 데이터 반환
    Plan->>Syn: 결과 + OKF 컨텍스트
    Syn-->>User: "VIP 고객 평균 구매액은 1,253,000원입니다."
```

---

## Implementation Guide: OpenKB + KChef 확장

### 1. OpenKB 설치 및 초기화

```bash
# OpenKB 설치
pip install openkb

# 프로젝트 초기화
openkb init
```

### 2. OKF Knowledge Catalog 구축

```bash
# 문서 추가 (자동 OKF 변환)
openkb add docs/vip_policy.md
openkb add docs/sales_metrics.pdf
openkb add docs/customer_segments.docx

# 소스 문서 수정 시 OKF 재컴파일
openkb recompile
```

### 3. KChef 확장 구현

```python
# kchef_engine.py

import subprocess
import sqlite3
import json
from typing import Dict, Any

class KChefEngine:
    def __init__(self, db_path: str, wiki_path: str = "./wiki"):
        self.db_path = db_path
        self.wiki_path = wiki_path

    def openkb_query(self, question: str) -> str:
        """OpenKB에 질의하여 OKF 개념 조회"""
        result = subprocess.run(
            ["openkb", "query", question],
            capture_output=True,
            text=True
        )
        return result.stdout

    def execute_sql(self, sql: str) -> list:
        """SQLite에 SQL 실행"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return results

    def plan_and_execute(self, question: str) -> Dict[str, Any]:
        """
        1. OpenKB에서 관련 개념 조회
        2. SQL 생성 (LLM)
        3. SQL 실행
        4. 결과 합성
        """
        # Step 1: OKF 개념 조회
        context = self.openkb_query(question)

        # Step 2: SQL 생성 (LLM 호출)
        sql = self._generate_sql(question, context)

        # Step 3: SQL 실행
        data = self.execute_sql(sql)

        # Step 4: 결과 합성 (OpenKB 답변 스타일 적용)
        answer = self._synthesize(question, data, context)

        return {
            "answer": answer,
            "sql": sql,
            "data": data,
            "context": context
        }
```

### 4. CLI 인터페이스

```bash
# kchef CLI 명령어
$ kchef query "VIP 고객의 최근 3개월 평균 구매액은?"

출력:
📊 질의 결과:
- VIP 고객 정의: total_purchase > 1000000
- 실행된 SQL: SELECT AVG(total_purchase) ...
- 결과: 1,253,000원

💡 답변: VIP 고객(연간 구매 100만원 이상)의 최근 3개월 평균 구매액은 1,253,000원입니다.
```

---

## Repository Structure

```
KnowledgeChef/
├── README.md
├── requirements.txt
├── setup.py
├── KChef/
│   ├── __init__.py
│   ├── engine.py          # KChef 메인 엔진
│   ├── planner.py         # Query Planner
│   ├── sql_agent.py       # SQL 생성/실행
│   ├── synthesizer.py     # 응답 합성
│   └── openkb_wrapper.py  # OpenKB API 래퍼
├── brain/                  # OpenKB OKF 위키
│   ├── index.md
│   ├── concepts/
│   ├── entities/
│   ├── metrics/
│   └── glossary.md
├── data/
│   └── ecommerce.db       # SQLite 데이터베이스
├── docs/                  # 원본 문서 (OpenKB 컴파일 전)
├── tests/
│   ├── test_queries/
│   └── test_sql/
├── cli.py                 # CLI 진입점
└── web/
    └── app.py             # Web Dashboard (Streamlit)
```

---

## Text-to-SQL 확장: OKF 기반 SQL 생성

OpenKB의 OKF 지식을 활용하여 SQL을 생성하는 핵심 로직:

```python
# sql_agent.py

def generate_sql(question: str, okf_context: str) -> str:
    """
    OKF 컨텍스트를 활용한 SQL 생성
    """
    prompt = f"""
    다음 OKF 지식을 참고하여 SQLite 쿼리를 생성하세요.

    [OKF 지식]
    {okf_context}

    [사용자 질문]
    {question}

    [SQLite 스키마]
    - customers: id, name, email, total_purchase, order_count, join_date
    - orders: id, customer_id, order_date, total_amount
    - order_items: id, order_id, product_id, quantity, price
    - products: id, product_name, category, price

    SQL만 출력하세요 (설명 없이):
    """

    # LLM 호출 (Gemini, Qwen 등)
    sql = llm_generate(prompt)
    return sql
```

---

## Supported LLM Providers

| Provider | Status | OpenKB 지원 |
|----------|--------|-------------|
| Gemini   | ✅     | ✅          |
| Claude   | ✅     | ✅          |
| Qwen 2.5 | ✅     | ✅          |
| OpenAI   | Planned | Planned   |

---

## Roadmap

### Phase 1: OpenKB 통합 (1주)
- [ ] OpenKB 설치 및 기본 CLI 테스트
- [ ] OKF 위키 초기 구축 (샘플 데이터)
- [ ] `openkb query` 연동 테스트

### Phase 2: SQLite 연동 (1-2주)
- [ ] SQL Agent 구현 (SQL 생성 + 실행)
- [ ] OKF → SQL 매핑 로직 구현
- [ ] 기본 질의-응답 파이프라인 완성

### Phase 3: Query Planner 고도화 (2주)
- [ ] 멀티홉 플래닝 구현
- [ ] OpenKB + SQL 결과 통합 로직
- [ ] RAG Agent 연동

### Phase 4: UI 완성 (1-2주)
- [ ] Web Dashboard (Streamlit)
- [ ] CLI 명령어 완성
- [ ] 평가 프레임워크 구축

---

# KChef (Knowledge and Data Query Engine) — OKF 기반 구현 프로젝트 정의 문서


## 1. 프로젝트 개요

### 1.1 비전

KChef는 사용자의 자연어 질문을 해석하여 정형 데이터베이스(SQLite), 비정형 문서(RAG), 비즈니스 규칙, 지식 카탈로그를 통합적으로 조회하고, Agent 기반 Query Planning 과정을 통해 최종 답변을 생성하는 **Cognitive Knowledge Operating System**이다.

기존 Text-to-SQL 및 RAG 시스템이 '비즈니스 의미'를 이해하지 못하는 문제를 해결하기 위해, OKF(Open Knowledge Format)를 의미 계층(Semantic Layer)으로 도입한다.

### 1.2 핵심 목표

| 목표 | 설명 |
|------|------|
| **의미 기반 질의** | 사용자의 "VIP 고객"이라는 개념을 `total_purchase > 1000000`이라는 SQL 조건으로 자동 변환 |
| **멀티-홉 추론** | "올해 VIP 고객 성장률을 작년과 비교해줘" 같은 복합 질의를 단계별로 계획하고 실행 |
| **벤더 중립성** | OKF를 채택하여 클라우드/DB/에이전트 프레임워크에 종속되지 않는 포터블한 지식 저장소 구축 |
| **자기 진화** | 에이전트가 질의를 수행하며 얻은 인사이트를 OKF 번들에 기록하고, 지식 베이스가 스스로 진화 |


## 2. OKF 기반 Knowledge Catalog 설계

### 2.1 OKF 번들 구조

OKF는 마크다운 파일과 YAML Frontmatter로 구성된 디렉토리 기반 포맷이다.KChef는 다음과 같은 OKF 번들 구조를 채택한다:

```
knowledge/
├── index.md                        # 번들 루트 (진입점)
├── catalog/
│   ├── index.md
│   ├── customer.md                 # type: Entity
│   ├── order.md                    # type: Entity
│   └── product.md                  # type: Entity
├── metrics/
│   ├── index.md
│   ├── sales.md                    # type: MetricGroup
│   ├── retention.md                # type: MetricGroup
│   └── growth.md                   # type: MetricGroup
├── business_rules/
│   ├── index.md
│   ├── vip_customer.md             # type: BusinessRule
│   └── refund_policy.md            # type: BusinessRule
├── glossary/
│   └── domain_terms.md             # type: Glossary
├── prompts/
│   ├── sql_generation.md           # type: PromptTemplate
│   └── answer_style.md             # type: PromptTemplate
├── query_templates/
│   ├── customer_summary.md         # type: QueryTemplate
│   └── sales_trend.md              # type: QueryTemplate
└── log.md                          # 변경 이력
```

### 2.2 OKF Concept 정의 예시

**`catalog/customer.md`** (Entity)
```yaml
---
type: Entity
title: Customer
description: 고객 마스터 정보를 저장하는 테이블
resource: sqlite:///data/ecommerce.db
tags: [core, customer, master]
table: customers
columns:
  customer_id: 고객 식별자 (PK)
  name: 고객명
  email: 이메일
  total_purchase: 누적 구매 금액
  order_count: 총 주문 건수
  join_date: 가입일
---
[Customer](/catalog/customer.md)는 [Order](/catalog/order.md)와 1:N 관계를 가집니다.
```

**`business_rules/vip_customer.md`** (BusinessRule)
```yaml
---
type: BusinessRule
title: VIP 고객 정의
description: 연간 구매 금액이 100만원을 초과하는 고객
applies_to: [Customer]
tags: [segmentation, vip]
---
# VIP 고객 조건

`total_purchase > 1000000`

## SQL 변환
```sql
WHERE total_purchase > 1000000
```

## 관련 메트릭
- [VIP 고객 수](/metrics/retention.md#vip-count)
- [VIP 매출 비중](/metrics/sales.md#vip-share)
```

**`metrics/sales.md`** (MetricGroup)
```yaml
---
type: MetricGroup
title: 매출 메트릭
description: 핵심 매출 지표 정의
tags: [sales, kpi]
---
## 월간 매출 (monthly_sales)
`SUM(total_amount)` WHERE `order_date` BETWEEN month_start AND month_end

## VIP 고객 평균 구매액 (vip_avg_purchase)
`AVG(total_purchase)` WHERE `total_purchase > 1000000`

## 신규 고객 매출 기여도 (new_customer_revenue_share)
`SUM(total_amount)` WHERE `join_date` >= current_month / 전체 매출
```

### 2.3 OKF Consumer (번들 로더)

OKF는 별도의 SDK 없이 표준 라이브러리로 파싱 가능하다. KChef는 다음 함수로 번들을 로드한다:

```python
import pathlib, re, yaml
from typing import Dict, List, Tuple

def load_okf_bundle(root: str) -> Tuple[Dict, List]:
    """
    OKF 번들을 로드하여 concepts와 link graph를 반환.
    - concepts: {path: {type, title, description, tags, ...}}
    - links: [(source_path, target_path), ...]
    """
    concepts, links = {}, []
    for path in pathlib.Path(root).rglob("*.md"):
        text = path.read_text(encoding='utf-8')
        meta = {}
        if text.startswith("---"):
            _, fm, body = text.split("---", 2)
            meta = yaml.safe_load(fm) or {}
        else:
            body = text
        concepts[str(path)] = meta
        # 마크다운 링크 추출로 knowledge graph 구성
        for target in set(re.findall(r"\]\(([^)]+\.md)\)", body)):
            links.append((str(path), target))
    return concepts, links
```


## 3. 시스템 아키텍처 상세

### 3.1 전체 컴포넌트

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Web Dashboard │  │     CLI      │  │   REST API / MCP     │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Core Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Agent Orchestrator                          │  │
│  │  - 질의 수신 및 라우팅  - 세션 관리  - 컨텍스트 관리   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Query Planner                               │  │
│  │  - 질문 분석  - 의도 분류  - 실행 계획 수립            │  │
│  │  - 멀티홉 추론  - Plan 검증                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Response Synthesizer                           │  │
│  │  - 결과 병합  - 자연어 생성  - 인사이트 추출           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Knowledge Layer (OKF)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Catalog    │  │    Metrics   │  │   Business Rules     │ │
│  │  (Entities)  │  │  (Formulas)  │  │   (Definitions)      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Glossary   │  │   Prompts    │  │  Query Templates     │ │
│  │  (Terms)     │  │ (Templates)  │  │   (Patterns)         │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Retrieval Layer                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐   │
│  │    SQL Agent         │  │        RAG Agent             │   │
│  │  - SQL 생성/검증     │  │  - 문서 청킹/임베딩         │   │
│  │  - 쿼리 최적화       │  │  - 벡터 검색                │   │
│  │  - 결과 정형화       │  │  - 문서 요약                │   │
│  └──────────────────────┘  └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   SQLite     │  │  Vector DB   │  │   OKF Repository     │ │
│  │  (ecommerce) │  │ (Chroma/PG)  │  │   (Git managed)      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Query Flow 상세

```mermaid
sequenceDiagram
    actor User
    participant Orch as Agent Orchestrator
    participant Plan as Query Planner
    participant Cat as Knowledge Catalog
    participant SQL as SQL Agent
    participant RAG as RAG Agent
    participant Syn as Synthesizer
    participant Mem as Session Memory

    User->>Orch: "VIP 고객의 최근 3개월 평균 구매액은?"
    Orch->>Plan: 질의 전달 + 세션 컨텍스트
    Plan->>Cat: "VIP" 의미 조회 (OKF 검색)
    Cat-->>Plan: vip_customer.md 반환<br/>(total_purchase > 1000000)
    Plan->>Plan: 실행 계획 수립
    Note over Plan: 1. VIP 정의 로드<br/>2. SQL 생성<br/>3. SQL 실행<br/>4. 결과 집계<br/>5. 답변 생성
    Plan->>SQL: SQL 생성 요청<br/>(VIP 조건 포함)
    SQL->>SQL: SQL 생성 (LLM)
    SQL->>SQL: SQL 검증 (문법/보안)
    SQL->>DB: SELECT AVG(total_purchase) ...
    DB-->>SQL: 결과 (1,253,000)
    SQL-->>Plan: 정형 데이터 반환
    Plan->>Syn: 결과 + 컨텍스트 전달
    Syn-->>User: "VIP 고객의 최근 3개월 평균 구매액은 1,253,000원입니다."
    Plan->>Mem: 실행 이력 저장 (OKF log.md)
```

### 3.3 Hermes OKF 연동 구조

`hermes-okf`를 KChef의 **세션 메모리 및 의사결정 기록 레이어**로 활용:

| 레이어 | 역할 | OKF 연동 방식 |
|--------|------|---------------|
| **Knowledge Catalog** | 비즈니스 개념 정의 | OKF 번들로 저장 (catalog/, metrics/, business_rules/) |
| **Session Memory** | 질의-응답 이력, 의사결정 기록 | `hermes okf log-append`로 OKF log.md에 기록 |
| **Context Provider** | Planner가 참조할 과거 패턴 | `hermes okf search`로 관련 메모리 검색 |
| **Self-Evolution** | 새로운 인사이트를 지식으로 등록 | `hermes okf concept add`로 새 OKF 파일 생성 |


## 4. 질의 처리 파이프라인 상세

### 4.1 3단계 질의 변환 파이프라인

```
[자연어 질의] → [중간 수준 질의] → [SQL/검색 실행] → [자연어 응답]
```

#### 단계 1: 자연어 → 중간 수준 질의 (NL → Intermediate)

LLM이 OKF Knowledge Catalog를 참조하여 사용자 질의를 구조화된 JSON으로 변환:

```json
{
  "intent": "aggregate_query",
  "target_entity": "Customer",
  "metric": "avg_purchase_amount",
  "filters": {
    "segment": "VIP",
    "time_range": "last_3_months"
  },
  "output_format": "natural_language"
}
```

#### 단계 2: 중간 수준 질의 → 실행 (Intermediate → Execution)

Query Planner가 중간 수준 질의를 실행 가능한 작업 그래프로 변환:

```yaml
plan:
  - action: load_okf_concept
    target: "business_rules/vip_customer.md"
  - action: resolve_metric
    metric: "avg_purchase_amount"
    from: "metrics/sales.md"
  - action: generate_sql
    template: "query_templates/customer_avg.sql"
    params:
      condition: "total_purchase > 1000000"
      date_range: "DATE('now','-3 month')"
  - action: execute_sql
    target: "sqlite:///data/ecommerce.db"
  - action: synthesize_answer
    style: "prompts/answer_style.md"
```

#### 단계 3: 실행 결과 → 자연어 응답

Response Synthesizer가 SQL 실행 결과와 RAG 검색 결과를 통합:

```
"VIP 고객(연간 구매 100만원 이상)의 최근 3개월 평균 구매액은 1,253,000원입니다.
이는 전체 고객 평균(320,000원) 대비 291% 높은 수치입니다."
```

### 4.2 멀티홉 질의 예시

**질의**: *"올해 VIP 고객 성장률을 작년과 비교해줘"*

```yaml
plan:
  - action: load_okf_concept
    target: "business_rules/vip_customer.md"
  - action: execute_sql
    query: "SELECT COUNT(*) FROM customers WHERE total_purchase > 1000000 AND strftime('%Y', join_date) = '2025'"
    result_key: "vip_count_2025"
  - action: execute_sql
    query: "SELECT COUNT(*) FROM customers WHERE total_purchase > 1000000 AND strftime('%Y', join_date) = '2026'"
    result_key: "vip_count_2026"
  - action: calculate
    formula: "(vip_count_2026 - vip_count_2025) / vip_count_2025 * 100"
    result_key: "growth_rate"
  - action: synthesize_answer
    template: "VIP 고객 수는 2025년 {vip_count_2025}명에서 2026년 {vip_count_2026}명으로 {growth_rate}% 성장했습니다."
```


## 5. 구현 로드맵

### Phase 1: 기반 인프라 (1-2주)

| Task | 설명 | 산출물 |
|------|------|--------|
| 1.1 | OKF 번들 초기 구조 설계 | `knowledge/` 디렉토리 구조 |
| 1.2 | OKF Loader 구현 | `okf_loader.py` (concepts + graph) |
| 1.3 | SQLite DB 연결 및 스키마 추출 | `db_connector.py` |
| 1.4 | `okf-sqlite` 스킬 연동 | SQLite 스키마 → OKF 변환 파이프라인 |

### Phase 2: 핵심 에이전트 (2-3주)

| Task | 설명 | 산출물 |
|------|------|--------|
| 2.1 | Knowledge Catalog 검색기 | `catalog_search.py` (OKF 기반 개념 조회) |
| 2.2 | Query Planner 기본 구현 | `query_planner.py` (단일 홉) |
| 2.3 | SQL Agent 구현 | `sql_agent.py` (Text-to-SQL + 검증) |
| 2.4 | Response Synthesizer | `synthesizer.py` (결과 → 자연어) |

### Phase 3: 고급 기능 (3-4주)

| Task | 설명 | 산출물 |
|------|------|--------|
| 3.1 | 멀티홉 Query Planner | `multi_hop_planner.py` |
| 3.2 | Hermes OKF 연동 | 세션 메모리 + 의사결정 기록 |
| 3.3 | RAG Agent 연동 | 문서 검색 + OKF 컨텍스트 통합 |
| 3.4 | 중간 수준 질의 인터페이스 | JSON 기반 질의 API |

### Phase 4: 완성 및 최적화 (2-3주)

| Task | 설명 | 산출물 |
|------|------|--------|
| 4.1 | Web Dashboard | Streamlit/Gradio 기반 UI |
| 4.2 | CLI 도구 | `kchef query "..."` 명령어 |
| 4.3 | 평가 프레임워크 | Exact Match, Execution Accuracy, Latency |
| 4.4 | OKF 번들 자동 업데이트 | 에이전트 피드백 기반 지식 진화 |


## 6. 기술 스택

| 계층 | 기술 | 선정 이유 |
|------|------|-----------|
| **LLM** | Qwen 2.5/3.5, Gemini, Claude | README에 명시된 지원 대상 |
| **벡터 DB** | Chroma / SQLite (sqlite-vec) | 경량, SQLite와 통합 용이 |
| **정형 DB** | SQLite | `sql-tutorial` 저장소와 호환 |
| **OKF 처리** | Python + PyYAML + pathlib | 별도 SDK 불필요 |
| **API** | FastAPI | REST API + MCP 서버 지원 |
| **UI** | Streamlit / Gradio | 빠른 프로토타이핑 |
| **CLI** | Click / Typer | 사용자 친화적 명령어 |
| **버전 관리** | Git | OKF 번들 버전 관리 |


## 7. OKF와 기존 접근법 비교

| 비교 항목 | OKF (kchef 채택) | RAG | Text-to-SQL |
|-----------|-----------------|-----|-------------|
| **지식 저장** | 큐레이션된 개념 (마크다운) | 원시 문서 청크 | 없음 (스키마만) |
| **지식 갱신** | Git PR로 버전 관리 | 문서 재임베딩 | 스키마 변경 시 재학습 |
| **크로스링크** | 마크다운 링크로 그래프 형성 | 없음 (벡터 유사도) | 없음 |
| **벤더 종속성** | 없음 (파일 기반) | 임베딩 모델 종속 | DB 방언 종속 |
| **에이전트 가독성** | 즉시 읽기 가능 | 검색 후 청크 해석 필요 | SQL 변환 후 실행 |
| **인간 가독성** | 높음 (마크다운) | 낮음 (청크) | 보통 (SQL) |


## 8. 평가 프레임워크

### 8.1 평가 메트릭

| 메트릭 | 측정 방법 | 목표치 |
|--------|-----------|--------|
| **SQL Execution Accuracy** | 생성된 SQL이 정답 결과 반환 | > 90% |
| **Plan Success Rate** | 멀티홉 Plan이 오류 없이 완료 | > 85% |
| **Latency (P95)** | 질의 → 응답까지 소요 시간 | < 5초 |
| **Token Cost** | 질의당 평균 토큰 사용량 | < 5,000 tokens |
| **OKF Hit Rate** | Knowledge Catalog에서 개념 검색 성공률 | > 95% |

### 8.2 테스트 데이터셋

`sql-tutorial` 저장소의 30개 테이블, 69만 행 데이터를 기반으로 100+ 테스트 질의 구성:

```text
test_queries/
├── simple/
│   ├── q001.md  # "전체 고객 수는?"
│   └── q002.md  # "가장 많이 팔린 제품은?"
├── intermediate/
│   ├── q101.md  # "카테고리별 월간 매출 추이"
│   └── q102.md  # "VIP 고객의 평균 구매 금액"
├── complex/
│   ├── q201.md  # "올해 VIP 성장률 vs 작년"
│   └── q202.md  # "재구매율이 가장 높은 카테고리"
└── expected/
    ├── q101.sql  # 정답 SQL
    └── q101.json # 정답 결과
```

---

KChef가 완성되면 OKF Concept 및 스키마를 기반으로 CSV, SQLite, JSONL 등 다양한 데이터 소스에서 조건에 맞는 데이터를 조회하고 응답을 생성하는 것은 **충분히 가능**합니다. 또한 OpenKB의 구현을 단계적으로 분해해 OKF 중심의 자기 진화형 시스템으로 발전시키는 것도 현실적인 로드맵 위에 있습니다.

### 🔍 OKF 기반 다중 데이터 소스 질의 가능성 분석

KChef의 핵심은 **OKF(Open Knowledge Format)를 표준 인터페이스**로 삼는 것입니다. OKF는 마크다운 파일과 YAML Frontmatter로 구성된 벤더 중립적인 포맷으로, 개념을 정의하고 상호 연결하는 데 최적화되어 있습니다. 이 구조를 활용하면 다양한 데이터 소스에 대한 질의를 추상화할 수 있습니다.

*   **OKF를 통한 데이터 소스 추상화**: OKF의 `Concept`은 특정 데이터 소스(SQLite, CSV, JSONL 등)를 가리키는 `resource` 필드와 실제 데이터를 조회하기 위한 `query` 또는 `schema` 정보를 포함할 수 있습니다. 예를 들어, `customers`라는 개념은 `sqlite:///db.sqlite`의 `customers` 테이블을, `sales_log`는 `s3://bucket/logs/*.jsonl`을 가리키도록 정의할 수 있습니다.
*   **통합 질의 엔진의 역할**: KChef는 사용자의 자연어 질의를 받아 관련 OKF 개념들을 조회하고, 각 개념에 연결된 데이터 소스에 맞는 질의어(SQL, JSONPath, Pandas Query 등)를 생성한 뒤, 결과를 취합해 응답하는 **통합 질의 엔진** 역할을 수행하게 됩니다.
*   **기술적 실현 가능성**: SQLite, CSV, JSONL 등은 모두 Python에서 쉽게 다룰 수 있는 데이터 포맷입니다. OKF의 메타데이터를 파싱해 각 소스에 맞는 Connector를 구현하면, 사용자는 데이터가 어디에 있든 OKF가 정의한 '의미'를 통해 질의할 수 있는 환경이 조성됩니다.

### 🧩 OpenKB 점진적 분해 및 OKF 중심 체계화 전략

OpenKB는 문서를 LLM으로 컴파일해 OKF 위키를 구축하는 '컴파일러'이자 '지식 베이스'입니다. KChef로의 점진적인 통합은 다음 단계로 가능합니다.

*   **1단계: OpenKB를 Knowledge Catalog로 활용**: 현재 상태 그대로 OpenKB를 도입합니다. `openkb add`와 `openkb compile`을 통해 다양한 문서에서 OKF 형식의 위키를 생성하고, `openkb query`로 지식을 조회하는 기능을 KChef의 일부로 사용합니다. 이 단계에서 KChef는 OpenKB 위에 얹혀 동작하는 얇은 래퍼가 됩니다.
*   **2단계: Query Planner를 OpenKB 위에 구현**: `openkb query`가 단순 텍스트 검색에 가깝다면, KChef는 여기에 **의도 분석 및 실행 계획(Query Planning) 기능**을 추가합니다. 예를 들어, "작년 VIP 고객 수는?"이라는 질문에 대해, OpenKB에서 VIP의 정의를 가져오고, SQLite에서 데이터를 조회하는 일련의 계획을 수립하고 실행하는 레이어를 구현합니다.
*   **3단계: Data Connector 계층으로 OpenKB 확장**: OpenKB의 Wiki Foundation을 그대로 두고, **Generator 계층을 확장**해 `query` 기능이 SQLite, CSV 등 다양한 데이터 소스를 직접 조회할 수 있도록 개선합니다. 이로써 OpenKB는 '지식 정의'와 '데이터 조회'를 함께 처리하는 통합 엔진으로 진화합니다.
*   **4단계: OKF 중심의 완전한 재구현**: OKF 스키마와 상호 운용성에 대한 이해가 깊어지면, OpenKB 의존성을 줄이고 OKF를 직접 처리하는 **자체 코어 엔진**으로 전환합니다. 이 단계에서는 OKF의 `Concept` 링크를 따라 데이터 흐름을 오케스트레이션하는 완전한 **Knowledge Operating System**으로 성장할 수 있습니다.

### ♻️ Hermes Memory 및 Skill을 통한 자기 진화 능력 구축

`hermes-okf`를 활용하면 Hermes Agent에 OKF 기반의 **영속적이고 구조화된 메모리**를 부여할 수 있습니다.

*   **Hermes Memory Provider로서의 hermes-okf**: `hermes-okf`는 Hermes Agent의 `MemoryProvider` 추상 클래스를 구현한 플러그인입니다. 이를 통해 에이전트는 세션을 넘어 과거의 의사결정, 관찰, 도구 사용 이력을 OKF 번들 형태로 저장하고 검색할 수 있습니다.
*   **Skill을 통한 행동 숙련화**: Hermes Agent에서 Skill은 에이전트가 특정 작업을 수행하는 방법을 담은 '작업 매뉴얼'입니다. KChef가 특정 유형의 질의(예: 월간 매출 보고서 생성)를 성공적으로 수행할 때마다, 그 과정을 Hermes Skill로 추상화하고 저장할 수 있습니다.
*   **자기 진화의 완성 (Self-Evolution)**: Memory와 Skill이 결합되면 Hermes는 **자기 성찰(Self-Reflection)** 과 **능력 개선(Self-Improvement)** 의 선순환 구조에 돌입합니다. 에이전트는 자신의 실패했던 쿼리 계획을 Memory에서 검토해 개선하고, 성공적인 패턴은 Skill로 체화해 다음에 더 빠르고 정확하게 실행합니다.

### 🗺️ 단계별 통합 로드맵

| 단계 | 주요 작업 | 핵심 결과물 |
| :--- | :--- | :--- |
| **Phase 1** | OpenKB 도입 및 OKF Catalog 구축 | `openkb` CLI로 관리되는 OKF 기반 지식 베이스 |
| **Phase 2** | Query Planner 구현 (OKF + Data Source) | OKF 개념과 SQLite/CSV 등을 연결하는 질의 실행 엔진 |
| **Phase 3** | `hermes-okf` Memory Provider 연동 | Hermes Agent가 OKF 메모리를 읽고 쓰는 환경 |
| **Phase 4** | Hermes Skill Factory 도입 및 Self-Evolution 구현 | 에이전트가 경험을 Skill로 체화하고 스스로 개선하는 루프 |

---

### 💎 종합 결론

KChef가 완성되면 OKF는 단순한 문서 포맷을 넘어 **모든 데이터 소스에 대한 통합 질의의 추상화 계층**이자, **에이전트의 기억과 경험이 축적되는 자기 진화의 기반**이 될 것입니다.

OpenKB는 초기 지식 기반을 빠르게 구축하는 훌륭한 도구이며, `hermes-okf`는 Hermes Agent와의 심층적인 통합을 통해 시스템의 지능을 지속적으로 향상시키는 핵심 동력이 될 것입니다. 두 도구를 KChef의 목표에 맞게 점진적으로 흡수하고 발전시키는 전략은 매우 실현 가능하며, 장기적인 비전을 달성하는 가장 효율적인 경로가 될 것입니다.


---


## 11. 참고 자료

- [OKF 공식 문서 (Google Cloud)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- Andrej Karpathy LLM Wiki Gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- `okf-skills` 저장소 (okf-sqlite): https://github.com/xSAVIKx/okf-skills
- `hermes-okf`: https://github.com/EliaszDev/hermes-okf (경량 메모리 시스템)
- [OpenKB GitHub](https://github.com/vectifyai/openkb)
- [sql-tutorial (테스트 데이터)](https://github.com/civilian7/sql-tutorial)
- https://civilian7.github.io/sql-tutorial/ko/

---

### ⚖️ OpenKB vs. hermes-okf: KChef 관점에서의 비교

| 비교 항목 | OpenKB | hermes-okf |
| :--- | :--- | :--- |
| **🎯 핵심 목적** | **지식 베이스 구축 및 컴파일러**<br>원본 문서를 LLM으로 컴파일해 구조화된 위키(OKF)를 생성하고 유지보수 | **에이전트 전용 메모리 시스템**<br>에이전트의 의사결정, 관찰, 도구 실행 이력 등을 OKF로 저장하고 검색 |
| **📥 입력** | PDF, Word, Excel, URL 등 **다양한 원본 문서** | 에이전트의 **행동 로그** (결정, 관찰, 도구 호출) |
| **📤 출력** | **OKF 형식의 위키** (요약, 개념, 엔티티 페이지, 상호 참조) | **OKF 형식의 메모리 번들** (세션, 결정, 계획, 도구 사용 기록) |
| **⚙️ 작동 방식** | **문서 컴파일 (Compile)**<br>`openkb add` → `openkb compile`로 지식을 **사전에 구축** | **실시간 기록 (Log)**<br>에이전트 실행 중 `@memorize_decision` 데코레이터 등으로 **실시간 저장** |
| **🔍 질의 방식** | **자연어 질의/채팅** (`openkb query`, `openkb chat`) | **검색 및 조회** (`hermes okf search`, `show`, `list`) |
| **🧠 핵심 기술** | **PageIndex**: 벡터 없는 트리 기반 인덱싱으로 장문 문서 검색 | **OKF Bundle**: 파일 기반 Concept CRUD, GraphExtractor, SearchIndex |
| **🔌 Hermes 연동** | **간접적**: `SKILL.md`를 통해 Hermes 같은 Agent CLI가 위키를 읽을 수 있음 | **기본 (Native)**: `HermesOKFMemoryProvider`로 Hermes Memory ABC 구현, `install-plugin`으로 자동 연동 |
| **🤖 KChef에서의 역할** | **Knowledge Catalog (지식 저장소)**<br>비즈니스 규칙, 용어집, 메트릭 정의를 OKF로 관리 | **Session Memory & Decision Log (에이전트 기억)**<br>질의/분석 이력, 의사결정 과정, 실행 계획을 기록하고 참조 |

---

## [appendix] TechLead (Coding Agent) 역할

| 역할 | 인원 | 주요 책임 |
|------|------|-----------|
| **Backend Lead** | 1 | OKF Loader, Query Planner, SQL Agent |
| **LLM Engineer** | 1 | 프롬프트 엔지니어링, 모델 연동 및 평가 |
| **Full-stack Developer** | 1 | Web Dashboard, CLI |
| **Data Engineer** | 1 | SQLite DB 관리, OKF 번들 구축, `okf-sqlite` 연동 |
| **QA Engineer** | 1 | 테스트 데이터셋 구축, 평가 프레임워크 |

---

## 성공 기준 (Success Criteria)

1. ✅ OpenKB 기반 OKF Knowledge Catalog 구축 완료
2. ✅ 자연어 질의 → OKF 개념 조회 → SQL 변환 → 실행 → 응답까지 End-to-End 동작
3. ✅ 멀티홉 질의 (3단계 이상) 처리 성공률 85% 이상
4. ✅ Web Dashboard 및 CLI 데모 완성
5. ✅ 모든 컴포넌트 Docker 기반 배포 가능

1. **OKF 기반 Knowledge Catalog**가 30개 테이블의 모든 비즈니스 개념을 커버
2. **자연어 → 중간 수준 질의 → SQL** 변환 정확도 90% 이상
3. **멀티홉 질의** (3단계 이상) 처리 성공률 85% 이상
4. Web Dashboard와 CLI를 통한 **엔드투엔드 데모** 완성
5. 모든 컴포넌트가 **벤더 종속성 없이** Docker로 배포 가능

---

### 테스트 환경

- Sqlite: 테크샵(TechShop)이라는 가상의 전자상거래 쇼핑몰 데이터베이스
- DB path: D:\sqlite\output\ecommerce-ko.db
- 질의 예시:
  - "30세 이상 VIP 고객 중 이번 달 주문한 사람"
```
sqlite> .tables
_sc_metadata            customers               product_views       v_cart_abandonment      v_product_abc
calendar                inventory_transactions  products            v_category_tree         v_product_performance
cart_items              order_items             promotion_products  v_coupon_effectiveness  v_return_analysis
carts                   orders                  promotions          v_customer_rfm          v_revenue_growth
categories              payments                returns             v_customer_summary      v_staff_workload
complaints              point_transactions      reviews             v_daily_orders          v_supplier_performance
coupon_usage            product_images          shipping            v_hourly_pattern        v_top_products_by_category
coupons                 product_prices          staff               v_monthly_sales         v_yearly_kpi
customer_addresses      product_qna             suppliers           v_order_detail          wishlists
customer_grade_history  product_tags            tags                v_payment_summary
sqlite> .schema customers
CREATE TABLE customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,                    -- email (fictional domain)
    password_hash   TEXT NOT NULL,                           -- SHA-256 hash (fictional)
    name            TEXT NOT NULL,                           -- customer name
    phone           TEXT NOT NULL,                           -- 020-XXXX-XXXX (fictional number)
    birth_date      TEXT NULL,                               -- birth date (YYYY-MM-DD, ~15% NULL)
    gender          TEXT NULL,                               -- M/F (NULL ~10%, male 65%)
    grade           TEXT NOT NULL DEFAULT 'BRONZE' CHECK(grade IN ('BRONZE','SILVER','GOLD','VIP')),
    point_balance   INTEGER NOT NULL DEFAULT 0 CHECK(point_balance >= 0),
    acquisition_channel TEXT NULL,                            -- organic/search_ad/social/referral/direct
    is_active       INTEGER NOT NULL DEFAULT 1,              -- active status (0=deactivated)
    last_login_at   TEXT NULL,                               -- last login (NULL=never logged in)
    created_at      TEXT NOT NULL,                           -- signup date
    updated_at      TEXT NOT NULL
);
CREATE INDEX idx_customers_email ON customers(email);
CREATE TRIGGER trg_customers_updated_at
AFTER UPDATE ON customers
BEGIN
    UPDATE customers SET updated_at = datetime('now') WHERE id = NEW.id;
END;

sqlite> .schema products
CREATE TABLE products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    supplier_id     INTEGER NOT NULL REFERENCES suppliers(id),
    successor_id    INTEGER NULL REFERENCES products(id),   -- next-generation replacement product
    name            TEXT NOT NULL,                           -- product name
    sku             TEXT NOT NULL UNIQUE,                    -- stock keeping unit (e.g. LA-GEN-Samsung-00001)
    brand           TEXT NOT NULL,                           -- brand name
    model_number    TEXT,                                    -- model number
    description     TEXT,                                    -- product description
    specs           TEXT NULL,                               -- JSON product specifications
    price           REAL NOT NULL CHECK(price >= 0),           -- current selling price (KRW)
    cost_price      REAL NOT NULL CHECK(cost_price >= 0),    -- cost price (KRW)
    stock_qty  INTEGER NOT NULL DEFAULT 0,              -- current stock quantity
    weight_grams    INTEGER,                                 -- shipping weight (g)
    is_active       INTEGER NOT NULL DEFAULT 1,              -- on sale flag
    discontinued_at TEXT NULL,                               -- discontinuation date (NULL=active)
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_supplier_id ON products(supplier_id);
CREATE INDEX idx_products_successor_id ON products(successor_id);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_sku ON products(sku);
CREATE TRIGGER trg_product_price_history
AFTER UPDATE OF price ON products
WHEN OLD.price != NEW.price
BEGIN
    -- Close existing history record
    UPDATE product_prices
    SET ended_at = datetime('now')
    WHERE product_id = NEW.id AND ended_at IS NULL;

    -- Insert new history record
    INSERT INTO product_prices (product_id, price, started_at, ended_at, change_reason)
    VALUES (NEW.id, NEW.price, datetime('now'), NULL, 'price_update');
END;
CREATE TRIGGER trg_products_updated_at
AFTER UPDATE ON products
BEGIN
    UPDATE products SET updated_at = datetime('now') WHERE id = NEW.id;
END;
```

---

## 1. agentic-stack이 전용 Agent 구현에 도움이 될까?

**결론부터 말씀드리면, agentic-stack은 전용 Agent의 '뼈대'와 '지식/메모리 관리' 측면에서 매우 유용하지만, Multi-user 서비스로 확장하려면 상당한 추가 개발이 필요합니다.**

### ✅ agentic-stack의 강점 (활용 가능한 부분)

| 기능 | 설명 | 전용 Agent에서의 활용 |
|------|------|----------------------|
| **포터블 `.agent/` 브레인** | 메모리(working/episodic/semantic/personal), 스킬, 프로토콜을 하나의 폴더에 담아 다양한 코딩 에이전트(Claude Code, Cursor, Hermes, Codex 등)와 공유 | 지식 베이스와 에이전트 설정을 표준화된 구조로 관리할 수 있어, 로컬 LLM 기반 에이전트도 동일한 인터페이스로 지식을 읽고 쓸 수 있음 |
| **외부 Brain 통합 (v0.18.0)** | `codejunkie99/brain`이라는 Git-backed 장기 메모리 CLI/TUI/MCP 서버와 브릿지 제공 | LLM-Wiki를 External Brain으로 연결하면, 에이전트가 프로젝트 간 지식을 Recall하고, 장기 기억을 유지할 수 있음 |
| **Data Layer (모니터링)** | 여러 에이전트의 활동, 토큰/비용 추정, KPI 요약, 일일 대시보드를 로컬에서 제공 | 전용 Agent 서비스의 운영 모니터링, 사용량 추적, 비용 관리에 그대로 활용 가능 |
| **Flywheel (자기 진화)** | 승인된 실행 기록을 Trace, Eval Case, Training-ready JSONL 등으로 변환 | 에이전트의 자가 진단 및 지속적 학습 파이프라인 구축에 활용 가능 |
| **다양한 Harness 지원** | Claude Code, Cursor, Hermes, Codex, Gemini CLI, DIY Python 등과 연결 가능 | Coding Agent 단계에서는 원하는 도구로 자유롭게 테스트하고, 이후 전용 Agent로 전환할 때도 `.agent/` 구조를 재사용 가능 |

### ⚠️ agentic-stack의 한계 (직접 개발 필요한 부분)

| 한계 | 설명 | 전용 Agent 개발 시 대응 방안 |
|------|------|------------------------------|
| **Multi-user 미지원** | agentic-stack은 단일 사용자/단일 프로젝트 환경을 가정 | 사용자 인증, 멀티테넌시, 세션 격리, 권한 관리 등을 직접 구현해야 함 |
| **로컬 LLM 연결 부재** | agentic-stack 자체는 LLM을 내장하지 않고, Harness(Codex 등)에 위임 | Ollama, vLLM, Llama.cpp 등 로컬 LLM 서버와 연동하는 Adapter/API를 직접 개발 |
| **서비스형 API 미제공** | CLI/TUI 기반 도구로, REST API나 WebSocket 서버를 제공하지 않음 | FastAPI, Flask 등으로 HTTP API 서버를 구축하고, agentic-stack의 내부 함수를 호출하는 Wrapper 개발 필요 |
| **사용자별 데이터 격리** | `.agent/` 폴더가 프로젝트 단위로 단일 저장소를 사용 | 사용자/조직별로 별도의 `.agent/` 브랜치나 디렉토리를 분리하고, DB로 메타데이터를 관리해야 함 |

---

## 2. Coding Agent → 전용 Agent Service 전환을 위한 개발 가이드

### 🏗️ 전체 아키텍처 제안

```
┌─────────────────────────────────────────────────────────────────┐
│                     전용 Agent Service                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  API Layer  │───▶│  Agent      │───▶│  Knowledge VM       │ │
│  │  (FastAPI)  │    │  Orchestrator│    │  (실행 엔진)        │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                  │                      │             │
│         ▼                  ▼                      ▼             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              agentic-stack .agent/ (포터블 브레인)         ││
│  │  - memory/ (working/episodic/semantic/personal)            ││
│  │  - skills/ (kdqe, data-layer, brain 등)                   ││
│  │  - protocols/ (도구 권한, 스키마)                          ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              External Brain (LLM-Wiki + OKF)               ││
│  │  - Git-backed 장기 지식 저장소                             ││
│  │  - brain_bridge.py로 연동                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Local LLM (Ollama + Qwen)                     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 📋 단계별 개발 로드맵

#### Phase 1: agentic-stack 기반 Coding Agent 고도화 (현재 단계)

| 작업 | 설명 | 비고 |
|------|------|------|
| **LLM-Wiki → External Brain 연결** | `agentic-stack brain` 명령어로 Brain 상태 확인, 프로젝트 온보딩, 글로벌 메모리 검색, durable note 작성 등 가능 | `.agent/tools/brain_bridge.py`를 활용해 Host Agent가 Cross-project Recall을 수행하도록 구성 |
| **Brain Seed Skill 활성화** | Brain Skill이 에이전트에게 Brain 메모리 Query/Write 시점을 알려주고, Secret handling을 명시적으로 관리 | Coding Agent가 지식 추가/검색/자가진단을 자동으로 수행하도록 Skill 내장 |
| **Data Layer로 모니터링** | `agentic-stack doctor`, `data-layer` 스킬로 Agent 활동, 토큰/비용, KPI를 대시보드화 | Coding Agent 실행 로그를 수집하고, Flywheel Artifact(Trace, Eval Case)를 생성하여 자기 진화 기반 마련 |

#### Phase 2: 전용 Agent Service 코어 개발

| 작업 | 설명 | 구현 포인트 |
|------|------|-------------|
| **로컬 LLM Adapter 구현** | Ollama, vLLM 등 OpenAI-compatible API를 호출하는 Wrapper | `langchain_community.llms.Ollama` 또는 `openai` 클라이언트로 Qwen/Gemma 등 연결 |
| **API 서버 구축** | FastAPI로 `/query`, `/add_knowledge`, `/search`, `/diagnose` 등 엔드포인트 제공 | agentic-stack의 `plan()` 함수를 호출하고, 결과를 JSON으로 반환 |
| **Multi-user 인증/세션** | JWT 또는 API Key 기반 사용자 인증, 사용자별 `.agent/` 브랜치 격리 | 각 user_id에 대해 별도의 `.agent/` 디렉토리(또는 Git 브랜치)를 생성하고, `system_model`을 동적으로 로드 |
| **지식 추가/검색/자가진단 API** | LLM-Wiki(OKF)에 새로운 Concept/Data를 추가하고, 검색하며, 무결성을 진단하는 엔드포인트 | `kchef add`, `kchef validate`, `brain_bridge.py`를 호출하는 Service Layer 구현 |

#### Phase 3: 확장 및 최적화

| 작업 | 설명 |
|------|------|
| **멀티테넌시 데이터 격리** | 사용자/조직별 OKF 번들, SQLite DB, Vector DB를 분리 |
| **캐싱 및 성능 최적화** | 자주 조회되는 Concept, IR 결과를 Redis 등에 캐싱 |
| **Webhook/Event 기반 자가진화** | 에이전트 실행 완료 시 Flywheel Artifact를 자동 생성하고, Brain에 학습 피드백을 기록 |
| **관리자 대시보드** | 사용자별 사용량, 토큰 소비, 에이전트 활동 로그를 시각화 |

---

### 🔧 핵심 구현 예시 (Python)

```python
# agent_service/api.py
from fastapi import FastAPI, Depends, HTTPException
from kchef.planner.pipeline import PlannerPipeline, load_system_model
from kchef.planner.simulator import MentalSimulator
from langchain_community.llms import Ollama

app = FastAPI()

# 사용자별 .agent/ 경로 매핑
USER_AGENT_PATHS = {
    "user1": "/path/to/user1/.agent",
    "user2": "/path/to/user2/.agent",
}

def get_planner(user_id: str):
    agent_path = USER_AGENT_PATHS.get(user_id)
    if not agent_path:
        raise HTTPException(404, "User not found")
    system_model = load_system_model(bundle_path=f"{agent_path}/wiki")
    return PlannerPipeline(system_model, skills_dir=f"{agent_path}/skills")

@app.post("/query")
def query(question: str, user_id: str):
    planner = get_planner(user_id)
    ir = planner.plan(question)
    # 로컬 LLM으로 최종 응답 생성
    llm = Ollama(model="qwen2.5:7b")
    response = llm.invoke(f"Based on this plan: {ir.dict()}, answer: {question}")
    return {"answer": response, "ir": ir.dict()}
```

---

### 📌 결론

agentic-stack은 **포터블 브레인(.agent/)** 과 **External Brain(brain_bridge)** 을 통해 지식과 메모리를 표준화하고, **Data Layer**와 **Flywheel**로 모니터링과 자기 진화의 기반을 제공합니다. 이는 전용 Agent Service의 **'지식 관리 및 메모리 계층'**을 단기간에 구축할 수 있게 해주는 강력한 자산입니다.

다만, **Multi-user 지원, 로컬 LLM 연동, REST API 서버**는 직접 개발해야 하며, agentic-stack은 이 부분을 대체하지 않고 **'내부 엔진'**으로 활용하는 것이 바람직합니다.

> 💡 **권장 전략**: Coding Agent 단계에서는 agentic-stack의 모든 기능을 활용해 지식베이스와 에이전트 워크플로를 완성하고, 전용 Agent Service로 전환할 때는 agentic-stack의 `.agent/` 폴더와 `brain_bridge`를 그대로 재사용하면서, 상위에 Multi-user API와 로컬 LLM Adapter를 씌우는 **Adapter 패턴**을 적용하세요.

---

**정확히 지적하셨습니다.** 일반적인 AI 업계 용어로 `Brain`은 종종 **LLM 자체(추론 엔진)**를 의미합니다. (예: "이 챗봇의 Brain은 GPT-4다").

하지만 `agentic-stack`과 `codejunkie99/brain` 저장소에서 말하는 **`Brain`**은 **LLM이 아닌, 에이전트의 '장기 기억 저장소 (Long-term Memory Store)'**를 뜻합니다. 
비유하자면, LLM은 `CPU/두뇌`이고, `Brain` 저장소는 `하드디스크/도서관`입니다. 에이전트가 과거에 쓴 노트(Note)나 지식(Knowledge)을 보관해 두고, 나중에 LLM이 참고할 수 있도록 꺼내는 저장소 역할을 합니다.

### 🧠 `Brain` vs `LLM-Wiki` 용어 비교

| 용어 | 의미 | 장점 | 단점 |
| :--- | :--- | :--- | :--- |
| **Brain** | 에이전트의 지속적이고 구조화된 **지식 저장소** | agentic-stack 공식 문서 및 CLI와 정확히 일치함. "외부 뇌"라는 개념이 에이전트 워크플로우에 직관적임. | LLM 자체와 혼동하기 쉬움. 기술이 아닌 사람에게 설명할 때 오해를 부를 수 있음. |
| **LLM-Wiki** | 사람과 LLM이 함께 읽고 쓰는 **OKF 기반 위키** | 의미가 완전히 명확함. LLM이 사용하는 **지식 베이스(Knowledge Base)**임을 바로 알 수 있음. 프로젝트 이름으로 매우 직관적임. | agentic-stack이 `brain`이라는 용어를 사용하므로, 코드 내부 변수명과 문서화 용어가 달라질 수 있음. |

---

### 💡 제안: 상황별 용어 전략

저는 **프로젝트 명칭은 `llm-wiki`**로 하고, **기술/아키텍처 용어로는 `Brain`을 병행** 사용하시기를 권장합니다.

1.  **폴더명/저장소명**: `llm-wiki` (직관적이고 명확)
2.  **설정 파일 내부 변수명**: `EXTERNAL_BRAIN_PATH` 또는 `KNOWLEDGE_STORE_PATH` (agentic-stack과의 호환성 유지)
3.  **사용자/팀원 설명 시**: "이건 LLM이 참고하는 **지식 위키(Knowledge Wiki)**입니다. agentic-stack에서는 이 위키를 **'External Brain(외부 뇌)'**라고 부릅니다."

**결론적으로**, `llm-wiki`가 **이해하기 훨씬 쉬운 용어**입니다. 단, 기술적으로 agentic-stack을 연동할 때는 내부에서 `brain`이라는 용어를 사용하므로, 팀 문서 최상단에 *"llm-wiki는 agentic-stack의 External Brain 저장소 역할을 합니다"*라고 명시해 두면 혼동을 완전히 피할 수 있습니다. 😊

---

# OKF 기반 자연어 질의응답 시스템의 성능 평가 및 KTCP 논문 게재 가이드

KTCP(한국정보과학회 컴퓨팅의 실제 논문지)에 논문을 게재하기 위해서는 **체계적인 실험 설계, 객관적인 평가 지표, 그리고 기존 방법론과의 공정한 비교**가 필수적입니다. OKF 기반 시스템이 일반 RAG나 단순 Text-to-SQL 대비 얼마나 우수한지를 과학적으로 입증하기 위한 구체적인 로드맵을 제시해 드립니다.


## 1. 연구의 차별성: OKF가 해결하는 문제

KTCP 논문에서 강조해야 할 핵심 차별점은 OKF가 **'의미적 단절(Semantic Gap)'** 을 해소하는 계층이라는 점입니다.

| 기존 접근법 | 한계 | OKF 기반 접근법 |
|------------|------|----------------|
| **Text-to-SQL** | "VIP 고객"과 같은 비즈니스 용어를 SQL 조건(`total_purchase > 1000000`)으로 매핑하는 로직이 없음 | OKF Concept(`vip_customer.md`)에 비즈니스 규칙을 정의하고, Planner가 이를 자동으로 SQL 조건으로 변환 |
| **RAG** | 벡터 유사도 기반 검색으로 인해 **환각(Hallucination)** 과 **출처 미상의 답변** 문제가 발생 | OKF는 **인용(Citation)**을 강제하여 모든 답변이 원본 데이터를 가리키도록 함 |
| **단순 Hybrid** | 정형 데이터와 비정형 문서를 통합적으로 조회하는 계층 부재 | OKF의 계층적 `index.md`가 **심볼 테이블** 역할을 하여 구조화된 탐색 지원 |


## 2. 평가 프레임워크 설계 (Contract-First 원칙)

KTCP 논문의 신뢰성을 높이려면 **LLM/Agent Stack에 독립적인 평가 체계**를 구축해야 합니다. 다음 5가지 원칙을 제안합니다.

### 2.1 평가 원칙

| 원칙 | 설명 |
|------|------|
| **Stack Independence** | 특정 LLM(Gemini, GPT, Qwen)에 종속되지 않는 테스트 코드 작성 |
| **Contractual Precision** | 답변을 JSON/YAML 같은 **구조화된 형식**으로 출력하고 검증 |
| **Data Provenance (인용)** | 모든 답변에 OKF 내 원본 데이터 경로를 **강제 인용** |
| **Hierarchical Failure Analysis** | IR(Intermediate Representation) 단계별 실패 모드를 구분 |
| **Reproducible Test Sets** | Ground Truth가 포함된 **불변 데이터셋** 사용 |

### 2.2 평가 지표 (Metrics)

#### A. 답변 정확도 (Answer Accuracy) — **핵심 지표**
- **정의**: 구조화된 답변(JSON) 내 각 필드가 Ground Truth와 일치하는 비율
- **측정**: 필드별 `assert response['total_students'] == gt['total_students']`
- **목표**: 98% 이상
- **참고**: dbt Labs의 2026년 벤치마크에 따르면 Text-to-SQL 정확도는 32.7%에서 64.5%로 향상되었습니다. OKF 기반 시스템은 이보다 현저히 높은 정확도를 목표로 해야 합니다.

#### B. Recipe/IR 정확도 (Plan Accuracy)
- **정의**: Planner가 생성한 IR(Intermediate Representation)이 Expected IR과 일치하는 정도
- **측정**: `goal`, `constraints` 정확 일치, `traversal`은 필수 경로 포함 여부로 Precision/Recall 측정
- **목표**: Precision 95%, Recall 100%

#### C. 환각률 (Hallucination Rate)
- **정의**: OKF 번들 외부의 정보가 답변에 포함된 비율
- **탐지**: 답변 텍스트를 분해하여 각 문장의 출처가 OKF 내에 존재하는지 LLM Critic이 판별
- **목표**: 0%

#### D. 인용 정밀도/재현율 (Citation F1)
- **정의**: Agent가 제공한 출처가 실제 정답 도출에 사용된 올바른 데이터인지 측정
- **정밀도**: Agent가 인용한 출처 중 실제 정답과 관련된 비율
- **재현율**: 실제 정답에 필요한 모든 출처를 Agent가 인용했는지

#### E. 탐색 효율성 (Traversal Efficiency)
- **정의**: 정답을 찾기 위해 Agent가 열어본 총 index.md 및 데이터 파일 수
- **목표**: 계층적 index.md로 인해 RAG 방식 대비 파일 I/O 50% 감소


## 3. 실험 설계 (Experimental Design)

### 3.1 비교 대상 (Baselines)

| 시스템 | 설명 |
|--------|------|
| **Text-to-SQL (Baseline 1)** | Spider/WikiSQL 벤치마크에서 SOTA 성능을 내는 오픈소스 모델 |
| **RAG (Baseline 2)** | Vector DB 기반의 표준 RAG 파이프라인 (예: LangChain + Chroma) |
| **Hybrid (Baseline 3)** | Text-to-SQL + RAG을 단순 결합한 시스템 |
| **OKF-based (Ours)** | OKF Knowledge Catalog + Cognitive Compiler + Knowledge VM |

### 3.2 테스트 데이터셋

| 데이터셋 | 출처 | 규모 | 특징 |
|----------|------|------|------|
| **OKF-Bench** | 자체 구축 | 200+ 질의 | OKF 개념(VIP, 매출 등)이 포함된 실제 비즈니스 질문 |
| **Spider** | 공개 벤치마크 | 200개 DB, 10,000+ 질의 | 복잡한 JOIN, GROUP BY, 서브쿼리 포함 |
| **WikiSQL** | 공개 벤치마크 | 80,654개 질의 | 단일 테이블 기반 단순 질의 |
| **OKGQA-style** | 자체 변형 | 500+ 질의 | 개방형(Open-ended) 질문, 환각 측정용 |

> OKGQA는 Knowledge Graph를 활용한 LLM의 개방형 질의응답을 평가하는 벤치마크로, OKF 기반 시스템의 평가에 직접 참고할 수 있습니다.

### 3.3 실험 조건

1. **동일한 LLM 백본 사용**: 모든 Baseline과 OKF 시스템이 동일한 LLM(Gemini 2.5 Pro 또는 Qwen 2.5)을 사용하도록 통제
2. **동일한 하드웨어 환경**: GPU, 메모리 등 동일 조건에서 실행
3. **Cold Start vs. Warm Start**: 캐싱 효과를 분리하여 측정
4. **Multi-hop 질의**: 2-hop, 3-hop 질의에 대한 성능 비교


## 4. KTCP 논문 구조 제안

### 제목 (가칭)
> *"OKF 기반 계층적 지식베이스를 활용한 자연어 질의응답 시스템의 성능 평가"*
> 또는
> *"Open Knowledge Format을 활용한 의미적 질의 계층의 효용성 검증: RAG 및 Text-to-SQL과의 비교 연구"*

### 초록 (Abstract)
- OKF의 개념과 문제 해결 방식을 2~3문장으로 요약
- 실험 설계 (3개 Baseline과 비교)
- 주요 결과 (정확도, 환각률, 탐색 효율성 수치)
- 학술적/실용적 기여

### 1. 서론 (Introduction)
- 기존 RAG/Text-to-SQL의 한계 (의미적 단절, 환각, 출처 미상)
- OKF의 등장 배경과 특장점
- 연구 질문: *"OKF 기반 시스템이 기존 접근법 대비 정확도, 환각률, 효율성 측면에서 유의미한 개선을 보이는가?"*

### 2. 관련 연구 (Related Work)
- Text-to-SQL 발전 동향 (Spider, WikiSQL, BIRD-SQL)
- RAG 평가 방법론 (RAGEval, Faithfulness, Context Relevance)
- Knowledge Graph QA (KGQA) 평가 프레임워크 (Chronos, OKGQA)
- OKF 및 agentic-stack 관련 연구

### 3. 시스템 아키텍처 (System Architecture)
- OKF Knowledge Catalog 구조 (Concept, Metric, Business Rule)
- Cognitive Compiler 파이프라인 (Intent Recognition → Concept Matching → IR Generation → Execution)
- Knowledge VM (SQLite + Document 검색 통합 실행)

### 4. 실험 설계 (Experimental Setup)
- 4.1 평가 지표 (Answer Accuracy, Hallucination Rate, Citation F1, Traversal Efficiency)
- 4.2 테스트 데이터셋 (OKF-Bench, Spider, WikiSQL)
- 4.3 Baseline 시스템 구성
- 4.4 실험 환경 (LLM, 하드웨어)

### 5. 실험 결과 (Results)
- **RQ1**: OKF 기반 시스템의 Answer Accuracy는 Baseline 대비 얼마나 높은가?
- **RQ2**: OKF 기반 시스템의 Hallucination Rate는 얼마나 낮은가?
- **RQ3**: OKF 기반 시스템의 Traversal Efficiency는 RAG 대비 얼마나 효율적인가?
- **RQ4**: 질의 복잡도(단일 hop vs multi-hop)에 따라 성능 차이는 어떻게 달라지는가?

### 6. 분석 및 토론 (Analysis & Discussion)
- 성공 사례 분석 (OKF Concept이 정확히 매핑된 경우)
- 실패 사례 분석 (Concept 누락, 모호한 질의)
- OKF의 한계점 (수동 큐레이션 의존성, 초기 구축 비용)

### 7. 결론 (Conclusion)
- 주요 발견 요약
- 학술적 기여 (OKF 기반 질의 계층의 효용성 입증)
- 실용적 기여 (RAG/Text-to-SQL 대비 OKF의 우수성 정량적 제시)
- 향후 연구 (자가 진화형 Knowledge Base, Multi-modal OKF)


## 5. 성능 개선 수치 예측 (Hypothesis)

다음은 OKF 기반 시스템이 기존 접근법 대비 기대되는 성능 향상치입니다 (논문에서 입증해야 할 가설).

| 지표 | Text-to-SQL | RAG | OKF-based (예상) | 개선율 |
|------|-------------|-----|------------------|--------|
| Answer Accuracy | 65-75% | 60-70% | **90-95%** | +20~30%p |
| Hallucination Rate | 15-25% | 20-30% | **< 5%** | -70% 이상 |
| Citation F1 | N/A | 40-60% | **> 90%** | +50%p |
| Traversal Efficiency | 1 query (SQL) | 10-50 chunks | **3-5 files** | -70% I/O |


## 6. TDD 기반 평가 파이프라인 (구현 가이드)

KTCP 논문의 재현성을 위해 **이미 구현된 TDD 평가체계**를 활용하세요.

```python
# tests/evaluation/test_okf_benchmark.py
import pytest
from kchef.planner.pipeline import PlannerPipeline
from kchef.eval.scorer import PlanningScorer

def test_okf_vs_baselines():
    """OKF, RAG, Text-to-SQL의 동일 질의에 대한 성능 비교"""
    questions = load_benchmark("okf_benchmark.jsonl")
    
    for q in questions:
        # 1. OKF 기반
        okf_ir = okf_planner.plan(q.question)
        okf_score = scorer.score(okf_ir, q.ground_truth)
        
        # 2. Text-to-SQL (Baseline)
        sql = text_to_sql_generator.generate(q.question)
        sql_score = evaluate_sql(sql, q.ground_truth)
        
        # 3. RAG (Baseline)
        rag_answer = rag_pipeline.query(q.question)
        rag_score = evaluate_rag(rag_answer, q.ground_truth)
        
        # 4. 검증
        assert okf_score.accuracy > sql_score.accuracy + 0.15
        assert okf_score.hallucination < rag_score.hallucination * 0.3
```

이 평가 파이프라인은 **LLM/Agent Stack이 변경되어도 동일하게 재사용**할 수 있습니다.


## 7. KTCP 논문 게재를 위한 추가 조언

1. **사전 등록 연구 (Preregistered Report)**: 실험 설계를 사전에 KTCP에 등록하면 연구의 투명성과 신뢰성이 높아집니다.

2. **오픈소스 공개**: OKF 기반 시스템의 코드와 평가 데이터셋을 GitHub에 공개하면 **재현성(Reproducibility)** 측면에서 높은 점수를 받을 수 있습니다.

3. **사례 연구 포함**: 실제 기업/대학의 데이터로 OKF 기반 시스템을 구축한 사례를 포함하면 실용적 가치를 강조할 수 있습니다.

4. **OKF의 한계도 솔직히 기술**: 초기 OKF 번들 구축 비용, 수동 큐레이션 의존성, OKF 생태계 성숙도 등을 논의하면 학술적 완성도가 높아집니다.

5. **KTCP 특성 고려**: KTCP는 "컴퓨팅의 실제"라는 이름처럼 **실용적이고 적용 가능한 연구**를 선호합니다. OKF 기반 시스템의 **실제 구축 비용, 유지보수 용이성, 확장성**에 대한 정성적 분석도 포함하세요.


## 8. 결론: 논문의 핵심 메시지

이 논문은 다음 메시지를 전달해야 합니다:

> **"OKF는 단순한 데이터 포맷이 아니라, 의미적 질의 계층(Semantic Query Layer)을 제공하여 RAG의 환각 문제와 Text-to-SQL의 의미적 단절 문제를 동시에 해결하는 실용적인 대안이다."**

이를 정량적 데이터(Answer Accuracy 90%+, Hallucination < 5%, Citation F1 > 90%)로 입증하고, KTCP 독자들이 OKF 기반 시스템을 실제 프로젝트에 도입할 수 있는 근거를 제시하는 것이 목표입니다. 🚀