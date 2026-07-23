# Text-to-Query Agent Baseline

Status: baseline scaffold
Baseline model: `agent/system-model.v00.yaml`
Predecessor baseline: `../text-to-sql-agent/FREEZE.md`

## Purpose

`text-to-query-agent` is the clean successor line after the v11.5 Text-to-SQL baseline. It starts from the same DB query behavior contract, but it is named and structured for multiple query targets:

- SQLite DB query;
- OKF schema projection;
- future OKF KB ingestion;
- future RAG query over OKF Knowledge Bundles;
- future hybrid SQL + KB answer fusion.

The folder exists to keep the next architecture from being constrained by the experimental naming and module boundaries inside `text-to-sql-agent`.

## Architectural Boundary

```text
ActiveGraph library
  -> Graph, Event, Runtime, Behavior, EventStore

TextToQueryAgent application layer
  -> PackContext
  -> SystemModelLoader
  -> BehaviorFactory
  -> QueryTarget adapters
  -> EvalRun protocol
  -> CLI / REPL
```

ActiveGraph should be imported as a Python runtime library. The query-specific agent should not live inside the generic ActiveGraph CLI module.

## Initial Milestones

1. Reproduce the frozen DB-only baseline from `text-to-sql-agent`.
2. Introduce `TextToQueryAgent` service boundary.
3. Introduce `PackContext` as the only path/config object passed through the runtime.
4. Move system-model parsing into `system_model/loader.py`.
5. Move RuleCatalog and deterministic SQL planning under `behaviors/sql_query.py` or `system_model/rule_catalog.py`.
6. Move eval-run protocol under `evals/eval_run.py`.
7. Only after DB baseline compatibility is green, add OKF KB ingestion and RAG behavior.

## Compatibility Gate

The first implementation milestone is not new functionality. It is compatibility:

```text
hospital consolidated eval: pass
techshop consolidated eval: pass
third-party pack import smoke: pass
eval-run export/attach-score smoke: pass
```

## Non-Goals For The Baseline Scaffold

- No automatic generic NL-to-SQL over arbitrary schemas.
- No implicit planner LLM fallback.
- No OKF KB writes yet.
- No RAG answer fusion yet.
- No generated `SKILL.md` yet.
- No sub-agent orchestration yet.
