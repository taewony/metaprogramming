import os
import time
import argparse
from random import randint, seed
from nanovllm import LLM, SamplingParams


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-cutile", action="store_true", help="Use cuTile backend")
    args = parser.parse_args()

    if args.use_cutile:
        os.environ["NANO_VLLM_USE_CUTILE"] = "1"
        print("🚀 Using cuTile attention backend")
    else:
        print("⚡ Using default (FlashAttention) backend")

    seed(0)
    num_seqs = 256
    max_input_len = 1024
    max_ouput_len = 1024

    path = os.path.expanduser("~/huggingface/Qwen3-0.6B/")
    llm = LLM(path, enforce_eager=False, max_model_len=4096)

    prompt_token_ids = [[randint(0, 10000) for _ in range(randint(100, max_input_len))] for _ in range(num_seqs)]
    sampling_params = [SamplingParams(temperature=0.6, ignore_eos=True, max_tokens=randint(100, max_ouput_len)) for _ in range(num_seqs)]

    llm.generate(["Benchmark: "], SamplingParams())
    
    print("🚀 Starting benchmark generation loop...")
    t = time.time()
    last_print_time = t
    total_finished = 0
    total_expected = len(prompt_token_ids)
    total_tokens_generated = 0
    
    for prompt, sp in zip(prompt_token_ids, sampling_params):
        llm.add_request(prompt, sp)
        
    while not llm.is_finished():
        outputs, num_tokens = llm.step()
        total_finished += len(outputs)
        if num_tokens < 0:
            total_tokens_generated += (-num_tokens)
            
        current_time = time.time()
        if current_time - last_print_time >= 30.0:
            elapsed = current_time - t
            percent = (total_finished / total_expected) * 100
            current_throughput = total_tokens_generated / elapsed if elapsed > 0 else 0
            active_running = len(llm.scheduler.running)
            active_waiting = len(llm.scheduler.waiting)
            print(f"⏱️ [Progress] Elapsed: {elapsed:.1f}s | Finished: {total_finished}/{total_expected} ({percent:.1f}%) | Active: {active_running} running, {active_waiting} waiting | Generated: {total_tokens_generated} tokens | Decode Throughput: {current_throughput:.1f} tok/s")
            last_print_time = current_time

    t = (time.time() - t)
    total_tokens = sum(sp.max_tokens for sp in sampling_params)
    throughput = total_tokens / t
    print(f"Total: {total_tokens}tok, Time: {t:.2f}s, Throughput: {throughput:.2f}tok/s")


if __name__ == "__main__":
    main()

