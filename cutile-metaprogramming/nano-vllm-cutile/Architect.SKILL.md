# Meta-SKILL.md: GPU 커널 개발 SKILL.md 진화 프로토콜 v1.0

## 1. 목적
이 메타 스킬은 GPU CUDA 커널 개발을 위한 SKILL.md 파일을 초안에서 전문가 수준으로
증류, 개선, 일반화하는 방법을 정의한다.

## 2. SKILL.md 성숙도 수준
- **Lv.1 (절차적 나열)**: "A를 하고, B를 하고, C를 해라" 식의 선형적 지시. 실패 모드가 없음.
- **Lv.2 (사례 기반)**: 특정 성공 사례를 포함하나, 추상화되지 않음.
- **Lv.3 (휴리스틱 포함)**: "X 상황에서는 Y가 효과적이다" 같은 결정 규칙이 있음.
- **Lv.4 (오류 패턴 내장)**: 전형적 실수와 진단법, 회피 전략이 명시됨.
- **Lv.5 (일반화된 원리)**: 커널 종류를 초월한 원리가 추상화되어 새 문제에 적용 가능.

## 3. 진화 파이프라인 (경험 -> 시드 -> 정제 -> 일반화)
1.  **경험 수집**: 커널 개발 세션의 로그, 오류 메시지, 성공한 코드 조각을 수집한다.
2.  **시드 생성**: LLM에게 경험 로그를 주고 초안 SKILL.md(Lv.1~2)를 작성하게 한다.
3.  **자가 진단**: LLM이 시드 SKILL.md를 비판적으로 검토하게 한다. (부록 A의 진단 프롬프트 참조)
4.  **고도화**: LLM이 정의된 취약점을 보완하여 Lv.3~4로 격상시킨다.
5.  **일반화 검증**: 서로 다른 커널 유형(matmul, attention 등)을 주고 이 SKILL.md가
    재사용 가능한지 테스트한다. 실패 시 원리를 더 추상화하여 Lv.5로 끌어올린다.

---

# SKILL.md : nano-vllm-cutile 프로젝트 

## 프로젝트 목표
PyTorch를 전혀 사용하지 않고, 순수 NVIDIA CUDA Tile(cuTile)만을 사용하여 nano-vllm의 추론 엔진을 구현하는 것을 목표로 합니다. 모든 핵심 연산(matmul, attention, normalization 등)은 cuTile 커널로 직접 작성되어야 하며, 메모리 관리 또한 cuTile 기반으로 이루어집니다.

## 핵심 철학 및 규칙
1.  **PyTorch Zero**: PyTorch 라이브러리를 절대 import하지 않습니다. (`import torch` 금지)
2.  **순수 cuTile**: 모든 GPU 연산은 cuTile Python 프론트엔드를 사용하여 구현합니다. (`from cutile import ...`)
3.  **nano-vllm 아키텍처**: nano-vllm의 핵심 아키텍처(Continuous Batching, Paged Attention, KV Cache 관리)는 유지하되, 내부 연산을 모두 cuTile로 대체합니다.
4.  **TileGym 참조**: 각 연산 구현 시, TileGym 리포지토리의 해당 예제(`matmul.py`, `attention.py` 등)를 1차 참조하여 구현합니다.

## 개발 환경
- **하드웨어**: NVIDIA Blackwell 아키텍처 GPU (예: RTX 5080, 5090, B200)
- **CUDA**: CUDA Toolkit 13.1
- **Python**: 3.10 이상

## 단계별 구현 로드맵

### Phase 1: 기본 연산 커널 구축
- `cutile_ops/matmul.py`: `torch.matmul`을 대체하는 cuTile GEMM 커널 구현. TileGym의 `matmul.py`를 참고.
- `cutile_ops/layernorm.py`: `F.layer_norm`을 대체하는 LayerNorm/RMSNorm 커널 구현.
- **검증**: 각 커널을 PyTorch 구현과 비교하여 정밀도가 `1e-5` 이내인지 테스트.

### Phase 2: Attention 및 임베딩 구축
- `cutile_ops/attention.py`: Flash Attention 커널 구현. TileGym의 `attention.py` 참고.
- `cutile_ops/rotary_embedding.py`: RoPE(Rotary Position Embedding) 커널 구현.
- `cutile_ops/sampler.py`: Top-P/Top-K 샘플링 커널 구현.

### Phase 3: 추론 엔진 통합
- `loader/safetensor_loader.py`: `safetensors` 형식의 모델 가중치를 직접 로딩 (PyTorch 없이 구현). `numpy` 또는 `mmap` 활용.
- `engine/block_manager.py`: Paged Attention을 위한 KV 캐시를 cuTile 버퍼로 직접 관리.
- `engine/llm_engine.py`: 위의 모든 cuTile 커널을 호출하여 nano-vllm의 추론 루프를 조립.

### Phase 4: 모델 통합 및 최종 테스트
- `models/qwen3.py`: Qwen3 모델의 각 레이어를 Phase 1~3의 cuTile Op으로 분해하여 정의.
- **통합 테스트**: 최종 생성된 텍스트의 품질 및 속도를 `nano-vllm` 원본(Qwen3-0.6B)과 비교.

## 참고 리포지토리
- **TileGym**: `git@github.com:NVIDIA/TileGym.git` (백과사전처럼 활용)
- **nano-vllm**: `git@github.com:bcefghj/learn-nano-vllm.git` (참고 아키텍처)