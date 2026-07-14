# Workspace (live task state)

## Current task
Added system-model load diagnostics for v03 RuleCatalog runtime and clarified named-capture behavior path.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/src/cli/hospital_logic.py
- activegraph/text-to-sql-agent/agent/system-model.v03.yaml

## Active hypotheses
- Named regex captures are used by the `parse_intent` behavior path: `parse_intent` calls `deterministic_plan()`, which calls the default `RuleCatalog` loaded from `system-model.v03.yaml`.
- Runtime load diagnostics should write to stderr so JSON stdout remains parseable for CLI/eval callers.

## Checkpoints
- [x] Added stderr print before loading a system model in `load_rule_catalog_from_system_model()`.
- [x] Added stderr print after loading with schema, catalog id, and rule count.
- [x] Verified direct catalog load prints `system-model.v03.yaml`, `hospital_text_to_sql_rules_v03`, and `rules=7`.
- [x] Verified driver ask still returns valid JSON for `이수진 의사의 전공은?`.
- [x] Verified full pytest: `20 passed`.
- [x] Verified `agent.py text-to-sql ask "이수진 의사의 전공은?"` prints load diagnostics and answers correctly.

## Next step
If the load prints are too noisy for JSON automation, add a CLI/env flag such as `ACTIVEGRAPH_SYSTEM_MODEL_TRACE=1` and default it off.

---

# Workspace (live task state)

## Current task
Completed v03.1 capture-based hospital lookup for the Text-to-SQL RuleCatalog runtime.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/system-model.v03.yaml
- activegraph/text-to-sql-agent/evals/hospital_cases.jsonl
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- v03.1 proves the named-capture mechanism is reusable across more than one intent family.
- q005 and q011 now share one generic doctor-hospital lookup rule.
- The next useful generalization is entity existence validation or broader captured field lookups.

## Checkpoints
- [x] Added q011 eval: `이수진 의사 병원?` -> `서울중앙병원`.
- [x] Added q011 test coverage and updated eval expected count to 11.
- [x] Replaced literal `doctor_hospital_by_name_q005` with `doctor_hospital_by_name_capture_q005_q011` in `system-model.v03.yaml`.
- [x] Kept v03 rule count at 7 while expanding eval coverage to q001-q011.
- [x] Verified direct planner binds `doctor_name = 이수진` for hospital lookup.
- [x] Verified JSONL eval: `11 passed, 0 failed`.
- [x] Verified pytest: `21 passed`.
- [x] Verified `agent.py text-to-sql ask "이수진 의사 병원?"` through default event store.
- [x] Verified `inspect 0 --json` shows `rule_id = doctor_hospital_by_name_capture_q005_q011` and `bindings.doctor_name = 이수진`.

## Next step
Choose between entity existence validation for captured names, broadening captured lookup fields, or pack/env separation for additional databases.

---

# Workspace (live task state)

## Current task
Completed v03.2 entity validation for captured doctor names in the Text-to-SQL RuleCatalog runtime.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/system-model.v03.yaml
- activegraph/text-to-sql-agent/evals/hospital_cases.jsonl
- activegraph/text-to-sql-agent/src/cli/hospital_logic.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- activegraph/text-to-sql-agent/scripts/hospital_activegraph_behaviors.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- Captured entity bindings should be validated against the current environment before SQL generation.
- Missing required entities should be represented as graph state, not as silent empty SQL results.
- The behavior path can answer validation failures directly while preserving replay/inspectability.

## Checkpoints
- [x] Added q012 eval: `없는의사 의사의 전공은?` -> missing doctor answer.
- [x] Added `capture_entities` metadata to `IntentPlan` and RuleCatalog planning output.
- [x] Added SQLite-backed `doctor.name` validation helpers in `hospital_logic.py`.
- [x] Updated both CLI and script behavior runtimes so `parse_intent` records `entity_validation:not_found`, emits `entity.validation_failed`, creates an answer, and skips `intent.created` / SQL generation.
- [x] Strengthened q012 test to assert graph artifact contains one `entity_validation` object with `status = not_found`.
- [x] Verified direct q012 driver ask: `ok: true`, `sql: null`, answer contains `없는의사` and `찾지 못했습니다`.
- [x] Verified JSONL eval: `12 passed, 0 failed`.
- [x] Verified pytest: `22 passed`.
- [x] Verified CLI ask through `agent.py text-to-sql ask` and SQLite event store.
- [x] Verified `agent.py text-to-sql inspect 0 --json --tail 5` shows `entity_validation#3` and no `sql_query` object.

## Next step
Generalize entity validation declarations beyond `doctor.name`, or introduce captured lookup fields so one rule family can answer more doctor attributes without Python changes.