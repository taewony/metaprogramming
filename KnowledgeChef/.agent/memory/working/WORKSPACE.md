# Workspace (live task state)

> Replace this template on your first real task. The dream cycle auto-archives
> this file after 2 days of inactivity — don't keep long-lived notes here.

## Current task
Build a behavior-backed CLI for hospital Text-to-SQL by referencing `activegraph/text-to-sql-agent/src`, then verify the user can ask `의사는 모두 몇명이야?` from CLI.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/scripts/hospital_activegraph_behaviors.py
- activegraph/text-to-sql-agent/scripts/hospital_tdd_driver.py
- activegraph/text-to-sql-agent/evals/hospital_cases.jsonl
- activegraph/text-to-sql-agent/.tests/runs/

## Active hypotheses
- Near-term behavior execution should use the local ActiveGraph `Graph`, `Runtime`, `Event`, and explicit `Behavior` objects from `activegraph/text-to-sql-agent/src`.
- Deterministic behavior rules are enough for the first TDD slice and keep LLM dependency out of the core loop.
- CLI output should expose SQL, rows, answer, run id, and trace/graph artifact paths.

## Checkpoints
- [x] Ran recall for behavior-backed Text-to-SQL CLI work.
- [x] Read local ActiveGraph runtime, graph, behavior, view, and CLI source.
- [x] Added failing q002 eval case for `의사는 모두 몇명이야?`.
- [x] Confirmed pre-implementation eval failed on q002.
- [x] Added `hospital_activegraph_behaviors.py` with parse_intent, compile_sql, execute_sql, and synthesize_answer behaviors.
- [x] Wired `hospital_tdd_driver.py` to default to behavior planner while preserving deterministic/LLM modes.
- [x] Verified requested CLI prompt returns `의사는 모두 5명입니다.`.
- [x] Verified eval suite passes 2/2.
- [x] Added local `activegraph` package shim so `PYTHONPATH=src python -m activegraph` uses copied runtime source.
- [x] Registered `text-to-sql` group in the original ActiveGraph Click CLI.
- [x] Verified original CLI ask/eval/REPL commands.`r`n- [x] Added default SQLite event store for Text-to-SQL runs at `activegraph/data/text_to_sql_events.sqlite`.`r`n- [x] Added `text-to-sql inspect-run` for latest or selected run inspection.`r`n- [x] Verified generic `activegraph inspect`, `replay`, and `export-trace` against the Text-to-SQL event store.`r`n- [x] Verified failed prompt inspection shows `parse_intent`/`deterministic_plan()` as the improvement target.

## Next step
Add event-log analysis that produces behavior adaptation candidates from `.tests/runs/<run_id>/trace.jsonl`.


