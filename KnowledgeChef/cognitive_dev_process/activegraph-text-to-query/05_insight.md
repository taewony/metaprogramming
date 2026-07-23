# 05 Insight

## Main Insight

The v11.5 implementation proved the behavior model, but its folder/module shape is still experimental. Before adding OKF KB and RAG, the architecture needs a clearer layer boundary.

## Architectural Insight

The correct abstraction is not `text-to-sql`.

The correct abstraction is `text-to-query`:

```text
natural language query
  -> target resolution
  -> DB query or KB retrieval or hybrid path
  -> evidence-grounded answer
```

SQL is one target. OKF KB is another. RAG is another. The agent should be named and organized around query behavior, not SQL only.

## Cognitive Insight

Without a frozen baseline, a refactor can become a moving target. Freezing the old line reduces cognitive load:

- known-good behavior stays available;
- tests remain a regression oracle;
- event traces stay teachable;
- the new line can be judged by compatibility evidence.

## Design Insight

A system-model-first architecture makes the agent easier to teach:

```text
The system model declares the world.
Behaviors are physics over that declared world.
Events are the proof trail.
Eval-runs package the evidence.
```
