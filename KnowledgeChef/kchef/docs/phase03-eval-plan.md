# Phase 03 Evaluation Plan

> Goal: move from planner-only contract checks to a practical end-to-end score that measures
> `Question -> IR -> SQL -> DB result` quality.

---

## 1. What `test_planner.py` has achieved so far

`kchef/eval/test_planner.py` is now a stable planner contract test.

### Verified behavior

- Loads benchmark cases from `kchef/eval/benchmark/q*.yaml`.
- Runs the standalone planner implementation in `kchef/planner_agent.py`.
- Prints the compiled IR for each case during the test run.
- Saves the compiled IR as `kchef/eval/benchmark/q*.json`.
- Reproduces benchmark output on direct execution:
  - `python .\kchef\eval\test_planner.py -v`
- Verifies planner output with the current `PlanningScorer`.

### Current benchmark coverage

- `Q001`: compound intent
- `Q002`: top-k / ambiguity resolution
- `Q003`: existence check
- `Q004`: trend
- `Q005`: aggregate with temporal constraint
- `Q006`: compare year-over-year revenue

### Current observed output

- `10 passed`
- IR artifacts are persisted for all 6 benchmark cases
- The test harness is now useful as a front-end regression suite

### What this evaluation proves

- The planner can map several natural-language query shapes into a structured IR.
- The planner emits a serializable intermediate artifact.
- Ambiguity resolution is traceable in the IR.
- The current score is a planner score, not a full system score.

### What it does not prove

- It does not prove SQL generation correctness.
- It does not prove the executor can run the generated SQL.
- It does not prove the final DB result matches the gold answer.

---

## 2. Why planner-only evaluation is not enough

The current IR benchmark checks front-end planning quality, but the actual product path is:

`question -> planner IR -> SQL compiler -> executor -> DB result -> answer`

Any of these can fail independently.

Examples:

- The IR is valid, but the SQL compiler emits invalid SQL.
- The SQL is valid, but the executor maps a field incorrectly.
- The query runs, but the result semantics are wrong.
- The planner resolves ambiguity correctly, but the executor misreads the time filter.

So the next evaluation layer must measure the whole chain.

---

## 3. Target: practical end-to-end score

The next score should measure real task completion, not just IR shape.

### Proposed score components

#### A. Planner quality

Reuse the current planner benchmark:

- `schema_valid`
- `intent_correct`
- `concept_f1`
- `source_correct`
- `filter_f1`
- `projection_f1`
- `aggregation_correct`
- `join_correct`
- `ambiguity_resolution_rate`

#### B. SQL compilation quality

Evaluate whether the executor can compile the saved IR JSON into SQL.

Metrics:

- `sql_compile_success`
- `sql_parse_valid`
- `sql_references_valid_columns`
- `sql_references_valid_tables`

#### C. Execution quality

Run the SQL against `data/techshop.db` and compare the result to the gold answer.

Metrics:

- `execution_success`
- `result_exact_match`
- `result_f1`
- `result_row_count_match`
- `result_value_match`

#### D. End-to-end quality

Combine the above into a single score:

```text
end_to_end_score
  = planner_quality
  * sql_compilation_success
  * execution_quality
```

Or, if a weighted score is preferred:

```text
end_to_end_score
  = 0.30 * planner_quality
  + 0.20 * sql_compilation_quality
  + 0.50 * execution_quality
```

The weighted version is better if we want to diagnose whether failures come from planning, translation, or execution.

---

## 4. Recommended eval artifacts

For each benchmark case, keep these files together:

- `qXXX.yaml`: question + expected IR
- `qXXX.json`: compiled IR produced by the planner
- `qXXX.sql`: SQL generated from the IR
- `qXXX.result.json`: raw DB result
- `qXXX.gold.json`: gold result
- `qXXX.report.json`: aggregated evaluation summary

This makes the pipeline auditable.

---

## 5. Next implementation steps

### Step 1. Add a SQL compiler

Implement a deterministic translator:

`IR JSON -> SQL`

Requirements:

- handle `COUNT`, `LIST`, `AGGREGATE`, `TOPK`, `EXISTENCE`, `TREND`, `COMPARE`
- preserve filter semantics
- preserve ordering and limit semantics
- reject unsupported IR instead of guessing

### Step 2. Add an executor harness

Implement:

`SQL -> SQLite execution -> rows`

Requirements:

- run against `data/techshop.db`
- capture query text
- capture exceptions
- capture row count and column names

### Step 3. Add gold result fixtures

For each benchmark case:

- define the expected SQL or expected result rows
- define whether exact row order matters
- define whether the case is aggregate, boolean, single-row, or list

### Step 4. Add an end-to-end scorer

Implement a scorer that reads:

- planner IR JSON
- generated SQL
- DB result
- gold result

and computes:

- planner score
- SQL score
- execution score
- final end-to-end score

### Step 5. Add failure classification

When a case fails, classify the failure:

- planner failure
- SQL compilation failure
- schema mapping failure
- execution failure
- result mismatch

This is essential for debugging regressions.

### Step 6. Expand benchmarks

Add cases that stress each stage:

- nested joins
- null handling
- date boundaries
- multi-step compound questions
- count distinct
- order by + limit
- ambiguity with multiple plausible resolutions

---

## 6. Suggested evaluation flow for Phase 03

1. Planner produces `qXXX.json`.
2. SQL compiler reads `qXXX.json` and emits `qXXX.sql`.
3. Executor runs `qXXX.sql` on `data/techshop.db`.
4. Scorer compares result to gold output.
5. Report aggregates scores across all cases.

This should be the default CI evaluation path for practical correctness.

---

## 7. Definition of success for Phase 03

Phase 03 is complete when:

- planner-only benchmarks remain green
- SQL compilation succeeds for the full benchmark set
- execution succeeds on the benchmark set
- gold result comparison is stable and reproducible
- the evaluation report clearly separates planner, SQL, and executor failures

