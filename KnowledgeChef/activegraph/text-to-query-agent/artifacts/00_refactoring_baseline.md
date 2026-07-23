# Text-to-Query Agent Refactoring Baseline

This artifact records the decision to freeze `text-to-sql-agent` at v11.5 and begin a clean `text-to-query-agent` line.

## Decision

Use `text-to-sql-agent` as the frozen reference implementation and create `text-to-query-agent` as the successor architecture.

## Rationale

The previous implementation proved the behavior model through real code, tests, event logs, pack validation, and eval-run artifacts. It also accumulated experimental naming and module coupling:

- `hospital_logic.py` now contains generic RuleCatalog behavior;
- `text_to_sql.py` mixes CLI, behavior factory, runtime assembly, eval, inspect, and session behavior;
- `activegraph.cli.main` contains both generic ActiveGraph CLI and application-specific pack/eval-run commands;
- path defaults are module-level constants rather than pack context;
- SQL-only naming is too narrow for OKF KB and RAG work.

The next phase needs a cleaner boundary before adding OKF/RAG.

## Baseline Principle

```text
Do not continue expanding the experiment folder.
Freeze the experiment as evidence.
Start the product-shaped architecture from the system model.
```

## Target Layering

```text
activegraph runtime library
  Graph / Runtime / Event / Behavior / Store

text_to_query_agent application layer
  TextToQueryAgent
  PackContext
  SystemModelLoader
  BehaviorFactory
  QueryTarget adapters
  EvalRun protocol
  CLI / REPL
```

## Migration Rule

No feature is considered migrated until it has:

- a system-model declaration;
- deterministic behavior implementation;
- eval coverage;
- event/graph evidence;
- compatibility check against the frozen `text-to-sql-agent` baseline.
