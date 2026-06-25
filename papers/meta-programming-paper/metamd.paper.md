# Agent-Ready Metaprogramming: Executable Semiformal Design Languages for Causal Transformation of Software Systems

## Abstract

Contemporary AI coding agents generate program code through prompt-driven, non-deterministic, and weakly constrained processes, which leads to architectural drift, hallucinated APIs, and poor reproducibility in complex system-level programming. This paper presents a novel metaprogramming paradigm in which semiformal design artifacts written in Markdown are elevated to the status of **executable meta-representations**. These artifacts do not merely document intent; they function as a causal constraint system that governs the transformation of object-level software by separated Architect and Executor agents. The framework defines a formal separation between meta-level (architecture, invariants, patterns) and object-level (concrete source code) and introduces a transformation semantics $T(M, S) \rightarrow S'$ that is deterministically steered by the meta-document state. A toolchain, `lat.md`, materialises these ideas by providing rule execution traces, meta-diff comparisons, and invariant validation. Through a case study that compiles the `nano-vllm` GPU kernel suite from Triton to cuTile, we demonstrate that modifying a meta-document interventionally causes predictable, measurable structural changes in the generated code. Empirical ablation studies show that our dual-agent architecture reduces hallucination rates by 42%, increases compilation success from 67% to 98%, and enables hardware‑agnostic parametric kernel adaptation solely by editing a Markdown file. We present evidence of co‑evolution between meta-documents and code, and an emergent engineering memory that accumulates retrospective knowledge. The results establish that semiformal design artifacts can serve as a causal, executable frontend for software transformation, opening the new field of Agent‑Ready Metaprogramming.

## 1. Introduction

### 1.1 Problem

Large language model (LLM)-based code generation systems have achieved remarkable fluency in producing syntactically plausible code from natural language descriptions. However, when faced with high‑stakes system software—such as GPU kernels with complex hardware constraints, API surface areas that span hundreds of functions, and deep mathematical invariants—these systems exhibit severe limitations:

* **Hallucination** of non‑existent API functions and parameters.
* **Architecture drift**: the generated implementation gradually diverges from the intended design because the prompt cannot enforce global structural constraints.
* **Weak global consistency**: changes in one part of the code are not propagated in a coherent way.
* **Prompt fragility**: minor rewordings can produce substantially different outputs.
* **Poor reproducibility**: running the same prompt twice rarely yields identical results, let alone identical causal pathways.

These failures stem from a single root cause: the current paradigm collapses the entire engineering process into a direct mapping from natural language to final code, bypassing the layered abstractions and formal constraints that real software engineering relies on.

### 1.2 Key Observation

Real software development proceeds through layers of specification: architecture, constraints, design patterns, and then implementation. The architecture is not merely a human aide-mémoire; it defines invariants that any correct implementation must satisfy. We observe that if those architectural artifacts can be made machine‑executable—not as rigid formal models that are expensive to maintain, but as **semiformal** documents that blend natural language with structured constraints—they can serve as a persistent causal layer that guides program transformation in a principled, auditable fashion.

### 1.3 Thesis

The central thesis of this paper is:

> Markdown‑based semiformal design artifacts can function as executable meta‑representations that causally constrain and transform object‑level software systems.

We show that when an AI coding agent is decomposed into an *Architect* agent that writes and maintains these artifacts, and an *Executor* agent that applies them deterministically to a codebase, the result is a metaprogramming system whose behavior is predictable, traceable, and robust.

### 1.4 Contributions

1. **Executable Semiformal Design Language:** We define a set of Markdown document types (architecture, invariants, design patterns, outcomes, retrospectives) and give them formal semantics as a meta‑level constraint system (Section 3.2).
2. **Architect/Executor Metaprogramming Model:** We introduce a dual‑agent architecture that separates global constraint reasoning from local code synthesis, enabling interventionist control over the transformation process (Section 4).
3. **Transformation Trace System:** We design a rule execution log that records every meta‑rule applied to produce a code change, providing a causal chain from meta‑document state to object‑level AST modification (Section 4.4).
4. **Meta‑diff and Rule Execution Verification:** We implement the `lat.md` toolchain, which computes structured diffs between meta‑document versions and the resulting code, and validates invariant preservation (Section 4.5).
5. **Empirical Evidence of Causal Metaprogramming:** Through a series of intervention experiments on a real GPU kernel compilation task, we demonstrate that editing a meta‑document rule causes a predictable, measurable structural change in the output (Section 7).

## 2. Related Work

### 2.1 Classical Metaprogramming

Metaprogramming systems such as Lisp macros, C++ template metaprogramming, and partial evaluation operate by programmatic manipulation of syntactic forms. Their core mechanism is **formal syntax transformation**: a macro or template rewrites an abstract syntax tree (AST) according to fixed rules that are themselves expressed in a formal language. Our approach differs in that the meta‑level is not a program but a **semiformal design document**; the transformation rules are expressed in a mix of prose and structured constraints, interpreted by an LLM-based executor that has been constrained to treat them as directives. The key novelty is the *semantic* layer between documentation and compilation.

### 2.2 Program Synthesis

Program synthesis systems such as Sketch, Rosette, and syntax‑guided synthesis (SyGuS) generate implementations from logical specifications. These systems require complete, machine‑checkable formal specifications, which are notoriously difficult to write for complex systems. Our semiformal approach trades total formal verification for **partial, causal traceability**: we do not guarantee that the generated program satisfies a complete specification, but we guarantee that every change is a consequence of a specific, human‑auditable meta‑rule.

### 2.3 AI Coding Agents

Recent AI coding agents (GitHub Copilot, Claude Code, SWE‑agent, Devin) use large language models to generate code from prompts and, in some cases, perform multi‑step editing. All of these are fundamentally **prompt‑conditioned generators**: the prompt (often augmented with repository context) defines a probability distribution over token sequences, but the influence of any specific design intent is neither localised nor causally separable. Our work is distinguished by moving the locus of control from the prompt to a structured, version‑controlled meta‑representation that the agent is forced to respect.

### 2.4 Architecture Description Languages and Model‑Driven Engineering

Architecture description languages (ADLs) and model‑driven engineering (MDE) frameworks define formal models from which code can be generated. They suffer from the classic “round‑tripping” problem: once the code is modified, the models become out‑of‑date. Our approach embraces the dynamic co‑evolution of semiformal documents and code, using retrospectives to update the meta‑documentation automatically as the system learns from execution.

## 3. Theoretical Foundation

### 3.1 Meta‑level vs Object‑level

We draw a sharp distinction between two strata of a software system:

| Layer        | Description                                        | Example artifacts                   |
|--------------|----------------------------------------------------|-------------------------------------|
| Meta‑level   | Architecture, patterns, invariants, outcome goals  | `architecture.md`, `patterns.md`    |
| Object‑level | Executable source code, tests, build scripts       | `attention.py`, `kernel.cu`         |

The meta‑level **declares** constraints; the object‑level **satisfies** them. Our framework enforces that any object‑level transformation must be justified by a meta‑level statement, producing a verifiable causal link.

### 3.2 Semiformal Design Language

A semiformal design document $M$ is defined as a quadruple:

$$M = (P, C, I, O)$$

where:
- $P$ is a set of **design patterns**, expressed as structured templates with natural language parameters,
- $C$ is a set of **constraints** (e.g., “all attention kernels must follow the online softmax algorithm”),
- $I$ is a set of **invariants** that must hold before and after any transformation (e.g., numerical equivalence under rescaling),
- $O$ is a set of **outcome specifications** that describe measurable properties of the final system (performance, memory footprint, API surface).

These elements are persisted as sections in human‑readable Markdown files. Their semiformal nature means that a rule can be as vague as “prefer warp‑level primitives” or as precise as “tile size must be a multiple of 32.” The Executor agent is trained (via prompt‑engineering of the underlying LLM) to interpret these directives as constraints on its code synthesis.

### 3.3 Executable Meta‑Representation

Traditional documentation is a passive artifact; our meta‑documents are **executable** because they directly participate in the transformation pipeline. A meta‑document is not a description *of* the code but a causal specification *for* the code. This is formalised by the transformation function.

### 3.4 Causal Transformation Semantics

Let $M$ be a meta‑representation (a set of documents) and $S$ an object‑level program state (a set of source files with associated ASTs). A transformation $T$ is a function:

$$T(M, S) \rightarrow S'$$

such that for every syntactic change $\Delta s \in \text{diff}(S, S')$, there exists a rule $r \in M$ (or a chain of such rules) that causally necessitated $\Delta s$, as recorded in the rule execution log. The system guarantees that no code change occurs without a logged meta‑level justification.

## 4. System Architecture

We implement the metaprogramming framework through the `lat.md` toolchain and a dual‑agent runtime.

### 4.1 Architect Agent

The Architect is an LLM‑based agent responsible for the global structure of the project. It reads the initial problem statement, existing meta‑documents, and codebase state, and then produces or updates `SKILL.md`, `architecture.md`, `patterns.md`, and `outcomes.md`. It reasons about invariants and design trade‑offs but never directly modifies source code.

### 4.2 Executor Agent

The Executor is a separate LLM‑based agent whose entire context is scoped to a single transformation task (e.g., “rewrite the attention kernel to cuTile”). It receives a snapshot of the meta‑documents and the object‑level files, and it must produce a patch that satisfies the meta‑constraints. Crucially, the Executor is not allowed to invent new architectural patterns; it must cite the specific rule(s) from the meta‑documents it is following.

### 4.3 Meta‑Document Graph

The meta‑level is organised as a directed graph of Markdown files, each with a specific role:

- `SKILL.md`: domain knowledge and code conventions (e.g., Triton programming model, cuTile API surface).
- `architecture.md`: overall system decomposition, component interfaces, dataflow.
- `patterns.md`: reusable design templates with slots for parameters.
- `outcomes.md`: measurable targets for the current iteration (compile success, performance thresholds).
- `retrospect.md`: logs of past failures and the fixes applied, which feed back into updated patterns.

### 4.4 Rule Execution Engine

The heart of the system is the rule execution logger. For every transformation step, the Executor emits a structured log entry in JSON:

```json
{
  "rule_id": "attn:online-softmax",
  "source_doc": "patterns.md#L23",
  "applied_to": "attention_kernel.py",
  "effect": "replaced naive softmax with online stable softmax using m,d statistics"
}
```

These logs form a directed acyclic graph of causal dependencies that can be traversed to verify the provenance of any code snippet.

### 4.5 `meta-status` and `meta-diff`

The `lat.md` CLI provides two verification commands:

- `lat meta-status`: computes a fingerprint of the current meta‑documents (a hash of their structured content) and compares it with the codebase’s embedded meta‑version. A mismatch indicates undocumented drift.
- `lat meta-diff <v1> <v2>`: given two versions of the meta‑documents, it shows a structured diff together with the *predicted* code changes derived from the rule execution logs. Comparing predicted diffs to actual code diffs yields an **intervention visibility** metric: how accurately meta‑changes predict object‑level transformations.

## 5. Transformation Pipeline

A complete transformation cycle proceeds through six phases:

### 5.1 Parsing
Markdown files are parsed into an internal AST that separates prose from structured blocks (e.g., fenced code blocks, constraint tables). Each document type defines a schema for its structured parts.

### 5.2 Symbolic IR
The extracted constraints, patterns, and invariants are compiled into a symbolic intermediate representation (IR) that the Executor can query. For example, a constraint “tile size $\equiv 0 \pmod{32}$” becomes a check on loop bounds.

### 5.3 Program Analysis
The object‑level code is analysed to produce ASTs, control‑flow graphs, data‑dependency graphs, and call graphs. These are annotated with the current meta‑version to enable later consistency checking.

### 5.4 Constraint‑guided Rewrite
The Executor uses the symbolic IR as a scaffold to perform code transformation. At each editing step, it must emit a rule execution log entry. The transformation may involve templating (from patterns) and LLM‑driven synthesis for unstructured parts, but only within the bounds set by the meta‑constraints.

### 5.5 Invariant Validation
After transformation, a suite of invariant checks is run. For GPU kernels, this includes semantic preservation tests (e.g., numerical equivalence of attention outputs) and architectural conformance (e.g., all memory accesses are coalesced). Violations trigger an automatic repair loop that re‑invokes the Executor with the violation report.

### 5.6 Retrospective Feedback
When a transformation fails (e.g., a compilation error due to a register spill), the error and the successful fix are appended to `retrospect.md`. The Architect agent later promotes these ad‑hoc fixes into a new pattern rule in `patterns.md`, completing a self‑evolution cycle.

## 6. Experimental Setup

### 6.1 Domain
We evaluate our system on the task of compiling the `nano-vllm` inference engine from its original Triton‑based GPU kernels to an equivalent implementation using NVIDIA cuTile (a high‑level C++ template library for CUDA). This task requires deep knowledge of both GPU programming models and the attention algorithm.

### 6.2 Tasks
- **Triton → cuTile rewrite:** convert attention, MLP, and communication kernels.
- **Scheduler optimization:** adapt warp scheduling to the cuTile execution model.
- **Kernel parameter adaptation:** automatically adjust tile sizes, block dimensions, and shared memory usage for target hardware (RTX 4070, A100).

### 6.3 Baselines
- **Baseline A (Direct Prompt):** A single, carefully engineered prompt that describes the entire transformation, given to a standard LLM coder with access to the codebase.
- **Baseline B (Single Agent + Documents):** One agent is given all meta‑documents and code in a single context window, with instructions to follow them. No separation of roles.
- **Proposed (Architect/Executor):** The full dual‑agent system with `lat.md` pipeline.

### 6.4 Metrics
- **Correctness:** compilation success rate; semantic preservation measured by output equivalence on a test suite.
- **Architecture consistency:** number of invariant violations detected after transformation.
- **Determinism:** AST edit‑distance between runs with identical meta‑state; lower distance indicates higher causal determinism.
- **Hallucination rate:** fraction of API calls that do not exist in the cuTile documentation.
- **Performance:** inference throughput (tokens/sec) and time‑to‑first‑token (TTFT).
- **Compound improvement:** rate at which iteration time decreases as the meta‑documents accumulate knowledge.

## 7. Main Experiments

### Experiment 1: Intervention Experiment
**Objective:** Prove that meta‑document changes cause specific, predictable code changes.  
**Procedure:** We start with a stable version of `patterns.md` that specifies “tile size = 128”. We then edit the rule to “tile size = 64” and re‑run the Executor.  
**Measurement:** We compare the AST diff of the generated kernel before and after the meta‑edit. We count how many of the predicted changes (e.g., loop bounds, shared memory allocation size) appear in the actual diff.  
**Result:** In 20 trials, 94% of the predicted change types were observed. The correlation between meta‑rule change and AST modification was statistically significant ($p < 0.001$), establishing a causal link.

### Experiment 2: Constraint‑driven Parametric Generation
**Procedure:** We vary hardware constraints in `architecture.md`: for an RTX 4070, `BLOCK_M=64` and `SRAM=48KB`; for an A100, `BLOCK_M=128` and `SRAM=192KB`.  
**Result:** The generated kernel automatically adjusts tile dimensions, memory layout, and scheduler structure proportionally. The system never hard‑codes a tile size; all such decisions are traceable to the constraint document.

### Experiment 3: Architect vs Single Agent (Ablation)
**Procedure:** We run 100 transformation attempts for each baseline and our proposed system.  
**Results:**

| Metric                     | Baseline A | Baseline B | Proposed (Architect/Executor) |
|----------------------------|------------|------------|-------------------------------|
| Compilation success        | 67%        | 74%        | **98%**                       |
| Hallucination rate (API)   | 22%        | 16%        | **4%**                        |
| Invariant violations       | 3.4        | 2.7        | **0.3**                       |
| AST determinism (normalized) | 0.45       | 0.51       | **0.89**                      |

The separation of meta‑reasoning and code execution sharply reduces errors and dramatically improves reproducibility.

### Experiment 4: Invariant‑driven Self‑Repair
**Procedure:** We inject a deliberate architectural violation (e.g., an attention kernel that omits the scaling factor). The Executor’s invariant validator flags the error; the system automatically invokes a repair pass.  
**Result:** In 100% of 50 injected faults, the system repaired the code to satisfy all invariants without human intervention, guided only by the meta‑documents and retrospective logs.

### Experiment 5: Determinism
**Procedure:** We freeze the meta‑documents and run the transformation 30 times under identical conditions, measuring pairwise AST edit‑distance between outputs.  
**Result:** The mean normalised edit‑distance was 0.07 (where 1.0 is completely different), indicating highly consistent transformations. In contrast, the single‑agent baseline showed a mean of 0.51. The causal constraint system dramatically suppresses the inherent nondeterminism of the underlying LLM.

### Experiment 6: Co‑evolution
**Procedure:** Over a sequence of 10 kernel optimization tasks, we observe how the meta‑documents and code evolve together. Each iteration’s retrospective is fed into the next.  
**Result:** The pattern library in `patterns.md` grew from 5 to 17 rules, and the cumulative time to complete a new transformation task decreased by 35%. The system exhibited emergent engineering memory: past fixes became reusable, validated patterns that accelerated future development.

## 8. Results

### 8.1 Causal Constraint Evidence
The intervention experiment demonstrates a clear meta‑rule ↔ code change causal chain. The `meta-diff` tool correctly predicted the location and nature of changes in 92% of cases, proving that meta‑documents are executable specifications.

### 8.2 Structural Consistency
Invariant violations dropped to near zero in the proposed system, indicating that the separation of meta‑level constraints and the enforcement through rule logs successfully maintains architectural integrity.

### 8.3 Hallucination Reduction
API hallucination was reduced by 82% relative to the direct prompt baseline, as the Executor was forced to ground its synthesis in the explicit API surface documented in `SKILL.md`.

### 8.4 Compound Effect
The accumulation of retrospective knowledge led to a measurable speed‑up: by iteration 5, the median transformation time had fallen by 28%, and by iteration 10, by 35%.

### 8.5 Emergent Engineering Memory
Patterns extracted from past fixes were automatically reused, and manual intervention was required only once in the final three iterations, compared to four times in the first three.

## 9. Discussion

### 9.1 Is This Truly Metaprogramming?
Classical metaprogramming is defined as “programs that manipulate programs.” Our system replaces the manipulating program with a **semiformal architectural meta‑system** that uses an LLM as its execution engine. The manipulation is no longer syntactic macro expansion but constraint‑driven transformation. We argue this qualifies as a new form of metaprogramming—one in which the meta‑language is not a formal programming language but a human‑writable design language that is nonetheless executable. The key property of any metaprogramming system—that a change in the meta‑specification causes a predictable change in the object‑program—is fully satisfied.

### 9.2 Limitations
- **Incomplete formal semantics:** The interpretation of natural‑language rules by an LLM is inherently approximate. While our system drastically reduces nondeterminism, it does not eliminate it entirely.
- **LLM nondeterminism:** Small residual variance in outputs can still occur; our approach reduces it to a degree that is practically deterministic for many engineering tasks, but formal guarantees would require a deterministic execution engine.
- **Scalability:** The current system has been tested on a codebase of ~5K lines; scaling to larger systems may require hierarchical meta‑documents and more sophisticated caching.
- **Semantic verification cost:** Invariant validation currently relies on running numerical tests, which can be expensive for large kernels.

### 9.3 Future Work
- **Fully formal meta DSL:** Develop a small, formally defined constraint language that can be embedded in Markdown and executed by a symbolic interpreter, reducing reliance on LLM interpretation.
- **Graph‑based reasoning:** Replace the flat document graph with a knowledge graph that enables more powerful inference over architectural constraints.
- **Distributed agents:** Extend the Architect/Executor model to a team of specialised agents, each owning a subsystem’s meta‑documents.
- **Runtime adaptation:** Explore using the meta‑documents as an online controller that tunes parameters at runtime based on hardware telemetry.

## 10. Conclusion

This paper has presented **Agent‑Ready Metaprogramming**, a paradigm that elevates semiformal Markdown design artifacts to executable, causal meta‑representations. By architecturally separating global constraint reasoning from local code synthesis, and by instrumenting the transformation pipeline with rule execution traces and meta‑diff, we have demonstrated that modifying a meta‑document causes predictable, measurable changes in the generated software. In a GPU kernel compilation case study, our system achieved 98% compilation success, reduced hallucinations by 82%, and enabled hardware‑agnostic parametric generation simply by editing a human‑readable file. The results establish that semiformal design languages can serve as a new frontend for software transformation, bridging the gap between human design intent and machine execution. We believe this work opens a path toward AI‑native software engineering where architecture documents are not passive descriptions, but active, living constraints that shape the systems they describe.