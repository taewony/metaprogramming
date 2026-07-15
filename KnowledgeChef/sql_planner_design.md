# SQL Planner Resolution Design

## Purpose

`v11_sql_planner_resolution` hardens the DB question-answering loop before KB/RAG work resumes. The goal is to handle imperfect real-world questions before SQL generation while preserving the current ActiveGraph properties:

- deterministic behavior remains the default path;
- every assumption, clarification, LLM call, and repair is visible in graph/event logs;
- unsupported prompts become eval cases or adaptation proposals instead of hidden branches;
- SQL execution remains read-only and bounded by safety policies.

This document is the design checkpoint before implementation.

## Current State

The current executable Text-to-SQL runtime is still intentionally simple:

```text
question.submitted
  -> parse_intent       # RuleCatalog.match + entity validation
  -> intent.created
  -> compile_sql        # SQL comes from matched rule
  -> sql.generated
  -> execute_sql        # SQLite SELECT only
  -> sql.executed
  -> synthesize_answer
  -> answer.created
```

v10 added session memory before this pipeline. In practice:

```text
raw prompt + session graph
  -> session_resolution
  -> resolved prompt
  -> question.submitted
```

This works for cases such as `그 의사는 어느 병원이야?`, but the next gap is broader than anaphora. We need a pre-SQL planner that can reason about imperfect prompts and either produce a fully specified executable intent or stop safely with a clarification.

## Problem Classes

v11 targets five classes of query imperfection:

| Class | Example | Desired outcome |
| --- | --- | --- |
| Ellipsis | `VIP 몇 명?` | Fill omitted entity/filter from session or schema semantics. |
| Ambiguity | `가장 많이 팔린 거` | Detect multiple valid interpretations and ask clarification unless confidence is high. |
| Implicit constraint | `이번 달 매출` | Expand time/status assumptions, such as current month and confirmed orders. |
| Concept mismatch | `회원 수`, `상품 수`, later `학생 수` | Map user vocabulary to schema/domain vocabulary with evidence. |
| Multi-intent | `VIP 고객은 몇 명이고 누구야?` | Split into count + list sub-intents or return a composed plan. |

## Design Position

The planner must not be a hidden SQL generator.

It should produce one of these outcomes:

```text
resolved
  -> a single fully specified prompt/intent candidate can continue to RuleCatalog/SQL

multi_intent_resolved
  -> multiple explicit sub-intents can be executed under a bounded orchestration plan

clarification_required
  -> answer asks the user a specific question; no SQL is generated

unsupported
  -> event log/adaptation path records why no safe resolution exists
```

## New Behavior Boundary

Yes, v11 should define new behavior contracts.

The minimal implementation can start with one new behavior and later split it as complexity grows:

```yaml
- id: resolve_sql_planner
  runtime:
    on: [question.submitted]
    creates:
      - planner_resolution
      - clarification_request
      - answer
    emits:
      - planner.resolved
      - clarification.required
      - planner.unsupported
  implementation: SQLPlannerResolver.resolve
```

Then `parse_intent` should move from `question.submitted` to `planner.resolved`:

```yaml
- id: parse_intent
  runtime:
    on: [planner.resolved]
    creates:
      - intent
      - entity_validation
      - answer
    emits:
      - intent.created
      - entity.validation_failed
      - answer.created
```

For a low-risk first implementation, we can internally call the planner from `parse_intent` while still emitting `planner_resolution` objects and `planner.resolved` / `clarification.required` events. But the target behavior model should expose `resolve_sql_planner` as its own behavior because it is conceptually separate from rule matching.

## Candidate Object Model

```yaml
planner_resolution:
  fields:
    original_prompt: string
    session_resolved_prompt: string
    planner_resolved_prompt: string
    status: enum[resolved, multi_intent_resolved, clarification_required, unsupported]
    imperfection_types: list
    confidence: number
    assumptions: list
    resolution_strategy: string
    selected_rule_hint: string
    sub_intents: list
    evidence: list
    llm_used: boolean
    llm_invocation_id: string

clarification_request:
  fields:
    question: string
    reason: string
    options: list
    unresolved_slots: list
    source_prompt: string

decision_rationale:
  fields:
    behavior: string
    decision: string
    confidence: number
    evidence: list
    alternatives: list
```

Candidate relations:

```yaml
planner_resolution -[derived_from]-> question
planner_resolution -[uses_session]-> session
planner_resolution -[uses_schema]-> schema_context
planner_resolution -[assumes]-> decision_rationale
clarification_request -[derived_from]-> planner_resolution
intent -[derived_from]-> planner_resolution
llm_invocation -[advises]-> planner_resolution
```

## Resolution Pipeline

Recommended deterministic-first pipeline:

```text
1. Normalize prompt
2. Apply session memory resolution from v10
3. Run planner-resolution detectors
4. Score candidate resolutions
5. If one candidate is high confidence, record assumptions and continue
6. If multiple candidates compete, ask clarification
7. If no deterministic candidate exists and planner LLM is enabled, ask LLM for structured resolution candidates
8. Validate LLM candidate against schema, rules, and SQL safety policy
9. If validated, continue with recorded assumptions
10. Otherwise ask clarification or emit unsupported/adaptation evidence
```

## Confidence Policy

Proposed thresholds for v11:

```yaml
confidence_policy:
  auto_resolve_min: 0.80
  clarification_below: 0.70
  llm_advisor_band: [0.40, 0.80]
  never_execute_below: 0.70
```

Rules:

- `confidence >= 0.80`: proceed, but record assumptions.
- `0.70 <= confidence < 0.80`: proceed only for deterministic, schema-backed resolutions with a narrow candidate set; otherwise clarify.
- `< 0.70`: do not generate SQL.
- Multi-intent plans require every sub-intent to pass the same threshold.

## LLM Fallback Policy

Do we need to call LLM when resolution finally fails?

Not by default.

The default should be clarification or adaptation evidence, not an automatic LLM last resort. A hidden last-resort LLM call would make the system harder to replay, harder to inspect, and easier to accidentally turn into unconstrained SQL generation.

The safer policy is:

```text
LLM is an optional planner advisor, not the owner of the plan.
```

LLM can be used only when all of these are true:

- planner LLM is explicitly enabled by CLI or pack config;
- deterministic resolution produced no high-confidence candidate;
- the prompt is not unsafe and does not request mutation;
- the LLM output is structured, not free-form SQL;
- the candidate is validated against schema/rule catalog/entity validators;
- the final graph records `llm_invocation`, `decision_rationale`, confidence, alternatives, and assumptions.

If LLM resolution still fails validation, the agent should ask a clarification question or emit `planner.unsupported`. It should not proceed to SQL.

## LLM Output Contract

The LLM advisor should return planner-level JSON, not SQL:

```json
{
  "status": "resolved",
  "imperfection_types": ["implicit_constraint"],
  "resolved_prompt": "VIP 고객의 확정 주문 총매출액",
  "assumptions": [
    {
      "slot": "order.status",
      "value": "confirmed",
      "reason": "매출액은 확정 주문 기준으로 계산한다는 pack policy"
    }
  ],
  "candidate_rule_ids": ["vip_customer_revenue_total"],
  "confidence": 0.86,
  "clarification_question": null
}
```

Disallowed LLM output for v11:

```json
{
  "sql": "SELECT ..."
}
```

SQL is still produced by the existing safe compiler path after the plan is resolved.

## New Behavior Set: Target Shape

Near-term v11 can start with four behavior concepts:

```yaml
resolve_sql_planner:
  on: [question.submitted]
  emits: [planner.resolved, clarification.required, planner.unsupported]

parse_intent:
  on: [planner.resolved]
  emits: [intent.created, entity.validation_failed]

compile_sql:
  on: [intent.created]
  emits: [sql.generated]

request_clarification:
  on: [clarification.required]
  creates: [answer]
  emits: [answer.created]
```

Later, if the planner becomes too large, split it into specialized behaviors:

```yaml
detect_query_imperfections:
  on: [question.submitted]
  emits: [imperfections.detected]

resolve_ellipsis:
  on: [imperfections.detected]
  emits: [planner.candidate_created]

resolve_concept_mismatch:
  on: [imperfections.detected]
  emits: [planner.candidate_created]

resolve_ambiguity:
  on: [planner.candidate_created]
  emits: [planner.resolved, clarification.required]

split_multi_intent:
  on: [planner.resolved]
  emits: [sub_intents.created]
```

For now, one planner behavior is enough. Splitting too early will add event noise before we have enough eval cases.

## Declarative System-Model Additions

Add a `planner_resolution_model` section to pack system-model YAML:

```yaml
planner_resolution_model:
  id: hospital_sql_planner_resolution_v11
  confidence_policy:
    auto_resolve_min: 0.80
    clarification_below: 0.70
  llm_advisor:
    enabled_by_default: false
    trigger: no_high_confidence_candidate
    output_schema: planner_resolution_candidate
    may_generate_sql: false
  imperfection_detectors:
    ellipsis:
      enabled: true
      sources: [session_memory, rule_catalog]
    ambiguity:
      enabled: true
      default_action: clarify
    implicit_constraint:
      enabled: true
      policies:
        revenue_status_default: confirmed
    concept_mismatch:
      enabled: true
      mappings:
        회원: customers
        상품: products
    multi_intent:
      enabled: true
      split_markers: ["그리고", "이고", "랑", "및"]
```

Pack-specific mappings belong here, not in generic runtime code.

## First v11 Eval Candidates

Hospital:

```text
h_v11_001: "그 의사 병원은?" after "김지훈 전문분야는?"
  class: ellipsis/anaphora reinforcement
  expected: 김지훈 hospital lookup

h_v11_002: "김지훈은 어디야?"
  class: implicit entity type from prior doctor/session or schema
  expected: clarify if no prior doctor context; resolve if prior context exists

h_v11_003: "예약 몇 건?"
  class: ambiguity/implicit status
  expected: clarify whether all appointments or scheduled appointments unless pack policy defines default
```

TechShop:

```text
t_v11_001: "VIP 고객은 몇 명이고 누구야?"
  class: multi_intent
  expected: count + list, or structured multi-intent unsupported if orchestration not implemented yet

t_v11_002: "이번 달 매출"
  class: implicit temporal/status constraints
  expected: clarify date range unless pack policy has a fixed current-date anchor and order status default

t_v11_003: "가장 많이 팔린 거"
  class: ambiguity
  expected: clarification with options: quantity by product, revenue by product, revenue by brand if available

t_v11_004: "회원 수"
  class: concept mismatch
  expected: customers count, with mapping evidence recorded
```

## Implementation Staging

### Stage 1: Design and Model

- Create this design document.
- Add planner-resolution declarations to system-model YAML in a v11 file, not by mutating v06 in place.
- Add eval candidates as pending/xfail or as focused failing tests one at a time.

### Stage 2: Deterministic Planner Resolver

- Add `activegraph.cli.sql_planner` with:
  - `PlannerResolution`
  - `ClarificationRequest`
  - deterministic detectors
  - confidence scoring
  - system-model loader for `planner_resolution_model`
- Unit-test the resolver without running SQLite.

### Stage 3: Runtime Integration

- Add planner-resolution object/event emission before `RuleCatalog.plan`.
- Keep `parse_intent` behavior responsible for validation and intent creation initially.
- Once stable, change behavior trigger shape so `parse_intent` consumes `planner.resolved`.

### Stage 4: Clarification Path

- If planner returns `clarification_required`, create an `answer` with the clarification question.
- Do not emit `intent.created` or `sql.generated`.
- Inspect must show `planner_resolution`, `clarification_request`, and no SQL object.

### Stage 5: Optional LLM Advisor

- Add `--planner-llm` or pack-level `planner.llm.enabled` separately from `--llm` answer composition.
- LLM advisor returns structured planner candidates only.
- Validated candidate may continue; invalid candidate produces clarification or unsupported.
- Add recorded/mock tests. Live Ollama smoke is optional.

## Inspect Expectations

For a resolved case, `inspect` should show:

```text
planner_resolution#N planner_resolution {
  "status": "resolved",
  "imperfection_types": ["implicit_constraint"],
  "confidence": 0.86,
  "assumptions": [...],
  "llm_used": false
}
intent#N -[derived_from]-> planner_resolution#N
```

For clarification:

```text
planner_resolution#N planner_resolution {"status": "clarification_required", ...}
clarification_request#N clarification_request {"question": "..."}
answer#N answer {"source": "clarification"}
# no sql_query object
```

For LLM advisor usage:

```text
llm_invocation#N -[advises]-> planner_resolution#N
planner_resolution#N {"llm_used": true, "validated": true}
```

## Safety Rules

- Planner resolution cannot bypass SQL safety validation.
- Planner LLM cannot output executable SQL in v11.
- Clarification is preferred over low-confidence execution.
- Every high-confidence assumption must be recorded in graph state.
- Every LLM advisor result must be replayable through recorded fixtures for tests.
- Multi-intent execution must have an explicit max sub-intent count, initially `2`.

## Recommendation

Start v11 with deterministic `resolve_sql_planner` as a graph-visible pre-SQL behavior. Add LLM only as an explicit advisor mode after deterministic planner objects, clarification answers, and inspect output are tested.

The immediate answer to the LLM question is:

```text
Do not call LLM automatically just because resolution failed.
Call LLM only when planner-advisor mode is explicitly enabled, and even then use it to propose a validated resolution or clarification, not SQL.
```

## Implementation Checkpoint

Implemented v11 deterministic scope:

- `system-model.hospital.v11.yaml` and `system-model.techshop.v11.yaml` declare `planner_resolution_model`.
- `resolve_sql_planner` runs before `parse_intent` for v11 packs.
- High-confidence rule-backed assumptions create `planner_resolution` and `decision_rationale` graph objects.
- Ambiguous prompts create `clarification_request` and an answer with `source: clarification`; SQL is not generated.
- Optional planner LLM remains intentionally unimplemented.
