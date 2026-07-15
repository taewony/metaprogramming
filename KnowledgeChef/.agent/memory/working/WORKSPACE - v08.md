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

```
• v08 prompt robustness is done.

  I added the candidate prompt catalog here: activegraph/text-to-sql-agent/evals/prompt_robustness_candidates.yaml:1

  It separates prompts into:

  - supported_now: deterministic rule variants we expect the current runtime to handle
  - deferred: prompts that belong to v09 adaptation, v10 memory, or v11 planner resolution

  Updated behavior rules:

  - Hospital aliases in activegraph/text-to-sql-agent/agent/system-model.hospital.v06.yaml:304
      - doctor count/list
      - doctor specialty/department
      - doctor hospital/workplace
      - available appointment slots

  - TechShop aliases in activegraph/text-to-sql-agent/agent/system-model.techshop.v06.yaml:236
      - VIP revenue variants: 매출합계, 판매액, 구매액, 총액, typo 맥출액
      - VIP list/name variants
      - new member_count
      - new item_count

  Added v08 tests in tests/test_activegraph_text_to_sql_tdd.py:487.

  Validation passed:

  pytest -k "v08": 3 passed
  full text-to-sql TDD file: 46 passed
  pack validate hospital-db: ok
  pack validate techshop-db: ok

  Representative CLI smokes passed:

  python activegraph/text-to-sql-agent/agent.py --pack hospital-db text-to-sql ask "김지훈 전문분야는?" --json
  python activegraph/text-to-sql-agent/agent.py --pack techshop-db text-to-sql ask "회원 수" --json

  Examples now covered include:

  전체 의사 수
  등록 의사 수 알려줘
  김지훈 전문분야는?
  김지훈 어디 근무해?
  의료진 목록

  VIP 매출 합계
  VIP 판매액
  VIP 고객 이름
  회원 수
  상품 몇 개야?
```