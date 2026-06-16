# compare_matmul.py
# cuTile matrix multiplication vs PyTorch matmul performance comparison
# Fixed tile size at 64, optimized for NVIDIA RTX 5070 GPU (SM 100/101)

import torch
import time
import numpy as np
import cuda.tile as ct

# ============================================================
# 1. cuTile Kernels
# ============================================================

TILE_M = 64
TILE_N = 64
TILE_K = 64

# ---- Version 1: cuTile Sample (32x32 Thread Block, 2x2 Register Blocking) ----
@ct.kernel(occupancy=2)
def matmul_sample(A, B, C, M, N, K):
    """
    Standard tiled matrix multiplication using 32x32 thread block (1024 threads).
    Each thread computes a 2x2 sub-tile of the 64x64 output block to stay within
    the CUDA limit of 1024 threads/block.
    """
    sm_A = ct.shared_tensor((64, 64), dtype=ct.float16)
    sm_B = ct.shared_tensor((64, 64), dtype=ct.float16)

    tx = ct.threadIdx.x
    ty = ct.threadIdx.y

    # 2x2 registers for accumulation
    accum_0_0 = ct.float32(0.0)
    accum_0_1 = ct.float32(0.0)
    accum_1_0 = ct.float32(0.0)
    accum_1_1 = ct.float32(0.0)

    num_k_blocks = ct.ceil_div(K, 64)
    for k_block in range(num_k_blocks):
        # Load A & B tiles into shared memory (each thread copies 4 elements)
        for i in range(2):
            for j in range(2):
                local_y = ty * 2 + i
                local_x = tx * 2 + j
                
                # A tile load
                g_row_A = ct.blockIdx.y * 64 + local_y
                g_col_A = k_block * 64 + local_x
                ct.copy(sm_A[local_y, local_x],
                        A[g_row_A, g_col_A],
                        mask=(g_row_A < M) & (g_col_A < K))
                
                # B tile load
                g_row_B = k_block * 64 + local_y
                g_col_B = ct.blockIdx.x * 64 + local_x
                ct.copy(sm_B[local_y, local_x],
                        B[g_row_B, g_col_B],
                        mask=(g_row_B < K) & (g_col_B < N))
                        
        ct.syncthreads()

        # Compute dot product
        for k in range(64):
            a0 = ct.float32(sm_A[ty * 2 + 0, k])
            a1 = ct.float32(sm_A[ty * 2 + 1, k])

            b0 = ct.float32(sm_B[k, tx * 2 + 0])
            b1 = ct.float32(sm_B[k, tx * 2 + 1])

            accum_0_0 += a0 * b0
            accum_0_1 += a0 * b1
            accum_1_0 += a1 * b0
            accum_1_1 += a1 * b1

        ct.syncthreads()

    # Store results to global memory C
    for i in range(2):
        for j in range(2):
            g_row_C = ct.blockIdx.y * 64 + ty * 2 + i
            g_col_C = ct.blockIdx.x * 64 + tx * 2 + j
            if g_row_C < M and g_col_C < N:
                if i == 0 and j == 0: val = accum_0_0
                elif i == 0 and j == 1: val = accum_0_1
                elif i == 1 and j == 0: val = accum_1_0
                elif i == 1 and j == 1: val = accum_1_1
                C[g_row_C, g_col_C] = ct.float16(val)


# ---- Version 2: Optimized TileGym Version (16x16 Thread Block, 4x4 Register Blocking) ----
@ct.kernel(occupancy=2)
def matmul_tilegym(A, B, C, M, N, K):
    """
    Optimized version using 16x16 thread block (256 threads).
    Each thread computes a 4x4 sub-tile of the 64x64 output block.
    Reduces shared memory read bandwidth pressure and increases ILP.
    """
    sm_A = ct.shared_tensor((64, 64), dtype=ct.float16)
    sm_B = ct.shared_tensor((64, 64), dtype=ct.float16)

    tx = ct.threadIdx.x
    ty = ct.threadIdx.y

    # 4x4 registers for accumulation
    accum_0_0 = ct.float32(0.0)
    accum_0_1 = ct.float32(0.0)
    accum_0_2 = ct.float32(0.0)
    accum_0_3 = ct.float32(0.0)
    accum_1_0 = ct.float32(0.0)
    accum_1_1 = ct.float32(0.0)
    accum_1_2 = ct.float32(0.0)
    accum_1_3 = ct.float32(0.0)
    accum_2_0 = ct.float32(0.0)
    accum_2_1 = ct.float32(0.0)
    accum_2_2 = ct.float32(0.0)
    accum_2_3 = ct.float32(0.0)
    accum_3_0 = ct.float32(0.0)
    accum_3_1 = ct.float32(0.0)
    accum_3_2 = ct.float32(0.0)
    accum_3_3 = ct.float32(0.0)

    num_k_blocks = ct.ceil_div(K, 64)
    for k_block in range(num_k_blocks):
        # Load A & B tiles into shared memory (each thread copies 16 elements total)
        for i in range(4):
            for j in range(4):
                local_y = ty * 4 + i
                local_x = tx * 4 + j
                
                # A tile load
                g_row_A = ct.blockIdx.y * 64 + local_y
                g_col_A = k_block * 64 + local_x
                ct.copy(sm_A[local_y, local_x],
                        A[g_row_A, g_col_A],
                        mask=(g_row_A < M) & (g_col_A < K))
                
                # B tile load
                g_row_B = k_block * 64 + local_y
                g_col_B = ct.blockIdx.x * 64 + local_x
                ct.copy(sm_B[local_y, local_x],
                        B[g_row_B, g_col_B],
                        mask=(g_row_B < K) & (g_col_B < N))
                        
        ct.syncthreads()

        # Compute dot product (unrolled loop accumulation)
        for k in range(64):
            # Load A values for this k-step
            a0 = ct.float32(sm_A[ty * 4 + 0, k])
            a1 = ct.float32(sm_A[ty * 4 + 1, k])
            a2 = ct.float32(sm_A[ty * 4 + 2, k])
            a3 = ct.float32(sm_A[ty * 4 + 3, k])

            # Load B values for this k-step
            b0 = ct.float32(sm_B[k, tx * 4 + 0])
            b1 = ct.float32(sm_B[k, tx * 4 + 1])
            b2 = ct.float32(sm_B[k, tx * 4 + 2])
            b3 = ct.float32(sm_B[k, tx * 4 + 3])

            # Multiply-accumulate
            accum_0_0 += a0 * b0
            accum_0_1 += a0 * b1
            accum_0_2 += a0 * b2
            accum_0_3 += a0 * b3

            accum_1_0 += a1 * b0
            accum_1_1 += a1 * b1
            accum_1_2 += a1 * b2
            accum_1_3 += a1 * b3

            accum_2_0 += a2 * b0
            accum_2_1 += a2 * b1
            accum_2_2 += a2 * b2
            accum_2_3 += a2 * b3

            accum_3_0 += a3 * b0
            accum_3_1 += a3 * b1
            accum_3_2 += a3 * b2
            accum_3_3 += a3 * b3

        ct.syncthreads()

    # Store results to global memory C
    for i in range(4):
        for j in range(4):
            g_row_C = ct.blockIdx.y * 64 + ty * 4 + i
            g_col_C = ct.blockIdx.x * 64 + tx * 4 + j
            if g_row_C < M and g_col_C < N:
                if i == 0 and j == 0: val = accum_0_0
                elif i == 0 and j == 1: val = accum_0_1
                elif i == 0 and j == 2: val = accum_0_2
                elif i == 0 and j == 3: val = accum_0_3
                elif i == 1 and j == 0: val = accum_1_0
                elif i == 1 and j == 1: val = accum_1_1
                elif i == 1 and j == 2: val = accum_1_2
                elif i == 1 and j == 3: val = accum_1_3
                elif i == 2 and j == 0: val = accum_2_0
                elif i == 2 and j == 1: val = accum_2_1
                elif i == 2 and j == 2: val = accum_2_2
                elif i == 2 and j == 3: val = accum_2_3
                elif i == 3 and j == 0: val = accum_3_0
                elif i == 3 and j == 1: val = accum_3_1
                elif i == 3 and j == 2: val = accum_3_2
                elif i == 3 and j == 3: val = accum_3_3
                C[g_row_C, g_col_C] = ct.float16(val)


# ============================================================
# 2. Benchmarking Utilities
# ============================================================

def compute_tflops(M, N, K, time_sec):
    ops = 2 * M * N * K
    return ops / (time_sec * 1e12)


def benchmark_pytorch(A, B, warmup=20, repeats=100):
    C = torch.empty(A.shape[0], B.shape[1], dtype=torch.float16, device='cuda')
    for _ in range(warmup):
        torch.matmul(A, B, out=C)
    torch.cuda.synchronize()
    start = time.perf_counter()
    for _ in range(repeats):
        torch.matmul(A, B, out=C)
    torch.cuda.synchronize()
    elapsed = (time.perf_counter() - start) / repeats
    return C, elapsed


def benchmark_cutile(kernel, A, B, M, N, K, warmup=20, repeats=100):
    C = torch.empty(M, N, dtype=torch.float16, device='cuda')
    grid_dim = (ct.ceil_div(N, TILE_N), ct.ceil_div(M, TILE_M), 1)
    
    # Configure thread block dim based on kernel register layout
    if kernel == matmul_sample:
        block_dim = (32, 32, 1)  # 1024 threads
    else:
        block_dim = (16, 16, 1)  # 256 threads
        
    args = (A, B, C, M, N, K)

    for _ in range(warmup):
        ct.launch(kernel, grid_dim, block_dim, args=args)
    torch.cuda.synchronize()
    start = time.perf_counter()
    for _ in range(repeats):
        ct.launch(kernel, grid_dim, block_dim, args=args)
    torch.cuda.synchronize()
    elapsed = (time.perf_counter() - start) / repeats
    return C, elapsed


def verify(label, C_torch, C_cutile):
    if torch.allclose(C_torch, C_cutile, atol=1e-2, rtol=1e-2):
        print(f"  {label}: ✅ Correctness Check Passed")
        return True
    else:
        diff = (C_torch.float() - C_cutile.float()).abs().max().item()
        print(f"  {label}: ❌ Correctness Check Failed! Max diff = {diff:.4f}")
        return False


# ============================================================
# 3. Main Benchmark
# ============================================================

if __name__ == "__main__":
    print("="*75)
    print("cuTile Matrix Multiplication Benchmark - Tile Size 64 Fixed")
    print("Target GPU: RTX 5070 (Blackwell SM100/101) | Data Type: float16")
    print("="*75)

    sizes = [256, 512, 1024, 2048, 4096]
    results = []

    for size in sizes:
        M = N = K = size
        print(f"\n[Matrix Dimension {M}x{K} x {K}x{N}]")

        A = torch.randn(M, K, dtype=torch.float16, device='cuda')
        B = torch.randn(K, N, dtype=torch.float16, device='cuda')

        # 1. PyTorch Benchmark
        C_pt, t_pt = benchmark_pytorch(A, B)
        tflops_pt = compute_tflops(M, N, K, t_pt)

        # 2. cuTile Sample
        try:
            C_sample, t_sample = benchmark_cutile(matmul_sample, A, B, M, N, K)
            tflops_sample = compute_tflops(M, N, K, t_sample)
            ok_sample = verify("cuTile Sample", C_pt, C_sample)
        except Exception as e:
            print(f"  cuTile Sample Execution Error: {e}")
            ok_sample = False
            t_sample = float('inf')
            tflops_sample = 0.0

        # 3. cuTile TileGym (Optimized)
        try:
            C_tilegym, t_tilegym = benchmark_cutile(matmul_tilegym, A, B, M, N, K)
            tflops_tilegym = compute_tflops(M, N, K, t_tilegym)
            ok_tilegym = verify("cuTile TileGym", C_pt, C_tilegym)
        except Exception as e:
            print(f"  cuTile TileGym Execution Error: {e}")
            ok_tilegym = False
            t_tilegym = float('inf')
            tflops_tilegym = 0.0

        results.append((size, t_pt, tflops_pt, t_sample, tflops_sample, t_tilegym, tflops_tilegym))

        # Printing intermediate performance figures
        print(f"  PyTorch:           {t_pt*1000:.3f} ms ({tflops_pt:.2f} TFLOPS)")
        if ok_sample:
            speedup = t_pt / t_sample
            print(f"  cuTile Sample:     {t_sample*1000:.3f} ms ({tflops_sample:.2f} TFLOPS) | Speedup: {speedup:.2f}x")
        if ok_tilegym:
            speedup = t_pt / t_tilegym
            print(f"  cuTile TileGym:    {t_tilegym*1000:.3f} ms ({tflops_tilegym:.2f} TFLOPS) | Speedup: {speedup:.2f}x")

    # Summary Table
    print("\n" + "="*75)
    print("                    PERFORMANCE SUMMARY TABLE")
    print("="*75)
    print(f"{'Size':>8} | {'PyTorch':>18} | {'cuTile Sample':>18} | {'cuTile TileGym':>18}")
    print("-"*75)
    for (sz, pt, ptf, sp, spf, gy, gyf) in results:
        print(f"{sz:>8} | {pt*1000:>7.2f} ms ({ptf:>5.1f}T) | {sp*1000:>7.2f} ms ({spf:>5.1f}T) | {gy*1000:>7.2f} ms ({gyf:>5.1f}T)")
    print("-"*75)
