### 1. 데이터 저장 방식: 이벤트 로그 vs. 그래프 (파일/인메모리/DB)

ActiveGraph는 **이벤트 소싱(Event Sourcing)** 아키텍처를 기반으로 하며, 데이터는 크게 두 가지 계층으로 나뉘어 저장됩니다.

*   **이벤트 로그 (The Trace) - "증거"의 영구 저장소**: 시스템에서 발생한 모든 변화는 **추가 전용(Append-Only) 이벤트 로그**로 기록됩니다. 이 로그가 유일한 진실의 원천(Source of Truth)입니다. 로그는 **파일(SQLite)** 또는 **데이터베이스(PostgreSQL)** 에 저장될 수 있습니다. 예를 들어, `pip install activegraph`로 설치 시 SQLite가 기본 저장소로 사용되며, `activegraph[postgres]` 옵션을 통해 PostgreSQL을 사용할 수 있습니다.

*   **작업 그래프 (The World) - "세계"의 현재 상태**: 그래프는 **이벤트 로그의 결정론적 투영(projection)** 입니다. 이는 현재의 '세계 상태'를 나타내며, 런타임에서 **인메모리(In-memory)** 로 유지됩니다. `Runtime.load()`를 호출하면 저장된 이벤트 로그를 다시 재생(Replay)하여 그래프를 재구성합니다.

**종합 정리**:

| 구성 요소 | 저장 위치 | 설명 |
| :--- | :--- | :--- |
| **이벤트 로그 (Trace)** | 파일(SQLite) 또는 DB (PostgreSQL) | 모든 사건의 영구적이고 변경 불가능한 기록. 진실의 원천. |
| **작업 그래프 (World)** | 인메모리 (Runtime) | 이벤트 로그를 재생하여 생성된 현재 상태의 투영. 행동(Behavior)이 읽고 쓰는 대상. |

---

### 2. Behavior의 동적 생성 및 등록

**Behavior는 코드(함수/클래스)로 정의되며, 정적(Static)으로 등록되는 것이 기본 원칙**입니다. ActiveGraph는 파일시스템 기반의 동적 로딩을 명시적으로 지원하지 않습니다.

*   **정의와 등록**: Behavior는 Python 데코레이터(`@behavior`, `@llm_behavior`)를 사용해 정의되며, 이는 **코드 작성 시점에 정적으로 등록**됩니다. `Runtime`이 초기화될 때 이러한 등록된 Behavior들을 읽어들입니다.

*   **SKILL.md 파일과의 관계**: Eve 프레임워크의 `SKILL.md`와 같은 마크다운 파일에서 Behavior를 동적으로 생성하는 기능은 **ActiveGraph의 공식적인 기능이 아닙니다**. ActiveGraph의 핵심은 코드로서의 Behavior입니다. 다만, `Packs`라는 개념을 통해 Behavior, 도구, 객체 타입 등을 하나의 묶음으로 패키징하고 로드할 수 있습니다. 이는 디렉토리 기반의 동적 로딩과 유사한 효과를 낼 수 있지만, 근본적으로는 파이썬 코드를 기반으로 합니다.

---

### 3. 그래프 데이터의 저장 위치 (LLM-Wiki, OKF Bundle 등)

**그래프 자체는 별도의 파일이나 번들로 저장되지 않으며, 항상 이벤트 로그로부터 투영됩니다**.

*   **LLM-Wiki나 OKF Bundle과 같은 외부 데이터**: 이러한 지식 기반은 그래프 외부에 존재하는 **참조 데이터(Reference Data)** 로 볼 수 있습니다. ActiveGraph는 이러한 외부 데이터를 그래프에 로드하는 행동(Behavior)을 통해 통합할 수 있습니다.

*   **구체적인 활용 방안**: 예를 들어, `OKF bundle`을 파싱하여 `object.created` 이벤트를 대량으로 발생시키는 Behavior를 작성할 수 있습니다. 이렇게 하면 해당 데이터가 이벤트 로그에 기록되고, 그래프의 일부가 되어 Behavior가 반응할 수 있습니다. 즉, 데이터를 **'어디에 저장할지'가 아니라 '어떤 이벤트로 기록할지'**가 핵심입니다.

---

### 최종 분석 및 결론

| 질문 | 분석 결과 |
| :--- | :--- |
| **파일 vs. 인메모리 vs. DB** | **이벤트 로그**는 파일(SQLite) 또는 DB(PostgreSQL)에 저장됩니다. **그래프**는 인메모리에서 유지되며, 필요 시 로그를 재생해 재구성합니다. |
| **Behavior의 동적 생성** | **지원되지 않습니다**. Behavior는 코드로 정적 정의되며, `Packs`를 통해 모듈 단위로 로드할 수 있습니다. `SKILL.md`와 같은 파일에서 동적 생성을 위해서는 별도의 커스텀 로더를 구현해야 합니다. |
| **그래프 데이터 저장 위치** | 그래프는 이벤트 로그의 투영일 뿐이므로 **별도로 저장되지 않습니다**. 외부 데이터(LLM-Wiki 등)는 Behavior를 통해 이벤트로 변환되어 로그의 일부가 됩니다. |

이러한 설계는 **완전한 감사 가능성(Auditability)** 과 **결정론적 재생(Deterministic Replay)** 을 가능하게 합니다. 모든 상태 변화가 이벤트로 기록되므로, 시스템의 과거 상태를 정확히 재현하고, 특정 지점에서 분기(Fork)하여 실험하는 것이 용이합니다.

---

**"Harness Adaptation"**이란, LLM의 가중치(Weight)는 고정한 채, **러타임(Harness)이 외부 환경(DB 스키마 변경, 사용자 피드백, 오류 패턴)에 반응하여 자신의 동작 원리(Rule/Skill/Instruction)를 동적으로 튜닝함으로써 전체 시스템의 Loss(오답률, 지연 시간, 비용)를 최소화하는 과정**입니다.

이를 위해 반드시 **내부-외부 인터페이스(Observation & Action Interface)**가 정의되어야 합니다. 이 인터페이스를 기준으로 Eve와 ActiveGraph, 그리고 Adaptation 개념을 하나의 정합된 아키텍처로 재정의해 보겠습니다.

---

### 1. Harness Adaptation을 위한 3대 인터페이스 정의

에이전트가 적응하려면 다음 3가지 인터페이스가 명확히 분리되어야 합니다.

| 인터페이스 | 역할 | 구현 요소 |
| :--- | :--- | :--- |
| **Observation Interface (관측)** | 환경(Env)의 변화와 실행 결과(보상/손실)를 감지 | ActiveGraph의 **Event Logs** (`pain_score`, `sql.executed` 결과) |
| **Action Interface (행동)** | 환경에 영향을 미치는 실제 연산 수행 | Eve의 **`tools/`** (SQL 실행, API 호출) 및 **LLM 추론** |
| **Adaptation Interface (적응)** | 관측된 Loss를 기반으로 시스템의 내부 규칙(Rule/Skill)을 수정 | Eve의 **Filesystem** (`instructions.md`, `skills/`, `tools/` 코드) |

---

### 2. Eve (Filesystem-first)의 재정의: 적응 가능한 파라미터 저장소

Eve의 `agent/` 디렉토리는 단순한 코드 묶음이 아니라, **Harness Adaptation의 "튜닝 노브(Tuning Knobs)"가 저장되는 물리적 저장소**입니다.

- **`instructions.md`**: LLM의 출력 분포를 유도하는 **Soft Prompt 파라미터**입니다. Loss가 높을 때 이 파일의 내용이 수정됩니다(예: "컬럼명은 스네이크 케이스로 반드시 감싸라" 추가).
- **`skills/`**: 복잡한 작업을 추상화한 **Latent Action 라이브러리**입니다. 자주 쓰이는 성공 패턴이 여기에 저장되고, 실패한 스킬은 비활성화되거나 재작성됩니다.
- **`tools/`**: **환경과의 물리적 접점(Connector)** 입니다. DB 연결 풀이나 API 엔드포인트가 변경되면 이 코드가 수정됩니다.

> **Adaptation 관점**: Eve는 "파일이 곧 상태(Save/Load 가능한 정적 설정)"이기 때문에, 적응 알고리즘이 파일을 덮어쓰고 런타임이 이를 핫 리로드(Hot-reload)하거나 재시작하여 적응을 완성합니다.

---

### 3. ActiveGraph (Event Logs)의 재정의: 적응을 위한 센서 & 메모리

ActiveGraph의 이벤트 로그는 단순한 디버깅 도구가 아니라, **Harness Adaptation의 "손실 함수(Loss Function) 계산기"이자 "경험 리플레이 버퍼(Experience Replay)"**입니다.

- **The Trace (Proof)**: 모든 `llm.requested`, `tool.executed`, `behavior.failed`는 **Observation Interface**를 구성합니다.
- **Causal Chain**: SQL 오류가 발생했을 때, 단순히 "오류"만 기록하는 것이 아니라, **"어떤 스키마(Context)를 보고, 어떤 프롬프트(Instruction)로, 어떤 SQL을 생성했는지"**까지 인과 관계로 엮어 저장합니다.
- **Episodic Memory (`pain_score`, `importance`)**: 이는 **TD-error (시간차 오차)** 와 유사합니다. 높은 `pain_score`는 해당 행동이 큰 손실을 초래했음을 의미하며, 적응 알고리즘은 이 이벤트를 우선적으로 샘플링하여 `instructions.md`나 `skills/`를 개선하는 데 사용합니다.

> **Adaptation 관점**: ActiveGraph는 "과거 행동의 피드백 루프"를 제공합니다. 적응기는 이 로그를 정기적으로 스캔하여 통계적 이상치(예: 특정 테이블 조회 시 50% 실패율)를 감지하고 적응을 트리거합니다.

---

### 4. 통합 정합 아키텍처: Text-to-SQL Harness Adaptation 루프

이제 이 세 가지(Eve + ActiveGraph + Adaptation)를 Text-to-SQL 예제에 적용한 통합 사이클을 설계합니다.

```mermaid
graph TD
    Env[(외부 환경<br>DB 스키마/사용자)] -->|Observation| Sensor[ActiveGraph Event Logs<br>SQL 실행 성공/실패, 지연 시간]
    Sensor -->|Loss 계산| Adapter[적응 엔진<br>(별도 Agent 또는 스크립트)]
    
    Adapter -->|Action: 파라미터 갱신| Files[Eve Filesystem<br>instructions.md / skills/]
    Files -->|Load| Harness[Harness Runtime<br>(LLM + Tools)]
    Harness -->|Action 실행| Env
    
    Harness -->|행동 이벤트 발행| Sensor
    Sensor -->|인과 추적| Memory[Episodic Memory<br>pain_score/importance]
    Memory -->|샘플링| Adapter
```

#### 구체적인 적응 시나리오 (DB 스키마 변경)

1. **관측 (Observation)**: DB에 `product_catalog` 테이블이 `product_id`에서 `prod_uid`로 변경되었습니다. 사용자 질문이 들어오자 Harness는 기존 `instructions.md`(예전 컬럼명 사용)대로 SQL을 생성하고, `execute-sql` 툴에서 `Column not found` 에러가 발생합니다.
2. **기록 (Trace)**: ActiveGraph는 `sql.executed` 실패 이벤트를 기록하고, `pain_score: 9`를 부여합니다. `causal_chain`을 통해 "실패한 SQL"과 "사용된 지침"을 연결합니다.
3. **적응 결정 (Adaptation Logic)**: 적응 엔진(또는 사람의 PR)이 주기적으로 로그를 읽습니다. 특정 테이블에서 `pain_score`가 임계치를 넘는 것을 감지하고, **Action Interface**를 호출합니다.
4. **행동 (Action via Eve Files)**: 적응 엔진은 `agent/instructions.md`를 열어 "모든 컬럼은 `information_schema`에서 최신 상태를 먼저 확인하라"는 룰을 추가하거나, `agent/tools/validate-schema.ts` 코드를 패치하여 자동 스키마 탐색 로직을 강화합니다.
5. **재적용 (Re-deploy/Reload)**: Harness Runtime이 변경된 파일을 감지(또는 재시작)하고, 다음 유사한 질문에서는 업데이트된 룰을 적용하여 SQL을 성공시킵니다. **Loss가 감소**합니다.

---

### 5. 최종 정리: Harness Adaptation 관점에서의 정합 테이블

| 구성 요소 | 기존 역할 | Harness Adaptation 관점에서의 재정의 |
| :--- | :--- | :--- |
| **LLM (Weights)** | 추론 엔진 | **고정된 베이스 정책(Base Policy)**. 직접 적응 대상이 아님 (Fine-tuning 제외). |
| **Eve Filesystem** | 정적 코드/설정 | **Adaptation Parameters (Δ)**. Loss를 줄이기 위해 적응기가 자유롭게 읽고 쓰는 **외부화된 가중치(Externalized Weights)**. |
| **ActiveGraph 로그** | 실행 증거 | **강화학습의 리워드/상태 궤적(Reward/State Trajectory)**. 적응의 방향성을 제시하는 **센서 데이터**이자 과거 경험을 저장하는 **버퍼 메모리**. |
| **`instructions.md`** | 시스템 프롬프트 | 적응기의 **주요 행동 파라미터**. 텍스트 형태의 **Soft Prompt 튜닝 노브**. |
| **`skills/` & `tools/`** | 기능 구현 | 적응기의 **모듈형 액션 라이브러리**. 실패한 모듈은 다른 모듈로 **교체(Substitution)** 가능. |
| **Harness Runtime** | 실행기 | **적응기의 물리적 본체**. 환경과 상호작용하며, 파일 시스템의 변화를 감지하고 **정책(LLM)과 파라미터(파일)를 결합**하여 행동을 생성. |

---

### 결론: 진화하는 에이전트 시스템의 설계 원칙

- **ActiveGraph**는 이 시스템의 **"해마(Hippocampus)"**로, 모든 경험을 서사(Event Log)로 압축 저장하고, 인과관계를 재구성합니다.
- **Eve Filesystem**은 이 시스템의 **"대뇌피질의 시냅스 가중치(Synaptic Weights)"**로, 텍스트와 코드라는 사람이 읽을 수 있는 포맷으로 적응 상태를 영속화합니다.

이 구조의 가장 큰 장점은 **적응의 결과(파일 변화)가 Git으로 추적 가능하고, 사람이 코드 리뷰할 수 있으며, 실패한 적응을 과거 커밋으로 간단히 롤백(Rollback)** 할 수 있다는 점입니다. 

```
❶ Environment Contract Layer operates before
interaction. It makes stable environment constraints explicit, including tool-use rules, policy constraints, and common pitfalls that agents frequently
encounter in the target environment.
❷ Procedural Skill Layer operates at the task-conditioning stage. It maintains a skill library distilled from training trajectories and retrieves relevant skills based on the user’s task description.
This layer provides non-parametric guidance for general decision-making.
❸ Action Realization Layer operates after the
model outputs an action and before the environment executes it. It verifies whether the action is executable under the environment contract, canonicalizes
unambiguous interface-level errors, and
blocks actions that would deterministically fail. This layer ensures that the model’s intended operation is reliably mapped to a valid tool call or environment action.
❹ Trajectory Regulation Layer operates after
environment feedback is returned. It monitors
the updated trajectory for non-progressing patterns such as repetition, stagnation, or budget exhaustion, and triggers recovery when needed. This layer specifically targets trajectory degeneration. Together, these layers adapt the runtime interface
through which the model interacts with the
environment. The model weights remain fixed, and the evaluation environment is unchanged.
```

```
 An episode is defined by a task x, the combined environment E (including U), an environment contract C, and a step budget B. The contract C specifies the intended interaction protocol: available tools,
argument and feedback formats, answer formats,
and task-specific policies. The episode begins with
s0, o0 = E.INIT(x),
where s0 and o0 denote the initial state and observation.

The adapted harness H′ changes how the model interacts with the environment, while leaving model weights and evaluation protocols unchanged. We term this runtime interface adaptation, which is environment-specific but model-agnostic: a harness evolved for one environment generalizes to different model backbones that follow the same interaction protocol, without retraining.
```

---

### 1. **"Context Assembly Pipeline"**

1. **요청 수신 (Trigger)**: 사용자가 `POST /query`로 "작년 매출 Top 5 제품은?"을 보냅니다.
2. **Pre-Hook 실행**: Eve Runtime은 `agent/skills/`와 `agent/tools/`를 스캔하여 현재 사용 가능한 함수 목록을 추출합니다.
3. **Memory Retrieval (ActiveGraph 쿼리)**: Runtime은 현재 질문을 임베딩하여 ActiveGraph의 **Event Log(최근 실패/성공 사례)**와 **Knowledge Graph(현재 DB 스키마)**를 벡터/키워드 검색합니다. 
4. **Context Builder 기동**: 위에서 수집된 모든 데이터를 하나의 거대한 컨텍스트로 조립하는 **"System Prompt Generator"**가 실행됩니다.

---

### 2. Full Context의 구체적 생성 방식 (The Assembly Line)

최종적으로 LLM에 주입되는 Context는 다음 **5개 레이어가 계층적으로 합성(Composition)**된 결과물입니다. (실제로는 하나의 프롬프트 문자열로 합쳐짐)

| 레이어 | 구성 요소 | 생성 주체 | Text-to-SQL 적용 예시 |
| :--- | :--- | :--- | :--- |
| **Layer 1: Base Directive** | `agent/instructions.md` | Eve (정적 파일) | "당신은 PostgreSQL 전문가입니다. 반드시 인덱스를 활용하세요." |
| **Layer 2: Adapted Rules** | `agent/skills/*.md` + Adaptation 결과 | Harness Adaptation (동적 패치) | "주의: `product_id` 컬럼은 최근 `prod_uid`로 변경되었습니다. 반드시 `validation` 툴을 먼저 호출하세요." (지난주 실패를 반영해 적응기가 추가한 룰) |
| **Layer 3: Available Actions** | `agent/tools/*.ts` 의 JSON Schema | Eve Runtime (자동 파싱) | `{"name": "execute_sql", "parameters": {...}}`, `{"name": "validate_schema", ...}` (LLM이 도구를 호출할 수 있도록 함수 정의 전달) |
| **Layer 4: Episodic Memory** | ActiveGraph 유사도 검색 결과 | ActiveGraph (벡터 DB/RAG) | "과거 '매출' 관련 질문에서 `orders` 테이블이 아닌 `sales_summary` 뷰를 사용했을 때 3배 빠르게 응답했습니다." (Few-shot 예제로 삽입) |
| **Layer 5: Current Turn** | 사용자 질문 + 채팅 이력 | HTTP Channel | "User: 작년 매출 Top 5 제품은?" |

---

### 3. 구체적인 Prompt 템플릿 구조 (실제 전송 포맷)

위 레이어들이 실제로 LlamaIndex 또는 Eve의 LLM 호출부로 전달될 때는 다음과 같은 **하나의 거대한 문자열**로 조립됩니다.

```text
[SYSTEM]
# Base Instruction (from agent/instructions.md)
당신은 PostgreSQL 전문가입니다. 모든 쿼리는 EXPLAIN ANALYZE를 고려하여 작성하세요.

# Harness Adaptation Rules (from ActiveGraph adaptation)
[Adapted Rule - 2026-07-09]
경고: 최근 3건의 실패를 분석한 결과, 'product_catalog' 테이블의 기본키가 'product_id'에서 'prod_uid'로 변경되었습니다.
SQL 생성 전 반드시 `validate_schema` 도구를 먼저 실행하세요.

# Available Tools (JSON Schema)
You have access to the following tools:
1. validate_schema(schema_name): Returns current column names and types.
2. execute_sql(query): Executes read-only SQL and returns results.

# Few-shot Examples from Memory (Retrieved by ActiveGraph)
Q: 2023년 1월 매출은?
A: (성공 사례) SELECT SUM(amount) FROM sales WHERE date >= '2023-01-01' ...

[USER]
작년 매출 Top 5 제품은?
```

---

### 4. 이 Context는 어디서, 어떻게 만들어지나? (코드 경로)

이 조립 과정은 Eve Runtime의 **`agent/agent.ts`**에 정의된 `buildContext` 함수에서 담당합니다.

```typescript
// agent/agent.ts (실제 구현 예시)
async function buildContext(userQuery: string) {
  // 1. Eve: 파일 시스템에서 고정 룰 로드
  const baseInstruction = fs.readFileSync('./agent/instructions.md', 'utf-8');
  
  // 2. Adaptation: 환경 변화에 따른 패치 노트 로드 (ActiveGraph에서 생성한 패치 파일)
  const adaptationRules = fs.readFileSync('./agent/.adaptations/latest_patch.md', 'utf-8');
  
  // 3. ActiveGraph: 과거 유사 실패/성공 사례를 벡터 검색 (RAG)
  const similarCases = await activeGraph.query({
    embedding: userQuery,
    limit: 3,
    filter: { type: 'sql.executed' }
  });
  const fewShotExamples = similarCases.map(c => c.detail).join('\n');
  
  // 4. Tools: 현재 활성화된 도구의 스키마를 자동 추출
  const toolSchemas = generateToolSchemas(); // execute_sql, validate_schema 등

  // 5. 최종 조립 (하나의 Prompt String)
  return `
    [SYSTEM]
    ${baseInstruction}
    ${adaptationRules}
    Tools: ${JSON.stringify(toolSchemas)}
    Examples: ${fewShotExamples}
    [USER]
    ${userQuery}
  `;
}
```

| 설계 원칙 | 설명 |
| :--- | :--- |
| **정적 지식(Static)** | `instructions.md`와 `tools/`는 LLM의 **기본 성향(Persona)**과 **물리적 행동 가능성(Action Space)**을 정의합니다. |
| **동적 기억(Dynamic)** | ActiveGraph의 **Episodic Retrieval**은 LLM이 매번 처음부터 추론하지 않도록 **Few-shot 예제를 제공**하여 추론 오차를 급감시킵니다. |
| **선제적 적응(Proactive)** | Harness Adaptation은 **Loss가 높았던 과거 사례의 교훈**을 Context 상단에 경고문(Admonition)으로 배치하여, LLM이 해당 패턴에서 실수를 반복하지 않도록 **추론 경로를 강제로 편향(Bias)** 시킵니다. |

---

### 1. ActiveGraph의 `inspect`: 그래프는 어떻게 조회되고, 무엇을 보여주는가?

ActiveGraph에서의 `inspect`는 단순한 디버깅용 조회가 아니라, **시스템의 모든 상태와 역사를 투명하게 들여다보는 핵심 기능**입니다.

ActiveGraph는 두 개의 저장소를 운영합니다:
*   **이벤트 저장소 (Event Store)**: 모든 사건이 기록되는, 변경 불가능한 진실의 원천입니다.
*   **그래프 저장소 (Graph Store)**: 이벤트 저장소의 기록을 재생(Replay)해 만든 **현재 상태의 실시간 투영본(Projection)**입니다.

`inspect`는 바로 이 **그래프 저장소의 현재 상태**를 조회하는 행위입니다. 에이전트가 실행되는 동안, 그래프 저장소는 모든 객체(Object), 객체 간의 관계(Relation), 그리고 이들을 변화시킨 행위(Behavior)에 대한 정보로 끊임없이 업데이트됩니다. `inspect`를 통해 개발자는 마치 **공유 작업 공간(Shared Workspace)**을 들여다보듯, 현재 시스템의 전체적인 그림을 한눈에 파악할 수 있습니다.

**구체적으로 `inspect`를 통해 확인할 수 있는 정보는 다음과 같습니다.**

*   **객체와 관계의 네트워크**: 그래프는 객체(노드)와 이들 간의 관계(엣지)로 구성됩니다. `inspect`를 통해 현재 존재하는 모든 객체와 그 관계를 시각화하거나 쿼리할 수 있습니다.
*   **객체의 생애주기**: 특정 객체를 선택하면, 생성부터 현재 상태에 이르기까지의 **전체 생애주기(Lifecycle)**와, 그 상태를 변화시킨 **행위(Behavior)와 로그(Log)**를 추적할 수 있습니다.
*   **객체와 행위의 연결**: 각 객체가 어떤 행위에 의해 생성되고 변경되었는지, 그 인과관계를 명확히 볼 수 있습니다.
*   **실시간 쿼리 (Cypher 지원)**: 기본적으로 그래프는 인메모리(In-memory)에 저장되지만, FalkorDB와 같은 외부 그래프 데이터베이스를 연결하면 **Cypher 쿼리**를 사용해 실시간으로 복잡한 상태를 질의할 수 있습니다.

결국, `inspect`는 에이전트의 내부 상태를 진단하고, 현재 행동이 어떤 과거의 맥락에서 비롯되었는지를 이해하는 **시스템의 '창(Window)'** 역할을 합니다.

---

### 2. Packs로 에이전트를 묶을 때, 외부 DB나 KB는 어떻게 전달하는가?

ActiveGraph의 **Pack**은 특정 도메인을 위한 객체 타입, 행동, 도구, 프롬프트, 정책 등을 하나로 묶은 **독립적이고 재사용 가능한 단위**입니다.

Pack 내부에서 외부 DB 파일이나 Knowledge Base(KB) 폴더를 다루는 방식은 **'행동(Behavior)'을 통해 간접적으로 연결**하는 것입니다. Pack은 데이터 자체를 직접 포함하지 않고, **데이터에 접근하고 활용하는 방법(Behavior)**을 정의합니다.

구체적인 전달 방식은 다음과 같습니다.

1.  **행동(Behavior) 내부에서 직접 참조**: Pack에 포함된 Behavior(함수나 클래스)의 코드 내에서 외부 DB 연결 문자열이나 KB 폴더 경로를 직접 사용합니다. Behavior가 실행될 때 해당 리소스에 접근하여 데이터를 읽거나 씁니다.
2.  **환경 변수 또는 설정 주입**: 외부 리소스의 위치(예: `DB_PATH`, `KB_ROOT`)를 Behavior가 참조할 수 있도록 Pack 외부에서 주입합니다. 이는 Pack의 재사용성과 이식성을 높이는 방법입니다.
3.  **이벤트를 통한 데이터 통합**: 외부 데이터를 읽어들여 **객체(Object)를 생성하거나 관계(Relation)를 추가하는 이벤트를 발생**시킵니다. 이렇게 하면 외부 데이터가 ActiveGraph의 그래프 저장소 내로 '투영(Project)'되어, 다른 Behavior들이 그래프를 통해 이 데이터에 반응할 수 있게 됩니다.

Pack의 핵심은 **'무엇을 할지(Behavior)'를 정의**하는 데 있으며, 외부 데이터는 그 행동이 실행될 때 동적으로 연결됩니다.

---

### 3. 무엇을 Behavior로 만들지에 대한 가이드라인과 원칙

ActiveGraph에서 Behavior는 시스템의 모든 동적 측면을 정의합니다. Behavior를 설계할 때는 다음의 가이드라인을 따르는 것이 좋습니다.

*   **단일 책임 원칙 (Single Responsibility)**: 하나의 Behavior는 **하나의 명확한 작업**만 수행해야 합니다. 예를 들어, "DB에서 데이터를 가져와 요약하는" Behavior보다는 "DB에서 데이터를 가져오는" Behavior와 "데이터를 요약하는" Behavior로 분리하는 것이 좋습니다.
*   **이벤트에 반응하라 (React to Events)**: Behavior는 특정 이벤트 패턴이나 그래프 상태 변화에 **구독(Subscribe)**하여 동작해야 합니다. 직접 다른 컴포넌트를 호출(Instruction)하기보다는, 그래프의 변화에 **반응(React)**하는 방식으로 설계합니다.
*   **상태를 변경하려면 이벤트를 발생시켜라 (Emit Events)**: Behavior의 모든 결과물(상태 변경, 새로운 사실)은 새로운 이벤트를 발생시켜 로그에 기록해야 합니다. 그래프는 이 이벤트들을 재생하여 갱신됩니다. 이는 시스템의 모든 변화를 감사 가능(Auditable)하게 만듭니다.
*   **도구(Tool)와의 명확한 구분**: Behavior는 **'왜'** 그 행동을 하는지(의사결정, 판단)에 가깝고, Tool은 **'어떻게'** 그 행동을 하는지(API 호출, DB 쿼리)에 가깝습니다. Behavior는 필요에 따라 Tool을 호출할 수 있습니다.
*   **LLM 행동의 특수성**: LLM을 사용하는 Behavior(`@llm_behavior`)는 프롬프트와 도구 사용이 명확히 정의되어야 하며, 그 응답 또한 이벤트로 기록되어야 합니다.

간단히 요약하면, **"시스템의 상태를 변화시키거나, 변화에 반응하여 새로운 결정을 내리는 모든 로직 단위"**를 Behavior로 만들면 됩니다.

---

### 4. 이벤트 로그 분석을 통한 적응(Adaptation) 과정과 기록 방식

이벤트 로그를 분석해 시스템을 개선하는 과정은 ActiveGraph의 철학과 완벽하게 들어맞습니다. 이는 외부에서 주입되는 패치가 아니라, **시스템 자신의 이력(Trace)을 증거(Proof)로 삼아 스스로를 진화시키는 과정**입니다. 이 과정은 **'Regimes'**라는 연구에서 구체적으로 제시됩니다.

적응 과정은 다음과 같은 단계로 이루어집니다.

1.  **진단 (Diagnose)**: 실패한 평가(Failed Evaluation)의 로그를 분석해 문제의 원인을 특정 파이프라인 지점으로 진단합니다.
2.  **수리안 제안 (Propose a Repair)**: 진단된 문제를 해결하기 위한 구체적인 수리안(예: 프롬프트 수정, 도구 호출 방식 변경)을 제안합니다.
3.  **검증 및 승격 (Validate & Promote)**: 제안된 수리안은 정적 검사, 샌드박스 실행, in-sample 평가, **보류된 데이터(Held-out)를 통한 검증** 등 여러 단계의 게이트(Gate)를 거칩니다. 모든 검증을 통과한 수리안만 승격(Promote)됩니다.
4.  **기록 (Record)**: 이 모든 과정(진단, 수리안 제안, 각 게이트의 통과/실패 여부, 최종 승격/폐기 결정)은 **그 자체로 이벤트가 되어 로그에 기록**됩니다.

**그렇다면, 이 적응 과정은 Eve 프레임워크의 디렉토리 파일들을 업데이트할까요, 아니면 ActiveGraph 런타임을 수정할까요?**

정답은 **"둘 다"**입니다. 하지만 그 역할과 방식은 명확히 구분됩니다.

*   **Eve 프레임워크의 파일들 (정적 설정 수정)**: 적응의 결과로 에이전트의 **정책(Policy)이나 규칙(Rule)**이 변경되어야 한다면, Eve의 `agent/instructions.md`와 같은 파일이 업데이트됩니다. 예를 들어, "날짜 형식을 항상 'YYYY-MM-DD'로 변환하라"는 새로운 지침이 추가된다면, 이는 `instructions.md` 파일에 반영됩니다. 이는 **장기적인 '법전(Law)'의 개정**에 해당합니다.
*   **ActiveGraph 런타임 (동적 상태 반영)**: 적응의 결과가 일회성 수리나 특정 컨텍스트에서만 적용되는 **전술적(Tactical)인 교훈**이라면, 이는 ActiveGraph의 그래프나 Behavior에 직접 반영됩니다. 예를 들어, 특정 유형의 질문에 대해 과거에 성공했던 도구 호출 패턴을 기억했다가 다음에 같은 상황이 오면 재사용하도록 Behavior를 수정하거나, 새로운 객체와 관계를 그래프에 추가하는 방식입니다. 이는 **단기적인 '교과서(Textbook)'의 갱신**에 해당합니다.

**결론적으로, 적응 과정은 다음과 같은 선순환 구조를 이룹니다.**

1.  ActiveGraph 로그에서 실패 패턴을 **진단**합니다.
2.  그 진단에 기반해 **수리안**을 제안합니다.
3.  수리안이 검증되면, 그 내용의 성격에 따라 **Eve의 파일 시스템(영구적인 규칙)**을 업데이트하거나, **ActiveGraph의 그래프/Behavior(동적인 교훈)**를 변경합니다.
4.  이 모든 결정과 행동은 다시 **ActiveGraph의 이벤트 로그에 기록**되어, 미래의 또 다른 적응을 위한 데이터가 됩니다.