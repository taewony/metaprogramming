"""Preflight check for CUDA Green Context support on the target PC.

PyTorch GreenContext is treated as optional because the current target
installation can import it but rejects activation. The required path for the
paper benchmark is cuda.core resource partitioning with Device.set_current().
"""

from __future__ import annotations

import os
import traceback

import torch


def print_header(title: str) -> None:
    print(f"\n--- {title} ---")


def test_pytorch_green_context() -> bool:
    print_header("Testing PyTorch GreenContext")
    try:
        from torch.cuda.green_contexts import GreenContext
    except ImportError as exc:
        print(f"torch.cuda.green_contexts is not importable: {exc}")
        return False

    print("torch.cuda.green_contexts is importable")
    try:
        ctx = GreenContext.create(num_sms=16)
        print("GreenContext.create(num_sms=16) succeeded")
        ctx.set_context()
        print("ctx.set_context() succeeded")
        ctx.pop_context()
        print("ctx.pop_context() succeeded")
        return True
    except Exception as exc:
        print(f"GreenContext creation or activation failed: {exc}")
        return False


def first_resource(layout):
    if isinstance(layout, (list, tuple)):
        return layout[0]
    return layout


def two_resources(layout):
    if not isinstance(layout, (list, tuple)) or len(layout) < 2:
        raise RuntimeError(f"expected two SM resource groups, got {layout!r}")
    return layout[0], layout[1]


def test_cuda_core_green_context() -> bool:
    print_header("Testing cuda.core API")
    try:
        from cuda.bindings import driver as cuda
        from cuda.core import ContextOptions, Device, SMResourceOptions
    except ImportError as exc:
        print(f"cuda.core module or bindings are not importable: {exc}")
        return False

    print("cuda.core and cuda.bindings modules are importable")
    try:
        cuda.cuInit(0)
        dev = Device(0)
        dev.set_current()

        sm = dev.resources.sm
        total_sms = sm.sm_count
        prefill_sms = int(os.environ.get("NANO_VLLM_PREFILL_SMS", "32"))
        decode_sms = int(os.environ.get("NANO_VLLM_DECODE_SMS", "16"))

        print(f"Device found: {dev.name}, total SMs: {total_sms}")
        print(f"Requested benchmark split: prefill={prefill_sms} SMs, decode={decode_sms} SMs")

        if prefill_sms + decode_sms > total_sms:
            raise RuntimeError(
                f"requested split {prefill_sms}+{decode_sms} exceeds total SM count {total_sms}"
            )

        print(f"Requesting single partition of size: {decode_sms} SMs")
        single_layouts = list(sm.split(SMResourceOptions(count=(decode_sms,))))
        if not single_layouts:
            raise RuntimeError("single partition split returned no layouts")
        crit_grp = first_resource(single_layouts[0])
        print(f"Single SM split succeeded; resource type: {type(crit_grp)}")

        ctx_crit = dev.create_context(ContextOptions(resources=[crit_grp]))
        print("single dev.create_context succeeded")
        dev.set_current(ctx_crit)
        print("dev.set_current(ctx_crit) succeeded")
        stream = ctx_crit.create_stream()
        print(f"ctx_crit.create_stream succeeded; stream type: {type(stream)}")
        dev.set_current()
        print("dev.set_current() restored primary context after single-context test")

        print(f"Requesting two-way partition: {prefill_sms} SMs + {decode_sms} SMs")
        pair_layouts = list(sm.split(SMResourceOptions(count=(prefill_sms, decode_sms))))
        if not pair_layouts:
            raise RuntimeError("two-way partition split returned no layouts")
        prefill_grp, decode_grp = two_resources(pair_layouts[0])

        ctx_prefill = dev.create_context(ContextOptions(resources=[prefill_grp]))
        ctx_decode = dev.create_context(ContextOptions(resources=[decode_grp]))
        print("two-context creation succeeded")

        dev.set_current(ctx_prefill)
        print("dev.set_current(ctx_prefill) succeeded")
        prefill_stream = ctx_prefill.create_stream()
        print(f"ctx_prefill.create_stream succeeded; stream type: {type(prefill_stream)}")

        dev.set_current(ctx_decode)
        print("dev.set_current(ctx_decode) succeeded")
        decode_stream = ctx_decode.create_stream()
        print(f"ctx_decode.create_stream succeeded; stream type: {type(decode_stream)}")

        dev.set_current()
        print("dev.set_current() restored primary context after two-context test")
        return True
    except Exception as exc:
        print(f"cuda.core operations failed: {exc}")
        print("--- detailed traceback ---")
        traceback.print_exc()
        return False


def main() -> int:
    print("CUDA Version:", torch.version.cuda)
    print("PyTorch Version:", torch.version.device if hasattr(torch.version, "device") else torch.__version__)

    pytorch_ok = test_pytorch_green_context()
    cuda_core_ok = test_cuda_core_green_context()

    print_header("Summary")
    print(f"pytorch_green_context_ok={pytorch_ok}")
    print(f"cuda_core_green_context_ok={cuda_core_ok}")

    if cuda_core_ok:
        print("RESULT: PASS - cuda.core Green Context path is available for benchmark runs")
        return 0

    print("RESULT: FAIL - cuda.core Green Context path is not available")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

