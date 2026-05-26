# nano-vllm-cutile

**GPU Kernel Development 특화 지식 증폭 도구 및 에이전틱 하니스(Agentic Harness)**

> ## Metaprogramming with Semiformal Design Specs for GPU Kernel development
> 이 프로젝트는 반정형 설계 언어(Semiformal Design Patterns, SDP)를 핵심 매개체로 활용하여 인간 연구자와 AI 에이전트 간의 의미론적 지식 기반(Semantic Knowledge-Base)을 구축하고, 이를 통해 저수준 GPU 커널(cuTile/CUDA)을 체계적으로 개발하는 시스템 아키텍처 및 에이전트 워크플로우를 실증합니다.

`nano-vllm` 코드베이스를 역설계하고 `cuTile` 기반으로 재구성하는 과정을 통해,
GPU 커널 개발에 특화된 **Semiformal Design Patterns**를 발굴·축적하며
**코드와 지식이 함께 복리 증식**하는 개발 환경을 구축하는 프로젝트입니다.

---

## 철학

우리는 범용 지식 그래프 도구를 만드는 대신, **GPU 커널 개발**이라는 구체적인 도메인에 최적화된 도구와 방법론을 직접 설계합니다.

-   **Codebase와 Knowledge-base를 함께 Rewriting**  
    코드를 바꾸는 순간, 그 결정의 이유와 맥락, 결과가 `lat.md` 지식 그래프에 축적됩니다.
-   **복리 증식되는 지식 산출물**  
    한 번의 커널 변환에서 얻은 통찰이 `retrospectives/`와 `patterns/`에 기록되고,
    다음 변환의 **자동 배경 지식**이 되어 비용을 낮춥니다.
-   **The Dual Agent Roles Paradigm**
    LLM 에이전트는 도메인 설계 언어(DSL)를 통해 동기화되는 두 가지 특화된 역할로 분리되어 작동합니다.
    * **System Engineer (Architect):** 상위 수준의 SKILL과 아키텍처를 설계하고, Design Spec을 정의하며, 하위 모델이 준수해야 할 시스템 모델(System Model)과 물리 법칙(제약 사항)을 규정합니다.
    * **Kernel Engineer (Executor):** 구체화된 컨텍스트를 바탕으로 저수준 GPU 커널(cuTile) 코드를 구현하고, 통제된 환경에서 에러 없는 실험과 성능 프로파일링을 수행합니다.


---

## 프로젝트 구조

```
nano-vllm-cutile/
├── .skills/lat.md/SKILL.md  # Gemini CLI가 읽을 워크플로우 지시사항
├── lat-cli/                 # GPU 커널 개발 특화 지식 그래프 도구 (Python)
│   ├── checker.py           #   lat check — [[wiki link]] + @lat: 주석 검증
│   ├── graph.py             #   양방향 참조 그래프
│   ├── section.py           #   섹션 파싱, 탐색, 확장
│   ├── search.py            #   lat search — 시맨틱 검색 (Ollama API)
│   ├── gap.py               #   lat gap — outcomes.md 기반 차이 분석
│   ├── embedder.py          #   Ollama 임베딩 클라이언트
│   ├── vector_db.py         #   SQLite 기반 벡터 저장소
│   └── cli.py               #   통합 CLI
├── src/                     # Target codebase — nano-vllm을 cuTile로 변환한 결과물
├── nano-vllm/               # Reference: 원본 nano-vllm GitHub 저장소
├── TileGym/                 # Reference: cuTile 예제 및 라이브러리
├── lat.md/                  # 지식 그래프 (인간 + 에이전트가 함께 유지보수)
│   ├── architecture.md      #   nano-vllm 전체 아키텍처 및 설계 의도
│   ├── outcomes.md          #   변환 목표 (cuTile 기반 최종 모습)
│   ├── patterns/            #   반정형 설계 패턴 카탈로그
│   ├── retrospectives/      #   변환 세션별 회고 (복리 축적)
│   ├── tests/               #   프로젝트 특화 테스트 명세 (Markdown)
│   └── .cache/
│       └── vectors.db       #   시맨틱 검색용 벡터 저장소 (자동 생성)
└── README.md
```

---

## lat-cli: GPU 커널 개발 특화 지식 그래프 도구

`lat-cli/`는 표준 `lat` 명령어와 호환되는 인터페이스를 가진 **Python 경량 구현체**입니다.
LLM API 호출은 시맨틱 검색(`lat search`)에만 사용되며, 그 외 모든 기능은 순수 Python으로 동작합니다.

| 명령어 | 설명 | LLM 필요 |
|:---|:---|:---|
| `lat check` | 마크다운 `[[wiki link]]`와 코드 `@lat:` 주석의 참조 무결성 검증 | ❌ |
| `lat section` | `# heading` 기준 섹션 분할 및 링크 추출 | ❌ |
| `lat refs` | 특정 섹션을 참조하는 모든 코드 위치 검색 | ❌ |
| `lat locate` | 섹션 ID 퍼지 매칭 | ❌ |
| `lat expand` | `[[wiki link]]`를 해당 섹션 내용으로 치환하여 프롬프트에 주입 | ❌ |
| `lat gap` | `outcomes.md`와 현재 `@lat:` 주석 간 차이 분석 (Seam 식별) | ❌ |
| `lat search` | 마크다운 섹션 임베딩 → SQLite 벡터 DB → 코사인 유사도 검색 | ✅ |
| `lat pattern list/show/apply` | 패턴 카탈로그 관리 및 코드 적용 | ❌ |
| `lat retro` | 변환 세션 회고 템플릿 자동 생성 | ❌ |

---

## 시맨틱 검색 구조

### 임베딩

-   **모델**: `nomic-embed-text` (Ollama)
-   모든 `lat.md/` 마크다운 섹션을 읽어 임베딩 벡터를 생성하고 `vectors.db`에 저장합니다.

### `vectors.db` 스키마 (SQLite3)

```sql
CREATE TABLE IF NOT EXISTS sections (
  id TEXT PRIMARY KEY,              -- 섹션 식별자 (예: "architecture#Pipeline")
  file TEXT NOT NULL,                -- 파일명 (예: "architecture.md")
  heading TEXT NOT NULL,             -- 섹션 제목
  content TEXT NOT NULL,             -- 섹션 내용
  content_hash TEXT NOT NULL,        -- 내용 해시 (변경 감지용)
  embedding F32_BLOB(${dimensions}), -- 임베딩 벡터
  updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS sections_vec_idx ON sections (libsql_vector_idx(embedding));
```

### 활용

```bash
lat search "how does KV cache block allocation work?"
# → semantic search results ranked by cosine similarity
```

---

## 개발 시작하기

### 사전 요구사항

-   Python 3.10+
-   Ollama (로컬 실행 중)
-   `nomic-embed-text` 모델: `ollama pull nomic-embed-text`
-   `qwen3:8b` (선택, 코드 생성용): `ollama pull qwen3:8b`

### 설정

```bash
git clone https://github.com/your-org/nano-vllm-cutile.git
cd nano-vllm-cutile

# lat-cli 의존성 설치
pip install -r lat-cli/requirements.txt

# 벡터 DB 초기 빌드
python lat-cli/cli.py search --build-index
```

### 사용

```bash
# 지식 그래프 무결성 검사
python lat-cli/cli.py check

# 변환 대상 Seam 식별
python lat-cli/cli.py gap

# 시맨틱 검색
python lat-cli/cli.py search "Flash Attention bank conflict"
```

### Vertical Knowledge Architecture (지적 자산의 복리 성장 체계)

작업 디렉토리에 `lat.md/` 폴더를 두고, 이 폴더 안에 지식 자산을 축적합니다. `SKILL.md`가 Agent가 수행할 작업 절차에 대한 것이라면, `lat.md/` 폴더는 **학습자와 Agent 모두를 위한 학습 자본(Learning Capital)**입니다.

Architect 에이전트를 활용해 지적 자산을 지속적으로 확장하기 위해, 횡적 연결을 배제한 **엄격한 수직적 계층형 지식 아키텍처**를 구축합니다. 이 지식 베이스를 버전 관리 시스템(Git)과 연동하여 에이전트가 스스로 개선하게 함으로써, 시간이 지날수록 작업 품질과 생성 속도가 기하급수적으로 향상되는 지식의 복리 효과를 창출합니다.

1. **Level 3 (Meta-Skills Layer):** 에이전트의 역할, 프로젝트 방향성, 그리고 하위 SKILL들의 오케스트레이션 및 평가 기준을 정의합니다. (무엇을, 언제 할 것인가)
2. **Level 2 (Procedural Layer - SKILL.md):** 반복 가능한 워크플로우와 구체적인 스킬셋을 모듈화합니다. (어떻게 할 것인가)
3. **Level 1 (Constraint Layer - Design.md, Pattern.md, Rules.md):** 시스템 환경, 메모리 레이아웃, 성능 제약(Invariants) 및 금지된 코드 패턴(Anti-patterns) 등 시스템 모델을 정의합니다.

(Compress the knowledge about codebase of GPU Kernel domain into a tree — a set of interconnected markdown files (Design specs) that live in a lat.md/ directory at the root of your project.)

4. **Level 0 (Codebase Layer):** 실제 실행 가능한 아티팩트(Python/cuTile 코드) 및 대상 레퍼런스입니다.

### Cybernetic Feedback Loop Workflow

작업의 실행과 지식의 축적은 **Human-in-the-loop (HITL)** 기반의 사이버네틱 피드백 루프를 통해 이루어집니다.

1. **Context Compilation (Top-Down):** `tdcc.py`가 주어진 Task에 필요한 SKILL과 DESIGN 문서를 파싱하여, Stateless Executor가 참고할 단일 컨텍스트(`current_task.md`)로 렌더링합니다.
2. **Human Verification:** 연구자가 Staging 영역에서 컴파일된 컨텍스트(전경화된 지식)를 검토하고 조율합니다.
3. **Stateless Execution:** Executor 에이전트가 오직 `current_task.md`만을 바탕으로 코드를 변환/생성하고 실행 흔적(Trace log)을 남깁니다.
4. **Evaluation:** `outcomes.md`에 기술된 루브릭 평가 지표를 기반으로 산출물을 검증합니다.
5. **Distillation (Bottom-Up):** `distiller.py`가 평가 결과와 프로파일링 로그를 분석하여 인사이트를 추출하고, 연구자의 승인을 거쳐 상위 시스템 모델(DESIGN)과 절차(SKILL)를 개선합니다.

### 동작 방식

1. 지능적 agent에 의해 GAP analysis (GAP analysis SKILL 사용)
2. 파악된 GAP을 매우기 위한 다른 Design.md 참조 문서 파싱 (Reference SKILL 사용)
3. 주어진 codebase를 최종 상태로 변환하기 위한 plan.md 작성 (PLAN SKILL 사용)
4. Executor로 plan.md에 따라 codebase 변환
5. outcomes.md 에서 기술한 루브릭 평가 지료에 의한 검증
6. 산출된 평가 결과 및 저장된 trace log를 기반으로 distilled Design.md 및 SKILL.md 개선

- 통합적 가시화 (Holistic Visualization): 개별 함수나 커널이 아닌, 데이터가 입력되어 출력될 때까지의 전 과정을 하나의 '연산 그래프'로 파악한다. (전체는 부분의 합보다 크다)
- 상하향식 교차 분석 (Bi-directional Analysis):
  - Top-down: 비즈니스 논리 및 시스템의 최종 목적(예: vLLM의 'Throughput')에서 하위 제약 사항으로 내려온다.
  - Bottom-up: 하드웨어 제약(GPU 메모리, 대역폭) 및 데이터 파편에서 상위 구조를 설계한다.
- 커널 퓨전 및 자원 최적화 (Fusion & Optimization): 오버헤드를 발생시키는 경계선(I/O, Context Switching)을 허물고 연산을 하나로 묶어 최적의 실행 단위를 재구성한다.

1.  Deconstruction (해체): 기존 시스템을 최소 기능 단위(Atomic Unit)로 분해하고 병목 지점을 수치화한다.
2.  Pattern Recognition (패턴 인식): 분해된 요소들 사이의 숨겨진 상관관계와 반복되는 데이터 흐름을 찾는다.
3.  Gestalt Reconfiguration (재구성): 인지적/공학적 효율을 극대화할 수 있는 새로운 통합 구조(Fused Model)를 설계한다.
4.  Validation (검증): 재구성된 시스템이 부분의 합을 넘어서는 시너지(성능 향상)를 내는지 데이터로 증명한다.

## 결론: 결과물이 아니라 ‘안목’을 설계하는 경험 그 자체를 배우는 과정입니다.

이 모든 과정을 관통하는 최종 목표는, **“복잡한 시스템을 마주했을 때, ‘어떤 질문을 던져야 하는가’를 아는 사람”**이 되도록 하는 것입니다.

LLM과 함께 cuTile 및 vLLM의 세계를 탐험하는 이 여정은, 단순한 기술 스택 하나를 배우는 것이 아닙니다.

- **무엇이 전경이고 배경인지 순간적으로 포착하는 능력**
- **눈에 보이지 않는 상호작용을 추론하여 게슈탈트를 완성하는 능력**
- **그리고 그 통찰을 다음 단계의 자산으로 축적하여 복리로 성장하는 방법**

---

> 현재 진행 중인 nano-vllm-cutile 프로젝트의 **`[[wiki link]]` 문법은 Obsidian과 100% 호환**됩니다. `@lat:` 코드 주석은 `lat check`의 자동화된 검증 기능으로, `[[wiki link]]`로 구축된 지식 그래프는 Obsidian의 강력한 시각화 및 탐색 기능으로 상호 보완하며, `lat health`로 그 구조적 안정성을 관리할 수 있습니다. 이 세 가지가 유기적으로 결합되어 프로젝트의 지식 자산을 더욱 강력하게 만들어 줄 것입니다.

### 1. lat.md와 Obsidian의 완벽한 호환성

lat.md의 `[[wiki link]]` 문법과 `#`을 이용한 섹션 참조 방식은 Obsidian의 내부 링크 문법과 완전히 동일하며, 파일 시스템 기반으로 작동합니다. 

*   **파일(노트) 링크**: `[[architecture]]`는 Obsidian에서 `architecture.md` 파일을 바로 열어줍니다.
*   **섹션(헤딩) 링크**: `[[architecture#scheduler]]`는 `architecture.md` 파일의 `## Scheduler` 헤딩으로 정확히 이동합니다.

덕분에 `lat.md/` 폴더를 Obsidian에서 하나의 Vault로 열면, 모든 마크다운 파일과 링크가 **별도의 변환 과정 없이 그대로 하나의 '지식 그래프'로 시각화**됩니다. 또한 `@lat:` 주석으로 코드와 문서를 연결하는 lat.md의 핵심 기능도 Obsidian과 함께 사용할 수 있습니다.

### 2. `@lat:` 주석과 Obsidian의 상호 보완

`@lat:` 주석은 Obsidian이 기본적으로 지원하지 않는 lat.md의 핵심 기능으로, 다음과 같이 상호 보완적으로 작동합니다.

*   **`@lat:` 주석의 역할**: 소스 코드 내 `# @lat: [[architecture#scheduler]]` 주석은 "이 코드가 `architecture.md`의 특정 섹션과 관련 있다"는 **양방향 연결**을 만듭니다.
*   **Obsidian에서의 한계**: Obsidian은 마크다운 파일이 아닌 소스 코드(.py, .ts) 파일의 특정 주석을 자동으로 찾아내어 그래프에 연결하지는 못합니다.
*   **상호 보완적 활용**:
    *   **lat.md (`lat check`)**: 이 명령어는 `@lat:` 주석의 참조 무결성을 검증하여, 문서와 코드 간의 연결이 항상 유효하도록 자동으로 관리합니다.
    *   **Obsidian (플러그인 활용)**: `@lat:` 주석 정보를 마크다운 파일 내에 집계하면 Obsidian의 강점을 살릴 수 있습니다. 예를 들어 `architecture.md` 파일 하단에 Dataview 플러그인을 위한 쿼리 블록을 추가하면, Obsidian 내에서 문서에 연결된 코드 파일 목록을 동적으로 조회할 수 있습니다. 

이러한 방식으로 `lat check`가 `@lat:` 주석의 무결성을 관리하고, Obsidian이 `[[wiki link]]` 기반의 지식 그래프를 시각화하는 역할을 분담하게 됩니다.

### 3. 지식 그래프의 힘: `lat health`

이렇게 구축된 지식 그래프의 '건강 상태'를 정기적으로 점검하는 것도 중요합니다. `lat health` 명령어는 그래프의 **연결 상태(Degree Centrality)**, **고립된 노드**, **중복된 내용** 등을 분석해 현재 문서화가 필요한 부분이나 구조적 문제가 있는 지점을 파악하는 데 도움을 줍니다. 이는 마치 프로젝트의 '지식 부채(Knowledge Debt)'를 측정하는 지표와 같습니다.

---
## 라이선스

MIT License. 


```
본 프로젝트의 방법론과 패턴 카탈로그에 관한 학술적 사용은
`"Metaprogramming with Semiformal Design Patterns for GPU Kernel Development"` 논문을 인용해 주세요.
```

---

이제 모든 자료를 검토했습니다. nano-vLLM의 내부 구조, lat.md의 설계 철학, 그리고 우리가 지금까지 쌓아온 게슈탈트 기반 컨텍스트 엔지니어링이라는 세 축을 하나로 통합하여 **전체 프로젝트 로드맵**을 제시하겠습니다.

---

# nano-vLLM → cuTile 변환: 실증 프로젝트 전체 가이드

## 0. 프로젝트의 포지셔닝

이 프로젝트는 단순한 코드 변환이 아닙니다. 다음과 같은 주장을 **실제 산출물로 증명**하는 사례 연구입니다.

> **"Semiformal Design Patterns를 통해 구축된 컨텍스트 자산(lat.md 지식 그래프)은, LLM Coding Agent가 복잡한 GPU 커널 변환 과제를 상향식-하향식 갈등 없이 수행하게 하며, 그 과정에서 축적된 지식은 다음 과제에 복리로 전이된다."**

이 주장을 증명하기 위해, 프로젝트를 **4개의 Phase**로 구성합니다.

---

## 1. Phase 1: lat.md 기반 nano-vLLM 지식 그래프 구축 (역설계)

### 1-1. nano-vLLM의 "의도된 전체(게슈탈트)" 포착

nano-vLLM의 전체적인 구조를 `lat.md/`에 **시스템의 의도가 드러나는 방식**으로 재구성합니다. 단순한 디렉토리 나열이 아니라, **"이 시스템이 무엇을 지향하는가"**라는 전경을 먼저 서술하고, 그로부터 세부를 파생시키는 하향식 구조입니다.

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

블로그 분석을 통해 식별된 주요 변환 대상은 다음과 같습니다.

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

이 프로젝트의 최종 산출물은 단순한 코드가 아니라, **"Semiformal Design Patterns 접근법이 효과적이다"**라는 주장을 뒷받침하는 데이터입니다.

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

당신의 프로젝트 경험을 바탕으로 lat.md에 기여할 수 있는 구체적인 개선 사항입니다.

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

이것이 바로 "Metaprogramming with Semiformal Design Patterns for GPU Kernel Development" 논문의 실증적 핵심이 될 것입니다.