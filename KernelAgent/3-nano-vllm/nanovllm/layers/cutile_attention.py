import math
import torch
import numpy as np

HAS_CUTILE = False
try:
    import cuda.tile as ct
    from cuda.tile import RoundingMode as RMd
    HAS_CUTILE = True
except ImportError:
    pass

if HAS_CUTILE:
    INV_LOG_2 = 1.0 / math.log(2)
    ConstInt = ct.Constant[int]
    ConstBool = ct.Constant[bool]

    @ct.kernel(occupancy=2)
    def fmha_prefill_kernel(Q, K, V, Out,
                            qk_scale: float,
                            TILE_D: ConstInt,
                            H: ConstInt,
                            TILE_M: ConstInt,
                            TILE_N: ConstInt,
                            QUERY_GROUP_SIZE: ConstInt,
                            CAUSAL: ConstBool):
        bid_x = ct.bid(0)
        bid_y = ct.bid(1)
        batch_idx = bid_y // H
        head_idx = bid_y % H
        off_kv_h = head_idx // QUERY_GROUP_SIZE

        qk_scale = qk_scale * INV_LOG_2

        offs_m = bid_x * TILE_M + ct.arange(TILE_M, dtype=np.int32)
        offs_m = offs_m[:, None]

        offs_n_tile = ct.arange(TILE_N, dtype=np.int32)
        offs_n_tile = offs_n_tile[None, :]

        m_i = ct.full((TILE_M, 1), -np.inf, dtype=np.float32)
        l_i = ct.full((TILE_M, 1), 0.0, dtype=np.float32)
        acc = ct.full((TILE_M, TILE_D), 0.0, dtype=np.float32)

        q = ct.load(
            Q, index=(batch_idx, head_idx, bid_x, 0), shape=(1, 1, TILE_M, TILE_D),
            padding_mode=ct.PaddingMode.ZERO,
            latency=2
        ).reshape((TILE_M, TILE_D))
        
        k_seqlen = K.shape[2]
        m_end = (bid_x + 1) * TILE_M
        if CAUSAL:
            mask_start = (bid_x * TILE_M) // TILE_N
            mask_start = min(mask_start, k_seqlen // TILE_N)
            Tc = ct.cdiv(min(m_end, k_seqlen), TILE_N)
        else:
            Tc = ct.cdiv(k_seqlen, TILE_N)
            mask_start = k_seqlen // TILE_N

        for j in range(0, Tc):
            k = ct.load(
                K, index=(batch_idx, off_kv_h, 0, j), shape=(1, 1, TILE_D, TILE_N),
                order=(0, 1, 3, 2),
                padding_mode=ct.PaddingMode.ZERO,
                latency=2
            ).reshape((TILE_D, TILE_N))
            
            qk = ct.full((TILE_M, TILE_N), 0., dtype=np.float32)
            qk = ct.mma(q, k, qk)

            if CAUSAL and j >= mask_start:
                offs_n = j * TILE_N + offs_n_tile
                mask = ct.where(offs_m >= offs_n, 0.0, -np.inf)
                qk += mask

            m_ij = max(m_i, ct.max(qk, axis=-1, keepdims=True) * qk_scale)
            qk = qk * qk_scale - m_ij

            p = ct.exp2(qk, flush_to_zero=True)
            l_ij = ct.sum(p, axis=-1, keepdims=True)
            alpha = ct.exp2(m_i - m_ij, flush_to_zero=True)
            
            l_i = l_i * alpha + l_ij
            acc = acc * alpha

            v = ct.load(
                V, index=(batch_idx, off_kv_h, j, 0), shape=(1, 1, TILE_N, TILE_D),
                padding_mode=ct.PaddingMode.ZERO,
                latency=4
            ).reshape((TILE_N, TILE_D))

            p = p.astype(Q.dtype)
            acc = ct.mma(p, v, acc)
            m_i = m_ij

        acc = ct.truediv(acc, l_i, flush_to_zero=True, rounding_mode=RMd.APPROX)
        acc = acc.reshape((1, 1, TILE_M, TILE_D)).astype(Out.dtype)
        ct.store(Out, index=(batch_idx, head_idx, bid_x, 0), tile=acc)

    @ct.kernel(occupancy=2)
    def paged_decode_kernel(
        Q, K_cache, V_cache, block_table, context_lens, Out,
        qk_scale: float,
        TILE_D: ConstInt,
        H: ConstInt,
        QUERY_GROUP_SIZE: ConstInt,
        BLOCK_SIZE: ConstInt,
    ):
        bid_y = ct.bid(0) # maps to Batch * Heads
        batch_idx = bid_y // H
        head_idx = bid_y % H
        off_kv_h = head_idx // QUERY_GROUP_SIZE

        # Get the context length for this batch item
        cur_len = ct.load(context_lens, index=(batch_idx,), shape=(1,)).reshape(())

        qk_scale = qk_scale * INV_LOG_2

        # Q shape: (B, H, 1, D)
        q = ct.load(
            Q, index=(batch_idx, head_idx, 0, 0), shape=(1, 1, 1, TILE_D),
            padding_mode=ct.PaddingMode.ZERO
        ).reshape((1, TILE_D))

        m_i = ct.full((1, 1), -np.inf, dtype=np.float32)
        l_i = ct.full((1, 1), 0.0, dtype=np.float32)
        acc = ct.full((1, TILE_D), 0.0, dtype=np.float32)

        # Number of blocks for this sequence
        num_seq_blocks = ct.cdiv(cur_len, BLOCK_SIZE)

        for j in range(0, num_seq_blocks):
            physical_block_id = ct.load(block_table, index=(batch_idx, j), shape=(1, 1)).reshape(())

            # Load K block and transpose it to (TILE_D, BLOCK_SIZE)
            k = ct.load(
                K_cache, index=(physical_block_id, 0, off_kv_h, 0), shape=(1, BLOCK_SIZE, 1, TILE_D),
                order=(0, 3, 2, 1),
                padding_mode=ct.PaddingMode.ZERO
            ).reshape((TILE_D, BLOCK_SIZE))

            qk = ct.full((1, BLOCK_SIZE), 0., dtype=np.float32)
            qk = ct.mma(q, k, qk)

            # Apply masking for the last block if it is partially filled
            if j == num_seq_blocks - 1:
                offs_n = j * BLOCK_SIZE + ct.arange(BLOCK_SIZE, dtype=np.int32)[None, :]
                mask = ct.where(offs_n < cur_len, 0.0, -np.inf)
                qk += mask

            m_ij = max(m_i, ct.max(qk, axis=-1, keepdims=True) * qk_scale)
            qk = qk * qk_scale - m_ij

            p = ct.exp2(qk, flush_to_zero=True)
            l_ij = ct.sum(p, axis=-1, keepdims=True)
            alpha = ct.exp2(m_i - m_ij, flush_to_zero=True)
            
            l_i = l_i * alpha + l_ij
            acc = acc * alpha

            # Load V block: shape (BLOCK_SIZE, TILE_D)
            v = ct.load(
                V_cache, index=(physical_block_id, 0, off_kv_h, 0), shape=(1, BLOCK_SIZE, 1, TILE_D),
                padding_mode=ct.PaddingMode.ZERO
            ).reshape((BLOCK_SIZE, TILE_D))

            p = p.astype(Q.dtype)
            acc = ct.mma(p, v, acc)
            m_i = m_ij

        acc = ct.truediv(acc, l_i, flush_to_zero=True, rounding_mode=RMd.APPROX)
        acc = acc.reshape((1, 1, 1, TILE_D)).astype(Out.dtype)
        ct.store(Out, index=(batch_idx, head_idx, 0, 0), tile=acc)


def cutile_fmha_prefill(
    q: torch.Tensor, k: torch.Tensor, v: torch.Tensor,
    cu_seqlens_q: torch.Tensor, cu_seqlens_k: torch.Tensor,
    max_seqlen_q: int, max_seqlen_k: int, scale: float, causal: bool
) -> torch.Tensor:
    if not HAS_CUTILE:
        raise RuntimeError("cuTile is not installed or import failed.")

    # Convert inputs to 4D padded tensors
    # Use tile size of 64 or 128 (let's use 64 for compatibility and smaller limits)
    tile_m, tile_n = 64, 64
    
    # Pad seqlen to a multiple of tile size, with a minimum of 64
    pad_len_q = max(64, math.ceil(max_seqlen_q / tile_m) * tile_m)
    pad_len_k = max(64, math.ceil(max_seqlen_k / tile_n) * tile_n)
    
    B = cu_seqlens_q.numel() - 1
    total_tokens_q = q.shape[0]
    num_heads = q.shape[1]
    num_kv_heads = k.shape[1]
    head_dim = q.shape[2]

    # Reconstruct padded 4D tensors: (B, H, SeqLen, D)
    q_4d = torch.zeros((B, num_heads, pad_len_q, head_dim), dtype=q.dtype, device=q.device)
    k_4d = torch.zeros((B, num_kv_heads, pad_len_k, head_dim), dtype=k.dtype, device=k.device)
    v_4d = torch.zeros((B, num_kv_heads, pad_len_k, head_dim), dtype=v.dtype, device=v.device)
    
    for b in range(B):
        # Q
        start_q = cu_seqlens_q[b].item()
        end_q = cu_seqlens_q[b+1].item()
        seqlen_q = end_q - start_q
        q_4d[b, :, :seqlen_q, :] = q[start_q:end_q].transpose(0, 1)
        
        # K, V
        start_k = cu_seqlens_k[b].item()
        end_k = cu_seqlens_k[b+1].item()
        seqlen_k = end_k - start_k
        k_4d[b, :, :seqlen_k, :] = k[start_k:end_k].transpose(0, 1)
        v_4d[b, :, :seqlen_k, :] = v[start_k:end_k].transpose(0, 1)

    Out = torch.empty((B, num_heads, pad_len_q, head_dim), dtype=q.dtype, device=q.device)

    grid_x = pad_len_q // tile_m
    grid_y = B * num_heads
    grid = (grid_x, grid_y, 1)
    query_group_size = num_heads // num_kv_heads

    ct.launch(torch.cuda.current_stream(), grid, fmha_prefill_kernel, (
        q_4d, k_4d, v_4d, Out,
        scale, head_dim, num_heads,
        tile_m, tile_n, query_group_size, causal
    ))

    # Pack the output back to (total_tokens, num_heads, head_dim)
    res = torch.empty((total_tokens_q, num_heads, head_dim), dtype=q.dtype, device=q.device)
    for b in range(B):
        start_q = cu_seqlens_q[b].item()
        end_q = cu_seqlens_q[b+1].item()
        seqlen_q = end_q - start_q
        res[start_q:end_q] = Out[b, :, :seqlen_q, :].transpose(0, 1)
        
    return res


def cutile_fmha_paged_decode(
    q: torch.Tensor, k_cache: torch.Tensor, v_cache: torch.Tensor,
    block_table: torch.Tensor, context_lens: torch.Tensor, scale: float,
    block_size: int
) -> torch.Tensor:
    if not HAS_CUTILE:
        raise RuntimeError("cuTile is not installed or import failed.")

    # q has shape (B, H, D)
    B, H, D = q.shape
    
    # Reshape Q to (B, H, 1, D) for the kernel
    q_4d = q.unsqueeze(2) # (B, H, 1, D)
    
    Out = torch.empty((B, H, 1, D), dtype=q.dtype, device=q.device)
    
    grid = (B * H, 1, 1)
    query_group_size = H // k_cache.shape[2]
    
    ct.launch(torch.cuda.current_stream(), grid, paged_decode_kernel, (
        q_4d, k_cache, v_cache, block_table, context_lens, Out, scale,
        D, H, query_group_size, block_size
    ))
    
    # Return (B, 1, H, D) to match flash_attn_with_kvcache
    return Out.transpose(1, 2)
