# Paper 2 Draft: ActiveGraph Educational Knowledge Agent

**Working title:** ActiveGraph Educational Knowledge Agent: Event-Sourced Knowledge Organization and Retrieval for Executable Systems Learning

**Author:** Taewon Kim

**Draft status:** Planning draft. This manuscript assumes the educational knowledge-agent prototype, OKF course bundles, retrieval evaluation, learner-task evaluation, and trace-inspection study are completed successfully. Numeric values marked `[ASSUMED]` are placeholders for final measured values.

## Abstract

Educational LLM agents often answer questions as opaque chat systems: they retrieve context, generate explanations, and sometimes execute code, but students and instructors cannot easily inspect why a source was selected, what evidence supported an answer, which tool action was performed, or how a failed attempt changed the agent's next behavior. This paper presents **ActiveGraph Educational Knowledge Agent**, an event-sourced educational agent architecture for organizing, retrieving, executing, and evaluating technical knowledge. The system represents course material as Open Knowledge Format (OKF) bundles, projects user questions and runtime events into an inspectable graph, and records every retrieval, answer, tool call, evaluation, correction, and learning artifact as an append-only event.

We instantiate the system in a CUDA Python and LLM inference-engine course centered on micro-vLLM and nano-vLLM. Students ask questions about CUDA kernels, KV cache, prefix caching, Green Contexts, and inference-engine bottlenecks. The agent retrieves OKF concepts, assembles grounded context, optionally runs executable checks such as unit tests, benchmarks, or CUDA smoke tests, and returns answers with evidence links. In an assumed successful evaluation, the ActiveGraph agent improves citation correctness from `[ASSUMED: 68%]` to `[ASSUMED: 91%]`, reduces unsupported claims by `[ASSUMED: 45%]`, and improves learner task-completion rate by `[ASSUMED: 18 percentage points]` compared with a baseline RAG chatbot. The contribution is not a new retrieval model alone, but a full educational evidence loop: knowledge organization, retrieval, graph projection, action, evaluation, reflection, and updated learning material.

## Keywords

Educational agents, knowledge organization, information retrieval, ActiveGraph, OKF, event sourcing, learning analytics, CUDA Python, nano-vLLM, executable education

## 1. Introduction

Technical education increasingly depends on complex artifacts: source code, benchmarks, papers, API documentation, execution logs, diagrams, and instructor rubrics. In topics such as CUDA kernel programming or LLM inference engines, understanding comes from connecting concepts across layers: memory hierarchy, kernel launch behavior, attention algorithms, KV cache layout, batching, profiling, and performance trade-offs.

LLM-based educational assistants can help students navigate this complexity, but ordinary chat interfaces have a structural limitation. They tend to hide the evidence chain. A student sees an answer, but not the retrieved concept graph, rejected sources, tool calls, validation results, or the reason the agent changed its plan. For instructors, this opacity makes it difficult to audit misconceptions, detect weak course materials, or evaluate whether the agent teaches grounded reasoning.

This paper proposes an event-sourced alternative. ActiveGraph Educational Knowledge Agent treats an educational interaction as a sequence of events projected into a graph. Course knowledge is stored in OKF bundles. Retrieval results become graph objects. Answers cite retrieved concepts and executable evidence. Student corrections and failed tool calls become learning signals. The same trace can be replayed, inspected, evaluated, and converted into updated course material.

The target domain is CUDA Python and LLM inference-engine education. This domain is intentionally difficult: students must understand both conceptual content and executable systems behavior. We use micro-vLLM and nano-vLLM as artifacts for teaching fixed-context LLM serving, prefix KV caching, Green Contexts, allocator behavior, and kernel migration.

## 2. Research Questions

**RQ1.** Does representing course knowledge as OKF bundles improve retrieval inspectability and evidence-grounded answers compared with unstructured RAG over the same material?

**RQ2.** Does projecting educational interactions into an event-sourced graph improve instructor and student ability to inspect reasoning, diagnose failure, and recover from misconceptions?

**RQ3.** Can executable evidence, such as tests, benchmarks, and trace files, improve answer correctness and student task completion in systems-programming education?

**RQ4.** Can fixed-context serving optimizations, such as prefix KV-cache reuse, make local educational agents practical on Windows-native consumer GPU environments?

## 3. Contributions

1. **Educational knowledge organization model.** We define an OKF-based structure for course concepts, procedures, examples, exercises, policies, rubrics, failures, and decisions.

2. **Event-sourced educational agent architecture.** We model questions, retrieved concepts, context snapshots, tool calls, answers, evaluations, corrections, and learning-material updates as graph objects and append-only events.

3. **Executable systems-learning workflow.** We show how the agent grounds CUDA and inference-engine explanations in runnable checks, such as kernel correctness tests, micro-vLLM benchmarks, and trace inspection.

4. **Evaluation protocol.** We define retrieval, grounding, learning, and runtime metrics for comparing the ActiveGraph agent against baseline chat/RAG assistants.

5. **Fixed-context inference link.** We connect the educational agent workload to the micro-vLLM prefix-cache paper, showing that course agents repeatedly reuse static system prompts, rubrics, schemas, and OKF context.

## 4. Background and Motivation

### 4.1 Knowledge Organization for Agentic Education

A course is not only a sequence of lectures. It is a knowledge system consisting of concepts, examples, procedures, assignments, misconceptions, rubrics, and evidence. Traditional documents organize this material for human reading, but LLM agents require machine-navigable structure. OKF is useful because it represents knowledge as Markdown files with YAML frontmatter, making it readable by humans, versionable in Git, and parseable by agents.

### 4.2 Event-Sourced Graphs

In ActiveGraph-style systems, the event log is the source of truth and the graph is a projection. This distinction matters in education. The graph may show that a student question mentions `prefix caching`, retrieves `KV cache`, and triggers a `benchmark explanation` behavior. If the answer is wrong, the event log can reveal whether the failure came from retrieval, context assembly, answer synthesis, or missing course material.

### 4.3 Executable Knowledge

For systems topics, an answer should not rely only on prose. A claim about CUDA Graphs, Green Contexts, or prefix caching should connect to executable evidence where possible: benchmark output, unit tests, profiling traces, source-code references, or inspectable graph states. This paper treats executable evidence as part of the knowledge system.

## 5. System Overview

The architecture has five layers.

```text
Student / Instructor
  -> Educational Agent CLI or UI
  -> ActiveGraph Runtime
  -> OKF Context Resolver + Tool Executor
  -> Event Store + Learning Artifact Store
```

### 5.1 OKF Course Bundle

The course bundle is organized as follows.

```text
okf-course-cuda-vllm/
  index.md
  concepts/
    cuda-memory-hierarchy.md
    tiled-matmul.md
    online-softmax.md
    kv-cache.md
    paged-attention.md
    prefix-kv-cache.md
    green-contexts.md
    allocator-thrashing.md
  procedures/
    debug-kernel.md
    run-benchmark.md
    interpret-profile.md
    explain-inference-trace.md
  exercises/
    matmul-tile-size.md
    fmha-causal-mask.md
    prefix-cache-measurement.md
    green-context-tradeoff.md
  rubrics/
    evidence-grounded-answer.md
    kernel-correctness.md
    performance-analysis.md
  failures/
    wrong-join-between-concepts.md
    unsupported-claim.md
    benchmark-misinterpretation.md
    code-without-test.md
  decisions/
    adr-001-use-windows-native-cuda-python.md
    adr-002-use-micro-vllm-as-educational-artifact.md
```

Each concept file includes title, type, tags, prerequisites, source links, verification status, and relationships to other concepts. Markdown bodies provide explanations, diagrams, code snippets, and examples.

### 5.2 Graph Object Model

The runtime projects interactions into graph objects.

| Object | Meaning |
| :--- | :--- |
| `learner_session` | One student or classroom session |
| `question` | Student prompt |
| `okf_concept` | Retrieved course concept |
| `context_snapshot` | Selected context passed to the LLM |
| `tool_call` | Test, benchmark, schema read, source read, or inspect action |
| `evidence` | Trace, result, source citation, benchmark, or graph output |
| `answer` | Agent response with citations |
| `misconception` | Detected misunderstanding or unsupported claim |
| `rubric_grade` | Evaluation of answer or student task |
| `learning_artifact` | Updated note, exercise, dashboard, or explanation |

### 5.3 Relations

| Relation | Example |
| :--- | :--- |
| `question -> retrieves -> okf_concept` | a prefix-cache question retrieves KV-cache and PagedAttention concepts |
| `answer -> cites -> evidence` | answer cites benchmark output and OKF concept |
| `tool_call -> produced -> evidence` | benchmark tool produced latency table |
| `misconception -> corrected_by -> answer` | wrong belief corrected by grounded explanation |
| `learning_artifact -> derived_from -> event_run` | tutorial page generated from trace |

### 5.4 Behavior Model

The first version uses deterministic behavior boundaries before adding optional LLM assistance.

1. `classify_question`: detect concept, procedure, debugging, benchmark, or reflection question.
2. `retrieve_okf_context`: select OKF concepts using metadata, links, and lexical/vector retrieval.
3. `assemble_full_context`: build a static prefix and dynamic query payload.
4. `execute_optional_tools`: run tests, benchmark scripts, source inspection, or graph replay when requested.
5. `synthesize_grounded_answer`: answer with citations to OKF concepts and executable evidence.
6. `grade_response`: check citation coverage, unsupported claims, and rubric conformance.
7. `record_learning_signal`: store misconceptions, weak concepts, failed retrievals, or correction events.
8. `propose_material_update`: draft updates to OKF or learning pages behind approval gates.

## 6. Example Learning Workflow

A student asks:

```text
Why does prefix KV caching improve TTFT but not always decode ITL?
```

The system records `question.submitted`, retrieves `prefix-kv-cache.md`, `kv-cache.md`, `prefill-decode.md`, and `micro-vllm-prefix-cache-results.md`, creates a `context_snapshot`, and answers:

```text
Prefix caching improves TTFT because the engine can skip recomputing the shared prompt prefix during prefill. Decode ITL changes less because each generated token still requires a new decode step. In the micro-vLLM fixed-context benchmark, the warm SQL-agent workload reused [ASSUMED: 90%] of prefix tokens and reduced TTFT from [ASSUMED: 820 ms] to [ASSUMED: 360 ms], while Decode P50 ITL changed by only [ASSUMED: +/-3%].
```

The answer cites the OKF concept and benchmark artifact. The graph links question, concepts, context snapshot, evidence, and answer. If the student later asks, "What about Green Contexts?", the session graph resolves the reference to serving-loop latency trade-offs.

## 7. Evaluation Design

### 7.1 Baselines

| System | Description |
| :--- | :--- |
| Plain Chat | LLM with no retrieval and no event graph |
| Baseline RAG | vector search over raw Markdown/PDF files |
| OKF RAG | retrieval over OKF concepts, no event-sourced graph |
| ActiveGraph Agent | OKF retrieval + graph projection + executable evidence + evaluation |

### 7.2 Dataset

The evaluation uses `[ASSUMED: 120]` questions across four categories.

| Category | Examples |
| :--- | :--- |
| Conceptual | explain KV cache, online softmax, Green Contexts |
| Procedural | how to run a benchmark, how to debug a kernel |
| Diagnostic | why padding slowed throughput, why a kernel failed |
| Integrative | connect prefix caching to educational agent prompts |

A held-out set of `[ASSUMED: 40]` questions is reserved for final evaluation. Student task evaluation uses `[ASSUMED: 20-30]` assignments where learners inspect traces, fix code, or explain measured results.

### 7.3 Metrics

| Metric | Definition |
| :--- | :--- |
| Recall@k | gold OKF concepts retrieved in top-k |
| MRR | rank quality of first relevant concept |
| Citation correctness | cited evidence actually supports answer claim |
| Unsupported-claim rate | claims not supported by retrieved context or tool evidence |
| Tool-evidence coverage | answer includes executable evidence when task requires it |
| Task completion | student successfully completes assigned task |
| Explanation quality | rubric score for causal reasoning |
| Trace inspectability | evaluator can locate why answer was produced |
| Runtime TTFT | serving latency for fixed-context prompts |

## 8. Assumed Results

The following tables assume successful completion of the experiments.

### 8.1 Retrieval and Grounding

| System | Recall@5 | Citation Correctness | Unsupported Claims |
| :--- | ---: | ---: | ---: |
| Plain Chat | n/a | `[ASSUMED: 42%]` | `[ASSUMED: 31%]` |
| Baseline RAG | `[ASSUMED: 74%]` | `[ASSUMED: 68%]` | `[ASSUMED: 18%]` |
| OKF RAG | `[ASSUMED: 84%]` | `[ASSUMED: 82%]` | `[ASSUMED: 11%]` |
| ActiveGraph Agent | `[ASSUMED: 89%]` | `[ASSUMED: 91%]` | `[ASSUMED: 6%]` |

### 8.2 Learning Task Outcomes

| Condition | Task Completion | Explanation Quality | Trace-Based Debug Success |
| :--- | ---: | ---: | ---: |
| Baseline RAG | `[ASSUMED: 63%]` | `[ASSUMED: 3.2/5]` | `[ASSUMED: 48%]` |
| ActiveGraph Agent | `[ASSUMED: 81%]` | `[ASSUMED: 4.1/5]` | `[ASSUMED: 72%]` |

### 8.3 Runtime Feasibility

| Workload | No Prefix Cache TTFT | Warm Prefix Cache TTFT | Improvement |
| :--- | ---: | ---: | ---: |
| CUDA Tutor | `[ASSUMED: 1450 ms]` | `[ASSUMED: 620 ms]` | `[ASSUMED: 57%]` |
| nano-vLLM Tutor | `[ASSUMED: 2050 ms]` | `[ASSUMED: 890 ms]` | `[ASSUMED: 56%]` |
| SQL Agent | `[ASSUMED: 820 ms]` | `[ASSUMED: 360 ms]` | `[ASSUMED: 56%]` |

The runtime result matters because educational agents repeatedly reuse system prompts, rubrics, and course context. Prefix caching makes local deployment more feasible on a single consumer GPU.

## 9. Discussion

### 9.1 Educational Contribution

The main contribution is not that the agent answers more questions. It is that the agent turns answers into inspectable learning objects. A student can see which concept was retrieved, which evidence was used, and whether a tool confirmed the claim. An instructor can see repeated retrieval misses and update the OKF bundle.

### 9.2 Information Organization Contribution

OKF files provide the human-editable knowledge layer. ActiveGraph provides the runtime evidence layer. Together, they separate relatively stable course knowledge from dynamic learning events. This separation makes the system more auditable than a monolithic vector index.

### 9.3 Agentic Systems Contribution

The event-sourced graph avoids hiding agent behavior inside a transcript. It enables replay, before/after graph inspection, adaptation proposals, and approval-gated knowledge updates. This makes the educational agent suitable for cumulative course improvement.

### 9.4 Connection to micro-vLLM

Paper #1 provides the executable artifact and serving-system experiments. Paper #2 uses that artifact as course material and as the local inference substrate. The fixed-context workload in Paper #1 is motivated by the educational agent in Paper #2.

## 10. Threats to Validity

- Learning gains may depend on student background and instructor rubric quality.
- OKF bundle quality may dominate retrieval performance.
- Automatic grading of explanations can be noisy and should be checked by human raters.
- CUDA experiments require specific hardware and driver versions.
- Prefix-cache runtime gains depend on stable prompt layout.
- `[ASSUMED]` results must be replaced with measured values and confidence intervals.

## 11. Implementation Roadmap

1. Build OKF course bundle for CUDA Python and micro-vLLM.
2. Implement ActiveGraph Text-to-Query agent with OKF retrieval and context snapshots.
3. Add event objects for learner sessions, concepts, evidence, answers, and rubric grades.
4. Add executable tools for source inspection, tests, benchmarks, and graph replay.
5. Add evaluation pack with retrieval, grounding, and learning-task cases.
6. Run baseline RAG and ActiveGraph comparison.
7. Generate learning dashboard from event traces and system-model updates.

## 12. Conclusion

This paper proposes an educational knowledge agent that organizes technical course material as OKF bundles and records learning interactions as event-sourced graph traces. In CUDA Python and LLM inference-engine education, this architecture makes abstract explanations concrete: concepts link to source code, tool results, benchmarks, and trace evidence. Assuming successful evaluation, the system improves citation correctness, reduces unsupported claims, and helps students complete executable systems-learning tasks. The broader thesis is that educational agents should not be opaque answer machines; they should be inspectable knowledge systems whose retrieval, reasoning, action, and learning artifacts can be audited and improved.

## References

1. GoogleCloudPlatform, "Open Knowledge Format Specification," https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
2. ActiveGraph project documentation and local repository design notes.
3. W. Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," SOSP 2023.
4. vLLM Project, "Automatic Prefix Caching," https://docs.vllm.ai/en/v0.8.3/design/automatic_prefix_caching.html
5. GeeeekExplorer, "nano-vLLM," https://github.com/GeeeekExplorer/nano-vllm
6. NVIDIA, "CUDA Python," https://nvidia.github.io/cuda-python/latest/
7. NVIDIA, "Green Contexts," CUDA Programming Guide, https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/green-contexts.html
8. T. Dao et al., "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness," NeurIPS 2022.
