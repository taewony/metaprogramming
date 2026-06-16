## KernelAgent: cuTile-Based GPU Kernel Optimization for LLM Inference

**Project Lead:** Tech Lead (Kernel Engineering & Performance Analysis)  
**Target Hardware:** NVIDIA GeForce RTX 5070 (Blackwell Architecture, SM 100/101)  
**Objective:** Establish a foundational research platform demonstrating the performance superiority of NVIDIA cuTile DSL + CUDA Python 1.0 over conventional PyTorch/Triton implementations. We focus on matrix multiplication, fused multi-head attention (FMHA), and end‑to‑end LLM inference with advanced KV‑cache management and CUDA Graphs.

---

## 1. Project Overview

Modern LLM inference demands extreme GPU efficiency, yet existing frameworks often suffer from host-side Python launch overhead, suboptimal memory access patterns, and rigid kernel dispatch boundaries. **KernelAgent** systematically replaces critical GPU kernels (MatMul, FMHA, full decoder blocks) with hand‑tuned cuTile implementations and compares them in a strictly apple‑to‑apple manner against PyTorch baselines.

The ultimate goal is to **write a peer‑reviewed paper** based on the measured data, proving that a cuTile‑optimized stack can outperform current production‑grade solutions, particularly in latency-sensitive serving scenarios.

---

## 2. Repository Structure

The actual structure of the repository and its experimental modules is organized as follows:

```
KernelAgent/
├── README.md                          # <--- You are here
├── 0-cuTile/                          # Matrix Multiplication Experiments
│   ├── cutile_matmul.py               # cuTile Matrix Multiplication kernel
│   ├── cutile_matmul_perf.py          # Benchmark: cuTile MatMul vs. PyTorch matmul
│   └── test.py                        # Correctness checks for cuTile MatMul
├── 1-FMHA/                            # Fused Multi-Head Attention Experiments
│   ├── AttentionFMHA.py               # FMHA correctness and tuning wrapper
│   └── AttentionFMHA_v3.py            # Latency-hiding FMHA implementation
├── 2-LLM-from-scratch/                # End-to-End LLM Inference Experiments
│   ├── compare_infer.py               # E2E Benchmark: PyTorch vs. cuTile Attention (with KV-Cache)
│   ├── compare_infer_cuda_graph.py    # E2E Benchmark: cuTile Raw vs. cuTile + CUDA Graphs
│   ├── src/                           # Model source codes
│   │   ├── model.py                   # Baseline GPT-2 Model (PyTorch)
│   │   ├── model_cutile.py            # cuTile Attention GPT-2 Model
│   │   ├── cutile_kernel.py           # cuTile FMHA kernel wrapper
│   │   ├── generate.py                # Generation helper (PyTorch)
│   │   └── generate_cutile.py         # Generation helper (cuTile)
│   └── study/                         # Design specifications and design documents
│       └── compare_infer.md           # Engineering guide for the E2E benchmark
└── 3-nano-vllm/                       # Advanced Multi-Tenant Serving (Future)
    └── TileGym-based-mirgration.md    # Plan for continuous batching migration
```

---

## 3. Experiments at a Glance

| Experiment | Key Kernel(s) | Baseline | cuTile Advantage |
|------------|---------------|----------|------------------|
| **0 - cuTile** | Tiled GEMM with vectorized loads, unrolled loops | `torch.matmul` (FP16) | Explicit shared memory tiling and register blocking optimized for Tensor Cores. |
| **1 - FMHA** | Online softmax Fused MHA (64×64 tile) | `F.scaled_dot_product_attention` | Reduces memory bandwidth pressure by fusing QK multiplication, Softmax, and PV reduction. |
| **2 - LLM-from-scratch** | FMHA Prefill + Decode (KV-Cache & CUDA Graph enabled) | GPT-2 Block with PyTorch attention | Bypasses Python launch latency during token-by-token decoding via static graphs. |
| **3 - nano-vllm** | PagedAttention & Green Contexts | PyTorch SDPA | Aims to eliminate VRAM fragmentation and compute interference in concurrent execution. |

All measurements use **warm-up (5–20×) and repeated runs (20–100×)** with `torch.cuda.synchronize()` to guarantee accurate GPU timings. Numerical correctness is verified using `torch.allclose` or exact output token matching.

---

## 4. Co-work Workflow (Tech Lead & Experiment Runner)

Since the experiments run on the **RTX 5070** target machine, we will collaborate as follows:

1. **Tech Lead (AI)**:
   - Authors and refactors cuTile kernels and wrapper scripts.
   - Designs benchmark suites to capture execution metrics.
   - Evaluates execution logs, profiles kernel performance, and drafts academic paper segments.
2. **Experiment Runner (User)**:
   - Runs the benchmark scripts locally on the RTX 5070.
   - Passes execution output, raw timing tables, and console logs back to the Tech Lead.
   - Provides feedback on performance bottlenecks and system configurations.

### RTX 5070 Optimization Directives:
- **Compute Capability**: Blackwell (SM 100/101).
- **Precision**: Tensors are cast to `float16` to leverage NVIDIA Tensor Cores.
- **Tiling Bounds**: Prefill uses $64 \times 64$ FMHA tiling (proved to yield optimal occupancy and SM utilization).
- **Graph Compilation**: Autoregressive decode steps are captured in CUDA Graphs using static cache buffers to eliminate Python host-side dispatch overhead.

---

## 5. How to Run the Comparisons

### Step 0: Prerequisites & Environment
Ensure PyTorch (with CUDA support) and the `cuda-python` / `cuda.tile` libraries are installed in your Python environment.

### Step 1: Matrix Multiplication Benchmark (`0-cuTile`)
To compare raw GEMM performance:
```bash
python 0-cuTile/cutile_matmul_perf.py
```

### Step 2: Fused Multi-Head Attention Benchmark (`1-FMHA`)
To run correctness verification and performance analysis of the raw attention kernel:
```bash
python 1-FMHA/AttentionFMHA.py --correctness-check
```

### Step 3: End-to-End LLM Inference (KV-Cache Aware)
To compare PyTorch and cuTile attention with KV-Cache during text generation:
```bash
python 2-LLM-from-scratch/compare_infer.py
```

### Step 4: CUDA Graph Acceleration Benchmark
To run the full comparison showing the speedup obtained by bypassing Python launch overhead with CUDA Graphs:
```bash
python 2-LLM-from-scratch/compare_infer_cuda_graph.py
```

---

## 6. Target Performance Goals

On the target RTX 5070 GPU, we aim for the following outcomes:

- **MatMul**: 1.2–1.5× higher TFLOPS than PyTorch for large matrix dimensions ($N \ge 2048$) through optimal L1 caching and register utilization.
- **FMHA**: Stable prefill latencies and lower memory bandwidth bottlenecking.
- **LLM-from-scratch (Raw)**: Consistent prefill performance with `T >= 64` sequences.
- **LLM-from-scratch (CUDA Graphs)**: **>2.0× speedup** in token-per-second decoding throughput over raw cuTile execution by resolving host-side dispatch overhead.
