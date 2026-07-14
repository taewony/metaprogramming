# Workspace (live task state)

## Current task
Implemented v02 RuleCatalog and verified table-driven/system-model-driven Text-to-SQL behavior.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/system-model.v02.yaml
- activegraph/text-to-sql-agent/src/cli/hospital_logic.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- v01 is complete and remains behaviorally stable.
- v02 now preserves the v01 ActiveGraph behavior/event shape while moving prompt matching, SQL text, params, and answer templates into `system-model.v02.yaml`.
- v02 remains deterministic: no LLM, no llama-index, no RAG/vector dependency.

## Checkpoints
- [x] Created `activegraph/text-to-sql-agent/agent/system-model.v02.yaml`.
- [x] Implemented `RuleCatalog`, `Rule`, catalog validation, YAML loader, deterministic matching, and catalog-backed `deterministic_plan()` in `src/cli/hospital_logic.py`.
- [x] Added RuleCatalog TDD coverage to `tests/test_activegraph_text_to_sql_tdd.py`.
- [x] Corrected v02 catalog entries to match current hospital fixture/evals: `홍길동`, `예정됨`, and joined availability SQL.
- [x] Verified focused RuleCatalog tests: passed.
- [x] Verified full pytest file: `16 passed`.
- [x] Verified CLI JSONL eval: `8 passed, 0 failed`.
- [x] Verified `agent.py text-to-sql ask "의사는 모두 몇명이야?"` returns `의사는 모두 5명입니다.` through the default event store.
- [x] Verified `inspect 0 --json` shows `intent.data.rule_id = doctor_count_q002_q003_q004`.

## Next step
Decide whether v02 should be closed now or extended with a small q009 that proves new coverage can be added by YAML/eval only, without changing Python runtime logic.

---

# Workspace (live task state)

## Current task
Completed v02.2 q010 YAML/eval-only extension for doctor-list Text-to-SQL behavior.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/system-model.v02.yaml
- activegraph/text-to-sql-agent/evals/hospital_cases.jsonl
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- v02.2 proves list-style table output can be added with system-model YAML plus eval/test updates, without changing Python runtime logic.
- The next meaningful generalization is named capture/entity binding so q001 and q009 can collapse into one parameterized rule.

## Checkpoints
- [x] Added q009 eval: `이수진 의사의 전공은?` -> `소아과`.
- [x] Added `doctor_specialty_by_name_q009` to `system-model.v02.yaml` with no runtime code changes.
- [x] Added q010 eval: `의사 명단` -> doctor names ordered by `doctor_id`.
- [x] Added `doctor_name_list_q010` to `system-model.v02.yaml` with no runtime code changes.
- [x] Updated v02 metadata to expect q001-q010 and `expected_min_passed: 10`.
- [x] Verified direct q010 driver ask: `의사 명단은 김지훈, 이수진, 박준석, 최미영, 정태호입니다.`.
- [x] Verified JSONL eval: `10 passed, 0 failed`.
- [x] Verified pytest with elevated filesystem permissions: `18 passed`.
- [x] Verified `agent.py text-to-sql ask "의사 명단"` through default event store.
- [x] Verified `inspect 0 --json` shows `intent.data.rule_id = doctor_name_list_q010`.

## Next step
Start v03 capture-based entity extraction/parameter binding so repeated literal doctor-specialty rules can become one reusable declarative rule.
