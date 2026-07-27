# ActiveGraph Text-to-Query Refactoring Plan

Status: approved baseline transition plan
Date: 2026-07-23

## Executive Decision

Freeze `activegraph/text-to-sql-agent` at the v11.5 deterministic DB-query baseline and start the next architecture in `activegraph/text-to-query-agent`.

The new agent line should be system-model-first and should treat ActiveGraph as a Python runtime library rather than a folder where application-specific behavior keeps accumulating.

## Why Freeze Instead Of Continuing In Place

The Text-to-SQL line proved the core ideas through implementation:

- graph/event behavior execution;
- deterministic SQL planning;
- session graph memory;
- OKF schema-bundle projection;
- pack validation;
- third-party pack import;
- eval-run artifact export and score attachment.

It also accumulated experimental coupling:

- CLI, runtime assembly, behavior factories, eval runner, and inspection are concentrated in `text_to_sql.py`;
- generic RuleCatalog code still lives under a hospital-oriented filename;
- application commands are registered inside the generic ActiveGraph CLI tree;
- SQL-only naming does not fit OKF KB/RAG expansion;
- module-level path defaults make pack/runtime boundaries harder to reason about.

Continuing OKF/RAG work in that folder would preserve short-term momentum but increase long-term architectural ambiguity.

## Target Architecture

```text
ActiveGraph runtime library
  Graph / Event / Runtime / Behavior / EventStore / inspect / replay / fork / diff

TextToQueryAgent application layer
  PackContext
  SystemModelLoader
  QueryTarget adapters
  BehaviorFactory
  EvalRun protocol
  CLI / REPL
```

## Folder Plan

```text
activegraph/
  text-to-sql-agent/
    FREEZE.md
    <v11.5 frozen reference implementation>

  text-to-query-agent/
    README.md
    agent/
      system-model.v00.yaml
      packs.yaml              # later
      instructions.md         # later
    artifacts/
      00_refactoring_baseline.md
    src/
      text_to_query_agent/
        app.py
        pack_context.py       # later or merged with app.py initially
        system_model/
        behaviors/
        adapters/
        evals/
        cli/
    evals/
    .tests/
```

## Migration Sequence

1. Freeze and document v11.5 Text-to-SQL baseline.
2. Create `text-to-query-agent` baseline scaffold and system-model v00.
3. Add a `TextToQueryAgent` service boundary and `PackContext`.
4. Migrate DB-only behavior behind the new boundary without changing behavior.
5. Re-run hospital/TechShop consolidated evals through the new agent.
6. Migrate third-party pack import and eval-run artifact protocol.
7. Only after DB compatibility is green, add OKF KB ingestion.
8. Add RAG query and answer fusion as separate behavior sets.

## Compatibility Gate

The new agent cannot be considered ready for OKF/RAG until it can reproduce:

```text
hospital consolidated eval: pass
techshop consolidated eval: pass
third-party pack import smoke: pass
eval-run export/attach-score smoke: pass
inspect graph evidence: available
```

## TDD Rule

Every migration step should start with a compatibility test against the frozen baseline. The intent is not to rewrite behavior by taste; it is to preserve proven behavior behind a cleaner system boundary.

## Learning Material Rule

Each milestone should update the cognitive dev-loop artifacts:

```text
System Model -> Implementation -> Evaluation -> Evidence -> Insight -> Decision -> Next System Model
```

The event trace and eval-run artifacts are not just debugging files. They are evidence for how the agent thinks, acts, fails, and adapts.
