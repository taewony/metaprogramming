
- CUDA 13.2 및 WSL2 Ubuntu 26.04 환경에서 RTX 4060 (Ada Lovelace 아키텍처)을 기반으로 PyTorch 오퍼레이터와 커스텀 cuTile 커널의 Parity Check(결과 검증), Latency(지연 시간), Throughput(처리량)을 비교 분석
- 엔드투엔드(End-to-End) 프로파일링 방법
- Nsight Compute CLI (ncu)
```
(cutile_env) cutile_project $ ncu -v
NVIDIA (R) Nsight Compute Command Line Profiler
Copyright (c) 2018-2026 NVIDIA Corporation
Version 2026.1.0.0 (build 37166530) (public-release)

(cutile_env) cutile_project $ nvcc --version
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2026 NVIDIA Corporation
Built on Mon_Mar_02_09:52:23_PM_PST_2026
Cuda compilation tools, release 13.2, V13.2.51
Build cuda_13.2.r13.2/compiler.37434383_0

(cutile_env) cutile_project $ python3 -c "import torch; print('CUDA 가용 여부:', torch.cuda.is_available()); print('사용 가능한 GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '없음')"
CUDA 가용 여부: True
사용 가능한 GPU: NVIDIA GeForce RTX 4060
```
------------------------------
## 1. 사전 준비 및 코드 작성 표준
오차 없는 정확한 측정과 프로파일링을 위해 Python 스크립트(profile_benchmark.py)를 아래 구조로 작성합니다. PyTorch의 비동기 실행 특성상 Warm-up과 CUDA Synchronization, 그리고 Nsight Compute가 타겟 커널만 추적할 수 있도록 돕는 cudaProfilerStart/Stop API 제어가 핵심입니다.

```
import torch
import ctypes
# Nsight Compute 제어를 위한 CUDA Driver API 로드cuda = ctypes.CDLL('libcuda.so')
def profile_baseline_pytorch(A, B):
    # PyTorch 내장 연산 (예: Matrix Multiplication)
    return torch.matmul(A, B)
def profile_cutile_kernel(A, B):
    # 사용자가 작성한 cuTile 커널 호출 (예시)
    # return cuTile_module.matmul(A, B)
    pass
# 1. 데이터 및 환경 준비 (RTX 4060 성능 극대화를 위해 FP16/BF16 권장)device = torch.device('cuda')A = torch.randn(2048, 2048, device=device, dtype=torch.float16)B = torch.randn(2048, 2048, device=device, dtype=torch.float16)
# 2. Warm-up (GPU 클록 안정화 및 초기 컨텍스트 오버헤드 제거)for _ in range(20):
    _ = profile_baseline_pytorch(A, B)
    # _ = profile_cutile_kernel(A, B)
torch.cuda.synchronize()
# 3. Parity Check (결과 일치성 검증)out_py = profile_baseline_pytorch(A, B)out_tile = profile_cutile_kernel(A, B) if 'profile_cutile_kernel' in locals() else out_py # 예시 대체# 두 텐서의 값이 허용 오차 내에서 일치하는지 확인
torch.testing.assert_close(out_py, out_tile, rtol=1e-3, atol=1e-3)
print("[PASS] Parity Check 성공: 두 커널의 출력 결과가 일치합니다.")
# 4. Latency 측정용 루프 (순수 연산 속도)start_event = torch.cuda.Event(enable_timing=True)end_event = torch.cuda.Event(enable_timing=True)

start_event.record()for _ in range(100):
    _ = profile_baseline_pytorch(A, B)
end_event.record()
torch.cuda.synchronize()
print(f"PyTorch Latency (Avg): {start_event.elapsed_time(end_event) / 100:.3f} ms")
# 5. Nsight Compute 프로파일링 구간 지정 (타겟 커널만 캡처)
cuda.cuProfilerStart()# 프로파일링 대상 커널을 딱 1~2회만 실행 (NCU 오버헤드 방지)_ = profile_baseline_pytorch(A, B)# _ = profile_cutile_kernel(A, B)
torch.cuda.synchronize()
cuda.cuProfilerStop()
```
------------------------------
## 2. Nsight Compute (ncu) CLI 명령어 실행
Nsight Compute(ncu)는 커널 단위의 하드웨어 카운터를 수집하므로 오버헤드가 큽니다. 전체 스크립트를 다 돌리면 시간이 매우 오래 걸리므로, 위 코드에서 지정한 cuProfilerStart() 구간만 스캔하도록 --profile-from-start off 옵션을 줍니다. [1, 2, 3] 
WSL2 터미널에서 다음 명령어를 실행하여 PyTorch와 cuTile 각각의 리포트 파일을 생성합니다.

# 1. PyTorch 오퍼레이터 커널 프로파일링
ncu --profile-from-start off \
    --target-processes all \
    --set full \
    -o report_pytorch \
    python3 profile_benchmark.py
# 2. cuTile 커널 프로파일링 (만약 코드를 분리했거나 커널 이름으로 필터링할 경우)# -k 옵션을 사용하면 특정 문자열이 포함된 커널만 획득 가능합니다.
ncu --profile-from-start off \
    --target-processes all \
    --set full \
    -k "cuTile" \
    -o report_cutile \
    python3 profile_benchmark.py


* 주의: WSL2에서 하드웨어 카운터에 접근할 때 권한 오류(ERR_NVGPUCTRPERM)가 발생하면 Windows 호스트에서 NVIDIA 제어판 ➔ 개발자 페이지 ➔ "모든 사용자가 GPU 성능 카운터에 액세스할 수 있도록 허용"을 체크해야 합니다. [4] 

------------------------------
## 3. Latency 및 Throughput 핵심 지표 비교 분석 (Parity Check)
생성된 report_pytorch.ncu-rep 파일과 report_cutile.ncu-rep 파일을 윈도우 호스트에 설치된 Nsight Compute GUI로 불러옵니다. 두 리포트를 동시에 열고 Add Baseline 기능을 활용하면 두 커널의 지표 변화를 퍼센트(%) 단위로 직접 비교할 수 있습니다. [5, 6, 7, 8] 
RTX 4060 (Ada 아키텍처) 분석 시 반드시 확인해야 하는 핵심 Throughput 및 Latency 지표는 다음과 같습니다.
## ① GPU Speed of Light (SOL) Throughput (처리량 지표)

* sm__throughput.avg.pct_of_peak_sustained_elapsed (SM SOL): GPU의 연산 코어가 이론상 최대 성능 대비 몇 %나 사용되었는지 나타냅니다. 이 값이 높을수록 Compute-bound(연산 중심)에 가깝습니다. [7, 9] 
* dram__throughput.avg.pct_of_peak_sustained_elapsed (DRAM SOL): 메모리 대역폭을 얼마나 효율적으로 썼는지 보여줍니다. 이 값이 높다면 Memory-bound(메모리 대역폭 제한) 상태이며 Tiling 크기 개선이 필요합니다. [3, 10] 

## ② Tensor Core 가동률 (Throughput 상세)
RTX 4060은 4세대 Tensor Core를 탑재하고 있습니다. FP16 연산 시 텐서 코어가 제대로 가동되었는지 확인해야 합니다.

* sm__inst_executed_pipe_tensor_op_hmma.sum: 이 카운터 수치가 0보다 크다면 하드웨어 텐서 코어를 사용해 행렬 연산을 고속 처리한 것입니다. 만약 cuTile의 수치가 0이라면 일반 CUDA 코어(ALU)로만 연산하여 PyTorch보다Throughput이 크게 떨어지게 됩니다. [11] 

## ③ Memory Latency & Cache Hit Rate (지연 시간 지표)

* l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum: 글로벌 메모리 로드 요청 수입니다.
* l1tex__t_hit_rate.pct & l2__t_hit_rate.pct: L1 및 L2 캐시 적중률입니다. cuTile 커널의 캐시 적중률이 PyTorch(cuDNN/cuBLAS)보다 낮다면, 메모리 병합(Coalesced Access)이 깨졌거나 공유 메모리(Shared Memory) 재사용 알고리즘이 비효율적임을 의미합니다. [10] 

## ④ Warp State Statistics (Stall 원인 분석)

* smsp__warp_issue_stalls_long_scoreboard_pct: 데이터가 메모리로부터 프론트엔드로 로드되기를 기다리며 멈춘(Stall) 비율입니다. 이 수치가 높다면 대기 시간(Latency)이 길어 성능이 저하된 것이므로 비동기 복사(cp.async) 등을 고려해야 합니다. [7] 

------------------------------
## 4. 권장 성능 최적화 워크플로우

   1. 결과 검증: 스크립트 내부의 assert_close를 통해 정확한 값(Parity)이 나오는지 먼저 확인합니다.
   2. 거시적 지연 시간 비교: Python 출력 창의 Latency (Avg) 값을 통해 전체적인 실행 속도 우위를 먼저 파악합니다.
   3. 미시적 하드웨어 분석: Nsight Compute GUI에서 두 리포트를 비교하여 cuTile 커널의 SM SOL 및 Tensor Core 매트릭이 PyTorch 백엔드(예: cuBLAS 크기 최적화 커널) 수준에 도달했는지 추적하고, 보틀넥(예: 낮은 L1 캐시 적중률)을 찾아 코드를 수정합니다. [7, 10] 

진행 중 Nsight Compute 명령어 실행 오류가 발생하거나 특정 하드웨어 카운터 수치 해석에 도움이 필요하시면 메시지를 남겨주세요! [10] 

[1] [https://docs.nvidia.com](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)
[2] [https://peanut159357.tistory.com](https://peanut159357.tistory.com/201)
[3] [https://docs.nvidia.com](https://docs.nvidia.com/deeplearning/tensorrt/latest/performance/measurement-techniques.html)
[4] [https://www.youtube.com](https://www.youtube.com/watch?v=Iuy_RAvguBM&t=75)
[5] [https://docs.nvidia.com](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)
[6] [https://docs.nvidia.com](https://docs.nvidia.com/nsight-compute/NsightCompute/index.html)
[7] [https://www.youtube.com](https://www.youtube.com/watch?v=04dJ-aePYpE)
[8] [https://docs.nvidia.com](https://docs.nvidia.com/nsight-compute/NsightCompute/index.html)
[9] [https://forums.developer.nvidia.com](https://forums.developer.nvidia.com/t/how-to-use-nsight-compute-profiling-results/107899)
[10] [https://www.youtube.com](https://www.youtube.com/watch?v=GCkdiHk6fUY)
[11] [https://developer.nvidia.com](https://developer.nvidia.com/blog/using-nsight-compute-nvprof-mixed-precision-deep-learning-models/)

- RTX 4060 환경에서 PyTorch 커널과 `cuTile` 커널을 동등한 조건에서 성능 검증하는 방법은, 워크플로우를 실제로 돌려가며 상황에 맞게 `ncu` 명령어와 세션 옵션을 조합하는 데에 있습니다.

### ⚙️ 1단계: 세팅 - 성능 카운터 권한 활성화
가장 먼저 해야 할 필수 단계는 RTX 4060의 GPU 성능 카운터 접근 권한을 활성화하는 것입니다. 그렇지 않으면 `ncu` 실행 시 에러가 발생하며 결과를 수집할 수 없습니다.
* **Windows (Native)** : NVIDIA 제어판의 "Manage GPU Performance Counters" 항목에서 "Allow access to the GPU performance counter to all users"를 활성화합니다.
* **WSL2** : Windows 호스트 측에서 먼저 위의 Windows 설정을 적용한 후, 필요한 라이브러리를 설치해야 할 수 있습니다.

### 📌 2단계: 포커싱 - PyTorch 코드에 Profiling 영역 표시
`cuTile`과 PyTorch의 `torch.compile` 또는 기본 연산을 정확히 비교하려면, PyTorch 코드 상에서 분석하고자 하는 특정 영역을 명확히 지정하는 것이 좋습니다.

NVIDIA Tools Extension (NVTX)을 사용하면 `ncu`의 범위 기반 프로파일링을 통해 커널을 특정할 수 있습니다.
```python
import torch
from torch.cuda.nvtx import range_push, range_pop

# 예시: PyTorch의 matmul 연산 프로파일링
range_push("my_matmul_op")
c = torch.matmul(a, b)
range_pop()
```

### ⚡ 3단계: 측정 및 분석
이제 준비가 완료되었습니다. 다음은 각 단계별 주요 작업입니다.

**Step 1. 기초 정보 수집 (ncu 기본 실행)**
```bash
ncu --set full -o profile_raw python my_script.py
```
`--set full` 옵션으로 기본적인 실행 시간, 점유율(Occupancy), 계산 및 메모리 처리량 등의 핵심 지표를 수집합니다.

**Step 2. 커널 상세 분석 (Custom Section)**
특정 커널의 지연 시간과 처리량 지표를 상세히 보려면, CLI를 통해 전용 세션 파일을 직접 지정할 수 있습니다.
```bash
ncu --section ComputeWorkloadAnalysis --section MemoryWorkloadAnalysis \
    --section SpeedOfLight --section Occupancy \
    --kernel-regex "my_matmul" \
    -o my_matmul_profile python run_matmul.py
```

**Step 3. GUI를 통한 심층 분석**
생성된 `.ncu-rep` 파일을 Nsight Compute GUI로 열면, 문제를 일으키는 정확한 소스 코드 라인을 시각적으로 파악할 수 있습니다. 이는 `cuTile`의 타일 통계를 분석할 때 특히 유용합니다.

### 📊 핵심 성능 지표 가이드
* **Kernel Latency (커널 지연 시간)** : 커널의 `Duration`을 기본으로, `smsp__average_warp_latency`는 워프 평균 지연 시간을, `sm__cycles_elapsed.avg`는 실행 사이클을 측정합니다.
* **Compute Throughput (컴퓨팅 처리량)** : `sm__throughput.avg.pct_of_peak_sustained_elapsed`로 SM의 이론적 최대 대비 활용률을, `sm__inst_executed`로 실행된 명령어 수를 확인합니다.
* **Memory Throughput (메모리 처리량)** : `gpu__dram_throughput.avg.pct_of_peak_sustained_elapsed`는 DRAM 대역폭 활용률을, `l1tex__data_bank_conflicts_pct`는 뱅크 컨플릭트 비율을 나타냅니다.

### 🔄 패리티 체크 (Parity Check)
두 구현체의 동등한 성능을 확인하려면, 메모리 패턴과 정확히 같은 문제 크기에서 동일한 조건으로 수집한 지표를 비교하는 것이 핵심입니다.
* **직접 비교 (A/B 테스트)** : 양쪽에서 동일한 `--kernel-regex`와 `--metrics`를 사용하여 측정합니다.
* **데이터 해석** : 실행 시간, 계산/메모리 처리량을 비교하며 두 구현체의 병목 지점을 분석합니다.

> 위 단계는 특정 커널의 최적화보다는 환경 설정 및 두 커널의 성능을 동등하게 검증하는 '패리티 체크(Parity Check)' 목적에 맞춰 작성되었습니다.

최종적으로 생성된 `.ncu-rep` 리포트 파일을 GUI에서 열어 "Source" 페이지를 보면, Nsight Compute가 NVTX 마커(`my_matmul_op`)로 둘러싸인 영역에 대해 캡처한 성능 지표들을 시각적으로 바로 확인할 수 있습니다.

---
Architect의 가설을 증명하기 위해 Executor(실험실)가 본격적으로 가동될 차례입니다. 논문에 들어갈 실측 데이터(Evidence)를 수집하려면, 정확성을 검증하던 Parity Test 코드와 달리 **프로파일링 전용 코드**가 필요합니다.

정확도 검증 로직을 걷어내고, GPU 워밍업(Warm-up)과 커널 반복 실행을 추가하여 Nsight Compute(`ncu`)가 측정하기 가장 좋은 상태로 만든 `profile_matmul.py`를 작성해 드립니다.

---

### `profile_matmul.py`

```python
import cuda.tile as ct
import cupy
import time

TILE_SIZE = 16

@ct.kernel
def matmul_kernel(a, b, c, K: ct.int32):
    row_bid = ct.bid(0)
    col_bid = ct.bid(1)
    acc_tile = ct.zeros((TILE_SIZE, TILE_SIZE), dtype=ct.float32)
    
    num_tiles_k = K // TILE_SIZE
    for k in range(num_tiles_k):
        a_tile = ct.load(a, index=(row_bid, k), shape=(TILE_SIZE, TILE_SIZE))
        b_tile = ct.load(b, index=(k, col_bid), shape=(TILE_SIZE, TILE_SIZE))
        acc_tile += a_tile @ b_tile

    ct.store(c, index=(row_bid, col_bid), tile=acc_tile)

def launch_matmul(a: cupy.ndarray, b: cupy.ndarray, c: cupy.ndarray):
    M, K = a.shape
    K_b, N = b.shape
    grid = (ct.cdiv(M, TILE_SIZE), ct.cdiv(N, TILE_SIZE), 1)
    
    # Nsight Compute가 정확히 이 커널 실행 시점만 캡처하도록 합니다.
    ct.launch(cupy.cuda.get_current_stream(), grid, matmul_kernel, (a, b, c, K))

if __name__ == "__main__":
    # 논문 데이터용으로 충분히 부하를 줄 수 있는 크기 설정
    M = TILE_SIZE * 128  # 2048
    K = TILE_SIZE * 128  # 2048
    N = TILE_SIZE * 128  # 2048

    print(f"Initializing data for Profiling (M={M}, K={K}, N={N})...")
    a_cupy = cupy.random.uniform(-1, 1, (M, K), dtype=cupy.float32)
    b_cupy = cupy.random.uniform(-1, 1, (K, N), dtype=cupy.float32)
    c_cupy = cupy.empty((M, N), dtype=cupy.float32)

    # 1. Warm-up Phase (매우 중요)
    # GPU 클럭을 최대치로 끌어올리고, JIT 컴파일 오버헤드를 제외하기 위해 
    # 측정 전에 미리 커널을 몇 번 실행합니다.
    print("Warming up GPU...")
    for _ in range(3):
        launch_matmul(a_cupy, b_cupy, c_cupy)
    cupy.cuda.Device().synchronize()

    # 2. Profile Phase
    print("Executing Kernel for Nsight Compute...")
    # ncu는 기본적으로 애플리케이션 내의 모든 커널을 캡처하지만, 
    # 워밍업을 거친 후의 순수 실행 상태를 캡처하는 것이 정확합니다.
    launch_matmul(a_cupy, b_cupy, c_cupy)
    cupy.cuda.Device().synchronize()
    print("Execution Finished.")

```

---

### 논문 데이터 추출을 위한 Nsight Compute(`ncu`) 측정 방법

WSL2 터미널(Executor 환경)에서 다음 명령어들을 단계별로 실행하여 실험 결과를 도출합니다.

#### 1. 기본 실행 통계 확인 (Summary)

가장 빠르게 커널의 실행 시간과 기본적인 레지스터 사용량을 텍스트로 확인합니다.

```bash
ncu python profile_matmul.py

```

* **논문 활용 포인트:** Terminal 출력 결과 중 `Duration` (커널 실행 시간)과 `Registers Per Thread`를 기록하여 베이스라인으로 삼습니다.

#### 2. 상세 리포트 생성 (가장 권장하는 워크플로우)

논문에 삽입할 병목(Bottleneck) 차트나 메모리 대역폭 데이터를 얻기 위해, 모든 측정 메트릭(Full set)을 캡처하여 파일(`.ncu-rep`)로 저장합니다.

```bash
ncu --set full -o matmul_experiment_01 python profile_matmul.py

```

* 위 명령어를 실행하면 WSL2 폴더에 `matmul_experiment_01.ncu-rep` 파일이 생성됩니다.
* **Architect의 분석:** 이 파일을 Windows 호스트 환경의 **Nsight Compute GUI** (Windows용 Nsight Compute 설치 필요)에서 엽니다. 그래픽 인터페이스를 통해 훨씬 직관적으로 진실(실측 데이터)을 확인할 수 있습니다.

#### 3. 논문에 반드시 포함해야 할 핵심 메트릭 (Roofline Model)

단순히 "속도가 빨라졌다"는 논문의 근거로 부족합니다. "왜 빨라졌는지"를 입증하려면 GUI에서 다음 지표를 찾아 캡처하거나 표로 정리해야 합니다.

* **Compute (SM) Throughput [%]:** GPU의 연산 코어(Tensor Core/CUDA Core)를 얼마나 효율적으로 사용하고 있는지 나타냅니다. 타일링 최적화가 잘 될수록 이 수치가 올라갑니다.
* **Memory Throughput [%]:** Global Memory 대역폭 사용량입니다. Shared Memory 타일링이 성공했다면 DRAM 트래픽이 줄어들어 이 수치가 100%를 치는 병목(Memory Bound)에서 벗어나게 됩니다.
* **GPU Speed Of Light (SOL):** 하드웨어의 물리적 한계 대비 현재 커널의 효율을 보여주는 궁극의 지표입니다. 논문에서 가장 강력한 증거 자료가 됩니다.
* **L1/Shared Memory Hit Rate:** 데이터 지역성(Locality)이 얼마나 개선되었는지 증명합니다.

이러한 **가설(Shared Memory) -> 실험(ncu profile) -> 결과 해석(SOL / Throughput 분석)** 과정 자체가 제안하시는 2계층 Kernel Engineering 에이전트 프레임워크의 탁월함을 보여주는 완벽한 시나리오가 될 것입니다.