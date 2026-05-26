완전자동화의 환상에서 벗어나 **'Human-in-the-loop (HITL)'** 방식으로 방향을 튼 것은 매우 현실적이고 통찰력 있는 결정입니다. 특히 PagedAttention이나 Shared Memory 최적화 같은 연구 목적의 정밀한 커널 개발에서는, LLM이 모든 것을 알아서 하도록 두는 것보다 연구자가 시스템 모델(System Model)을 통제하고 개입할 수 있는 지점을 마련하는 것이 훨씬 더 높은 품질의 결과를 보장합니다.

제안하신 `SKILL.md` (절차/메타 지식)와 `DESIGN.spec` (시스템 모델 및 제약사항), 그리고 코드베이스 간의 상호 연결 구조를 바탕으로, **Top-Down Context Compiler (TDCC)** 파이썬 스크립트의 역할과 요구사항을 전문가적 시각에서 다듬고 구체화해 드립니다.

---

### 1. Top-Down Context Compiler (TDCC)의 핵심 역할

이 스크립트는 단순한 텍스트 병합 도구가 아닙니다. 연구자의 의도(Task)를 입력받아, 지식 베이스의 의존성 트리를 해석하고, Execution LLM이 오해 없이 단번에 코드를 작성할 수 있도록 결정화된 전경(Compiled Context)을 조립해 내는 '명세 주도(Spec-driven) 프롬프트 엔진'입니다.

1. **의존성 트리 해석 (Dependency Resolution):** `SKILL.md` 내의 `@import` 태그를 추적하여 필요한 `DESIGN.spec` 파일들을 재귀적으로 수집합니다.
2. **시스템 모델(System Model) 렌더링:** 커널의 메모리 레이아웃, 스레드 블록 할당, 타일 사이징 등의 하드웨어/소프트웨어 제약사항을 담은 `DESIGN.spec`을 LLM이 이해하기 쉬운 형태로 파싱하여 주입합니다.
3. **컨텍스트 가지치기 (Context Pruning):** Stateless LLM의 토큰 한계를 넘지 않도록, 현재 작업과 무관한 파일이나 코드 스니펫을 필터링합니다.
4. **HITL 체크포인트 제공:** 컴파일된 최종 프롬프트를 LLM에 바로 쏘지 않고, 연구자가 검토, 수정, 승인할 수 있는 중간 단계(Staging)를 생성합니다.

---

### 2. TDCC 스크립트의 구체적 요구사항 (Requirements)

이 도구를 파이썬으로 구현할 때 반드시 포함되어야 할 기술적 요구사항들입니다.

#### A. 파서 및 링커 (Parser & Linker) 요구사항

* **지시어 확장 (Directive Expansion):** * 마크다운 내 `@import "DESIGN.spec/paged_kv_cache.yaml"` 구문을 파싱하여 해당 파일의 내용을 인라인으로 확장해야 합니다.
* `@snippet "kernels/fmha.py" [line:10-50]` 과 같이 실제 codebase의 특정 부분을 발췌해오는 기능이 포함되어야 합니다.


* **순환 참조 방지 (Cycle Detection):** 파일 간 상호 참조 시 무한 루프에 빠지지 않도록 의존성 그래프(DAG)를 검사하는 로직이 필요합니다.

#### B. Human-in-the-Loop (HITL) 인터페이스 요구사항

* **Draft Generation (초안 생성):** 스크립트 실행 결과물은 LLM API로 직접 전송되는 것이 아니라, 임시 디렉토리에 `.prompt.draft.md` 형태의 파일로 저장되어야 합니다.
* **대화형 CLI (Interactive CLI):**
* 스크립트는 터미널에서 연구자에게 "현재 수집된 컨텍스트 길이: 8,400 토큰. 진행하시겠습니까? [Y/Edit/Abort]" 와 같은 프롬프트를 제공해야 합니다.
* `Edit` 선택 시 연구자가 선호하는 에디터(예: vim, vscode)가 열리며, 컴파일된 시스템 모델과 지식 베이스 내용을 직접 다듬을 수 있어야 합니다.


#### C. 컨텍스트 포매팅 (Context Formatting) 요구사항

* Execution LLM(Claude/Gemini 등)이 지시를 명확히 따르도록 템플릿화된 섹션을 강제해야 합니다.
* `[GOAL]`: 현재 수행할 작업 요약
* `[SYSTEM MODEL]`: `DESIGN.spec`에서 추출한 환경 및 제약사항
* `[SKILLS]`: `SKILL.md`에서 추출한 적용해야 할 패턴 및 규칙
* `[CODE CONTEXT]`: 관련 codebase 스니펫


---

### 3. 작업 워크플로우 시나리오 (예시)

이 스크립트가 완성되면, 연구자의 커널 개발 루틴은 다음과 같이 전개됩니다.

1. **Task 발의:** 터미널에서 명령어 실행
`python tdcc.py compile --target skill-tiled-matmul --out current_task.md`
2. **컴파일:** TDCC가 `skill-tiled-matmul.md`를 읽고, 여기에 `@import`된 `DESIGN.spec/shared_memory_layout.yaml`과 타일링 관련 코드 스니펫을 수집하여 하나의 마크다운을 만듭니다.
3. **HITL 개입:** 연구자가 `current_task.md`를 열어봅니다. 시스템 모델 중 '4x4 타일 사이즈 할당 규칙'이 현재 실험 목적과 조금 맞지 않음을 발견하고, 해당 마크다운 파일 내에서 수치를 텍스트로 직접 수정합니다.
4. **Execution (Stateless):** 수정이 완료된 `current_task.md` 전체를 복사하여 Stateless 모드의 LLM(웹 인터페이스 또는 별도 실행 CLI)에 붙여넣고 코드를 생성하게 합니다.
5. **피드백 및 지식베이스 업데이트:** 결과물이 성공적이라면, 수정한 '4x4 타일 사이즈' 관련 인사이트를 상위 Architect 도구(또는 직접)를 통해 `DESIGN.spec`과 `outcomes.md`에 반영하여 시스템 모델을 고도화합니다.