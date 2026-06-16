### CUDA 13.3 환경과 호환되는 cuda-core 패키지 설치
```
pip install cuda-python
pip install cuda-core[cu13]
```

### 예제 코드
```
from cuda.core import Device

# 0번 GPU 장치를 선택하고 활성화합니다.
dev = Device(0)
dev.set_current()

# 1. 기존 기본 및 시스템 정보 출력
sys_dev = dev.to_system_device()
print(f"=== GPU 장치 정보 ===")
print(f"장치 이름: {sys_dev.name}")
print(f"아키텍처 (Compute Capability): {dev.arch}")

# 2. 하드웨어 세부 제한 속성 조회
print(f"\n=== 하드웨어 제한 속성 (Hardware Limits) ===")

# 스트리밍 멀티프로세서(SM) 개수
sm_count = dev.multiprocessor_count
print(f"스트리밍 멀티프로세서 (SM) 개수: {sm_count} 개")

# 스레드 및 워프(Warp) 제한
print(f"블록당 최대 스레드 수 (Max Threads per Block): {dev.max_threads_per_block} 개")
print(f"SM당 최대 스레드 수 (Max Threads per SM): {dev.max_threads_per_multiprocessor} 개")
print(f"워프 크기 (Warp Size): {dev.warp_size} 스레드")

# 메모리 제한 속성
print(f"블록당 최대 공유 메모리 (Shared Memory per Block): {dev.shared_mem_per_block / 1024:.2f} KB")
print(f"SM당 최대 공유 메모리 (Shared Memory per SM): {dev.shared_mem_per_multiprocessor / 1024:.2f} KB")

# 최대 그리드 / 블록 차원 크기
print(f"블록 최대 차원 크기 (Max Block Dim): X={dev.max_block_dim_x}, Y={dev.max_block_dim_y}, Z={dev.max_block_dim_z}")
print(f"그리드 최대 차원 크기 (Max Grid Dim): X={dev.max_grid_dim_x}, Y={dev.max_grid_dim_y}, Z={dev.max_grid_dim_z}")

```

## cuda.core 개요

- NVIDIA의 공식 [CUDA Python](https://developer.nvidia.com/cuda/python) 생태계에서 "C++의 CUDA Runtime API(및 일부 Driver API)를 파이썬 스타일로 완전히 추상화한 핵심 제어 레이어" 역할을 담당

------------------------------
### 1. CUDA Python 생태계 내에서의 위치
NVIDIA가 공식 제공하는 cuda-python 스택은 역할에 따라 명확히 계층이 나뉩니다. [1] 

* cuda.bindings (최하위 레이어): CUDA C/C++ API를 1:1로 직접 매핑한 저수준 바인딩입니다. 성능은 뛰어나지만 포인터 처리, 수동 메모리 할당/해제 등 C++ 방식의 복잡한 코딩이 강제됩니다. [1, 3] 
* cuda.core (중간 및 핵심 레이어 - 현재 다루는 영역): bindings의 복잡한 저수준 API들을 파이썬의 객체 지향 스타일(Pythonic)로 감싼 래퍼(Wrapper)입니다. 앞서 사용하신 Device() 객체처럼 장치 관리, 컨텍스트 제어, 메모리 스트림 관리를 파이썬답게 제어할 수 있도록 해줍니다. [1, 2] 
* cuda.compute / cuda.coop (상위 연산 레이어): 호스트에서 즉시 호출 가능한 병렬 알고리즘(정렬, 스캔, 축소 등)이나 커널 내부에서 쓰는 협력적 원시 기능을 제공합니다. [1, 2] 

------------------------------
### 2. 타 프레임워크(PyTorch, CuPy 등)와의 차이점 및 관계
흔히 쓰는 PyTorch나 CuPy와는 지향하는 목적과 추상화의 수준이 완전히 다릅니다. [4] 

[ 최상위 애플리케이션 프레임워크 ]
       PyTorch, TensorFlow, JAX
                 │
                 ▼
[ GPU 배열 및 범용 연산 라이브러리 ]
          CuPy, Numba
                 │
                 ▼
[ NVIDIA 공식 드라이버/컨텍스트 제어 ] ◀─── 이 위치가 바로 `cuda.core`
  cuda.core (Pythonic Runtime API)
                 │
                 ▼
[ 최하위 C API 바인딩 ]
          cuda.bindings


* PyTorch / TensorFlow: 딥러닝 모델의 텐서 연산과 자동 미분에 초점이 맞춰진 최상위 프레임워크입니다. 사용자는 GPU 컨텍스트나 스트림의 세부 하드웨어 제어권을 정밀하게 다루기 어렵습니다. [4] 
* CuPy / NumPy-like: GPU 기반의 다차원 배열 연산을 가속하는 데 집중합니다. [2, 4] 
* cuda.core: 연산 자체가 목적이 아니라, "GPU 하드웨어 자원을 어떻게 관리하고 분배할 것인가"에 집중합니다. 하드웨어의 한계 속성을 조회하고, 멀티 GPU 환경에서 컨텍스트를 스위칭하며, 스트림(Stream)과 이벤트를 동기화하는 등 C++ 개발자가 시스템 레벨에서 하던 제어 작업을 파이썬으로 완벽하게 이식해 온 형태입니다. [2, 5] 

------------------------------
### 3. 어떤 상황에 cuda.core를 사용해야 할까?
일반적인 딥러닝 모델 학습에는 cuda.core를 직접 만질 일이 거의 없습니다. 하지만 다음과 같은 고급 시스템 개발 단계에서는 필수적인 위치를 차지합니다. [4] 

   1. 커널 오서링 및 JIT 컴파일 (Numba 연동): 파이썬으로 직접 커널 코드를 작성할 때(@cuda.jit), 하드웨어 제약(SM 개수, 블록당 최대 스레드 등)을 런타임에 동적으로 파악하여 그리드/블록 레이아웃을 최적화할 때 사용합니다. [6] 
   2. 멀티 GPU 런타임 오케스트레이션: 다중 GPU 시스템에서 프로세스별로 컨텍스트를 분할하고 관리하는 인프라 솔루션을 파이썬 기반으로 구축할 때 유용합니다.
   3. 고성능 그래픽스 및 하드웨어 가속 파이프라인: CUDA 스트림과 그래픽스 API(OpenGL, Vulkan) 간의 하드웨어 메모리 공유(Interoperability) 및 저수준 동기화 제어가 필요할 때 필수적입니다.

요약하자면, cuda.core는 파이썬 개발자가 C++을 쓰지 않고도 GPU 하드웨어의 컨트롤 타워(제어실)에 직접 진입할 수 있도록 다리를 놓아주는 공식 기반 라이브러리라고 이해하시면 됩니다. [4] 

## CUDA 13.3
- CUDA 13.3은 파이썬을 C++과 동등한 최우선 지원 언어(First-Class Citizen)로 격상시킨 기념비적인 릴리스입니다. [1] 
NVIDIA는 이번 버전에서 공식 라이브러리인 CUDA Python 1.0 정식 버전을 출시하며 파이썬 생태계에 강력한 기능들과 아키텍처적 안정성을 대거 도입했습니다. 핵심적인 파이썬 지원 기능을 요약하면 다음과 같습니다. [2, 3] 
------------------------------
## 1. CUDA Python 1.0 정식 도달 및 시맨틱 버저닝 적용 [3, 4, 5] 

* API 안정성 보장: 기존의 실험적 단계를 벗어나 CUDA Python 1.0 메이저 마일스톤을 달성했습니다.
* 예측 가능한 업데이트: 메이저 버전 변경 시에만 주요 파괴적 변경(Breaking Changes)을 허용하는 시맨틱 버저닝(Semantic Versioning)을 엄격히 준수하기 시작하여 기업형 파이썬 AI 서비스 구축 시의 안정성을 극대화했습니다. [2, 3, 6, 7] 

## 2. 고급 리소스 제어 기능 도입
C++ 저수준 드라이버 영역에서만 가능했던 연산 및 프로세스 제어 기능이 파이썬 API(cuda.core) 영역으로 대거 이식되었습니다.

* 그린 컨텍스트 (Green Contexts): 단일 GPU의 스트리밍 멀티프로세서(SM) 자원을 독립된 하드웨어 리소스 그룹으로 쪼개어 관리할 수 있습니다. 이를 통해 처리량이 많은 작업(Throughput workload)이 도는 와중에도 지연 시간에 민감한 파이썬 커널(Latency-sensitive)이 블로킹되지 않도록 방지합니다. [7, 8] 
* 프로세스 체크포인팅 (Process Checkpointing - Linux 전용): 현재 메모리 할당 상태, 스트림, 컨텍스트를 포함한 CUDA 상태 전체를 스냅숏 형태로 저장하고 이후 복구할 수 있습니다. 장시간 구동되는 파이썬 기반 분산 AI 학습의 결함 허용(Fault-tolerant)이나 LLM 추론 웜스타트(Warm-start) 효율이 비약적으로 향상됩니다. [7, 8] 
* Zero-copy IPC 지원: 복잡한 호스트 메모리 복사 단계 없이, 다중 파이썬 프로세스 간에 GPU 메모리를 다이렉트로 공유하여 멀티 프로세싱 데이터 처리 속도를 끌어올렸습니다. [7] 

## 3. 컴파일러 및 생태계 고도화
파이썬 코드를 GPU 가속 코드로 변환해 주는 컴파일러 생태계가 크게 강화되었습니다. [9] 

* Numba CUDA MLIR 백엔드 도입: 기존 numba.cuda 아키텍처를 진화시킨 numba-cuda-mlir을 선보였습니다. MLIR 인프라를 백엔드로 차용함으로써 파이썬으로 작성된 SIMD/SIMT 커널 코드의 JIT 컴파일 최적화 성능과 디바이스 라이브러리 바인딩 속도가 대폭 개선되었습니다. [3, 10] 
* cuTile Python 및 JAX 확장 지원: 픽셀이나 타일 단위로 연산을 직관적으로 구조화하는 하이레벨 DSL인 cuda.tile이 확장되었습니다. 최신 Hopper(sm_90) 아키텍처 및 블록 스케일 MMA 연산을 완벽 지원하며, 차세대 고성능 수치 연산 프레임워크인 JAX와의 긴밀한 연동 및 Python 3.14 프리 스레딩(Free-threading) 환경 지원이 추가되었습니다. [5, 10] 

## 4. 고성능 파이썬 수학 라이브러리 결합

* 패키지 다이어트 및 이식성 강화를 위해 기존 복잡했던 수학 라이브러리들이 nvmath-python 패키지 형태로 깔끔하게 통합되었습니다. 파이썬 사용자들은 복잡한 C API를 거치지 않고도 NVIDIA GPU 내장 cuBLAS, cuSPARSE 등의 고속 행렬 연산 기능을 파이썬 네이티브 스타일로 손쉽게 호출할 수 있습니다. [1, 6] 

------------------------------
요약하자면 CUDA 13.3 환경의 파이썬은 단순히 C++ API를 '호출하는 껍데기'가 아니라, GPU 하드웨어의 자원 분할, 프로세스 복구, 타일 기반 최적화 커널 생성까지 직접 제어하는 진정한 고성능 백엔드 언어로 완전히 자리 잡았습니다. 
