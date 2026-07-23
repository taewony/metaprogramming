# 04 Evidence

## Evidence Sources

The ActiveGraph development process has unusually strong evidence surfaces:

- event logs;
- graph projections;
- eval-run manifests;
- per-case scoring inputs;
- external score attachments;
- inspect output;
- replay/fork/export commands;
- pytest results.

## Evidence From v11.5

The v11.5 baseline produced evidence for:

```text
question -> planner -> intent -> sql -> result -> answer
pack import -> validate -> schema projection -> eval -> export -> external score
```

## Evidence As Learning Material

A single eval case can be taught as a causal chain:

```text
User asked a question.
The question became an event.
The event projected graph objects.
The graph state triggered deterministic behavior.
The behavior generated SQL.
SQLite returned rows.
The answer behavior cited the query result.
The eval-run recorded the evidence bundle.
```

## Evidence Standard For Future OKF/RAG

OKF KB/RAG behavior should not be accepted merely because it returns a plausible answer. It must record:

- source file or OKF page;
- extraction or retrieval path;
- graph object projection;
- confidence and provenance;
- approval state for writes;
- answer citation and unsupported-claim checks.
