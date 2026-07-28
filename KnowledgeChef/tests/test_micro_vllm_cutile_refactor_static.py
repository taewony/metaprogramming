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
