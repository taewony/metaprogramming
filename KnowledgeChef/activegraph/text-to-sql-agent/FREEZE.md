# ActiveGraph Text-to-SQL Agent Freeze Baseline

Status: frozen reference baseline
Frozen milestone: v11.5 deterministic third-party pack onboarding and eval-run protocol
Date: 2026-07-23

## Purpose

This folder is now the reference implementation for the DB-only Text-to-SQL experiment line. It should remain useful as a regression oracle, design reference, and learning artifact, but it should not absorb the next OKF KB/RAG expansion work.

The next product line starts in `activegraph/text-to-query-agent/` and treats ActiveGraph as an imported Python runtime library while implementing query-specific agent behavior in a separate application layer.

## Frozen Capabilities

The frozen baseline includes:

- deterministic Korean Text-to-SQL behavior over SQLite packs;
- hospital and TechShop DB packs;
- OKF schema-bundle projection for DB schema context;
- pack validation and pack schema inspection;
- third-party SQLite DB + OKF schema-bundle onboarding through `pack import`;
- eval-run artifacts under `.tests/eval-runs/<eval_run_id>`;
- `eval-run export` and `eval-run attach-score` for external scoring;
- session-scoped memory for supported multi-turn references;
- deterministic SQL planner resolution before SQL generation;
- optional Ollama answer composition after deterministic SQL/result execution;
- event-log adaptation proposals through `text-to-sql adapt`.

## Verification Baseline

Last known verification for this frozen line:

```text
python -m pytest tests/test_activegraph_text_to_sql_tdd.py -q
63 passed
```

The baseline should continue to answer the supported hospital and TechShop eval cases. New OKF KB/RAG behavior should be implemented and evaluated in `text-to-query-agent`, then compared back to this baseline for DB regression compatibility.

## Allowed Changes

Allowed:

- bug fixes that preserve the frozen behavior contract;
- test-only changes that clarify baseline expectations;
- documentation updates that explain the baseline;
- security or correctness fixes in shared copied ActiveGraph runtime code, when necessary.

Avoid:

- adding OKF KB ingestion behavior here;
- adding RAG query behavior here;
- adding sub-agent orchestration here;
- broad package restructuring inside this frozen folder;
- hiding behavior changes behind LLM fallback.

## Baseline CLI Surface

```text
python activegraph/text-to-sql-agent/agent.py pack list
python activegraph/text-to-sql-agent/agent.py pack validate --all --json
python activegraph/text-to-sql-agent/agent.py pack schema techshop-db --json
python activegraph/text-to-sql-agent/agent.py --pack hospital-db text-to-sql ask "의사는 모두 몇명이야?"
python activegraph/text-to-sql-agent/agent.py --pack techshop-db text-to-sql eval --json
python activegraph/text-to-sql-agent/agent.py eval-run export <eval_run_id>
python activegraph/text-to-sql-agent/agent.py eval-run attach-score <eval_run_id> <case_id> --score-file score.json
```

## Migration Target

The successor architecture is `activegraph/text-to-query-agent/`.

The migration target keeps this principle:

```text
ActiveGraph = generic event-sourced graph/runtime library
TextToQueryAgent = application layer over ActiveGraph
Pack = external resources + system-model + eval contract
Behavior = declarative system-model action unit projected into runtime
```

The first `text-to-query-agent` milestone should reproduce the DB-only baseline before adding OKF KB/RAG.
