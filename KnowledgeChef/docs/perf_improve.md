## cuTile 기반 Windows nano-vLLM과 Linux PyTorch/Triton 구현 간 성능 차이 원인

두 구현 간의 약 4.62배 성능 차이는 단일 원인이 아닌, **소프트웨어 스택, 커널 구현 방식, 메모리 관리 전략**이 복합적으로 작용한 결과입니다.

### 1. FlashAttention vs 수동 타일링 커널

Linux 구현의 핵심 강점은 **FlashAttention**과 **Triton** 커널의 활용에 있습니다. FlashAttention은 IO-aware 알고리즘을 통해 HBM 접근을 최소화하고, 온라인 소프트맥스 계산을 블록 단위로 처리하여 메모리 대역폭 병목을 완화합니다.

반면 cuTile 기반 Windows 구현은 수동 타일링 커널을 사용합니다. 수동 커널은 다음과 같은 한계가 있습니다:

- **메모리 접근 패턴 최적화 부족**: FlashAttention처럼 HBM 읽기/쓰기를 최소화하는 전략이 커널 수준에서 구현되어야 하지만, cuTile의 수동 구현은 이 부분에서 최적화가 부족할 수 있습니다.
- **Tensor Core 활용도 차이**: Linux의 Triton 구현은 Tensor Core 명령어(`mma`, `mmaf_scaled`)를 적극 활용하여 높은 연산 집약도를 달성합니다. cuTile도 Tensor Core를 지원하지만, 활용도와 최적화 수준에서 차이가 있을 수 있습니다.

### 2. 운영체제 및 드라이버 스택 차이

Windows와 Linux의 CUDA 드라이버 스택은 성능에 영향을 미칠 수 있습니다:

- NVIDIA 공식 문서에 따르면, **CUDA Graph**의 성능 최적화는 Linux 환경에서 더 적극적으로 이루어져 왔습니다. CUDA Toolkit 11.8에서 12.6 사이에 반복 실행 CPU 오버헤드가 2μs + 200ns/노드에서 **약 2.5μs + 1ns/노드** 수준으로 개선되었습니다.
- Windows 환경에서도 동일한 CUDA 드라이버가 적용되지만, WSL2를 통한 Linux 커널과의 통합이 일부 최적화 경로에서 더 유리할 수 있습니다.

### 3. 커널 런처 오버헤드

Linux PyTorch/Triton 구현은 `torch.compile`을 통한 커널 퓨전과 Triton의 JIT 컴파일 캐싱을 활용합니다. 반면 cuTile은 **JIT 컴파일을 런타임에 수행**하며, 다음 요소들이 오버헤드로 작용할 수 있습니다:

- **타일 형상(`S=[16,16]` vs `[32,32]`) 변경 시 재컴파일**: cuTile은 entry function의 const generic 인자가 변경되면 새로운 GPU specialization을 생성합니다.
- **스트라이드 및 텐서 특수화 힌트**: cuTile은 텐서의 shape divisibility, stride 정보 등을 기반으로 최적화된 코드를 생성하지만, 이 과정에서 캐시 미스 시 추가 컴파일이 발생합니다.

### 4. 메모리 관리 및 할당 전략

Linux의 FlashAttention 기반 구현은 **paged KV cache를 Triton 커널**로 구현하여 비연속적 메모리 접근을 효율적으로 처리합니다. cuTile의 수동 메모리 관리 방식은:

- PyTorch CUDA 캐싱 할당자와의 상호작용에서 추가 오버헤드가 발생할 수 있습니다.
- 동적 형상 패딩과 같은 최적화 시도가 오히려 할당자 압력을 증가시켜 성능을 저하시킨 사례가 논문에 보고되었습니다.

---

## cuTile 커널 호출 빈도 감소 방안

### 1. CUDA Graph 도입

**CUDA Graph**는 여러 커널을 단일 실행 가능 객체로 캡처하여 호스트의 커널 런처 오버헤드를 제거합니다:

```python
# CUDA Graph 캡처 및 실행 (cuda-python 예시)
from cuda.core import Device, LaunchConfig, Program

graph_builder = stream.create_graph_builder()
graph_builder.begin_building()

# 여러 커널 런처를 그래프에 추가
launch(graph_builder, config, kernel1, ...)
launch(graph_builder, config, kernel2, ...)
launch(graph_builder, config, kernel3, ...)

# 그래프 완성 및 업로드
graph = graph_builder.end_building().complete()
graph.upload(stream)

# 반복 실행: 단일 cudaGraphLaunch 호출로 모든 커널 실행
for _ in range(iterations):
    graph.launch(stream)
    stream.sync()
```

TensorRT도 CUDA Graph를 기본 지원하며, `enqueueV3()` 호출을 그래프로 캡처하여 재생할 수 있습니다. CUDA 12.6 기준으로 **반복 실행 CPU 오버헤드가 노드 수에 관계없이 약 2.5μs 수준**으로 개선되었습니다.

### 2. 타일 형상 최적화

cuTile에서 타일 크기는 커널 런처 오버헤드와 데이터 재사용성에 직접적 영향을 미칩니다:

| 타일 크기 | 영향 |
| :--- | :--- |
| 너무 작음 | **오버헤드가 유용한 작업을 지배** |
| 너무 큼 | 레지스터 압력 증가 → 점유율 저하 또는 스필 발생 |

**권장 시작점**:
- GEMM: Tensor Core MMA 차원과 호환되는 타일 형상 (`[16, 16]`, `[32, 32]`, `[64, 16]` 등)
- 실제 프로파일링(Nsight Compute)을 통해 타겟 GPU(SM_120)에 최적화된 타일 크기를 튜닝

### 3. 커널 퓨전 (Kernel Fusion)

여러 개별 커널을 하나의 커널로 융합하여 글로벌 메모리 트래픽과 런처 오버헤드를 동시에 줄입니다:

```rust
#[cutile::entry()]
fn fused_kernel<const BM: i32, const BN: i32>(
    z: &mut Tensor<f32, { [BM, BN] }>,
    x: &Tensor<f32, { [-1, -1] }>,
) {
    // 하나의 타일을 로드하고, 여러 연산을 수행한 후 한 번 저장
    let tile = load_tile_like(x, z);
    let centered = tile - reduce_max(tile, 1i32)
        .reshape(const_shape![BM, 1])
        .broadcast(const_shape![BM, BN]);
    let exp_x = exp(centered);
    let sum = reduce_sum(exp_x, 1i32)
        .reshape(const_shape![BM, 1])
        .broadcast(const_shape![BM, BN]);
    z.store(true_div(exp_x, sum));
}
```

세 개의 분리된 커널이 중간 텐서를 여러 번 읽고 쓰는 것보다 **하나의 융합 커널이 중간 값을 레지스터에 유지**하는 것이 훨씬 효율적입니다.

### 4. JIT 캐시 재사용 최적화

cuTile의 JIT 캐시 키는 `device_id`, `module_name`, `function_generics`, `compile_options` 등으로 구성됩니다. 다음 사항에 주의하세요:

- **`const_grid` 대신 `grid` 사용**: `.const_grid()`는 그리드 값을 컴파일 타임 값으로 임베드하여 캐시 분리를 유발합니다. `.grid()`를 사용하면 런타임 값으로 전달되어 캐시 재사용성이 높아집니다.
- **`compile_options` 변경 최소화**: `occupancy`, `num_cta_in_cga` 등은 서로 다른 캐시 항목을 생성하므로, 변경이 필요한 경우에만 사용하세요.
- **동적 차원(`-1`) 활용**: 텐서 차원이 런타임에 변하는 경우 `-1`을 사용하면 재컴파일 없이 동일한 커널을 재사용할 수 있습니다.

### 5. 연산 집약도(Arithmetic Intensity) 향상

메모리 대역폭이 아닌 컴퓨트가 병목이 되도록 연산 집약도를 높입니다:

| 연산 유형 | 집약도 | 병목 |
| :--- | :--- | :--- |
| 벡터 덧셈 | 낮음 | 메모리 대역폭 |
| 행렬-행렬 곱셈 | 높음 | Tensor Core 처리량 |
| 융합 어텐션 | 높음 | 컴퓨트/메모리/점유율 혼합 |

로드된 타일을 재사용하고, 인접 연산을 융합하며, 불필요한 호스트 읽기백이나 중간 텐서를 피하는 것이 핵심입니다.
---

## 구현 체크포인트: cuTile Decode CUDA Graph + Prefill Padding/Copy 제거

이번 변경은 Linux/FlashAttention 기준 측정값은 그대로 재사용하고, Windows-native cuTile 경로만 개선 대상으로 둔다.

### 변경 내용

1. `NANO_VLLM_USE_CUTILE=1`일 때 더 이상 `ModelRunner`가 강제로 eager mode로 고정되지 않는다.
   - `enforce_eager=False`이면 decode CUDA Graph capture를 시도한다.
   - capture 성공 시 benchmark log에 `cuTile CUDA Graph decode capture enabled`가 출력된다.
   - capture 실패 시 cuTile 경로만 eager decode로 fallback하며, Linux/FlashAttention 경로 동작은 유지한다.

2. cuTile prefill wrapper에서 Python-side padded `q_4d/k_4d/v_4d` materialization과 `res[start_q:end_q]` repack copy를 제거했다.
   - 일반 prefill은 flat `q/k/v` tensor의 per-sequence BHTD view를 직접 kernel에 전달한다.
   - prefix-cache prefill은 `fmha_prefill_paged_kernel`을 통해 `block_table`과 paged KV cache에서 직접 읽는다.
   - prefix-cache causal mask는 `Q_START_IN_K = seqlen_k - seqlen_q` offset을 반영한다.

### Target-PC 측정 절차

Linux reference는 기존 측정값을 재사용한다.

```text
WSL2 FlashAttention reference: 2138.55 tok/s mean, 4.62x over previous Windows cuTile baseline.
```

Windows-native cuTile 재측정은 target PC에서 다음을 수행한다.

```powershell
cd D:\code\metaprogramming\KnowledgeChef\KernelAgent\3-micro-vllm
python bench.py --use-cutile
```

판정 기준:

- log에 `cuTile CUDA Graph decode capture enabled`가 있으면 decode graph path가 활성화된 측정이다.
- warning fallback이 출력되면 해당 결과는 CUDA Graph 개선 실험으로 사용하지 않고, fallback 원인을 별도 repair 대상으로 기록한다.
- 새 cuTile throughput은 기존 Linux reference `2138.55 tok/s`와 비교하되, 논문 본문에서는 여전히 Linux를 optimized reference baseline으로 둔다.
