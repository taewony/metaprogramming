# KnowledgeChef System Design: OKF 기반 지식베이스 Producer/Consumer 아키텍처

## Executive Summary

KnowledgeChef는 **OKF(Open Knowledge Format)**을 표준 스키마로 삼아 다양한 소스(CSV, SQLite, JSONL, 문서)로부터 지식베이스를 구축(Producer)하고, 자연어 질의를 통해 사실과 데이터를 찾아 응답(Consumer)까지 생성하는 **Snowball형 지식 증식 시스템**입니다.

본 프로젝트는 **자연어로 데이터를 조회하고 응답할 수 있는 Agent**를 개발하는 것을 목표로 한다. 최종 목표는 Local LLM을 기반으로 동작하는 전용 Agent를 구축하는 것이며, 이를 위해 다음의 단계적 접근을 취한다:

1. **agentic-stack 기반 Coding Agent 실험**: `agentic-stack`의 Data Layer를 확장하여 OKF(Open Knowledge Format) 지식베이스의 user/order/product 스키마를 자연어로 조회하는 기능을 Coding Agent(antigravity CLI)로 구현 및 검증
2. **openkb 기반 OKF 컴파일 실험**: `openkb`를 활용하여 OKF 지식베이스를 컴파일하고 활용하는 기능 검증
3. **전용 Agent로 전환**: Coding Agent 의존성을 제거하고 Local LLM 기반의 전용 Agent로 동일 기능을 구현

---

## 1. 시스템 아키텍처 개관

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KNOWLEDGECHEF SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────── PRODUCER LAYER ───────────────────────────────┐    │
│  │                                                                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │  Raw Data    │  │  Documents   │  │  Existing    │             │    │
│  │  │  (CSV/JSONL) │  │  (PDF/MD)    │  │  OKF Bundle  │             │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │    │
│  │         │                 │                 │                      │    │
│  │         ▼                 ▼                 ▼                      │    │
│  │  ┌──────────────────────────────────────────────────────────┐      │    │
│  │  │              OKF Compiler / Ingredient Builder           │      │    │
│  │  │  - Schema Inference  - Concept Extraction  - Linking    │      │    │
│  │  └──────────────────────────────────────────────────────────┘      │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │  ┌──────────────────────────────────────────────────────────┐      │    │
│  │  │              OKF Knowledge Bundle (Git Repo)             │      │    │
│  │  │  concepts/  data/  documents/  index.md  log.md         │      │    │
│  │  └──────────────────────────────────────────────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────── CONSUMER LAYER ───────────────────────────────┐    │
│  │                                                                     │    │
│  │  ┌──────────────┐                                                  │    │
│  │  │   Natural    │                                                  │    │
│  │  │   Language   │────▶  Cognitive Compiler (Agent)                │    │
│  │  │   Query      │      - Intent Analysis                          │    │
│  │  └──────────────┘      - Symbol Resolution (index.md)             │    │
│  │                        - Tree Traversal & Pruning                 │    │
│  │                        - SQL/Data Generation                      │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │  ┌──────────────────────────────────────────────────────────┐      │    │
│  │  │              Execution Engine (Knowledge VM)             │      │    │
│  │  │  - SQLite Query  - CSV Filter  - Document Retrieval     │      │    │
│  │  └──────────────────────────────────────────────────────────┘      │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │  ┌──────────────────────────────────────────────────────────┐      │    │
│  │  │              Response Synthesizer                        │      │    │
│  │  │  - Citation Generation  - Natural Language Answer       │      │    │
│  │  └──────────────────────────────────────────────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌───────────────────── SNOWBALL MERGER ──────────────────────────────┐    │
│  │  - Union (합치기)  - Distinct (중복제거)  - Difference (차등)   │    │
│  │  - Selection & Join (관계 검증)  - Link Integrity Checker        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. OKF 기반 Knowledge Producer 설계

### 2.1 OKF 표준 준수

OKF는 **벤더 중립적인 오픈 포맷**으로, YAML Frontmatter가 포함된 Markdown 파일의 디렉터리로 지식을 표현합니다. 최소 필수 필드는 `type` 하나이며, 나머지는 자유 텍스트로 허용하여 생산성을 높이면서도 에이전트가 소비할 수 있는 충분한 구조를 제공합니다.

**OKF 번들 기본 구조:**
```
okf_bundle/
├── index.md                    # 최상위 심볼 테이블
├── log.md                      # 변경 이력 (Delta 추적용)
├── concepts/
│   ├── customer.md             # type: Entity
│   ├── vip_customer.md         # type: BusinessRule
│   └── monthly_sales.md        # type: Metric
├── entities/
│   └── ...                     # type: Entity
├── metrics/
│   └── ...                     # type: MetricGroup
├── data/
│   ├── customers.csv           # 정형 데이터
│   └── orders.csv
└── documents/
    └── reports/                # 비정형 문서
```

### 2.2 Producer 파이프라인: 다양한 소스 → OKF 번들

| 소스 유형 | 변환 방식 | 산출물 |
|-----------|-----------|--------|
| **SQLite/CSV/JSONL** | `okf-sqlite` 또는 커스텀 스키마 추출기 | `entities/` + `data/` 파일 |
| **PDF/Word/마크다운** | OpenKB `compile` 또는 LLM 요약 | `concepts/` + `documents/` |
| **기존 OKF 번들** | `kchef merge`로 통합 | 병합된 번들 |
| **웹 문서** | `okfy crawl` | OKF 개념 파일 |

### 2.3 OpenKB 도입 판단

| 평가 항목 | OpenKB 사용 | 자체 Coding Agent 구현 |
|-----------|-------------|------------------------|
| **문서→OKF 변환** | ✅ `openkb add` + `compile`로 자동화 | ❌ 직접 파서/LLM 파이프라인 구현 필요 |
| **PageIndex 검색** | ✅ 벡터 없는 트리 기반 장문 검색 | ❌ 직접 구현 필요 |
| **Skill Factory** | ✅ 에이전트 Skill로 자동 내보내기 | ❌ 직접 구현 필요 |
| **OKF 호환성** | ✅ OKF 명세 준수 | ⚠️ 수동 검증 필요 |
| **커스터마이징** | ⚠️ 제한적 (오픈소스 수정 가능) | ✅ 완전 자유 |
| **유지보수 부담** | ✅ 낮음 (커뮤니티 업데이트) | ❌ 높음 (전담 개발 필요) |

**판단: OpenKB를 핵심 도구로 채택**

OpenKB는 OKF 컴파일과 지속적 유지보수를 위한 **Wiki Foundation**과 질의/채팅/Skill Factory를 위한 **Generators**로 구성된 2계층 아키텍처를 제공합니다. 특히 `SKILL.md`를 자동 생성하여 Codex, Claude Code, Gemini CLI 등 모든 에이전트가 별도 설정 없이 지식을 소비할 수 있게 합니다.

**단, 다음 부분은 자체 구현:**
- **SQLite/CSV/JSONL → OKF 변환**: `okf-skills` 참조하거나 커스텀 Connector 구현
- **Snowball Merger (합치기/중복제거/차등)**: KnowledgeChef 고유 기능으로 자체 구현
- **자연어→SQL 변환**: KDQE의 Query Planner 확장

---

## 3. OKF 기반 Knowledge Consumer 설계

### 3.1 Cognitive Compiler 파이프라인

사용자의 자연어 질의를 OKF 지식베이스에 대해 실행 가능한 계획(IR)으로 변환하는 과정입니다.

```
[Natural Language Query]
         │
         ▼
┌─────────────────────────────────────────────────────┐
│ 1. Intent Analysis                                  │
│    - 엔티티 추출 (Customer, Order, Product 등)      │
│    - 메트릭 추출 (COUNT, SUM, AVG 등)               │
│    - 조건/필터 추출 (시간, 카테고리, 등급 등)       │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│ 2. Symbol Resolution (index.md Traversal)           │
│    - 최상위 index.md에서 관련 Concept 검색          │
│    - 계층적 트리 탐색으로 정확한 파일 경로 획득     │
│    - 메타데이터 기반 가지치기(Pruning)로 탐색 최적화│
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│ 3. Intermediate Representation (IR) Generation      │
│    {                                                │
│      "goal": "COUNT_STUDENTS",                      │
│      "constraints": {"semester": "2026-1"},         │
│      "traversal": ["semesters/2026-1/index.md",     │
│                    "data/project_participation.csv"],│
│      "aggregation": "count(distinct student_id)"    │
│    }                                                │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│ 4. Execution (Knowledge VM)                         │
│    - SQLite Query 실행                              │
│    - CSV/JSONL 필터링                               │
│    - 문서 검색/요약                                  │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│ 5. Response Synthesis                               │
│    - 구조화된 결과 + 인용(Citation) 생성            │
│    - 자연어 요약 생성                                │
└─────────────────────────────────────────────────────┘
         │
         ▼
   [Final Answer]
```

### 3.2 Symbol Resolution 상세: index.md가 심볼 테이블 역할

OKF의 계층적 `index.md`는 전통적인 컴파일러의 **심볼 테이블(Symbol Table)** 역할을 합니다.

**index.md 예시:**
```markdown
# 2026년 1학기 프로젝트 지식베이스

## Concepts
- [Project](/concepts/project.md) - 프로젝트 엔티티
- [Student](/concepts/student.md) - 학생 엔티티
- [VIP Customer](/concepts/vip_customer.md) - VIP 고객 정의 (total_purchase > 1000000)

## Data Files
- [projects.csv](/data/projects.csv) - 47개 프로젝트
- [students.csv](/data/students.csv) - 1,234명 학생
- [project_participation.csv](/data/project_participation.csv) - 312개 참여 기록

## Documents
- [2026-1 캡스톤 보고서](/documents/reports/capstone_2026_1.pdf)
```

에이전트는 이 심볼 테이블을 참조하여:
1. 질의에 필요한 Concept의 정확한 경로 획득
2. 데이터 파일의 위치와 스키마 파악
3. 관련 문서의 존재 확인

### 3.3 Tree Traversal & Pruning 전략

브루트 포스 검색을 피하고 효율적인 탐색을 위해:

1. **메타데이터 기반 가지치기**: `index.md`의 태그와 질의 의도를 매칭하여 불필요한 하위 트리 탐색 스킵
2. **Symbol Resolution 우선**: 전체 파일 시스템 스캔 없이 `index.md` 심볼 테이블로 직접 경로 해결
3. **캐싱**: 자주 조회되는 Concept과 데이터 파일 경로는 메모리 캐시

---

## 4. Snowball Merger: 지식 증식 및 정제 엔진

### 4.1 관계대수 기반 TDD 연산 매핑

| 연산 | 관계대수 | TDD 검증 포인트 | 구현 위치 |
|------|----------|----------------|-----------|
| **합치기** | Union ($\cup$) | 전체 파일 카디널리티 = \|A\| + \|B\| | `kchef merge` |
| **중복제거** | Distinct ($\pi$) | 동일 resource 중 최신 1개만 유지 | `kchef dedupe` |
| **차등** | Difference ($-$) | 추가/수정/삭제된 Delta만 추출 | `kchef diff` |
| **리팩토링** | Selection ($\sigma$) + Join ($\bowtie$) | Broken Link 0, type 필터링 정확 | `kchef validate` |

### 4.2 Ingredient → Snowball → Main Bundle 병합 파이프라인

```
┌─────────────────────────────────────────────────────────────────┐
│                    SNOWBALL MERGER PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Ingredient 1 │    │ Ingredient 2 │    │ Ingredient 3 │      │
│  │ (컴공과)     │    │ (전자과)     │    │ (산학협력)   │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Step 1: Structure Harmonizer (Union)                    │   │
│  │ - 동일 Concept 파일 병합 (예: project.md 합치기)        │   │
│  │ - 동일 스키마 CSV concat (예: projects.csv)             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Step 2: Deduplication Engine (Distinct)                 │   │
│  │ - Concept 유사도 분석 (TF-IDF + 코사인 유사도)          │   │
│  │ - 데이터 레코드 중복 제거 (key 기준)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Step 3: Link Integrity Checker (Selection + Join)       │   │
│  │ - 내부 링크(Broken Link) 탐지 및 자동 수정              │   │
│  │ - log.md에 변경 이력 기록 (Difference)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Step 4: Index Generator                                  │   │
│  │ - 각 디렉터리 index.md 재생성 (심볼 테이블 갱신)        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Step 5: Snowball Bundle (1차 병합 완료)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 구현 스택 및 통합 아키텍처

### 5.1 권장 기술 스택

| 계층 | 기술 | 선정 이유 |
|------|------|-----------|
| **OKF 처리** | OpenKB + 커스텀 확장 | OKF 컴파일 및 Skill Factory 자동화 |
| **로컬 LLM** | Ollama + Qwen2.5 | 토큰 비용 절감, 데이터 보안 |
| **Agent Framework** | agentic-stack + Codex | .agent/ 포터블 브레인, 에이전트 간 지식 공유 |
| **CLI** | Typer/Click | 직관적인 `kchef` 명령어 |
| **버전 관리** | GitPython | 스냅샷, 롤백, Diff 추적 |
| **테스트** | Pytest + 관계대수 기반 TDD | 스택 독립적 평가체계 |

### 5.2 OpenKB + 자체 구현 통합 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGECHEF SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              OpenKB (Core Engine)                         │ │
│  │  - Wiki Foundation: 문서→OKF 컴파일, PageIndex 검색     │ │
│  │  - Generators: query/chat/Skill Factory                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         KnowledgeChef Extensions (자체 구현)              │ │
│  │  - kchef merge (Snowball Merger)                         │ │
│  │  - kchef dedupe (중복 제거)                              │ │
│  │  - kchef validate (링크 무결성)                          │ │
│  │  - kchef diff (차등 추적)                                │ │
│  │  - SQLite/CSV/JSONL → OKF Connector                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              agentic-stack (Agent Runtime)                │ │
│  │  - .agent/ 포터블 브레인                                  │ │
│  │  - Codex/Claude Code/Cursor 통합                         │ │
│  │  - Data Layer: 에이전트 활동 모니터링                    │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 `kchef` CLI 명령어 설계

| 명령어 | 설명 | 관계대수 연산 |
|--------|------|---------------|
| `kchef init <path>` | 빈 OKF 번들 초기화 | CREATE DATABASE |
| `kchef add <source>` | 새 Ingredient 추가 (OpenKB 호출) | INSERT |
| `kchef merge <src> <dest>` | 두 번들 병합 | UNION |
| `kchef dedupe <path>` | 중복 Concept/데이터 제거 | DISTINCT |
| `kchef diff <old> <new>` | 변경 Delta 추출 | DIFFERENCE |
| `kchef validate <path>` | 링크 무결성 + OKF Spec 검증 | SELECT + JOIN |
| `kchef index <path>` | index.md 재생성 | CREATE INDEX |
| `kchef query "<question>"` | 자연어 질의 실행 (Consumer) | — |

---

## 6. 질의 응답 시나리오 (End-to-End Example)

### 시나리오: "VIP 고객은 몇 명이고, 누구야?"

```
[User] "VIP 고객은 몇 명이고, 누구야?"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Cognitive Compiler (Codex + kdqe Skill)                    │
│    - Intent: LIST + COUNT, Entity: Customer                   │
│    - Symbol Resolution: concepts/vip_customer.md 조회         │
│    - VIP 정의 확인: grade='VIP'                               │
│    - IR 생성: {goal: "LIST+COUNT", table: "customers",        │
│                filter: "grade='VIP'"}                         │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Execution (Knowledge VM)                                   │
│    - SQLite: SELECT id, name, email FROM customers            │
│               WHERE grade='VIP'                               │
│    - 결과: [(4, '정민호', 'dave@test.kr'), ...] 5 rows       │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Response Synthesizer                                       │
│    - "VIP 고객은 총 5명입니다."                                │
│    - "목록: 정민호(dave@test.kr), 오세훈(hank@test.kr), ..." │
│    - Citation: data/customers.csv (grade='VIP' 조건)          │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
[Answer] "VIP 고객은 총 5명입니다. 목록: 정민호, 오세훈, 강태영, 문창호, 황미소"
```

---

## 7. TDD 및 평가체계

### 7.1 관계대수 기반 평가 지표

| 지표 | 측정 방법 | 목표 |
|------|-----------|------|
| **Answer Accuracy** | 구조화된 답변 필드 일치율 | ≥ 98% |
| **Plan (IR) Accuracy** | Expected IR과 생성 IR 비교 | Precision 95%, Recall 100% |
| **Hallucination Rate** | 인용 없는 답변 비율 | 0% |
| **Citation F1** | 인용 정밀도/재현율 | ≥ 95% |
| **Traversal Efficiency** | 질의당 파일 I/O 횟수 | RAG 대비 50% 감소 |

### 7.2 TDD 사이클 (Red-Green-Refactor)

1. **RED**: `tests/test_compiler.py`에 실패 테스트 작성 (예: VIP 고객 COUNT 검증)
2. **GREEN**: OKF 번들에 필요한 데이터 추가 (CSV, index.md) → 테스트 통과
3. **REFACTOR**: 중복 OKF 구조 정리, index.md 포맷 개선

**핵심 원칙**: LLM/Agent Stack 변경 시에도 동일한 테스트 스위트로 검증 가능.

---

## 8. 로드맵 및 마일스톤

| 단계 | 기간 | 목표 | 완료 기준 |
|------|------|------|-----------|
| **Phase 0** | 1주 | 환경 구축 | OpenKB + agentic-stack 설치, OKF 번들 초기화 |
| **Phase 1** | 2주 | Producer 구현 | CSV/SQLite → OKF 변환, `kchef add` 동작 |
| **Phase 2** | 3주 | Consumer 구현 | 자연어→SQL 변환, `kchef query` 동작 |
| **Phase 3** | 2주 | Snowball Merger | `kchef merge/dedupe/validate` 구현 |
| **Phase 4** | 2주 | TDD 평가체계 | 50개 테스트 쿼리로 Answer Accuracy 98% 달성 |
| **Phase 5** | 2주 | Stack Migration Test | 동일 평가로 새 Agent Stack 검증 |

---

## 9. 결론: KnowledgeChef의 핵심 가치

KnowledgeChef는 OKF를 **지식의 표준 인터페이스**로 삼아:

1. **Producer**: 다양한 소스(CSV, SQLite, 문서)를 OKF 번들로 통합
2. **Snowball Merger**: 관계대수 기반 연산(합치기/중복제거/차등)으로 지식 증식 및 정제
3. **Consumer**: 계층적 `index.md` 심볼 테이블을 통한 효율적 질의 응답
4. **OpenKB**: 문서→OKF 컴파일과 Skill Factory 자동화로 생산성 극대화

이 아키텍처는 LLM/Agent Stack이 변경되어도 **평가체계는 그대로 유지**되며, 지식베이스가 눈덩이처럼 성장해도 **무결성과 확장성**을 보장합니다.
## 2. 프로젝트 목표

### 2.3 비목표 (Non-Goals)

- 대규모 실시간 데이터 스트리밍 처리
- 다중 사용자 인증/권한 관리 시스템
- 프로덕션 급 확장성 및 고가용성 인프라
- 벡터 데이터베이스 도입 (openkb의 PageIndex 기반 검색 활용)

---

## 3. 참조 문서 및 기술 스택

### 3.1 참조 문서

| 문서 | URL | 용도 |
|------|-----|------|
| OKF SPEC | https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md | OKF 형식 규격 참조 |
| agentic-stack | https://github.com/codejunkie99/agentic-stack | Coding Agent 실행 환경 및 Data Layer |
| openkb | https://github.com/vectifyai/openkb | OKF 기반 지식베이스 컴파일/조회 도구 |

### 3.2 기술 스택

| 계층 | 기술 | 비고 |
|------|------|------|
| **Coding Agent** | antigravity CLI | agentic-stack 지원 하네스 |
| **Agent Framework** | agentic-stack | `.agent/` 기반 portable agent layer |
| **지식베이스** | OKF (Open Knowledge Format) | Markdown + YAML Frontmatter 기반 |
| **KB 컴파일러** | openkb | OKF 번들 생성 및 쿼리 |
| **Local LLM** | (추후 결정) | Ollama, llama.cpp, GPT4All 등 검토 |
| **언어** | Python 3.10+ | 전용 Agent 구현 언어 |
| **버전 관리** | Git | 전체 프로젝트 형상 관리 |

---

## 4. OKF 지식베이스 설계

### 4.1 OKF 기본 구조

OKF(Open Knowledge Format)는 디렉토리 기반의 Markdown 파일로 구성되며, 각 파일은 YAML Frontmatter와 본문으로 이루어진다.

```
okf-kb/
├── index.md                    # 번들 루트 인덱스
├── log.md                      # 변경 이력
├── schemas/
│   ├── index.md               # 스키마 목록
│   ├── users.md               # User 스키마 개념
│   ├── orders.md              # Order 스키마 개념
│   └── products.md            # Product 스키마 개념
├── datasets/
│   └── sales.md               # 데이터셋 설명
└── examples/
    └── queries.md             # 예제 쿼리
```

### 4.2 개념 정의 (Concept)

각 개념은 하나의 Markdown 파일로 표현되며, Concept ID는 파일 경로에서 `.md` 확장자를 제외한 경로로 정의된다.

#### schemas/users.md

```yaml
---
title: User Schema
description: 사용자 테이블 스키마 정의
type: Schema
tags: [user, schema, authentication]
timestamp: 2026-06-26T00:00:00Z
---
# User Schema

## Description
사용자 정보를 저장하는 테이블 스키마입니다.

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | STRING | 고유 사용자 식별자 |
| `email` | STRING | 사용자 이메일 (고유) |
| `name` | STRING | 사용자 이름 |
| `created_at` | TIMESTAMP | 계정 생성 일시 |
| `status` | STRING | 계정 상태 (active/inactive/suspended) |

## Relationships
- [Orders](/schemas/orders.md) - 사용자가 작성한 주문
```

#### schemas/orders.md

```yaml
---
title: Order Schema
description: 주문 테이블 스키마 정의
type: Schema
tags: [order, schema, transaction]
timestamp: 2026-06-26T00:00:00Z
---
# Order Schema

## Description
주문 정보를 저장하는 테이블 스키마입니다.

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | STRING | 고유 주문 식별자 |
| `user_id` | STRING | [Users](/schemas/users.md) 테이블 참조 |
| `product_id` | STRING | [Products](/schemas/products.md) 테이블 참조 |
| `quantity` | INTEGER | 주문 수량 |
| `total_amount` | NUMERIC | 총 주문 금액 |
| `order_date` | TIMESTAMP | 주문 일시 |
| `status` | STRING | 주문 상태 (pending/shipped/delivered/cancelled) |
```

#### schemas/products.md

```yaml
---
title: Product Schema
description: 상품 테이블 스키마 정의
type: Schema
tags: [product, schema, catalog]
timestamp: 2026-06-26T00:00:00Z
---
# Product Schema

## Description
상품 정보를 저장하는 테이블 스키마입니다.

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | STRING | 고유 상품 식별자 |
| `name` | STRING | 상품명 |
| `category` | STRING | 상품 카테고리 |
| `price` | NUMERIC | 상품 가격 |
| `stock_quantity` | INTEGER | 재고 수량 |
| `created_at` | TIMESTAMP | 상품 등록 일시 |
```

### 4.3 OKF SPEC 준수 사항

- 각 개념 파일은 YAML Frontmatter에 `title`, `description`, `type`, `tags`, `timestamp`를 포함
- Schema 타입의 개념은 `# Schema` 섹션에 테이블 형식으로 컬럼 정의
- `[[wikilink]]` 또는 Markdown 링크를 통한 개념 간 참조
- `index.md`를 통한 점진적 공개(progressive disclosure) 지원

---

## 5. agentic-stack Data Layer 확장 설계

### 5.1 agentic-stack 개요

`agentic-stack`은 하나의 portable한 `.agent/` 폴더를 여러 Coding Agent 하네스(Claude Code, Cursor, Windsurf, **Antigravity** 등)에서 공유할 수 있게 해주는 프레임워크다.

기존 Data Layer는 다음 기능을 제공한다:
- 하네스 이벤트 수집
- Cron 실행 타임라인
- KPI 요약
- 토큰/비용 추정
- `dashboard.html`, `daily-report.md` 생성

### 5.2 확장 목표

기존 Data Layer에 **OKF 지식베이스 Connector**를 추가하여:

1. Coding Agent가 자연어로 OKF 지식베이스 내 개념/스키마를 조회
2. 조회 결과를 사용자에게 응답으로 제공
3. agentic-stack의 기존 데이터 수집/모니터링 기능과 통합

### 5.3 확장 아키텍처

```
.agent/
├── tools/
│   ├── data_layer_export.py      # 기존 Data Layer Export
│   ├── data_layer_okf.py         # [신규] OKF Connector
│   ├── okf_query.py              # [신규] OKF 조회 엔트리포인트
│   └── ...
├── skills/
│   ├── data-layer/
│   │   └── SKILL.md              # 기존 data-layer 스킬 (확장)
│   └── okf-query/
│       └── SKILL.md              # [신규] OKF 조회 전용 스킬
├── data-layer/
│   ├── exports/                  # 기존 Export 결과
│   └── okf-cache/                # [신규] OKF 조회 캐시
└── config/
    └── okf-config.yaml           # [신규] OKF 번들 경로 설정
```

### 5.4 OKF Connector 구현 (data_layer_okf.py)

```python
#!/usr/bin/env python3
"""
OKF Knowledge Base Connector for agentic-stack Data Layer

Usage:
    python3 .agent/tools/data_layer_okf.py --query "user schema"
    python3 .agent/tools/data_layer_okf.py --concept "schemas/users"
    python3 .agent/tools/data_layer_okf.py --list-concepts
"""

import argparse
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional

class OKFConnector:
    def __init__(self, bundle_path: str):
        self.bundle_path = Path(bundle_path)
        
    def list_concepts(self) -> List[Dict]:
        """번들 내 모든 개념 목록 반환"""
        concepts = []
        for md_file in self.bundle_path.rglob("*.md"):
            if md_file.name in ["index.md", "log.md"]:
                continue
            concept = self._parse_concept(md_file)
            if concept:
                concepts.append(concept)
        return concepts
    
    def get_concept(self, concept_id: str) -> Optional[Dict]:
        """특정 개념 ID로 개념 조회"""
        # concept_id: "schemas/users" -> schemas/users.md
        md_path = self.bundle_path / f"{concept_id}.md"
        if not md_path.exists():
            return None
        return self._parse_concept(md_path)
    
    def search_concepts(self, query: str) -> List[Dict]:
        """자연어 쿼리로 개념 검색 (키워드 기반)"""
        results = []
        query_lower = query.lower()
        for concept in self.list_concepts():
            # title, description, tags, 본문에서 검색
            score = self._calculate_relevance(concept, query_lower)
            if score > 0:
                concept["relevance_score"] = score
                results.append(concept)
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)
    
    def _parse_concept(self, md_path: Path) -> Dict:
        """Markdown 파일에서 Frontmatter와 본문 파싱"""
        content = md_path.read_text(encoding="utf-8")
        parts = re.split(r'^---\s*$', content, flags=re.MULTILINE)
        
        if len(parts) < 3:
            return None
            
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        
        return {
            "id": str(md_path.relative_to(self.bundle_path)).replace(".md", ""),
            "path": str(md_path),
            "frontmatter": frontmatter,
            "body": body,
            "schema": self._extract_schema(body)  # Schema 타입일 경우
        }
    
    def _extract_schema(self, body: str) -> Optional[List[Dict]]:
        """본문에서 Markdown 테이블 형식의 스키마 추출"""
        # Schema 섹션에서 테이블 파싱
        # ...
        pass
    
    def _calculate_relevance(self, concept: Dict, query: str) -> float:
        """간단한 키워드 기반 관련도 계산"""
        score = 0.0
        text = " ".join([
            concept.get("frontmatter", {}).get("title", ""),
            concept.get("frontmatter", {}).get("description", ""),
            " ".join(concept.get("frontmatter", {}).get("tags", [])),
            concept.get("body", "")
        ]).lower()
        
        for word in query.split():
            if word in text:
                score += 1.0
        return score / max(1, len(query.split()))
```

### 5.5 OKF Query Skill (SKILL.md)

```markdown
---
name: okf-query
description: OKF 지식베이스에서 개념과 스키마를 자연어로 조회합니다.
---

# OKF Query Skill

이 스킬은 OKF(Open Knowledge Format) 지식베이스에서 개념과 스키마 정보를
자연어로 조회할 수 있게 해줍니다.

## 사용법

사용자가 OKF 지식베이스에 대해 질문하면 다음 도구를 사용하세요:

### 개념 목록 조회
```bash
python3 .agent/tools/data_layer_okf.py --list-concepts
```

### 특정 개념 조회
```bash
python3 .agent/tools/data_layer_okf.py --concept "schemas/users"
```

### 자연어 검색
```bash
python3 .agent/tools/data_layer_okf.py --query "사용자 테이블 스키마"
```

## 응답 형식

조회 결과는 다음 형식으로 사용자에게 제공하세요:

1. **개념 정보**: title, description, type, tags
2. **스키마 정보**: 컬럼명, 타입, 설명이 포함된 테이블
3. **관련 개념**: 링크된 다른 개념들

## 예제

**사용자**: "user 테이블 구조를 알려줘"

**응답**:
```
User Schema
- 설명: 사용자 정보를 저장하는 테이블 스키마입니다.
- 태그: user, schema, authentication

| Column | Type | Description |
|--------|------|-------------|
| user_id | STRING | 고유 사용자 식별자 |
| email | STRING | 사용자 이메일 (고유) |
| name | STRING | 사용자 이름 |
| created_at | TIMESTAMP | 계정 생성 일시 |
| status | STRING | 계정 상태 |

관련 개념: Orders (/schemas/orders.md)
```
```

---

## 6. openkb 통합 설계

### 6.1 openkb 개요

`openkb`는 LLM을 활용하여 raw 문서를 구조화된 위키 스타일의 지식베이스로 컴파일하는 CLI 도구다. 주요 특징:

- PDF, Word, Markdown, PowerPoint, HTML, Excel, CSV, URL 등 다양한 포맷 지원
- PageIndex 기반 벡터리스 검색으로 장문 문서 처리
- OKF 스펙을 따르는 위키 페이지 생성
- Obsidian 호환 Markdown 파일 생성

### 6.2 openkb 활용 흐름

```bash
# 1. OKF 번들 생성 (openkb init)
mkdir my-okf-kb && cd my-okf-kb
openkb init

# 2. raw 문서 추가 (자동 컴파일)
openkb add schemas/users.md
openkb add schemas/orders.md
openkb add schemas/products.md
openkb add dataset/sales_description.md

# 3. 지식베이스 상태 확인
openkb status
openkb list

# 4. 자연어 질의
openkb query "user 테이블의 컬럼은 무엇인가요?"
openkb query "orders와 products의 관계를 설명해줘"

# 5. 대화형 탐색
openkb chat
> "product 카테고리별 매출 현황을 알려줘"
> "user가 작성한 주문 내역을 조회하려면 어떻게 해?"
```

### 6.3 openkb 연동 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Coding Agent                        │
│              (antigravity + agentic-stack)             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              .agent/tools/data_layer_okf.py            │
│              (OKF Connector - 통합 인터페이스)          │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌───────────────────┐   ┌───────────────────────────┐
│   OKF 번들 직접   │   │   openkb CLI 호출         │
│   (Markdown 파싱) │   │   (컴파일/쿼리 위임)       │
└───────────────────┘   └───────────────────────────┘
```

### 6.4 openkb 통합 옵션

| 옵션 | 설명 | 장단점 |
|------|------|--------|
| **A. openkb CLI 호출** | `subprocess`로 openkb 명령어 실행 | 구현 간단, openkb 기능 최대 활용. 단, 외부 의존성 |
| **B. openkb API 사용** | openkb의 Python API 직접 호출 | 더 정교한 제어 가능. 단, API 문서 확인 필요 |
| **C. OKF 직접 파싱** | openkb 없이 OKF 번들 직접 읽기 | 의존성 최소화. 단, openkb의 LLM 기반 기능 활용 불가 |

**권장**: Phase 1에서는 **옵션 C (직접 파싱)**로 빠르게 프로토타입하고, Phase 2에서 **옵션 A (openkb CLI)**로 전환하여 LLM 기반 컴파일/쿼리 기능을 검증한다.

---

## 7. 개발 단계 (Phases)

### 7.1 Phase 0: 환경 준비 (1주)

| 작업 | 내용 | 산출물 |
|------|------|--------|
| 0.1 | agentic-stack 설치 | `agentic-stack` CLI 정상 동작 확인 |
| 0.2 | Antigravity CLI 설정 | Coding Agent 실행 환경 구성 |
| 0.3 | openkb 설치 | `pip install openkb` |
| 0.4 | 프로젝트 디렉토리 구조 생성 | Git repository 초기화 |

### 7.2 Phase 1: OKF 지식베이스 구축 (1주)

| 작업 | 내용 | 산출물 |
|------|------|--------|
| 1.1 | OKF 번들 디렉토리 생성 | `okf-kb/` 디렉토리 구조 |
| 1.2 | user/order/product 스키마 OKF 정의 | `schemas/users.md`, `orders.md`, `products.md` |
| 1.3 | 인덱스 및 예제 문서 작성 | `index.md`, `examples/queries.md` |
| 1.4 | OKF SPEC 준수 검증 | lint 결과 |
| 1.5 | openkb로 컴파일 테스트 | `openkb add` 및 `openkb list` 정상 동작 |

### 7.3 Phase 2: agentic-stack Data Layer 확장 (2주)

| 작업 | 내용 | 산출물 |
|------|------|--------|
| 2.1 | OKF Connector 기본 구현 (`data_layer_okf.py`) | 개념 목록 조회, 단일 개념 조회 기능 |
| 2.2 | 자연어 검색 기능 구현 | 키워드 기반 개념 검색 |
| 2.3 | 스키마 파싱 및 포맷팅 | Markdown 테이블 → 구조화된 응답 |
| 2.4 | OKF Query Skill 작성 (`SKILL.md`) | Coding Agent용 스킬 정의 |
| 2.5 | agentic-stack과 통합 테스트 | Antigravity 내에서 스킬 호출 확인 |

### 7.4 Phase 3: openkb 통합 실험 (1.5주)

| 작업 | 내용 | 산출물 |
|------|------|--------|
| 3.1 | openkb CLI 연동 wrapper 구현 | `openkb_wrapper.py` |
| 3.2 | openkb query/chat 기능 테스트 | 자연어 질의 응답 검증 |
| 3.3 | OKF Connector에 openkb 통합 옵션 추가 | `--engine openkb` 플래그 |
| 3.4 | 성능/정확도 비교 (직접 파싱 vs openkb) | 비교 분석 보고서 |

### 7.5 Phase 4: Coding Agent 통합 실험 (1.5주)

| 작업 | 내용 | 산출물 |
|------|------|--------|
| 4.1 | Antigravity + agentic-stack 환경 구성 | `.agent/` 폴더 설정 |
| 4.2 | OKF Query Skill 주입 및 활성화 | Coding Agent가 스킬 인식 |
| 4.3 | 자연어 조회 시나리오 테스트 | 테스트 케이스 및 결과 |
| 4.4 | Data Layer Export와 통합 | OKF 조회 결과를 dashboard에 포함 |
| 4.5 | 문제점 및 개선사항 문서화 | 피드백 목록 |

### 7.6 Phase 5: 전용 Agent 개발 (3주)

| 작업 | 내용 | 산출물 |
|------|------|--------|
| 5.1 | Local LLM 선정 및 설정 | Ollama/llama.cpp 등 구성 |
| 5.2 | 전용 Agent 아키텍처 설계 | Intent Parser + Query Planner + Output Formatter |
| 5.3 | Core Engine 구현 (Python) | OKF 조회/LLM 추론/응답 생성 |
| 5.4 | CLI 인터페이스 구현 | 대화형 쿼리 환경 |
| 5.5 | agentic-stack 의존성 제거 검증 | 독립 실행 확인 |

### 7.7 Phase 6: 비교 평가 및 최적화 (2주)

| 작업 | 내용 | 산출물 |
|------|------|--------|
| 6.1 | Coding Agent vs 전용 Agent 성능 비교 | 정확도/응답 시간/리소스 사용량 |
| 6.2 | 사용자 시나리오 기반 테스트 | 실제 사용 사례 검증 |
| 6.3 | 최적화 및 버그 수정 | 개선된 버전 |
| 6.4 | 최종 문서화 및 발표 자료 | 완전한 프로젝트 문서 |

---

## 8. 전체 일정

```
Phase 0: 환경 준비           ████████░░░░░░░░░░░░ (1주)
Phase 1: OKF KB 구축         ░░░░░░░░████████░░░░ (1주)
Phase 2: Data Layer 확장     ░░░░░░░░░░░░░░██████ (2주)
Phase 3: openkb 통합         ░░░░░░░░░░░░░░░░░░██ (1.5주)
Phase 4: Coding Agent 실험   ░░░░░░░░░░░░░░░░░░░░ (1.5주)
Phase 5: 전용 Agent 개발     ░░░░░░░░░░░░░░░░░░░░ (3주)
Phase 6: 비교 평가/최적화    ░░░░░░░░░░░░░░░░░░░░ (2주)
─────────────────────────────────────────────────────────
Total: 약 12주
```

---

## 9. 위험 요소 및 대응 방안

| 위험 | 영향 | 확률 | 대응 방안 |
|------|------|------|-----------|
| **OKF SPEC 변경** | 중간 | 낮음 | v0.1 안정화 단계, 변경 시 최신 SPEC 반영 |
| **agentic-stack 호환성** | 높음 | 중간 | 최신 버전 유지, Antigravity 지원 확인 |
| **openkb 설치/실행 문제** | 중간 | 중간 | GitHub 이슈 확인, 대체 옵션(직접 파싱) 준비 |
| **Local LLM 성능** | 높음 | 중간 | 경량 모델(Mistral 7B 등) 우선 검토, 필요시 API LLM 백업 |
| **자연어 이해 정확도** | 높음 | 높음 | 의도 분류기 + 규칙 기반 하이브리드 접근 |
| **일정 지연** | 중간 | 중간 | MVP 우선 개발, 추가 기능은 Phase 6 이후로 연기 |

---

## 10. 성공 지표 (KPIs)

| 지표 | 측정 방법 | 목표치 |
|------|-----------|--------|
| **자연어 질의 정확도** | 정답 스키마 대비 응답 정확도 | ≥ 85% |
| **응답 시간** | 질의 → 응답까지 소요 시간 | ≤ 5초 |
| **지원 질의 유형 수** | 테스트 케이스 커버리지 | ≥ 20개 시나리오 |
| **Coding Agent vs 전용 Agent 비용** | 토큰/추론 비용 비교 | 전용 Agent ≤ Coding Agent의 50% |
| **OKF 번들 컴파일 시간** | `openkb add` 실행 시간 | ≤ 30초 (문서 10개 기준) |

---

## 11. 다음 단계 (Next Actions)

1. **Phase 0 시작**: agentic-stack, openkb, Antigravity CLI 설치 및 환경 구성
2. **OKF 번들 초안 작성**: user/order/product 스키마 OKF 정의
3. **주간 미팅 일정**: 매주 금요일 진행 상황 점검
4. **Git repository 생성**: 프로젝트 코드 및 문서 버전 관리 시작

---

## 12. 부록

### A. OKF SPEC 주요 용어

| 용어 | 설명 |
|------|------|
| **Knowledge Bundle** | 지식 문서의 자체 포함된 계층적 컬렉션. 배포 단위 |
| **Concept** | 번들 내 단일 지식 단위. 하나의 Markdown 문서로 표현 |
| **Concept ID** | 번들 내 파일 경로에서 `.md` 확장자 제거한 경로 |
| **Frontmatter** | `---`로 구분된 YAML 메타데이터 블록 |
| **Body** | Frontmatter 이후의 모든 내용 |
| **Link** | 개념 간 관계를 표현하는 Markdown 링크 |

### B. agentic-stack 지원 하네스

- Claude Code
- Cursor
- Windsurf
- OpenCode
- OpenClaw
- GitHub Copilot CLI
- Google Gemini CLI
- Hermes
- Pi Coding Agent
- Codex
- **Antigravity** (사용 예정)
- DIY Python loop

### C. openkb 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `openkb init` | 새 지식베이스 초기화 |
| `openkb add <file\|dir\|url>` | 문서 추가 및 자동 컴파일 |
| `openkb list` | 인덱싱된 문서 및 개념 목록 |
| `openkb status` | 지식베이스 통계 표시 |
| `openkb query "<질문>"` | 자연어 질의 |
| `openkb chat` | 대화형 세션 시작 |

---

> **문서 변경 이력**
>
> | 버전 | 일자 | 변경 내용 | 작성자 |
> |------|------|-----------|--------|
> | v1.0 | 2026-06-26 | 최초 작성 | - |