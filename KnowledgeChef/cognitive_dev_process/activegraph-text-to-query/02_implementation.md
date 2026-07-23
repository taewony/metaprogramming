# 02 Implementation

## What Was Implemented In This Baseline Transition

The transition does not yet rewrite the DB runtime. It creates the physical scaffolding for the next architecture:

```text
activegraph/text-to-sql-agent/FREEZE.md
activegraph/text-to-query-agent/README.md
activegraph/text-to-query-agent/agent/system-model.v00.yaml
activegraph/text-to-query-agent/artifacts/00_refactoring_baseline.md
activegraph/text-to-query-agent/src/text_to_query_agent/app.py
artifacts/activegraph_text_to_query_refactoring_plan.md
cognitive_dev_process/activegraph-text-to-query/*.md
cognitive_dev_process.html
```

## Freeze Implementation

`FREEZE.md` marks `text-to-sql-agent` as the v11.5 frozen baseline:

- DB-only deterministic query reference;
- third-party pack onboarding reference;
- eval-run evidence protocol reference;
- bug-fix-only or regression-reference role.

## New Baseline Implementation

The new `text-to-query-agent` starts with:

- `TextToQueryAgent` service placeholder;
- `PackContext` dataclass;
- system-model v00 that declares the desired layering;
- artifact explaining why the new line exists.

## Implementation Discipline

The first real implementation milestone is compatibility, not feature expansion.

```text
Do not add OKF KB/RAG first.
First prove the new boundary can reproduce the frozen DB behavior.
```
