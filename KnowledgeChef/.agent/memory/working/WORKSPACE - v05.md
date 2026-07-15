# Workspace (live task state)

## Current task
v05 generic system-model interpreter for ActiveGraph text-to-SQL packs.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/agent/system-model.hospital.v05.yaml
- activegraph/text-to-sql-agent/agent/system-model.techshop.v05.yaml
- activegraph/text-to-sql-agent/agent/system-model.v99.yaml
- activegraph/text-to-sql-agent/src/cli/hospital_logic.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- v05 should be a conservative interpreter step, not a full compiler: keep stable Python behavior stubs, but move runtime contracts and environment validation declarations into system-model YAML.
- YAML keys such as `on` must be quoted because PyYAML's YAML 1.1 parsing can coerce unquoted `on` to boolean `True`.
- World-model snapshot is the right operator surface for seeing pack-selected model identity, schema projection, behavior contracts, and entity validator declarations before asking questions.

## Checkpoints
- [x] Added `system-model.hospital.v05.yaml` and `system-model.techshop.v05.yaml` from v04 pack models.
- [x] Switched `packs.yaml` to v05 system models for hospital, techshop, and DB+KB packs.
- [x] Extended RuleCatalog loading to accept `system-model.v05`.
- [x] Added `entity_validation_model` parsing with `sqlite_exists` validators.
- [x] Added behavior runtime contract parsing from `behavior_model.behaviors[].runtime`.
- [x] Updated behavior factory to use YAML-declared `on` and `creates` values.
- [x] Updated hospital captured doctor validation to use the v05 system-model SQLite existence adapter.
- [x] Extended world-model snapshot with behavior contract and entity validation metadata.
- [x] Updated roadmap in `system-model.v99.yaml` to mark v05 completed.
- [x] Added TDD coverage for v05 behavior contracts, v05 entity validation source, and v05 snapshot metadata.
- [x] Verified focused v05 pytest subset: `6 passed, 28 deselected`.
- [x] Verified full activegraph text-to-SQL pytest file: `34 passed`.
- [x] Smoke-tested `pack validate hospital-db --json`.
- [x] Smoke-tested `--pack hospital-db text-to-sql snapshot --json`.
- [x] Smoke-tested `--pack hospital-db text-to-sql ask "의사는 모두 몇명이야?" --event-store activegraph/data/v05_smoke_events.sqlite --json` with answer `의사는 모두 5명입니다.`.

## Next step
Start v06 Full Context assembly: define a concrete `FullContext` object assembled from system prompt, selected system-model slice, schema projection, graph/event state, user prompt, and optional KB snippets, with deterministic tests before LLM adapters.

---

# Workspace (live task state)

## Current task
TechShop event-log repair for `VIP는 누구?` unsupported prompt.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/agent/system-model.hospital.v05.yaml
- activegraph/text-to-sql-agent/agent/system-model.techshop.v05.yaml
- activegraph/text-to-sql-agent/agent/system-model.v99.yaml
- activegraph/text-to-sql-agent/src/cli/hospital_logic.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- v05 should be a conservative interpreter step, not a full compiler: keep stable Python behavior stubs, but move runtime contracts and environment validation declarations into system-model YAML.
- YAML keys such as `on` must be quoted because PyYAML's YAML 1.1 parsing can coerce unquoted `on` to boolean `True`.
- World-model snapshot is the right operator surface for seeing pack-selected model identity, schema projection, behavior contracts, and entity validator declarations before asking questions.

## Checkpoints
- [x] Inspected latest TechShop event log after user reproduced `VIP는 누구?`.
- [x] Found failure at `parse_intent`: `UnsupportedPromptError` before graph objects were created.
- [x] Confirmed DB truth: VIP customers are 정민호, 오세훈, 강태영, 문창호, 황미소.
- [x] Added `vip_customer_list` rule to `system-model.techshop.v05.yaml`.
- [x] Added regression coverage for `VIP는 누구?`.
- [x] Re-ran CLI ask; successful run `01KXHF630AXRX53MPPVVYC3ZGN` produced 5 graph objects, 4 relations, no failures.
- [x] Verified TechShop pack validation: ok, 4 executable rules.
- [x] Verified full activegraph text-to-SQL pytest file: `35 passed`.
- [x] Added `system-model.hospital.v05.yaml` and `system-model.techshop.v05.yaml` from v04 pack models.
- [x] Switched `packs.yaml` to v05 system models for hospital, techshop, and DB+KB packs.
- [x] Extended RuleCatalog loading to accept `system-model.v05`.
- [x] Added `entity_validation_model` parsing with `sqlite_exists` validators.
- [x] Added behavior runtime contract parsing from `behavior_model.behaviors[].runtime`.
- [x] Updated behavior factory to use YAML-declared `on` and `creates` values.
- [x] Updated hospital captured doctor validation to use the v05 system-model SQLite existence adapter.
- [x] Extended world-model snapshot with behavior contract and entity validation metadata.
- [x] Updated roadmap in `system-model.v99.yaml` to mark v05 completed.
- [x] Added TDD coverage for v05 behavior contracts, v05 entity validation source, and v05 snapshot metadata.
- [x] Verified focused v05 pytest subset: `6 passed, 28 deselected`.
- [x] Verified full activegraph text-to-SQL pytest file: `34 passed`.
- [x] Smoke-tested `pack validate hospital-db --json`.
- [x] Smoke-tested `--pack hospital-db text-to-sql snapshot --json`.
- [x] Smoke-tested `--pack hospital-db text-to-sql ask "의사는 모두 몇명이야?" --event-store activegraph/data/v05_smoke_events.sqlite --json` with answer `의사는 모두 5명입니다.`.

## Next step
Start v06 Full Context assembly: define a concrete `FullContext` object assembled from system prompt, selected system-model slice, schema projection, graph/event state, user prompt, and optional KB snippets, with deterministic tests before LLM adapters.

---

# Workspace (live task state)

## Current task
TechShop shorthand VIP count support for `VIP는 몇명`.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/agent/system-model.hospital.v05.yaml
- activegraph/text-to-sql-agent/agent/system-model.techshop.v05.yaml
- activegraph/text-to-sql-agent/agent/system-model.v99.yaml
- activegraph/text-to-sql-agent/src/cli/hospital_logic.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- v05 should be a conservative interpreter step, not a full compiler: keep stable Python behavior stubs, but move runtime contracts and environment validation declarations into system-model YAML.
- YAML keys such as `on` must be quoted because PyYAML's YAML 1.1 parsing can coerce unquoted `on` to boolean `True`.
- World-model snapshot is the right operator surface for seeing pack-selected model identity, schema projection, behavior contracts, and entity validator declarations before asking questions.

## Checkpoints
- [x] Confirmed existing `vip_customer_count` rule required both `vip` and `고객`, so shorthand `VIP는 몇명` could miss.
- [x] Relaxed `vip_customer_count` in `system-model.techshop.v05.yaml` to require `vip` plus count words.
- [x] Added regression test for `VIP는 몇명`.
- [x] Ran focused TechShop VIP tests: `2 passed`.
- [x] Ran CLI ask `VIP는 몇명`; answer `VIP 고객은 총 5명입니다.`.
- [x] Inspected latest event-log run `01KXHFDX9WCXH9RTDAAZ5F0YBQ`; graph has intent rule `vip_customer_count`, SQL result, answer, and no failures.
- [x] Verified `pack validate techshop-db`: ok.
- [x] Verified full activegraph text-to-SQL pytest file: `36 passed`.
- [x] Inspected latest TechShop event log after user reproduced `VIP는 누구?`.
- [x] Found failure at `parse_intent`: `UnsupportedPromptError` before graph objects were created.
- [x] Confirmed DB truth: VIP customers are 정민호, 오세훈, 강태영, 문창호, 황미소.
- [x] Added `vip_customer_list` rule to `system-model.techshop.v05.yaml`.
- [x] Added regression coverage for `VIP는 누구?`.
- [x] Re-ran CLI ask; successful run `01KXHF630AXRX53MPPVVYC3ZGN` produced 5 graph objects, 4 relations, no failures.
- [x] Verified TechShop pack validation: ok, 4 executable rules.
- [x] Verified full activegraph text-to-SQL pytest file: `35 passed`.
- [x] Added `system-model.hospital.v05.yaml` and `system-model.techshop.v05.yaml` from v04 pack models.
- [x] Switched `packs.yaml` to v05 system models for hospital, techshop, and DB+KB packs.
- [x] Extended RuleCatalog loading to accept `system-model.v05`.
- [x] Added `entity_validation_model` parsing with `sqlite_exists` validators.
- [x] Added behavior runtime contract parsing from `behavior_model.behaviors[].runtime`.
- [x] Updated behavior factory to use YAML-declared `on` and `creates` values.
- [x] Updated hospital captured doctor validation to use the v05 system-model SQLite existence adapter.
- [x] Extended world-model snapshot with behavior contract and entity validation metadata.
- [x] Updated roadmap in `system-model.v99.yaml` to mark v05 completed.
- [x] Added TDD coverage for v05 behavior contracts, v05 entity validation source, and v05 snapshot metadata.
- [x] Verified focused v05 pytest subset: `6 passed, 28 deselected`.
- [x] Verified full activegraph text-to-SQL pytest file: `34 passed`.
- [x] Smoke-tested `pack validate hospital-db --json`.
- [x] Smoke-tested `--pack hospital-db text-to-sql snapshot --json`.
- [x] Smoke-tested `--pack hospital-db text-to-sql ask "의사는 모두 몇명이야?" --event-store activegraph/data/v05_smoke_events.sqlite --json` with answer `의사는 모두 5명입니다.`.

## Next step
Start v06 Full Context assembly: define a concrete `FullContext` object assembled from system prompt, selected system-model slice, schema projection, graph/event state, user prompt, and optional KB snippets, with deterministic tests before LLM adapters.