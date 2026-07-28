# Workspace (live task state)

## Current task
Created frozen Text-to-SQL v11.5 baseline docs, new Text-to-Query v00 baseline scaffold, cognitive dev-loop markdown artifacts, and root cognitive_dev_process.html learning dashboard.

## Open files
- cognitive_dev_process/activegraph-text-to-query/07_next_system_model.md
- cognitive_dev_process/activegraph-text-to-query/01_system_model.md
- cognitive_dev_process.html
- artifacts/activegraph_text_to_query_refactoring_plan.md
- activegraph/text-to-query-agent/src/text_to_query_agent/app.py
- activegraph/text-to-query-agent/artifacts/00_refactoring_baseline.md
- activegraph/text-to-query-agent/agent/system-model.v00.yaml
- activegraph/text-to-query-agent/README.md
- activegraph/text-to-sql-agent/FREEZE.md
- activegraph/text-to-sql-agent/agent/system-model.v99.yaml
- plan.md
- design-spec.md
- activegraph/text-to-sql-agent/src/cli/main.py
- activegraph/text-to-sql-agent/src/cli/eval_run.py
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
## Third-party DB+OKF readiness review checkpoint
- [x] Reviewed `system-model.v99.yaml`, current v11 runtime, pack registry, OKF schema projection, eval manifest, scorer, event-store/adaptation path for third-party SQLite DB + OKF bundle onboarding.
- [x] Current state: pack registry, pack validate, schema projection, eval execution, SQLite event logs, inspect/adapt loop are implemented for declared packs.
- [!] Not yet product-ready for arbitrary third-party domains: no pack scaffold/import command, no system-model generator from DB+OKF, no generic NL-to-SQL planner, no first-class eval-run/scoring artifact written to event logs, and KB/RAG v12-v13 remain deferred.
## Design-spec v11.5 checkpoint
- [x] Updated `design-spec.md` purpose/current decisions so the next milestone after v11 deterministic Text-to-SQL is third-party DB + OKF schema-bundle onboarding.
- [x] Added `v11.5 Third-Party Pack Onboarding And Eval-Run Protocol` covering third-party package inputs, manual/current onboarding path, future `pack import`, sparse system-model bootstrap boundary, eval-run objects/events, external scoring, export bundle shape, and v11.5 acceptance criteria.
- [x] Reframed OKF KB ingestion, RAG query, and sub-agent orchestration as Future Work.
- [x] Updated evaluation strategy and required CLI surfaces around pack validation, schema projection, eval-run export, and external score attachment.
- [x] Updated near-term implementation plan, resolved questions, deferred decisions, and design rules to match the v11.5 focus.
## v11.5 third-party onboarding checkpoint
- [x] Added `import_thirdparty_pack` in `activegraph.cli.pack_config` to register a third-party SQLite DB, OKF schema bundle, eval JSONL, generated v11 system model, event-store binding, and eval manifest entry.
- [x] Added generated exact-prompt RuleCatalog support through `match.exact` for eval-backed deterministic bootstrap rules.
- [x] Added `activegraph.cli.eval_run` for eval-run IDs, eval event JSONL, per-case result/trace/graph/scoring-input artifacts, export, and external score attachment.
- [x] Extended `text-to-sql eval` to create `.tests/eval-runs/<eval_run_id>` artifacts and include `eval_run_id` in CLI/JSON output.
- [x] Added top-level `pack import`, `eval-run export`, and `eval-run attach-score` CLI commands and exposed them in REPL help.
- [x] Updated `design-spec.md`, `plan.md`, and `system-model.v99.yaml` to mark v11.5 implemented for the deterministic pack-runtime path.
- [x] Tests: focused v11.5 `2 passed`; focused pack/eval regression `11 passed`; full `tests/test_activegraph_text_to_sql_tdd.py` `63 passed`.

```
• Implemented v11.5.

  What changed:

  - Added pack import for third-party SQLite DB + OKF schema bundle + eval JSONL onboarding.
  - Added generated v11 system-model bootstrap from OKF table docs and eval cases with public expected_sql.
  - Added match.exact support in RuleCatalog for imported eval-backed deterministic rules.
  - Added eval-run protocol artifacts under .tests/eval-runs/<eval_run_id>/.
  - Added eval-run export and eval-run attach-score.
  - Extended text-to-sql eval to emit eval_run_id, per-case result.json, trace.jsonl, graph.json, and scoring-
    input.json.

  - Updated REPL/help, design-spec.md, plan.md, and system-model.v99.yaml.

  Key files:

  - activegraph/text-to-sql-agent/src/cli/pack_config.py
  - activegraph/text-to-sql-agent/src/cli/eval_run.py
  - activegraph/text-to-sql-agent/src/cli/text_to_sql.py
  - activegraph/text-to-sql-agent/src/cli/main.py
  - tests/test_activegraph_text_to_sql_tdd.py

  Validation:

  - 63 passed for full tests/test_activegraph_text_to_sql_tdd.py
  - pack validate --all --json passed
  - CLI smoke passed for:
      - pack import --help
      - eval-run export
      - eval-run attach-score
      - hospital eval with eval-run artifact generation

  Important boundary: this is still deterministic pack onboarding, not generic NL-to-SQL. pack import generates exact-
  prompt rules from eval cases that include expected_sql; private eval packs without public SQL can be registered/
  evaluated, but useful answering still needs explicit rule/adaptation work.

  Note: smoke/eval runs appended to tracked SQLite event stores under activegraph/data/. Existing unrelated workspace
  changes such as .tmp deletions and packs.yaml default pack state were not reverted.
```
## Text-to-Query baseline + cognitive dashboard checkpoint
- [x] Added `activegraph/text-to-sql-agent/FREEZE.md` to freeze the v11.5 DB-only Text-to-SQL baseline as regression oracle and learning reference.
- [x] Created `activegraph/text-to-query-agent/` scaffold with `README.md`, `agent/system-model.v00.yaml`, `artifacts/00_refactoring_baseline.md`, and minimal `TextToQueryAgent`/`PackContext` placeholders.
- [x] Added root refactoring plan at `artifacts/activegraph_text_to_query_refactoring_plan.md`.
- [x] Added cognitive dev-loop markdown sequence under `cognitive_dev_process/activegraph-text-to-query/` for System Model, Implementation, Evaluation, Evidence, Insight, Decision, and Next System Model.
- [x] Generated root `cognitive_dev_process.html` as a self-contained learning dashboard with architecture transition, evidence protocol, compatibility gate, and links to generated artifacts.
- [x] Validated generated file existence plus Python AST and YAML parse for the new baseline scaffold.
## Artifact process rewrite checkpoint
- [x] Rewrote `artifacts/SKILL.md` into a reusable `cognitive-dev-loop` skill for staged Coding Agent development.
- [x] Rewrote `artifacts/cognitive_dev_process.md` into a general cognitive/epistemic development process covering system models, TDD/evals, evidence, insight, decisions, ActiveGraph projection, baseline freezes, and learning artifacts.
- [x] Validated `artifacts/SKILL.md` frontmatter with PyYAML and checked required cognitive process sections.
## Two-paper draft checkpoint
- [x] Created `docs/paper1_micro_vllm_educational_systems_artifact_draft.md` as a revised micro-vLLM paper centered on Windows-native inference-engine migration, fixed-context agent workloads, and assumed successful prefix KV-cache experiments.
- [x] Created `docs/paper2_activegraph_educational_knowledge_agent_draft.md` as the broader educational knowledge-agent paper using OKF, ActiveGraph event logs, graph projection, executable evidence, and CUDA/nano-vLLM course material.
- [x] Marked all hypothetical experimental numbers with `[ASSUMED]` so they can be replaced with measured data before submission.
## Paper #1 active work checkpoint
- [x] Inventoried KernelAgent stages: `0-MatMul`, `1-FMHA`, `2-LLM-from-scratch`, and `3-micro-vllm`.
- [x] Confirmed Paper #1 should use host-PC for source/paper/script preparation and target-PC RTX5070 for all final GPU measurements.
- [x] Added `docs/paper1_execution_plan.md` with contribution framing, host/target split, existing evidence, and prefix KV-cache experiment plan.
- [x] Added `KernelAgent/3-micro-vllm/bench_prefix_cache.py` to measure no-cache, warm-cache, and prefix-changed fixed-context workloads.
- [x] Validated benchmark script with AST parsing and `--help`; GPU execution remains target-PC work because host Python lacks `torch`.
## Paper #1 prefix-cache result checkpoint
- [x] Found three target-PC result files under `KernelAgent/3-micro-vllm`: `prefix_cache_results_cutile.jsonl`, `prefix_cache_results_cutile_1024.jsonl`, and `prefix_cache_results_cutile_3072.jsonl`.
- [x] Parsed all three JSONL files successfully: each has 28 rows, no malformed JSON, and summaries for `no_cache`, `warm_cache`, and `prefix_changed`.
- [x] Key result: warm prefix cache reduces TTFT strongly and reduces computed prefill tokens to 64, while E2E throughput does not consistently improve because decode dominates the 64-token generation loop.
## Paper #1 KTCP revision checkpoint
- [x] Generated `docs/paper1_prefix_cache_results.md` from measured prefix-cache JSONL data.
- [x] Created `docs/paper1_micro_vllm_ktcp_revised_draft.md` with measured results replacing earlier `[ASSUMED]` placeholders.
- [x] Created `KernelAgent/paper/paper-v4-prefix-cache.tex` as a KCC/KTCP-oriented LaTeX draft with fixed-context agent workload and prefix KV-cache evidence.
- [x] Checked the new Paper #1 artifacts for unresolved placeholder markers; `pdflatex` is not available on PATH in the current environment.
## Paper #1 HTML review checkpoint
- [x] Created Korean review HTML at `KernelAgent/paper/paper-v4-prefix-cache.ko.html` from `paper-v4-prefix-cache.tex`.
- [x] Created English review HTML at `KernelAgent/paper/paper-v4-prefix-cache.en.html` with matching structure and measured-result tables.
- [x] Validated language tags, closing HTML tags, key prefix-cache metrics, and absence of placeholder markers.
## Paper #1 Green Context TTFT checkpoint
- [x] Re-analyzed saved Green Context logs: TTFT mean delta -0.57% across 9 runs, but effect is small and mixed.
- [x] Added forced Green Context API selection via `NANO_VLLM_GREEN_CONTEXT_API=auto|pytorch|cuda_core` plus SM split env vars in `model_runner.py`.
- [x] Added Green Context metadata to `bench_green.py` result JSON.
- [x] Added `KernelAgent/3-micro-vllm/bench_green_repeat.py` for target-PC repeated JSONL evidence collection.
- [x] Added `docs/paper1_green_context_ttft_analysis.md` with interpretation, target-PC commands, and paper inclusion decision rule.
## Active hypotheses
- Green Context integration failure is caused by stale cuda.core usage in `model_runner.py`: old `from cuda import cuda` import plus `ctx.push_current()/pop_current()` activation, while the target PC validates `from cuda.bindings import driver as cuda` plus `dev.set_current(ctx)/dev.set_current()`.
## Paper #1 cuda.core Green Context runtime checkpoint
- [x] Incorporated target-PC finding: PyTorch GreenContext remains unavailable, but `cuda.core` works with `cuda.bindings.driver`, `Device.set_current(ctx)`, and `Device.set_current()` restoration.
- [x] Updated `KernelAgent/3-micro-vllm/nanovllm/engine/model_runner.py` to use the working cuda.core import and activation path.
- [x] Updated `KernelAgent/3-micro-vllm/tests/test_green_contexts_api.py` with the working preflight and an exact 32/16 two-context check.
- [x] Updated `docs/paper1_green_context_ttft_analysis.md` to distinguish prior fallback-control JSONL from future valid Green Context efficacy runs.
## Paper #1 Green Context preflight checkpoint
- [x] Rewrote `KernelAgent/3-micro-vllm/tests/test_green_contexts_api.py` as a structured target-PC preflight.
- [x] Treats PyTorch GreenContext as optional and cuda.core `Device.set_current()` activation as the required benchmark path.
- [x] Checks both a single decode partition and the exact benchmark split from `NANO_VLLM_PREFILL_SMS`/`NANO_VLLM_DECODE_SMS` defaults 32/16.
- [x] Returns process exit code 0 only when cuda.core Green Context preflight succeeds.
## Paper #1 Green Context split-mapping checkpoint
- [x] Updated `model_runner.py` to use `sm.split(SMResourceOptions(count=(decode_sms,)))` and map the returned remainder resource to prefill.
- [x] Updated `test_green_contexts_api.py` to match the target-PC passing run: PyTorch path optional, cuda.core path required, decode partition plus remainder-as-prefill mapping.
- [x] AST validation passed for `model_runner.py` and `test_green_contexts_api.py`.
## Active hypotheses
- `cuda.core` `sm.split(SMResourceOptions(count=(decode_sms,)))` may return only the requested decode SMResource on RTX 5070; requiring a second remainder resource is too strict. The passing target-PC probe uses the device SM resource object as the prefill-side fallback when no explicit remainder is returned.
## Paper #1 Green Context one-resource layout checkpoint
- [x] Fixed `split_decode_and_remainder` after target-PC traceback showed `layout=[SMResource]` rather than `[decode, remainder]`.
- [x] Runtime now maps `layout[0]` to decode and uses `layout[1]` if available, otherwise the device SM resource object as the prefill fallback.
- [x] Added `green_split_layout_width` and `green_prefill_resource_source` metadata to `bench_green.py` output.
- [x] AST validation passed for `test_green_contexts_api.py`, `model_runner.py`, and `bench_green.py`.
## Paper #1 Green Context v2 JSONL checkpoint
- [x] Found and parsed `KernelAgent/3-micro-vllm/green_context_results_cuda_core_32_16_v2.jsonl`.
- [x] Confirmed Green side activation: 20/20 `green_enabled=true`, 20/20 `green_api_type=cuda_core`.
- [x] Confirmed split metadata: 20/20 `green_split_layout_width=1`, 20/20 `green_prefill_resource_source=device_sm_fallback`.
- [x] Interpreted results as activation-valid but efficacy-neutral: one baseline P99 outlier drives the apparent full-run P99 improvement; excluding it leaves TTFT/P99/throughput near flat.
## Paper #1 Green Context Level 1 stress benchmark checkpoint
- [x] Added `KernelAgent/3-micro-vllm/bench_green_stress.py` for adversarial protected-decode plus repeated-prefill interference.
- [x] Measures decode step latency and protected decode completion gap, including prefill-induced pauses between decode tokens.
- [x] Parent mode runs paired baseline/Green subprocesses and writes JSONL evidence with activation metadata.
- [x] AST validation and `--help` passed locally; GPU execution remains target-PC work.
