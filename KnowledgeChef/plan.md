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

