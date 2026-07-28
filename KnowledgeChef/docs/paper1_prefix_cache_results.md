# Paper #1 Prefix KV-Cache Result Summary

Source files:
- `KernelAgent/3-micro-vllm/prefix_cache_results_cutile_1024.jsonl`
- `KernelAgent/3-micro-vllm/prefix_cache_results_cutile.jsonl`
- `KernelAgent/3-micro-vllm/prefix_cache_results_cutile_3072.jsonl`

All files parsed successfully as JSONL. Each file contains 8 request rows per condition plus summary rows for `no_cache`, `warm_cache`, and `prefix_changed`.

## Main Table

| Static Prefix | Prompt Tokens | Warm Cache Hit | Computed Prefill NoCache | Computed Prefill Warm | Prefill Reduction | TTFT NoCache | TTFT Warm | TTFT Reduction | PrefixChanged TTFT | E2E Delta Warm vs NoCache |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 1088 | 94.1% | 1088 | 64 | 94.1% | 146.98 ms | 86.56 ms | 41.1% | 148.18 ms | +34.2% |
| 2048 | 2112 | 97.0% | 2112 | 64 | 97.0% | 255.58 ms | 86.72 ms | 66.1% | 256.93 ms | +4.9% |
| 3072 | 3136 | 98.0% | 3136 | 64 | 98.0% | 381.76 ms | 77.47 ms | 79.7% | 389.61 ms | +1.2% |

## Paper-Safe Interpretation

- Warm prefix KV-cache reuse reduces computed prefill tokens to 64 in all three fixed-context workloads.
- TTFT reduction grows with static-prefix length: 41.1% at 1024 tokens, 66.1% at 2048 tokens, and 79.7% at 3072 tokens.
- The `prefix_changed` negative control returns 0.0% cache hit and TTFT close to the no-cache condition, confirming exact-prefix dependence.
- E2E throughput does not consistently improve because the benchmark generates 64 output tokens and decode dominates total runtime. The paper should claim TTFT/prefill reduction, not universal throughput improvement.

## Data Rows For Manuscript

```json
[
  {
    "file": "prefix_cache_results_cutile_1024.jsonl",
    "static_prefix": 1024,
    "prompt_tokens": 1088,
    "warm_cached_tokens": 1024,
    "warm_computed_tokens": 64,
    "warm_hit_pct": 94.11764705882352,
    "no_ttft": 146.98058750946075,
    "warm_ttft": 86.56151250033872,
    "changed_ttft": 148.18346251558978,
    "ttft_reduction_pct": 41.10684004799818,
    "prefill_reduction_pct": 94.11764705882352,
    "no_e2e": 2797.595324998838,
    "warm_e2e": 3753.868562496791,
    "e2e_delta_pct": 34.18197152936515,
    "no_tps": 22.95291743887698,
    "warm_tps": 17.087179298752368,
    "changed_hit_pct": 0.0,
    "changed_tokens": 1088
  },
  {
    "file": "prefix_cache_results_cutile.jsonl",
    "static_prefix": 2048,
    "prompt_tokens": 2112,
    "warm_cached_tokens": 2048,
    "warm_computed_tokens": 64,
    "warm_hit_pct": 96.96969696969697,
    "no_ttft": 255.58482500491664,
    "warm_ttft": 86.71571251034038,
    "changed_ttft": 256.93256249360275,
    "ttft_reduction_pct": 66.07165057288819,
    "prefill_reduction_pct": 96.96969696969697,
    "no_e2e": 3277.6794000019436,
    "warm_e2e": 3437.25903750601,
    "e2e_delta_pct": 4.868677440019659,
    "no_tps": 20.047782553836136,
    "warm_tps": 18.815776974309582,
    "changed_hit_pct": 0.0,
    "changed_tokens": 2112
  },
  {
    "file": "prefix_cache_results_cutile_3072.jsonl",
    "static_prefix": 3072,
    "prompt_tokens": 3136,
    "warm_cached_tokens": 3072,
    "warm_computed_tokens": 64,
    "warm_hit_pct": 97.95918367346938,
    "no_ttft": 381.7594249994727,
    "warm_ttft": 77.46865000081016,
    "changed_ttft": 389.60701250471175,
    "ttft_reduction_pct": 79.70746891162749,
    "prefill_reduction_pct": 97.95918367346938,
    "no_e2e": 3205.811662497581,
    "warm_e2e": 3242.7611999955843,
    "e2e_delta_pct": 1.1525797953213734,
    "no_tps": 20.021328225640556,
    "warm_tps": 19.90191317946777,
    "changed_hit_pct": 0.0,
    "changed_tokens": 3136
  }
]
```
