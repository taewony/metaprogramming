# Workspace (live task state)

## Current task`r`nUpdated text-to-SQL REPL help to document global pack commands and ActiveGraph mode switching.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/agent/system-model.hospital.v04.yaml
- activegraph/text-to-sql-agent/agent/system-model.techshop.v04.yaml
- activegraph/text-to-sql-agent/src/cli/schema_context.py
- activegraph/text-to-sql-agent/src/cli/pack_config.py
- activegraph/text-to-sql-agent/src/cli/main.py
- activegraph/text-to-sql-agent/src/cli/hospital_logic.py
- activegraph/okf-wiki/hospital-medical/tables/*.md
- activegraph/okf-wiki/techshop-commerce/tables/*.md
- activegraph/okf-wiki/techshop-commerce/skills/TechShop-DB-SKILL.md
- activegraph/text-to-sql-agent/agent.py`r`n- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- DB schema source of truth should live in OKF table documents, not embedded in Python planner code.
- The system-model should declare `schema_projection`: which OKF table docs to load, how to validate them against SQLite, and what graph object/relation types represent the projected context.
- Pack configuration should bind DB files, OKF schema roots, and executable system-model files independently so hospital and TechShop can use the same runtime boundary.

## Checkpoints`r`n- [x] Added REPL shell help preamble before delegated Click help.`r`n- [x] Documented global pack commands: list, current, inspect, schema, validate, use.`r`n- [x] Documented mode switching with `mode activegraph` and `mode text-to-sql`.`r`n- [x] Forced UTF-8 stdout/stderr in `agent.py` so captured REPL help is stable on Windows.`r`n- [x] Added TDD coverage for REPL help output.`r`n- [x] Verified full activegraph text-to-SQL pytest file: `31 passed`.`r`n- [x] Added `schema` capability/config to packs and set OKF schema roots for hospital-db, techshop-db, and hybrid packs.
- [x] Added `system-model.hospital.v04.yaml` with `hospital_okf_schema_projection` over 8 hospital tables.
- [x] Added `system-model.techshop.v04.yaml` with `techshop_okf_schema_projection` over customers, products, orders, and order_items.
- [x] Added OKF `tables/*.md` schema docs generated from activegraph/data/hospital.db and activegraph/data/techshop.db.
- [x] Preserved TechShop logical joins in OKF foreign_keys even though the SQLite fixture has no declared FK constraints.
- [x] Added `activegraph.cli.schema_context` to load OKF table docs, compare with SQLite, and produce graph projection objects/relations.
- [x] Added `agent.py pack schema [pack_id] [--json]`.
- [x] Extended `pack validate` to verify schema OKF root, schema format, system-model projection loading, and SQLite alignment.
- [x] Updated TechShop OKF skill copy to point at OKF table docs and removed a stale nonexistent `category` example.
- [x] Added TDD coverage for hospital/TechShop schema projection and CLI output.
- [x] Verified `pack validate --all` passes.
- [x] Verified full activegraph text-to-SQL pytest file: `30 passed`.
- [x] Verified TechShop smoke with escalated SQLite event-store write: `VIP 고객은 총 5명입니다.`

## Next step
Use projected `SchemaContext` as planner input: either generate rule catalogs from schema/model declarations or assemble Full Context for an LLM planner while recording the schema projection object in each run graph/event log.

---

# Workspace (live task state)

## Current task
Pre-v05 world-model snapshot and original ActiveGraph event-log capability review.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- Original ActiveGraph recovery/debug loop is event-log-first: inspect -> replay -> fork -> modify behavior/config -> diff -> export-trace.
- There is no standalone `repair` command in the copied runtime; repair is an operator workflow built from replay/fork/diff plus code or pack changes.
- Before v05 generic interpretation, the text-to-SQL agent needs a stable snapshot of the selected world model: pack bindings, system-model identity, schema projection, behavior registry, and event-store run inventory.

## Checkpoints
- [x] Reviewed original ActiveGraph CLI commands for `inspect`, `replay`, `fork`, `diff`, and `export-trace`.
- [x] Added `activegraph_event_log_capabilities()` documenting inspect/replay/fork/diff/export-trace in the text-to-SQL snapshot payload.
- [x] Added `world_model_snapshot()` to capture selected pack, system-model metadata, DB path, OKF schema projection graph, behavior specs, event-store runs, and repair loop.
- [x] Added `text-to-sql snapshot [--json]` CLI command.
- [x] Updated REPL help to mention `snapshot --json`.
- [x] Added TDD coverage for TechShop world-model snapshot.
- [x] Verified focused snapshot test.
- [x] Verified full activegraph text-to-SQL pytest file: `32 passed`.
- [x] Smoke-tested original `inspect`, `replay`, and `export-trace` against TechShop event log run `01KXHC7JB436ED29P5FD4AA683`.

## Next step
Start v05 generic system-model interpreter: use the world-model snapshot as the input contract, then move more behavior registration and planner configuration out of Python and into system-model declarations.

```
• Checked original ActiveGraph behavior and added a world-model snapshot command for our agent.

  Original ActiveGraph supports this operator loop:

  - inspect: see run state, event history, behaviors, memo/search metadata.
  - replay: rebuild graph from stored events without firing behaviors.
  - fork: branch from a previous run/event and test a repair/adaptation path.
  - diff: compare two run graphs structurally.
  - export-trace: export event history for analysis/adaptation.

  There is no separate first-class repair command in the source. The repair flow is effectively: inspect failure ->
  replay -> fork -> adjust behavior/config -> diff -> export trace.

  I added:

  python activegraph/text-to-sql-agent/agent.py --pack techshop-db text-to-sql snapshot --json

  This prints the current “world model” snapshot: selected pack, loaded system-model, DB/OKF schema projection,
  projected graph objects/relations, behavior specs, event-store runs, and the original ActiveGraph event-log
  capabilities.

  REPL help also now shows snapshot --json.

  Verification:

  python -m pytest tests/test_activegraph_text_to_sql_tdd.py -q --basetemp activegraph/text-to-sql-agent/.tests/pytest-
  activegraph -p no:cacheprovider

  Result: 32 passed.

  So v05 can start from a cleaner contract: the runtime can first materialize a snapshot of its projected world model,
  then behavior execution and later adaptation/repair can compare “expected model vs observed event-log outcome.”
```