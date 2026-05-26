# nano‑vLLM Architecture

> **Purpose**: 이 문서는 nano‑vLLM의 원래 설계 의도, 구성 요소, 데이터 흐름을 기술한다.  
> **Usage**: 각 `#` 제목은 `@lat: [[architecture#…]]` 주석을 통해 해당 설계 결정이 구현된 코드 위치를 추적하는 식별자로 사용된다.  
> **Target**: 최종 변환 목표는 [[outcomes#Pipeline]]에 기술되어 있다.

---

## Overview [[overview#nano-vllm]]
nano‑vLLM은 **연속적인 일괄 처리(Continuous Batching)**를 지원하는 경량 LLM 추론 서버로, HTTP 인터페이스를 통해 요청을 받아 토큰을 생성한다.

핵심 아이디어는 **Prefill‑Decode 분리**이며, 요청 생명주기는 다음과 같다.

1. HTTP 요청 도착 → Scheduler의 Waiting Queue에 진입
2. Prefill 단계: 전체 프롬프트를 한 번에 처리하여 KV Cache를 생성
3. Decode 단계: KV Cache를 이용해 한 토큰씩 자동 회귀 생성
4. 종료 조건(최대 길이, EOS) 충족 시 요청 제거

이 흐름은 [[scheduler#Request Lifecycle]]에서 더 자세히 다룬다.

---

## Scheduler [[scheduler#scheduler]]
Scheduler는 시스템의 **제어 평면(Control Plane)** 이다.  
CPU에서 동작하며, 요청 상태를 관리하고 배치를 구성한다.

- **Waiting Queue** → `@lat: [[architecture#scheduler#Waiting Queue]]`  
  아직 Prefill이 수행되지 않은 요청들.
- **Running Queue** → `@lat: [[architecture#scheduler#Running Queue]]`  
  이미 Prefill을 마치고 Decode 중인 요청들.
- **Batch 구성** → `@lat: [[architecture#scheduler#Batch Construction]]`  
  Prefill batch와 Decode batch를 분리하여 구성하며, Throughput‑Latency 트레이드오프를 관리한다.

Scheduler는 메모리 할당을 [[block‑manager#Block Allocation]]에 위임하고, 실제 GPU 실행은 [[model‑runner#Model Execution]]에 위임한다.

---

## Block Manager [[block-manager]]
Block Manager는 **KV Cache 메모리 관리자** 이다.

- **Block 단위 할당** → `@lat: [[architecture#block-manager#Block Allocation]]`  
  물리 GPU 메모리를 고정 크기 블록(예: 16 토큰)으로 나누고, 가변 길이 시퀀스를 블록 리스트로 매핑한다.
- **Prefix Caching** → `@lat: [[architecture#block-manager#Prefix Hashing]]`  
  동일한 프롬프트 접두사를 해싱하여 중복 KV Cache 생성을 방지한다.
- **Control Plane / Data Plane 분리**  
  Block Manager는 CPU에서 블록 메타데이터를 관리하고, 실제 텐서 연산은 [[kv‑cache‑dataplane#Physical Layout]]에서 수행된다.

---

## Model Runner [[model-runner]]
Model Runner는 GPU 상의 **추론 실행 엔진** 이다.

- **Prefill Mode** → `@lat: [[architecture#model-runner#Prefill]]`  
  Attention 계산에 전체 프롬프트 길이가 포함되므로, 연산은 Matrix Multiplication 위주로 구성된다.
- **Decode Mode** → `@lat: [[architecture#model-runner#Decode]]`  
  각 요청이 단 하나의 새로운 토큰만 처리하므로, 연산은 Memory‑Bound이며 Latency에 민감하다.
- **CUDA Graph** → `@lat: [[architecture#model-runner#CUDA Graph]]`  
  Decode 루프의 커널 실행을 미리 캡처하여 Launch Overhead를 제거한다.
- **Tensor Parallelism** → `@lat: [[architecture#model-runner#Tensor Parallel]]`  
  모델 가중치를 여러 GPU에 분할하고, All‑Reduce로 결과를 집계한다.

Model Runner는 실제 연산을 [[triton‑kernels#Attention]] 등에 의존한다.

---

## KV Cache Data Plane [[kv-cache-dataplane]]
GPU 메모리 상에서 KV Cache의 **물리적 배치**를 정의한다.

- **Layout**: `(num_blocks, num_layers, 2, num_kv_heads, block_size, head_dim)`  
  → `@lat: [[architecture#kv-cache-dataplane#Layout]]`
- **Block Table** → `@lat: [[architecture#kv-cache-dataplane#Block Table]]`  
  논리 블록 → 물리 블록 매핑을 위한 2D 텐서.
- **Cache Read/Write** → `@lat: [[architecture#kv-cache-dataplane#Read/Write Ops]]`  
  Triton 커널을 이용한 캐시 읽기/쓰기로, 추후 cuTile `ct.load`/`ct.store`로 대체될 대상이다.

---

## Current GPU Kernel Implementation [[triton-kernels]]
nano‑vLLM은 현재 **Triton** DSL로 구현된 다음 커널들을 사용한다.

- **Flash Attention (Prefill)** → `@lat: [[architecture#triton-kernels#Flash Attention Prefill]]`  
  Multi‑head attention의 Prefill을 tile‑based로 수행.
- **Attention (Decode)** → `@lat: [[architecture#triton-kernels#Attention Decode]]`  
  KV Cache와 단일 쿼리 토큰의 연산.
- **LayerNorm / RMSNorm** → `@lat: [[architecture#triton-kernels#LayerNorm]]`  
  정규화 커널. cuTile에서는 [[patterns/shared‑memory‑coalescing]]과 [[patterns/fused‑epilogue]]를 적용할 수 있다.
- **Rotary Embedding** → `@lat: [[architecture#triton-kernels#RoPE]]`  
  위치 인코딩. [[patterns/online‑softmax]]와 결합 가능.

이 커널들은 모두 `@lat:` 주석을 통해 문서와 연결되며, 각 커널은 추후 [[outcomes#attention]] 및 [[outcomes#mlp]]에 명시된 cuTile 구현으로 대체된다.

---

## How to Use This Document with lat

1. **코드와 연결하기**: 원본 nano‑vLLM 코드에 다음과 같이 주석을 추가한다.
   ```python
   # @lat: [[architecture#scheduler#Waiting Queue]]
   class WaitingQueue:
       ...
   ```