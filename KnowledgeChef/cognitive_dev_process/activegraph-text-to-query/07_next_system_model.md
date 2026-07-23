# 07 Next System Model

## Next System Model Summary

The next system model is now externalized in:

```text
activegraph/text-to-query-agent/agent/system-model.v00.yaml
```

It defines the first clean boundary for the successor agent.

## Target Runtime Shape

```text
TextToQueryAgent.from_pack(pack_id)
  -> resolves PackContext
  -> loads system-model
  -> projects OKF schema context
  -> registers ActiveGraph behaviors
  -> executes query behavior
  -> records event/eval evidence
```

## First Compatibility Milestone

The first implementation task for the new line should be:

```text
Implement ask/eval for hospital-db through TextToQueryAgent service boundary.
```

Expected proof:

```text
hospital consolidated eval passes
trace.jsonl exists per case
graph.json exists per case
summary.json records eval-run result
```

## Future Expansion After Compatibility

Only after DB compatibility is green:

1. Add OKF raw-file ingestion draft behavior.
2. Add one-approval-per-upload write gate.
3. Add OKF KB page write artifacts.
4. Add KB question answering behavior.
5. Add RAG context retrieval.
6. Add SQL + KB answer fusion.
7. Add generated `SKILL.md` from system-model specs.

## Learning Loop Re-entry

The next coding session should begin by reading:

```text
activegraph/text-to-sql-agent/FREEZE.md
activegraph/text-to-query-agent/README.md
activegraph/text-to-query-agent/agent/system-model.v00.yaml
artifacts/activegraph_text_to_query_refactoring_plan.md
cognitive_dev_process.html
```
