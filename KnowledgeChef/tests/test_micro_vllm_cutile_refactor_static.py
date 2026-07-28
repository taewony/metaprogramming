from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MICRO = ROOT / "KernelAgent" / "3-micro-vllm"


def read(path: str) -> str:
    return (MICRO / path).read_text(encoding="utf-8")


def test_cutile_does_not_force_eager_mode():
    source = read("nanovllm/engine/model_runner.py")
    assert "self.enforce_eager = config.enforce_eager or use_cutile" not in source
    assert "self.use_cutile = use_cutile" in source


def test_cutile_decode_graph_capture_is_documented_in_code():
    source = read("nanovllm/engine/model_runner.py")
    assert "capture_cudagraph" in source
    assert "self.use_cutile" in source
    assert "use_cutile=self.use_cutile" in source


def test_cutile_prefill_wrapper_avoids_padded_tensor_materialization():
    source = read("nanovllm/layers/cutile_attention.py")
    forbidden = [
        "q_4d = torch.zeros",
        "k_4d = torch.zeros",
        "v_4d = torch.zeros",
        "res[start_q:end_q]",
    ]
    for pattern in forbidden:
        assert pattern not in source

    assert "def _bhtd_view" in source
    assert "fmha_prefill_paged_kernel" in source


def test_cutile_kv_store_avoids_pytorch_advanced_indexing_path():
    source = read("nanovllm/layers/attention.py")
    assert "store_kvcache_cutile" in source
    assert "store_kvcache_cutile(key, value, k_cache, v_cache, slot_mapping)" in source
    use_cutile_branch = source[source.index("def store_kvcache("):source.index("class Attention")]
    assert "if use_cutile and HAS_CUTILE" in use_cutile_branch
    assert "slot_mapping[mask]" not in use_cutile_branch
