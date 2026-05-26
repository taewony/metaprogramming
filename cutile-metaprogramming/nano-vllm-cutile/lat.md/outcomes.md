# cuTile 기반 nano-vLLM – 최종 목표 아키텍처

> **Purpose**: 이 문서는 nano-vLLM이 cuTile Python DSL로 완전히 변환된 후의 **목표 상태(Target State)**를 기술한다.  
> **Usage**: `lat gap`이 이 문서의 각 섹션과 현재 코드의 `@lat:` 주석을 비교하여 변환 대상을 식별한다.  
> **관계**: 현재 아키텍처는 [[architecture#Overview]]에, 검증 기준은 [[tests/migration-pass-criteria]]에 기술되어 있다.

---

## Inference Pipeline [[pipeline]]
모든 GPU 연산이 `@ct.kernel` 데코레이터와 `ct.launch`를 통해 실행된다.
- `nn.Linear`, `F.scaled_dot_product_attention`, Triton 커널 호출은 **모두 제거**된다.
- Scheduler 로직은 CPU에서 Python으로 유지되며, 연산 요청만 cuTile 커널에 위임한다.

## Attention [[attention]]
- **Prefill**: Flash Attention 로직을 cuTile `ct.load`/`ct.store` 기반 타일드 연산으로 구현한다. [[patterns/online-softmax]]를 적용하여 수치적 안정성을 유지한다.
- **Decode**: KV Cache와 단일 쿼리 토큰의 연산을 경량 cuTile 커널로 처리한다.
- KV Cache 읽기/쓰기는 `ct.load`/`ct.store`로 직접 수행하며, Triton 기반 캐시 접근 코드는 삭제한다.

## MLP [[mlp]]
- `nn.Linear` 가중치를 `ct.launch`를 통해 호출되는 MatMul 커널로 대체한다.
- SiLU, GELU 등의 활성화 함수는 [[patterns/fused-epilogue]]를 적용하여 MatMul 커널 내에서 융합한다.

## Normalization [[norm]]
- LayerNorm과 RMSNorm을 cuTile Reduction + Element-wise 커널로 구현한다.
- [[patterns/shared-memory-coalescing]]과 [[patterns/bank-conflict-avoidance]] 패턴을 적용한다.

## Rotary Embedding [[rope]]
- Rotary Position Embedding을 cuTile 커널로 구현한다.
- 가능한 경우 Attention 커널의 epilogue로 융합한다.

## KV Cache Data Plane [[kv-cache]]
- Paged KV Layout과 Block Indexing 구조는 유지한다.
- Cache Read/Write는 cuTile `ct.load`/`ct.store`로 직접 수행한다.
- Block Table과 Gather/Scatter 로직은 보존된다.

## Tensor Parallelism [[tensor-parallel]]
- All-Reduce 등 NCCL 집합 연산과 cuTile 커널이 올바르게 협력한다.
- Vocabulary-parallel LM head 동작이 수치적으로 안정적으로 유지된다.

## Continuous Batching [[batching]]
- Scheduler의 연속 일괄 처리 로직(heterogeneous sequences, dynamic batching)은 유지된다.
- Prefill과 Decode의 공존 모드가 보존된다.

## Performance [[performance]]
- cuTile 변환 후 처리량(throughput)이 기준선보다 유의미하게 낮아지지 않는다.
- Decode latency가 허용 범위를 벗어나지 않는다.

## Memory [[memory]]
- KV Cache 단편화, 최대 VRAM 사용량, 임시 텐서 할당 압력에 주요 회귀가 발생하지 않는다.

## Knowledge Artifacts [[knowledge]]
변환 과정에서 다음 지식 자산이 `lat.md/` 내에 축적된다.
- **Patterns**: 적용된 반정형 설계 패턴이 `patterns/` 디렉토리에 문서화되고, 패턴 간 링크가 유지된다.
- **Retrospectives**: 각 변환 세션의 교훈이 `retrospectives/` 에 기록된다.
- **Compounding**: 한 커널 변환의 `retrospective`가 다음 커널 변환 시 `lat search`를 통해 자동 참조된다.

## Code Quality [[code-quality]]
- Kernel, Scheduler, Runtime 코드가 명확히 분리된다.
- cuTile DSL 사용이 모듈화되고 가독성 있게 유지된다.

## Build Reproducibility [[build]]
- 문서화된 명령어로 설치, 컴파일, 실행, 벤치마크가 재현 가능하다.