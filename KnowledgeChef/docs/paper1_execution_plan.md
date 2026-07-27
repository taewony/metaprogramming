# Paper #1 Execution Plan

**Paper:** Windows-Native LLM Inference Engine Migration as an Educational Systems Artifact

**Status:** active work plan

## 1. Working Position

Paper #1 should not depend on extending ActiveGraph with Tau. The submission target is KTCP, so the contribution should be framed as a computing-practice artifact with reproducible implementation, measured behavior, and engineering lessons.

The core contribution is:

```text
Windows-native CUDA Python/cuTile micro-vLLM
+ staged learning path from MatMul to FMHA to LLM-from-scratch to micro-vLLM
+ fixed-context agent workload showing prefix KV-cache benefit
+ honest bottleneck analysis against WSL2 FlashAttention, Green Contexts, and allocator thrashing
```

## 2. Host-PC / Target-PC Work Split

### Host-PC

The host-PC is used for:

- source review,
- benchmark script preparation,
- paper writing,
- log parsing,
- table generation,
- figure planning,
- interpretation and revision.

The host-PC must not be treated as the source of GPU performance truth unless it is the RTX5070 machine.

### Target-PC

The target-PC has the RTX5070 and is used for:

- CUDA Python/cuTile execution,
- micro-vLLM serving benchmarks,
- WSL2 FlashAttention reference runs,
- Green Contexts experiments,
- prefix KV-cache experiments,
- correctness and benchmark logs.

All final paper numbers must come from target-PC logs.

## 3. Existing Codebase Map

| Stage | Folder | Paper Role |
| :--- | :--- | :--- |
| 0 | `KernelAgent/0-MatMul` | staged kernel-learning artifact: tiling, swizzling, GEMM baseline |
| 1 | `KernelAgent/1-FMHA` | fused attention migration and online softmax stage |
| 2 | `KernelAgent/2-LLM-from-scratch` | minimal autoregressive loop, KV cache, CUDA Graph learning bridge |
| 3 | `KernelAgent/3-micro-vllm` | Windows-native serving artifact, paged KV cache, prefix cache, Green Contexts |

## 4. Existing Evidence

Already available from previous runs:

- `KernelAgent/paper/micro_vllm.pdf`
- `KernelAgent/paper/paper-v3.tex`
- `KernelAgent/3-micro-vllm/analysis_report.md`
- `KernelAgent/3-micro-vllm/test-result-cuTile.md`
- `KernelAgent/3-micro-vllm/test-result-cuTile-run.md`
- `KernelAgent/3-micro-vllm/test-result-flash_attn*.md`
- `KernelAgent/paper/gpu_info.txt`

Current paper-safe interpretation:

- WSL2 FlashAttention is the optimized reference baseline and is much faster than the current Windows cuTile path.
- Windows cuTile path is valuable as an educational and inspectable migration artifact.
- Dynamic shape padding can trigger allocator thrashing and should be presented as a negative result.
- Green Contexts show feasibility and possible tail-latency tradeoff, but repeated results are mixed.

## 5. New Experiment: Fixed-Context Prefix KV Cache

### Hypothesis

Agent workloads repeatedly use long static prefixes:

```text
system prompt
+ DB schema
+ SKILL.md or tool contract
+ course/rubric/context excerpt
+ dynamic user question
```

If the static prefix is token-identical and aligned into complete KV-cache blocks, micro-vLLM can reuse cached prefix blocks and reduce prefill work, TTFT, and end-to-end latency for short or moderate answers.

### New Script

Use:

```powershell
cd KernelAgent/3-micro-vllm
python bench_prefix_cache.py --use-cutile --requests 8 --static-prefix-tokens 2048 --dynamic-suffix-tokens 64 --max-tokens 64 --out-jsonl prefix_cache_results_cutile.jsonl
```

Recommended additional runs:

```powershell
python bench_prefix_cache.py --use-cutile --requests 8 --static-prefix-tokens 1024 --dynamic-suffix-tokens 64 --max-tokens 64 --out-jsonl prefix_cache_results_cutile_1024.jsonl
python bench_prefix_cache.py --use-cutile --requests 8 --static-prefix-tokens 3072 --dynamic-suffix-tokens 64 --max-tokens 64 --out-jsonl prefix_cache_results_cutile_3072.jsonl
```

For WSL2 reference, omit `--use-cutile` if FlashAttention dependencies are active:

```bash
python bench_prefix_cache.py --requests 8 --static-prefix-tokens 2048 --dynamic-suffix-tokens 64 --max-tokens 64 --out-jsonl prefix_cache_results_flash.jsonl
```

### Metrics

The script records:

- condition: `no_cache`, `warm_cache`, `prefix_changed`,
- prompt tokens,
- cached tokens,
- computed prefill tokens,
- cache hit ratio,
- TTFT milliseconds,
- E2E latency milliseconds,
- decode P50/P99 ITL,
- output tokens,
- throughput tokens/sec.

## 6. Paper Acceptance Criteria

Before replacing `[ASSUMED]` values in the draft, collect:

- at least 3 repeated runs per main condition,
- JSONL raw logs,
- mean/std table,
- exact target-PC hardware/software info,
- confirmation that prompt prefixes are token-identical for warm-cache runs,
- negative control showing prefix changes destroy cache hits,
- correctness sanity check that outputs are coherent and no runtime errors occurred.

## 7. Next Paper Edits After Data

1. Replace `[ASSUMED]` values in `docs/paper1_micro_vllm_educational_systems_artifact_draft.md`.
2. Add a new figure: fixed-context prompt layout and reused KV blocks.
3. Add a table: NoCache vs WarmCache vs PrefixChanged.
4. Add a subsection explaining why agent context layout matters for serving systems.
5. Tone down any remaining claim that cuTile outperforms production FlashAttention.
```
• Started Paper #1 work.

  I found and inventoried the four KernelAgent stages:

  - KernelAgent/0-MatMul
  - KernelAgent/1-FMHA
  - KernelAgent/2-LLM-from-scratch
  - KernelAgent/3-micro-vllm

  I also confirmed that 3-micro-vllm already has prefix-cache machinery in BlockManager,
  Sequence.num_cached_tokens, Scheduler, and ModelRunner.prepare_prefill, so we can add the fixed-
  context prefix KV-cache experiment without extending ActiveGraph or Tau.

  New files:

  - docs/paper1_execution_plan.md
    Paper #1 execution plan, host-PC/target-PC split, existing evidence map, and target RTX5070
    experiment protocol.

  - KernelAgent/3-micro-vllm/bench_prefix_cache.py
    Benchmark script for no_cache, warm_cache, and prefix_changed conditions. It records TTFT,
    cached tokens, computed prefill tokens, cache hit ratio, E2E latency, decode P50/P99 ITL, and
    throughput.

  Target-PC command:

  cd KernelAgent/3-micro-vllm
  python bench_prefix_cache.py --use-cutile --requests 8 --static-prefix-tokens 2048 --dynamic-
  suffix-tokens 64 --max-tokens 64 --out-jsonl prefix_cache_results_cutile.jsonl

  Optional additional runs:

  python bench_prefix_cache.py --use-cutile --requests 8 --static-prefix-tokens 1024 --dynamic-
  suffix-tokens 64 --max-tokens 64 --out-jsonl prefix_cache_results_cutile_1024.jsonl
  python bench_prefix_cache.py --use-cutile --requests 8 --static-prefix-tokens 3072 --dynamic-
  suffix-tokens 64 --max-tokens 64 --out-jsonl prefix_cache_results_cutile_3072.jsonl

  Validation done on host:

  - AST parse passed.
  - python bench_prefix_cache.py --help works.
  - I did not run GPU benchmarks here because this host Python lacks torch; final performance
    numbers must come from the RTX5070 target-PC.
```