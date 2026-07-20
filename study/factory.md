```
https://addyosmani.com/blog/own-the-outer-loop/ 이 블로그에서 inner loop과 outer loop에 대한 설명이 있는데, 
나는 Coding Agent를 이용해, 문서와 DB에 대해 자연서 질의/응답 전용 Agent를 개발 중이야.

전용 Agent는 일반 사용자가 사용하는 multi-user system이고, target machine에서 동작해야 해.
Coding Agent는 개발자의 의도와 System Model Spec을 받아 이를 Target Agent로 Cognitive Compile을 하고, 
TDD 및 eval-run 에 대해 Cognitibe Debugger로 동작하고,
마지막으로는 external evaluator가 만들어진 전용 agent를 full scope로 평가하게 되.
이처럼 Host 개발 상황과 Target 실행환경이 명확히 구분되는 상황 기준으로 블로그 내용을 전문가인 당신이 다시 설명해줘.
```
개발 환경(Host)과 실행 환경(Target)이 물리적·논리적으로 명확히 분리되고, 그 사이를 '인지적 컴파일(Cognitive Compile)'과 '디버거(Cognitive Debugger)'가 연결하는 구조라면 아디 오스마니(Addy Osmani)의 루프 이론은 가장 고도화된 엔지니어링 패러다임인 '소프트웨어 공장(Software Factory)'의 교과서적인 모델로 변모합니다.
이 명확한 가상 머신(Host/Target) 분리 환경을 기준으로, "인간은 Outer Loop를 소유하고, AI 시스템은 Inner Loop를 실행한다"는 철학을 4가지 아키텍처 관점으로 재설명해 드립니다.
------------------------------
## 1. 전체 구조의 재정의: 개발(Host)과 배포(Target)의 경계선
질문자님이 설계하신 아키텍처에서 루프의 수는 본질적으로 Host 환경의 Inner Loop와 Target 환경의 Runtime Loop, 그리고 이 전체를 지배하는 인간의 Outer Loop로 엄격하게 정렬됩니다.

* Inner Loop (Host / 개발 환경): 인간의 의도와 스펙을 받아 Coding Agent가 Target Agent를 빌드(Cognitive Compile), 테스트(TDD), 교정(Cognitive Debugger)하는 빌드 파이프라인 전체가 여기에 속합니다.
* Runtime Loop (Target / 실행 환경): 배포 완료된 Target Agent가 실제 다중 사용자(Multi-user)와 상호작용하며 문서와 DB를 쿼리하는 프로덕션 영역입니다.
* Outer Loop (Human Developer / 통제 영역): Host 환경에 스펙을 입력하고, External Evaluator의 '최종 증거'를 받아 배포(Verdict)를 승인하는 질문자님(개발자)의 영역입니다.

------------------------------
## 2. 가상 컴파일 환경 기준으로 보는 3대 핵심 개념## ① Harness Engineering (하네스 엔지니어링)

"모델은 엔진일 뿐이다. 하네스는 엔진을 감싸서 안전하게 달릴 수 있게 만드는 자동차다."


* Host(개발) 관점의 하네스: Coding Agent가 임의로 코딩하지 못하도록 묶는 "System Model Spec"이 바로 하네스입니다. 스펙이라는 제약 조건을 엄격히 정의해 주어야 Coding Agent가 엇나가지 않고 올바른 가이드라인 안에서 움직입니다.
* Target(배포) 관점의 하네스: Target Agent가 다중 사용자(Multi-user) 환경의 운영 장비(Target Machine)에서 작동하므로, "DB 접근 권한, 세션 격리 샌드박스, 악성 쿼리 필터링 가드레일"이 필수적인 하네스가 됩니다. Coding Agent는 이 Target용 하네스를 함께 컴파일해 내야 합니다.

## ② Loop Engineering (루프 엔지니어링)

"독립적인 체크 기능이 언제 작업이 끝날지 결정하게 하라."


* Cognitive Compile & Debugger의 순환 메커니즘: Host 환경 내부에서 일어나는 완벽한 루프 엔지니어링의 예시입니다.
1. Coding Agent가 스펙을 컴파일하여 Target Agent의 소스/프롬프트를 출력합니다.
   2. 생성된 결과물을 가지고 TDD 및 에발-런(Eval-run)을 돌립니다.
   3. 실패하면 Cognitive Debugger가 개입하여 추론 과정과 에러 로그를 분석(Investigate)하고 수정을 반영(Implement)한 뒤 재테스트(Verify)합니다.
* 이 루프는 인간의 개입 없이 Host 시스템 내부의 독립적인 테스트 통과 기준(Green Signal)에 의해서만 종료 조건이 결정됩니다.

## ③ Agentic Software Factory (에이전틱 소프트웨어 공장)

"공장은 루프가 대규모로 돌아가는 곳이며, 인간은 그 경계선에서 결정을 내린다."


* 질문자님이 설계하신 External Evaluator(외부 평가기)가 바로 이 공장의 핵심 '경계선(Boundary)' 역할을 수행합니다.
* Coding Agent와 디버거가 자기들끼리 "TDD 다 통과했다"고 주장하는 것(Say-so)만으로는 Target Machine에 배포할 수 없습니다.
* Inner Loop를 완전히 벗어난 독립된 객체인 External Evaluator가 Full Scope(보안, 다중 사용자 동시성, DB 부하, 할루시네이션 율 등)로 검증을 때려 얻어낸 객관적인 데이터(Evidence)를 Outer Loop의 인간(질문자님)에게 제출해야 합니다.

------------------------------
## 3. 분리된 환경에서 반드시 방어해야 할 '숨겨진 비용'

* 지독한 인지적 부채 (Cognitive Debt) 방어:
Coding Agent가 시스템 스펙을 받아 Target Agent를 '인지적 컴파일(Cognitive Compile)'하는 과정은 고도의 추상화가 일어나는 구간입니다. AI가 코드를 인간이 이해하기 힘든 구조로 컴파일해 버리면, Target Machine에서 버그가 터졌을 때 인간은 손을 댈 수 없습니다. 따라서 Cognitive Debugger가 동작할 때, 컴파일된 Target Agent의 구조와 쿼리 생성 로직을 인간이 추적할 수 있도록 설명서(Artifact/Documentation)를 함께 빌드하도록 강제(Answerability)해야 합니다.
* 오케스트레이션 택스 (Orchestration Tax) 감소:
개발 환경(Host)에서 Coding Agent ➔ Debugger ➔ Evaluator로 이어지는 파이프라인의 조율 비용이 커지면 개발자가 지칩니다. 각 주체 간의 데이터 포맷을 정형화하여 공장 파이프라인 자체를 매끄럽게(Seamless) 자동화하는 데 초반 에너지를 집중해야 합니다.

------------------------------
## 4. 아디 오스마니 관점에서의 최종 Verdict(결정) 흐름

   1. 인간 (Outer Loop): System Model Spec 및 의도 입력.
   2. Host System (Inner Loop): Cognitive Compile ➔ TDD / Eval-run ➔ Cognitive Debugger 무한 순환 및 자가 교정.
   3. Boundary (경계선): External Evaluator가 완성된 Target Agent를 샌드박스에서 Full Scope 벤치마킹 후 리포트(Evidence) 생성.
   4. 인간 (Outer Loop): 리포트를 보고 "이 Target Agent는 다중 사용자용 Target Machine에 배포해도 안전하다"라는 최종 판결(Verdict)을 내리고 배포 스위치를 누름.

------------------------------
💡 이 완벽한 자동화 공장 파이프라인을 구체화하기 위해 다음 단계를 정교화해 볼 수 있습니다:

* External Evaluator가 Target Agent를 평가할 때, 다중 사용자 환경을 시뮬레이션하기 위해 어떤 핵심 지표(Metric)(예: 데이터 격리성, 응답 지연 시간, DB 커넥션 풀 고갈 여부 등)를 최우선으로 측정하게 설계하실 계획인가요?

```
특히 전용 agent가 서비스하는 동안, 발생하는 변경사항이나 failure에 대한 runtime adaptation, harness adaptation 등 
적응성을 갖도록 하려면, Coding Agent의 기능 일부는 항상 target 전용 agent에도 구현해 두어야 하는 거 아닐까?
```
## 결론

맞습니다. **Target Agent에도 Coding Agent의 일부 기능이 필요합니다.** 다만 Target에 들어가야 하는 것은 소스 코드를 자유롭게 수정하고 배포하는 완전한 Coding Agent가 아니라, 다음과 같은 **제한된 Cognitive Runtime / Adaptive Supervisor**입니다.

> 운영 중의 실패를 관찰하고, 원인을 분류하고, 미리 승인된 대응책 중 하나를 선택하며, 결과를 검증하고, 증거를 Host로 되돌려 보내는 기능

즉,

* **Host Coding Agent**는 시스템을 발전시키는 개발자 역할을 하고,
* **Target Adaptive Supervisor**는 현재 배포된 시스템을 안전하게 유지하는 운영자 역할을 해야 합니다.

중요한 원칙은 다음과 같습니다.

> Target은 스스로 행동을 조정할 수는 있지만, 스스로 요구사항·권한·평가기준·소스 코드를 바꾸고 그 변경을 승인해서는 안 됩니다.

---

# 1. 블로그의 Inner Loop과 Outer Loop

Addy Osmani가 말하는 Agent는 단순한 LLM이 아니라 다음을 포함합니다.

* 모델
* 파일과 메모리
* 도구
* 스킬
* 권한
* 샌드박스
* 테스트
* 관찰성
* 복구 메커니즘

그리고 이 Agent가 수행하는 반복 과정이 다음과 같은 **inner loop**입니다.

```text
Investigate
   ↓
Implement
   ↓
Verify
   ↓
Repeat
```

Agent는 문제를 조사하고, 계획을 실행하고, 결과를 검사한 후 실패하면 다시 반복합니다.

그러나 Agent가 결과를 만들었다고 해서 그것이 자동으로 프로덕션에 들어가서는 안 됩니다. Outer loop에서는 사람이 증거를 보고 다음을 결정합니다.

* 배포할 것인가
* 차단할 것인가
* 범위를 축소할 것인가
* 가드레일을 추가할 것인가
* 다시 실행할 것인가
* 결과를 폐기할 것인가

블로그는 이를 **Quality → Evidence → Verdict → Answerability**의 관계로 설명합니다. Agent는 capability를 행사하지만, 시스템 경계에서 결정을 내리고 결과에 책임지는 agency는 인간에게 있다는 주장입니다. ([Addy Osmani][1])

여기서 중요한 점은 **Host가 Outer이고 Target이 Inner라는 단순한 구분이 아니라는 것**입니다.

Inner/Outer는 물리적 위치가 아니라 **판단 수준에 따라 달라지는 상대적인 개념**입니다.

---

# 2. 당신의 시스템에는 여러 개의 중첩된 Loop가 있다

당신이 구상한 구조에는 최소한 네 개의 loop가 존재합니다.

| 수준        | Inner loop            | Outer loop          | 주요 책임자                              |
| --------- | --------------------- | ------------------- | ----------------------------------- |
| L0 요청 처리  | 질의 이해, 검색, SQL, 답변 생성 | 답변 검증, 재시도, 거부      | Target Agent                        |
| L1 운영 적응  | 실패 대응과 복구 실행          | 적응 정책, 범위, rollback | Target Adaptive Supervisor          |
| L2 시스템 진화 | 코드·Harness·Eval 변경    | 설계 승인과 배포 판정        | Host Coding Agent + Human Architect |
| L3 독립 검증  | 전체 시스템 평가 실행          | 최종 release verdict  | External Evaluator + 인간 책임자         |

따라서 전체 구조는 다음과 같이 보는 것이 적절합니다.

```text
┌─────────────────────────────────────────────────────┐
│ L3: Assurance / Governance Outer Loop               │
│ External Evaluator + Human Owner                    │
│                                                     │
│  - Full-scope evaluation                            │
│  - Security / privacy / quality verdict             │
│  - Promotion or rejection                           │
└───────────────────────────▲─────────────────────────┘
                            │ evidence
┌───────────────────────────┴─────────────────────────┐
│ L2: Host Engineering Loop                           │
│ Human Architect + Coding Agent                      │
│                                                     │
│  System Model Spec                                  │
│        ↓                                            │
│  Cognitive Compile                                  │
│        ↓                                            │
│  TDD / Eval-run / Cognitive Debugging               │
│        ↓                                            │
│  Candidate Target Agent                             │
└───────────────────────────▲─────────────────────────┘
                            │ traces / failure cases
                            │
┌───────────────────────────┴─────────────────────────┐
│ L1: Target Runtime Adaptation Loop                   │
│ Adaptive Supervisor                                 │
│                                                     │
│  Monitor → Analyze → Select Plan → Execute → Verify │
│                                                     │
│  Approved harness variants / fallbacks / rollback   │
└───────────────────────────▲─────────────────────────┘
                            │ supervises
┌───────────────────────────┴─────────────────────────┐
│ L0: Target Request Execution Loop                    │
│                                                     │
│ Question → Plan → Retrieve/SQL → Synthesize          │
│          → Verify → Answer                           │
└─────────────────────────────────────────────────────┘
```

## 핵심 해석

Host에서 Coding Agent가 수행하는 TDD와 eval-run은 **개발 시스템의 inner loop**입니다.

하지만 이 전체 개발 loop를 바깥에서 보면 Human Architect와 External Evaluator가 **engineering outer loop**를 소유합니다.

Target에서는 사용자 질문을 처리하는 과정이 inner loop이고, 이를 감시하면서 재시도·fallback·격리·중단을 결정하는 Adaptive Supervisor가 **runtime outer loop**가 됩니다.

그리고 Runtime Supervisor조차도 조직 전체의 관점에서는 다시 inner loop입니다. 최종 정책과 시스템 변경 권한은 Host 및 인간 책임자에게 남기 때문입니다.

---

# 3. Cognitive Compile의 산출물은 Agent 코드만이어서는 안 된다

System Model Spec을 Cognitive Compile한 결과가 단순한 실행 코드나 프롬프트 묶음이어서는 부족합니다.

다음과 같은 **Operational Contract**까지 함께 생성되어야 합니다.

```text
System Model Spec
    │
    ├── Executable Agent
    ├── Harness Manifest
    ├── Capability Graph
    ├── Runtime Invariants
    ├── Access-control Policies
    ├── Failure Taxonomy
    ├── Recovery Playbooks
    ├── Observability Schema
    ├── Offline / Online Eval Pack
    ├── Adaptation Envelope
    └── Rollback Manifest
```

### 1. Executable Agent

질의 계획, 문서 검색, SQL 생성, 도구 호출, 답변 생성 기능입니다.

### 2. Runtime invariants

운영 중 반드시 지켜야 할 불변조건입니다.

예를 들면 다음과 같습니다.

```text
- 다른 tenant의 데이터는 절대 참조하지 않는다.
- SQL은 기본적으로 read-only이다.
- 답변의 주요 주장은 source evidence와 연결되어야 한다.
- 권한 확인에 실패하면 요청을 거부한다.
- 데이터가 불충분하면 답을 추측하지 않는다.
```

### 3. Failure taxonomy

실패를 구조적으로 분류하기 위한 모델입니다.

```text
INPUT_AMBIGUITY
SCHEMA_DRIFT
RETRIEVAL_MISS
STALE_INDEX
UNSAFE_SQL
TOOL_TIMEOUT
AUTHORIZATION_FAILURE
GROUNDING_FAILURE
LATENCY_BUDGET_EXCEEDED
UNKNOWN_FAILURE
```

### 4. Recovery playbooks

각 실패에 대해 Target이 실행할 수 있는 승인된 복구 절차입니다.

### 5. Adaptation envelope

Target Agent가 스스로 바꿀 수 있는 것과 없는 것을 명시합니다.

이 Adaptation Envelope가 Target의 자율성을 제한하는 일종의 **runtime type system**이 됩니다.

---

# 4. Target에 필요한 것은 “작은 Coding Agent”가 아니라 “Autonomic Kernel”이다

Target Agent에는 Coding Agent의 능력을 그대로 복제하기보다, 다음과 같은 축소된 실행 구조를 두는 것이 좋습니다.

```text
Target Agent
├── Request Executor
├── Runtime Verifier
├── Failure Classifier
├── Adaptive Harness Controller
├── Policy Enforcement Point
├── Experience Recorder
└── Escalation Gateway
```

이 구조는 전통적인 자율 시스템의 MAPE-K 구조와 유사합니다.

```text
Monitor
Analyze
Plan
Execute
    ↕
Knowledge
```

MAPE-K는 시스템이 고수준 정책을 바탕으로 자신의 상태와 환경을 관찰하고, 분석하고, 대응 계획을 세우고, 제한된 조치를 실행하는 self-management 구조입니다. ([IEEE Xplore][2])

당신의 Target Agent에 적용하면 다음과 같습니다.

## Monitor

* 요청 및 응답 trace
* 검색된 문서와 SQL 결과
* tool call 성공·실패
* latency와 token 사용량
* schema version
* index freshness
* grounding score
* tenant와 권한 정보
* 사용자 correction
* fallback 발생 횟수

## Analyze

* 실패 유형 분류
* invariant 위반 확인
* known failure signature 매칭
* schema drift 탐지
* retrieval 품질 저하 판정
* 반복 실패 및 cascading failure 탐지

## Plan

새로운 코드를 생성하는 것이 아니라 **승인된 대응책 중 하나를 고릅니다.**

```text
retry_same
retry_with_backoff
replan_query
switch_retriever
switch_model_route
refresh_schema_cache
use_direct_source
reduce_scope
request_clarification
return_partial_answer
abstain
open_circuit
escalate_to_host
```

## Execute

선택한 계획을 제한된 범위에서 실행합니다.

## Knowledge

* System Model Spec의 runtime projection
* 현재 배포 버전
* 승인된 harness variants
* known failure catalog
* runbook
* tenant policy
* tool capability metadata
* 과거 incident signature

이 Knowledge는 자유롭게 덮어쓰는 메모리가 아니라 **버전 관리되고 감사 가능한 운영 지식**이어야 합니다.

---

# 5. Target Agent가 자동으로 적응해도 되는 네 가지 수준

적응을 한 종류로 취급하면 위험합니다. 적응 수준을 구분해야 합니다.

## Level A — Request adaptation

한 요청 안에서만 유지되는 일시적 적응입니다.

Target이 자동 수행해도 됩니다.

예:

* SQL 오류 후 쿼리 재작성
* 검색어 확장 또는 축소
* 문서 검색과 DB 검색 순서 변경
* timeout 후 재시도
* 답변 범위 축소
* 사용자에게 명확화 요청
* 근거가 부족할 때 답변 거부

이 변화는 다음 요청에 영구적으로 남지 않습니다.

---

## Level B — Harness configuration adaptation

미리 승인된 Harness 구성 사이를 선택합니다.

Target이 수행할 수 있지만, 강한 제한이 필요합니다.

예:

```text
Retriever A → Retriever B
Model Large → Model Small
Vector Search → Hybrid Search
SQL Planner v2 → SQL Planner v1
Prompt Profile A → Prompt Profile B
Primary DB → Read Replica
```

여기서 Target은 새로운 Prompt Profile이나 Retriever를 생성하는 것이 아니라, **Host에서 미리 compile하고 검증한 후보 중 하나를 선택**합니다.

각 adaptation에는 최소한 다음 정보가 있어야 합니다.

```yaml
adaptation:
  id: switch-to-hybrid-retrieval
  trigger: retrieval_grounding_score < 0.65
  allowed_scope: current_tenant
  max_duration: 30m
  validation:
    - no_permission_change
    - grounding_score_improves
    - p95_latency_under_3s
  rollback:
    condition: error_rate_increase > 2%
  evidence:
    required: true
```

이것은 사실상 Harness의 **runtime polymorphism**입니다.

---

## Level C — Artifact adaptation

다음은 Target에서 직접 수행해서는 안 됩니다.

* 소스 코드 수정
* 새 도구 구현
* DB schema 변경
* 새로운 Skill 생성 및 활성화
* 장기 Prompt 수정
* 새로운 retrieval pipeline 구현
* production index 구조 변경
* dependency upgrade

이 작업들은 Target에서 failure evidence를 수집한 뒤 Host의 Cognitive Compiler로 되돌려 보내야 합니다.

```text
Target failure
    ↓
Failure Capsule
    ↓
Host Cognitive Debugger
    ↓
Spec / Code / Harness update
    ↓
TDD + Eval
    ↓
External Evaluation
    ↓
Canary
    ↓
Promotion
```

Canary 배포와 control population 비교는 변경을 전체 트래픽에 노출하기 전에 실제 운영 데이터를 낮은 위험으로 검증하고, 이상이 있으면 rollback하기 위한 대표적인 release back-pressure 방식입니다. ([Google SRE][3])

---

## Level D — Policy and intent adaptation

다음은 인간 또는 명시적인 governance process만 변경해야 합니다.

* 시스템 목적
* 허용되는 데이터 범위
* tenant 간 정보 공유 정책
* 개인정보 처리 정책
* 위험 허용 수준
* tool permission
* write access
* 평가 기준
* 성공의 정의
* 시스템이 답변을 거부해야 하는 조건

Target Agent가 자신의 평가 기준을 수정할 수 있게 하면 다음 문제가 생깁니다.

```text
실패
→ 평가기준 완화
→ 새로운 기준으로 자기 자신을 통과
→ 성공으로 보고
```

이는 adaptation이 아니라 **self-certification**입니다.

Target은 자신의 실행을 검사할 수 있지만, 자신이 통과해야 할 기준을 변경할 수는 없어야 합니다.

---

# 6. 문서·DB 질의 Agent에서 필요한 Runtime Adaptation

## 6.1 DB schema drift

예를 들어 column 이름이 변경되거나 table이 추가된 경우입니다.

Target에서 허용할 수 있는 대응:

```text
1. schema mismatch 탐지
2. schema catalog 재조회
3. 영향을 받는 cached plan 무효화
4. 새 schema로 query replan
5. read-only validator 실행
6. 결과 검증
```

허용하지 않아야 할 대응:

```text
- Target Agent가 임의로 ALTER TABLE 실행
- 권한을 높여 metadata에 접근
- 기존 의미와 다른 column을 임의로 대체
```

Column의 의미가 바뀌었는지 불명확하면 Host로 escalation해야 합니다.

---

## 6.2 문서 변경 또는 index staleness

Target에서 가능한 적응:

* index freshness 확인
* 최신 원문 직접 검색
* lexical/vector/hybrid retrieval 전환
* stale index임을 답변에 명시
* reindex job 요청
* 최신성이 중요한 질문에 답변 거부

Target이 임의로 전체 corpus를 다시 해석하여 영구 지식으로 등록하게 해서는 안 됩니다.

---

## 6.3 SQL generation failure

Target 내부의 작은 Cognitive Debugger가 다음을 수행할 수 있습니다.

```text
Generated SQL
    ↓
Parser validation
    ↓
Schema validation
    ↓
Permission validation
    ↓
Cost / row-limit check
    ↓
Dry run or EXPLAIN
    ↓
Execute
    ↓
Result shape validation
```

실패하면 SQL을 다시 생성할 수 있지만 다음 제약을 지켜야 합니다.

* read-only
* 허용된 table만 접근
* tenant predicate 강제
* row limit 적용
* timeout 적용
* sensitive column masking
* 실행 횟수 제한

---

## 6.4 Retrieval 또는 grounding failure

가능한 Target 적응은 다음과 같습니다.

```text
vector search
   ↓ low confidence
hybrid search
   ↓
query decomposition
   ↓
cross-source verification
   ↓
clarification or abstention
```

중요한 것은 “어떻게든 답을 생성하는 것”이 아니라, 적응 후에도 근거가 부족하면 **안전하게 답하지 않는 것**입니다.

---

## 6.5 Authorization failure

Authorization은 적응 대상이 아닙니다.

```text
권한 부족
→ 다른 credential 탐색
→ 더 넓은 권한 요청
```

과 같은 행동은 금지해야 합니다.

정상적인 동작은 다음뿐입니다.

```text
권한 부족
→ fail closed
→ 감사 로그 기록
→ 사용자에게 제한 설명
→ 필요한 경우 관리자 escalation
```

Runtime policy engine을 Agent 밖의 enforcement layer로 두어 tool action을 실제 실행 전에 검사하는 방식은 Agent의 powers를 제한하고 행동을 관찰 가능하게 만드는 방어선으로 사용될 수 있습니다. ([Google Cloud][4])

---

# 7. Runtime Adaptation과 Harness Adaptation의 차이

두 개념은 분리하는 것이 좋습니다.

## Runtime adaptation

현재 실행을 복구하거나 품질을 유지합니다.

```text
retry
replan
fallback
route
clarify
abstain
rollback
circuit-break
```

## Harness adaptation

Agent가 생각하고 행동하는 실행 환경을 변경합니다.

```text
prompt profile
tool selection
memory policy
retrieval strategy
model route
step budget
verification depth
permission envelope
```

Harness는 모델을 둘러싸는 실행 구조입니다. 최근 Agent 시스템에서도 session log, harness loop, sandbox 등을 별도 구성 요소로 분리하는 접근이 사용됩니다. ([Anthropic][5])

Harness adaptation은 Runtime adaptation보다 위험합니다. 따라서 다음 원칙이 필요합니다.

> Target은 Harness를 생성하지 않고, Host가 승인한 Harness Variant를 선택한다.

예:

```text
Harness Registry
├── H1: Fast / low-cost
├── H2: High-accuracy
├── H3: Schema-drift recovery
├── H4: Retrieval-degraded mode
└── H5: Safe minimal mode
```

Target Adaptive Supervisor는 현재 상태에 따라 H1에서 H3로 전환할 수 있지만, H6를 새로 작성해서 활성화할 수는 없습니다.

---

# 8. External Evaluator와 Embedded Evaluator를 분리해야 한다

Target에도 evaluator가 필요하지만, 그것이 External Evaluator를 대체하지는 않습니다.

## Embedded runtime evaluator

Target 내부에서 빠르게 검사합니다.

* SQL 유효성
* source 존재 여부
* 답변 인용 일치
* latency budget
* permission invariant
* 응답 형식
* known failure signature

목적은 **현재 요청을 안전하게 처리하는 것**입니다.

## External evaluator

Target 밖에서 전체 시스템을 평가합니다.

* end-to-end task success
* 복수 tenant 격리
* adversarial query
* 권한 우회
* schema drift
* 문서 변경
* 장시간 운영
* concurrent user load
* recovery correctness
* hallucination
* cost와 latency
* regression
* adaptation이 새로운 실패를 만들지 않았는가

Agent eval은 최종 출력뿐 아니라 tool call과 중간 trace를 함께 평가해야 Agent workflow의 실패 원인을 분석할 수 있습니다. 공식 Agent eval 가이드도 trace, grader, dataset 및 eval run을 이용해 workflow 수준을 평가하는 구조를 제시합니다. ([OpenAI Developers][6])

세 평가 계층을 분리하는 것이 좋습니다.

```text
Self-check
    advisory

Runtime verifier
    enforcement

External evaluator
    release verdict
```

Target Agent는 “내 답은 맞다”고 주장할 수 있지만, 그것은 evidence 중 하나일 뿐 최종 verdict가 되어서는 안 됩니다.

---

# 9. Target에서 Host로 보내야 할 것은 로그가 아니라 Failure Capsule이다

단순 trace를 모두 Host에 전달하면 Coding Agent가 원인을 찾기 어렵습니다.

Target은 실패를 다음과 같은 구조로 정리해야 합니다.

```yaml
failure_capsule:
  incident_id: inc-2026-0718-0042
  agent_version: 1.4.2
  harness_version: h3.7
  tenant_scope: anonymized-tenant-17

  user_intent:
    class: aggregate-query
    normalized_query: "VIP 고객 수와 목록 조회"

  observed_failure:
    type: SCHEMA_DRIFT
    symptom: "column customers.grade not found"

  execution:
    plan_id: plan-8841
    tools:
      - schema_catalog
      - sql_generator
      - sql_validator
    failed_step: sql_validation

  adaptations_attempted:
    - refresh_schema_cache
    - replan_sql

  result:
    status: escalated
    user_response: safe_partial_response

  evidence:
    schema_before: customers-v14
    schema_after: customers-v15
    trace_ref: trace-33842

  suspected_spec_gap:
    - customer grade moved to customer_tiers table

  candidate_eval:
    input: "VIP 고객은 몇 명이고 누구인가?"
    expected_properties:
      - joins customer_tiers
      - tenant filtering
      - read_only
```

이 Failure Capsule은 Host의 Cognitive Debugger에 다음 세 가지로 사용됩니다.

1. 재현 가능한 test fixture
2. regression eval case
3. System Model Spec의 부족한 부분을 찾는 증거

여기서 중요한 원칙은 다음과 같습니다.

> Production experience는 곧바로 새 코드나 새 정책이 되는 것이 아니라, 먼저 새로운 evidence와 eval case가 되어야 합니다.

---

# 10. 권장하는 최종 역할 분담

## Human Architect

* 목적과 시스템 경계 정의
* System Model Spec 작성
* invariants와 risk budget 결정
* Adaptation Envelope 승인
* 최종 변경 책임

## Host Coding Agent

* Spec을 Target artifact로 Cognitive Compile
* 코드·프롬프트·Skill·Harness 생성
* TDD 실행
* eval-run
* failure trace 분석
* 수정 후보 생성
* regression suite 확장

## Target Request Agent

* 사용자 질문 수행
* 문서 및 DB 접근
* 답변 생성
* request-level verification

## Target Adaptive Supervisor

* runtime monitoring
* failure classification
* 승인된 playbook 실행
* 승인된 Harness Variant 선택
* rollback과 circuit breaker
* Failure Capsule 생성
* Host escalation

## External Evaluator

* 독립적인 full-scope 평가
* adversarial 및 regression 평가
* adaptation 동작 평가
* release 후보 비교
* evidence 생성

## Human Owner

* evidence 검토
* 최종 verdict
* 배포·차단·축소·rollback 결정
* 결과에 대한 answerability

---

# 11. 가장 중요한 설계 원칙

당신의 시스템에서는 다음 문장으로 Outer Loop 개념을 다시 정의할 수 있습니다.

> **Coding Agent는 Host에서 Target Agent를 Cognitive Compile하고 Cognitive Debugging하지만, 배포된 Target Agent는 자신의 운영 상태를 감시하고 제한된 범위에서 적응할 수 있는 Cognitive Runtime을 포함해야 한다. 다만 Target의 적응은 사전 승인되고 검증 가능하며 되돌릴 수 있는 실행 대안에 한정되고, 시스템 목적·권한·평가기준·지속적인 코드와 Harness의 변경은 Host Engineering Outer Loop와 External Evaluator의 통제를 받아야 한다.**

더 간단히 표현하면 다음과 같습니다.

```text
Target may adapt execution.
Target may select an approved harness.
Target may produce evidence for evolution.

Target may not redefine intent.
Target may not expand authority.
Target may not approve its own evolution.
```

따라서 질문에 대한 가장 정확한 답은 다음과 같습니다.

> **Coding Agent의 기능 일부는 Target에 남겨야 한다. 그러나 그것은 self-modifying Coding Agent가 아니라, System Model Spec으로부터 compile된 invariants, failure taxonomy, recovery playbooks, runtime verifiers와 approved harness variants를 실행하는 bounded adaptive runtime이어야 한다.**

이 구조에서는 Target Agent가 단순한 컴파일 결과물이 아니라, **제한된 runtime cognition을 갖춘 실행 가능한 System Model**이 됩니다. Host는 새로운 능력을 만들고, Target은 기존 능력을 상황에 맞게 조정하며, External Evaluator와 인간은 두 시스템 모두의 Outer Loop를 소유합니다.

[1]: https://addyosmani.com/blog/own-the-outer-loop/ "AddyOsmani.com - Own the Outer Loop"
[2]: https://ieeexplore.ieee.org/document/1160055?utm_source=chatgpt.com "The vision of autonomic computing"
[3]: https://sre.google/workbook/canarying-releases/?utm_source=chatgpt.com "Google SRE - Canary Release: Deployment Safety and Efficiency"
[4]: https://cloud.google.com/blog/products/identity-security/cloud-ciso-perspectives-how-google-secures-ai-agents?e=48754805&hl=en&utm_source=chatgpt.com "Cloud CISO Perspectives: How Google secures AI Agents | Google Cloud Blog"
[5]: https://www.anthropic.com/engineering/managed-agents?lid=8orHBY9s2fwFg2gZ&utm_source=chatgpt.com "Scaling Managed Agents: Decoupling the brain from the hands \ Anthropic"
[6]: https://developers.openai.com/api/docs/guides/agent-evals?utm_source=chatgpt.com "Evaluate agent workflows | OpenAI API"


