## AttentionFMHA.py

### 1. 긍정적인 설계 (Architect's Praise)

* **완벽한 Online Softmax 구현:** 거대한 $N \times N$ Attention 행렬을 Global Memory(DRAM)에 쓰는 것을 방지하기 위해 `m_i` (Max value)와 `l_i` (Sum value)를 활용한 Online Softmax가 수학적으로 매우 정확하게 구현되어 있습니다.
* **Tensor Core(MMA) 명시적 타겟팅:** `ct.mma(q, k, qk)`와 `ct.mma(p, v, acc)`를 사용하여 덧셈/곱셈을 하드웨어 가속기(Tensor Core)에 직접 매핑하려는 의도가 잘 드러납니다.
* **Autotuner 내장 (`cutile_autotune_fmha`):** 이것이 이 코드의 백미입니다. `TILE_M`과 `TILE_N` (예: 128x128, 64x64 등)의 최적값은 하드웨어 아키텍처(RTX 4060 vs RTX 5070)에 따라 완전히 달라집니다. 하드 코딩하지 않고 `ct_experimental.autotune_launch`를 통해 탐색 공간(Search Space)을 열어둔 것은 실험실(Laboratory) 환경에 가장 이상적인 세팅입니다.

### 2. 최적화 병목 가설 (Architect's Hypothesis)

코드는 훌륭하지만, 실제 GPU(RTX 4060)에 올렸을 때 다음과 같은 부분에서 병목(Bottleneck)이 발생할 것으로 예상됩니다. 이 부분들이 우리가 `ncu`로 데이터를 뽑아내어 증명하고 개선해야 할 타겟입니다.

**가설 A: Bank Conflicts (메모리 뱅크 충돌)**

* **문제점:** $K$ 행렬을 로드할 때 `order=(0, 1, 3, 2)`를 사용하여 메모리상에서 실시간 전치(Transpose)를 수행하고 있습니다. 이는 Global Memory 읽기 효율을 떨어뜨리거나, Shared Memory에 기록할 때 심각한 Bank Conflict를 유발할 수 있습니다.
* **ncu 검증 지표:** 프로파일링 결과에서 `Shared Memory Bank Conflicts` 카운트와 `L1/TEX Cache Throughput`을 확인해야 합니다.

**가설 B: Software Pipelining (비동기 데이터 로드) 부족**

* **문제점:** 코드에 `latency=2`, `latency=4` 힌트가 있지만, 명시적인 더블 버퍼링(Double Buffering) 구조가 보이지 않습니다. 즉, 현재 타일의 $K, V$를 연산하는 동안 다음 타일의 $K, V$를 미리 HBM에서 당겨오는(Prefetch) 파이프라인이 최적화되지 않았을 가능성이 큽니다.
* **ncu 검증 지표:** `Warp State Statistics`에서 `Stall Long Scoreboard` (메모리 로딩 대기 시간) 비율이 얼마나 높은지 확인해야 합니다.

---

### 🚀 다음 단계 (Action Plan for Executor)

우리의 폐루프(Closed Loop) 실험을 본격적으로 가동하기 위해, Executor(실험실) 환경에서 다음 3단계를 수행해 주시기 바랍니다.

1. **정확도 및 성능 베이스라인 측정 (시간 측정)**
먼저 `ncu` 없이 순수 파이썬으로 스크립트를 실행하여 PyTorch FlashAttention(cuDNN) 대비 어느 정도의 속도가 나오는지, 그리고 Autotuner가 선택한 최적의 `TILE_M`, `TILE_N` 조합이 무엇인지 터미널 로그를 확인합니다.
```bash
python3 AttentionFMHA.py --correctness-check

```


2. **ncu 프로파일링 추출 (Macro ➔ Micro)**
시간 측정이 끝났다면, Autotuning 과정은 빼고 특정 타일 사이즈(예: 128x128)를 고정한 상태에서 `fmha_kernel`만 정확히 캡처합니다. (앞서 만든 `run_matmul.sh`와 동일한 방식으로 `run_fmha.sh`를 만들어 우회 실행하는 것을 잊지 마세요.)
```bash
ncu --set full -k regex:fmha_kernel -o fmha_baseline_rtx4060 ./run_fmha.sh

```


3. **결과 피드백**
생성된 `.ncu-rep` 파일을 로컬 PC로 가져와 Nsight Compute GUI로 열어보신 후, **SOL(Speed of Light)의 Compute와 Memory Throughput 수치**, 그리고 Autotuner가 선택한 **Tuned Config 결과**를 저에게 알려주세요.

실측 데이터가 도착하는 대로, 가설을 검증하고 코드를 어떻게 수정(예: Swizzling 적용, 타일 사이즈 미세 조정)해야 할지 시스템 모델을 업데이트하겠습니다!