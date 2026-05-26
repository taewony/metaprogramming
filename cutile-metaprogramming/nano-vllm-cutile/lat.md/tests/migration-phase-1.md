이 작업은 **GPU 커널 변환 + 테스트 설계 + CPU 부분 Mock 검증**이라는 세 축이 맞물린 복합 과제입니다. Agent에게 단계적으로 의도를 전달하고, 각 단계마다 검증을 통과해야만 다음으로 넘어가게 하는 **"검증 게이트 기반 워크플로우"**를 설계해 보겠습니다.

---

## 1. 전체 작업의 의도 구조화 — Agent에게 전달할 "게슈탈트"

Agent에게 가장 먼저 심어줘야 할 것은 **"이 작업이 어떤 전체 그림을 향해 가는가"**입니다.  
이것이 있어야 Agent가 중간에 헤매지 않고, 사용자가 의도하지 않은 방향으로 가지 않습니다.

**Agent에게 전달할 핵심 의도:**

> 우리는 nano-vLLM의 Attention 연산(Prefill + Decode)을 cuTile Python DSL로 교체하는 **Phase 1**을 진행 중이다.  
> 목표는 단순히 "돌아가는 코드"가 아니라, 다음 세 가지를 동시에 달성하는 것이다:
> 1. **Parity**: PyTorch 참조 구현과 수치적으로 일치해야 한다.
> 2. **Traceability**: 모든 실험 결과(parity check, latency, throughput)가 구조화된 trace log로 저장되어야 한다.
> 3. **Modularity**: CPU 부분(Scheduler, BlockManager)은 MockLLM으로 독립 검증 가능해야 한다.
>
> 전체 시스템을 한 번에 바꾸지 않는다. 1) Prefill Attention → 2) Decode Attention → 3) KV Cache Ops 순서로 **한 번에 한 커널만** 변환한다.

---

## 2. 사전 준비: Agent가 알아야 할 컨텍스트 자산

### Agent가 작업을 시작하기 전에 반드시 읽어야 할 파일들:

| 파일 | 용도 |
|:---|:---|
| `TileGym/src/tilegym/ops/cutile/attention.py` | cuTile Attention 참조 구현 |
| `nano-vllm/layers/attention.py` | 현재 Triton 기반 Attention |
| `lat.md/architecture.md` | nano-vLLM의 설계 의도 |
| `lat.md/outcomes.md` | cuTile 변환 목표 아키텍처 |
| `lat.md/patterns/online-softmax.md` | 온라인 소프트맥스 패턴 |
| `lat.md/patterns/design_patterns_for_migration.md` | cuTile Migration 관련 패턴 |
| `nano-vllm/engine/scheduler.py` | (MockLLM 검증 시) Scheduler |

---

## 3. 5단계 검증 게이트 워크플로우

### Gate 0: 환경 검증 — MockLLM으로 CPU 부분 독립 확인

**목적**: GPU 커널을 건드리기 전에, CPU 로직이 정상임을 먼저 확인합니다.

**Agent에게 전달할 지시:**
```
### Gate 0: MockLLM 검증

1. `nano-vllm/engine/scheduler.py`와 `engine/block_manager.py`를 분석하여,
   GPU 커널을 호출하지 않는 MockLLM 클래스를 `tests/mock_llm.py`에 작성하세요.
   - MockLLM은 `forward()` 호출 시 미리 계산된 더미 logit을 반환합니다.
   - KV Cache 할당/해제는 실제 BlockManager를 통과합니다.

2. `tests/test_mock_scheduler.py`를 작성하여:
   - 단일 요청 Prefill → Decode 시퀀스
   - 여러 요청의 Continuous Batching
   - KV Cache 블록 고갈 시나리오
   를 테스트하세요.

3. `python -m pytest tests/test_mock_scheduler.py -v` 실행하여 PASS를 확인하세요.
   실패 시 원인을 분석하고 수정 후 재실행하세요.

Gate 0 통과 조건: 모든 테스트 PASS
```

---

### Gate 1: Prefill Attention — cuTile 변환 및 Parity Check

**Agent에게 전달할 지시:**
```
### Gate 1: Prefill Attention cuTile 변환

1. TileGym의 `attention.py`에서 Prefill에 해당하는 Flash Attention 구현을 분석하세요.
   - 온라인 소프트맥스 (running m, l)
   - 타일 루프 구조 (Q 블록 × KV 블록)
   - 인과적 마스킹 적용 방식

2. `nano-vllm/kernels/attention.py`의 Prefill 커널을 cuTile로 재작성하여
   `src/cutile_kernels/prefill_attention.py`에 저장하세요.
   - 모든 연산은 `@ct.kernel` + `ct.launch`를 통해야 합니다 (Pure Forward Path).
   - 타일 크기는 2의 거듭제곱을 사용하세요.
   - 모든 상수에 `ct.Constant[type]` 어노테이션을 추가하세요.

3. Parity Check 테스트를 `tests/test_prefill_attention.py`에 작성하세요:
   ```python
   import torch
   from cutile_kernels.prefill_attention import prefill_attention_cutile
   from nano_vllm.kernels.attention import prefill_attention_triton
   
   def test_prefill_parity():
       # 다양한 입력 크기 테스트
       for B, H, S, D in [(1, 32, 512, 128), (4, 32, 2048, 128), (1, 8, 4096, 64)]:
           Q = torch.randn(B, H, S, D, dtype=torch.float16, device="cuda")
           K = torch.randn(B, H, S, D, dtype=torch.float16, device="cuda")
           V = torch.randn(B, H, S, D, dtype=torch.float16, device="cuda")
           
           ref = prefill_attention_triton(Q, K, V)
           out = prefill_attention_cutile(Q, K, V)
           
           assert torch.allclose(out, ref, atol=1e-2, rtol=1e-2), \
               f"Parity failed for shape {(B,H,S,D)}"
   ```

4. 성능 측정을 `tests/bench_prefill_attention.py`에 작성하세요:
   - Triton vs cuTile 처리량 (TFLOPS) 비교
   - 다양한 시퀀스 길이에서의 latency 측정
   - `ncu` 또는 `nsys` 프로파일링 결과 포함

5. Trace log는 JSONL 형식으로 `logs/prefill_attention_trace.jsonl`에 저장하세요:
   ```json
   {"timestamp": "2026-05-18T10:30:00", "shape": [1,32,512,128], "triton_tflops": 45.2, "cutile_tflops": 47.1, "parity": "PASS", "max_diff": 0.003}
   ```

Gate 1 통과 조건:
- Parity test ALL PASS (모든 shape에 대해)
- cuTile throughput이 Triton 대비 90% 이상
- Trace log가 JSONL 형식으로 저장됨
```

---

### Gate 2: Decode Attention — cuTile 변환 및 Parity Check

**Agent에게 전달할 지시:**
```
### Gate 2: Decode Attention cuTile 변환

1. Decode는 Query가 단일 토큰(B×H×1×D)인 특수 케이스입니다.
   TileGym의 `attention.py`에서 이 패턴을 찾거나, Prefill 커널을 변형하세요.

2. `src/cutile_kernels/decode_attention.py`에 Decode 전용 경량 커널을 작성하세요.
   - KV Cache로부터 K, V 블록을 읽어오는 `ct.load` 연산 포함
   - Prefill과 달리 KV 차원 루프가 지배적임을 고려한 타일 크기 선택

3. Decode는 KV Cache와의 상호작용이 중요하므로,
   `tests/test_decode_attention.py`에서:
   - 빈 KV Cache에 첫 토큰 쓰기 → 읽기 → 어텐션 계산
   - 여러 decode step에 걸친 cache 정합성 검증

4. 성능 측정 및 trace log: `logs/decode_attention_trace.jsonl`

Gate 2 통과 조건:
- Parity test ALL PASS
- Decode latency가 Triton 대비 110% 이하 (약간의 회귀 허용)
```

---

### Gate 3: 통합 테스트 — Prefill + Decode 연속 시나리오

**Agent에게 전달할 지시:**
```
### Gate 3: 통합 시나리오 테스트

1. `tests/test_attention_integration.py`를 작성하여 실제 nano-vLLM 추론 흐름을 모사:
   - Prefill → 첫 토큰 생성
   - KV Cache에 Prefill 결과 저장
   - Decode 루프 (최대 10토큰)
   - 각 스텝마다 logit이 PyTorch 참조와 일치하는지 확인

2. 연속적인 cache update가 누적 오차를 발생시키지 않는지 확인하세요.

Gate 3 통과 조건:
- 10스텝 Decode 후에도 parity 유지
- Trace log `logs/integration_trace.jsonl` 저장
```

---

## 4. Agent에게 전달할 통합 프롬프트 템플릿

아래는 이 워크플로우 전체를 한 번에 Agent에게 전달할 수 있는 **통합 프롬프트**입니다.

```markdown
@skill:cutile-python
@skill:nano-vllm-cutile-refactor

## 임무: nano-vLLM Attention을 cuTile로 변환하고 검증하라

### 전체 목표
nano-vLLM의 Attention 연산(Prefill + Decode)을 cuTile Python DSL로 교체한다.
PyTorch/Triton 참조와의 parity, 성능 지표, trace log를 모두 확보한다.

### 제약
1. 한 번에 하나의 커널만 변환한다. (Prefill → Decode → Integration 순서)
2. 각 Gate를 통과하기 전까지 다음 Gate로 넘어가지 않는다.
3. 모든 중간 결과는 `logs/` 아래 JSONL trace log로 저장한다.
4. `lat check`를 각 Gate 완료 후 실행하여 지식 그래프 무결성을 유지한다.

### 사전 읽기
- `lat section "architecture#triton-kernels"` — 현재 Attention 구조
- `lat section "outcomes#attention"` — 목표 상태
- `lat search "online softmax cuTile"` — 관련 패턴 검색
- TileGym의 `attention.py` 파일 전체를 읽을 것

### 실행 순서
Gate 0 → Gate 1 → Gate 2 → Gate 3 (각 Gate 설명은 위 참조)

### 보고
각 Gate 완료 후:
- 통과/실패 상태
- 실패 시 원인과 수정 내역
- `lat check` 결과
를 보고하라.

시작하라.
```

---

## 5. Agent의 자율성과 사용자 개입 지점

| 상황 | Agent 동작 | 사용자 개입 |
|:---|:---|:---|
| Parity FAIL | 자동으로 최대 3회 수정 시도 | 3회 실패 시 사용자에게 보고하고 지시 대기 |
| 성능 회귀 >10% | 가능한 최적화 시도 | 설계 변경이 필요하면 옵션을 제시하고 승인 대기 |
| `lat check` 오류 | 자동 수정 시도 | 해결 불가 시 보고 |
| 새 패턴 발견 | `lat.md/patterns/`에 초안 작성 | 사용자가 패턴을 검증하고 일반화 |

---

## 6. MockLLM 검증의 구체적 설계

Scheduler와 BlockManager가 cuTile 커널을 올바르게 호출하는지 확인하기 위해, **MockLLM**은 다음과 같은 인터페이스를 제공해야 합니다.

```python
# tests/mock_llm.py
class MockLLM:
    """
    GPU 커널 대신 CPU에서 더미 logit을 반환하는 경량 모델.
    Scheduler → ModelRunner → Kernel 호출 체인을 검증한다.
    """
    def __init__(self, vocab_size=32000, hidden_dim=4096):
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
    
    def prefill(self, input_ids: torch.Tensor) -> torch.Tensor:
        """더미 Prefill. 실제로는 cuTile 커널이 호출된다."""
        B, S = input_ids.shape
        return torch.randn(B, S, self.vocab_size)
    
    def decode(self, token_id: torch.Tensor) -> torch.Tensor:
        """더미 Decode."""
        B = token_id.shape[0]
        return torch.randn(B, 1, self.vocab_size)
```

이 MockLLM을 통해:
- Scheduler가 Prefill/Decode 배치를 올바르게 구성하는지
- BlockManager가 KV Cache 블록을 올바르게 할당/해제하는지
- CUDA Graph launch가 정상 동작하는지

를 **GPU 없이도** 검증할 수 있습니다.