# Overall Evaluation Method for Text-to-SQL / OKF-KB

> TechLead note: the goal is not to crown one architecture by intuition.
> The goal is to define a repeatable evaluation contract that can compare
> multiple approaches on the same questions, schemas, and gold answers.

---

## 1. Problem Framing

We are evaluating systems that convert:

`natural language question -> structured query artifact -> executable action -> answer`

The target backend may be:

- SQL over SQLite / DuckDB
- OKF knowledge traversal
- hybrid SQL + KB retrieval
- agentic tool use over multiple sources

The evaluation method must work even when the internal approach differs.

That means the benchmark should measure:

- planning quality
- intermediate artifact quality
- execution correctness
- final answer correctness
- failure localization

---

## 2. Candidate Approaches

### Approach A. Direct Text-to-SQL

The model generates SQL directly from the question.

**Pipeline**

`question -> SQL -> DB result -> answer`

**Strengths**

- simple to implement
- easy to benchmark against classic Text-to-SQL datasets
- low latency

**Weaknesses**

- hard to inspect intermediate reasoning
- ambiguity handling is fragile
- schema linking errors are common
- difficult to reuse across non-SQL KB backends

**Best use**

- narrow DB tasks
- high-confidence structured schemas
- low-cost prototype systems

---

### Approach B. Planner IR + SQL Compiler

The model first produces a structured intermediate representation, then a deterministic compiler produces SQL.

**Pipeline**

`question -> IR -> SQL -> DB result -> answer`

**Strengths**

- inspectable and auditable
- easier to score the planner separately
- better for ambiguity resolution
- easier to support multiple executors

**Weaknesses**

- higher engineering cost
- IR design becomes a contract that must be maintained
- coverage gaps in the IR can block execution

**Best use**

- production systems needing regression testing
- multi-backend systems
- workloads where traceability matters

This is the current KnowledgeChef direction.

---

### Approach C. OKF-KB Planner + Executor

The system maps the question to OKF entities, concepts, and traversal steps rather than SQL-first artifacts.

**Pipeline**

`question -> OKF plan -> KB traversal -> answer`

**Strengths**

- domain knowledge is explicit
- good for conceptual queries and document-like knowledge
- can unify tables, concepts, and rules in one model

**Weaknesses**

- harder to benchmark with classic SQL metrics
- KB traversal semantics may be less standardized than SQL
- compiler/executor contracts need more custom tooling

**Best use**

- knowledge bases with rich semantics
- mixed structured / semi-structured retrieval
- rule-heavy business logic

---

### Approach D. Hybrid Planner

The system chooses between SQL, OKF traversal, document retrieval, or tool calls.

**Pipeline**

`question -> route -> specialized plan -> specialized executor -> answer`

**Strengths**

- flexible across heterogeneous sources
- can optimize per task type
- best long-term architecture if the system grows

**Weaknesses**

- hardest to evaluate fairly
- more moving parts
- debugging becomes multi-layered

**Best use**

- mature systems with mixed sources
- enterprise assistants
- agent platforms with multiple skills

---

### Approach E. Agentic Tool-Using LLM

The LLM decides when to call SQL, KB, search, or other tools during reasoning.

**Pipeline**

`question -> agent loop -> tool calls -> answer`

**Strengths**

- flexible
- fast to prototype
- can handle open-ended tasks

**Weaknesses**

- weakest auditability
- hard to compare runs reproducibly
- evaluation is noisy if tool policy is not fixed

**Best use**

- exploratory systems
- rapid prototyping
- tasks where controlled determinism is not required

---

## 3. Formal Evaluation Layers

To compare these approaches fairly, use the same evaluation ladder.

### Layer 1. Task Understanding

Measures whether the system understood the question correctly.

Metrics:

- intent accuracy
- concept F1
- ambiguity resolution accuracy
- constraint extraction accuracy

Applicable to:

- all approaches

---

### Layer 2. Intermediate Artifact Quality

Measures whether the system produced a correct structured plan.

Examples:

- SQL string
- IR JSON
- OKF traversal plan
- tool-call plan

Metrics:

- schema validity
- field coverage
- operator correctness
- join correctness
- step ordering correctness

Applicable to:

- all approaches, but artifact type differs

---

### Layer 3. Execution Correctness

Measures whether the artifact executes correctly on the target backend.

Metrics:

- compile success
- runtime success
- result match
- row count match
- value match

Applicable to:

- SQL, OKF traversal, agentic tool use

---

### Layer 4. End Answer Correctness

Measures the final user-visible answer.

Metrics:

- exact answer match
- semantic answer match
- numerical tolerance
- ranking correctness

Applicable to:

- all approaches

---

### Layer 5. Operational Quality

Measures whether the system is practical.

Metrics:

- latency
- token cost
- tool-call count
- retry count
- failure recovery rate

Applicable to:

- all approaches

---

## 4. Unified Benchmark Contract

Every test case should contain:

- `question`
- `schema_context`
- `gold_intermediate`
- `gold_sql` when SQL is relevant
- `gold_result`
- `gold_answer`
- `ambiguity_type`
- `difficulty`
- `backend_type`

This lets us test multiple approaches with one benchmark corpus.

Example:

```yaml
id: Q005
question: "이번 달 매출은 얼마야?"
backend_type: sql
difficulty: medium
ambiguity_type: implicit_constraint
schema_context: |
  orders(id, status, total_amount, ordered_at)
gold_intermediate:
  intent: AGGREGATE
  concept: Order
  constraints:
    temporal: "2026-06"
gold_sql: "SELECT SUM(total_amount) FROM orders WHERE ordered_at LIKE '2026-06%' AND status IN ('confirmed','delivered','shipped')"
gold_result:
  - total_revenue: 1234567
gold_answer: "이번 달 매출은 1,234,567원입니다."
```

---

## 5. Recommended Score Design

Use separate scores first, then aggregate.

### 5.1 Primary scores

- `planner_score`
- `sql_score`
- `execution_score`
- `answer_score`
- `ops_score`

### 5.2 Composite score

For production comparison, compute:

```text
overall_score
  = 0.20 * planner_score
  + 0.20 * sql_score
  + 0.35 * execution_score
  + 0.20 * answer_score
  + 0.05 * ops_score
```

The exact weights can be adjusted by product priorities, but the components should stay separated.

---

## 6. Failure Taxonomy

When a case fails, classify the failure before scoring it as a single number.

### Planner failures

- wrong intent
- wrong concept
- missed ambiguity
- wrong filter or join logic

### Compilation failures

- invalid SQL
- unsupported IR field
- backend-specific syntax mismatch

### Execution failures

- runtime exception
- missing table or column
- type mismatch

### Semantic failures

- query runs but returns wrong rows
- answer paraphrase hides wrong result
- aggregation scope is wrong

### Operational failures

- too slow
- too many retries
- too many tool calls

---

## 7. Candidate Evaluation Modes

### Mode 1. Planner-only

Use when the focus is the quality of planning.

Best for:

- IR-based approaches
- planning regression tests
- prompt upgrades

### Mode 2. SQL-end-to-end

Use when the focus is database answering quality.

Best for:

- direct Text-to-SQL
- planner IR + SQL compiler

### Mode 3. KB-end-to-end

Use when the backend is OKF traversal or mixed KB retrieval.

Best for:

- knowledge-base questions
- document-plus-table tasks

### Mode 4. Mixed-source end-to-end

Use when the system chooses among SQL, KB, and documents.

Best for:

- hybrid assistants
- enterprise query systems

---

## 8. Recommendation for KnowledgeChef

Use a staged evaluation strategy:

1. keep `test_planner.py` as the front-end contract test
2. add SQL compilation tests from `qXXX.json`
3. add executor tests against `data/techshop.db`
4. add gold-result matching
5. add an aggregated report that separates planner, SQL, and execution failures

That gives us both:

- a stable regression test for planner behavior
- a practical end-to-end score for user-facing correctness

---

## 9. Decision Rule

If two approaches have the same final answer accuracy, prefer the one with:

- better intermediate traceability
- lower failure ambiguity
- lower operational cost
- better backend portability

That is the selection rule I would use as TechLead.

