---
name: cognitive-dev-loop
description: Use when Codex needs to run staged Coding Agent development where implementation work must produce tests, evidence, updated system-model YAML, roadmap notes, and reusable learning artifacts. Trigger for system-model driven development, TDD followups, eval/event-log based adaptation, cognitive_dev_process documentation, baseline/freeze transitions, and artifact generation after incremental agent changes.
---

# Cognitive Dev Loop

Use this skill to turn a Coding Agent task into a disciplined development loop:

```text
System Model -> Implementation Plan -> TDD Task -> Implementation -> Evaluation
-> Evidence -> Insight -> Decision -> Updated System Model -> Learning Materials
```

The goal is not only to change code. The goal is to keep the human, the Coding Agent, the tests, the event logs, and the declared system model synchronized.

## Inputs

Load only the inputs needed for the current increment:

- User goal and latest user constraints.
- Current `system-model*.yaml`.
- Current roadmap, `plan.md`, `design-spec.md`, `FREEZE.md`, or baseline notes.
- Existing source code, tests, eval files, CLI commands, and pack configuration.
- Event logs, traces, graph snapshots, inspect output, eval-run artifacts, or failure transcripts.
- External constraints such as approval gates, environment variables, DB paths, OKF bundle paths, and no-regression requirements.

## Outputs

Produce the smallest useful set of artifacts for the increment:

- Updated `system-model*.yaml` when behavior, graph objects, runtime phases, pack rules, or roadmap state changes.
- Updated implementation plan, design spec, freeze note, or decision record when architecture meaning changes.
- New or updated tests/evals that make the expected behavior executable.
- Evidence artifacts such as `trace.jsonl`, `graph.json`, eval summaries, scoring inputs, CLI transcripts, screenshots, or focused command output summaries.
- Learning artifacts under `artifacts/` or `cognitive_dev_process/<project>/`.
- Optional root `cognitive_dev_process.html` when the user asks for a visual learning material.

## Procedure

1. Load context and constraints.
   Read the relevant system model, current docs, nearby source, and existing tests before changing files. Check memory/lessons when the task is a refactor, schema change, debug task, or repeated workflow.

2. Declare the current system model.
   State the current objects, relations, behaviors, events, packs, and boundaries that matter for this increment. Distinguish runtime behavior from agent-pack configuration.

3. Split one incremental task.
   Choose a small task that can be tested and inspected. Keep future work visible, but avoid implementing speculative layers.

4. Write the failing test or eval first.
   Add a focused unit test, CLI regression, eval case, or event-log assertion that would fail before the implementation. If a test is impossible, document the concrete evidence that substitutes for it.

5. Implement the minimal change.
   Follow existing code patterns. Keep runtime-general code below pack-specific behavior. Do not hide a missing deterministic behavior behind an LLM fallback.

6. Validate.
   Run the smallest meaningful test first, then broader tests when the blast radius justifies it. For CLI agents, include at least one smoke command when behavior is user-facing.

7. Capture evidence.
   Preserve the facts needed to inspect the change later: command summaries, event IDs, run IDs, graph before/after, trace files, eval-run outputs, or screenshots.

8. Extract insight.
   Convert evidence into a short explanation of what changed in the system model: new trigger, new graph projection, new failure class, new behavior contract, or rejected assumption.

9. Decide the next state.
   Mark whether the increment is accepted, blocked, deferred, or requires adaptation. If an event-log adaptation is accepted, create explicit eval/system-model/test artifacts before changing behavior.

10. Update system model and learning materials.
    Update the canonical YAML and related docs so the next Coding Agent can reconstruct the current model without reading the whole conversation.

11. Freeze or branch on architecture shifts.
    When the project moves to a new architectural baseline, freeze the old agent as a regression oracle and create a clean successor baseline with compatibility gates.

## Artifact Layout

Prefer this structure unless the repository already has a stronger convention:

```text
artifacts/
  <project>_refactoring_plan.md
  <project>_learning_index.md
  SKILL.md
  cognitive_dev_process.md

cognitive_dev_process/<project>/
  01_system_model.md
  02_implementation_plan.md
  03_tdd_and_evaluation.md
  04_evidence.md
  05_insight.md
  06_decision.md
  07_updated_system_model.md

<agent>/
  FREEZE.md
  README.md
  agent/
    system-model.vNN.yaml
  artifacts/
    <increment>.md
  evals/
    <pack>_cases.jsonl
```

## Stage Entry Template

Use this compact format for each development increment:

```markdown
## vNN: <Increment Name>

**Goal**
Describe the behavior or learning objective.

**System Model Delta**
- Objects:
- Relations:
- Behaviors:
- Events:
- Pack/config:

**TDD/Eval**
- Added:
- Expected failure before implementation:
- Validation command:

**Evidence**
- Tests:
- CLI:
- Event/trace/graph:

**Insight**
What this proves or changes in the model.

**Decision**
Accepted, deferred, rejected, or next increment.
```

## Behavior Rules

- Use TDD-first for followups unless the user explicitly asks for design-only work.
- Record assumptions in artifacts or graph/event state, not only in chat.
- Treat event logs and graph snapshots as first-class evidence.
- Keep deterministic behavior inspectable before adding LLM assistance.
- Use LLM calls as explicit adapters with recorded inputs, outputs, status, and fallback path.
- Keep pack configuration separate from runtime source.
- Put external environment details in config/env surfaces, not hard-coded runtime logic.
- Use approval gates for external KB writes or other user-visible persistent side effects.
- Never overwrite unrelated user changes.
- When behavior changes, update the system model in the same increment.

## Quality Gate

Before finishing, confirm:

- The user-visible behavior is implemented or the blocker is concrete.
- The relevant tests/evals were added or updated.
- Validation was run, or the reason it could not run is stated.
- The system model reflects the new behavior.
- Evidence artifacts are discoverable by path, run ID, eval-run ID, or command.
- Learning docs explain what changed and why.
- Future work is marked as deferred instead of silently omitted.
