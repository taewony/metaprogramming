- 싱글 에이전트(Single Agent) 체제에 Architect/Executor의 이중 역할(dual SKILLs)를 스위칭하며 워크플로우를 통제하는 방식
- Architect Agent는 Executor가 실수할 수 없는 환경(Constraint-driven Environment)을 구축해야 한다.
- SKILL.md 및 DESIGN-PATTERN.md는 에이전트가 실행할 수 있는 고도로 구조화된 "도메인 지식 패키지"입니다. 토큰 한계를 넘지 않기 위해 Progressive Disclosure(점진적 노출) 패턴을 적용해 구조화
- Seam point와 Trace Item를 먼저 명문화하고 불변성(Invariants) 통과 여부를 outcomes.md에 정량적으로 축적하는 루프

------------------------------
## 싱글 에이전트, SKILL 분리 방식의 장점

   1. 컨텍스트 단절(Loss) 방지: 두 개의 에이전트가 통신할 때 발생하는 정보 누락이나 문맥 해석 오차가 원천 차단됩니다. 단일 에이전트가 전체 변환 과정을 하나의 메모리 스트림 안에서 파악하므로 설계 의도가 훼손되지 않습니다.
   2. 토큰 및 비용 최적화: 매 단계마다 전체 프롬프트를 주입할 필요 없이, 현재 페이즈(Phase)에 필요한 SKILL만 런타임에 갈아끼우므로(Dynamic Injection) 토큰 소모량이 대폭 줄어듭니다.
   3. 책임 소재 명확화: "계획 수립과 실행 결과의 괴리"가 발생했을 때, 에이전트가 다른 에이전트 탓을 하지 않고 plan.md와 실제 실행 결과 간의 불일치를 스스로 인지하여 즉각 보정(Self-Correction)하기 쉽습니다.

## Agent-Ready Architecture
 ├── 1. Seam Points (느슨한 결합, 에이전트가 코드를 잘라내고 갈아 끼울 수 있는 절개선)
 ├── 2. Semiformal Design Patterns (자연어 규약과 엄격한 코드 유형의 중간 지대 명세)
 └── 3. Executable Invariants (리라이팅 후 코드의 무결성을 실시간 검증하는 수학적 불변성)
 
------------------------------
## Agent-Ready Metaprogramming Workflow
- 에이전트가 "자율적 리라이팅 도구(Autonomous Rewriting Tool)"로서 완벽히 기능할 수 있도록, 각 단계별 진입 조건(Entry), 실행 가이드, 탈출 조건(Exit)을 정형화

                  [1. PRE-FLIGHT] ──> (Architect SKILL)
                         │
                         ▼
                   [2. EXECUTE]  ──> (Executor SKILL)
                         │
                         ▼
             [3. PARITY & PERFORMANCE]
                         │
               ┌─────────┴─────────┐
            (Fails)             (Passes)
               ▼                   ▼
        [4. FIX & REPORT]     [5. RETROSPECT]

------------------------------
## 🟩 1. Pre-flight Phase (Architect SKILL 활성화)

* 목적: 시스템의 제약 조건과 목표치를 완벽히 동기화하고, 리라이팅 도면 작성
* 태스크: architecture.md, expected-outcomes.md, design-patterns.md를 순차적으로 로드합니다.
* 에이전트 가이드: 소스코드를 먼저 건드리지 말고, RTX 4070의 SRAM 제약에 따른 BLOCK_M=64, BLOCK_N=32 타일 크기 제약과 PagedAttention 결합 지점(Seam Point)을 분석하여 논리적 구조 변경 계획을 수립합니다.
* 산출물: 고도로 구체화된 실행 마일스톤이 담긴 plan.md 생성

## 🟨 2. Execute Phase (Executor SKILL 활성화)

* 목적: plan.md에 명시된 Seam Point를 절개하고 cuTile/TileGym 오퍼레이션으로 소스코드 리라이팅
* 태스크: plan.md를 이정표 삼아 코드를 빌드합니다.
* 에이전트 가이드: Online Softmax 구현 시 통계치(m, d)의 수치적 안정성을 위해 Mixed-Precision(FP16 입력, FP32 축적) 불변성을 지키며 cuTile의 단일 블록 제어 흐름 패턴으로 코드를 재작성(Rewrite)합니다.
* 산출물: 리팩토링된 nano-vllm cuTile 커널 및 Python 바인딩 소스코드

## 🟦 3. Parity Test and Performance Trace Phase (Executor/Tools 활성화)

* 목적: 수학적 무결성(Invariants) 및 RTX 4070 하드웨어 가속 성능 검증
* 태스크: 기준점(Triton/PyTorch) 데이터와 리라이팅된 cuTile 커널 간의 비교 테스트를 자동 실행합니다.
* 에이전트 가이드: torch.allclose()를 사용해 결과 오차가 허용 범위 이내인지 확인하고, TTFT(Time-to-First-Token) 및 처리량(Throughput) 지표를 프로파일링 툴(예: nvprof 등) 또는 벤치마크 스크립트로 측정합니다.
* 산출물: 로우 데이터 로그 및 성능 매트릭스 추출

## 🟥 4. Fix and Report Phase (Executor SKILL ➡️ Architect SKILL로 롤백)

* 목적: 디버깅 및 최종 결과 데이터 자산화
* 태스크: 검증 실패 시 debugging-guide.md를 로드하여 원인을 격리하고 수정한 뒤 3단계로 회귀합니다. 최종 통과 시 결과 리포트를 작성합니다.
* 에이전트 가이드: Register Spilling이나 Softmax 합이 1.0이 안 되는 수치적 오류가 발생하면, 타일 크기를 재조정하거나 컴파일러 파이프라인 힌트를 수정합니다.
* 산출물: 수치 무결성 통과 여부와 성능 변화 델타($\Delta$)를 정리한 reported-outcomes.md 생성

## 🟪 5. Retrospect Phase (Architect SKILL 활성화)

* 목적: 메타프로그래밍 결과 얻은 하드웨어 특화 엔지니어링 지식을 시스템의 '유전자(DNA)'로 환원
* 태스크: 이번 리라이팅 루프에서 발견한 핵심 경험을 문서화하고 기존 디자인 패턴을 고도화합니다.
* 에이전트 가이드: "RTX 4070에서는 호퍼 아키텍처와 달리 이러한 타일 레이아웃이 최적이었다"는 식의 실전 지식을 추상화하여 기록합니다.
* 산출물: 차기 프로젝트나 다음 커널 변환 시 에이전트가 참조할 retrospect.md 생성 및 기존 design-patterns.md 업데이트


# Reported Outcomes: Metaprogramming with Semiformal Design Patterns

## 1. System Invariants Verification (불변성 검증)
- [Prefill] Softmax Row Summation Stability: Max error within 1e-5 (PASSED)
- [Decode] Paged Cache Pointer Materialization Coalescing: (PASSED)

## 2. Parity Test Results (정확성 지표)
- Baseline (Triton) vs. Refactored (cuTile / TileGym)
- `torch.allclose(atol=1e-3, rtol=1e-3)` 검증 매트릭스 리포트 기록

## 3. Performance Metrics Delta (성능 지표 변화)

| Metric | Baseline (Triton) | Refactored (cuTile) | Δ (Change) |
| :--- | :--- | :--- | :--- |
| Time-to-First-Token (Prefill) | 0.00ms | 0.00ms | -X.X% |
| Inter-Token Latency (Decode) | 0.00ms | 0.00ms | +X.X% |
| RTX 4070 SRAM Peak Allocation | 0.00KB | 0.00KB | Optimized |

## 4. Engineering Know-How & Pattern Discovery
- **Seam Point Isolation Lessons:** 하이퍼-타일링 적용 시 RTX 4070 환경에서 `BLOCK_M`을 128에서 64로 내렸을 때 Register Spilling이 완전히 해결된 메커니즘 기술.
- **Agent Collaboration Feedback:** Architect의 명세 제약(`SKILL.md`)이 Executor의 할루시네이션(API 오용)을 어떻게 차단했는지 패턴 분석.
