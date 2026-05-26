# nano-vLLM → cuTile 변환: 실증 프로젝트 전체 가이드

> **"Semiformal Design Patterns를 통해 구축된 컨텍스트 자산(lat.md 지식 그래프)은, LLM Coding Agent가 복잡한 GPU 커널 변환 과제를 상향식-하향식 갈등 없이 수행하게 하며, 그 과정에서 축적된 지식은 다음 과제에 복리로 전이된다."**

---

## 1. Phase 1: lat.md 기반 nano-vLLM 지식 그래프 구축 (역설계)

### 1-1. nano-vLLM의 "의도된 전체(Gestalt)" 포착

블로그 Part 1, 2에서 드러난 nano-vLLM의 구조를 `lat.md/`에 **시스템의 의도가 드러나는 방식**으로 재구성합니다. 단순한 디렉토리 나열이 아니라, **"이 시스템이 무엇을 지향하는가"**라는 전경을 먼저 서술하고, 그로부터 세부를 파생시키는 하향식 구조입니다.

**구축할 lat.md 그래프의 뼈대:**

```
nano-vllm-cutile/
├── lat.md/
│   ├── architecture.md          ← 시스템 게슈탈트의 최상위
│   │   ├── "Inference Pipeline: Producer-Consumer 패턴으로서의 전체상"
│   │   ├── [[scheduler#Prefill vs Decode]] 로 연결
│   │   └── [[model-runner#CUDA Graph Execution]] 로 연결
│   │
│   ├── scheduler.md             ← 스케줄링의 설계 의도
│   │   ├── "Waiting Queue → Running Queue 상태 전이"
│   │   ├── "Batch 구성의 Throughput-Latency Trade-off"
│   │   └── [[block-manager#Memory Preemption]] 과의 협력
│   │
│   ├── block-manager.md         ← KV Cache 제어 평면
│   │   ├── "고정 크기 블록 할당: 가변 길이 시퀀스의 근접성 해결"
│   │   ├── "Prefix Caching via Hashing: 유사성 기반 중복 제거"
│   │   └── "Control Plane (CPU) vs Data Plane (GPU) 분리"
│   │
│   ├── model-runner.md          ← GPU 실행 조율
│   │   ├── "Prefill vs Decode: 두 가지 전경 모드"
│   │   ├── "Tensor Parallelism: Leader-Worker 공동 운명"
│   │   └── [[cuda-graphs#Decode Optimization]] 연결
│   │
│   ├── kv-cache-dataplane.md    ← GPU 메모리 상의 물리적 배치
│   │   ├── "Multi-dimensional Layout: Block × Layer × K/V × Token"
│   │   └── [[triton-kernels#Cache Read/Write]] 연결
│   │
│   ├── triton-kernels.md        ← 현재 GPU 커널 구현 상세
│   │   ├── "Flash Attention, LayerNorm, RMSNorm, Rotary Embedding"
│   │   └── 각 커널별 cuTile 변환 후보 식별
│   │
│   ├── patterns/                ← Semiformal Design Patterns 카탈로그
│   │   ├── shared-memory-coalescing.md
│   │   ├── bank-conflict-avoidance.md
│   │   ├── tile-size-selection.md
│   │   ├── online-softmax.md
│   │   └── fused-epilogue.md
│   │
│   └── retrospectives/          ← 복리 지식 축적 공간
│       └── (변환 세션마다 추가)
```

### 1-2. `@lat:` 주석으로 코드와 양방향 연결

이것이 lat.md의 핵심 가치입니다. 지식 그래프의 각 섹션이 **코드의 어느 지점에서 구현되었는지**를 추적합니다.

**예시 — nano-vLLM scheduler.py:**
```python
# @lat: [[scheduler#Waiting Queue → Running Queue]]
# @lat: [[scheduler#Batch Construction]]
class Scheduler:
    def __init__(self, block_manager):
        self.waiting_queue = []  # @lat: [[scheduler#Waiting Queue]]
        self.running_queue = []  # @lat: [[scheduler#Running Queue]]
```

**예시 — nano-vLLM attention kernel:**
```python
# @lat: [[triton-kernels#Flash Attention Forward]]
# @lat: [[patterns/online-softmax#Running Statistics]]
# CANDIDATE: cuTile 변환 시 ct.load / ct.store 로 대체 필요
@triton.jit
def attention_kernel(...):
    ...
```

이렇게 하면 `lat refs "triton-kernels#Flash Attention Forward"` 한 줄로 **이 설계 의도와 연결된 모든 코드 위치**를 즉시 찾을 수 있습니다.

### 1-3. `lat check`로 참조 무결성 확보

`lat init`을 실행하면 코딩 에이전트가 작업 완료 전 자동으로 `lat check`를 호출하게 설정할 수 있습니다. 이를 통해:
- 문서에서 언급된 모든 `[[wiki link]]`가 실제 존재하는 섹션을 가리키는지
- `@lat:` 주석이 존재하지 않는 섹션을 참조하고 있지 않은지
- `require-code-mention: true`가 설정된 테스트 명세에 백링크가 존재하는지

이 모든 것이 CI에서 자동 검증되어, **지식 그래프와 코드가 시간이 지나도 어긋나지 않도록** 강제할 수 있습니다.

---

## 2. Phase 2: cuTile 변환 대상 식별 및 리팩토링 청사진 작성

### 2-1. LLM과 함께 "Seam(이음새)" 식별하기

지식 그래프가 구축되면, LLM Coding Agent와 함께 다음과 같은 사고 흐름으로 변환 대상을 식별합니다.

**프롬프트 예시:**
> "`lat section 'architecture#Inference Pipeline'`의 결과를 읽고, 이 전체 흐름 중 `nn.Linear`, `F.scaled_dot_product_attention`, Triton 커널 등 GPU 연산을 직접 호출하는 지점을 모두 찾아줘. 각각을 `# @lat: [[candidate-cutile#MatMul Replacement]]` 태그로 표시해 줘."

### 2-2. nano-vLLM에서 cuTile 변환 대상이 되는 주요 지점

| nano-vLLM 구성요소 | 현재 구현 | cuTile 변환 대상 |
|:---|:---|:---|
| Attention 연산 (Prefill) | Triton Flash Attention | `ct.load`/`ct.store` 기반 타일드 어텐션 |
| Attention 연산 (Decode) | Triton 커널 | 단일 토큰 디코드를 위한 경량화된 cuTile 커널 |
| MLP (Dense) | `nn.Linear` → cuBLAS | cuTile MatMul + Fused Activation |
| LayerNorm / RMSNorm | Triton 커널 | cuTile Reduction + Element-wise |
| Rotary Embedding | Triton 커널 | cuTile Fused RoPE |
| KV Cache Read/Write | Triton 커널 | cuTile Memory Ops |
| Sampling (Logits → Token) | PyTorch | 선택적: cuTile Top-K / Top-P |

### 2-3. 변환 우선순위 설정 — 게슈탈트 기반 Amdahl's Law

전체 시스템의 전경을 결정하는 병목 지점부터 변환합니다:

1. **Attention (FMHA)**: 전체 추론 시간의 18-62%를 차지하는 최우선 변환 대상
2. **MatMul (MLP)**: 62%까지 차지하는 핵심 연산
3. **LayerNorm / RMSNorm**: 8-12% 차지, Fusion 시 더 큰 효과
4. **Rotary Embedding**: 2-5% 차지, Fused 시 부가 효과

이 순서는 우리가 논의한 **"전체 게슈탈트에 가장 큰 영향을 주는 구성요소부터"**라는 원칙에 부합합니다.

---

## 3. Phase 3: Semiformal Design Patterns를 적용한 cuTile 변환 실행

### 3-1. 각 변환은 하나의 "지각적 게슈탈트 형성 사이클"

변환 작업은 다음과 같은 **Validation Loop**로 진행됩니다. 이 루프 자체가 게슈탈트의 폐쇄성을 실현합니다.

```
[lat.md 패턴 카탈로그 로딩] → [LLM이 cuTile 코드 생성]
    → [lat check: 참조 무결성 검증] → [bench.py 실행]
    → [결과가 Reference와 일치?]
        ├─ YES → lat.md/retrospectives/ 에 성공 패턴 기록 → 다음 커널로
        └─ NO  → "깨진 게슈탈트" 진단 → 패턴 조건 수정 → 재생성
```

### 3-2. 패턴 카탈로그의 실전 적용 예

**FMHA 변환 시 `online-softmax.md` 패턴 로딩:**
```markdown
---
pattern_name: OnlineSoftmax
domain: Flash Attention cuTile Implementation
---

## 전경 (Intent)
단일 패스에서 running max와 running sum을 추적하여, 전체 입력을 두 번 읽지 않고 수치적으로 안정된 softmax를 계산한다.

## 핵심 변환 (Core Transformation)
1. 타일 루프 내에서 `m_i = max(m_{i-1}, row_max(S_ij))` 추적
2. `l_i = exp(m_{i-1} - m_i) * l_{i-1} + row_sum(exp(S_ij - m_i))`
3. 루프 종료 후 `P_ij = exp(S_ij - m) / l` 로 최종 정규화

## 검증
- PyTorch `F.softmax` 와 1e-3 이내 일치
- `ncu --metrics gpu_time` 에서 메모리 바운드 → 컴퓨트 바운드 전환 확인
```

이 패턴을 `lat expand "fix [[patterns/online-softmax#Rescaling Step]]"` 로 LLM에게 전달하면, LLM은 추상적인 설명이 아닌 **구체적인 코드 변환 규칙과 검증 기준**을 전달받게 됩니다.

### 3-3. 복리 실현: retrospectives에 기록

각 변환이 완료될 때마다:

```markdown
# lat.md/retrospectives/fmha-cutile-2026-05-17.md

## 실험: FMHA Triton → cuTile 변환
- **적용 패턴**: [[patterns/online-softmax#Rescaling Step]], [[patterns/tile-size-selection#Power of 2]]
- **성공한 설계 결정**: BLOCK_M=64, BLOCK_K=128 은 레지스터 스필 없이 최대 점유율 달성
- **실패한 시도**: BLOCK_M=128 시도 시 레지스터 스필로 23% 성능 저하
- **추출된 컨텍스트**: "FMHA의 경우 QK^T 연산의 중간 결과가 레지스터를 많이 점유하므로, BLOCK_M은 보수적으로 설정해야 한다"

## 다음 변환을 위한 힌트
- MLP 변환 시에도 유사한 레지스터 압박 예상 → [[patterns/tile-size-selection#Register Budget]] 먼저 검토
```

이 회고는 `lat search "FMHA BLOCK_M register spill"` 로 다음 에이전트 세션에서 자동 검색되어, **같은 실수를 반복하지 않도록 하는 컨텍스트 자산**이 됩니다.

---

## 4. Phase 4: 실증 데이터 수집 — 논문의 증거 축적

> **"Semiformal Design Patterns 접근법이 효과적이다"**라는 주장을 뒷받침하는 데이터

### 4-1. 수집할 메트릭

| 메트릭 | 측정 방법 | 의미 |
|:---|:---|:---|
| **변환 성공률** | 전체 시도 중 Validation PASS 비율 | LLM이 패턴을 얼마나 잘 따랐는가 |
| **평균 반복 횟수** | 커널당 Validation Loop 평균 반복 수 | 패턴의 완결성 지표 |
| **컨텍스트 재사용률** | `lat search` 로 과거 회고를 참조한 횟수 | 복리 효과의 정량적 증거 |
| **End-to-End Speedup** | nano-vLLM vs nano-vLLM-cutile 처리량 | 기술적 성과 |
| **패턴 카탈로그 성장률** | 프로젝트 기간 중 추가된 패턴 수 | 지식 축적의 정량화 |

### 4-2. 대조군 설정 (가능하다면)

동일한 FMHA 변환을:
- **실험군**: lat.md + Semiformal Design Patterns를 사용하여 LLM과 협업
- **대조군**: 전통적인 프롬프트 엔지니어링만 사용

두 경우의 성공률, 반복 횟수, 코드 일관성을 비교하여 **패턴 기반 접근의 효과를 실증**합니다.

---

## 5. lat.md 자체에 대한 개선 제안
lat.md에 기여할 수 있는 구체적인 개선 사항

### 5-1. `lat diff`: 변경의 파급 효과 시각화

**문제**: 한 패턴 섹션이 변경되면, 그 섹션을 참조하는 모든 코드 위치를 `lat refs`로 일일이 찾아야 합니다.

**제안**: `lat diff <section-id>` 명령어를 구현하여, 한 섹션의 변경이 그래프를 통해 어떤 코드로 파급되는지 자동으로 보여줍니다. 이것은 **게슈탈트의 연속성 유지**를 도구 차원에서 지원하는 것입니다.

### 5-2. `lat health`: 지식 그래프의 게슈탈트 품질 평가

**문제**: `lat check`는 참조 무결성만 검증할 뿐, 그래프가 LLM에게 **좋은 게슈탈트**를 제공하는지는 평가하지 않습니다.

**제안**: 그래프의 구조적 품질을 평가하는 `lat health` 명령어:
- **고립 섹션 비율**: 다른 어떤 섹션과도 연결되지 않은 문서들 (근접성 위반)
- **깊이 불균형**: 지나치게 중첩된 섹션 vs 평평한 구조
- **역참조 커버리지**: `@lat:` 주석이 없는 코드 블록 비율

### 5-3. Pattern Enforcement 메타데이터

**문제**: `require-code-mention: true`는 테스트 명세에만 적용됩니다. 설계 패턴에는 유사한 추적 메커니즘이 없습니다.

**제안**: 다음과 같은 메타데이터를 제안합니다:
```markdown
---
pattern_name: SharedMemoryCoalescing
pattern-enforce: true
enforce-rule: "stride > 1 → transpose, stride % 32 == 0 → pad +1"
---
```
`lat check`가 이 규칙을 참조하는 코드 블록이 실제로 그 변환을 적용했는지 검증하게 합니다.

---

## 6. 전체 워크플로우 요약

```
┌─────────────────────────────────────────────────────┐
│  Phase 1: 역설계 (2-3일)                            │
│  lat.md 지식 그래프로 nano-vLLM의 의도 포착          │
│  @lat: 주석으로 코드와 양방향 연결                   │
├─────────────────────────────────────────────────────┤
│  Phase 2: 변환 청사진 (1일)                          │
│  cuTile 변환 대상 Seam 식별                          │
│  우선순위: FMHA → MatMul → LayerNorm → RoPE         │
├─────────────────────────────────────────────────────┤
│  Phase 3: 변환 실행 (2-4주)                          │
│  패턴 카탈로그 로딩 → Validation Loop → 회고 기록    │
│  각 커널 변환 시 lat check로 무결성 유지             │
├─────────────────────────────────────────────────────┤
│  Phase 4: 실증 데이터 수집 (변환과 병행)             │
│  성공률, 반복 횟수, 컨텍스트 재사용률 측정           │
│  대조군과 비교하여 패턴 기반 접근의 효과 실증         │
└─────────────────────────────────────────────────────┘
```

---

## 결론: 이 프로젝트가 증명하는 것

이 프로젝트가 완료되면, 당신은 다음을 실증하게 됩니다:

1. **lat.md는 단순한 문서화 도구가 아니라**, LLM Coding Agent와 인간이 공유하는 **지각적 공간**을 설계하는 플랫폼이다.
2. **Semiformal Design Patterns는** GPU 커널 개발의 암묵지를 체계화하여, 상향식(구현)과 하향식(설계)의 갈등을 해소한다.
3. **컨텍스트 복리는** 매 변환 세션에서 retrospectives에 축적된 지식이 다음 세션의 배경 지식으로 자동 활성화되며 실현된다.
4. **이 접근법은 학습 효과와 생산성 모두에서 측정 가능한 개선을 가져온다.**