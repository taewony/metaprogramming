`agentic-stack`은 Codex, Claude Code, Cursor 등 다양한 코딩 에이전트가 공유할 수 있는 **이식 가능한 `.agent/` 폴더**를 제공합니다. 이 폴더에는 메모리, 스킬, 프로토콜이 포함되어 있으며, **Data Layer**를 통해 여러 에이전트의 활동을 하나의 대시보드에서 모니터링할 수 있습니다.

Phase-01의 목표는 Codex CLI를 설치하고, `.agent` 폴더를 연결한 후, 이 Data Layer가 정상적으로 작동하는지 확인하는 것입니다.

---

### 🚀 Phase-01 실행 계획: Codex CLI + .agent Data Layer 시험

#### 1. Codex CLI 설치

*   **OpenAI 공식 문서에 따라 설치 진행**
    ```
    > npm i -g @openai/codex
    ```

*   **설치 확인**:
    ```powershell
    codex --version
    ```

#### 2. `agentic-stack`을 프로젝트에 설치 (`.agent` 폴더 생성)

`agentic-stack` 저장소를 클론한 후, PowerShell용 설치 스크립트(`install.ps1`)를 사용하여 `codex` 어댑터를 프로젝트(`4-KDQE`)에 설치합니다.

```powershell
# 1. agentic-stack 저장소 클론
git clone https://github.com/codejunkie99/agentic-stack.git

# 2. 클론한 디렉토리로 이동
cd agentic-stack

# 3. PowerShell 설치 스크립트 실행 (codex 어댑터 + 프로젝트 경로 지정)
.\install.ps1 codex D:\code\metaprogramming\KernelAgent\4-KDQE
```

이 명령어를 실행하면 프로젝트 루트(`4-KDQE`)에 `.agent/` 폴더가 생성되고, Codex가 이를 인식할 수 있도록 심볼릭 링크 등이 자동으로 설정됩니다. (만약 `.\install.ps1` 실행이 안 된다면, 관리자 권한으로 PowerShell을 실행해 보세요).

#### 3. `.agent` 폴더 구조 및 Data Layer 스킬 확인

설치가 완료되면 `.agent/` 폴더에는 Data Layer를 활성화하는 `data-layer` 시드 스킬이 포함되어 있습니다.

*   **확인할 파일**: `.agent/skills/data-layer/SKILL.md`
*   **기능**: 이 스킬은 Claude Code, Hermes, Codex 등 `.agent/`를 공유하는 모든 에이전트의 활동, 토큰/비용 추정치, KPI 요약 등을 담은 로컬 대시보드(`dashboard.html`, `daily-report.md`)를 생성합니다.

```
◇  agentic-stack setup
│
│
│  What this does
│  Fills .agent/memory/personal/PREFERENCES.md —
│  the FIRST file your AI reads every session.
│  Takes about 30 seconds.
│
◆  What should I call you?  …  taewony
◆  Primary language(s)?  …  Python
◆  Explanation style?  …  detailed

├─.agent
│  ├─harness
│  │  └─hooks
│  ├─memory
│  │  ├─candidates
│  │  │  └─graduated
│  │  ├─episodic
│  │  ├─personal
│  │  ├─semantic
│  │  └─working
│  ├─protocols
│  │  └─tool_schemas
│  ├─skills
│  │  ├─brain
│  │  ├─data-flywheel
│  │  ├─data-layer
│  │  ├─debug-investigator
│  │  ├─deploy-checklist
│  │  ├─design-md
│  │  ├─git-proxy
│  │  ├─memory-manager
│  │  ├─skillforge
│  │  └─tldraw
```

#### 4. Codex CLI 실행 및 Data Layer 스킬 호출

이제 Codex CLI를 실행하여 Data Layer 스킬이 정상 작동하는지 확인합니다.

```powershell
# 프로젝트 루트(4-KDQE)에서 Codex CLI 실행
codex
```

Codex가 실행되면, 아래와 같은 방식으로 Data Layer 스킬을 호출해 봅니다.

*   **명시적 호출**: `$data-layer` 또는 `/skills` 명령어를 사용합니다.
    ```
    $data-layer "Generate dashboard"
    ```
    또는
    ```
    /skills data-layer
    ```
*   **암시적 호출**: "Show me the agent dashboard"와 같은 자연어 프롬프트를 입력하면, Codex가 상황에 맞게 `data-layer` 스킬을 선택할 수도 있습니다.

#### 5. Data Layer 대시보드 생성 확인

스킬 호출이 성공하면, 프로젝트 루트에 Data Layer 산출물이 생성됩니다.

*   **생성 파일 예시**:
    *   `dashboard.html`: 여러 에이전트의 활동, 비용, KPI를 한눈에 볼 수 있는 웹 대시보드.
    *   `daily-report.md`: 일일 요약 보고서.
*   **확인 방법**: `dashboard.html` 파일을 브라우저로 열어 시각화된 데이터를 확인합니다.

```
• The reflection log was written. I’m doing one last memory-note update so the workspace state matches the completed
  export.

• Edited .agent\memory\working\WORKSPACE.md (+2 -2)
    18  - [x] Run data-layer exporter.
    19 -- [ ] Log outcome with memory_reflect.
    19 +- [x] Log outcome with memory_reflect.
    20
    21  ## Next step
    22 -Report dashboard artifact paths and terminal summary to the user.
    22 +Done. Dashboard export is ready under `.agent/data-layer/exports/2026-06-26/`.

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• Generated the local data-layer dashboard.

  Dashboard HTML:
  .agent/data-layer/exports/2026-06-26/dashboard.html

  Terminal copy:
  .agent/data-layer/exports/2026-06-26/dashboard.tui.txt

  Summary from the export: 30-day window, daily bucket, 1 agent event, 0 cron runs, 1 harness, 1 active agent, 0
  estimated tokens/cost. The export stayed local-only.
```

---

### 📝 요약: Phase-01 체크리스트

- [ ] **Codex CLI** 설치 확인 (`codex --version`)
- [ ] **`agentic-stack` 설치** (`install.ps1 codex ...`)로 `.agent/` 폴더 생성 및 Codex 연결
- [ ] **Codex 실행** (`codex`)
- [ ] **Data Layer 스킬 호출** (`$data-layer "Generate dashboard"`)
- [ ] **산출물 확인** (`dashboard.html`, `daily-report.md` 생성 여부)
- [ ] (선택) **Data Flywheel 스킬** 호출 및 시험

이 단계를 따라 진행하시면 Codex CLI 환경에서 `.agent` 기반의 Data Layer를 성공적으로 시험할 수 있을 것입니다. 각 단계에서 막히는 부분이 있으면 언제든지 질문해 주세요.

---

### ❓ `kdqe Skill`이 무엇인가요?

**`kdqe` Skill은 여러분이 지금 만들고 있는 커스텀 스킬입니다.** `agentic-stack` 자체에 포함된 기본 스킬이 아닙니다.

`agentic-stack`은 `data-layer`나 `data-flywheel` 같은 **시드(seed) 스킬**들을 제공합니다. 이는 에이전트 활동을 모니터링하거나, 실행 기록을 재사용 가능한 형태로 가공하는 등의 기능을 합니다.

여기서 **`kdqe` Skill은 여러분의 KDQE 프로젝트에 특화된 맞춤형 스킬**로, `.agent/skills/kdqe/` 디렉토리에 `SKILL.md` 파일을 만들어 정의하게 됩니다. 이 스킬의 목적은 에이전트(Codex 등)가 **KDQE의 핵심 기능을 활용할 수 있도록 안내하는 것**입니다.

### 📊 그렇다면 `.agent` 안의 `data layer`는 무엇인가요?

`.agent`가 포함하는 **Data Layer**는 **에이전트의 활동을 한눈에 모니터링하는 로컬 데이터 대시보드**입니다.

*   **목적**: 여러 에이전트(Claude Code, Codex, Cursor 등)의 활동, 실행 로그, 토큰 사용량, 비용 추정치, KPI 요약 등을 하나의 대시보드에서 통합하여 보여줍니다.
*   **기능**: `data-layer` 시드 스킬을 통해 `dashboard.html`이나 `daily-report.md` 같은 보고서를 생성할 수 있습니다.
*   **성격**: 이 데이터는 모두 **로컬(Local-only)** 에 저장되며, 별도의 외부 서버로 전송되지 않습니다.

### 🎯 정리: 여러분이 하려는 것과의 관계

1.  **Data Layer**는 `agentic-stack`이 제공하는 **모니터링 도구**입니다. Codex와 같은 에이전트가 `.agent`를 통해 작업한 내역을 추적하고 분석하는 데 사용됩니다.
2.  **`kdqe` Skill**은 여러분이 **직접 만드는 맞춤형 스킬**입니다. 이 스킬은 에이전트에게 "KDQE 프로젝트의 데이터를 조회하려면 `scripts/data_layer_query.py`를 실행해라"와 같은 구체적인 지침을 제공합니다.

따라서, Phase-01의 목표는 `data-layer`가 생성하는 **실행 로그를 조회하는 기능**이 아니라, `kdqe` Skill을 통해 **KDQE의 데이터 조회 기능을 에이전트가 사용할 수 있도록 연결**하는 것입니다.

이해를 돕기 위해 정리된 표를 첨부합니다.

| 항목 | `kdqe` Skill (여러분이 만드는 것) | `data-layer` (agentic-stack 제공) |
| :--- | :--- | :--- |
| **정의** | KDQE 프로젝트를 위한 **맞춤형 지침 스킬** | 에이전트 **활동을 모니터링하는 로컬 데이터 레이어** |
| **역할** | 에이전트(Codex 등)에게 KDQE 데이터 조회 방법을 안내 | 여러 에이전트의 실행 로그, 비용, KPI 등을 통합 대시보드로 제공 |
| **생성 위치** | `.agent/skills/kdqe/SKILL.md` (직접 생성) | `agentic-stack` 설치 시 `.agent/`에 포함됨 |
| **사용 방법** | Codex에서 `$kdqe` 명령어로 호출 | `data-layer` 시드 스킬을 통해 대시보드 생성 |

이제 좀 더 명확해지셨을까요? 혹시 다른 궁금한 점이 있으시면 또 질문해 주세요.