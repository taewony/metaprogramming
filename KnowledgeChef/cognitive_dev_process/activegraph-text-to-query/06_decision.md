# 06 Decision

## Decision

Freeze `text-to-sql-agent` and begin `text-to-query-agent` as a clean successor baseline.

## Accepted Constraints

- Do not add OKF KB ingestion to the frozen folder.
- Do not add RAG answer fusion to the frozen folder.
- Do not hide unsupported prompts behind implicit LLM fallback.
- Do not treat private third-party eval answers as training data.
- Keep deterministic compatibility as the first migration goal.

## Chosen Next Actions

1. Preserve `text-to-sql-agent` through `FREEZE.md`.
2. Create `text-to-query-agent` folder and baseline system-model v00.
3. Store the refactoring rationale in `artifacts/activegraph_text_to_query_refactoring_plan.md`.
4. Track the development process as cognitive dev-loop markdown.
5. Generate `cognitive_dev_process.html` at the root as learning material.

## Deferred Decisions

- Exact package layout after compatibility migration.
- Whether `text-to-query-agent` gets its own Click CLI or wraps the current ActiveGraph CLI initially.
- How much of v11.5 code is copied, moved, or reimplemented behind the new boundary.
- When generated `SKILL.md` becomes part of pack scaffolding.
- How OKF KB approval state is represented in graph objects.
