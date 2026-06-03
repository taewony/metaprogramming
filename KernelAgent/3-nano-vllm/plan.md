# 📑 Project Roadmap: nano-vllm Reverse Engineering

본 프로젝트는 거대 언어 모델 서빙 프레임워크인 **vLLM**의 핵심 원리를 `nano-vllm` 코드베이스를 통해 분해(Decomposition)하고, 다시 재조립(Re-assembly)하며 심층적으로 이해하는 것을 목표로 합니다.

---

## 🛠️ Phase 1: 시스템 분해 및 핵심 문서화 (Decomposition)
가장 먼저 전체 코드베이스를 분석하여 입문자가 이해하기 쉬운 5단계 학습 경로를 구축했습니다.

*   **[01_Introduction]**: KV Cache 파편화 문제와 PagedAttention의 탄생 배경 설명.
*   **[02_PagedAttention]**: 물리적/논리적 블록 매핑 및 `BlockManager`의 역할 분석.
*   **[03_Scheduling]**: 요청의 생명주기(Waiting, Running)와 선점(Preemption) 로직 파악.
*   **[04_Model_Layers]**: 텐서 병렬화(Column/Row Parallel) 및 RoPE 위치 임베딩 구현 확인.
*   **[05_Engine_Flow]**: `LLMEngine`의 초기화부터 최종 토큰 생성까지의 오케스트레이션 정리.

---

## 🔍 Phase 2: 모델 정찰 및 데이터 준비 (Inspection)
특정 모델(예: DeepSeek)을 로드하기 전, 모델의 메타데이터를 분석하여 필요한 자원을 예측하는 도구를 마련했습니다.

*   **`src/download_model.py`**: HuggingFace로부터 모델을 안전하게 다운로드하는 스크립트.
*   **`src/inspect_model.py`**: `config.json`을 분석하여 GQA 비율, Layer 수, 필요한 KV Cache 메모리를 사전에 계산하는 도구.
*   **[docs/inspect_model.md]**: 모델 설계도 분석법 및 로컬 환경 준비 가이드.

---

## 💻 Phase 3: CPU 전용 시뮬레이션 환경 (Hacking)
GPU 의존성을 제거하고 vLLM의 **제어 로직(Control Plane)**만 따로 떼어내어 학습할 수 있는 시뮬레이션 모드를 구축했습니다.

*   **`src/cpu_sim/mock_model_runner.py`**: 실제 연산 대신 가짜 토큰을 생성하고 연산 시간을 모방하는 '가짜 근육' 구현.
*   **`src/cpu_sim/run_cpu_sim.py`**: 실제 `nano-vllm`의 `Scheduler`와 `BlockManager`를 사용하여 CPU 환경에서 추론 루프를 시각화.
*   **[docs/cpu_01~03]**: 두뇌(Control)와 근육(Data)의 분리 개념 및 시뮬레이션 관찰 포인트 정리.

---

## 🧪 Phase 4: 수치 검증 및 TDRE (Validation)
역공학한 코드의 정확성을 보장하기 위해 **Test-Driven Reverse Engineering (TDRE)** 방법론을 도입했습니다.

*   **`src/tests/utils.py`**: 고정된 랜덤 데이터(GIGO) 생성 및 `torch.allclose` 기반 수치 비교 유틸리티.
*   **`src/tests/test_layers.py`**: `ColumnParallelLinear`, `RotaryEmbedding` 등의 레이어가 정답(Golden Reference)과 일치하는지 자동 검증.
*   **[docs/test_driven_re.md]**: 수치적 정밀도 검증의 중요성과 오차 범위 관리 기법 설명.

---

## 🚀 Phase 5: Future Roadmap (Next Steps)
성공적인 분해 작업을 마친 후, 더 깊은 이해와 고도화를 위해 다음 단계로 나아갈 것을 제안합니다.

### 1. **연속 배치(Continuous Batching) 구현**
*   현재는 Batch 단위로 끊어서 처리하지만, 먼저 끝난 요청을 즉시 내보내고 새 요청을 채워 넣는 'Continuous Batching' 로직을 `Scheduler`에 추가해 보세요.

### 2. **실시간 시각화 대시보드 (Monitoring)**
*   `BlockManager`의 상태(`free_block_ids`, `used_block_ids`)를 실시간으로 보여주는 간단한 웹 대시보드나 터미널 UI를 만들어 보세요. 메모리가 동적으로 변하는 모습을 보면 PagedAttention이 더 확실히 이해됩니다.

### 3. **양자화(Quantization) 레이어 추가**
*   16비트 연산을 8비트나 4비트로 변환하는 레이어를 만들고, TDRE를 통해 원본 대비 수치 오차가 얼마나 발생하는지 측정해 보세요.

### 4. **Serving API 서버 구축**
*   시뮬레이션 모드나 실제 엔진을 FastAPI 등으로 감싸서 실제 웹 서비스처럼 동작하게 만들어 보세요. 수많은 동시 접속자가 들어올 때 스케줄러가 어떻게 버티는지 테스트할 수 있습니다.

---
> **최종 한 줄 평**: 분해(Decomposition)를 통해 원리를 배웠다면, 이제 최적화(Optimization)와 확장(Extension)을 통해 나만의 vLLM을 완성할 차례입니다.
