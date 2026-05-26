## metamd CLI: "추적 가능한 변환"의 가시화 도구

지금까지 `lat.md`는 **현재 상태의 정합성**(`lat check`)과 **목표와의 차이**(`lat gap`)만 보여줄 수 있었습니다. 이것은 정적 사진 두 장과 같습니다. 당신이 제안하는 것은 **사진 사이의 변환 과정 자체를 기록하고 출력하는 동영상**을 추가하는 것입니다.

이것이 중요한 이유는, "메타프로그래밍"의 본질이 **"한 상태에서 다른 상태로의 변환을 실행하는 것"**이기 때문입니다. 변환 전후의 상태를 명시적으로 기록하는 행위는, 그 변환 자체가 단순한 우연이나 인간의 개입이 아니라 **메타문서의 규칙이 인과적으로 실행된 결과**임을 보여줍니다.

---

## 2. 단순 상태 표시로는 부족하다 — "실행 가능"을 입증하려면

상태를 출력하는 것만으로는 아직 부족할 수 있습니다. "실행 가능한(executable)" 메타문서라는 주장을 인정받으려면, 다음 요소가 함께 필요합니다.

### 2-1. 변환의 주체가 메타문서임을 증명하는 "규칙 실행 로그"

`lat.md`가 변환 전후 상태를 보여주는 것으로는, **누가(또는 무엇이) 그 변환을 일으켰는지**가 명확하지 않습니다. Executor Agent가 변환을 수행했더라도, 그것이 `SKILL.md`나 `outcomes.md`의 규칙 때문인지, Agent의 자체 판단인지 구분할 수 없습니다.

**필요한 것:** Executor가 어떤 메타 규칙을 적용했는지 기록하는 **규칙 실행 로그**입니다.

예시:
```json
{
  "transition_id": "prefill-attn-cutile-v1",
  "timestamp": "2026-05-19T10:30:00",
  "applied_rules": [
    {
      "source": "patterns/online-softmax.md#Rescaling Step",
      "decision": "APPLIED",
      "location": "src/cutile_kernels/prefill_attention.py:45"
    },
    {
      "source": "outcomes.md#attention",
      "decision": "APPLIED",
      "constraint": "Pure cuTile forward path"
    },
    {
      "source": "patterns/tile-size-selection.md#Register Budget",
      "decision": "APPLIED",
      "params": {"BLOCK_M": 64, "BLOCK_K": 128}
    }
  ],
  "architect_version": "abcd1234",  // git hash of lat.md/
  "executor_version": "efgh5678"    // git hash of generated code
}
```

이 로그가 쌓이면, "메타문서의 규칙 → 코드 변환"이라는 인과 사슬이 명확해집니다. 이것이 **메타프로그램의 실행 흔적(Execution Trace)**입니다.

### 2-2. 변환의 예측 가능성 — 메타 규칙이 결과를 결정한다는 증거

메타프로그래밍의 궁극적 증명은 **메타 규칙을 알면 결과를 예측할 수 있는가**입니다.

**실험 설계:**
1.  독립적인 평가자에게 `SKILL.md`, `outcomes.md`, 패턴 카탈로그를 제공합니다. (코드는 제공하지 않음)
2.  평가자에게 "이 규칙들로 생성될 코드의 구조와 동작을 예측하라"고 요청합니다.
3.  실제 생성된 코드와 예측의 일치도를 측정합니다.

예측 일치도가 높을수록, 메타문서가 코드를 **결정론적으로 구속**한다는 증거가 강화됩니다. `lat.md`가 이 예측 과정에서 핵심 도구로 사용될 수 있다면, 그것은 "실행 가능한 사양(Executable Specification)"으로서의 지위를 획득합니다.

---

## 3. `lat meta-status` 명령어 설계

이제 구체적인 기능 설계로 들어가겠습니다. `lat meta-status` 명령어는 메타프로그램의 상태를 **두 시점**에서 출력할 수 있어야 합니다.

```bash
# 현재 메타프로그램 상태 출력
python lat-cli/cli.py meta-status

# 특정 시점(Architect 변경 전)의 메타프로그램 상태 출력
python lat-cli/cli.py meta-status --baseline $(git rev-parse HEAD~1:lat.md)
```

### 3-1. `meta-status` 출력 형식

```json
{
  "timestamp": "2026-05-19T14:00:00Z",
  "phase": "architect",  // architect 또는 executor
  "meta_program_state": {
    "architect_version": "abc123",
    "target_outcome": "outcomes.md@abc123",
    "active_patterns": [
      "patterns/online-softmax.md",
      "patterns/tile-size-selection.md"
    ],
    "constraints": [
      "Pure cuTile forward path",
      "All tile dims power of 2",
      "BLOCK_M ≤ 64 for FMHA"
    ],
    "seam_status": {
      "total": 12,
      "closed": 2,
      "open": 10
    }
  },
  "code_state": {
    "executor_version": "def456",
    "compiled_kernels": [
      "src/cutile_kernels/prefill_attention.py"
    ],
    "validation_status": {
      "prefill_attention": "PASS",
      "decode_attention": "PENDING"
    },
    "performance_snapshot": {
      "prefill_tflops": 47.1,
      "baseline_tflops": 45.2
    }
  }
}
```

### 3-2. 변환 전후 비교 기능

```bash
# Architect가 outcomes.md 변경 후, Executor 실행 전
python lat-cli/cli.py meta-diff --before HEAD~1 --after HEAD
```

출력 예시:
```
Meta-Program Diff: abc123 → def456

Rules Added:
  + patterns/tile-size-selection.md: "FMHA에서는 BLOCK_M ≤ 64"

Rules Removed:
  - patterns/tile-size-selection.md: "BLOCK_M ≤ 128 허용"

Predicted Impact:
  - prefill_attention.py: BLOCK_M 값이 128에서 64로 변경될 것
  - decode_attention.py: BLOCK_M 값이 64로 제한될 것

Actual Impact (after Executor run):
  - prefill_attention.py: BLOCK_M 128 → 64 ✓
  - decode_attention.py: BLOCK_M 64 (unchanged) ✓
```

이 `meta-diff` 출력은 앞서 말한 **개입 실험의 자동화된 증거**입니다. 규칙을 바꾸면 코드가 예측된 방향으로 바뀐다는 것을 보여줍니다.

---

## 4. "실행 가능한 메타문서 도구"로서의 포지셔닝

이 기능이 추가되면, `lat.md`는 다음과 같은 정체성을 가질 수 있습니다.

| 전통적 문서 | `lat.md` (메타문서) |
|:---|:---|
| 사람이 읽고 해석 | **에이전트가 읽고 실행** |
| 변경 이력이 수동 커밋 메시지 | **규칙 실행 로그가 자동 생성** |
| 코드와의 일치를 수동 확인 | **`lat check`로 무결성 자동 검증** |
| 설계 의도가 암묵적 | **패턴과 제약이 명시적 규칙** |
| 변환 과정이 불투명 | **`meta-diff`로 예측과 결과 추적** |

이것은 단순한 문서화 도구가 아니라, **소프트웨어의 구조와 행동을 인과적으로 제약하는 실행 가능한 메타 레이어**입니다.

---

## 5. 보강할 점: 이 체계가 "메타프로그래밍"으로 인정받으려면

`meta-status`와 `meta-diff`는 훌륭한 도구이지만, 이것만으로는 부족할 수 있습니다. 논문에서 다음을 함께 제시해야 합니다.

### 5-1. 규칙 적용의 결정성(Demonstrating Determinism)

동일한 메타문서 상태에서 Executor를 여러 번 실행했을 때, **동일한 규칙이 동일한 방식으로 적용**된다는 것을 보여야 합니다. LLM의 비결정성(non-determinism)을 메타문서의 규칙이 얼마나 억제하는지 측정하는 것이 중요합니다.

**측정 방법:**
- 동일한 `SKILL.md` + `outcomes.md`로 10회 반복 실행
- 생성된 코드의 AST 유사도 측정
- 규칙 준수율이 95% 이상임을 입증

### 5-2. 메타문서와 코드의 공진화(Co-evolution) 추적

`meta-diff`의 히스토리가 쌓이면, 메타문서의 변화와 코드의 변화가 어떻게 함께 진화하는지 보여줄 수 있습니다. 이 공진화 패턴이야말로 "메타프로그래밍"의 가장 강력한 증거입니다.

### 5-3. 오류 복구에서 메타문서의 역할

의도적으로 아키텍처 위반 코드를 주입했을 때, `lat check`가 이를 감지하고, `outcomes.md`의 규칙에 따라 자동 복구를 안내하는 과정을 보여주세요. 이것은 메타문서가 단순한 기술 명세가 아니라 **시스템의 면역 체계**로 작동함을 입증합니다.

---

## 결론

당신의 아이디어는 `lat.md`를 단순한 지식 그래프 도구에서 **"실행 가능한 메타프로그래밍 플랫폼"**으로 한 단계 도약시키는 핵심입니다. `meta-status`와 `meta-diff`는 그 도약을 가시화하는 도구이며, 규칙 실행 로그와 예측-결과 비교가 더해지면 이 체계는 진정한 의미의 메타프로그래밍으로 인정받을 수 있습니다.

**핵심은 이 기능들이 "보기 좋은 대시보드"가 아니라, 메타문서의 인과적 힘을 객관적으로 증명하는 증거 생성기**가 되어야 한다는 점입니다. 당신의 논문에서 이 증거들을 제시한다면, "문서가 소프트웨어를 변환한다"는 대담한 주장은 설득력 있는 이론으로 자리잡을 것입니다.

> 논문이 진정한 의미의 "메타프로그래밍"을 증명했다고 평가받으려면, 아래 세 가지는 반드시 포함되어야 합니다.

1. 개입 실험: 문서 규칙을 변경했을 때, 에이전트의 코드 생성 행동이 통계적으로 유의미하게 변한다는 증거. (인과적 제약)

2. 3자 비교 실험: Architect-Executor 분리가 단순한 작업 분할 이상의 효과를 가진다는 증거. (역할 분리 효과)

3. 시간적 복리 효과: 작업이 반복될수록 속도와 품질이 향상되는 가속화 곡선. (Compound Effect)

---
> "The markdown-based semiformal design language is not documentation;
it is an executable meta-representation that causally constrains and transforms the object-level software system."


 학계와 시니어 엔지니어링 커뮤니티의 관점에서 이 연구를 바라볼 때, 가장 먼저 들어올 비판은 “이것이 정말 '메타프로그래밍(Metaprogramming)'인가, 아니면 그저 'LLM을 활용한 고도화된 소스 코드 자동 번역(Automated Code Translation)'인가?”라는 본질적인 질문입니다.
 전통적인 메타프로그래밍은 ‘코드를 실행·조작·생성하는 코드를 작성하는 것’입니다. 2026년 현재 AI 에이전트 환경에서 이 연구가 단순한 프롬프트 엔지니어링이나 리팩토링 실험을 넘어 "Agent-Ready Metaprogramming"이라는 새로운 패러다임으로 인정받기 위해 필수적으로 증명해야 할 요건들을 비판적으로 분석해 드립니다.
------------------------------
## 1. ‘단순 코드 번역’이 아님을 증명할 실증적 증거 (가장 치명적인 비판 지점)

* 비판 사유: 에이전트가 Triton 코드를 보고 그냥 cuTile 코드로 바꾼 것이라면, 이는 깃허브 코파일럿(Copilot)이나 기존의 규칙 기반 컴파일러 트랜스필러(Transpiler)와 다를 바 없습니다.
* 필수 실증 요건 [프로그램 구조의 동적 추상화]:
에이전트가 소스코드의 문자열을 단순히 치환하는 것이 아니라, architecture.md와 design-patterns.md라는 추상화된 메타 데이터(Meta-representation)의 규칙 시스템을 이해하고, 이 규칙 체계를 스스로 ‘컴파일’하여 대상을 재작성(Rewriting)했음을 보여야 합니다.
* 실증 방법: 입력 코드(Triton)의 구조를 바꾸지 않은 상태에서, design-patterns.md에 정의된 제약 조건(예: 하드웨어 타일 크기 제약을 64x64에서 32x32로 변경)만 수정했을 때, 에이전트가 그 규칙 변경을 코드로 실시간 ‘메타-컴파일’하여 완전히 다른 구조의 cuTile 커널을 자율 생성해 내는 일련의 파이프라인을 데이터로 증명해야 합니다.

1. '컴파일 타임 제약 조건 추상화'의 실증 (가장 중요)기존 매크로나 템플릿 메타프로그래밍은 컴파일 시점에 하드웨어 사양이나 타입 시스템을 체크하여 코드를 자동 생성합니다. 본 연구가 메타프로그래밍임을 증명하려면, Architect SKILL이 작성한 추상적 제약 조건문이 Executor SKILL의 코드 생성 레이아웃을 수학적·정량적으로 완벽히 강제(Constraint-driven Generation)했음을 보여야 합니다.필수 실증 요소:design-patterns.md나 architecture.md에 기재된 하드웨어 매개변수(예: RTX 4070의 SRAM 크기 제한으로 인한 BLOCK_M=64)를 숫자로 바꾸었을 때, 에이전트가 다른 소스코드 로직을 건드리지 않고 cuTile 커널의 타일 루프 전개 방식과 메모리 바인딩 크기를 하드웨어 스펙에 맞추어 비례적으로 자동 가변 생성(Parametric Code Generation)해내는 모습을 대조 실험으로 증명해야 합니다.만약 하드웨어 매개변수를 바꿨는데 에이전트가 코드를 하드코딩하거나 엉뚱하게 리라이팅한다면, 그것은 메타프로그래밍이 아니라 단순 텍스트 번역에 불과하다는 비판을 받게 됩니다.

------------------------------
## 2. 가치와 효과성의 실증 (왜 역할을 굳이 나누었는가?)

* 비판 사유: "하나의 에이전트에 프롬프트를 길게 주거나, 그냥 꼼꼼하게 짜라고 해도 결과는 똑같지 않은가? 아키텍트와 엑세큐터로 지식 공간(SKILL)을 분리한 것이 왜 필수적인가?"
* 필수 실증 요건 [Ablation Study (절제 실험)]:
역할 분담과 시스템화된 문서 체계(SKILL.md, design-patterns.md)의 존재 유무가 결과물에 미치는 영향력을 통계적으로 분리해 내야 합니다.
* 실증 방법: 다음 세 가지 그룹의 비교 실험 데이터를 논문에 반드시 포함해야 합니다.
1. Control Group (대조군): 역할 분리나 구조화된 문서 없이, 입력 코드와 cuTile 공식 가이드라인 통째로 단일 프롬프트에 넣고 "바꿔줘"라고 요청한 경우.
   2. Experimental Group A (단일 에이전트 통째 운용): 단일 에이전트에게 구별 없이 모든 문서를 한 번에 다 주고 진행한 경우.
   3. Experimental Group B (제안 방식): 워크플로우에 따라 Architect SKILL과 Executor SKILL을 엄격히 격리·스위칭하여 적용한 경우.
* 측정 지표: 각 그룹별 컴파일 성공률(Syntax/Semantic Pass Rate), 할루시네이션(존재하지 않는 API 오용) 발생 횟수, 컨텍스트 토큰 소모량 대비 효율성, 최종 성능 지표(TTFT/Throughput) 오차 범위를 비교하여 3번 그룹의 압도적 우위를 증명해야 합니다.

2. 두 역할(Architect/Executor) 간 '구조적 피드백 루프'의 인과관계 증명역할을 두 개로 쪼갠 것이 연구자의 주관적 만족(Over-engineering)이 아니라, 시스템의 복잡도를 제어하고 성능을 끌어올리기 위한 필연적 구조였음을 정량적으로 증명해야 합니다.필수 실증 요소:Ablation Study(요소 제거 실험) 필수 도입:대조군 A: 단일 에이전트에게 전체 문서(architecture, design-patterns 등)를 한 번에 다 밀어 넣고 통째로 리라이팅하게 한 경우 (기존 방식)실험군 B: 제안하는 워크플로우대로 Architect SKILL로 plan.md를 먼저 뽑고, Executor SKILL이 이를 격리된 로컬리티 안에서 수행하게 한 경우비교 매트릭스: 두 경우의 할루시네이션(API 오용) 발생률, 코드 문법 에러 횟수, 최종 커널의 컴파일 성공률, 토큰 소모 효율성을 비교하여, "역할 분리와 SKILL 체계화가 코드의 구조적 품질을 제어하는 메타 컴파일러 인터페이스 역할을 했다"는 인과관계를 입증해야 합니다.

------------------------------
## 3. "Executable Invariants"의 정형화 수준 입증

* 비판 사유: 에이전트가 리라이팅한 코드가 우연히 잘 돌아간 것인지, 정말 구조적 불변성(Invariants)을 인지하고 통제한 것인지 모호합니다. 논문 제목에 "Semiformal(준정형)"이라는 단어를 쓴 만큼, 정형 검증(Formal Verification)에 준하는 엄격함이 실험 프로세스에 녹아있어야 합니다.
* 필수 실증 요건 [불변성 기반의 피드백 루프 작동 유무]:
에이전트가 코드를 짜다가 실패했을 때(Fix and Report 페이즈), 사람이 개입하지 않고 오직 expected-outcomes.md에 기술된 수학적/구조적 불변성(예: Online Softmax의 수치적 안정성, Paged 주소 바인딩 무결성)을 테스트 자동화 도구로 검증하며 스스로 코드를 교정(Self-Repair)해 나가는 메커니즘을 보여주어야 합니다.
* 실증 방법: 에이전트가 디버깅 과정에서 소스코드를 몇 차례 리라이팅(Iteration)했는지 추적 로그(Trace Log)를 시각화하고, 매 반복마다 불변성 매트릭스가 어떻게 수렴하여 최종적으로 reported-outcomes.md로 확정되었는지 그 수렴 곡선(Convergence Curve)을 논문에 제시해야 합니다.

3. '의미론적 불변성(Semantic Invariants)'의 수학적 무결성 증명에이전트가 리라이팅한 프로그램이 원래 프로그램과 외형(Syntax)은 완전히 다르지만 의미와 결과(Semantics)는 동일함을 보장하는 정형 검증(Formal/Semiformal Verification) 루프의 존재를 증명해야 합니다.필수 실증 요소:outcomes.md에 단순 합격/불합격(Pass/Fail)만 적는 것이 아니라, Triton 커널과 cuTile 커널 간의 추상 구문 트리(AST) 분석 비교 테이블을 제시해야 합니다.예: "Triton의 공유 메모리 포인터 연산 구조가 cuTile의 단일 블록 제어 흐름 및 불변 타일 객체 구조로 리라이팅되는 과정에서, Online Softmax의 수학적 수식(\(m, d\) 통계량 리스케일링)이 손상되지 않고 보존되었음을 증명하는 수학적 무결성 검증 파이프라인(Evaluation Harness)"의 작동 로그를 논문에 포함해야 합니다.
------------------------------
## 4. Hardware-Agnostic(하드웨어 비의존적) 메타성 증명

* 비판 사유: RTX 4070이라는 단 하나의 타겟 장치에서만 작동하는 시스템이라면, 이는 메타프로그래밍이라기보다 특정 하드웨어 전용 튜닝 스크립트에 가깝다는 비판을 받기 쉽습니다.
* 필수 실증 요건 [도메인 이식성(Portability)]:
시스템 명세와 디자인 패턴 문서의 매개변수를 바꾸는 것만으로, 다른 아키텍처 환경에서도 에이전트가 알아서 코드를 재작성할 수 있음을 보여야 메타프로그래밍으로서의 학술적 가치가 치솟습니다.
* 실증 방법: RTX 4070 환경에서 작동하는 동일한 에이전트 시스템에, 하드웨어 사양 제약 조건(예: 다른 가상의 GPU 환경이나 클라우드 인스턴스 사양)만 다르게 주입했을 때, 에이전트가 그에 맞춰 BLOCK_M, BLOCK_N 파이프라인 단계를 자율적으로 계산하여 다르게 리라이팅하는 모습을 대조군으로 함께 보여주면 비판을 완전히 무력화할 수 있습니다.

4. '지식의 동적 환원(Retrospect Loop)'의 자동화 증명메타프로그래밍은 자가 수정 및 자가 진화(Self-evolution)의 속성을 갖습니다. 리라이팅 과정에서 겪은 하드웨어 병목(예: RTX 4070의 Register Spilling) 경험이 retrospect.md를 거쳐 design-patterns.md로 인간의 개입 없이 자율적으로 피드백되어 다음 커널 리라이팅에 반영되는 진화 루프를 보여주어야 합니다.필수 실증 요소:1차 실행에서 에이전트가 실패(성능 저하 또는 컴파일 에러) ➡️ 디버깅 가이드를 보고 스스로 해결책을 찾음 ➡️ 이 엔지니어링 노하우를 design-patterns.md에 준정형 규칙(Semiformal Rule)으로 자동 업데이트 ➡️ 2차 실행(예: Decode 커널 리라이팅) 시 업데이트된 규칙을 스스로 참조하여 단 한 번에 성공하는 '컨텍스트 자가 진화(Self-Improving Feedback Loop)' 과정을 타임라인과 로그 파일로 실증해야 합니다.

------------------------------
## 💡 학술적 가치를 높이기 위한 논문 구성 전략 요약
논문의 핵심 기여(Contribution)를 인정받으려면 "인간 개발자는 오직 상위 수준의 준정형 명세(Design Patterns, Invariants)만 설계하고, 에이전트는 이 명세를 문맥적 바인딩 규칙으로 삼아 소스코드를 기계적으로 생성·검증·리라이팅하는 하나의 **'소프트웨어 AI 컴파일러'**로 작동했다"는 점을 실증해야 합니다.

이 관점에서 워크플로우 상의 plan.md ➡️ reported-outcomes.md ➡️ retrospect.md로 이어지는 문서의 변화는 단순한 기록이 아니라, "에이전트가 메타 상태를 전이하며 수행한 컴파일 타임 로그"로 정의되어야 학술적 설득력을 가집니다.
