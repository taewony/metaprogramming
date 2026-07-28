# Paper #1 Green Context TTFT Analysis Note

## Current conclusion

Current saved benchmark logs do **not** yet support a strong paper claim that CUDA Green Contexts consistently regulate TTFT. They support a weaker and useful systems claim:

> Green Contexts are feasible in the Windows-native micro-vLLM runtime, but the current sequential Python serving loop shows nearly flat TTFT and mixed ITL/throughput effects. Stable benefit likely requires a workload with real prefill/decode overlap and profiling counters.

## Existing evidence from saved logs

Source logs:

- `KernelAgent/3-micro-vllm/test-result-cuTile.md`
- `KernelAgent/3-micro-vllm/test-result-cuTile-run.md`

The logs contain 9 paired Green OFF/ON comparisons for the dedicated Green Context workload.

| Metric | Green OFF Mean | Green ON Mean | Mean Delta | Delta Std. | Improved Runs |
| :--- | ---: | ---: | ---: | ---: | ---: |
| TTFT | 250.99 ms | 249.54 ms | -0.57% | 1.48% | 6 / 9 |
| Decode P50 ITL | 49.63 ms | 51.16 ms | +4.90% | 23.33% | 5 / 9 |
| Decode P99 ITL | 90.49 ms | 87.24 ms | -3.12% | 7.28% | 6 / 9 |
| Throughput | 399.12 tok/s | 395.01 tok/s | -0.07% | 16.69% | 4 / 9 |

Interpretation:

- TTFT has a slight average improvement, but the effect is small relative to run-to-run variation.
- Decode P99 ITL has a larger average improvement than TTFT, but still varies by run.
- Throughput is effectively flat on average and highly variable.
- Therefore, the paper should not yet claim stable Green Context speedup.

## Why TTFT may stay flat

Green Contexts partition SM resources. In our intended 32/16 split, prefill receives fewer SMs than the default full-GPU context. If the 2048-token batch-1 prefill fully saturated all 48 SMs, Green ON should increase TTFT. Instead, TTFT is nearly flat. The likely reasons are:

1. **Prefill saturation limit:** the tested batch-1 2048-token prefill may not use all 48 SMs efficiently, so reducing the prefill partition to 32 SMs does not hurt much.
2. **Sequential engine loop:** `LLMEngine.step()` schedules either prefill or decode in one step. It does not prove concurrent execution of prefill and decode on separate contexts.
3. **Context switch overhead vs. isolation benefit:** Green Context push/pop and allocator/cache effects may be close to the small TTFT delta.
4. **Metric design:** the benchmark labels the injected heavy request's prefill latency as TTFT. Green Contexts are conceptually more relevant to protecting active decode latency from prefill interference than to accelerating the prefill itself.

## Code changes made for auditable reruns

- `nanovllm/engine/model_runner.py`
  - Added `NANO_VLLM_GREEN_CONTEXT_API=auto|pytorch|cuda_core`.
  - Added `NANO_VLLM_PREFILL_SMS` and `NANO_VLLM_DECODE_SMS`.
  - Allows forced `cuda.core` Green Context execution instead of silently preferring PyTorch GreenContext.

- `bench_green.py`
  - Added result metadata: requested API, actual API, enabled flag, prefill SMs, decode SMs.

- `bench_green_repeat.py`
  - New repeated benchmark driver that writes paired Green OFF/ON JSONL evidence and prints aggregate mean/std.

## Target-PC command

Run this on the RTX 5070 target PC:

```powershell
cd D:\code\metaprogramming\KnowledgeChef\KernelAgent\3-micro-vllm
python bench_green_repeat.py --repeats 20 --green-api cuda_core --prefill-sms 32 --decode-sms 16 --jsonl green_context_results_cuda_core_32_16.jsonl
```

Optional comparison run:

```powershell
python bench_green_repeat.py --repeats 20 --green-api pytorch --prefill-sms 32 --decode-sms 16 --jsonl green_context_results_pytorch_32_16.jsonl
```

## Decision rule for paper inclusion

Add a Green Context TTFT/latency-regulation subsection only if the target-PC rerun satisfies at least one of these:

1. TTFT or Decode P99 ITL improves in at least 16 of 20 runs, with mean improvement larger than one delta standard deviation.
2. Nsight or CUDA profiling counters show a plausible mechanism: L2 hit-rate improvement, achieved occupancy change, or real overlap between prefill and decode streams.
3. The benchmark is revised to create actual concurrent prefill/decode execution, not just sequential context switching, and still shows consistent regulation.

If those conditions are not met, keep Green Contexts as a feasibility/future-work result rather than a core contribution.

```
  Green Contexts는 TTFT를 직접 줄이는 기술이라기보다, prefill/decode가 경쟁할 때 decode 쪽 tail
  latency를 보호하는 자원 격리 메커니즘입니다. 그런데 현재 LLMEngine.step() 구조는 prefill 또는
  decode를 순차적으로 실행하므로, 실제 prefill/decode overlap이 충분히 만들어지지 않습니다. 그래서
  TTFT는 거의 flat이고, P99 ITL도 방향은 조금 보이지만 안정적이지 않습니다.

  이번에 준비한 것:

  - docs/paper1_green_context_ttft_analysis.md
  - KernelAgent/3-micro-vllm/bench_green_repeat.py
  - model_runner.py에 NANO_VLLM_GREEN_CONTEXT_API=auto|pytorch|cuda_core 추가
  - bench_green.py 결과 JSON에 실제 green_api_type, green_enabled, SM split metadata 추가

  RTX 5070 target PC에서 다음을 실행하면 됩니다.

  cd D:\code\metaprogramming\KnowledgeChef\KernelAgent\3-micro-vllm
  python bench_green_repeat.py --repeats 20 --green-api cuda_core --prefill-sms 32 --decode-sms 16
  --jsonl green_context_results_cuda_core_32_16.jsonl

  논문에 넣는 기준은 엄격하게 잡는 게 좋습니다: TTFT 또는 Decode P99 ITL이 20회 중 16회 이상 개선
  되고, 평균 개선폭이 delta 표준편차보다 크면 본문 분석으로 넣고, 아니면 지금처럼 “feasible but
  mixed result”로 두는 게 안전합니다.
```
## 2026-07-28 target-PC API update

A target-PC preflight showed the following:

- PyTorch `torch.cuda.green_contexts.GreenContext` is importable but cannot create a context in the current environment, reporting `Green Context is only supported on CUDA 12.8+!` despite PyTorch reporting CUDA 13.0.
- `cuda.core` resource partitioning works when using `from cuda.bindings import driver as cuda`, `Device.set_current(ctx)`, and `Device.set_current()` for restoration.
- The runtime was updated to use this `cuda.core` activation pattern instead of the stale `from cuda import cuda` and `ctx.push_current()/ctx.pop_current()` path.

Paper implication: if a rerun now records `green_enabled=true` and `green_api_type="cuda_core"`, then it can be treated as a real resource-partitioning intervention. Previous JSONL files where `green_enabled=false` remain fallback-control runs and should not be used as Green Context efficacy evidence.
