# 01 System Model

## Core Question

How should the ActiveGraph agent architecture evolve before OKF KB ingestion and RAG query are added?

## Baseline Mental Model

The v11.5 Text-to-SQL agent proved that a deterministic ActiveGraph agent can answer DB questions through an event-sourced graph runtime:

```text
question.submitted
  -> planner.resolved
  -> intent.created
  -> sql.generated
  -> sql.executed
  -> answer.created
```

It also proved that third-party packs can be evaluated through event evidence:

```text
pack import
  -> pack validate
  -> schema projection
  -> eval run
  -> eval-run export
  -> external score attachment
```

## New System Model

The next system model separates generic runtime from query-agent application code:

```text
ActiveGraph = event-sourced graph runtime library
TextToQueryAgent = application layer for DB, OKF schema, OKF KB, and RAG query
PackContext = resolved external resources and configuration
SystemModel = declarative behavior and context contract
EvalRun = inspectable evidence bundle
```

## Key Architectural Bet

Freezing the experiment and starting a clean successor line will reduce cognitive drift before OKF/RAG complexity is introduced.

## Success Criteria

- `text-to-sql-agent` remains a reproducible frozen baseline.
- `text-to-query-agent` starts with `system-model.v00.yaml`.
- DB-only behavior is migrated before new OKF/RAG behavior is added.
- Every milestone produces event/eval evidence that can be used as learning material.
