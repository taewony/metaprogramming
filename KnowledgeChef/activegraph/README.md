# ActiveGraph Framework to build KB&DB query/response agent

> The graph is the world. Behaviors are physics. The trace is the proof.

An event-sourced reactive graph runtime for long-running, auditable,
agentic systems. Behaviors react to a shared graph instead of talking
to each other. Every change is traceable. Every run is resumable,
forkable, and diff-able from its event log.

If chat-based agents are a group conversation, Active Graph is a
shared workspace where everyone can see what changed, who changed it, and why.

## Try it in 30 seconds

The bundled Diligence pack runs against recorded fixtures: no API
key, no configuration, byte-deterministic output. You see what the
framework does before you read about how it does it.
Then walk the 10-minute tutorial:
```bash
pip install activegraph
activegraph quickstart
activegraph quickstart --interactive
```

It scaffolds a behavior, runs it against the same fixtures, and ends
with the fork-and-diff workflow — the framework's most differentiated
capability.

## Install
Python 3.11+. Two hard dependencies (`click` for the CLI, `pydantic`
for the pack format); persistence backends and provider integrations
are opt-in extras.
```bash
pip install activegraph                    # core runtime + SQLite store + Diligence pack
```

## Separation between Runtime (loop engine), Word Model/State, and External KB/DB

```
- Vercel Eve Framework의 파일시스템 기반 구조
- ActiveGraph의 감사 가능한 이벤트 소싱 and event loop
- OKF and LLM wiki based Knowledge-base
- SQLite3 DB
```



## What you get

- **Event-sourced graph runtime.** Objects + typed relations + an
  append-only event log. Every mutation is an event; the trace is the
  audit trail.
- **Reactive behaviors as first-class.** Function, class, LLM-backed,
  or attached to typed edges (the relation-behavior primitive — edges
  with logic). Subscriptions are event type + predicate + a Cypher
  subset for graph-shape patterns.
- **Fork-and-diff.** Branch any run at any event into an independent
  fork, configure it differently, and structurally diff the result
  against the parent. Cache replay means the shared prefix doesn't
  re-execute (no new LLM calls). Most agent frameworks can't do this.
- **Packs.** A pack bundles object types, behaviors, tools, prompts,
  and policies for a specific domain. The bundled
  [Diligence pack](activegraph/packs/diligence) is the reference:
  8 object types, 7 behaviors, 3 tools, recorded fixtures.
- **Per-error reference pages.** Every error message ends with a
  `More:` link to a page that explains when it fires, why, and how to
  fix it. Catalog at [docs.activegraph.ai/reference/errors](https://docs.activegraph.ai/reference/errors/).

## Concepts at a glance

The framework's twelve primitives, in roughly the order you meet them
when reading a trace. Each links to its concept page on the doc site;
read those when you want depth on one piece.

- **Graph** — objects and typed relations forming the world the
  framework reasons about. The graph is a projection of the event log;
  every mutation is an event. [→ concepts/graph](https://docs.activegraph.ai/concepts/graph/)
- **Events** — the append-only history. Every behavior fires in
  response to events and produces more events; the trace is the
  ordered log of all of them. [→ concepts/events](https://docs.activegraph.ai/concepts/events/)
- **Behaviors** — the unit of reactive code. Function, class, or
  LLM-backed; declares what events it subscribes to and what it
  produces. The determinism contract is per-behavior. [→ concepts/behaviors](https://docs.activegraph.ai/concepts/behaviors/)
- **Relations** — typed edges between objects, with their own
  behaviors. The relation-behavior primitive — coordination logic on
  the edge, not on either endpoint — is uncommon in other agent
  frameworks. [→ concepts/relations](https://docs.activegraph.ai/concepts/relations/)
- **Patches** — proposed mutations with optimistic concurrency.
  Behaviors propose patches; the runtime applies or rejects them;
  rejections are events in their own right. [→ concepts/patches](https://docs.activegraph.ai/concepts/patches/)
- **Views** — scoped reads of the graph for behavior context. Type
  filters, depth filters, recent-event windows. Views are how
  pattern-driven behaviors see only what they need to. [→ concepts/views](https://docs.activegraph.ai/concepts/views/)
- **Frames** — bounded contexts for a run. Goal, constraints, budget,
  and the registered behaviors for this frame. A run can have one
  frame or many. [→ concepts/frames](https://docs.activegraph.ai/concepts/frames/)
- **Policies** — approval and gating for behavior capabilities. Which
  behaviors can call which tools, which mutations require human
  approval, what the runtime refuses. [→ concepts/policies](https://docs.activegraph.ai/concepts/policies/)
- **Patterns** — the Cypher subset for pattern subscriptions. Beyond
  event-type + predicate, behaviors can subscribe to graph shapes
  (claim-cited-by-evidence, task-blocks-task, …) with `NOT EXISTS`
  and temporal predicates. [→ concepts/patterns](https://docs.activegraph.ai/concepts/patterns/)
- **Replay** — re-execute a run from its event log. Strict mode
  re-fires every behavior and fails on divergence; permissive mode
  reconstructs state without re-firing. The LLM replay cache is what
  makes fork cheap. [→ concepts/replay](https://docs.activegraph.ai/concepts/replay/)
- **Forking** — branch any run at any event into an independent
  fork; structurally diff the fork against the parent. The framework's
  mechanism for hypothesis testing on agentic systems. [→ concepts/forking](https://docs.activegraph.ai/concepts/forking/)
- **Failure model** — a behavior failure is a `behavior.failed`
  event, not an exception. The audit trail captures failures as
  first-class history. Exceptions live at runtime entry points only.
  [→ concepts/failure-model](https://docs.activegraph.ai/concepts/failure-model/)

## The type system at a glance

What's fixed and what's yours. The framework speaks a small vocabulary
of event types — the verbs of what happened. The nouns and edges of
your domain are strings you choose.

**Event types — fixed.** The runtime emits these; the trace, replay,
and observability surfaces all key off them.

- **Lifecycle:** `goal.created`, `runtime.idle`, `runtime.budget_exhausted`
- **Graph:** `object.created`, `object.removed`, `relation.created`, `relation.removed`
- **Behaviors:** `behavior.scheduled`, `behavior.started`, `behavior.completed`, `behavior.failed`, `relation_behavior.started`
- **Patterns:** `pattern.matched`
- **LLM:** `llm.requested`, `llm.responded`
- **Tools:** `tool.requested`, `tool.responded`
- **Patches:** `patch.proposed`, `patch.applied`, `patch.rejected`
- **Approvals:** `approval.proposed`, `approval.granted`
- **Packs:** `pack.loaded`

Behaviors can also emit custom event types — any string. The
`task.completed` signal in the example below is one: an
application-level event the `unblock` relation behavior subscribes
to, flowing through the same log alongside the framework's own.

**Object and relation types — yours.** Any string works. There is no
central schema, no registration step, no enum to extend.
`graph.add_object("claim", {...})` creates a `claim` because you said
`claim`; `graph.add_relation(a, b, "depends_on")` makes a
`depends_on` edge because you said `depends_on`. Packs can attach
optional Pydantic validation per type; absent a pack, the data passes
through unchanged. The Diligence pack's object types (`claim`,
`evidence`, `risk`, `memo`, …) and relation types (`supports`,
`contradicts`, `references`, …) are an example ontology, not framework
base types — you design your own for your domain.

**Patch states — fixed.** `proposed` → `applied` | `rejected`. Three
values, two of them terminal.

The full model — composition, ontology design guidance, the Diligence
pack as a worked example — lives at
[→ concepts/type-system](https://docs.activegraph.ai/concepts/type-system/).

## A small example

The relation-behavior primitive — coordination logic on the edge,
not on either endpoint:

```python
from activegraph import Graph, Runtime, behavior, relation_behavior

graph = Graph()
runtime = Runtime(graph, budget={"max_events": 200, "max_seconds": 60})

@behavior(name="planner", on=["goal.created"])
def planner(event, graph, ctx):
    research = graph.add_object("task", {"title": "Research", "status": "open"})
    memo = graph.add_object("task", {"title": "Draft memo", "status": "blocked"})
    graph.add_relation(research.id, memo.id, "depends_on")

@behavior(name="researcher", on=["object.created"], where={"object.type": "task"})
def researcher(event, graph, ctx):
    task = event.payload["object"]
    if task["data"]["status"] != "open" or "Research" not in task["data"]["title"]:
        return
    graph.add_object("claim", {"text": "Market early but growing.", "confidence": 0.7})
    graph.emit("task.completed", {"task_id": task["id"]})

@relation_behavior(name="unblock", relation_type="depends_on", on=["task.completed"])
def unblock(relation, event, graph, ctx):
    if event.payload["task_id"] == relation.source:
        graph.patch_object(relation.target, {"status": "open"})

runtime.run_goal("Evaluate this startup idea")
runtime.print_trace()
```

The `unblock` relation behavior fires only for events touching one of
its edge endpoints. The conceptual deep-dive on edges-with-logic is
in [`docs/concepts/relations.md`](https://docs.activegraph.ai/concepts/relations/).

## Documentation

- **[docs.activegraph.ai](https://docs.activegraph.ai/)** — full doc site:
  concepts, guides, cookbook, CLI reference, API reference, the
  per-error catalog.
- **[10-minute tutorial](https://docs.activegraph.ai/quickstart/)** — install
  to a working custom behavior, including fork-and-diff.
- **AI coding assistants** — the docs are machine-readable at
  [docs.activegraph.ai/llms.txt](https://docs.activegraph.ai/llms.txt)
  (structured index) and
  [docs.activegraph.ai/llms-full.txt](https://docs.activegraph.ai/llms-full.txt)
  (concatenated full content), generated from the same source markdown
  as the rendered site. Built for AI agents evaluating the framework
  via Claude Code, Cursor, Replit, and similar tooling.
- **[CHANGELOG.md](CHANGELOG.md)** — every release, with per-version
  migration notes.
- **[CONTRACT.md](CONTRACT.md)** — locked design decisions, version
  by version. Useful when you want to know *why* something is the way
  it is.
- **[examples/](examples)** — runnable end-to-end demos:
  [`diligence_real_run.py`](examples/diligence_real_run.py),
  [`resume_and_fork.py`](examples/resume_and_fork.py),
  [`llm_claim_extraction.py`](examples/llm_claim_extraction.py),
  [`diligence_with_tools.py`](examples/diligence_with_tools.py),
  [`operate_a_run.py`](examples/operate_a_run.py),
  [`babyagi.py`](examples/babyagi.py) — BabyAGI's autonomous agent loop,
  rebuilt as three reactive behaviors over a shared graph.

## What this is not

- Not a chat framework. If your problem fits in one conversation, use
  a chat framework.
- Not a workflow engine. Workflows model control flow. This models
  world state.
- Not a rules engine, exactly. Rules engines forward-chain over
  facts. This event-sources over a graph and supports LLM behaviors
  as first-class.
- Not a production graph database. The event log lives in SQLite
  (default) or Postgres behind the `EventStore` protocol; the
  materialized graph lives behind the `GraphStore` protocol —
  in-memory by default, or [FalkorDB](https://docs.activegraph.ai/guides/using-falkordb/)
  for a real, traversable graph backend. For a different
  high-throughput store, plug one in behind either protocol.
- Not magic. Bad behaviors produce bad graphs. The runtime makes the
  badness inspectable, not absent.

---
"Agent를 직접 만들지 말고, agent가 살아갈 world model을 먼저 선언하자. Then behaviors become small, testable physics over that world."

  어떤 객체가 존재하는가?
  어떤 관계가 허용되는가?
  어떤 이벤트가 발생할 수 있는가?
  어떤 행동이 어떤 이벤트에 반응하는가?
  그 행동은 무엇을 읽고, 무엇을 쓸 수 있는가?
  환경에는 어떤 도구를 통해서만 작용할 수 있는가?
  어떤 경우 사람 승인이 필요한가?
  어떻게 평가할 것인가?

  이걸 선언하면 agent는 
  {model spec + behavior pack + policy + eval cases} 로 조립되는 시스템이 됩니다.
  
```
ActiveGraph behavior is the runtime equivalent of an agent skill/action rule.

  SKILL.md tells an agent:

  - when this capability applies
  - what context to read
  - what procedure to follow
  - what tools/actions are allowed
  - what output/side effects are expected

  ActiveGraph behavior should encode the same thing, but executable and auditable:

  - trigger: which event or graph pattern wakes it up
  - view: what part of the world model it can see
  - decision logic: deterministic code or LLM prompt
  - effect: graph patch, tool call, DB query, file write, approval request
  - trace: every step becomes event log

  So:

  SKILL.md = human/agent-readable capability contract
  ActiveGraph behavior = runtime-executable capability contract
  Agent action = environment effect produced by behavior
  Event log = proof of what happened

  Important Distinction

  I would separate three layers:

  System Model
    What exists? Objects, relations, events, policies, tools.

  Behavior Model
    What reacts to what? What can mutate what?

  Execution Model
    How does the runtime schedule, log, replay, fork, and diff actions?

  A lot of agent systems mix these together. I think your direction should keep them separate.

  For Text-to-SQL:

  System model:
    question, schema, sql_intent, sql_query, query_result, answer, score

  Behavior model:
    question -> intent
    intent + schema -> sql_query
    sql_query -> query_result
    query_result -> answer
    answer + expected -> score

  Execution model:
    event log, replay, fork, diff, approval, budget

  How Agent Can Be Built From System-Model-Spec

  I’d define a declarative system-model-spec first, then generate/register runtime pieces from it.

  Example shape:

  system: hospital_text_to_sql
  version: 0.1

  objects:
    question:
      fields:
        text: string
        language: string

    sql_query:
      fields:
        sql: string
        params: list
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
      source: [sql_query, answer]
      target: [question, query_result]

    executed_as:
      source: sql_query
      target: query_result

  events:
    question.submitted:
      payload:
        question_id: string

    sql.generated:
      payload:
        query_id: string

    sql.executed:
      payload:
        result_id: string

  tools:
    sqlite.query:
      input:
        sql: string
        params: list
      output:
        rows: list

  behaviors:
    compile_sql:
      on: [question.submitted]
      reads: [question, schema]
      writes: [sql_query]
      mode: deterministic
      implementation: behaviors.compile_sql

    execute_sql:
      on: [sql.generated]
      reads: [sql_query]
      tools: [sqlite.query]
      writes: [query_result]
      policy:
        readonly_sql_only: true

    synthesize_answer:
      on: [sql.executed]
      reads: [question, query_result]
      writes: [answer]

  Then the runtime can compile this into:

  - object validators
  - relation validators
  - behavior registration
  - tool registry
  - policy gates
  - event payload checks
  - eval scaffolds
  - trace rendering

  This is where the system becomes declarative: the spec says what the world is and what reactions are allowed. Python
  code only fills in the behavior implementation.

  SKILL.md Mapping

  A SKILL.md can become a behavior-pack source.

  For example, a text-to-sql/SKILL.md might say:

  # Text-to-SQL Skill

  ## Trigger
  Use when the user asks a question requiring database lookup.

  ## Required Context
  - database schema
  - allowed SQL operations
  - current user question
  - prior dialogue state if available

  ## Procedure
  1. Identify intent.
  2. Select relevant tables.
  3. Generate read-only SQL.
  4. Execute SQL.
  5. Summarize result.
  6. Emit score if expected answer exists.

  ## Constraints
  - SELECT only.
  - No mutation.
  - Cite tables used.

  ActiveGraph equivalent:

  behavior:
    name: text_to_sql
    trigger: question.submitted
    view:
      objects: [question, schema, dialogue_state]
    tools:
      - sqlite.query
    policy:
      sql:
        allowed_statements: [SELECT]
        deny: [INSERT, UPDATE, DELETE, DROP, ALTER]
    produces:
      - sql_query
      - query_result
      - answer

  So SKILL.md remains useful for human-readable agent instruction, but the declarative model should be the source of
  executable truth.
```