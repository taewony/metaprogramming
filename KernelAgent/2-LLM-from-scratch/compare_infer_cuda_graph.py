import torch
import torch.nn as nn
import time
import argparse
import os
import sys
import numpy as np

# Ensure src directory is in path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from model import GPT as GPT_PyTorch, GPTConfig
from model_cutile import GPT as GPT_cuTile
from cutile_kernel import cutile_fmha

# =========================================================================
# Static Model Runner for CUDA Graph Capture
# =========================================================================
class StaticGPTRunner(nn.Module):
    """
    Wraps the cuTile GPT model with pre-allocated static KV cache buffers.
    This allows capturing a 100% static execution graph during the decoding loop,
    completely bypassing dynamic shape allocations and pointer mutations.
    """
    def __init__(self, model_cu, max_seq_len=1024):
        super().__init__()
        self.model = model_cu
        self.max_seq_len = max_seq_len
        self.config = model_cu.config
        
        # Pre-allocate static KV Cache buffers for each layer
        self.static_k = []
        self.static_v = []
        for _ in range(self.config.n_layer):
            # Shape: [Batch, Heads, MaxSeqLen, HeadDim]
            k_buf = torch.zeros((1, self.config.n_head, max_seq_len, self.config.n_embd // self.config.n_head),
                                dtype=torch.float16, device='cuda')
            v_buf = torch.zeros((1, self.config.n_head, max_seq_len, self.config.n_embd // self.config.n_head),
                                dtype=torch.float16, device='cuda')
            self.static_k.append(k_buf)
            self.static_v.append(v_buf)

        # Pre-allocate static inputs/outputs for the captured graph step
        self.static_input = torch.zeros((1, 1), dtype=torch.long, device='cuda')
        self.static_step = torch.zeros((1,), dtype=torch.long, device='cuda')
        self.static_logits = None

    def reset_cache(self, prompt_tokens):
        """
        Initializes the static cache with prompt keys/values and fills the remaining
        slots with a large negative value (-10000.0) so they are masked out in softmax.
        """
        # Initialize KV Cache buffers with -10000.0 (safely masks out unpopulated steps in FP16)
        for i in range(self.config.n_layer):
            self.static_k[i].fill_(-10000.0)
            self.static_v[i].fill_(0.0)  # Values can be zero since keys are masked out

        # Compute prompt keys/values
        device = next(self.model.parameters()).device
        idx = torch.tensor([prompt_tokens], dtype=torch.long, device=device)
        
        # We run the prefill forward pass once and capture the KV Cache
        self.model.eval()
        with torch.no_grad():
            # Extract key/values from the standard prefill pass
            logits, past_key_values = self.model(idx, use_cache=True)
            
            # Copy prefill key/values into our static buffers
            prefill_len = len(prompt_tokens)
            for i in range(self.config.n_layer):
                pk, pv = past_key_values[i]
                # Copy into the static cache prefix slice
                self.static_k[i][:, :, :prefill_len, :].copy_(pk)
                self.static_v[i][:, :, :prefill_len, :].copy_(pv)
                
        return logits, prefill_len

    def forward_step(self, next_token, step_idx):
        """
        Runs a single decoding step using the pre-allocated static buffers.
        """
        # step_idx is a 1-element GPU tensor containing the current step index
        B, T = next_token.shape
        pos = step_idx
        
        # Token & Position embeddings
        tok_emb = self.model.transformer.wte(next_token)
        pos_emb = self.model.transformer.wpe(pos)
        x = tok_emb + pos_emb

        for i, block in enumerate(self.model.transformer.h):
            # Layer Normalization before Attention
            normed = block.ln_1(x)
            
            # Compute new Q, K, V
            qkv = block.attn.c_attn(normed)
            q, k, v = qkv.split(self.config.n_embd, dim=2)
            
            head_dim = self.config.n_embd // self.config.n_head
            q = q.view(B, T, self.config.n_head, head_dim).transpose(1, 2).contiguous()
            k = k.view(B, T, self.config.n_head, head_dim).transpose(1, 2).contiguous()
            v = v.view(B, T, self.config.n_head, head_dim).transpose(1, 2).contiguous()

            # Write the new key & value in-place to the static buffers at step_idx
            self.static_k[i].index_copy_(2, step_idx, k)
            self.static_v[i].index_copy_(2, step_idx, v)

            # Launch cuTile attention over the static buffers
            # By passing causal=False and using the static cache (where future slots are -10000.0),
            # the attention runs with 100% static shapes while correctly ignoring unpopulated steps.
            y = cutile_fmha(
                Q=q, K=self.static_k[i], V=self.static_v[i],
                tile_m=64, tile_n=64,
                causal=False,
                input_pos=0
            )

            # Reshape back and add residual connection
            y = y.transpose(1, 2).contiguous().view(B, T, self.config.n_embd)
            x = x + block.attn.c_proj(y)
            
            # MLP block
            x = x + block.mlp(block.ln_2(x))

        # Final LayerNorm & LM Head
        x = self.model.transformer.ln_f(x)
        logits = self.model.lm_head(x)
        return logits


@torch.no_grad()
def timed_generate_pytorch(model, prompt, stoi, max_new_tokens=200):
    device = next(model.parameters()).device
    tokens = [stoi[c] for c in prompt if c in stoi]
    idx = torch.tensor([tokens], dtype=torch.long, device=device)

    model.eval()
    torch.cuda.synchronize()
    t_start = time.perf_counter()
    
    # Prefill
    logits, past_key_values = model(idx, use_cache=True)
    next_token = logits[:, -1, :].argmax(dim=-1, keepdim=True)
    torch.cuda.synchronize()
    t_first = time.perf_counter()
    
    generated = [next_token.item()]
    
    # Decode
    for _ in range(max_new_tokens - 1):
        logits, past_key_values = model(next_token, past_key_values=past_key_values, use_cache=True)
        next_token = logits[:, -1, :].argmax(dim=-1, keepdim=True)
        generated.append(next_token.item())
        
    torch.cuda.synchronize()
    t_end = time.perf_counter()
    return t_first - t_start, t_end - t_start, generated


@torch.no_grad()
def timed_generate_cutile_raw(model, prompt, stoi, max_new_tokens=200):
    device = next(model.parameters()).device
    tokens = [stoi[c] for c in prompt if c in stoi]
    idx = torch.tensor([tokens], dtype=torch.long, device=device)

    model.eval()
    torch.cuda.synchronize()
    t_start = time.perf_counter()
    
    # Prefill
    logits, past_key_values = model(idx, use_cache=True)
    next_token = logits[:, -1, :].argmax(dim=-1, keepdim=True)
    torch.cuda.synchronize()
    t_first = time.perf_counter()
    
    generated = [next_token.item()]
    
    # Decode
    for _ in range(max_new_tokens - 1):
        logits, past_key_values = model(next_token, past_key_values=past_key_values, use_cache=True)
        next_token = logits[:, -1, :].argmax(dim=-1, keepdim=True)
        generated.append(next_token.item())
        
    torch.cuda.synchronize()
    t_end = time.perf_counter()
    return t_first - t_start, t_end - t_start, generated


@torch.no_grad()
def timed_generate_cutile_graph(runner, prompt, stoi, max_new_tokens=200):
    tokens = [stoi[c] for c in prompt if c in stoi]
    
    torch.cuda.synchronize()
    t_start = time.perf_counter()
    
    # 1. Prefill and initialize cache
    logits, prefill_len = runner.reset_cache(tokens)
    next_token = logits[:, -1, :].argmax(dim=-1, keepdim=True)
    torch.cuda.synchronize()
    t_first = time.perf_counter()
    
    generated = [next_token.item()]
    
    # 2. CUDA Graph Capture for the decode step (re-use static graph if already captured)
    # To capture, we run a single warmup execution, then record on the CUDA stream.
    # PyTorch's native CUDAGraph API captures all stream dispatches (including custom cuTile kernels).
    g = torch.cuda.CUDAGraph()
    
    # Set initial values for graph capture
    runner.static_input.copy_(next_token)
    runner.static_step.copy_(torch.tensor([prefill_len], device='cuda'))
    
    # Capture step
    with torch.cuda.graph(g):
        runner.static_logits = runner.forward_step(runner.static_input, runner.static_step)
        
    # 3. Decode Loop using the replayed CUDA Graph
    next_token_tensor = next_token.clone()
    for step in range(prefill_len, prefill_len + max_new_tokens - 1):
        # Update inputs in-place without changing memory addresses
        runner.static_input.copy_(next_token_tensor)
        runner.static_step.copy_(torch.tensor([step], device='cuda'))
        
        # Replay the CUDA graph (bypasses all PyTorch dispatch & Python launch overheads!)
        g.replay()
        
        # Sample next token
        next_token_tensor = runner.static_logits[:, -1, :].argmax(dim=-1, keepdim=True)
        generated.append(next_token_tensor.item())
        
    torch.cuda.synchronize()
    t_end = time.perf_counter()
    return t_first - t_start, t_end - t_start, generated


def benchmark(model_type, model_or_runner, prompt, stoi, warmup=5, repeats=20, max_new_tokens=200):
    # Warmup
    for _ in range(warmup):
        if model_type == 'pytorch':
            _ = timed_generate_pytorch(model_or_runner, prompt, stoi, max_new_tokens)
        elif model_type == 'cutile_raw':
            _ = timed_generate_cutile_raw(model_or_runner, prompt, stoi, max_new_tokens)
        elif model_type == 'cutile_graph':
            _ = timed_generate_cutile_graph(model_or_runner, prompt, stoi, max_new_tokens)
            
    ttfts = []
    totals = []
    last_tokens = None
    
    for _ in range(repeats):
        if model_type == 'pytorch':
            ttft, total, tokens = timed_generate_pytorch(model_or_runner, prompt, stoi, max_new_tokens)
        elif model_type == 'cutile_raw':
            ttft, total, tokens = timed_generate_cutile_raw(model_or_runner, prompt, stoi, max_new_tokens)
        elif model_type == 'cutile_graph':
            ttft, total, tokens = timed_generate_cutile_graph(model_or_runner, prompt, stoi, max_new_tokens)
            
        ttfts.append(ttft)
        totals.append(total)
        last_tokens = tokens
        
    return np.array(ttfts), np.array(totals), last_tokens


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark PyTorch vs raw cuTile vs cuTile + CUDA Graphs")
    parser.add_argument("--checkpoint", default="checkpoint_final.pt", help="Path to checkpoint file")
    parser.add_argument("--warmup", type=int, default=5, help="Number of warmup runs")
    parser.add_argument("--repeats", type=int, default=20, help="Number of measurement runs")
    parser.add_argument("--max_new_tokens", type=int, default=200, help="Number of tokens to generate")
    args = parser.parse_args()

    long_prompt = (
        "O Romeo, Romeo! wherefore art thou Romeo? Deny thy father and refuse thy name; "
        "Or, if thou wilt not, be but sworn my love, and I'll no longer be a Capulet. "
        "'Tis but thy name that is my enemy; thou art thyself, though not a Montague. "
        "What's Montague? it is nor hand, nor foot, nor arm, nor face, nor any other part "
        "belonging to a man. O, be some other name! What's in a name? that which we call a rose "
        "by any other name would smell as sweet; so Romeo would, were he not Romeo call'd, "
        "retain that dear perfection which he owes without that title. Romeo, doff thy name, "
        "and for that name which is no part of thee take all myself."
    )
    
    if os.path.exists(args.checkpoint):
        print(f"Loading checkpoint from {args.checkpoint}...")
        checkpoint = torch.load(args.checkpoint, weights_only=False, map_location='cuda')
        config = checkpoint["config"]
        stoi = checkpoint["stoi"]
        itos = checkpoint["itos"]
        
        model_pt = GPT_PyTorch(config)
        model_pt.load_state_dict(checkpoint["model_state_dict"])
    else:
        print(f"Checkpoint '{args.checkpoint}' not found.")
        print("Using standard comparison configuration from design guide with random weights...")
        chars = sorted(list(set(long_prompt)))
        stoi = {c: i for i, c in enumerate(chars)}
        itos = {i: c for c, i in stoi.items()}
        
        config = GPTConfig(
            vocab_size=len(chars),
            block_size=1024,
            n_layer=6,
            n_head=12,
            n_embd=768
        )
        model_pt = GPT_PyTorch(config)

    model_pt = model_pt.half().to('cuda')
    
    # Initialize cuTile models
    model_cu = GPT_cuTile(config).half().to('cuda')
    model_cu.load_state_dict(model_pt.state_dict())
    
    runner_graph = StaticGPTRunner(model_cu, max_seq_len=1024)
    
    print("\nStarting benchmark...")
    print(f"Prompt length: {len(long_prompt)} characters")
    print(f"Generating {args.max_new_tokens} tokens per run over {args.repeats} repeats (with {args.warmup} warmups)")
    print(f"Model Configuration: {config.n_layer} Layers | {config.n_head} Heads | {config.n_embd} Embedding Dim")
    
    # 1. Benchmark PyTorch
    print("\nBenchmarking PyTorch Native Attention...")
    pt_ttfts, pt_totals, pt_tokens = benchmark(
        'pytorch', model_pt, long_prompt, stoi, warmup=args.warmup, repeats=args.repeats, max_new_tokens=args.max_new_tokens
    )
    
    # 2. Benchmark cuTile Raw
    print("Benchmarking cuTile Attention (Raw)...")
    cu_ttfts, cu_totals, cu_tokens = benchmark(
        'cutile_raw', model_cu, long_prompt, stoi, warmup=args.warmup, repeats=args.repeats, max_new_tokens=args.max_new_tokens
    )
    
    # 3. Benchmark cuTile + CUDA Graphs
    print("Benchmarking cuTile Attention + CUDA Graphs...")
    graph_ttfts, graph_totals, graph_tokens = benchmark(
        'cutile_graph', runner_graph, long_prompt, stoi, warmup=args.warmup, repeats=args.repeats, max_new_tokens=args.max_new_tokens
    )
    
    # Calculate statistics (ms)
    pt_ttft_mean, pt_ttft_std = np.mean(pt_ttfts) * 1000, np.std(pt_ttfts) * 1000
    pt_total_mean, pt_total_std = np.mean(pt_totals) * 1000, np.std(pt_totals) * 1000
    pt_dec_speed = (args.max_new_tokens - 1) / (pt_totals - pt_ttfts)
    pt_dec_mean, pt_dec_std = np.mean(pt_dec_speed), np.std(pt_dec_speed)
    
    cu_ttft_mean, cu_ttft_std = np.mean(cu_ttfts) * 1000, np.std(cu_ttfts) * 1000
    cu_total_mean, cu_total_std = np.mean(cu_totals) * 1000, np.std(cu_totals) * 1000
    cu_dec_speed = (args.max_new_tokens - 1) / (cu_totals - cu_ttfts)
    cu_dec_mean, cu_dec_std = np.mean(cu_dec_speed), np.std(cu_dec_speed)
    
    graph_ttft_mean, graph_ttft_std = np.mean(graph_ttfts) * 1000, np.std(graph_ttfts) * 1000
    graph_total_mean, graph_total_std = np.mean(graph_totals) * 1000, np.std(graph_totals) * 1000
    graph_dec_speed = (args.max_new_tokens - 1) / (graph_totals - graph_ttfts)
    graph_dec_mean, graph_dec_std = np.mean(graph_dec_speed), np.std(graph_dec_speed)
    
    # Verification
    pt_cu_match = (pt_tokens == cu_tokens)
    cu_graph_match = (cu_tokens == graph_tokens)
    
    print("\n" + "="*95)
    print("                                      BENCHMARK RESULTS")
    print("="*95)
    print(f"Metrics             | Baseline PyTorch       | cuTile Attention (Raw) | cuTile + CUDA Graphs   | Graph Speedup")
    print("-"*95)
    print(f"TTFT (Prefill)      | {pt_ttft_mean:7.2f} ± {pt_ttft_std:5.2f} ms | {cu_ttft_mean:7.2f} ± {cu_ttft_std:5.2f} ms | {graph_ttft_mean:7.2f} ± {graph_ttft_std:5.2f} ms | {cu_ttft_mean/graph_ttft_mean:6.3f}x")
    print(f"Total Response Time | {pt_total_mean:7.2f} ± {pt_total_std:5.2f} ms | {cu_total_mean:7.2f} ± {cu_total_std:5.2f} ms | {graph_total_mean:7.2f} ± {graph_total_std:5.2f} ms | {cu_total_mean/graph_total_mean:6.3f}x")
    print(f"Decoding Speed      | {pt_dec_mean:7.2f} ± {pt_dec_std:5.2f} t/s| {cu_dec_mean:7.2f} ± {cu_dec_std:5.2f} t/s| {graph_dec_mean:7.2f} ± {graph_dec_std:5.2f} t/s| {graph_dec_mean/cu_dec_mean:6.3f}x")
    print("="*95)
    print(f"Accuracy Verifications:")
    print(f"  ➔ PyTorch vs cuTile (Raw) Match Check   : {'PASSED' if pt_cu_match else 'FAILED'}")
    print(f"  ➔ cuTile (Raw) vs cuTile (Graph) Match : {'PASSED' if cu_graph_match else 'FAILED'}")
