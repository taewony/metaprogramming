# Workspace (live task state)

## Current task
Implemented the initial v04 pack/environment boundary for the Text-to-SQL agent.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent.py
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/agent/system-model.v99.yaml
- activegraph/text-to-sql-agent/src/cli/main.py
- activegraph/text-to-sql-agent/src/cli/pack_config.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- activegraph/okf-wiki/hospital-medical/index.md
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- A single central pack registry is enough for v04 and keeps runtime/config separation easy to inspect.
- The generic runtime should accept DB/event-store/KB paths from a selected pack, while explicit CLI options still override pack values.
- `pack use` can update `default_pack` inside `agent/packs.yaml` rather than introducing a second state file.

## Checkpoints
- [x] Added `activegraph/text-to-sql-agent/agent/packs.yaml` with four packs: hospital-db, techshop-db, hospital-db-medical-kb, techshop-db-commerce-kb.
- [x] Added `activegraph/text-to-sql-agent/src/cli/pack_config.py` for loading, validating, resolving, inspecting, and setting default packs.
- [x] Added `pack list`, `pack current`, `pack inspect`, and `pack use` commands to the local CLI while preserving `pack new` and `pack list --installed` for original entry-point packs.
- [x] Added root `--pack <id>` and `text-to-sql --pack <id>` selection.
- [x] Updated text-to-sql ask/eval/inspect/repl so selected packs supply DB and event-store paths unless explicit CLI paths are passed.
- [x] Added REPL routing so `pack ...` commands work from the default text-to-sql REPL mode.
- [x] Added minimal hospital medical OKF bundle index at `activegraph/okf-wiki/hospital-medical/index.md`; techshop OKF bundle already existed.
- [x] Updated v99 roadmap v04 status to active and noted the initial implementation.
- [x] Added tests for pack registry path resolution and `agent.py pack list` output.
- [x] Verified CLI pack list/current/inspect.
- [x] Verified default text-to-sql ask still uses hospital-db.
- [x] Verified root `--pack hospital-db-medical-kb` uses `activegraph/data/hospital_medical_kb_events.sqlite` when run outside the restricted SQLite-create sandbox.
- [x] Verified YAML validation for `packs.yaml` and `system-model.v99.yaml`.
- [x] Verified pytest: `24 passed`.

## Next step
Generalize pack-selected system-model loading. Current pack selection controls DB, event store, and KB locations; the deterministic planner still loads the default v03 system model from `hospital_logic.py`.

---

# Workspace (live task state)

## Current task
Implemented pack-selected executable `system_model` loading for the Text-to-SQL runtime.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/agent/system-model.v99.yaml
- activegraph/text-to-sql-agent/src/cli/main.py
- activegraph/text-to-sql-agent/src/cli/pack_config.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- In v04, `pack.system_model` should mean the executable RuleCatalog system model used by the current deterministic runtime.
- North-star/non-executable models such as v99 should be tracked separately as `reference_model` until the generic interpreter can execute them.
- `run_text_to_sql`, `run_eval`, and `inspect` should report the system model path used so event/debug output can explain which rules were loaded.

## Checkpoints
- [x] Added `reference_model` to `AgentPack` and `pack_to_dict`.
- [x] Updated hybrid packs to use executable `system-model.v03.yaml` and reference `system-model.v99.yaml`.
- [x] Updated `pack inspect` to display `reference_model` when present.
- [x] Updated `text_to_sql.py` so selected pack system model is passed into `make_hospital_behaviors`.
- [x] `make_hospital_behaviors` now loads the RuleCatalog from the passed `system_model_file` and uses that catalog for deterministic planning.
- [x] `run_text_to_sql`, `run_eval`, and `inspect_text_to_sql_run` now accept/report `system_model_file`.
- [x] CLI `ask/eval/inspect/repl` pass the selected pack's executable system model through to runtime helpers.
- [x] Added tests for hybrid pack executable/reference model metadata and CLI pack-selected system-model output.
- [x] Verified focused pack tests: `3 passed`.
- [x] Verified full pytest: `25 passed`.
- [x] Verified CLI JSON smoke with `--pack hospital-db-medical-kb` reports `system-model.v03.yaml` and writes to the hybrid pack event store.
- [x] Updated v99 roadmap v04 deliverable to include pack-selected executable `system_model` loading.

## Next step
Use pack-selected system models to introduce a real techshop RuleCatalog, or add an explicit runtime validation command that reports whether a pack is executable by the current deterministic interpreter.

---

# Workspace (live task state)

## Current task
Completed v04 pack environment boundary with `pack validate`.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/agent/system-model.v99.yaml
- activegraph/text-to-sql-agent/src/cli/main.py
- activegraph/text-to-sql-agent/src/cli/pack_config.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- In v04, `pack.system_model` means the executable RuleCatalog system model used by the current deterministic runtime.
- North-star/non-executable models such as v99 should be tracked separately as `reference_model` until the generic interpreter can execute them.
- Pack validation should prove that runtime configuration is locally executable before deeper semantic/domain validation is introduced.

## Checkpoints
- [x] Added `reference_model` to `AgentPack` and `pack_to_dict`.
- [x] Updated hybrid packs to use executable `system-model.v03.yaml` and reference `system-model.v99.yaml`.
- [x] Updated `pack inspect` to display `reference_model` when present.
- [x] Updated `text_to_sql.py` so selected pack system model is passed into `make_hospital_behaviors`.
- [x] `make_hospital_behaviors` now loads the RuleCatalog from the passed `system_model_file` and uses that catalog for deterministic planning.
- [x] `run_text_to_sql`, `run_eval`, and `inspect_text_to_sql_run` now accept/report `system_model_file`.
- [x] CLI `ask/eval/inspect/repl` pass the selected pack's executable system model through to runtime helpers.
- [x] Added `pack validate` for single-pack and `--all` validation.
- [x] Validation checks system model path, executable RuleCatalog loading, DB readability, event-store parent writability, reference model path, OKF root/index, OKF format, and approval policy.
- [x] Added TDD coverage for validation helper and CLI JSON output.
- [x] Marked v04 completed in `system-model.v99.yaml`.
- [x] Verified CLI validation for `hospital-db-medical-kb` and all packs.
- [x] Verified full activegraph text-to-SQL pytest file: `27 passed`.

## Next step
Use the pack boundary to introduce a real techshop RuleCatalog/system model, or begin v05 by reducing Python domain code through a generic system-model interpreter.

```
• Implemented pack validate and marked v04 complete.

  Changed:

  - Added pack validation helpers in activegraph/text-to-sql-agent/src/cli/pack_config.py:252
  - Added CLI command agent.py pack validate [pack_id] [--all] [--json] in activegraph/text-to-sql-agent/src/cli/
    main.py:274

  - Added TDD coverage for all-pack validation and CLI JSON output in tests/test_activegraph_text_to_sql_tdd.py:93
  - Updated v04 roadmap status to completed in activegraph/text-to-sql-agent/agent/system-model.v99.yaml:726

  Validation now checks:
  system_model, executable RuleCatalog load, DB readability, event-store parent writability, reference_model, OKF root/
  index, OKF format, and approval policy.

  Verified:

  python activegraph/text-to-sql-agent/agent.py pack validate hospital-db-medical-kb --json
  python activegraph/text-to-sql-agent/agent.py pack validate --all
  python -m pytest tests/test_activegraph_text_to_sql_tdd.py -q --basetemp activegraph/text-to-sql-agent/.tests/pytest-
  activegraph -p no:cacheprovider

  Result: 27 passed.
```  

```
• Short answer: 현재 구현에서는 techshop-db agent가 OKF schema를 읽지 않습니다.
  지금은 pack이 DB_FILE과 system_model만 runtime에 넘기고, system-model.v03.yaml 안의 RuleCatalog SQL rule을 실행합니다.
  그리고 그 system_model도 아직 hospital 전용입니다.

  Current State
  packs.yaml 기준:

  - techshop-db
      - DB_FILE: ../../data/techshop.db
      - system_model: system-model.v03.yaml
      - kb: false
      - OKF path 없음

  - techshop-db-commerce-kb
      - DB_FILE: ../../data/techshop.db
      - OKF_BUNDLE_ROOT: ../../okf-wiki/techshop-commerce
      - kb: true

  즉, techshop schema는 디스크에 OKF bundle로 존재하지만, runtime planner는 아직 그걸 schema source로 쓰지 않습니다.

  내 생각
  system-model 파일에 DB schema 전체를 넣는 건 좋지 않습니다. 중복되고 금방 stale 됩니다.

  좋은 분리는 이겁니다:

  - pack YAML: 어떤 DB, 어떤 OKF bundle, 어떤 system-model을 쓸지 연결
  - OKF bundle: table/column/metric/join 같은 domain schema와 semantic knowledge의 source of truth
  - system-model: agent behavior contract. 즉 “schema를 어디서 읽고, 어떤 planner/behavior가 그것을 어떻게 사용할지”를
    선언

  예를 들면 system-model에는 이런 식이면 됩니다:

  schema_context:
    sources:
      - id: techshop_okf_schema
        type: okf_bundle
        root_env: OKF_BUNDLE_ROOT
        include:
          - tables/index.md
          - tables/*.md
          - references/metrics/*.md
          - references/joins/*.md

    db_validation:
      type: sqlite_introspection
      db_env: DB_FILE
      compare_with_okf: true

    exposed_to_planner:
      tables: true
      columns: true
      joins: true
      metrics: true

  그리고 pack에는 kb와 별도로 schema capability를 두는 게 맞습니다:

  techshop-db:
    runtime: text-to-sql
    system_model: system-model.techshop.v01.yaml
    env:
      DB_FILE: ../../data/techshop.db
      EVENT_STORE: ../../data/techshop_text_to_sql_events.sqlite
      OKF_BUNDLE_ROOT: ../../okf-wiki/techshop-commerce
    capabilities:
      db: true
      schema: true
      kb: false

  이렇게 하면 techshop-db는 “답변 RAG용 KB”는 안 쓰더라도, “DB schema source”로 OKF를 사용할 수 있습니다.

  중요한 구분
  system-model.schema_version은 YAML 포맷 버전이지 DB schema가 아닙니다.
  DB schema 자체는 OKF bundle에 두고, system-model은 그 schema를 runtime graph/context로 projection하는 규칙을 선언하는
  게 좋습니다.

  Next Step 제안
  v04를 끝냈으니 바로 다음은 pack schema inspect 또는 schema validate가 좋습니다.

  예상 동작:

  python activegraph/text-to-sql-agent/agent.py pack schema techshop-db

  출력:

  - selected pack
  - DB tables from SQLite introspection
  - OKF tables/metrics/joins loaded
  - mismatch warnings
  - generated SchemaContext

  그 다음 v05에서 planner가 이 SchemaContext를 Full Context에 넣고, RuleCatalog 또는 LLM planner가 techshop query를 만들
  게 하면 됩니다.
```

---

# Workspace (live task state)

## Current task
Implemented OKF-backed DB schema projection for hospital and TechShop packs.

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
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- DB schema source of truth should live in OKF table documents, not embedded in Python planner code.
- The system-model should declare `schema_projection`: which OKF table docs to load, how to validate them against SQLite, and what graph object/relation types represent the projected context.
- Pack configuration should bind DB files, OKF schema roots, and executable system-model files independently so hospital and TechShop can use the same runtime boundary.

## Checkpoints
- [x] Added `schema` capability/config to packs and set OKF schema roots for hospital-db, techshop-db, and hybrid packs.
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

```
• Implemented the OKF-backed schema projection slice.

  What changed:

  - Added schema-aware pack config in activegraph/text-to-sql-agent/agent/packs.yaml
      - hospital-db -> system-model.hospital.v04.yaml
      - techshop-db -> system-model.techshop.v04.yaml
      - both now have schema: { format: okf, root: ... }

  - Added v04 system models:
      - activegraph/text-to-sql-agent/agent/system-model.hospital.v04.yaml
      - activegraph/text-to-sql-agent/agent/system-model.techshop.v04.yaml

  - Added schema projection runtime:
      - activegraph/text-to-sql-agent/src/cli/schema_context.py

  - Added CLI:
      - python activegraph/text-to-sql-agent/agent.py pack schema techshop-db --json
      - python activegraph/text-to-sql-agent/agent.py pack schema hospital-db --json

  - Generated OKF table schema docs from the actual SQLite DBs:
      - activegraph/okf-wiki/hospital-medical/tables/index.md
      - activegraph/okf-wiki/techshop-commerce/tables/index.md

  - Checked and corrected activegraph/okf-wiki/techshop-commerce/skills/TechShop-DB-SKILL.md
      - It now points to OKF tables/*.md as schema source of truth.
      - Removed the stale category SQL example because products.category does not exist.

  Important behavior:

  - The DB schema itself now lives in OKF table docs.
  - The system-model declares schema_projection.include.tables.
  - Runtime loads only those declared table docs, validates them against SQLite, and projects graph-like objects/
    relations:
      - db.schema_context
      - db.table
      - db.column
      - schema.has_table
      - table.has_column
      - column.references

  Verified:

  python activegraph/text-to-sql-agent/agent.py pack validate --all
  python activegraph/text-to-sql-agent/agent.py pack schema techshop-db --json
  python -m pytest tests/test_activegraph_text_to_sql_tdd.py -q --basetemp activegraph/text-to-sql-agent/.tests/pytest-
  activegraph -p no:cacheprovider

  Result: 30 passed.

  Also smoke-tested TechShop:

  python activegraph/text-to-sql-agent/agent.py --pack techshop-db text-to-sql ask "VIP 고객 몇명이야?" --json

  Answer: VIP 고객은 총 5명입니다.
```