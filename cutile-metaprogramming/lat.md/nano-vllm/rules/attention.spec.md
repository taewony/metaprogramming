---
id: SPEC-ATTN-01
level: 1
type: system_spec
domain: attention
target_symbols:
  - "model.CausalSelfAttention.forward"
hardware_constraints:
  architecture: "Ampere/AdaLovelace/Hopper"
  max_shared_memory_per_block_kb: 48
  warp_size: 32
rules:
  - id: ATTN-ONLINE-SOFTMAX
    description: "Online softmax with running m, l for numerical stability"
    constraint: |
      The kernel must use online softmax:
      - track running max (m) and running sum (l) per row
      - rescale previous accumulated output when new max is larger
      - final division by l after loop
    enforcement: hard
    condition:
      kernel_type: flash_attention
  - id: ATTN-CAUSAL-MASK
    description: "Causal masking: prevent attending to future positions"
    constraint: |
      For each query position, only keys up to that position (inclusive) are allowed.
      Implement via early loop termination or explicit mask where mask[seq_q, seq_k] = -inf for seq_k > seq_q.
      The baseline uses `self.bias[:,:,:T,:T] == 0`; this must be preserved in cuTile.
    enforcement: hard
    condition:
      causal: true
  - id: ATTN-SCALING
    description: "Scale dot products by 1/sqrt(d_head)"
    constraint: "Apply scaling factor `1.0 / math.sqrt(head_dim)` to QK^T before softmax."
    enforcement: hard
    condition: null
  - id: ATTN-TILE-POWER-OF-2
    description: "Tile dimensions must be powers of 2"
    constraint: "BLOCK_M, BLOCK_N, BLOCK_K ∈ {16, 32, 64, 128}"
    enforcement: hard
    condition: null
  - id: ATTN-PURE-CUTILE-FORWARD
    description: "Pure cuTile forward path: no PyTorch/Triton compute in forward()"
    constraint: |
      All compute must be inside @ct.kernel + ct.launch.
      No nn.Linear, F.scaled_dot_product_attention, or custom Triton kernels.
      Weights can be stored in __init__ but extracted and passed to ct.launch.
    enforcement: hard
    condition: null
  - id: ATTN-KV-CACHE-INTEGRATION
    description: "Support paged KV cache with block indexing"
    constraint: |
      The kernel must accept a block_table and paged KV cache.
      Load K, V tiles via ct.load using block_table indices.
      This is a soft requirement for later integration; initially may use contiguous tensors.
    enforcement: soft
    condition:
      integrated: true
---

# Specification: CausalSelfAttention to cuTile Migration

## 1. Input/Output Tensor Semantics (지각적 공간 정의)
이 커널은 표준 PyTorch 인과 관계 어텐션(Causal Attention)의 순방향 연산을 대체한다.
* **Input Q, K, V Tensors:** 형태는 `[B, T, NH, HS]` 이며, 각각 Batch size, Sequence length, Number of heads, Head size를 의미한다.
* **Baseline PyTorch Expression:**
  ```python
  # 이 연산 구조를 cuTile의 Tile-based 매크로 연산으로 사상해야 함
  att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
  att = att.masked_fill(self.bias[:,:,:T,:T] == 0, float('-inf'))
  att = F.softmax(att, dim=-1)
  y = att @ v # [B, T, NH, HS]