---
name: "nano-vllm-cutile-refactor"
version: 0.1.0
description: "Reverse-engineer nano-vLLM, build a lat.md knowledge graph, and refactor GPU kernels to cuTile using Semiformal Design Patterns and outcomes-based gap analysis. This skill turns a complex GPU‑kernel refactoring into a systematic, teachable, and
compounding engineering practice."
metadata:
  author: "taewony <taewony@wsu.ac.kr>"
  tags:
    - cutile
    - gpu-kernels
    - lat
    - knowledge-graph
    - reverse-engineering
    - compounding-engineering
    - metaprogramming
---

# nano‑vLLM → cuTile Refactoring Skill

You are an expert in GPU kernel reverse‑engineering and refactoring. Your mission is to
take the `nano‑vLLM` codebase, understand its architecture, and systematically replace
PyTorch/Triton operations with high‑performance cuTile kernels. You use **lat.md** as your
living knowledge graph and **Semiformal Design Patterns** to make the process
controllable, auditable, and compoundable.

## Core Philosophy

- **Gestalt‑aware context engineering**: every document, annotation, and prompt is
  designed to shape the *foreground* (the immediate task) and *background* (accumulated
  knowledge) of both the human and the LLM.
- **Semiformal Design Patterns**: GPU‑kernel know‑how (coalescing, bank‑conflict
  avoidance, tile‑size selection, online softmax, etc.) is captured as structured,
  reusable patterns with intent, conditions, transformation, and validation.
- **Compounding knowledge**: every successful (or failed) refactoring produces a
  *retrospective* that becomes part of the knowledge graph and reduces the cost of the
  next similar task.
- **Outcomes‑driven gap analysis**: a pre‑written `outcomes.md` describes the target
  cuTile‑based architecture. The distance between the current code and that target is
  bridged by explicit *seams* identified through `lat gap`.

## When to Use This Skill

Invoke this skill when:
- You are starting the nano‑vLLM → cuTile refactoring project.
- You need to map the existing architecture, identify cuTile conversion candidates, or
  tag code with `@lat:` annotations.
- You need to apply a specific GPU‑kernel design pattern to a piece of code.
- You need to run the validation loop for a newly written cuTile kernel.
- You need to check the health of the knowledge graph or compute the gap against the
  desired architecture.

---

## The lat.md Knowledge Graph – Quick Reference

`lat` is a CLI tool that maintains a bidirectional link graph between Markdown documents
and source code. All knowledge – architecture, patterns, retrospectives – lives inside
the `lat.md/` directory.

| Command | Purpose | How you use it |
|---------|---------|----------------|
| `lat init` | Scaffold `lat.md/` and initial config | Run once at the very beginning |
| `lat check` | Validate all wiki links and code `@lat:` refs | Run after any document/code change; fail the build on errors |
| `lat locate "OAuth Flow"` | Find sections by name (exact/fuzzy) | Quickly jump to a section you remember |
| `lat section "arch#Pipeline"` | Display a section with its links and refs | Understand the full context around a topic |
| `lat refs "arch#Pipeline"` | List everything that references a section | Discover which code points are affected by a design change |
| `lat search "how do we auth?"` | Semantic search via embeddings | Explore the knowledge graph conceptually |
| `lat expand "fix [[arch#Pipeline]]"` | Expand `[[wiki links]]` in a prompt for LLM agents | Prepare a context‑rich prompt for code generation |
| `lat mcp` | Start MCP server for editor integration | Use inside an IDE that supports the Model Context Protocol |
| `lat health` | Assess graph quality (isolated sections, depth balance, back‑link coverage) | Periodically check that the knowledge graph remains a “good gestalt” |
| `lat gap` | Compare current code annotations against an `outcomes.md` target and list missing/different seams | The primary tool for gap analysis; run before each refactoring batch |
| `lat diff <section>` | Show the propagation impact of changing a section | Evaluate risk before modifying a pattern or architecture decision |

For detailed CLI help, run `lat --help` or `lat <command> --help`.

---

## Project Workflow

### Phase 0: Initialization & Outcome Description

1. **Initialize the knowledge graph**
   ```bash
   cd nano-vllm-cutile
   lat init
   ```
   This creates the `lat.md/` directory.

2. **Write the target architecture – `outcomes.md`**
   Create `lat.md/outcomes.md`. It should describe the *desired* cuTile‑based system at a
   high level, using the same section IDs you will later use in `@lat:` annotations.
   Example fragment:
   ```markdown
   # Desired Architecture (cuTile)

   ## Inference Pipeline [[pipeline]]
   All compute is executed through `@ct.kernel` functions.
   Scheduler still uses CPU, but all GPU ops are pure cuTile.

   ## Attention [[attention]]
   - Flash‑Attention implemented in cuTile with online softmax.
   - KV‑cache reads/writes use `ct.load`/`ct.store` directly on the cache tensor.

   ## MLP [[mlp]]
   - Linear layers replaced by cuTile matmul + fused activation.
   - SwiGLU is a single fused cuTile kernel.

   ## Normalization [[norm]]
   - LayerNorm & RMSNorm as cuTile reduction + element‑wise kernels.
   ```

   This document is the “foreground” of your long‑term goal. Everything else is a step
   toward it.

### Phase 1: Reverse‑Engineering (Building the Current‑State Graph)

1. **Document the existing architecture**
   Create `lat.md/architecture.md`, `lat.md/scheduler.md`, `lat.md/model-runner.md`,
   `lat.md/kv-cache.md`, `lat.md/triton-kernels.md`, etc. Use `[[wiki links]]` to connect
   them. Each section should explain *why* something exists, not just *what* it is.

2. **Annotate the source code**
   For every key function/class, add `@lat:` comments that link back to the relevant
   sections.
   ```python
   # @lat: [[scheduler#Waiting Queue]]
   class Scheduler:
       ...
   ```

3. **Run `lat check`** to ensure all links are valid.

### Phase 2: Gap Analysis – Seam Identification

1. **Run `lat gap`**
   ```bash
   lat gap
   ```
   This compares the current code annotations (from Phase 1) against the target sections
   defined in `outcomes.md`. It will output a list of *seams*: pieces of code that need
   to change, new sections that need to be introduced, or sections that are no longer
   required.

   For each seam you will see:
   - **MISSING**: a target section has no corresponding `@lat:` annotation in the code.
   - **MISMATCH**: the code references the current architecture but the target describes
     a different pattern.
   - **EXTRA**: code annotations that do not map to any target section (legacy code to be
     removed).

2. **Record seams in `lat.md/seams.md`**
   Structure the seam list as a set of actionable items, each linking back to the target
   section and the current code location. Example:
   ```markdown
   ## Seam: Attention uses Triton, must become cuTile [[seam-attn]]
   - Target: [[outcomes.md#attention]]
   - Current: [[triton-kernels#Flash Attention Forward]]
   - Code: `nano_vllm/kernels/attention.py:45`
   - Suggested pattern: [[patterns/online-softmax]]
   ```

3. **Prioritize seams**
   Focus on the seams that affect the largest portion of the overall inference time
   (attention, then matmul, then normalization, etc.). This is the gestalt‑aware
   equivalent of Amdahl’s law.

### Phase 3: Pattern‑Driven Refactoring

For each seam (in priority order):

1. **Retrieve relevant patterns**
   Use `lat search "bank conflict"` or `lat expand "fix [[seam-attn]] with [[patterns/online-softmax]]"` to build a context‑rich prompt for the coding agent.

2. **Implement the cuTile kernel**
   - Use the existing `SKILL.md` for cuTile Python (`cutile-python` skill) to generate
     the kernel code.
   - The kernel must follow the *pure cuTile forward path* rule: every compute op goes
     through `@ct.kernel` + `ct.launch`.
   - All tile dimensions must be powers of 2, constants must be typed, etc.

3. **Validate**
   Run the kernel with a PyTorch reference. If validation fails, apply the debugging
   patterns (check tile indices, bank conflicts, register spilling) and try again. The
   loop continues until `PASS`.

4. **Commit the change and update the knowledge graph**
   - Replace the old code, update `@lat:` annotations to point to the new cuTile kernel
     section (e.g., `[[cutile-kernels#FMHA]]`).
   - Create or update the corresponding section in `lat.md/cutile-kernels.md`.

5. **Record a retrospective**
   Create `lat.md/retrospectives/<seam-name>.md` with:
   - Applied patterns (links).
   - What worked / what failed.
   - Concrete lessons learned.
   Example:
   ```markdown
   ## Retrospective: FMHA cuTile conversion
   - **Seam**: [[seam-attn]]
   - **Applied patterns**: [[patterns/online-softmax]], [[patterns/tile-size-selection]]
   - **Insight**: BLOCK_M=128 caused register spill; staying at 64 gives 95% occupancy.
   - **Compounding hint**: For MLP, also start with conservative block sizes.
   ```

6. **Verify health**
   Run `lat check` and `lat health` periodically to ensure the graph stays navigable and
   the gap is shrinking.

### Phase 4: Final Integration & Validation

1. Once all seams are closed (i.e., `lat gap` shows no more missing/mismatched items),
   run the full model end‑to‑end with a reference implementation.
2. Update `outcomes.md` if any target had to be adjusted during the refactoring (this
   keeps the compass accurate).
3. Produce a summary report with:
   - Number of seams closed.
   - Average validation‑loop iterations per seam.
   - Patterns reused across seams (compounding evidence).
   - End‑to‑end speedup.

---

## Agent‑Specific Instructions (for Gemini CLI)

- **Always start** a new task by running `lat check` and `lat gap` to understand the
  current state.
- When generating code, use `lat expand` to inject the relevant pattern pages directly
  into your prompt. This is how you turn semiformal patterns into executable context.
- After every file change, re‑run `lat check` to ensure you haven’t broken the graph.
- Use `lat diff "patterns/online-softmax"` before modifying a pattern to see which seams
  will be affected.
- **Never** modify the original `nano‑vLLM` code directly; always work on a separate
  branch and only touch files that are part of the seam.

---

## Important Constraints

- The `lat.md/` directory is **read‑only** for the refactoring agent except for the
  `retrospectives/` folder and the `seams.md` file.
- All generated cuTile kernels must go into the project source tree (e.g.,
  `nano_vllm/cutile_kernels/`), never into `lat.md/`.
- Do not delete any existing `@lat:` annotation unless the corresponding code is being
  replaced by a cuTile equivalent and the new annotation is already in place.

---

## Success Criteria

1. ✅ `lat gap` reports zero missing/mismatched seams.
2. ✅ All cuTile kernels pass validation against PyTorch reference.
3. ✅ End‑to‑end inference speedup is measurable and documented.
4. ✅ The knowledge graph (`lat.md/`) remains consistent (`lat check` passes).
5. ✅ At least one pattern was reused across multiple seams, demonstrating compounding.