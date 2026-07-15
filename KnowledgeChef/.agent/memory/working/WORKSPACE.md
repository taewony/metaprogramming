# Workspace (live task state)

## Current task
Optional Ollama answer-composer integration for ActiveGraph Text-to-SQL.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent.py
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/src/cli/full_context.py
- activegraph/text-to-sql-agent/src/cli/llm_answer.py
- activegraph/text-to-sql-agent/src/cli/pack_config.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- LLM interaction should be an optional answer-composer adapter, not a required planner/runtime dependency.
- SQL/result truth should remain deterministic and inspectable before any LLM wording is accepted.
- If Ollama is unavailable, the run should still succeed with the deterministic answer and record fallback events.

## Checkpoints
- [x] Added `activegraph.cli.llm_answer` with fake and Ollama/OpenAI-compatible answer composers.
- [x] Added pack-level `llm` config blocks in `agent/packs.yaml`, disabled by default.
- [x] Extended `AgentPack`/`pack_to_dict` to carry `llm` config.
- [x] Extended Full Context `llm_contract` with provider/model/mode/fallback from the selected pack.
- [x] Wired optional LLM composition into `synthesize_answer` after SQL execution.
- [x] Recorded `llm_invocation` graph object, `decision_rationale` on success, and `llm.invocation_requested` / `llm.response_received` / `llm.fallback_used` events.
- [x] Added `text-to-sql ask --llm --ollama-base-url --ollama-model --llm-timeout` CLI options.
- [x] Updated REPL help with `ask --llm` usage.
- [x] Added TDD coverage for fake composer and local fake Ollama endpoint.
- [x] Focused context/composer tests: `4 passed`.
- [x] Focused TechShop VIP/composer regressions: `5 passed`.
- [x] Deterministic CLI smoke still answers `VIP 고객 총매출액은 6486000원입니다.`.
- [x] `--llm` CLI smoke with no Ollama records failed `llm_invocation` and falls back to deterministic answer.
- [x] `text-to-sql inspect 0 --json` shows `llm_invocation#5`, `llm.fallback_used`, and answer source `deterministic` for fallback run `01KXHHKR6KF8CDQFHRK0KYZBZ0`.
- [x] `pack validate techshop-db --json`: ok.

## Known constraints
- Full pytest suite currently cannot complete in this environment because pytest temp-directory creation/cleanup hits Windows `PermissionError` on `tmp_path`/`basetemp`; focused tests that avoid `tmp_path` pass.
- Creating a brand-new SQLite event store file at `activegraph/data/ollama_fallback_smoke.sqlite` hit `sqlite3.OperationalError: disk I/O error`; existing TechShop event store remains writable.

## Next step
Run with a real local Ollama model:
`python activegraph/text-to-sql-agent/agent.py --pack techshop-db text-to-sql ask "VIP 고객 총매출액" --llm --json`

Expected if Ollama is available: `answer_source` becomes `llm`, `llm.status` becomes `completed`, and inspect shows `llm.response_received` plus `decision_rationale`.
## Latest checkpoint
- [x] Set all pack `llm` defaults to `base_url: http://localhost:11434/v1` and `model: qwen2.5:7b`.
- [x] Changed code fallback `DEFAULT_OLLAMA_MODEL` to `qwen2.5:7b` for packs that omit a model.
- [x] Added regression assertions for pack LLM defaults.
- [x] Fixed direct `TimeoutError` from `urllib.request.urlopen` so unavailable Ollama still triggers deterministic fallback instead of `behavior.failed`.
- [x] Focused tests: `7 passed, 35 deselected`.
- [x] `ask --llm --llm-timeout 0.1 --json` reports `llm.model=qwen2.5:7b`, `llm.status=failed`, `ok=true`, and deterministic fallback answer.
- [x] `pack validate techshop-db --json`: ok.
## Typo prompt checkpoint
- [x] Reproduced user failure: `VIP 고객 총 맥출액 --llm` failed in `parse_intent` before the answer-composer LLM path.
- [x] Root cause: `--llm` currently composes answers after deterministic intent/SQL/result; it does not yet repair unsupported prompts.
- [x] Added declarative TechShop matcher aliases `총맥출액`, `맥출액`, `맥출` to `vip_customer_revenue_total`.
- [x] Added regression test `test_v06_techshop_vip_revenue_accepts_common_sales_typo_with_llm_path`.
- [x] Focused tests: `4 passed, 39 deselected`.
- [x] CLI smoke: `ask "VIP 고객 총 맥출액" --llm --llm-timeout 0.1 --json` returns `ok=true`, SQL executes, LLM fallback is recorded cleanly.
- [x] `pack validate techshop-db --json`: ok.
## DB query/response finalization checkpoint
- [x] Updated `system-model.v99.yaml` roadmap so DB query/response hardening runs through v09-v11 before KB/RAG.
- [x] Added v07 `llm_answer_composition` as completed and v08 `prompt_robustness` as active to reflect current DB work.
- [x] Moved OKF KB ingestion to v12 and SQL/RAG parallelism to v13 with `deferred_until_db_query_response_complete` status.
- [x] Added `DB Query And Response Completion Gate` to `design-spec.md`.
- [x] Added `DB Query And Response Finalization Roadmap` to `plan.md`.
- [x] Verified `system-model.v99.yaml` parses with PyYAML.
## v08 prompt robustness checkpoint
- [x] Added `activegraph/text-to-sql-agent/evals/prompt_robustness_candidates.yaml` with `supported_now` and `deferred` prompt groups for `hospital-db` and `techshop-db`.
- [x] Expanded hospital deterministic matchers for doctor count/list, doctor specialty, doctor hospital, and available-slot prompt variants.
- [x] Expanded TechShop deterministic matchers for VIP revenue/list aliases and added `member_count` plus `item_count` rules.
- [x] Focused v08 tests: `3 passed, 43 deselected`.
- [x] Full Text-to-SQL TDD file: `46 passed`.
- [x] CLI smokes passed for `hospital-db` prompt `김지훈 전문분야는?` and `techshop-db` prompt `회원 수`.
- [x] `pack validate hospital-db --json`: ok.
- [x] `pack validate techshop-db --json`: ok.
## v09 adaptation loop checkpoint
- [x] Added `activegraph.cli.adaptation` with event-store run analysis, classification, proposal generation, and explicit proposal acceptance.
- [x] Added `text-to-sql adapt [run-selector]` to write `analysis.json`, proposal JSON, `adaptation_events.jsonl`, and `adaptation_graph.json` artifacts.
- [x] Added `text-to-sql adapt-accept <proposal-file>` to generate draft eval-case JSONL and system-model patch-hint artifacts without auto-editing canonical files.
- [x] Added v09 TDD coverage for unsupported prompt classification, proposal artifacts, acceptance artifacts, and CLI JSON output.
- [x] Updated `system-model.v99.yaml`, `plan.md`, and `design-spec.md` with v09 completed implementation notes.
- [x] Focused v09 tests: `3 passed, 46 deselected`.
- [x] Full Text-to-SQL TDD file: `49 passed`.
- [x] CLI smoke: `VIP 평균 주문 단가` failure run produced one unsupported-prompt adaptation proposal.
- [x] `pack validate hospital-db --json`: ok.
- [x] `pack validate techshop-db --json`: ok.
## v10 multi-turn and memory checkpoint
- [x] Added `activegraph.cli.session_memory` with local JSON session graph state, explicit memory boundaries, deterministic prompt resolution, and turn persistence.
- [x] Added `--session-id` / `--session-store-dir` support to `text-to-sql ask`, `context`, and `repl`.
- [x] `run_text_to_sql` now records original/resolved prompts, session graph objects, session resolution objects, and persisted turn state when a session is selected.
- [x] Full Context now includes `session_context` and `memory_boundaries` and plans against the resolved prompt.
- [x] Deterministic v10 coverage: hospital `그 의사...` resolves to the last `doctor.name`; TechShop `몇 명이야?` resolves to `VIP 몇 명이야?` after a VIP turn.
- [x] Focused v10 tests: `3 passed, 49 deselected`.
- [x] Full Text-to-SQL TDD file after v10 CLI wiring: `52 passed`.
- [x] CLI two-turn smokes passed for hospital doctor anaphora and TechShop VIP ellipsis.
- [x] `pack validate hospital-db --json`: ok.
- [x] `pack validate techshop-db --json`: ok.
## Active hypothesis - REPL session bug
- The `text-to-sql repl` Click command enables v10 session memory, but the top-level `agent.py` mode-aware REPL only prefixes `text-to-sql` and does not add `--session-id` to shortcut `ask`/`context` commands. Therefore multi-turn references in the top-level REPL run without session state and fall back to deterministic entity capture, interpreting `그` as a doctor name.
## v10 REPL session bugfix checkpoint
- [x] Reproduced top-level `agent.py` REPL failure: shortcut `ask` commands did not pass `--session-id`, so `그 의사...` was parsed as doctor name `그` instead of resolving from session memory.
- [x] Fixed `agent.py` REPL to inject default session id `agent-repl-default` for text-to-sql `ask` and `context` shortcuts unless the user supplies `--session-id`.
- [x] Reconfigured REPL stdin/stdout/stderr to UTF-8 so Korean piped/subprocess REPL input does not produce surrogate decode errors.
- [x] Delegated command `SystemExit` is caught inside the REPL so one failed command does not terminate the shell.
- [x] Added regression test `test_v10_agent_repl_uses_default_session_for_text_to_sql_shortcuts`.
- [x] Verified `inspect 0` shows `before ask` behaviors and `after ask` graph objects/relations including `session`, `session_resolution`, and `belongs_to_session`.
- [x] Full Text-to-SQL TDD file: `53 passed`.
- [x] `pack validate hospital-db --json`: ok.
- [x] `pack validate techshop-db --json`: ok.
## v10 inspect before-graph bugfix checkpoint
- [x] Root cause: `inspect` replayed only the selected run graph, so `before ask` stayed empty even when session memory existed outside that per-run event graph.
- [x] Added session-memory projection for `inspect`: when a run has `session_id`, `before ask` now shows the session graph as it existed before that run was appended.
- [x] `inspect` and hidden `inspect-run` now pass selected `pack_id` and `--session-store-dir` into the inspection path.
- [x] Added regression `test_v10_inspect_shows_session_graph_before_current_ask`.
- [x] Focused regression: `1 passed, 53 deselected`; focused v10 subset: `5 passed, 49 deselected`; full Text-to-SQL TDD file: `54 passed`.
- [x] CLI smoke for run `01KXHQCV1XGCCARSSR6JTT8DJE` shows `before ask` graph_scope `session_memory_before_run`, prior `session_turn`, `entity:doctor.name:김지훈`, and session relations.
- [!] Creating brand-new SQLite files still hit environment-level `sqlite3.OperationalError: disk I/O error`; existing default event store remains writable and was used for smoke.
## v10 inspect graph print alignment checkpoint
- [x] Refactored `echo_inspect_run` to render before/after graph snapshots through the same formatter.
- [x] Both `before ask` and `after ask` now show `graph_scope`, `session_id` when present, `events/objects/relations` counts, aligned object columns, and aligned relation source columns.
- [x] Added regression `test_v10_inspect_human_output_aligns_before_and_after_graph_format`.
- [x] Focused formatter test: `1 passed, 54 deselected`; v10 subset: `6 passed, 49 deselected`; full Text-to-SQL TDD file: `55 passed`.
## v11 SQL planner design checkpoint
- [x] Created root `sql_planner_design.md` as the v11 design checkpoint before implementation.
- [x] Design defines `resolve_sql_planner` as the new pre-SQL behavior boundary, plus `planner_resolution`, `clarification_request`, and `decision_rationale` graph objects.
- [x] Policy decision: do not call LLM automatically when resolution fails; use LLM only as explicit planner-advisor mode that returns structured resolution candidates, never SQL.
- [x] Proposed deterministic-first staging: model declarations, resolver unit tests, runtime graph integration, clarification path, then optional LLM advisor.
## v11 SQL planner resolution implementation checkpoint
- [x] Added deterministic `activegraph.cli.sql_planner` with `PlannerResolution`, planner config loading, direct-rule assumption recording, ambiguity clarification, implicit constraint detection, concept-mismatch hooks, and multi-intent detection fallback.
- [x] Added `system-model.hospital.v11.yaml` and `system-model.techshop.v11.yaml` with `planner_resolution_model` declarations; pack registry now points hospital/techshop DB and DB+KB packs at v11 files.
- [x] Runtime v11 path now runs `resolve_sql_planner` before `parse_intent`; v06 explicit tests remain backward-compatible.
- [x] Graph/event traces record `planner_resolution`, `decision_rationale`, and `clarification_request`; ambiguity returns `source: clarification` answer and no SQL.
- [x] Optional planner LLM remains intentionally unimplemented per design.
- [x] Tests: v11 focused `3 passed`; broader pack/context/v10/v11 `18 passed`; full Text-to-SQL TDD file `58 passed`.
- [x] CLI smokes: `VIP 고객 총매출액` records confirmed-order assumption and executes SQL; `가장 많이 팔린 거` requests clarification with no SQL; `inspect` shows planner graph objects.
- [x] Pack validate passed for `hospital-db` and `techshop-db`; v11 YAML files parse.
## Consolidated Text-to-SQL evals checkpoint
- [x] Added `activegraph/text-to-sql-agent/evals/eval_manifest.yaml` as the two-pack eval index for `hospital-db` and `techshop-db`.
- [x] Added runnable consolidated JSONL evals: `hospital_consolidated_cases.jsonl` (29 cases) and `techshop_cases.jsonl` (23 cases), including v08 prompt robustness and v11 planner clarification outcomes.
- [x] Extended eval scoring to assert `answer_source` and `planner_resolution` status, imperfection types, and selected rule hints.
- [x] Fixed hospital scheduled appointment variants by adding `예정예약수` to rule matching and tightened TechShop v11 planner multi-intent/ambiguity detection.
- [x] Focused consolidated eval tests: `2 passed, 58 deselected`.
- [x] CLI eval smokes: hospital `29 passed, 0 failed`; techshop `23 passed, 0 failed`.
- [x] Full Text-to-SQL TDD file: `60 passed`.
## Pack-selected eval default bugfix checkpoint
- [x] Root cause: `text-to-sql eval` had a static Click default of `evals/hospital_cases.jsonl`, so after `pack use techshop-db`, bare `eval` still ran hospital cases against the TechShop DB/model.
- [x] Added pack-aware eval case resolution in `activegraph.cli.text_to_sql`: bare `eval` reads `eval_manifest.yaml` and selects the pack's consolidated JSONL, with DB-name fallback for DB+KB packs.
- [x] `run_eval` JSON payload now includes `cases_file` so inspect/debug output shows which eval suite ran.
- [x] Added regression `test_text_to_sql_eval_defaults_to_selected_pack_cases`.
- [x] Updated the v10 REPL regression to explicitly select `hospital-db` for hospital prompts and restore `techshop-db`, so it no longer depends on mutable global default pack state.
- [x] Exact REPL smoke passed: `pack use techshop-db` then `eval` now reports `summary: 23 passed, 0 failed`.
- [x] Hospital bare eval smoke passed with `hospital_consolidated_cases.jsonl`: `29 passed, 0 failed`.
- [x] Focused pytest set passed: `4 passed, 57 deselected`.
- [!] Full pytest run was blocked by environment temp-directory permission errors in pytest basetemp/tmp_path handling; relevant focused tests and CLI smokes passed.
