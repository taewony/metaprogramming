# ch09_text_to_sql Design Note

## Purpose

This module is a direct conversion of `ch09_text_to_sql.ipynb` into a
scripted, reviewable form.

The original notebook was a hospital-domain Text-to-SQL demo using:

- an in-notebook SQLite database
- `llama_index` `FunctionAgent`
- a single `db_query` tool
- a Gradio chat UI
- manual multi-turn prompt stitching

The converted script keeps the same behavior while making the code easier
to run, diff, and extend.

---

## Architecture

### Runtime flow

`user question -> LLM agent -> SQL tool call -> SQLite result -> answer`

This is a direct Text-to-SQL agent, not a planner IR pipeline.

### Main components

- `hospital_schema`: DDL for the hospital database
- sample data blocks: seed rows for doctors, patients, appointments, and related tables
- `create_hospital_db()`: builds the temporary SQLite database
- `db_query()`: executes SQL against the database
- `system_prompt`: tells the agent how to behave
- `FunctionAgent`: chooses whether to call the DB tool
- `run_agent_verbose()`: streams tool calls and prints them
- `chat_handler()`: Gradio chat callback with manual conversation memory

---

## Design Characteristics

### 1. Direct tool-using agent

The LLM writes SQL directly and invokes `db_query`.

This is simple and flexible, but it is not strongly typed.

### 2. Prompt-based multi-turn memory

Conversation history is concatenated into a single prompt string.

This is easy to inspect, but it is weaker than a structured dialogue state.

### 3. Notebook-to-module conversion

The converted script removes notebook-specific execution order and turns
the cells into functions.

That improves:

- reproducibility
- code reviewability
- testability
- CLI execution

### 4. Demo-first execution model

The script keeps the notebook behavior:

- default mode: run the five sample queries
- `--serve`: launch the Gradio UI

---

## What this design is good at

- quick hospital-domain Text-to-SQL prototyping
- manual inspection of tool calls
- lightweight conversational demoing
- showing the behavior of a direct agent loop

---

## What this design does not do

- no planner IR
- no structured query contract
- no separate SQL compilation stage
- no formal benchmark scorer
- no backend-agnostic KB planning

---

## Relationship to KnowledgeChef

This notebook-derived module is useful as a baseline, but it is not the
same architecture as the KnowledgeChef planner pipeline.

KnowledgeChef uses:

- planner IR generation
- explicit ambiguity resolution
- deterministic compilation
- saved JSON artifacts
- separated evaluation layers

This notebook uses:

- direct SQL generation in the agent loop
- conversational prompt memory
- immediate execution through one tool

The difference matters for evaluation:

- notebook style is easier to prototype
- KnowledgeChef style is easier to benchmark and debug

---

## Suggested future extension

If this module becomes a production path, the next step would be to split
the flow into:

1. planner
2. SQL compiler
3. executor
4. scorer

That would make it comparable to the rest of KnowledgeChef’s evaluation
stack.

