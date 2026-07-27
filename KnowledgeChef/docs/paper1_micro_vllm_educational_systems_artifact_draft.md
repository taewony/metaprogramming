# Paper 1 Draft: Windows-Native LLM Inference Engine Migration as an Educational Systems Artifact

**Working title:** Windows-Native LLM Inference Engine Migration as an Educational Systems Artifact: micro-vLLM, CUDA Python 1.0, and Fixed-Context Agent Workloads

**Author:** Taewon Kim

**Draft status:** Planning draft. This manuscript assumes the additional prefix KV-cache experiments described here are completed successfully. Numeric values marked `[ASSUMED]` are placeholders for final measured values and must be replaced before submission.

## Abstract

High-performance LLM serving systems are commonly developed and evaluated in Linux-centric GPU software stacks that combine optimized attention kernels, Triton compilation, NCCL-based distributed execution, and production-oriented schedulers. These systems are powerful, but their complexity makes it difficult for students and local Windows-based researchers to inspect how prefill, decode, KV cache management, kernel launch overhead, and memory allocation interact inside an inference engine. This paper presents **micro-vLLM**, a Windows-native educational inference-engine artifact built with CUDA Python 1.0 and a cuTile-style Python kernel development workflow. Instead of claiming production superiority over mature Linux serving engines, micro-vLLM is designed to make LLM serving mechanisms observable, modifiable, and experimentally teachable.

We extend the original micro-vLLM prototype with a fixed-context agent workload inspired by Text-to-SQL and educational knowledge agents, where every request shares a long static prefix such as a system prompt, database schema, `SKILL.md`, or course knowledge bundle, followed by a short dynamic user question. This workload exposes prefix KV-cache reuse as an important optimization for educational and knowledge-retrieval agents. In an assumed successful evaluation, warm prefix-cache reuse reduces prefill token computation by `[ASSUMED: 70-90%]`, improves TTFT by `[ASSUMED: 35-60%]` for long static contexts, and improves end-to-end throughput by `[ASSUMED: 1.25-1.75x]` when output lengths are short to moderate. These results complement earlier observations: WSL2 FlashAttention remains much faster than the current Windows-native cuTile backend in raw throughput, Green Contexts slightly reduce Decode P99 inter-token latency while harming median latency and throughput, and naive shape padding can trigger allocator thrashing. Together, these findings support the thesis that educational inference-engine artifacts should teach the full serving loop, not isolated kernels alone.

## Keywords

LLM serving, CUDA Python 1.0, cuTile, prefix KV cache, nano-vLLM, fixed-context agents, educational systems artifact, Windows-native GPU computing

## 1. Introduction

Local LLM inference is increasingly relevant for education, private data analysis, and offline research environments. Students and researchers want to understand not only how to call an LLM API, but how an inference engine transforms prompts into prefill work, maintains KV cache state, schedules decode steps, and trades latency against throughput. Production-grade systems such as vLLM, TensorRT-LLM, FlashAttention-based stacks, and Triton kernels provide strong performance, but they are difficult to modify and often assume Linux-centered dependencies.

Windows-native GPU development is important for educational settings because many learners use consumer GPUs on Windows machines. However, the dominant LLM serving stack frequently relies on Linux-first build scripts, NCCL, Triton, and prebuilt CUDA packages. WSL2 is a practical workaround, but it adds another layer between the learner and the native runtime they are trying to understand.

This paper argues for a different target: **an educational systems artifact**. micro-vLLM is not positioned as a faster replacement for vLLM. It is a controlled artifact that exposes the key mechanisms of an LLM inference engine inside a Windows-native CUDA Python workflow. The artifact is valuable if it helps learners and researchers observe mechanisms, reproduce bottlenecks, and connect low-level GPU behavior to high-level agent workloads.

The revised contribution of this paper is the addition of **fixed-context agent workloads**. Many real agent systems repeatedly prepend the same system prompt, schema, policy, tool specification, few-shot examples, or course context to each user query. Text-to-SQL agents repeatedly include database schema and rule context. Educational agents repeatedly include rubrics, course modules, and source-code excerpts. Such workloads are a natural fit for prefix KV-cache reuse, because the expensive prefill computation for the static prefix can be reused across requests.

## 2. Research Questions

**RQ1.** Can a Windows-native educational inference-engine artifact expose the main serving-loop mechanisms of LLM inference: prefill, decode, KV cache management, prefix reuse, allocation behavior, and GPU resource partitioning?

**RQ2.** For fixed-context agent workloads, how much does prefix KV-cache reuse reduce prefill computation, TTFT, and end-to-end latency in a Windows-native micro-vLLM implementation?

**RQ3.** How do prefix caching, Green Contexts, and shape stabilization interact with the full serving loop, and what can students learn from successful and failed optimizations?

## 3. Contributions

This paper makes four contributions.

1. **Educational migration artifact.** We present micro-vLLM as a staged Windows-native LLM inference-engine artifact that migrates concepts from MatMul, fused attention, llm-from-scratch, and nano-vLLM-style serving into an inspectable CUDA Python workflow.

2. **Fixed-context agent benchmark.** We define a benchmark for educational and data-query agents whose requests share long static prefixes such as system prompts, schemas, `SKILL.md` files, and course knowledge bundles.

3. **Prefix KV-cache evaluation.** Assuming successful completion of the planned experiments, we show that prefix KV reuse substantially reduces prefill work and improves TTFT for fixed-context workloads, while producing limited benefit when decode dominates or prefixes do not match.

4. **Systems-learning analysis.** We connect positive and negative optimization findings: WSL2 FlashAttention remains the performance reference, Green Contexts show a tail-latency trade-off, and naive shape padding can harm throughput through allocator thrashing.

## 4. Background

### 4.1 LLM Serving Loop

Autoregressive LLM serving has two main phases. In **prefill**, the model processes the input prompt and produces KV cache entries for all prompt tokens. In **decode**, the model generates one token at a time while attending to previously cached keys and values. Prefill is sensitive to prompt length and parallel compute throughput. Decode is sensitive to per-token latency, scheduler overhead, memory bandwidth, and KV-cache access patterns.

### 4.2 Paged KV Cache and Prefix Caching

Paged KV-cache systems divide the KV cache into blocks that can be mapped, reused, and evicted. Prefix caching extends this idea: when a new request shares an identical token prefix with an earlier request, the engine can reuse the cached KV blocks for the shared prefix instead of recomputing them. This is especially useful for repeated system prompts, long documents, course modules, and multi-turn conversations.

The key engineering condition is exact token-prefix stability. Dynamic metadata such as timestamps, run IDs, random examples, or user-specific text placed early in the prompt can break cache reuse. Therefore, prompt layout is part of the serving-system design: static context should appear first, dynamic user queries should appear last.

### 4.3 CUDA Python 1.0 and Windows-Native Experimentation

CUDA Python provides Python-level access to CUDA runtime, driver, graph, profiling, and related APIs. In this work, it enables a teaching-oriented path where students can inspect host-side runtime control while still connecting to real GPU execution. cuTile-style Python kernels are used as a learning bridge between high-level PyTorch operations and low-level CUDA C++ kernels.

### 4.4 nano-vLLM as a Readable Reference

nano-vLLM is a compact vLLM-like implementation intended to be readable and hackable. Its compact codebase makes it useful as a migration reference and teaching object. micro-vLLM borrows this pedagogical stance but targets Windows-native CUDA Python experimentation rather than full production serving.

## 5. System Design

### 5.1 Design Goals

micro-vLLM is designed around four goals.

- **Inspectability:** learners should see how prompt tokens become prefill work, KV blocks, and decode steps.
- **Modifiability:** kernels and scheduler logic should be small enough to modify during experiments.
- **Windows-native execution:** the artifact should run in a Windows CUDA environment without treating WSL2 as the only viable path.
- **Agent-workload relevance:** the benchmark should reflect repeated static context used by educational, Text-to-SQL, and knowledge-retrieval agents.

### 5.2 Migration Stages

The implementation is organized as a learning path.

1. **MatMul stage:** tiling, shared memory, register pressure, occupancy, and baseline comparison.
2. **FMHA stage:** online softmax, causal masking, attention score residency, and memory hierarchy.
3. **llm-from-scratch stage:** minimal transformer inference, KV cache lifecycle, and decode loop.
4. **micro-vLLM stage:** paged KV cache, continuous batching, prefix reuse, and agent workload benchmarks.

### 5.3 Fixed-Context Prompt Layout

The benchmark uses prompts with the following structure.

```text
[Static system prompt]
[Static policy / tool contract]
[Static DB schema or course OKF excerpt]
[Static examples or rubric]
[Dynamic user query]
```

The static prefix is intentionally identical across many requests. The dynamic suffix changes per user question. This design represents common agent workloads such as:

- Text-to-SQL over a fixed SQLite schema.
- CUDA programming tutor over a fixed course module.
- nano-vLLM tutor over a fixed source-code excerpt.
- Retrieval agent over a fixed OKF knowledge bundle selection.

### 5.4 Prefix KV-Cache Mechanism

The prefix cache stores fully computed KV blocks for token prefixes. Each block is identified by a chained content hash over previous tokens and current block tokens. On a new request, the scheduler finds the longest cached prefix, skips recomputation for those tokens, and only precomputes the suffix tokens. The model runner then decodes using both reused prefix KV blocks and newly computed suffix KV blocks.

The implementation records:

- number of prompt tokens,
- number of reused prefix tokens,
- number of newly computed prefill tokens,
- reused KV blocks,
- cache-hit ratio,
- TTFT,
- decode ITL,
- end-to-end latency,
- VRAM occupancy.

## 6. Experimental Methodology

### 6.1 Hardware and Software

The target machine is a Windows 11 workstation with an NVIDIA GeForce RTX 5070 GPU, 48 SMs, 12 GB VRAM, and CUDA 13.3. The model is Qwen2.5-3B-Instruct or a comparable local model that fits in VRAM under the tested batch and cache settings.

### 6.2 Workloads

| Workload | Static Prefix | Dynamic Suffix | Purpose |
| :--- | :--- | :--- | :--- |
| SQL Agent | system prompt + database schema + `SKILL.md` | natural-language SQL question | fixed schema query workload |
| CUDA Tutor | course module + kernel template + rubric | student question or patch request | educational code reasoning |
| nano-vLLM Tutor | source excerpt + serving concept notes | concept question | inference-engine learning |
| Negative Control | shuffled or changed prefix | question | verifies prefix exactness |

### 6.3 Conditions

| Condition | Description |
| :--- | :--- |
| NoCache | prefix cache disabled or bypassed |
| ColdCache | prefix cache enabled, first request computes full prefix |
| WarmCache | prefix cache enabled, repeated static prefix reused |
| PrefixChanged | prefix differs early, cache hit should collapse |
| WSL2 Reference | WSL2 FlashAttention or vLLM baseline |

### 6.4 Metrics

- TTFT: time to first token.
- Prefill tokens computed: actual model tokens processed during prefill.
- Prefix cache hit ratio: reused prefix tokens divided by total prompt tokens.
- Throughput: output tokens per second.
- Decode P50/P99 ITL: median and tail inter-token latency.
- VRAM overhead: memory consumed by cache retention.
- Correctness: output equivalence under deterministic sampling.

## 7. Results

### 7.1 Existing Baseline Results

The original micro-vLLM evaluation found that WSL2 FlashAttention remains substantially faster than the current Windows-native cuTile backend in raw throughput.

| Backend | Runs | Time | Throughput | Relative |
| :--- | ---: | ---: | ---: | ---: |
| Windows cuTile | 3 | 289.16 s | 463.35 tok/s | 1.00x |
| WSL2 FlashAttention | 4 | 62.65 s | 2138.55 tok/s | 4.62x |

This result supports the paper's positioning: micro-vLLM is not yet a production-grade performance replacement. Its value is inspectability, migration feasibility, and experimental diagnosis.

### 7.2 Assumed Prefix Cache Results

The following table is written under the user's assumption that all required prefix-cache experiments succeed. Replace all `[ASSUMED]` values with final measured data.

| Workload | Prefix Tokens | Output Tokens | Condition | Prefill Tokens Computed | TTFT | E2E Throughput | Cache Hit |
| :--- | ---: | ---: | :--- | ---: | ---: | ---: | ---: |
| SQL Agent | 2048 | 64 | NoCache | 2048 | `[ASSUMED: 820 ms]` | `[ASSUMED: 310 tok/s]` | 0% |
| SQL Agent | 2048 | 64 | WarmCache | `[ASSUMED: 128-256]` | `[ASSUMED: 360 ms]` | `[ASSUMED: 480 tok/s]` | `[ASSUMED: 87-94%]` |
| CUDA Tutor | 4096 | 128 | NoCache | 4096 | `[ASSUMED: 1450 ms]` | `[ASSUMED: 240 tok/s]` | 0% |
| CUDA Tutor | 4096 | 128 | WarmCache | `[ASSUMED: 256-512]` | `[ASSUMED: 620 ms]` | `[ASSUMED: 360 tok/s]` | `[ASSUMED: 88-94%]` |
| nano-vLLM Tutor | 6144 | 128 | NoCache | 6144 | `[ASSUMED: 2050 ms]` | `[ASSUMED: 190 tok/s]` | 0% |
| nano-vLLM Tutor | 6144 | 128 | WarmCache | `[ASSUMED: 512-768]` | `[ASSUMED: 890 ms]` | `[ASSUMED: 290 tok/s]` | `[ASSUMED: 87-92%]` |
| Negative Control | 4096 | 128 | PrefixChanged | `[ASSUMED: 4096]` | `[ASSUMED: near NoCache]` | `[ASSUMED: near NoCache]` | `[ASSUMED: <5%]` |

The expected pattern is mechanism-specific. Prefix caching improves prefill-dominated metrics such as TTFT and computed prefill tokens. It has less direct effect on decode ITL because decode still produces new tokens one step at a time.

### 7.3 Green Contexts and Shape Stabilization

The original Green Contexts experiment showed a mixed trade-off.

| Metric | Green OFF | Green ON | Delta |
| :--- | ---: | ---: | ---: |
| TTFT | 251.79 ms | 250.30 ms | -0.6% |
| Decode P50 ITL | 49.76 ms | 52.33 ms | +5.2% |
| Decode P99 ITL | 91.14 ms | 87.60 ms | -3.9% |
| Throughput | 397.07 tok/s | 386.92 tok/s | -2.6% |

The shape-padding experiment showed that launch/JIT avoidance can backfire when it changes memory allocation behavior. The padded path reduced total throughput by 67.0% relative to no-padding eager execution. This result is pedagogically useful because it demonstrates that a local optimization hypothesis must be evaluated against the full serving loop.

## 8. Discussion

### 8.1 Why Fixed-Context Agents Matter

Agent systems often pay a repeated prefill cost for context that is logically constant: system prompt, safety policy, database schema, tool descriptions, examples, and course material. A serving engine that ignores this structure repeatedly recomputes the same hidden states. Prefix KV caching makes the workload structure visible to the runtime.

### 8.2 Educational Value

The artifact helps students observe three classes of optimization.

- **Successful mechanism:** prefix KV reuse improves prefill-heavy fixed-context workloads.
- **Trade-off mechanism:** Green Contexts can reduce tail latency while hurting throughput in a sequential engine loop.
- **Failed mechanism:** shape padding can reduce JIT variability but increase allocator overhead enough to dominate runtime.

This is a stronger educational story than a single speedup claim. It teaches students to connect hypotheses, measurements, and system-level causality.

### 8.3 Why Not Replace vLLM?

The results do not challenge vLLM's production role. vLLM and FlashAttention remain stronger for mature high-throughput serving. micro-vLLM is valuable because it is small, Windows-native, and instrumented for learning. It provides a controlled environment where students can modify runtime components and observe consequences.

## 9. Threats to Validity

- The experiments use a single consumer GPU and may not generalize to larger datacenter GPUs.
- Prefix-cache gains depend on exact token-prefix reuse and will shrink when prompts vary early.
- Workloads with long generated outputs may be decode-dominated and show smaller end-to-end gains.
- Windows-native implementation maturity is lower than Linux serving stacks.
- `[ASSUMED]` values must be replaced with measured data before publication.

## 10. Conclusion

This paper reframes micro-vLLM as a Windows-native educational systems artifact for learning LLM inference-engine internals. The revised evaluation adds fixed-context agent workloads, showing why prefix KV-cache reuse is a natural optimization for Text-to-SQL, CUDA tutoring, and knowledge-retrieval agents. Combined with Green Contexts and allocator-thrashing analysis, the artifact demonstrates that inference-engine education should teach complete serving-loop causality: prompt layout, prefill reuse, KV-cache management, decode latency, memory allocation, and GPU resource partitioning.

## References

1. W. Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," SOSP 2023.
2. vLLM Project, "Automatic Prefix Caching," https://docs.vllm.ai/en/v0.8.3/design/automatic_prefix_caching.html
3. vLLM Project, "Prefix caching," https://www.mintlify.com/vllm-project/vllm/features/prefix-caching
4. GeeeekExplorer, "nano-vLLM," https://github.com/GeeeekExplorer/nano-vllm
5. GeeeekExplorer, "Nano-vLLM Prefix Caching," https://www.mintlify.com/GeeeekExplorer/nano-vllm/guides/prefix-caching
6. NVIDIA, "CUDA Python," https://nvidia.github.io/cuda-python/latest/
7. NVIDIA, "Green Contexts," CUDA Programming Guide, https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/green-contexts.html
8. T. Dao et al., "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness," NeurIPS 2022.
