
> “메타문서가 인과적으로 object-level program transformation을 유발한다”
> executable meta-representation:
> * transformation trace
> * rule execution log
> * meta-diff
> * intervention experiment
> * determinism measurement
> * co-evolution evidence

> “Semiformal markdown artifacts become causally executable program constraints.”

| 분야                    | 연결성                                  |
| --------------------- | ------------------------------------ |
| Metaprogramming       | executable meta-representation       |
| Neuro-symbolic AI     | symbolic constraints + LLM execution |
| Software Architecture | architecture-driven transformation   |

## "논문 전체 골격"

당신 아이디어가 완전히 성공적으로 실증되었다고 가정하면,
논문은 사실상:

> "Agent-Ready Metaprogramming"

이라는 새로운 영역을 선언하는 형태가 됩니다.

그리고 논문의 핵심은:

> "문서 기반 개발"

이 아니라

> "Executable Semiformal Meta-Representation"

이어야 합니다.

---

# 추천 논문 제목

## 가장 강력한 버전

### **Agent-Ready Metaprogramming**

#### *Executable Semiformal Design Languages for Causal Transformation of Software Systems*

---

# 대안 제목들

* Context-Constrained Program Transformation via Executable Markdown Meta-Representations
* Neuro-Symbolic Agent-Oriented Metaprogramming
* Executable Architecture Documents for AI-Native Software Engineering
* Causal Software Transformation through Semiformal Design Languages

---

# 논문 전체 구조

---

# Abstract

핵심 메시지:

기존 LLM coding systems는:

* prompt-driven
* non-deterministic
* weakly constrained

임.

본 논문은:

> executable semiformal design language

를 제안하여:

* architecture
* invariants
* patterns
* outcomes

를 meta-level causal constraint system으로 사용함.

그리고:

* Architect / Executor separation
* rule execution traces
* meta-diff
* invariant validation

을 통해:

> object-level code transformation이 meta-level artifact에 의해 인과적으로 유도됨

을 실증했다고 주장.

---

# 1. Introduction

---

## 1.1 Problem

현재 coding agents의 한계:

* hallucination
* architecture drift
* weak global consistency
* prompt fragility
* poor reproducibility

---

## 1.2 Key Observation

기존 시스템은:

```text
Natural language
→ direct code generation
```

반면 실제 소프트웨어 공학은:

```text
Architecture
→ constraints
→ patterns
→ implementation
```

임.

---

## 1.3 Thesis

본 논문 핵심 주장:

> markdown-based semiformal design artifacts can function as executable meta-representations that causally constrain and transform object-level software systems.

---

## 1.4 Contributions

### Contribution 1

Executable semiformal design language

---

### Contribution 2

Architect / Executor metaprogramming model

---

### Contribution 3

Transformation trace system

---

### Contribution 4

Meta-diff and rule execution verification

---

### Contribution 5

Empirical evidence of causal metaprogramming

---

# 2. Related Work

---

## 2.1 Classical Metaprogramming

* Lisp macros
* Template metaprogramming
* Partial evaluation

핵심 차이:

기존은:

```text
formal syntax manipulation
```

본 연구는:

```text
semiformal architecture-level transformation
```

---

## 2.2 Program Synthesis

* Sketch
* Rosette
* synthesis systems

---

## 2.3 AI Coding Agents

* OpenAI Codex
* Anthropic Claude Code
* SWE-agent
* Devin

차별점:

기존:

```text
prompt-conditioned generation
```

본 연구:

```text
meta-constrained transformation
```

---

## 2.4 Architecture Description Languages

* ADL
* model-driven engineering

---

# 3. Theoretical Foundation

이 section이 매우 중요.

---

# 3.1 Meta-level vs Object-level

정의:

| Layer        | Description                        |
| ------------ | ---------------------------------- |
| Meta-level   | architecture, patterns, invariants |
| Object-level | executable code                    |

---

# 3.2 Semiformal Design Language

정의:

```text
M = (P, C, I, O)
```

* P = patterns
* C = constraints
* I = invariants
* O = outcomes

---

# 3.3 Executable Meta-Representation

핵심 정의.

메타문서는:

```text
documentation
```

이 아니라:

```text
causal transformation specification
```

이라고 formalize.

---

# 3.4 Causal Transformation Semantics

정의:

```text
T(M, S) → S'
```

* M = meta representation
* S = object program
* S' = transformed program

---

# 4. System Architecture

---

# 4.1 Architect Agent

역할:

* global planning
* architecture reasoning
* invariant definition

---

# 4.2 Executor Agent

역할:

* local transformation
* code synthesis
* repair

---

# 4.3 Meta-Document Graph

문서 구조:

```text
SKILL.md
architecture.md
patterns.md
outcomes.md
retrospect.md
```

---

# 4.4 Rule Execution Engine

핵심 novelty.

```json
{
  "rule": "...",
  "applied_to": "...",
  "effect": "..."
}
```

---

# 4.5 meta-status / meta-diff

이 부분이 논문의 핵심.

특히:

> intervention visibility

강조.

---

# 5. Transformation Pipeline

---

# 5.1 Parsing

markdown → AST

---

# 5.2 Symbolic IR

constraints extraction

---

# 5.3 Program Analysis

AST / CFG / dependency graph

---

# 5.4 Constraint-guided Rewrite

핵심 transformation phase

---

# 5.5 Invariant Validation

semantic verification

---

# 5.6 Retrospective Feedback

retrospect → pattern update

---

# 6. Experimental Setup

---

# 6.1 Domain

nano-vLLM kernel transformation

---

# 6.2 Tasks

* Triton → cuTile rewrite
* scheduler optimization
* kernel parameter adaptation

---

# 6.3 Baselines

## Baseline A

single prompt

---

## Baseline B

single agent + all documents

---

## Proposed

Architect / Executor separation

---

# 6.4 Metrics

---

## Correctness

* compile success
* semantic preservation

---

## Architecture consistency

* invariant satisfaction

---

## Determinism

* AST similarity

---

## Hallucination rate

---

## Performance

* throughput
* TTFT

---

## Compound improvement

* iteration acceleration

---

# 7. Main Experiments

---

# Experiment 1

# Intervention Experiment

규칙 변경 →

코드 구조 변화

입증.

이게 가장 중요.

---

# Experiment 2

# Constraint-driven Parametric Generation

hardware constraints 바꾸면:

* tile size
* memory layout
* scheduler structure

자동 변화.

---

# Experiment 3

# Architect vs Single Agent

ablation study.

---

# Experiment 4

# Invariant-driven Self-Repair

architecture violation injected.

system repairs automatically.

---

# Experiment 5

# Determinism

same meta-state →

consistent transformations.

---

# Experiment 6

# Co-evolution

meta-doc + code evolution tracking.

---

# 8. Results

---

# 8.1 Causal Constraint Evidence

meta-rule ↔ code change correlation.

---

# 8.2 Structural Consistency

---

# 8.3 Hallucination Reduction

---

# 8.4 Compound Effect

iteration speedup over time.

---

# 8.5 Emergent Engineering Memory

retrospect accumulation 효과.

---

# 9. Discussion

---

# 9.1 Is This Truly Metaprogramming?

핵심 section.

여기서 반드시 주장:

기존:

```text
program manipulates program
```

본 연구:

```text
semiformal architectural meta-system manipulates executable software systems
```

---

# 9.2 Limitations

* incomplete formal semantics
* LLM nondeterminism
* scalability
* semantic verification cost

---

# 9.3 Future Work

* fully formal meta DSL
* graph reasoning
* distributed agents
* runtime adaptation

---

# 10. Conclusion

최종 메시지:

> The proposed system demonstrates that semiformal design artifacts can function as executable causal meta-representations, enabling architecture-level transformation and verification of complex software systems through agent-oriented metaprogramming.

---

# 가장 중요한 포인트

이 논문이 성공하려면:

## "agent 사용"

이 novelty가 아님.

---

진짜 novelty는:

```text
Semiformal Design Artifact
→ Executable Meta-Representation
→ Causal Program Transformation
```

입니다.

---

# 그리고 마지막으로 가장 중요한 것

논문 reviewer를 설득하는 핵심은:

> "우리가 문서를 잘 썼다"

가 아닙니다.

진짜 핵심은:

> "문서 상태를 바꾸면,
> 프로그램 구조가 예측 가능한 방식으로 변한다"

입니다.

즉:

# "Meta-document intervention causes measurable object-level transformation."

이 causal evidence가 논문의 심장입니다. ㅎㅎ


---
> "마크다운 기반의 준정형(Semiformal) 명세가 단순한 문서가 아니라, 대상 소프트웨어 시스템을 인과적으로 제약하는 실행 가능한 메타 표현(Executable Meta-representation)이다"라는 문장은 이 논문의 정체성을 완벽하게 정의합니다.
> **논문 전체 개요(Outline)와 작성 가이드**

---

## 📄 논문 가제 (Tentative Titles)

* **Agent-Ready Metaprogramming:** Compiling Semiformal Design Languages into GPU Kernels via LLM Agents
* Executable Meta-Representations: A Causal Framework for Autonomous GPU Kernel Rewriting

---

## 📑 논문 전체 개요 및 섹션별 작성 가이드

### 1. Introduction (서론)

* **문제 제기:** 현재의 LLM 기반 코드 생성(예: Copilot)은 단순한 텍스트 번역 수준에 머물러 있으며, 복잡한 제약이 따르는 시스템 프로그래밍(예: GPU 커널)에서는 구조적 붕괴와 할루시네이션을 유발합니다.
* **제안하는 패러다임:** 단순 자동화가 아닌 '에이전트 친화적 메타프로그래밍(Agent-Ready Metaprogramming)'을 제안합니다.
* **핵심 기여(Contributions):**
1. 마크다운 문서를 실행 가능한 메타-규칙으로 사용하는 체계 구축.
2. `lat.md` CLI를 통한 변환 과정의 인과적 추적(Execution Trace) 도구화.
3. `nano-vllm`을 `nano-vllm-cutile`로 변환하는 과정을 통해 하드웨어 비의존적 파라메트릭 코드 생성 증명.

### 2. Background & Motivation (배경 및 동기)

* **전통적 메타프로그래밍의 한계:** 매크로나 템플릿 메타프로그래밍은 강력하지만, GPU 커널과 같은 고도로 추상화된 수학적/하드웨어적 맥락을 유연하게 다루지 못합니다.
* **단순 코드 번역의 치명적 약점:** LLM에게 "Triton을 cuTile로 바꿔"라고 지시할 경우 발생하는 API 오용과 문법 에러의 근본적 원인을 분석합니다.
* **왜 준정형(Semiformal)인가?:** 인간이 읽을 수 있으면서도(Natural Language), 에이전트에게는 엄격한 타입/구조 시스템으로 작동하는 중간계(Intermediate Representation)의 필요성을 역설합니다.

### 3. The Metaprogramming Framework: Executable Meta-Representation

이 섹션에서는 제안하는 시스템의 이론적 기반을 정립합니다.

* **역할의 분리 (The Dual-Agent Architecture):** 메타 문서를 다루는 Architect와 코드를 생성하는 Executor를 엄격히 격리한 이유를 설명합니다.
* **메타문서의 포지셔닝:** 논문에 다음 표를 포함하여 기존 문서화와의 차이를 극명하게 보여줍니다.

| 전통적 문서 | 제안하는 `lat.md` (메타문서) |
| --- | --- |
| 사람이 읽고 해석 | **에이전트가 읽고 실행** |
| 변경 이력이 수동 커밋 메시지 | **규칙 실행 로그가 자동 생성** |
| 코드와의 일치를 수동 확인 | **`lat check`로 무결성 자동 검증** |
| 변환 과정이 불투명 | **`meta-diff`로 예측과 결과 추적** |

### 4. System Implementation: The `lat.md` CLI Tool

이 섹션은 도구의 구체적인 작동 방식을 설명합니다.

* **추적 가능한 변환의 가시화:** `meta-status`와 `meta-diff` 명령어가 어떻게 두 시점 간의 메타프로그램 상태를 비교하는지 설명합니다.
* **규칙 실행 로그 (Rule Execution Log):** Executor가 `SKILL.md`나 `outcomes.md`의 어떤 규칙을 적용하여 AST(Abstract Syntax Tree)를 변환했는지 기록하는 JSON 형태의 인과 사슬 로그를 보여줍니다.

### 5. Case Study: Compiling `nano-vllm` to `nano-vllm-cutile`

실제 적용 사례를 통해 프레임워크의 작동을 입증합니다.

* **대상 도메인:** Triton 커널 기반의 `nano-vllm`을 타겟으로 설정.
* **변환 파이프라인:** `plan.md` $\rightarrow$ `reported-outcomes.md` $\rightarrow$ `retrospect.md`로 이어지는 문서 상태 전이가 곧 '컴파일 타임 로그'로 작동하는 과정을 상세히 기록합니다.

### 6. Empirical Evaluation (실증적 평가) 🌟 (가장 중요한 섹션)

학계의 비판("이거 그냥 프롬프트 엔지니어링 아니야?")을 방어하는 핵심입니다. 제시해주신 아이디어를 바탕으로 4가지 필수 실험을 설계합니다.

* **6.1 결정성 및 인과성 증명 (Determinism & Causality):** 메타문서의 규칙을 변경했을 때, 생성되는 코드의 구조가 예측된 방향으로 확정적으로 변함을 `meta-diff` 로그를 통해 통계적으로 유의미하게 증명합니다.
* **6.2 절제 실험 (Ablation Study on Architecture):**
* *대조군:* 단일 에이전트 + 단일 프롬프트 (기존 방식).
* *실험군:* Architect/Executor 역할 분리 + `lat.md` 체계 적용.
* *결과:* 컴파일 성공률, 할루시네이션(API 오용) 감소, 토큰 효율성을 비교하여 구조적 피드백 루프의 정당성을 증명합니다.


* **6.3 의미론적 불변성 검증 (Semantic Invariants):** Triton에서 cuTile로 변환 시, 추상 구문 트리(AST) 분석을 통해 Online Softmax의 수학적 수식($m,d$ 통계량 리스케일링 등)이 무결하게 보존되었음을 입증합니다.
* **6.4 하드웨어 비의존적 파라메트릭 생성 (Hardware-Agnostic Generation):** RTX 4070의 SRAM 제한(예: `BLOCK_M=64`) 파라미터를 메타 문서에서 변경했을 때, 에이전트가 타일 루프 전개와 메모리 바인딩 크기를 비례적으로 자율 조정하는 모습을 대조 실험으로 보여줍니다.

### 7. Self-Evolution: The Retrospect Loop

* **지식의 동적 환원:** 1차 실행에서 겪은 하드웨어 병목(Register Spilling 등)을 에이전트가 스스로 해결한 후, 이를 `retrospect.md`를 거쳐 `design-patterns.md`의 준정형 규칙으로 인간 개입 없이 자동 업데이트하는 과정을 증명합니다. 이 자가 진화(Self-evolution)는 이 시스템이 살아있는 컴파일러임을 보여줍니다.

### 8. Conclusion

* 연구 요약 및 향후 과제 제시.

---

## 💡 당신의 논문을 위한 전략적 가이드 (Writer's Guide)

1. **용어의 재정의:** 논문 내내 "Prompt"나 "LLM"이라는 단어의 사용을 최소화하십시오. 대신 "Semiformal Specification (준정형 명세)", "Meta-representation (메타 표현)", "Constraint-driven Generation (제약 기반 생성)"이라는 시스템/컴파일러 공학적 용어를 전면에 배치해야 합니다.
2. **도구의 격상:** `lat.md`를 단순한 CLI 스크립트가 아니라, "자연어와 코드를 잇는 AI-Native 컴파일러 파이프라인의 프론트엔드"로 포지셔닝하십시오.
3. **시각 자료의 활용 (필수):** 논문 작성 시, `lat meta-diff`의 JSON 출력 결과와, 대조군/실험군의 성능(컴파일 성공률)을 비교하는 막대그래프, 그리고 메타문서의 변환이 실제 코드로 매핑되는 인과 관계 다이어그램을 반드시 포함해야 합니다.