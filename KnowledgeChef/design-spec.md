# ActiveGraph Agent Framework Design Spec

## Purpose

This document captures the current design concept for a generic agent framework
that starts with DB natural-language querying and later expands to file-to-KB
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
- The first `system-model.yaml` schema is `activegraph.system-model.v0`, defined in this document.
- Long-term, `SKILL.md` files are generated from system-model specs by the coding agent. Near-term, packing and `SKILL.md` generation are deferred; implementation should focus on behavior execution, event traces, and behavior adaptation.
- Replay is strict for deterministic behaviors before LLM adapters are added. LLM-backed behaviors must run through recorded fixtures or cache-backed replay in tests. Live LLM replay is allowed only in explicit exploratory runs and must be marked non-deterministic in the trace.
- `llm-wiki` writes target an OKF Knowledge Bundle.
- KB page writes are approval-gated by default.
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

The Text-to-SQL runtime must be pack-configurable. Hospital DB and TechShop DB should use the same runtime and behavior contracts, with different pack-local environment files and system-model declarations.

The next development loop should be TDD-first:

1. Add one eval case.
2. Run the CLI/eval driver and observe failure.
3. Implement the smallest deterministic behavior to pass.
4. Record event trace.
5. Add LLM adapter only after deterministic behavior and scoring are stable.

## Pack Directory Structure

The runtime should support multiple agents as packs. A pack is the unit that binds one shared runtime to a domain, environment, system model, prompts, evals, and generated skill docs.

Recommended layout:

```text
activegraph/
  data/
    hospital.db
    techshop.db

  llm-wiki/
    <okf-knowledge-bundles>

  text-to-sql-agent/
    instructions.md
    src/
      <ActiveGraph runtime source>
    scripts/
      build_hospital_db.py
      verify_hospital_db.py
      run_pack.py
      run_eval.py
    packs/
      hospital-db/
        system-model.yaml
        .env
        SKILL.md
        prompts/
        evals/
          cases.jsonl
        .tests/
          traces/
          graphs/
          runs/

      techshop-db/
        system-model.yaml
        .env
        SKILL.md
        prompts/
        evals/
        .tests/

      hospital-db-medical-kb/
        system-model.yaml
        .env
        SKILL.md
        prompts/
        evals/
        okf/
          bundle-root.md
        .tests/

      file-to-okf-kb/
        system-model.yaml
        .env
        SKILL.md
        prompts/
        evals/
        .tests/
```

Pack `.env` files contain environment-specific bindings, not reusable behavior logic. Examples:

```dotenv
TEXT_TO_SQL_DB_URL=sqlite:///../../data/hospital.db
ACTIVEGRAPH_EVENT_STORE_URL=sqlite:///.tests/runs/events.sqlite
OKF_BUNDLE_DIR=../../llm-wiki/hospital-medical
```

This lets the same Text-to-SQL runtime process hospital DB, TechShop DB, or a hybrid DB plus KB pack by changing pack configuration rather than changing runtime code.

Pack generation rules:

- `system-model.yaml` is the primary source of truth.
- Long-term, `SKILL.md` is generated from `system-model.yaml` by the coding agent. Near-term, do not implement packing or skill generation.
- `instructions.md` remains the shared system prompt entry point for the Text-to-SQL runtime.
- Pack-local prompts can be referenced by behaviors.
- Pack-local `.tests` captures traces, graph projections, replay outputs, and eval results.
- Pack-local `.env` binds external resources such as DB URLs and OKF bundle roots.

## Future Product: Raw File to LLM-Wiki KB

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

## Future Product: KB Question Answering

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

Evaluation should be a first-class part of the system model.

Text-to-SQL evals:

- input question
- expected SQL properties
- expected rows
- expected answer substrings
- forbidden SQL operations

KB ingestion evals:

- input file fixture
- expected chunks
- expected claims
- expected KB page path
- expected index entries
- expected OKF frontmatter fields

KB QA evals:

- input question
- expected cited page
- expected answer facts
- forbidden unsupported claims

Evaluation should run without LLM calls first. LLM behaviors can be evaluated later through recorded fixtures and replay caches.

## Required CLI Surfaces

Initial DB CLI:

```text
submit-question
run-eval
trace
inspect-graph
```

Future KB CLI:

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

Near-term adaptation scope is behavior-only. The system should not implement pack generation, `SKILL.md` generation, or broad harness runtime mutation yet. Runtime changes should be proposed only after repeated behavior-level evidence shows that the runtime itself is the limiting factor.

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

- pack generation
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
10. Keep Text-to-SQL and KB workflows as domain packs over the same runtime.
11. Long-term, generate `SKILL.md` from system-model specs; near-term, defer packing and skill generation.
12. Store external resource bindings in local `.env` files and commit non-secret `.env.example` files.
13. Use `.tests` for test outputs and scratch artifacts.
14. Treat OKF writes as approval-gated external mutations by default, with one approval per raw file upload request.
15. Use event-log analysis to adapt behavior definitions first; runtime adaptation is a later, evidence-heavy step.

## Near-Term Implementation Plan

1. Keep implementation focused on behavior execution, not pack generation.
2. Implement a deterministic CLI driver against the local runtime in `activegraph/text-to-sql-agent/src`.
3. Implement deterministic behaviors for question -> intent -> SQL -> result -> answer.
4. Record event traces, graph projections, run results, and eval results under `.tests`.
5. Add event-log analysis that produces behavior adaptation candidates.
6. Validate behavior adaptations with strict replay and eval cases before applying them.
7. Handle environment variables with local `.env` plus committed non-secret `.env.example` conventions.
8. Add optional LLM adapters behind the same behavior contracts only after deterministic behavior and adaptation traces are stable.
9. Defer pack scaffolding and `SKILL.md` generation until the behavior loop is proven.
10. Later, generalize the same model shape for file-to-OKF-KB ingestion.

## Resolved Questions

- `system-model.yaml` uses `activegraph.system-model.v0`, defined above, but near-term work should focus on behavior execution rather than complete pack scaffolding.
- Packing and `SKILL.md` generation are deferred for now. Long-term, `SKILL.md` should be generated from system-model specs by the coding agent.
- SQLite is the first persistent local event store.
- Replay is strict for deterministic and recorded-fixture runs; live LLM runs are explicitly non-deterministic exploration.
- Environment variables use local `.env` files with committed non-secret `.env.example` templates. Real local `.env` files should stay uncommitted.
- `llm-wiki` integration writes to OKF Knowledge Bundles.
- OKF approval happens once per raw file upload request. The approved run can write the OKF concept and index updates derived from that file.
- KB page writes are approval-gated by default.

## Deferred Decisions

- Exact pack scaffolding and pack loader behavior.
- Whether generated `SKILL.md` files are committed, regenerated on demand, or both.
- How much of the local ActiveGraph runtime should be wrapped versus modified directly for pack loading.
- How far behavior adaptation can be auto-applied after the eval suite becomes stable.


