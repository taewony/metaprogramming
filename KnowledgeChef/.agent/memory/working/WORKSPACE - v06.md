# Workspace (live task state)

## Current task
TechShop VIP confirmed-order total revenue support for `VIP 고객 총매출액`.

## Open files
- .agent/memory/working/WORKSPACE.md
- activegraph/text-to-sql-agent/agent/instructions.md
- activegraph/text-to-sql-agent/agent/packs.yaml
- activegraph/text-to-sql-agent/agent/system-model.hospital.v06.yaml
- activegraph/text-to-sql-agent/agent/system-model.techshop.v06.yaml
- activegraph/text-to-sql-agent/agent/system-model.v99.yaml
- activegraph/text-to-sql-agent/src/cli/full_context.py
- activegraph/text-to-sql-agent/src/cli/hospital_logic.py
- activegraph/text-to-sql-agent/src/cli/text_to_sql.py
- activegraph/text-to-sql-agent/agent.py
- tests/test_activegraph_text_to_sql_tdd.py

## Active hypotheses
- Full Context should be deterministic and inspectable before any LLM adapter is introduced.
- The first v06 slice should assemble context without executing SQL, so it remains replay-safe and suitable for tests.
- Packs should move to v06 system models so the selected configuration declares `full_context_model` explicitly.

## Checkpoints
- [x] Inspected TechShop orders schema and VIP order data.
- [x] Decided `총매출액` should use confirmed orders only, excluding cancelled/returned rows.
- [x] Added `vip_customer_revenue_total` rule to `system-model.techshop.v06.yaml`.
- [x] Added regression test for `VIP 고객 총매출액`.
- [x] Verified focused TechShop VIP tests: `3 passed`.
- [x] Ran CLI ask `VIP 고객 총매출액`; answer `VIP 고객 총매출액은 6486000원입니다.`.
- [x] Inspected latest event-log run `01KXHGBFD2XCEQ7Y9HCXPCZYRZ`; graph uses rule `vip_customer_revenue_total`, SQL result `6486000`, no failures.
- [x] Verified `pack validate techshop-db`: ok, 5 executable rules.
- [x] Verified full activegraph text-to-SQL pytest file: `39 passed`.
- [x] Added `activegraph/text-to-sql-agent/src/cli/full_context.py`.
- [x] Added `text-to-sql context <prompt> [--json]` CLI command.
- [x] Added system prompt content to `agent/instructions.md`.
- [x] Created `system-model.hospital.v06.yaml` and `system-model.techshop.v06.yaml` with `full_context_model` declarations.
- [x] Switched all packs to v06 system-model files.
- [x] Extended RuleCatalog schema support to `system-model.v06`.
- [x] Full Context includes system prompt, selected pack, system-model slice, schema context, user prompt, planned intent, recent event trace, KB context, and LLM contract.
- [x] Added direct assembly and CLI regression tests.
- [x] Verified focused v06 context tests: `5 passed`.
- [x] Verified full activegraph text-to-SQL pytest file: `38 passed`.
- [x] Verified `pack validate --all`: ok.
- [x] Smoke-tested `--pack techshop-db text-to-sql ask "VIP는 몇명" --json` with v06 system model.

## Next step
Start v06.1 or v07: either add a no-op/mock LLM adapter that records `llm_invocation` without changing deterministic answers, or move to approval-gated OKF KB ingestion.

```
• v06 Full Context assembly is implemented.

  What changed:

  - Added deterministic assembler: activegraph/text-to-sql-agent/src/cli/full_context.py:206
  - Added CLI command: activegraph/text-to-sql-agent/src/cli/text_to_sql.py:955

  python activegraph/text-to-sql-agent/agent.py --pack techshop-db text-to-sql context "VIP는 몇명" --json

  It assembles, without executing SQL:

  - system prompt from agent/instructions.md
  - selected pack
  - v06 system-model slice
  - OKF schema context
  - user prompt
  - planned deterministic intent
  - recent event trace
  - KB context placeholder
  - explicit LLM adapter contract

  Also added v06 system models:

  - activegraph/text-to-sql-agent/agent/system-model.hospital.v06.yaml
  - activegraph/text-to-sql-agent/agent/system-model.techshop.v06.yaml:173

  All packs now point to v06 models in activegraph/text-to-sql-agent/agent/packs.yaml:7.

  Verification:

  - focused v06 context tests: 5 passed
  - full suite: 38 passed
  - pack validate --all: ok
  - v06 ask smoke still works: VIP 고객은 총 5명입니다.
```

```
• Supported.

  I added a TechShop v06 rule for:

  VIP 고객 총매출액

  It uses confirmed orders only, excluding cancelled and returned rows.

  SQL:

  SELECT CAST(SUM(o.total_amount) AS INTEGER)
  FROM orders o
  JOIN customers c ON c.id = o.customer_id
  WHERE c.grade = ? AND o.status = ?

  params:

  ["VIP", "confirmed"]

  CLI result:

  VIP 고객 총매출액은 6486000원입니다.

  Latest inspected run: 01KXHGBFD2XCEQ7Y9HCXPCZYRZ

  Graph confirmed:

  - intent.rule_id: vip_customer_revenue_total
  - query_result.rows: [[6486000]]
  - failures: none

  Verification:

  - focused TechShop VIP tests: 3 passed
  - full suite: 39 passed
  - pack validate techshop-db: ok, 5 executable rules

```

---

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
