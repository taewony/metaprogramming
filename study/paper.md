# 논문 권장 방향

세 가지 중 하나만 선택하기보다 다음 순서로 통합하는 것이 가장 좋습니다.

> **3번을 연구의 중심축으로 삼고, 1번을 실험 대상 시스템으로 확장한 뒤, 2번을 통제된 적응 실험으로 추가한다.**

실제 개발 순서는 조금 더 세분화해야 합니다.

```text
현재 DB Agent 고정
        ↓
3-lite: Spec·Trace 계측 기반 구축
        ↓
1: OKF + DB 통합 질의 Agent
        ↓
3-full: Spec–Trace Conformance SDLC/IDE
        ↓
2: Bounded Runtime Adaptation
        ↓
Multi-user Target System + 논문 실험
```

즉, **당장 2번의 “runtime adaptation 최대화”부터 시작하지 않는 것**이 중요합니다. 측정·명세·검증 체계가 없는 상태에서 적응 능력을 높이면 무엇이 개선됐고 무엇이 퇴행했는지 설명하기 어려워집니다.

---

# 1. 현재 위치에 대한 평가

현재 구현 상태는 이미 일반적인 PoC 수준을 넘어섰습니다.

```text
ActiveGraph 기반 DB QA Agent
├── CLI 실행
├── 자연어 질의
├── DB 조회
├── 답변 생성
├── 외부 Eval Pack 로딩
└── Eval-run을 통한 기본 처리 가능성 검사
```

ActiveGraph는 객체와 typed relation으로 세계 상태를 표현하고, behavior가 event에 반응하며, 모든 변경을 append-only event log에 기록합니다. 또한 replay, fork, structural diff, pack, policy 및 runtime introspection을 기본 개념으로 제공합니다. 따라서 지금 시스템은 단순한 QA Agent가 아니라 **실행 이력을 재현하고 비교할 수 있는 실험 가능한 Agent Runtime** 위에 구축되어 있습니다. ([GitHub][1])

다음 단계에서는 “질문에 답을 잘하는가?”보다 한 단계 높은 질문을 다뤄야 합니다.

> **설계자가 의도한 Agent와 실제 실행된 Agent가 얼마나 일치하는가?**

이 질문이 3번 연구 방향의 핵심입니다.

---

# 2. 세 방향의 역할을 다시 정의해야 한다

| 방향                    | 프로젝트에서의 역할   | 논문에서의 역할    |  우선순위 |
| --------------------- | ------------ | ----------- | ----: |
| 1. OKF 질의 시스템         | 기능·데이터 범위 확장 | 복합 질의 실험 환경 | 1차 확장 |
| 2. Runtime adaptation | 운영 복구 및 적응   | 통제된 처치 변수   |   마지막 |
| 3. Spec–Behavior 일치성  | 개발·검증 플랫폼    | 핵심 연구 기여    |   최우선 |

## 1번만 수행할 경우

DB QA에서 문서 QA/RAG로 기능을 확장한 좋은 프로젝트는 되지만, 논문 기여는 “또 하나의 문서·DB 통합 Agent”로 보일 가능성이 큽니다.

## 2번만 수행할 경우

흥미롭지만, adaptation의 성공 여부를 판정할 기준이 불명확합니다. Agent가 스스로 behavior나 harness를 변경한 뒤 자기 평가까지 하면 self-certification 문제가 생깁니다.

## 3번을 중심에 둘 경우

ActiveGraph의 event-sourced 특성을 직접 활용하면서 다음을 연구할 수 있습니다.

* 설계 의도와 실행 궤적의 대응
* 명세 기반 eval 생성
* trace 기반 failure localization
* behavior version 간 fork-and-diff
* 적응 전후의 정량적 비교
* 운영 중 spec drift 탐지

이 방향은 기존의 model-based testing, runtime verification, process-mining conformance checking과 LLM Agent engineering을 연결할 수 있습니다. Runtime verification은 실행 trace를 명세와 대조하는 기술이고, process mining은 event log와 normative process model 사이의 적합성을 분석합니다. ([IMDEA Software Institute][2])

---

# 3. 제안하는 전체 연구 주제

가칭으로 다음과 같이 정의할 수 있습니다.

## **Spec-Driven and Trace-Conformant SDLC for Adaptive Knowledge Agents**

또는 논문 제목 형태로는 다음이 적절합니다.

> **System Model Specification and Trace Conformance Checking for Event-Sourced Adaptive LLM Agents**

핵심 아이디어는 다음과 같습니다.

```text
System Model Spec
       │
       │ Cognitive Compile
       ▼
ActiveGraph Agent
  ├── Object Types
  ├── Relations
  ├── Behaviors
  ├── Policies
  ├── Tools
  └── Eval Obligations
       │
       │ Execution
       ▼
Event Log / Trace
       │
       │ Conformance Analysis
       ▼
Specification–Execution Gap
       │
       ├── Debugging
       ├── Evaluation
       ├── Visualization
       └── Runtime Adaptation
```

논문의 핵심 기여는 Cognitive Compile이라는 비유 자체보다 다음 세 가지가 되어야 합니다.

1. **Agent용 System Model Spec**
2. **Spec과 ActiveGraph event trace의 일치성 분석 방법**
3. **일치성 결과를 이용한 통제된 runtime adaptation 절차**

---

# 4. 첫 번째 단계: 현재 DB Agent를 Baseline으로 고정

OKF 기능을 추가하기 전에 현재 구현을 실험 가능한 기준점으로 고정해야 합니다.

## Baseline release

```text
db-agent-v0.1
eval-pack-v1
system-model-v0
trace-schema-v1
```

최소한 다음 항목을 기록하십시오.

* Agent version
* Pack version
* Behavior version
* Prompt hash
* DB schema version
* Eval pack version
* Model/provider/version
* 실행된 behavior 순서
* 생성된 event 목록
* tool invocation
* SQL
* 검색·조회 결과
* 최종 답변
* 비용과 latency
* 성공·실패 판정
* failure category

ActiveGraph는 structured logging, metrics, event sink, CLI inspect/replay/fork/diff/export-trace와 runtime 상태 조회를 제공합니다. 따라서 별도의 계측 체계를 처음부터 만들기보다 이 operator surface 위에 연구용 metadata를 추가하는 편이 좋습니다. ([GitHub][3])

## Event metadata에 추가할 필드

```yaml
spec_id: db-qa-spec-v0.1
requirement_id: REQ-DB-017
behavior_id: generate_sql
obligation_ids:
  - OBL-READ-ONLY
  - OBL-TENANT-FILTER
  - OBL-SCHEMA-VALID
evidence_refs:
  - schema:customers-v3
  - query-result:event-113
adaptation_id: null
eval_case_id: dbqa-0042
```

이 metadata가 있어야 나중에 “event가 많다”에서 끝나지 않고, **어떤 requirement를 만족하기 위해 발생한 event인가**를 분석할 수 있습니다.

---

# 5. 두 번째 단계: OKF 기반 문서·DB 통합 Agent

OKF는 현재 0.1 draft이며, Markdown 파일과 YAML frontmatter로 knowledge bundle과 concept을 표현합니다. Concept은 table이나 API 같은 자산뿐 아니라 metric, business process 같은 추상 지식도 표현할 수 있고, Markdown link를 통해 concept 관계를 구성합니다. OKF는 저장·검색·질의 엔진을 규정하지 않으므로, 이를 어떻게 소비할지는 Agent 설계자가 결정해야 합니다. ([GitHub][4])

따라서 OKF를 단순히 vector DB에 넣는 방식으로 구현하지 않는 것이 좋습니다.

## 권장 OKF Pack 구조

```text
packs/
└── okf_qa/
    ├── manifest.yaml
    ├── objects.py
    ├── relations.py
    ├── behaviors/
    │   ├── discover_bundle.py
    │   ├── classify_question.py
    │   ├── select_concepts.py
    │   ├── traverse_links.py
    │   ├── retrieve_content.py
    │   ├── verify_citations.py
    │   └── synthesize_answer.py
    ├── tools/
    │   ├── okf_reader.py
    │   ├── lexical_search.py
    │   └── vector_search.py
    └── policies/
        ├── provenance.yaml
        └── freshness.yaml
```

## Object types

```text
KnowledgeBundle
Concept
ConceptLink
ExternalCitation
DocumentSection
RetrievalCandidate
Evidence
Claim
Answer
```

## Relations

```text
Bundle CONTAINS Concept
Concept LINKS_TO Concept
Concept CITES ExternalSource
Question REQUIRES Concept
Claim SUPPORTED_BY Evidence
Evidence DERIVED_FROM Concept
```

## 핵심 Behavior

```text
QuestionReceived
    ↓
ClassifyInformationNeed
    ↓
SelectKnowledgeSource
    ├── DB
    ├── OKF
    └── DB + OKF
    ↓
PlanRetrieval
    ↓
TraverseConceptGraph
    ↓
ExecuteSQL / ReadConcept
    ↓
BuildEvidenceSet
    ↓
VerifyClaims
    ↓
GenerateAnswer
```

ActiveGraph에서 pack은 object type, behavior, tool, prompt, policy를 하나의 domain capability로 묶는 구조이므로, `db_qa`, `okf_qa`, `runtime_supervisor`를 별도 pack으로 분리하는 것이 framework의 방향과도 맞습니다. 공식 pack 프로젝트 역시 최소 Core Pack 위에 domain pack을 계층적으로 조합하는 방식을 사용합니다. ([GitHub][5])

---

# 6. OKF 실험은 “문서 QA 정확도”만 측정하면 부족하다

질문 유형을 명시적으로 나누어야 합니다.

## A. DB-only 질의

```text
VIP 고객은 몇 명인가?
지난달 주문 금액이 가장 큰 고객은 누구인가?
```

## B. OKF-only 질의

```text
VIP 고객 등급의 정의는 무엇인가?
주문 취소 정책은 어떻게 되어 있는가?
```

## C. DB + OKF 결합 질의

```text
VIP 기준에 해당하지만 현재 등급이 일반으로 등록된 고객이 있는가?
```

처리 과정:

```text
OKF → VIP 기준 검색
DB  → 고객별 포인트와 등급 검색
Agent → 기준과 실제 데이터 비교
```

## D. Contradiction 질의

```text
문서에는 VIP 기준이 30,000점이라고 되어 있지만,
DB의 실제 등급 배정과 일치하는가?
```

## E. Freshness 질의

```text
현재 적용되는 환불 정책은 무엇인가?
```

이 경우 OKF concept version, source citation, updated timestamp를 확인해야 합니다.

## F. Insufficient-evidence 질의

정보가 없을 때 답을 만들어내지 않고 다음과 같이 판단해야 합니다.

```text
ANSWER
PARTIAL_ANSWER
CLARIFICATION_REQUIRED
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
ACCESS_DENIED
```

---

# 7. 세 번째 단계: System Model Spec 설계

처음부터 복잡한 정형 언어를 만들 필요는 없습니다. YAML 기반의 최소 DSL로 시작하는 것이 좋습니다.

```yaml
agent:
  id: enterprise-knowledge-agent
  version: 0.2

goals:
  - id: G-ANSWER
    description: Answer questions using authorized DB and OKF evidence.

invariants:
  - id: INV-READ-ONLY
    rule: database.operations subset_of [SELECT, EXPLAIN]

  - id: INV-PROVENANCE
    rule: every(answer.claims) has supporting_evidence

  - id: INV-TENANT
    rule: every(data_access) matches request.tenant_id

behaviors:
  - id: classify_question
    subscribes:
      - QuestionReceived
    emits:
      - QuestionClassified
    postconditions:
      - source_type in [db, okf, hybrid]

  - id: generate_sql
    subscribes:
      - DatabaseQueryPlanned
    emits:
      - SQLProposed
    obligations:
      - INV-READ-ONLY
      - INV-TENANT

  - id: synthesize_answer
    subscribes:
      - EvidenceSetCompleted
    emits:
      - AnswerProposed
    obligations:
      - INV-PROVENANCE

eval_obligations:
  - id: EVAL-HYBRID-001
    requirement: G-ANSWER
    required_behaviors:
      - classify_question
      - select_concepts
      - execute_sql
      - synthesize_answer

adaptations:
  - id: ADAPT-RETRIEVER-FALLBACK
    trigger: retrieval.confidence < 0.6
    allowed_action: switch_to_hybrid_retrieval
    max_attempts: 1
```

## Cognitive Compile의 출력

```text
System Model Spec
├── ActiveGraph object definitions
├── Behavior registration
├── Relation definitions
├── Runtime policies
├── Monitor rules
├── Eval test skeletons
├── Trace obligations
└── IDE visualization metadata
```

모든 것을 자동 생성할 필요는 없습니다.

초기에는 다음 정도면 충분합니다.

```text
Spec → validation
Spec → behavior/event mapping table
Spec → runtime monitor configuration
Spec → eval obligation generation
Spec → visualization graph
```

코드 전체 생성은 후속 연구로 남겨도 됩니다.

---

# 8. 네 번째 단계: Spec–Trace Conformance Engine

이 부분이 논문의 가장 중요한 구현입니다.

## 일치성의 다섯 수준

### 1. Structural conformance

필요한 behavior와 event가 존재했는가?

```text
Expected: QuestionReceived → QueryPlanned → SQLExecuted → AnswerGenerated
Observed: QuestionReceived → SQLExecuted → AnswerGenerated

Deviation: QueryPlanned missing
```

### 2. Ordering conformance

event 순서가 명세에서 허용된 순서인가?

```text
CitationVerified가 AnswerPublished보다 먼저 발생했는가?
```

### 3. Semantic conformance

event payload가 조건을 만족하는가?

```text
SQLProposed.statement is read_only
Answer.claims have evidence_refs
```

### 4. Policy conformance

tool과 데이터 접근이 권한 범위 내에 있는가?

```text
behavior X가 tool Y를 호출할 권한이 있는가?
tenant filtering이 적용되었는가?
```

### 5. Adaptation conformance

적응이 승인된 trigger와 범위 안에서 실행됐는가?

```text
retrieval confidence가 정상인데 fallback을 실행했는가?
최대 재시도 횟수를 넘었는가?
승인되지 않은 behavior variant를 사용했는가?
```

---

# 9. Conformance 정량 지표

## Trace Fitness

실행 trace가 허용된 System Model 경로에 얼마나 잘 정렬되는지 측정합니다.

```text
Trace Fitness
= 1 - weighted_deviations / maximum_possible_deviations
```

## Spec Coverage

eval suite가 명세의 obligation을 얼마나 실행했는지 측정합니다.

```text
Spec Coverage
= exercised obligations / reachable obligations
```

## Behavioral Precision

실행된 action 가운데 명세상 허용되고 질의 해결에 필요했던 action의 비율입니다.

```text
Behavioral Precision
= relevant sanctioned actions / all observed actions
```

## Evidence Completeness

```text
Evidence Completeness
= supported claims / total factual claims
```

## Recovery Effectiveness

```text
Recovery Effectiveness
= successfully recovered failures / adaptation attempts
```

## Adaptation Safety

```text
Adaptation Safety
= adaptations without new invariant violations
  / total adaptations
```

## Diagnosis Locality

failure 발생 후 원인이 되는 behavior/event를 얼마나 좁게 특정할 수 있는지 측정합니다.

```text
Diagnosis Locality
= suspected events / total trace events
```

작을수록 좋은 지표입니다.

---

# 10. IDE는 일반 Trace Viewer가 아니어야 한다

ActiveGraph pack 프로젝트에는 이미 React 기반 Inspector UI가 있습니다. 따라서 단순히 object graph나 event 목록을 보여주는 UI를 만들면 연구 기여가 약합니다. ([GitHub][5])

당신의 IDE는 **Spec–Implementation–Execution–Evaluation을 동시에 연결하는 Agent Engineering Workbench**여야 합니다.

## 권장 화면

### A. System Model View

```text
Goals
 └── Requirements
      └── Behaviors
           └── Events
                └── Tools / Policies
```

### B. Trace Overlay

명세 graph 위에 실제 실행 경로를 겹쳐 보여줍니다.

```text
초록색: 명세와 일치
노란색: 허용되지만 예상하지 않은 경로
빨간색: invariant 위반
회색: eval에서 미실행
```

### C. Timeline

```text
Time ──────────────────────────────────────────>

Question   Plan   Retrieve   SQL   Verify   Answer
   ●────────●──────●────────●──────●────────●
```

각 event를 클릭하면 다음을 표시합니다.

* 입력 object
* 출력 patch
* behavior version
* prompt hash
* tool invocation
* evidence
* 관련 spec obligation

### D. Fork Diff

```text
Original Run
    ├── Retriever A
    └── Failure

Forked Run
    ├── Retriever B
    └── Success
```

다음 차이를 보여줍니다.

* 추가·누락된 event
* object state 변화
* 답변 차이
* 비용 차이
* latency 차이
* conformance score 차이

ActiveGraph의 fork-and-diff는 특정 event에서 run을 분기해 다른 구성으로 실행하고 parent와 구조적으로 비교하도록 설계되어 있으므로, adaptation 실험의 핵심 실험 장치로 사용할 수 있습니다. ([GitHub][1])

### E. Eval Matrix

| Eval case | Answer | Trace | Policy | Evidence | Adaptation |
| --------- | -----: | ----: | -----: | -------: | ---------: |
| DB-001    |   Pass |  Pass |   Pass |     Pass |        N/A |
| OKF-012   |   Pass |  Fail |   Pass |     Fail |        N/A |
| DRIFT-004 |   Pass |  Pass |   Pass |     Pass |    Success |

최종 답변이 맞아도 trace나 evidence가 잘못되면 전체적으로 실패 처리할 수 있어야 합니다.

---

# 11. 다섯 번째 단계: Runtime Adaptation

이 단계에서 2번 방향을 추가합니다.

핵심은 **adaptation 최대화가 아니라 adaptation의 통제 가능성 최대화**입니다.

## 권장 adaptation loop

```text
Runtime Failure
      ↓
Failure Classification
      ↓
Select Approved Candidate
      ↓
Fork at Failure Event
      ↓
Run Candidate in Trial Fork
      ↓
Conformance + Eval Check
      ↓
Compare with Original
      ↓
Use Temporarily / Reject / Escalate
```

## 처음 허용할 adaptation

### Request-level adaptation

* query re-planning
* SQL 재생성
* 검색어 확장
* retrieval 방식 변경
* 답변 범위 축소
* clarification
* abstention

### Harness variant selection

미리 정의된 후보 중 선택합니다.

```text
FAST
ACCURATE
HYBRID_RETRIEVAL
SCHEMA_DRIFT_RECOVERY
SAFE_MINIMAL
```

### 제한적으로 허용할 behavior adaptation

* behavior parameter 변경
* prompt profile 변경
* model routing 변경
* retriever variant 변경
* verification depth 변경

## 초기에 금지할 adaptation

* production 코드 직접 수정
* 새 tool 생성과 즉시 활성화
* 권한 확대
* invariant 변경
* 평가 기준 변경
* DB schema 변경
* 새로운 behavior를 자기 판단만으로 promote

ActiveGraph의 별도 behavior-drafts 실험은 LLM이 작성한 behavior를 inert draft로 기록하고, static analysis와 test를 거친 뒤 sandbox fork에서 실행하며, diff와 policy를 확인하고 명시적 결정으로 promote하는 수명주기를 제시합니다. 따라서 논문의 신규성은 단순한 “Agent self-modification”이 아니라, **System Model Spec 및 external eval pack에 근거한 adaptation 검증과 promotion**에 두어야 합니다. ([GitHub][6])

---

# 12. External Eval Pack을 확장해야 한다

현재의 Eval Pack이 “질문을 처리할 수 있는가?”를 검사한다면 다음 단계에서는 **답변과 궤적을 함께 정의**해야 합니다.

```yaml
case:
  id: hybrid-vip-001
  query: "VIP 기준을 만족하지만 등급이 일반인 고객을 찾아줘"

expected:
  outcome:
    type: answer
    required_entities:
      - customer

  source_usage:
    required:
      - okf
      - database

  trace:
    required_behaviors:
      - classify_question
      - select_okf_concepts
      - extract_business_rule
      - plan_database_query
      - execute_sql
      - compare_rule_and_data
      - verify_evidence

    forbidden_behaviors:
      - write_database

  policies:
    - read_only
    - tenant_isolation
    - evidence_required

  evidence:
    min_okf_concepts: 1
    min_database_results: 1

  performance:
    max_tool_calls: 8
    max_latency_ms: 10000
```

이렇게 하면 Eval Pack이 단순 question-answer dataset이 아니라 다음 역할을 합니다.

```text
Requirement Specification
Test Oracle
Trace Contract
Policy Contract
Performance Budget
Adaptation Acceptance Criteria
```

---

# 13. 논문 연구 질문

## RQ1. System Model Spec의 유효성

> Agent의 goal, behavior, event, policy 및 eval obligation을 명세화하면 개발된 Agent의 구조와 실행을 체계적으로 추적할 수 있는가?

측정:

* requirement–behavior traceability
* 명세 누락 발견 수
* eval coverage
* 개발자가 원인을 찾는 시간

---

## RQ2. Trace 기반 평가의 효과

> 최종 답변만 평가하는 방식보다 event trace conformance 평가가 잠재적 결함을 더 잘 탐지하는가?

예를 들어 답변은 맞지만 다음과 같은 내부 결함이 있을 수 있습니다.

* 잘못된 문서를 읽었음
* tenant filter가 빠졌음
* 불필요하게 민감한 table을 조회함
* 근거 없이 우연히 맞았음
* 검증 behavior를 건너뜀

비교:

```text
Output-only evaluation
vs.
Output + trace conformance evaluation
```

---

## RQ3. OKF 구조 활용의 효과

> OKF의 concept, link 및 citation 구조를 활용한 retrieval이 Markdown을 평탄화한 일반 RAG보다 복합 질의에서 더 나은가?

비교군:

```text
Flat chunk RAG
Vector-only OKF
Structure-first OKF traversal
Structure + vector hybrid
```

측정:

* answer correctness
* evidence completeness
* concept traversal precision
* retrieval cost
* hallucination
* cross-source reasoning accuracy

OKF는 query infrastructure를 규정하지 않기 때문에, 이 비교 자체가 의미 있는 consumer-side 연구가 될 수 있습니다. ([GitHub][4])

---

## RQ4. Bounded adaptation의 효과

> Spec과 external eval에 의해 제한된 fork-based runtime adaptation이 고정 Agent보다 failure recovery를 개선하면서 invariant violation을 증가시키지 않는가?

비교군:

```text
A. No adaptation
B. Blind retry
C. LLM self-reflection
D. Spec-bounded fork adaptation
```

측정:

* recovery success
* 추가 latency
* 추가 비용
* 신규 failure 발생률
* invariant violations
* rollback rate
* wrong adaptation rate

---

# 14. Fault Injection 실험

논문을 위해서는 정상 질의만으로 부족합니다.

## 데이터 변경

* table 추가·삭제
* column rename
* join path 변경
* enum 값 변경
* 데이터 타입 변경

## 문서 변경

* OKF concept 삭제
* 깨진 link
* 오래된 citation
* 상충하는 concept
* 최신·구버전 동시 존재
* bundle 간 동일 concept ID

## Runtime failure

* tool timeout
* DB connection failure
* retriever failure
* malformed LLM output
* token budget 초과
* 반복 behavior
* event queue overload

## 보안·정책 failure

* tenant leakage 시도
* write SQL 생성
* forbidden table 접근
* prompt injection 문서
* citation fabrication
* unauthorized adaptation

## Harness drift

* prompt version 불일치
* behavior version 불일치
* model 변경
* policy pack 누락
* eval pack과 production pack 불일치

---

# 15. 실험군 구성

다음 네 시스템을 동일한 Eval Pack으로 비교하는 것이 좋습니다.

| 시스템                 | DB | OKF | Trace 검사 | Adaptation |
| ------------------- | -: | --: | -------: | ---------: |
| S0 Baseline         |  O |   X |        X |          X |
| S1 Knowledge Agent  |  O |   O |        X |          X |
| S2 Conformant Agent |  O |   O |        O |          X |
| S3 Adaptive Agent   |  O |   O |        O |          O |

이 구성이 좋은 이유는 각 기능의 효과를 단계적으로 분리할 수 있기 때문입니다.

```text
S0 → S1: OKF 효과
S1 → S2: Spec/Trace conformance 효과
S2 → S3: Runtime adaptation 효과
```

추가 ablation도 가능합니다.

* System Model Spec 제거
* semantic conformance 제거
* fork sandbox 제거
* external evaluator 제거
* OKF link traversal 제거

---

# 16. 권장 Repository 구조

```text
project/
├── system-model/
│   ├── agent.yaml
│   ├── invariants.yaml
│   ├── failure-taxonomy.yaml
│   └── adaptation-policies.yaml
│
├── packs/
│   ├── core_qa/
│   ├── db_qa/
│   ├── okf_qa/
│   ├── evidence/
│   ├── evaluator/
│   └── runtime_supervisor/
│
├── knowledge/
│   ├── bundles/
│   └── bundle-registry.yaml
│
├── evalpacks/
│   ├── db-basic/
│   ├── okf-basic/
│   ├── hybrid/
│   ├── failure-injection/
│   └── security/
│
├── conformance/
│   ├── spec_loader.py
│   ├── trace_normalizer.py
│   ├── aligner.py
│   ├── monitors.py
│   ├── metrics.py
│   └── reports.py
│
├── adaptation/
│   ├── failure_classifier.py
│   ├── candidate_registry.py
│   ├── trial_runner.py
│   ├── promotion_policy.py
│   └── rollback.py
│
├── ide/
│   ├── api/
│   └── web/
│
├── experiments/
│   ├── baselines/
│   ├── fault_injection/
│   ├── ablations/
│   └── results/
│
└── paper/
    ├── research-questions.md
    ├── experiment-protocol.md
    └── figures/
```

---

# 17. 12주 실행 로드맵

## 1–2주: Baseline 고정

* 현재 DB Agent release
* Eval Pack schema 고정
* trace metadata 확장
* 30~50개 기본 질의 작성
* failure taxonomy 작성
* baseline 결과 저장

산출물:

```text
db-agent-v0.1
eval-pack-v1
baseline-report-v1
```

## 3–5주: OKF Pack

* OKF bundle loader
* concept/link/citation parser
* structure-first retrieval
* DB/OKF query router
* provenance graph
* hybrid 질의 30개 추가

산출물:

```text
okf-qa-pack-v0.1
hybrid-eval-pack-v1
```

## 6–8주: System Model 및 Conformance Engine

* 최소 System Model DSL
* behavior/event mapping
* invariant monitor
* trace aligner
* conformance metrics
* CLI report

CLI 예:

```bash
agent spec validate system-model/agent.yaml
agent eval run evalpacks/hybrid
agent trace check runs/run-0042
agent trace explain runs/run-0042
agent trace diff runs/run-0042 runs/run-0042-fork
```

## 9–10주: IDE

* Spec graph
* trace overlay
* timeline
* eval matrix
* fork diff
* failure heatmap

## 11–12주: Bounded Adaptation

* failure classifier
* approved adaptation registry
* trial fork
* conformance gate
* temporary activation
* escalation 및 rollback

---

# 18. 가장 먼저 구현할 구체적인 Vertical Slice

다음 한 사례를 end-to-end로 완성하는 것을 첫 목표로 잡는 것이 좋습니다.

## 질의

```text
“VIP 기준을 충족하지만 실제 등급이 VIP가 아닌 고객이 있는가?”
```

## 필요한 처리

```text
1. 질문 분류
2. OKF에서 VIP 기준 concept 탐색
3. 기준과 citation 확인
4. DB schema 탐색
5. 고객 포인트와 등급 SQL 생성
6. read-only 및 tenant policy 검증
7. SQL 실행
8. 문서 규칙과 DB 결과 비교
9. evidence-backed answer 생성
10. external eval
11. spec–trace conformance 분석
```

## 주입할 failure

```text
customers.grade column을 customer_tiers.grade로 이동
```

## 기대 adaptation

```text
1. SQL validation failure 탐지
2. SCHEMA_DRIFT로 분류
3. schema cache refresh
4. 새로운 join path를 이용한 후보 plan 생성
5. failure event에서 fork
6. 후보 실행
7. invariant 및 eval 확인
8. original과 diff
9. 성공 시 현재 요청에만 적용
10. Failure Capsule을 Host에 전달
```

이 하나의 vertical slice만 완성해도 1번, 2번, 3번이 모두 연결됩니다.

---

# 최종 권고

당신의 연구에서 **OKF는 지식 표현 및 복합 질의 대상**, **ActiveGraph는 실행 및 증거 인프라**, **System Model Spec은 설계 의도**, **External Eval Pack은 독립적인 test oracle**, **Conformance Engine은 이들을 연결하는 핵심 연구 기여**가 되어야 합니다.

따라서 최종 구조는 다음과 같습니다.

```text
              Human Architect
                    │
             System Model Spec
                    │
          Cognitive Compile / Build
                    ▼
     ┌────────────────────────────┐
     │ ActiveGraph Knowledge Agent│
     │ DB + OKF + Evidence        │
     └────────────────────────────┘
                    │
                Event Trace
                    │
         Spec–Trace Conformance
             ┌──────┴──────┐
             │             │
        External Eval   Runtime Monitor
             │             │
             └──────┬──────┘
                    │
           Bounded Adaptation
        Fork → Test → Diff → Gate
```

가장 강한 논문 메시지는 다음과 같습니다.

> **LLM Agent의 신뢰성은 최종 응답 정확도만으로 평가할 수 없다. Agent의 설계 명세, 실행 behavior, event trace, 사용된 evidence, 정책 준수 및 runtime adaptation을 하나의 추적 가능한 SDLC로 연결해야 한다.**

첫 번째 작업은 OKF 검색 기능 자체가 아니라, **현재 DB Agent의 System Model–Behavior–Event–Eval 연결표와 trace metadata를 정의하는 것**입니다. 이것이 만들어진 다음 OKF Pack을 추가하면, 이후 모든 기능 확장이 연구 데이터로 축적됩니다.

[1]: https://github.com/yoheinakajima/activegraph "GitHub - yoheinakajima/activegraph: Event-sourced graph runtime for durable and stateful agents · GitHub"
[2]: https://software.imdea.org/~cesar/papers/francalanza18runtime.pdf?utm_source=chatgpt.com "Runtime Verification for Decentralised and Distributed ..."
[3]: https://github.com/yoheinakajima/activegraph/blob/main/docs/guides/operating-in-production.md "activegraph/docs/guides/operating-in-production.md at main · yoheinakajima/activegraph · GitHub"
[4]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md "knowledge-catalog/okf/SPEC.md at main · GoogleCloudPlatform/knowledge-catalog · GitHub"
[5]: https://github.com/yoheinakajima/activegraph-packs "GitHub - yoheinakajima/activegraph-packs: first iteration of a core pack schema for activegraph and a UI to explore capabilities · GitHub"
[6]: https://github.com/yoheinakajima/activegraph-behaviordrafts "GitHub - yoheinakajima/activegraph-behaviordrafts · GitHub"
