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

`agentic-stack` 저장소를 클론한 후, PowerShell용 설치 스크립트(`install.ps1`)를 사용하여 `codex` 어댑터를 프로젝트 root에 설치합니다.

```powershell
# 1. agentic-stack 저장소 클론
git clone https://github.com/codejunkie99/agentic-stack.git

# 2. 클론한 디렉토리로 이동
cd agentic-stack

# 3. PowerShell 설치 스크립트 실행 (codex 어댑터 + 프로젝트 경로 지정)
.\install.ps1 codex D:\code\metaprogramming\KnowledgeChef
```

이 명령어를 실행하면 KnowledgeChef 프로젝트 루트에 `.agent/` 폴더가 생성되고, Codex가 이를 인식할 수 있도록 심볼릭 링크 등이 자동으로 설정됩니다. (만약 `.\install.ps1` 실행이 안 된다면, 관리자 권한으로 PowerShell을 실행해 보세요).

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
# 프로젝트 루트(KnowledgeChef)에서 Codex CLI 실행
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

스킬 호출이 성공하면, 프로젝트 .agent에 Data Layer 산출물이 생성됩니다.

*   **생성 파일 예시**:
    *   `dashboard.html`: 여러 에이전트의 활동, 비용, KPI를 한눈에 볼 수 있는 웹 대시보드.
    *   `daily-report.md`: 일일 요약 보고서.
*   **확인 방법**: KnowledgeChef\.agent\data-layer\export `dashboard.html` 파일을 브라우저로 열어 시각화된 데이터를 확인합니다.

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

이 단계를 따라 진행하시면 Codex CLI 환경에서 `.agent` 기반의 Data Layer를 성공적으로 시험할 수 있을 것입니다.
