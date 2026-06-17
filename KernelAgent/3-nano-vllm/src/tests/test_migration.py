import os
import sys
import torch
import torch.nn as nn
import math

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.tests.utils import fix_seed, compare_outputs

# =========================================================================
# 1. Migrated PyTorch KV Cache Store implementation
# =========================================================================
def store_kvcache_pytorch(key: torch.Tensor, value: torch.Tensor, k_cache: torch.Tensor, v_cache: torch.Tensor, slot_mapping: torch.Tensor):
    """
    Pure PyTorch implementation of KV cache storing (eliminates Triton).
    """
    D = key.shape[1] * key.shape[2]  # num_heads * head_dim
    N = key.shape[0]
    
    # Flat views of KV cache and projections
    k_cache_flat = k_cache.view(-1, D)
    v_cache_flat = v_cache.view(-1, D)
    key_flat = key.view(-1, D)
    value_flat = value.view(-1, D)
    
    # Write only active slots (ignoring slots that map to -1)
    mask = slot_mapping != -1
    valid_slots = slot_mapping[mask].long()
    
    k_cache_flat[valid_slots] = key_flat[mask]
    v_cache_flat[valid_slots] = value_flat[mask]


def test_store_kvcache_cpu():
    """
    [TDD Step 1] Verify the pure PyTorch store_kvcache implementation on CPU.
    """
    print("\n[TDD Step 1] Verification of store_kvcache_pytorch (CPU)")
    fix_seed(42)
    
    # Dimensions: 4 tokens, 6 heads, 64 head_dim
    N, num_heads, head_dim = 4, 6, 64
    D = num_heads * head_dim
    num_blocks, block_size = 8, 16
    
    # Allocate cache buffers
    k_cache_ref = torch.zeros((num_blocks, block_size, num_heads, head_dim))
    v_cache_ref = torch.zeros((num_blocks, block_size, num_heads, head_dim))
    k_cache_target = torch.zeros((num_blocks, block_size, num_heads, head_dim))
    v_cache_target = torch.zeros((num_blocks, block_size, num_heads, head_dim))
    
    # New keys and values
    key = torch.randn(N, num_heads, head_dim)
    value = torch.randn(N, num_heads, head_dim)
    
    # Define slots to write to (including a -1 for padding/inactive token)
    slot_mapping = torch.tensor([5, 12, -1, 38], dtype=torch.int32)
    
    # 1. Reference: Eager loop implementation
    k_cache_ref_flat = k_cache_ref.view(-1, D)
    v_cache_ref_flat = v_cache_ref.view(-1, D)
    for idx in range(N):
        slot = slot_mapping[idx].item()
        if slot != -1:
            k_cache_ref_flat[slot] = key[idx].view(D)
            v_cache_ref_flat[slot] = value[idx].view(D)
            
    # 2. Target: PyTorch optimized implementation
    store_kvcache_pytorch(key, value, k_cache_target, v_cache_target, slot_mapping)
    
    # 3. Compare Results
    k_match = compare_outputs(k_cache_ref, k_cache_target)
    v_match = compare_outputs(v_cache_ref, v_cache_target)
    if k_match and v_match:
        print("✅ store_kvcache_pytorch Verification passed!")
    else:
        print("❌ store_kvcache_pytorch Verification failed!")


# =========================================================================
# 2. Prefill Causal Padding verification
# =========================================================================
def test_prefill_causal_padding_cpu():
    """
    [TDD Step 2] Verify the mathematical equivalence of causal padding.
    """
    print("\n[TDD Step 2] Verification of Causal Padding (CPU)")
    fix_seed(42)
    
    # Sequence length T = 32 (less than block size 64)
    B, H, T, D = 1, 6, 32, 64
    pad_len = 64 - T
    
    q = torch.randn(B, H, T, D)
    k = torch.randn(B, H, T, D)
    v = torch.randn(B, H, T, D)
    
    # 1. Reference: PyTorch Native Causal Attention on unpadded inputs
    q_ref = q
    k_ref = k
    v_ref = v
    o_ref = torch.nn.functional.scaled_dot_product_attention(q_ref, k_ref, v_ref, is_causal=True)
    
    # 2. Target: Causal attention on inputs padded to 64, then sliced back
    q_padded = torch.nn.functional.pad(q, (0, 0, 0, pad_len))
    k_padded = torch.nn.functional.pad(k, (0, 0, 0, pad_len))
    v_padded = torch.nn.functional.pad(v, (0, 0, 0, pad_len))
    
    o_padded = torch.nn.functional.scaled_dot_product_attention(q_padded, k_padded, v_padded, is_causal=True)
    o_target = o_padded[:, :, :T, :]
    
    # 3. Compare
    match = compare_outputs(o_ref, o_target)
    if match:
        print("✅ Causal Sequence Padding Verification passed!")
    else:
        print("❌ Causal Sequence Padding Verification failed!")


# =========================================================================
# 3. Paged KV Cache vs Contiguous KV Cache Attention verification
# =========================================================================
def test_paged_attention_lookup_cpu():
    """
    [TDD Step 3] Verify that retrieving from Paged KV Cache block table
    produces identical attention inputs to contiguous cache blocks.
    """
    print("\n[TDD Step 3] Verification of Paged KV Cache lookup mapping (CPU)")
    fix_seed(42)
    
    B, H, T_q, D = 1, 6, 1, 64  # Decode step: 1 token
    block_size = 16
    context_len = 35 # We have generated 35 tokens so far
    num_blocks = math.ceil(context_len / block_size)  # 3 blocks
    
    # Allocate contiguous KV Cache for comparison
    k_contiguous = torch.randn(B, H, context_len, D)
    
    # Allocate Paged KV Cache: [num_blocks, block_size, H, D]
    k_paged = torch.zeros(num_blocks, block_size, H, D)
    
    # Create block table mapping logical blocks to physical block IDs
    # Let's map logical blocks 0, 1, 2 to physical blocks 5, 2, 7
    block_table = [5, 2, 7]
    
    # Populate Paged cache using block table mapping
    for i in range(context_len):
        logical_block_idx = i // block_size
        block_offset = i % block_size
        physical_block_id = block_table[logical_block_idx]
        
        # Copy contiguous element to paged location
        k_paged[physical_block_id, block_offset, :, :] = k_contiguous[0, :, i, :]
        
    # Reconstruct contiguous cache back from paged cache using block table to verify mapping correctness
    k_reconstructed = torch.zeros(B, H, context_len, D)
    for i in range(context_len):
        logical_block_idx = i // block_size
        block_offset = i % block_size
        physical_block_id = block_table[logical_block_idx]
        
        k_reconstructed[0, :, i, :] = k_paged[physical_block_id, block_offset, :, :]
        
    match = compare_outputs(k_contiguous, k_reconstructed)
    if match:
        print("✅ Paged KV Cache block mapping Verification passed!")
    else:
        print("❌ Paged KV Cache block mapping Verification failed!")


if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Running nano-vllm migration TDD suite on device: {device}")
    
    test_store_kvcache_cpu()
    test_prefill_causal_padding_cpu()
    test_paged_attention_lookup_cpu()
