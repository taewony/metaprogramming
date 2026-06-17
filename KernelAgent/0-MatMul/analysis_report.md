# Analysis Report: cuTile MatMul vs PyTorch Baseline on RTX 5070

**Date:** June 17, 2026  
**Tech Lead:** AI Agent  
**Target Platform:** NVIDIA GeForce RTX 5070 (Blackwell SM100/101, 48 SMs, 48.0 MB L2 Cache)

---

## 1. Executive Summary

We successfully executed the matrix multiplication benchmark comparing two cuTile-based kernels against PyTorch's highly optimized `torch.matmul` (cuBLAS/CUTLASS) on the target RTX 5070 GPU.

Both cuTile implementations passed all numerical correctness checks within the allowed floating-point 16-bit limits (`atol=2e-1, rtol=2e-2`):
- **matmul_sample** (Standard tiled scheduling): **PASSED**
- **matmul_tilegym** (Grouped swizzled scheduling): **PASSED**

---

## 2. Quantitative Performance Analysis

The following table summarizes the measured execution times and TFLOPS across different matrix dimensions:

| Dimension | PyTorch Time (ms) | PyTorch (TFLOPS) | cuTile Sample (ms) | cuTile Sample (TFLOPS) | cuTile TileGym (ms) | cuTile TileGym (TFLOPS) | Speedup (TileGym) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **256 × 256** | 0.009 | 3.63 | 0.007 | 4.62 | 0.008 | 4.32 | **1.19×** (Sample: **1.27×**) |
| **512 × 512** | 0.010 | 25.95 | 0.010 | 25.68 | 0.010 | 26.00 | **1.00×** |
| **1024 × 1024** | 0.039 | 54.96 | 0.045 | 47.55 | 0.043 | 49.52 | **0.90×** |
| **2048 × 2048** | 0.259 | 66.37 | 0.294 | 58.36 | 0.303 | 56.78 | **0.86×** |
| **4096 × 4096** | 2.016 | 68.18 | 2.199 | 62.49 | 2.232 | 61.56 | **0.90×** |

```
TFLOPS Performance Curves
 80 ┼────────────────────────────────────────────────── PyTorch (~68T)
 70 ┼                                                  cuTile Sample (~62T)
 60 ┼─────────────────────────────────────────        cuTile TileGym (~61T)
 50 ┼                        ────────────
 40 ┼
 30 ┼           ─────────────
 20 ┼
 10 ┼
  0 ┼───┴─────────────┴─────────────┴─────────────┴───
       256           512           1024          2048
```

---

## 3. Performance Insights & Bottleneck Analysis

### A. Small Matrix Efficiency ($N \le 512$)
At $256 \times 256$, both cuTile kernels outperformed PyTorch by up to **1.27×** (4.62 TFLOPS vs. 3.63 TFLOPS). This is because PyTorch incurs framework dispatch and tensor wrapping overheads, which dominate small-scale executions. cuTile's JIT compiler generates low-overhead dispatches directly, yielding superior throughput.

### B. Large Matrix Saturation ($N \ge 1024$)
At larger dimensions, PyTorch scales up to **68.18 TFLOPS** (leveraging cuBLAS/CUTLASS warp-group Tensor Core operations). The cuTile kernels saturate slightly lower:
- `matmul_sample`: **62.49 TFLOPS** (91.6% of PyTorch)
- `matmul_tilegym`: **61.56 TFLOPS** (90.3% of PyTorch)

### C. Persistent Thread Block Under-occupancy in TileGym
The `matmul_tilegym` kernel uses a persistent thread block pattern with `num_ctas = 48` (1 CTA per SM).
- **The Problem**: A single thread block of size $64 \times 64$ requires $16\text{ KB}$ of shared memory ($8\text{ KB}$ for A, $8\text{ KB}$ for B). With the RTX 5070's $100\text{ KB}$ Shared Memory per SM, we can theoretically run up to **6 blocks concurrently** on each SM.
- **The Bottleneck**: Launching only $48$ blocks total ensures that each SM only hosts $1$ block. If this block stalls while loading tiles from global memory, the SM execution pipelines sit idle. 
- **The Solution**: We must increase `num_ctas` to **192** (4 blocks per SM) to allow the hardware warp scheduler to hide memory access latencies.

---

## 4. Next Step Action Items

1. **Tune persistent thread counts (`num_ctas`)**: Change the default `num_ctas` in `compare_matmul.py` from 48 to **192** (or profile across 48, 96, 144, 192) to maximize SM occupancy.
2. **Increase Swizzling Group Size**: Change `GROUP_SIZE_M` from 4 to **8** to exploit the massive $48\text{ MB}$ L2 Cache of the RTX 5070.
