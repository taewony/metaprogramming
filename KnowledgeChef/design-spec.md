# ActiveGraph Agent Framework Design Spec

## Purpose

This document captures the current design concept for a generic agent framework
that starts with DB natural-language querying, moves next into third-party
SQLite DB + OKF schema-bundle onboarding, and later expands to file-to-KB
ingestion and KB question answering.

The immediate product path is a Text-to-SQL agent over SQLite. The deeper
architecture goal is a declarative, event-sourced agent framework where agents
are assembled from:

```text
system-model-spec + behavior pack + policy + tools + eval cases
```

The core principle is:

```text
Do not build the agent first.
Declare the world model the agent lives in first.
Then behaviors become small, testable physics over that world.
```

## Current Decisions

The following decisions are locked for the next implementation pass:

- The first persistent local event store is SQLite.
- The system-model schema family starts from `activegraph.system-model.v0`; current deterministic Text-to-SQL packs use the v11 runtime shape.
- Long-term, `SKILL.md` files are generated from system-model specs by the coding agent. Near-term, implement only minimal third-party pack onboarding and eval-run evidence protocols; generated `SKILL.md`, KB/RAG, and sub-agent orchestration remain Future Work.
- Replay is strict for deterministic behaviors before LLM adapters are added. LLM-backed behaviors must run through recorded fixtures or cache-backed replay in tests. Live LLM replay is allowed only in explicit exploratory runs and must be marked non-deterministic in the trace.
- Near-term OKF usage is schema-bundle only: a third party can provide a small OKF bundle that describes the SQLite schema, table semantics, columns, relationships, examples, and constraints.
- OKF KB writes, RAG, and `llm-wiki` ingestion remain Future Work. When enabled later, KB writes are approval-gated by default with one approval per raw file upload request.
- Runtime source code is available locally under `activegraph/text-to-sql-agent/src` and should be referenced for implementation instead of inventing a parallel runtime.
- The system prompt for the Text-to-SQL agent belongs in `activegraph/text-to-sql-agent/instructions.md`.
- Test scratch/output folders should use `.tests`, not `.tmp`.
- External environment configuration is handled with local `.env` files and committed non-secret `.env.example` files. Real local `.env` files should stay uncommitted. The same runtime should eventually run different configurations such as hospital DB, TechShop DB, or hospital DB plus medical knowledge base.

## Source Concepts

The design follows the local ActiveGraph framing in `activegraph/README.md`:

- The graph is the projected world model.
- Behaviors are reactive units of work.
- The event log is the audit trail and replay source.
- Relations can carry coordination logic.
- Runs should be resumable, forkable, and diff-able.
- Packs bundle object types, behaviors, tools, prompts, and policies.

This design also adopts a filesystem-first agent workflow:

- Human Architect writes strategic intent and system declarations into files.
- TechLead Agent converts those declarations into executable systems and evals.
- Runtime records event logs, tool calls, graph mutations, and failures.
- Logs feed reflection and refinement loops.

## Mental Model

External world state is not the graph itself.

Instead:

```text
external world
  -> observation / user input / tool result / file watcher / DB query
  -> event log
  -> projected graph
  -> behavior trigger
  -> action
```

The graph is therefore not truth. It is an auditable belief state.

This matters because behaviors may act on stale or incomplete projections. The framework must model observation quality explicitly instead of pretending that the graph is always correct.

## Layer Separation

The framework should keep three layers separate.

### System Model

Defines what exists:

- object types
- relation types
- event types
- tools
- policies
- context assembly rules
- eval contracts
- external resource bindings
- generated artifacts

### Behavior Model

Defines what reacts to what:

- event subscriptions
- graph-pattern subscriptions
- readable views
- writable object/relation types
- tool access
- deterministic or LLM-backed implementation mode

### Execution Model

Defines how work runs:

- scheduling
- event logging
- graph projection
- patch lifecycle
- replay
- fork and diff
- budget
- failure capture
- approval gates

## SKILL.md and Behavior Mapping

`SKILL.md` is a human/agent-readable capability contract.

It usually specifies:

- when the skill applies
- what context to read
- what procedure to follow
- which tools are allowed
- what output or side effect is expected

An ActiveGraph behavior is the executable and auditable equivalent:

- trigger: which event or graph pattern wakes it up
- view: which part of the graph it can read
- decision logic: deterministic code or LLM prompt
- effect: graph patch, tool call, DB query, file write, or approval request
- trace: every step becomes event log

Mapping:

```text
SKILL.md              -> generated human-readable behavior contract
ActiveGraph behavior -> runtime-executable behavior contract
Agent action         -> environment effect produced by behavior
Event log            -> proof of what happened
```

The executable source of truth is the system-model spec and behavior implementation. Long-term, `SKILL.md` should be generated from that spec by the coding agent so agents and humans can read the capability contract without hand-reading every YAML and Python file. Near-term, generated skills are intentionally out of scope; behavior execution and behavior adaptation come first.

## Observation Model

Because the graph is a projection, the framework needs first-class observation objects.

Example object types:

```yaml
objects:
  observation:
    fields:
      source: string
      observed_at: datetime
      subject: string
      value: any
      confidence: number
      freshness_seconds: integer
      provenance: list
      status: enum[fresh, stale, contradicted, invalidated]

  fact:
    fields:
      claim: string
      confidence: number
      valid_until: datetime
      derived_from: list
```

Example relations:

```yaml
relations:
  observes:
    source: observation
    target: external_resource

  supports:
    source: observation
    target: fact

  contradicts:
    source: observation
    target: fact
```

Important actions should require fresh observations before execution. SQL execution may require a fresh schema snapshot; file mutation may require a fresh workspace snapshot and approval.

## Declarative System Model Schema

The first `system-model.yaml` schema should be intentionally small and implementation-oriented. It declares the world, behavior contracts, context assembly, external environment bindings, policies, evals, and generated artifact targets.

Top-level fields:

```yaml
schema_version: activegraph.system-model.v0
system: string
version: string
description: string

runtime:
  source_dir: string
  event_store:
    type: sqlite
    uri_env: string
  graph_store:
    type: memory | sqlite | falkordb
  replay:
    deterministic: strict
    llm: recorded_fixture_required

instructions:
  system_prompt_file: string

pack:
  name: string
  env_file: string
  generated_skill_file: string

environment:
  resources: map

objects: map
relations: map
events: map
tools: map
policies: map
behaviors: map
evals: map
artifacts: map
```

Example:

```yaml
schema_version: activegraph.system-model.v0
system: hospital_text_to_sql
version: 0.1
description: Natural-language query agent for the hospital SQLite fixture.

runtime:
  source_dir: ../../src
  event_store:
    type: sqlite
    uri_env: ACTIVEGRAPH_EVENT_STORE_URL
  graph_store:
    type: memory
  replay:
    deterministic: strict
    llm: recorded_fixture_required

instructions:
  system_prompt_file: ../../instructions.md

pack:
  name: hospital_db
  env_file: .env
  generated_skill_file: SKILL.md

environment:
  resources:
    database:
      kind: sqlite
      uri_env: TEXT_TO_SQL_DB_URL
      schema_observation: sqlite.inspect_schema

objects:
  question:
    fields:
      text: string
      language: string

  schema_snapshot:
    fields:
      tables: list
      columns: list
      observed_at: datetime
      status: enum[fresh, stale]

  intent:
    fields:
      entity: string
      filters: map
      requested_fields: list

  sql_query:
    fields:
      sql: string
      params: list
      statement_type: string
      status: enum[draft, approved, executed, failed]

  query_result:
    fields:
      rows: list
      row_count: integer

  answer:
    fields:
      text: string
      citations: list

relations:
  derived_from:
    source: [intent, sql_query, answer]
    target: [question, schema_snapshot, query_result]

  executed_as:
    source: sql_query
    target: query_result

events:
  question.submitted:
    payload:
      question_id: string

  schema.observed:
    payload:
      schema_snapshot_id: string

  intent.created:
    payload:
      intent_id: string

  sql.generated:
    payload:
      sql_query_id: string

  sql.executed:
    payload:
      query_result_id: string

tools:
  sqlite.inspect_schema:
    output:
      schema_snapshot: object

  sqlite.query:
    input:
      sql: string
      params: list
    output:
      rows: list
      row_count: integer

policies:
  readonly_sql:
    allowed_statements: [SELECT]
    denied_keywords: [INSERT, UPDATE, DELETE, DROP, ALTER, PRAGMA]

behaviors:
  observe_schema:
    on: [runtime.started]
    tools: [sqlite.inspect_schema]
    writes: [schema_snapshot]

  parse_intent:
    on: [question.submitted]
    reads: [question, schema_snapshot]
    writes: [intent]
    llm:
      required: false
      adapter: deterministic_first

  compile_sql:
    on: [intent.created]
    reads: [intent, schema_snapshot]
    writes: [sql_query]
    llm:
      required: optional
      purpose: sql_generation
      output_schema: sql_query

  execute_sql:
    on: [sql.generated]
    reads: [sql_query]
    tools: [sqlite.query]
    writes: [query_result]
    policy: readonly_sql

  synthesize_answer:
    on: [sql.executed]
    reads: [question, query_result]
    writes: [answer]
    llm:
      required: optional
      purpose: answer_synthesis

evals:
  cases_file: evals/hospital_cases.jsonl
  output_dir: .tests/runs

artifacts:
  trace_dir: .tests/traces
  graph_dir: .tests/graphs
  generated_skill: SKILL.md
```

## Full Context Assembly

The system-model spec must describe how LLM context is assembled. The context should not be an ad hoc prompt string hidden inside behavior code.

Each behavior should declare:

- graph objects to include
- relations to traverse
- recent events to include
- tool schemas to expose
- output schema to enforce
- freshness constraints
- redaction rules
- token or size limits

Example:

```yaml
behaviors:
  compile_sql:
    on: [intent.created]
    reads: [intent, schema_snapshot]

    context:
      include:
        - object: intent
          fields: [entity, filters, requested_fields]

        - object: schema_snapshot
          fields: [tables, columns, foreign_keys]
          filter:
            relevant_to: intent

        - recent_events:
            types: [question.submitted, intent.created]
            limit: 5

      exclude:
        - patients.email
        - patients.phone

      freshness:
        schema_snapshot:
          max_age_seconds: 3600

    llm:
      required: optional
      prompt_template: prompts/compile_sql.md
      output_schema: sql_query
```

Runtime flow:

```text
behavior trigger
  -> resolve triggering event
  -> build declared graph view
  -> apply relation traversal and filters
  -> apply freshness checks
  -> apply redaction and policy
  -> add recent event trace
  -> add tool schemas
  -> add output schema
  -> render prompt
  -> call deterministic function or LLM adapter
  -> validate output
  -> emit patch/event
```

## LLM Dependency Injection

The framework should not be globally LLM-dependent. LLM dependency belongs at the behavior level.

For Text-to-SQL, possible LLM-dependent steps are:

- natural language question to structured intent
- intent/schema to SQL
- query result to natural language answer

Each must support deterministic alternatives for TDD:

```text
prompt_to_intent:
  deterministic fixture/rule | LLM

intent_to_sql:
  deterministic compiler | LLM

result_to_answer:
  deterministic template | LLM
```

Provider integrations such as OpenAI, Anthropic, or llamaindex should be adapters. The core eval loop should not depend on them.

## Immediate Product: DB Natural-Language Query

The first vertical slice is a deterministic Text-to-SQL system over the hospital SQLite fixture.

Initial pipeline:

```text
user question
  -> question.submitted
  -> parse_intent
  -> intent.created
  -> compile_sql
  -> sql.generated
  -> execute_sql
  -> sql.executed
  -> synthesize_answer
  -> answer.created
  -> score if eval case exists
```

The current fixture lives at:

```text
activegraph/data/hospital.db
```

The DB setup scripts live at:

```text
activegraph/text-to-sql-agent/scripts/
```

The system prompt lives at:

```text
activegraph/text-to-sql-agent/instructions.md
```

The runtime implementation should use:

```text
activegraph/text-to-sql-agent/src
```

The Text-to-SQL runtime must be pack-configurable. Hospital DB, TechShop DB, and third-party SQLite DBs should use the same runtime and behavior contracts, with different pack-local environment bindings, OKF schema projections, system-model declarations, and eval cases.

The next development loop should be TDD-first:

1. Add one eval case.
2. Run the CLI/eval driver and observe failure.
3. Implement the smallest deterministic behavior to pass.
4. Record event trace.
5. Add LLM adapter only after deterministic behavior and scoring are stable.

## Pack Configuration And Directory Structure

The runtime supports multiple agents as packs. In the current implementation, a pack is a registry entry that binds one shared Text-to-SQL runtime to a DB file, event store, OKF schema bundle, system-model file, LLM defaults, and eval cases. This is intentionally lighter than full generated pack directories.

Current implementation layout:

```text
activegraph/
  data/
    hospital.db
    techshop.db
    <third-party>.db
    <third-party>_events.sqlite

  okf-wiki/
    hospital-medical/
    techshop-commerce/
    <third-party-schema-bundle>/
      index.md
      tables/
        <table>.md

  text-to-sql-agent/
    instructions.md
    agent/
      packs.yaml
      system-model.hospital.v11.yaml
      system-model.techshop.v11.yaml
      system-model.<third-party>.v11.yaml
      system-model.v99.yaml
    evals/
      eval_manifest.yaml
      hospital_consolidated_cases.jsonl
      techshop_cases.jsonl
      <third-party>_cases.jsonl
    src/
      <ActiveGraph runtime source>
    .tests/
      runs/
      sessions/
      adaptations/
      eval-runs/
```

The near-term pack registry entry is the source of environment binding:

```yaml
packs:
  thirdparty-db:
    display_name: Third Party DB Agent
    runtime: text-to-sql
    system_model: system-model.thirdparty.v11.yaml
    env:
      DB_FILE: ../../data/thirdparty.db
      EVENT_STORE: ../../data/thirdparty_text_to_sql_events.sqlite
      OKF_BUNDLE_ROOT: ../../okf-wiki/thirdparty-schema
    capabilities:
      db: true
      schema: true
      kb: false
    schema:
      format: okf
      root: ../../okf-wiki/thirdparty-schema
```

Pack validation must check:

- DB file exists and is readable as SQLite.
- Event-store parent is writable.
- System-model YAML loads and declares an executable rule catalog, even if initially sparse.
- OKF schema bundle exists, has `index.md`, and lists table files.
- OKF table/column declarations align with the actual SQLite schema.
- Eval manifest maps the pack to a runnable cases file.

Future generated pack directories may include generated `SKILL.md`, pack-local prompts, and pack-local `.env` files. That generation is not required for the v11 deterministic third-party onboarding path.

## DB Query And Response Completion Gate

Before implementing KB ingestion or RAG query, the DB query/response loop must be hardened as its own product surface. The goal is not only to answer known prompts, but to make failures, adaptations, and imperfect real-world queries inspectable.

The completion gate is:

```yaml
v09_adaptation_loop:
  status: completed
  focus: "Use event logs to improve harness/runtime behavior without hiding changes."
  deliverables:
    - "Event-log analyzer classifies failures, unsupported prompts, slow paths, validation misses, and user corrections."
    - "Adaptation proposals are stored as graph/event artifacts before code, YAML, or eval changes are applied."
    - "Accepted proposals generate new eval cases, system-model patches, or behavior tests."

v10_multi_turn_and_memory:
  status: completed
  focus: "Support session-scoped graph reasoning."
  deliverables:
    - "Session graph tracks prior questions, answers, entities, filters, SQL, rows, and unresolved references in a local JSON graph selected by `--session-id`."
    - "Ellipsis/anaphora resolution uses graph state before asking the LLM; current deterministic coverage includes hospital doctor references and TechShop VIP count ellipsis."
    - "Full Context distinguishes current run graph, session memory, pack KB, and long-term adaptation artifacts."

v11_sql_planner_resolution:
  status: completed
  focus: "Handle real-world query imperfections before SQL generation."
  deliverables:
    - "Implemented deterministic `resolve_sql_planner` behavior for v11 packs before intent parsing."
    - "Planner records `planner_resolution`, `decision_rationale`, and `clarification_request` graph objects."
    - "Low-confidence ambiguity returns clarification with no SQL; high-confidence rule-backed assumptions are recorded in graph state."
```

This means current `--llm` answer composition is not enough. It improves the final wording after deterministic SQL execution, but unsupported prompts still need either declarative rule adaptation or a planner-resolution behavior before SQL generation. The event-log adaptation loop should turn failures such as unsupported prompts or typo variants into explicit proposals, eval cases, and system-model patches.

KB/RAG and sub-agent work are deferred until this DB loop and the v11.5 third-party onboarding loop can show:

- failed or unsupported DB prompts are explainable through `inspect`
- accepted adaptations leave proposal artifacts before source/YAML/eval changes
- multi-turn references are resolved from session graph state
- ambiguity and low-confidence assumptions are either clarified or recorded
- SQL repair and planner repair obey circuit breakers
- third-party DB packs can be validated, evaluated, and externally scored from recorded evidence

## v11.5 Third-Party Pack Onboarding And Eval-Run Protocol

The next product surface after the v11 deterministic pack runtime is third-party DB onboarding. The goal is not automatic RAG or KB mutation. The goal is to accept a SQLite DB file, a small OKF schema bundle describing that DB, and third-party eval cases, then run a deterministic, auditable evaluation whose event logs can be scored by the third party.

### Inputs From The Third Party

A third-party onboarding package should contain:

```text
thirdparty-package/
  db/
    domain.db
  okf-schema/
    index.md
    tables/
      customers.md
      orders.md
      ...
  evals/
    cases.jsonl
  README.md
```

The OKF bundle in this phase is a schema bundle, not a knowledge base. It should describe relational tables, columns, descriptions, primary keys, and foreign keys. It may use OKF-compatible markdown/frontmatter, but the runtime only requires the table schema projection fields needed by `pack schema` and `pack validate`.

Eval cases should be JSONL. A minimum case is:

```json
{"id":"case_001","prompt":"고객은 몇 명이야?","expected_sql":"SELECT COUNT(*) FROM customers","expected_params":[],"expected_rows":[[20]],"expected_answer_contains":["20"]}
```

If the third party does not want to reveal expected SQL or rows to the agent author, they can provide a private scoring file. The public eval file can then contain only `id`, `prompt`, and policy expectations, while the external judge scores the exported run bundle after execution.

### Onboarding Procedure

The intended CLI workflow is:

```text
pack import thirdparty-db \
  --db activegraph/data/domain.db \
  --okf activegraph/okf-wiki/domain-schema \
  --evals activegraph/text-to-sql-agent/evals/domain_cases.jsonl

pack validate thirdparty-db --json
pack schema thirdparty-db --json
text-to-sql --pack thirdparty-db context "<sample prompt>" --json
text-to-sql --pack thirdparty-db eval --json
```

The current implementation includes `pack import` for this minimal v11.5 path. It registers the DB, OKF schema bundle, eval cases, generated system-model file, and eval manifest entry. Manual onboarding remains useful for review or custom pack authoring:

1. Copy the SQLite DB under `activegraph/data/`.
2. Copy the OKF schema bundle under `activegraph/okf-wiki/`.
3. Add a pack entry to `activegraph/text-to-sql-agent/agent/packs.yaml`.
4. Create `system-model.<domain>.v11.yaml` with `schema_projection`, `behavior_model`, `planning_model.rule_catalog`, and optional `planner_resolution_model`.
5. Add the pack's eval file to `activegraph/text-to-sql-agent/evals/`.
6. Add the pack to `eval_manifest.yaml` so bare `eval` chooses the correct cases file.
7. Run `pack validate`, `pack schema`, `context`, `ask`, and `eval`.

### System-Model Bootstrap Boundary

For arbitrary third-party domains, the runtime should not pretend it can answer natural-language questions merely from table names. A system-model bootstrap step should create a sparse, inspectable model:

```yaml
schema_version: system-model.v11
name: thirdparty-db-agent
schema_projection:
  source:
    type: okf_bundle
  include:
    tables:
      - tables/customers.md
      - tables/orders.md
behavior_model:
  behaviors:
    - id: resolve_sql_planner
    - id: parse_intent
    - id: compile_sql
    - id: execute_sql
    - id: synthesize_answer
planning_model:
  rule_catalog:
    id: thirdparty_text_to_sql_rules_v01
    rules: []
```

Rules should then be added from approved eval cases, observed failures, or human-authored domain decisions. This keeps behavior changes explicit and replayable. A later LLM planner can propose candidate rules, but it must not silently generate and execute SQL outside the event protocol.

### Eval-Run Event Protocol

An eval run should be represented as a first-class run group, not just a console summary. The protocol should create one eval-run artifact and one ordinary ActiveGraph run per case.

Required eval-run objects:

```yaml
objects:
  eval_run:
    fields: [eval_run_id, pack_id, cases_file, started_at, completed_at, status]
  eval_case:
    fields: [id, prompt, source, expected_policy]
  eval_case_result:
    fields: [case_id, run_id, ok, sql, params, rows, answer, failure_summary]
  eval_score:
    fields: [case_id, scorer, score, rubric, notes]
```

Required eval-run events:

```text
eval.started
eval.case_started
question.submitted
planner.resolved | clarification.required | behavior.failed
sql.generated
sql.executed
answer.created
eval.case_completed
eval.case_scored
eval.completed
```

`question.submitted` through `answer.created` are normal per-case run events. `eval.*` events bind those runs back to the eval-run group so a third party can audit both case-level evidence and aggregate scoring.

### External Scoring Procedure

The third-party scoring loop should be:

```text
third-party package received
  -> pack import or manual pack registration
  -> pack validate
  -> schema projection check
  -> deterministic eval run
  -> export eval-run bundle
  -> third-party judge scores case outputs from event evidence
  -> external scores are recorded as eval.case_scored / external_judgment.recorded
  -> adaptation proposals are generated only from scored evidence
```

The exported eval-run bundle should contain:

```text
.tests/eval-runs/<eval_run_id>/
  manifest.json
  summary.json
  cases/
    <case_id>/
      result.json
      trace.jsonl
      graph.json
      scoring-input.json
      external-score.json   # optional, written after third-party scoring
```

The scoring input should include prompt, final answer, SQL, params, rows or row summary, planner resolution, clarification request, failure events, and graph artifact paths. If rows contain sensitive data, the export must support redaction or row summaries before external review.

### Acceptance Criteria For v11.5

Status: implemented for the deterministic pack-runtime path.
v11.5 is complete when:

- a third-party DB and OKF schema bundle can be registered without modifying runtime source code;
- `pack validate` catches DB/OKF/schema mismatches before eval;
- bare `text-to-sql --pack <id> eval` selects the pack's eval cases;
- every eval case has a run id, trace, graph snapshot, and result artifact;
- eval-run aggregate metadata is written to disk and event store;
- external score artifacts can be attached without rewriting the original run evidence;
- unsupported prompts become adaptation proposals, not hidden runtime branches;
- KB/RAG/sub-agent features remain disabled unless explicitly selected by a future pack capability.

### Out Of Scope For v11.5

- Writing OKF knowledge-base pages from raw files.
- RAG over OKF concept documents.
- Multi-agent/sub-agent orchestration.
- Fully automatic SQL generation over arbitrary schemas without eval-backed rules.
- Training or fine-tuning from third-party traces.

## Future Work: Raw File to LLM-Wiki KB

After the DB path proves the framework, the same model should support raw file ingestion into an external structured KB such as `llm-wiki`.

The `llm-wiki` folder should follow the Open Knowledge Format (OKF) draft specification. In this design, an `llm-wiki` target is an OKF Knowledge Bundle: a directory tree of UTF-8 markdown concept documents with YAML frontmatter, optional `index.md` files for progressive disclosure, and optional `log.md` files for update history. Concept documents require a non-empty `type` field; recommended frontmatter includes `title`, `description`, `resource`, `tags`, and `timestamp`. Consumers must tolerate unknown types, unknown frontmatter keys, broken links, and missing optional files.

Pipeline:

```text
raw file observed
  -> file.observed
  -> extract_chunks
  -> chunk.created
  -> extract_claims
  -> claim.created
  -> classify_topics
  -> topic.created
  -> propose_okf_concept
  -> upload approval requested once for the raw file
  -> approval.granted
  -> okf_concept.written
  -> update_index
  -> kb_index.updated
```

Candidate object types:

```yaml
objects:
  raw_file:
    fields:
      path: string
      content_hash: string
      observed_at: datetime

  document_chunk:
    fields:
      text: string
      source_span: map
      content_hash: string

  claim:
    fields:
      text: string
      confidence: number
      provenance: list

  kb_topic:
    fields:
      title: string
      slug: string
      parent: string

  kb_page:
    fields:
      path: string
      title: string
      summary: string
      status: enum[draft, proposed, published, stale]

  kb_index:
    fields:
      path: string
      entries: list

  okf_bundle:
    fields:
      root: string
      okf_version: string
      status: enum[observed, proposed, updated]

  okf_concept:
    fields:
      concept_id: string
      path: string
      type: string
      title: string
      description: string
      resource: string
      tags: list
      timestamp: datetime
      body: string
```

Candidate behaviors:

```yaml
behaviors:
  observe_files:
    on: [scan.requested]
    tools: [filesystem.read]
    writes: [raw_file, observation]

  extract_chunks:
    on: [raw_file.observed]
    reads: [raw_file]
    writes: [document_chunk]

  extract_claims:
    on: [document_chunk.created]
    reads: [document_chunk]
    writes: [claim]
    llm:
      required: optional
      purpose: information_extraction

  propose_okf_concept:
    on: [claim.created]
    reads: [claim, kb_topic]
    tools: [okf.propose_concept]
    writes: [kb_page, okf_concept, approval_request]
    policy: approval_required

  write_okf_concept:
    on: [approval.granted]
    reads: [okf_concept]
    tools: [okf.write_concept]
    writes: [kb_page]
    policy: approval_required

  update_kb_index:
    on: [kb_page.updated]
    reads: [kb_page, kb_index]
    tools: [okf.propose_index]
    writes: [kb_index, approval_request]
    policy: approval_required
```

The KB writer is approval-gated by default because it mutates external state. Approval is requested once per raw file upload request. After that approval is granted, the run may create the proposed OKF concept files and index updates derived from that uploaded file. The write flow is:

```text
raw file upload request -> one approval -> claim graph -> proposed OKF concept/index patch -> OKF bundle write
```

Automated behaviors may propose OKF patches, update draft graph state, and run conformance checks. They must not write published OKF bundle files for a raw file until that upload request has one approval event. Separate raw file upload requests require separate approvals.

## Future Work: KB Question Answering

When users ask questions about the KB, the system should follow the KB structure rather than performing unstructured retrieval only.

Pipeline:

```text
user question
  -> question.submitted
  -> resolve_topic_from_index
  -> kb_context_selected
  -> retrieve_relevant_pages
  -> synthesize_answer
  -> answer.created
```

The `index.md` structure should be modeled as graph state:

```yaml
objects:
  kb_index:
    fields:
      path: string
      topics: list

  kb_page:
    fields:
      path: string
      title: string
      summary: string

relations:
  links_to:
    source: kb_index
    target: kb_page

  parent_of:
    source: kb_topic
    target: kb_topic

  page_about:
    source: kb_page
    target: kb_topic
```

The answer behavior should cite KB pages and claims:

```yaml
answer:
  fields:
    text: string
    citations:
      - page_path: string
        claim_id: string
```

## Evaluation Strategy

Evaluation is a first-class part of the system model and the pack contract. The near-term priority is DB query evaluation over third-party SQLite packs. KB ingestion and KB QA evals are Future Work.

### Text-to-SQL Eval Cases

Runnable DB eval cases may include:

- `id`
- input `prompt`
- expected SQL text or SQL policy constraints
- expected params
- expected rows or row summary
- expected answer substrings
- expected answer source, such as `deterministic` or `clarification`
- expected planner-resolution status and imperfection types
- forbidden SQL operations

The deterministic scorer can evaluate these fields directly when expected SQL/rows are public.

### Private Third-Party Scoring

A third party may choose not to disclose gold SQL or rows to the agent implementer. In that case:

- the public cases file contains prompts and policy constraints only;
- the agent executes each case and records run evidence;
- an eval-run export bundle is produced;
- the third party scores `scoring-input.json` files externally;
- external scores are attached as immutable artifacts and `eval.case_scored` / `external_judgment.recorded` events.

This keeps benchmark answers private while preserving auditability.

### Future Work Eval Types

KB ingestion evals are deferred and may later include input file fixtures, expected chunks, expected claims, expected KB page paths, expected index entries, and expected OKF frontmatter fields.

KB QA evals are deferred and may later include input questions, expected cited pages, expected answer facts, and forbidden unsupported claims.

Evaluation should run without LLM calls first. LLM behaviors can be evaluated later through recorded fixtures and replay caches.

## Required CLI Surfaces

Initial DB CLI:

```text
pack import              # implemented v11.5
pack validate
pack schema
text-to-sql ask
text-to-sql context
text-to-sql eval
text-to-sql inspect
text-to-sql adapt
eval-run export          # implemented v11.5
eval-run attach-score    # implemented v11.5
```

Future Work KB CLI:

```text
scan-files
ingest-file
propose-okf-write
approve-okf-write
ask-kb
diff-run
replay-run
```

The CLI should expose prompts or query inputs directly so every user-facing interaction can become a test case.

## Replay Policy

Replay starts strict and deterministic.

Before LLM adapters:

- every deterministic behavior must re-run to the same event payloads
- every tool fixture must return the same response
- graph projection after replay must match the original projection
- divergence is a test failure

After LLM adapters:

- eval and CI runs use recorded LLM fixtures or cache-backed responses
- the LLM request identity includes model, prompt template, rendered context, output schema, and relevant tool schema
- replay with recorded fixtures remains strict
- live LLM replay is marked exploratory and non-deterministic
- fork-and-diff is used to compare prompt/model/provider variants

## Event Log Adaptation Loop

Event logs are not just debugging output. They are execution evidence used to adapt behavior definitions, context assembly, prompts, validators, and tests.

The adaptation loop is:

```text
run execution
  -> event log
  -> trace analysis
  -> behavior adaptation candidates
  -> replay / eval validation
  -> approved behavior change
  -> next run
```

Near-term adaptation scope is behavior-first. Minimal pack import/scaffold work is allowed for v11.5 because it is required to onboard third-party DBs, but generated `SKILL.md`, KB/RAG scaffolding, sub-agent orchestration, and broad harness runtime mutation remain deferred. Runtime changes should be proposed only after repeated behavior-level evidence shows that the runtime itself is the limiting factor.
Current v09 implementation:

- `text-to-sql adapt <run-selector>` reads a persisted SQLite event-store run and writes reproducible adaptation artifacts.
- The analyzer currently classifies unsupported prompts, behavior exceptions, validation misses, LLM fallbacks, and slow paths.
- Proposal artifacts include `analysis.json`, proposal JSON files, `adaptation_events.jsonl`, and `adaptation_graph.json`.
- `text-to-sql adapt-accept <proposal-file>` generates draft eval-case and system-model patch-hint artifacts, but does not auto-edit source, YAML, or canonical eval files.

### Recorded Artifacts

For each run, the harness should record:

```text
.tests/
  runs/
    <run_id>/
      events.sqlite
      trace.jsonl
      graph.json
      result.json
      eval.json
      analysis.json

  adaptations/
    proposed/
      adapt-0001.yaml
    accepted/
      adapt-0001.yaml
    rejected/
      adapt-0002.yaml

  replay/
    <run_id>/
      replay-result.json
      diff.json
```

The raw event store is the source of truth. Derived files such as `analysis.json` and adaptation YAML files are reproducible analysis artifacts.

### Trace Analysis

The analyzer should summarize:

- behavior success, failure, latency, and retry counts
- tool calls, tool errors, and payload sizes
- LLM context size, output validation failures, and schema drift
- patch proposed/applied/rejected counts
- stale observation usage
- eval pass/fail status by case
- replay divergence

Example analysis output:

```json
{
  "run_id": "run_001",
  "finding": "compile_sql output schema validation failed",
  "behavior": "compile_sql",
  "frequency": 4,
  "likely_causes": [
    "schema context includes irrelevant tables",
    "output schema is not prominent enough",
    "validator feedback is not retried"
  ],
  "suggested_adaptations": [
    "limit schema_snapshot to relevant tables",
    "move output_schema before examples in prompt",
    "add one deterministic validator-feedback retry"
  ]
}
```

### Adaptation Candidates

An adaptation candidate must include evidence, target, proposed change, and validation plan.

```yaml
id: adapt-0001
scope: behavior
target: behaviors.compile_sql.context
reason: compile_sql repeatedly failed SQL output validation
evidence:
  runs: [run_001, run_002]
  eval_cases: [q001, q002]
change:
  context:
    include:
      - object: intent
        fields: [entity, filters, requested_fields]
      - object: schema_snapshot
        fields: [tables, columns, foreign_keys]
        filter:
          relevant_to: intent
    token_budget:
      max_context_tokens: 3000
validation:
  replay: strict
  eval_cases: [q001, q002, q003]
status: proposed
```

Allowed near-term behavior adaptation targets:

- `behaviors.*.context`
- `behaviors.*.prompt_template`
- `behaviors.*.output_schema`
- `behaviors.*.validator`
- `behaviors.*.retry`
- deterministic fallback rules
- eval cases that reproduce observed failures

Deferred adaptation targets:

- generated pack directories beyond minimal v11.5 pack import
- `SKILL.md` generation
- runtime source mutation
- external write policy relaxation
- OKF write automation beyond the one-approval-per-upload rule

### Approval Rule

Behavior adaptation candidates may be generated automatically, but applying them should be explicit until the eval suite is stable. Runtime source changes require stronger evidence: repeated failures across runs, a candidate patch, strict replay validation, and regression eval results.

## Design Rules

1. Treat graph state as belief, not truth.
2. Model observations, provenance, confidence, and freshness explicitly.
3. Re-observe external state before important actions.
4. Keep LLM dependency behavior-local, not framework-global.
5. Assemble full context from declarative context specs.
6. Keep tools behind policy gates.
7. Start deterministic and TDD-first.
8. Add LLM adapters only after contracts and evals are stable.
9. Prefer event logs and graph diffs over hidden control flow.
10. Keep Text-to-SQL workflows as domain packs over the same runtime; keep KB/RAG workflows in Future Work until the deterministic DB path is proven with third-party packs.
11. Long-term, generate `SKILL.md` from system-model specs; near-term, implement only minimal third-party pack onboarding and defer generated skills.
12. Store external resource bindings in local `.env` files and commit non-secret `.env.example` files.
13. Use `.tests` for test outputs and scratch artifacts.
14. Treat future OKF KB writes as approval-gated external mutations by default, with one approval per raw file upload request.
15. Use event-log analysis to adapt behavior definitions first; runtime adaptation is a later, evidence-heavy step.
16. Make eval-run evidence exportable so a third party can score runs from recorded events, graph snapshots, SQL, answers, and declared expectations.

## Near-Term Implementation Plan

1. Keep v11 deterministic Text-to-SQL behavior stable for declared hospital and TechShop packs.
2. Add v11.5 minimal third-party pack onboarding from SQLite DB file, OKF schema bundle, and eval JSONL.
3. Validate imported packs by checking DB accessibility, OKF schema coverage, declared table/column bindings, event-store configuration, and eval manifest wiring.
4. Project the OKF schema bundle into runtime graph/context before query execution.
5. Record eval-run events, graph snapshots, SQL/result/answer evidence, scoring inputs, and exported artifacts under `.tests/eval-runs`.
6. Add `eval-run export` and `eval-run attach-score` so third-party scoring can be external but auditable.
7. Feed failed eval evidence into adaptation proposals; applying YAML/code/eval changes remains explicit.
8. Keep optional LLM answer composition behind deterministic SQL/result contracts; do not add implicit planner LLM fallback in v11.5.
9. Defer generated `SKILL.md`, full pack directory generation, OKF KB ingestion, RAG query, and sub-agent orchestration.
10. Later, generalize the same model shape for file-to-OKF-KB ingestion.

## Resolved Questions

- `system-model.yaml` uses the schema family defined above; near-term work should focus on deterministic behavior execution plus minimal v11.5 third-party pack onboarding.
- Full generated pack directories and `SKILL.md` generation are deferred for now. Long-term, `SKILL.md` should be generated from system-model specs by the coding agent.
- SQLite is the first persistent local event store.
- Replay is strict for deterministic and recorded-fixture runs; live LLM runs are explicitly non-deterministic exploration.
- Environment variables use local `.env` files with committed non-secret `.env.example` templates. Real local `.env` files should stay uncommitted.
- Near-term OKF use is schema-bundle input for DB pack onboarding, not KB writing.
- Third-party eval runs should produce exportable event evidence so external scoring can be replayed and audited.
- Future OKF KB writes require one approval per raw file upload request; the approved run can write the OKF concept and index updates derived from that file.

## Deferred Decisions

- Generated pack directory scaffolding beyond minimal v11.5 pack import.
- Whether generated `SKILL.md` files are committed, regenerated on demand, or both.
- How much of the local ActiveGraph runtime should be wrapped versus modified directly after the minimal pack loader is proven.
- How far behavior adaptation can be auto-applied after the eval suite becomes stable.
- OKF KB ingestion, RAG query, and sub-agent orchestration.







