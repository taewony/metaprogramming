# ActiveGraph Text-to-SQL Plan

## Direction

Build the Text-to-SQL agent with a TDD-first, dependency-free core before
introducing LLM, llama-index, or ActiveGraph behavior adapters.

The immediate goal is a deterministic loop:

```text
user prompt -> query plan -> SQL + params -> SQLite rows -> answer -> score
```

This gives us a stable contract for evaluation, regression testing, and later
event-log wrapping.

## Current Baseline

- SQLite fixture: `activegraph/data/hospital.db`
- Database builder: `activegraph/text-to-sql-agent/scripts/build_hospital_db.py`
- Database verifier: `activegraph/text-to-sql-agent/scripts/verify_hospital_db.py`
- TDD driver: `activegraph/text-to-sql-agent/scripts/hospital_tdd_driver.py`
- Eval cases: `activegraph/text-to-sql-agent/evals/hospital_cases.jsonl`
- Focused tests: `tests/test_activegraph_text_to_sql_tdd.py`

Current passing case:

```text
김지훈 의사의 전공은?
-> SELECT specialty FROM doctors WHERE name = ?
-> [["내과"]]
-> 김지훈 의사의 전공은 내과입니다.
```

## TDD Workflow

For each followup:

1. Add one failing JSONL eval case.
2. Add or adjust focused pytest expectations.
3. Implement the smallest deterministic planner/compiler/executor change.
4. Run the focused tests.
5. Run the CLI eval against `activegraph/data/hospital.db`.
6. Only after deterministic behavior is stable, add ActiveGraph events or LLM adapters.

## Near-Term Test Cases

Add these one at a time:

1. Doctor hospital lookup
   - Prompt: `김지훈 의사 병원?`
   - Expected SQL: `SELECT hospital_name FROM doctors WHERE name = ?`
   - Expected row: `["서울중앙병원"]`

2. Doctor count
   - Prompt: `의사 몇명 있니?`
   - Expected SQL: `SELECT COUNT(*) FROM doctors`
   - Expected row: `[5]`

3. Patient insurance number
   - Prompt: `홍길동 환자의 보험은?`
   - Expected SQL: `SELECT insurance_number FROM patients WHERE name = ?`
   - Expected row: `["I12345"]`

4. Available slots
   - Prompt: `김지훈 의사의 가능한 시간은?`
   - Expected SQL joins `doctors` and `availability`
   - Expected rows include `2025-04-02 09:00`, `2025-04-02 11:00`, `2025-04-02 14:00`

5. Scheduled appointments
   - Prompt: `예정된 예약은 몇 개야?`
   - Expected SQL: `SELECT COUNT(*) FROM appointments WHERE status = ?`
   - Expected row: `[2]`

## Core Contracts

Keep the initial contract simple and JSON-friendly:

```json
{
  "ok": true,
  "prompt": "...",
  "sql": "...",
  "params": [],
  "rows": [],
  "answer": "...",
  "error": null
}
```

Eval cases should stay explicit:

```json
{
  "id": "q001",
  "prompt": "김지훈 의사의 전공은?",
  "expected_sql": "SELECT specialty FROM doctors WHERE name = ?",
  "expected_params": ["김지훈"],
  "expected_rows": [["내과"]],
  "expected_answer_contains": ["내과"]
}
```

## Optional LLM Planner

The driver now supports an optional OpenAI-compatible planner mode for local
Ollama:

```powershell
python activegraph/text-to-sql-agent/scripts/hospital_tdd_driver.py ask "김지훈 의사의 전공은?" --planner llm --model qwen3:8b --openai-base-url http://localhost:11434/v1 --openai-timeout 120
```

Current verified local behavior with `qwen3:8b`:

```json
{
  "sql": "SELECT specialty FROM doctors WHERE name = :name",
  "params": {"name": "김지훈"},
  "rows": [["내과"]]
}
```

Rules:

- Deterministic mode remains the default for CI-style evals.
- LLM mode uses the same result contract as deterministic mode.
- The LLM response must compile to a read-only single SELECT statement.
- Both positional params and SQLite named params are supported.
- Keep using mocked OpenAI-compatible tests for regression; real Ollama smoke
  tests are useful locally but should not be required for every test run.

## ActiveGraph Integration Later

After the deterministic TDD core covers enough cases, wrap the same steps with
graph objects and events:

- objects: `question`, `query_plan`, `sql_query`, `query_result`, `answer`,
  `eval_case`, `score`
- relations: `derived_from`, `compiled_to`, `executed_as`, `answered_by`,
  `evaluated_by`
- events: `question.submitted`, `plan.created`, `sql.generated`,
  `sql.executed`, `answer.completed`, `eval.scored`

The adapter should preserve the same CLI/eval contract so existing tests remain
useful.

## Dependency Policy

- Required for current core: Python standard library only.
- Do not require `llama_index` for the TDD/eval path.
- Treat `ch09_text_to_sql.py` as reference/demo source, not the production
  followup architecture.
- Add LLM or framework adapters only behind stable interfaces.

## Verification Commands

```powershell
python activegraph/text-to-sql-agent/scripts/build_hospital_db.py
python activegraph/text-to-sql-agent/scripts/verify_hospital_db.py
python activegraph/text-to-sql-agent/scripts/hospital_tdd_driver.py ask "김지훈 의사의 전공은?"
python activegraph/text-to-sql-agent/scripts/hospital_tdd_driver.py eval
python activegraph/text-to-sql-agent/scripts/hospital_tdd_driver.py ask "김지훈 의사의 전공은?" --planner llm --model qwen3:8b --openai-base-url http://localhost:11434/v1 --openai-timeout 120
python -m pytest tests/test_activegraph_text_to_sql_tdd.py -q --basetemp activegraph/.tmp/pytest-activegraph -p no:cacheprovider
```

On this Windows environment, pytest temp-directory access may require running
the focused pytest command outside the managed sandbox.

---
Your intuition to treat the **Coding Agent** as a *Cognitive Compiler* or *TechLead* is brilliant and highly aligned with the future of software engineering. 

However, based on the `system-model.v99.yaml` context you provided, **you must absolutely avoid choosing between "pure compilation" and "pure LLM-generation."** 

The `system-model.yaml` defines the **"What"** (Behaviors, Objects, Relations, Security, Events), but it **cannot** define the **"How"**—the core algorithmic logic inside `execute_query`, the vector similarity math, or the specific regex patterns in `repair_sql`. If you try to compile or generate *everything*, you will inevitably hit a wall of maintenance hell or hallucinated bugs.

Here is the **Systematic, Expert Guide** to successfully building this Hybrid Agent System.

---

### 1. The Crucial Verdict: Adopt the "Scaffold + Stub" Synthesis Model

Instead of treating the YAML as code to be *interpreted* or *fully generated*, treat it as a **"DSL for System Architecture"** that generates the **Immutable Framework Code**, while leaving the **Mutable Business Logic** to iterative development (either human or an LLM "Junior Dev").

| Approach | What it does | When to use it | The Verdict |
| :--- | :--- | :--- | :--- |
| **Static Compilation (YAML → Runtime)** | Generates the entire runtime executable. | Simple CRUD apps. | **Discard for this case** because YAML lacks the imperative logic (e.g., database connection pooling, embedding models). |
| **LLM Code Generation (YAML → Full Codebase)** | Asks GPT-4 to write all Python/TS files from scratch. | PoC prototypes. | **Discard for Production** because updating the YAML later would overwrite your custom logic, and LLM output is non-deterministic. |
| **The "Scaffold + Stub" Compilation** | YAML generates the **Wiring Framework** (Event Bus, Pydantic Schemas, Security Filters) and creates **Stub files** with exact method signatures, placing `# TODO: Implement` where human logic belongs. | Enterprise-grade, evolving systems. | **Strongly Recommended.** The `system-model` becomes the single source of truth for *architecture*, while developers (or a specialized Coding Agent) fill the stubs. |

---

### 2. The "TechLead" Compiler: What to Auto-Generate (100% Compile)

Write a compiler script (`agent_compiler.py`) that reads the `system-model.yaml`. **Do not** generate the full Behavior logic. Instead, generate the **Boilerplate**:

**A. Data Contracts & Schemas (from `object_model`)**
Generate strict Pydantic (Python) or Zod (TS) classes.

- `compiled/models/objects.py` contains classes for `ResolvedIntent`, `QueryResult`, `SqlQuery`, etc.
- Benefit: If your YAML changes the `filters` field from `string` to `list`, re-running the compiler instantly updates the type-safe models without manual refactoring.

**B. The Event Bus & Subscriber Registry (from `behavior_model` and `on` triggers)**
Generate the boilerplate for the **Parallel Join Barrier**.

- For `fuse_answers` with `on: [sql.executed, rag.synthesized]`, the compiler auto-generates an `EventCollector` class that waits for both events before firing.
- Benefit: You never write concurrency handling code manually.

**C. Security Circuit Breakers (from `safety_and_constraints`)**
Generate a middleware wrapper around the DB executor.

- `compiled/security/sql_policy.py` contains an exact `if "DROP" in sql or "DELETE" in sql: raise Violation`.
- Benefit: Security policies become declarative and auditable.

---

### 3. The "Cognitive Compiler": What to Generate via Code Agent (100% LLM)

For the **Actions** (the internal logic of the Behaviors), the YAML only gives a name and a signature. The compiler should generate **Stub Files** with `# BEGIN HUMAN_CODE` blocks. 

*Then*, you use a specialized **"Coding Agent"** (acting as a Junior Developer) to fill these stubs based on the YAML context.

- **How it works**: The Coding Agent reads `system-model.yaml`, sees `behavior: compile_sql` with `uses_llm: true` and `prompt_ref: agent/instructions.md`. It writes the LLM orchestration logic.
- **How to avoid overwrites**: The compiler is programmed to **never** overwrite code inside `# BEGIN HUMAN_CODE` blocks if the file already exists. If the YAML updates, the Coding Agent reads the diff and suggests merges.

**Example Workflow**:
1. Compiler creates `behaviors/repair_sql.py` with:
```python
def repair_sql(ctx, event):
    # BEGIN HUMAN_CODE (DO NOT DELETE)
    # TODO: Implement regex or LLM fallback logic
    # END HUMAN_CODE
```
2. The Coding Agent reads the YAML (which specifies `max_sql_repairs: 2` and `database_type: postgres`) and writes the `psycopg2` error-parsing logic inside the block.

---

### 4. The Ideal Development Workflow (The "Golden Path")

To build your DB/KB hybrid agent system, establish this Git-based lifecycle:

1.  **Architect Update**: You (or the TechLead) edit `system-model.v99.yaml`.
2.  **Compile Phase**: Run `python compile_agent.py --spec system-model.v99.yaml`.
    - It regenerates `generated/models/`, `generated/event_bus.py`, and `generated/security.py`.
    - It **preserves** the existing `behaviors/` folder (user logic) and only updates stub signatures if they changed.
3.  **Generation Phase (Optional but powerful)**: If stubs are empty, run `codegen-agent --spec system-model.v99.yaml --behavior compile_sql`.
    - The Coding Agent uses the YAML's `prompt_ref` and `created_objects` to write the exact LLM prompt injection logic.
4.  **Runtime Phase**: The `activegraph_runtime.py` bootstrapper loads `generated/event_bus.py` and dynamically imports all existing `behaviors/*.py` modules. The system runs.

---

### 5. ActiveGraph Integration: Auto-Synthesizing the Adaptation Loop

Your `system-model.yaml` defines `repair_sql` and `max_repairs`. The compiler can leverage this to auto-wire ActiveGraph's strongest feature: **The Causal Chain**.

- **Compile the Fallback Graph**: The compiler reads `on: query.failed` and generates the code that emits a **new** `patch.applied` event when the repair succeeds.
- **Compile the Adaptation Trigger**: The compiler writes a monitoring behavior that checks the `pain_score` accumulated on the `Session` object. If the YAML defines `adaptation_threshold: 0.8`, it auto-injects a hook that asks the `Coding Agent` to rewrite the `instructions.md` file.

---

### 6. Crucial Warning: The "Dependency Hell" Trap

If you let the Coding Agent generate *all* the code (including imports for vector DBs or SQL drivers), it will often pick conflicting library versions.

**Solution**: 
- The **Compiler** generates a standard `requirements.txt` / `pyproject.toml` *based on the YAML's `runtimes` definitions* (e.g., if `execution_engine: duckdb`, it pins `duckdb>=0.9.0`).
- The **Coding Agent** is strictly forbidden from editing dependency files. It only writes the logic inside the stubs.

---

### 7. Summary: Your Recommended "TechLead" Strategy

**Do not** try to fully compile the agent. **Do not** let the LLM generate the entire codebase from scratch.

Instead, implement the **"Scaffold-Then-Synthesize"** dual-engine:

1.  **The Compiler (Deterministic)**: Takes `system-model.yaml` → Generates **all structural code** (Models, Event Bus, Security, SQL executors with timeouts). This ensures zero syntax errors, perfect type safety, and follows the Open-Closed Principle (you can change the architecture without touching the logic).
2.  **The Code Agent (Stochastic)**: Takes `system-model.yaml` + empty stubs → Writes **imperative logic** (Prompt engineering, SQL repair heuristics, embedding calls) inside sandboxed stub files.

This way, your `system-model.yaml` becomes the **single source of truth for the Software Architecture**, and the ActiveGraph runtime acts as the **glue** that binds the compiled framework with the generated business logic. This is the exact recipe for building a truly maintainable, self-evolving Agentic System.